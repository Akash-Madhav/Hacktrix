from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sla import MonitoredTask, SLARule
from app.models.application import Application
from app.models.user import User
from app.services.sla_engine import sla_engine
from app.services.early_warning import early_warning

router = APIRouter(prefix="/api/monitoring", tags=["SLA Monitoring Engine (WATCH)"])

@router.get("/summary")
def get_monitoring_summary(db: Session = Depends(get_db)):
    """Unified Control Room KPI counters across all monitored tasks."""
    total = db.query(MonitoredTask).count()
    active = db.query(MonitoredTask).filter(MonitoredTask.status == "ACTIVE").count()
    due_soon = db.query(MonitoredTask).filter(MonitoredTask.status == "DUE_SOON").count()
    overdue = db.query(MonitoredTask).filter(MonitoredTask.status == "OVERDUE").count()
    escalated = db.query(MonitoredTask).filter(MonitoredTask.status == "ESCALATED").count()
    resolved = db.query(MonitoredTask).filter(MonitoredTask.status == "RESOLVED").count()

    # Regional distribution
    from sqlalchemy import select
    regions = ["Northern", "North-Western", "Central", "Eastern", "Western", "Southern", "South-Western", "South-Central"]
    region_stats = []
    for reg in regions:
        reg_app_ids = select(Application.id).filter(Application.region == reg)
        reg_overdue = db.query(MonitoredTask).filter(
            MonitoredTask.entity_id.in_(reg_app_ids),
            MonitoredTask.status.in_(["OVERDUE", "ESCALATED"])
        ).count()
        reg_total = db.query(MonitoredTask).filter(MonitoredTask.entity_id.in_(reg_app_ids)).count()
        region_stats.append({
            "region": reg,
            "total_dossiers": reg_total,
            "breached_count": reg_overdue,
            "compliance_rate": round(100.0 * (reg_total - reg_overdue) / max(1, reg_total), 1)
        })

    return {
        "kpis": {
            "total_monitored": total,
            "active_on_track": active,
            "due_soon": due_soon,
            "overdue_breach": overdue,
            "escalated_critical": escalated,
            "resolved_completed": resolved,
            "compliance_percentage": round(100.0 * (total - overdue - escalated) / max(1, total), 1)
        },
        "regional_breakdown": region_stats
    }

@router.get("/tasks")
def list_monitored_tasks(
    category: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    officer_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(MonitoredTask)

    if category:
        query = query.filter(MonitoredTask.process_category == category)
    if status:
        query = query.filter(MonitoredTask.status == status)
    if officer_id:
        query = query.filter(MonitoredTask.assigned_officer_id == officer_id)
    if risk_level:
        query = query.filter(MonitoredTask.risk_level == risk_level)
    if search:
        query = query.filter(MonitoredTask.title.ilike(f"%{search}%") | MonitoredTask.task_number.ilike(f"%{search}%"))

    tasks = query.order_by(MonitoredTask.calculated_due_date.asc()).offset(skip).limit(limit).all()

    results = []
    for t in tasks:
        # Officer lookup
        officer_name = "Unassigned"
        if t.assigned_officer_id:
            user = db.query(User).filter(User.id == t.assigned_officer_id).first()
            if user:
                officer_name = user.full_name

        # Regional lookup if application
        reg = "General"
        if t.entity_type == "APPLICATION":
            app = db.query(Application).filter(Application.id == t.entity_id).first()
            if app:
                reg = app.region

        results.append({
            "id": t.id,
            "task_number": t.task_number,
            "title": t.title,
            "entity_type": t.entity_type,
            "entity_id": t.entity_id,
            "process_category": t.process_category,
            "current_stage": t.current_stage,
            "region": reg,
            "assigned_officer_name": officer_name,
            "start_date": t.start_date.isoformat() if t.start_date else None,
            "calculated_due_date": t.calculated_due_date.isoformat() if t.calculated_due_date else None,
            "status": t.status,
            "working_days_elapsed": t.working_days_elapsed,
            "working_days_remaining": t.working_days_remaining,
            "calendar_days_remaining": t.calendar_days_remaining,
            "escalation_level": t.escalation_level,
            "risk_score": t.risk_score,
            "risk_level": t.risk_level,
            "recommended_intervention": t.recommended_intervention
        })

    return results

@router.get("/tasks/{task_id}/explain")
def explain_task(task_id: str, db: Session = Depends(get_db)):
    """Provides transparent, deterministic explanation of SLA calculation and escalation decision."""
    try:
        return sla_engine.explain_task_sla(db, task_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/sweep")
def trigger_sla_sweep(db: Session = Depends(get_db)):
    """Manually triggers evaluation of all active tasks across all modules."""
    summary = sla_engine.evaluate_all_tasks(db)
    return {"status": "SUCCESS", "evaluated_summary": summary}
