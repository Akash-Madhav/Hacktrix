from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit import AuditLedger
from app.services.audit_ledger import audit_ledger

router = APIRouter(prefix="/api/audit", tags=["Proof-Grade Audit Ledger (PROVE)"])

class TamperRequest(BaseModel):
    target_sequence: Optional[int] = None

@router.get("/ledger")
def get_audit_ledger(limit: int = 50, skip: int = 0, db: Session = Depends(get_db)):
    records = db.query(AuditLedger).order_by(AuditLedger.sequence_number.desc()).offset(skip).limit(limit).all()
    return [{
        "sequence_number": r.sequence_number,
        "event_type": r.event_type,
        "entity_type": r.entity_type,
        "entity_id": r.entity_id,
        "actor_role": r.actor_role,
        "action_summary": r.action_summary,
        "previous_state": r.previous_state,
        "new_state": r.new_state,
        "reason": r.reason,
        "previous_hash": r.previous_hash[:12] + "...",
        "current_hash": r.current_hash[:12] + "...",
        "full_current_hash": r.current_hash,
        "is_tampered": r.is_tampered,
        "timestamp": r.timestamp.isoformat() if r.timestamp else None
    } for r in records]

@router.get("/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    """Recomputes the cryptographic SHA-256 hash sequence from genesis to prove immutability."""
    return audit_ledger.verify_chain(db)

@router.post("/tamper-demo")
def trigger_tamper_demo(req: TamperRequest, db: Session = Depends(get_db)):
    """Controlled evaluator test: deliberately alters a past record to verify tamper-evidence."""
    return audit_ledger.simulate_tamper_for_demo(db, target_sequence=req.target_sequence)
