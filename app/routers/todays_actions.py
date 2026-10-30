from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sla import MonitoredTask
from app.models.application import Application
from app.models.user import User

router = APIRouter(prefix="/api/actions", tags=["Officer Console (Today's Actions)"])

@router.get("/today")
def get_todays_action_docket(
    officer_id: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 15,
    db: Session = Depends(get_db)
):
    """Produces the prioritized, urgency-ranked daily action list for scrutiny officers.
    Ranked by: Overdue delay, Early-Warning P(breach), Escalation level, and Application Priority.
    """
    query = db.query(MonitoredTask).filter(MonitoredTask.status.notin_(["RESOLVED", "CANCELLED"]))

    if officer_id:
        query = query.filter(MonitoredTask.assigned_officer_id == officer_id)

    tasks = query.all()

    # Score each task for urgency ranking
    ranked_items = []
    for t in tasks:
        app = db.query(Application).filter(Application.id == t.entity_id).first() if t.entity_type == "APPLICATION" else None
        
        if region and app and app.region != region:
            continue

        # Urgency scoring formula
        score = 0.0
        if t.status == "ESCALATED":
            score += 1000.0 + (t.escalation_level * 200.0)
        elif t.status == "OVERDUE":
            score += 500.0 + (abs(t.working_days_remaining) * 20.0)
        elif t.status == "DUE_SOON":
            score += 200.0 + ((4 - max(0, t.working_days_remaining)) * 30.0)
        else:
            score += 50.0

        # Add Early Warning Risk Weight (0-100)
        score += (t.risk_score or 0.0) * 100.0

        # Priority multiplier
        if app and app.priority == "CRITICAL":
            score += 150.0
        elif app and app.priority == "HIGH":
            score += 75.0

        # Officer lookup
        officer_name = "Unassigned"
        officer_leave = False
        if t.assigned_officer_id:
            user = db.query(User).filter(User.id == t.assigned_officer_id).first()
            if user:
                officer_name = user.full_name
                officer_leave = user.is_on_leave

        # Construct concise human reason
        urgency_reason = ""
        if t.status == "ESCALATED":
            urgency_reason = f"CRITICAL: Escalated to Level {t.escalation_level}. Overdue by {abs(t.working_days_remaining)} working days."
        elif t.status == "OVERDUE":
            urgency_reason = f"OVERDUE: Stage limit exceeded by {abs(t.working_days_remaining)} working days. Imminent Regional Head escalation."
        elif t.status == "DUE_SOON":
            prob_pct = int((t.risk_score or 0.5) * 100)
            urgency_reason = f"DUE SOON: {t.working_days_remaining} working days remaining. Early-Warning ML estimates {prob_pct}% chance of SLA breach."
        else:
            urgency_reason = f"Active docket in {t.current_stage.replace('_', ' ').title()}. On-track with {t.working_days_remaining} days remaining."

        if officer_leave:
            urgency_reason += " (Assigned officer on leave; auto-delegated to regional deputy)."

        ranked_items.append({
            "task_id": t.id,
            "task_number": t.task_number,
            "title": t.title,
            "entity_type": t.entity_type,
            "application_id": app.id if app else None,
            "application_number": app.application_number if app else None,
            "institution_name": app.institution_name if app else t.title,
            "region": app.region if app else "Western",
            "current_stage": t.current_stage,
            "status": t.status,
            "working_days_remaining": t.working_days_remaining,
            "calculated_due_date": t.calculated_due_date.isoformat() if t.calculated_due_date else None,
            "escalation_level": t.escalation_level,
            "risk_score": t.risk_score,
            "risk_level": t.risk_level,
            "assigned_officer": officer_name,
            "urgency_score": round(score, 1),
            "urgency_reason": urgency_reason,
            "recommended_action": t.recommended_intervention or "Review application documents and complete verification."
        })

    # Sort descending by urgency score
    ranked_items.sort(key=lambda x: x["urgency_score"], reverse=True)
    return ranked_items[:limit]
