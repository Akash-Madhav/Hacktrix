from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.clock_service import clock_service
from app.services.sla_engine import sla_engine
from app.services.audit_ledger import audit_ledger

router = APIRouter(prefix="/api/clock", tags=["Simulated Clock & Fast-Forward"])

class AdvanceClockRequest(BaseModel):
    days: int = 1
    hours: int = 0

@router.get("/now")
def get_current_time(db: Session = Depends(get_db)):
    sim_now = clock_service.now(db)
    return {
        "simulated_now": sim_now.isoformat(),
        "formatted_display": sim_now.strftime("%d %B %Y, %I:%M %p"),
        "date_only": sim_now.strftime("%Y-%m-%d"),
        "year": sim_now.year
    }

@router.post("/advance")
def advance_clock(req: AdvanceClockRequest, db: Session = Depends(get_db)):
    """Fast-forwards application time by N days and immediately sweeps all SLAs."""
    old_time = clock_service.now(db)
    new_time = clock_service.advance_time(db, days=req.days, hours=req.hours)
    
    # Audit time advancement
    audit_ledger.record_event(
        db=db,
        event_type="CLOCK_FAST_FORWARD",
        entity_type="SYSTEM_CLOCK",
        entity_id="niriksha-system-clock",
        actor_id="EVALUATOR_DEMO",
        actor_role="ADMIN",
        action_summary=f"Fast-forwarded simulated clock by +{req.days} days ({old_time.strftime('%d-%b')} -> {new_time.strftime('%d-%b-%Y')})",
        previous_state=old_time.isoformat(),
        new_state=new_time.isoformat(),
        reason=f"Evaluation demo fast-forward (+{req.days} days)"
    )

    # Immediately run SLA evaluation sweep to reflect new state
    sweep_summary = sla_engine.evaluate_all_tasks(db)

    return {
        "status": "SUCCESS",
        "previous_time": old_time.isoformat(),
        "current_time": new_time.isoformat(),
        "formatted_display": new_time.strftime("%d %B %Y, %I:%M %p"),
        "days_advanced": req.days,
        "sla_sweep_summary": sweep_summary
    }

@router.post("/reset")
def reset_clock(db: Session = Depends(get_db)):
    reset_time = clock_service.reset_to_real_time(db)
    sweep_summary = sla_engine.evaluate_all_tasks(db)
    return {
        "status": "SUCCESS",
        "reset_to": reset_time.isoformat(),
        "formatted_display": reset_time.strftime("%d %B %Y, %I:%M %p"),
        "sla_sweep_summary": sweep_summary
    }
