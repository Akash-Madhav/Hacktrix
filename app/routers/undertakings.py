from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.undertaking import Undertaking
from app.models.application import Application
from app.services.clock_service import clock_service
from app.services.audit_ledger import audit_ledger

router = APIRouter(prefix="/api/undertakings", tags=["Undertakings Register"])

class VerifyUndertakingRequest(BaseModel):
    compliance_status: str # VERIFIED, BREACHED
    verifier_id: str
    verification_notes: str

@router.get("")
def list_undertakings(
    status: Optional[str] = None,
    institution_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Undertaking)
    if status:
        query = query.filter(Undertaking.compliance_status == status)
    if institution_id:
        query = query.filter(Undertaking.institution_id == institution_id)

    undertakings = query.order_by(Undertaking.due_date.asc()).all()
    sim_now = clock_service.now(db)

    results = []
    for u in undertakings:
        app = db.query(Application).filter(Application.id == u.application_id).first()
        days_left = (u.due_date.date() - sim_now.date()).days
        results.append({
            "id": u.id,
            "undertaking_number": u.undertaking_number,
            "application_id": u.application_id,
            "application_number": app.application_number if app else None,
            "institution_name": app.institution_name if app else "Institution",
            "institution_id": u.institution_id,
            "category": u.category,
            "title": u.title,
            "undertaking_text": u.undertaking_text,
            "issued_date": u.issued_date.isoformat() if u.issued_date else None,
            "due_date": u.due_date.isoformat() if u.due_date else None,
            "days_remaining": days_left,
            "compliance_status": u.compliance_status,
            "is_overdue": days_left < 0 and u.compliance_status != "VERIFIED",
            "evidence_document_id": u.evidence_document_id,
            "verified_at": u.verified_at.isoformat() if u.verified_at else None
        })
    return results

@router.post("/{undertaking_id}/verify")
def verify_undertaking(undertaking_id: str, req: VerifyUndertakingRequest, db: Session = Depends(get_db)):
    u = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Undertaking not found.")

    sim_now = clock_service.now(db)
    u.compliance_status = req.compliance_status
    u.verifier_id = req.verifier_id
    u.verification_notes = req.verification_notes
    u.verified_at = sim_now
    db.commit()

    audit_ledger.record_event(
        db=db,
        event_type="UNDERTAKING_VERIFIED",
        entity_type="UNDERTAKING",
        entity_id=u.id,
        actor_id=req.verifier_id,
        actor_role="SCRUTINY_OFFICER",
        action_summary=f"Marked undertaking {u.undertaking_number} as {req.compliance_status}",
        previous_state="PENDING",
        new_state=req.compliance_status,
        reason=req.verification_notes
    )

    return {"status": "SUCCESS", "undertaking_number": u.undertaking_number, "compliance_status": u.compliance_status}
