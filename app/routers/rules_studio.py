import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sla import SLARule
from app.services.policy_compiler import policy_compiler
from app.services.sla_engine import sla_engine

router = APIRouter(prefix="/api/rules", tags=["Rules Studio & SLM Policy Compiler"])

class CompileClauseRequest(BaseModel):
    clause_id: str
    actor_id: str = "ADMIN-CHIEF"

class ApproveRuleRequest(BaseModel):
    admin_id: str = "ADMIN-CHIEF"

class DraftLetterRequest(BaseModel):
    application_number: str
    institution_name: str
    stage: str
    deficiency_reason: str

@router.get("/all")
def list_rules(db: Session = Depends(get_db)):
    sla_engine.ensure_default_rules(db)
    rules = db.query(SLARule).order_by(SLARule.rule_code.asc(), SLARule.version.desc()).all()
    return [{
        "id": r.id,
        "rule_code": r.rule_code,
        "version": r.version,
        "process_category": r.process_category,
        "stage_name": r.stage_name,
        "duration_days": r.duration_days,
        "duration_type": r.duration_type,
        "reminder_offsets": json.loads(r.reminder_offsets_json) if r.reminder_offsets_json else [],
        "escalation_ladder": json.loads(r.escalation_ladder_json) if r.escalation_ladder_json else [],
        "effective_from": r.effective_from.isoformat() if r.effective_from else None,
        "is_active": r.is_active,
        "approval_status": r.approval_status,
        "change_summary": r.change_summary
    } for r in rules]

@router.get("/clauses")
def list_sample_clauses():
    """Lists handbook provisions (e.g. 2 Dec 2025 Corrigendum) ready for SLM Policy Compilation."""
    return policy_compiler.get_sample_clauses()

@router.post("/compile-clause")
def compile_clause(req: CompileClauseRequest, db: Session = Depends(get_db)):
    """Small Language Model parses clause into draft versioned rule (Quarantined until human approval)."""
    return policy_compiler.compile_clause_to_rule(db, req.clause_id, req.actor_id)

@router.post("/{rule_id}/approve")
def approve_rule(rule_id: str, req: ApproveRuleRequest, db: Session = Depends(get_db)):
    """Human-in-the-loop gate: Administrator approves draft rule to go live."""
    try:
        return policy_compiler.approve_rule(db, rule_id, req.admin_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/draft-letter")
def draft_bilingual_memo(req: DraftLetterRequest):
    """Produces bilingual deficiency letters in English and Hindi."""
    return policy_compiler.draft_bilingual_letter(
        application_number=req.application_number,
        institution_name=req.institution_name,
        stage=req.stage,
        deficiency_reason=req.deficiency_reason
    )
