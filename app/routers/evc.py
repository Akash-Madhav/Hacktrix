import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.evc import EVCPanel, EVCExpert
from app.models.application import Application
from app.services.evc_optimizer import evc_optimizer

router = APIRouter(prefix="/api/evc", tags=["EVC Panel Management & CP-SAT Optimizer"])

class OptimizeRequest(BaseModel):
    scheduled_date: Optional[str] = None

class ConfirmPanelRequest(BaseModel):
    panel_id: str
    officer_notes: Optional[str] = None

@router.get("/panels")
def list_evc_panels(region: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(EVCPanel)
    if region:
        query = query.filter(EVCPanel.region == region)
    if status:
        query = query.filter(EVCPanel.status == status)

    panels = query.order_by(EVCPanel.created_at.desc()).all()
    results = []
    for p in panels:
        app = db.query(Application).filter(Application.id == p.application_id).first()
        results.append({
            "id": p.id,
            "panel_number": p.panel_number,
            "application_id": p.application_id,
            "application_number": app.application_number if app else None,
            "institution_name": app.institution_name if app else "Institution",
            "region": p.region,
            "scheduled_date": p.scheduled_date.isoformat() if p.scheduled_date else None,
            "status": p.status,
            "assigned_experts": json.loads(p.assigned_experts_json) if p.assigned_experts_json else [],
            "selection_reasons": json.loads(p.selection_reasons_json) if p.selection_reasons_json else [],
            "excluded_candidates": json.loads(p.excluded_candidates_json) if p.excluded_candidates_json else [],
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    return results

@router.get("/experts")
def list_evc_experts(domain: Optional[str] = None, region: Optional[str] = None, db: Session = Depends(get_db)):
    evc_optimizer.ensure_default_experts(db)
    query = db.query(EVCExpert).filter(EVCExpert.is_active == True)
    if domain:
        query = query.filter(EVCExpert.expertise_area == domain)
    if region:
        query = query.filter(EVCExpert.region == region)

    experts = query.all()
    return [{
        "id": e.id,
        "name": e.name,
        "email": e.email,
        "department": e.department,
        "designation": e.designation,
        "affiliation_university": e.affiliation_university,
        "region": e.region,
        "expertise_area": e.expertise_area,
        "max_monthly_visits": e.max_monthly_visits,
        "visits_this_month": e.visits_this_month,
        "is_available": e.visits_this_month < e.max_monthly_visits
    } for e in experts]

@router.post("/optimize/{application_id}")
def optimize_panel(application_id: str, req: OptimizeRequest, db: Session = Depends(get_db)):
    """Runs the CP-SAT optimizer to match 3 conflict-free experts for this inspection."""
    try:
        return evc_optimizer.optimize_panel_for_application(
            db=db,
            application_id=application_id,
            scheduled_date=req.scheduled_date
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/confirm/{panel_id}")
def confirm_panel(panel_id: str, db: Session = Depends(get_db)):
    panel = db.query(EVCPanel).filter(EVCPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found.")
    panel.status = "CONFIRMED"
    db.commit()
    return {"status": "SUCCESS", "message": f"Panel {panel.panel_number} confirmed."}
