import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.application import Application
from app.models.workflow import WorkflowConfig, WorkflowTransition
from app.services.workflow_engine import workflow_engine

router = APIRouter(prefix="/api/workflow", tags=["Workflow Statechart Engine (ROUTE)"])

class TransitionRequest(BaseModel):
    application_id: str
    to_stage: str
    action_type: str = "ADVANCE" # ADVANCE, REVERT, ESCALATE, ON_HOLD
    actor_id: str
    actor_role: str
    mandatory_reason: Optional[str] = None
    notes: Optional[str] = None

@router.get("/configs")
def list_pathway_configs(db: Session = Depends(get_db)):
    workflow_engine.ensure_default_configs(db)
    configs = db.query(WorkflowConfig).filter(WorkflowConfig.is_active == True).all()
    return [{
        "id": c.id,
        "name": c.name,
        "pathway_code": c.pathway_code,
        "description": c.description,
        "version": c.version,
        "effective_from": c.effective_from.isoformat() if c.effective_from else None,
        "stages": json.loads(c.stages_json)
    } for c in configs]

@router.get("/configs/{pathway_code}")
def get_pathway_detail(pathway_code: str, db: Session = Depends(get_db)):
    cfg = workflow_engine.get_pathway_config(db, pathway_code)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Pathway {pathway_code} not found.")
    return {
        "id": cfg.id,
        "name": cfg.name,
        "pathway_code": cfg.pathway_code,
        "description": cfg.description,
        "version": cfg.version,
        "stages": json.loads(cfg.stages_json)
    }

@router.post("/transition")
def execute_transition(req: TransitionRequest, db: Session = Depends(get_db)):
    try:
        app = workflow_engine.transition_stage(
            db=db,
            application_id=req.application_id,
            to_stage=req.to_stage,
            actor_id=req.actor_id,
            actor_role=req.actor_role,
            action_type=req.action_type,
            mandatory_reason=req.mandatory_reason,
            notes=req.notes
        )
        return {
            "status": "SUCCESS",
            "message": f"Application {app.application_number} transitioned to {app.current_stage}",
            "application": {
                "id": app.id,
                "application_number": app.application_number,
                "current_stage": app.current_stage,
                "sla_status": app.sla_status,
                "stage_entered_at": app.stage_entered_at.isoformat() if app.stage_entered_at else None
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.get("/applications/{application_id}/history")
def get_transition_history(application_id: str, db: Session = Depends(get_db)):
    transitions = db.query(WorkflowTransition).filter(
        WorkflowTransition.application_id == application_id
    ).order_by(WorkflowTransition.created_at.asc()).all()

    return [{
        "id": t.id,
        "from_stage": t.from_stage,
        "to_stage": t.to_stage,
        "action_type": t.action_type,
        "actor_id": t.actor_id,
        "actor_role": t.actor_role,
        "mandatory_reason": t.mandatory_reason,
        "notes": t.notes,
        "timestamp": t.created_at.isoformat() if t.created_at else None
    } for t in transitions]
