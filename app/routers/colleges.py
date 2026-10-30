import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.application import Application
from app.models.sla import MonitoredTask
from app.models.workflow import WorkflowTransition
from app.services.clock_service import clock_service
from app.services.calendar_service import calendar_service

router = APIRouter(prefix="/api/colleges", tags=["College Monitoring MVP"])

# Standard AICTE Stages for the MVP
AICTE_STAGES = [
    {"stage": "SUBMITTED", "label": "1. Application Submitted", "sla_days": 3},
    {"stage": "INITIAL_SCRUTINY", "label": "2. Document Scrutiny", "sla_days": 15},
    {"stage": "TECHNICAL_REVIEW", "label": "3. Technical Review", "sla_days": 10},
    {"stage": "EVC_INSPECTION", "label": "4. EVC Inspection", "sla_days": 10},
    {"stage": "REGIONAL_REVIEW", "label": "5. Regional Review", "sla_days": 7},
    {"stage": "APPROVED", "label": "6. Bureau Approved", "sla_days": 0},
]

class CollegeCreatePayload(BaseModel):
    institution_name: str
    application_number: Optional[str] = None
    institution_permanent_id: Optional[str] = None
    region: str = "Western"
    state: str = "Maharashtra"
    district: Optional[str] = "Pune"
    institution_type: Optional[str] = "ENGINEERING_TECH"
    current_stage: Optional[str] = "INITIAL_SCRUTINY"
    assigned_officer: Optional[str] = "Regional Scrutiny Officer"
    sla_working_days: Optional[int] = 15

class TransitionPayload(BaseModel):
    to_stage: str
    reason: Optional[str] = "Stage advanced per approval procedure"
    actor: Optional[str] = "Admin / Officer"

class AIUpdatePayload(BaseModel):
    college_name: str
    update_text: str

@router.get("", response_model=List[Dict[str, Any]])
def list_colleges(db: Session = Depends(get_db)):
    """Retrieve all colleges with their live approval stages, deadlines, and SLA statuses."""
    apps = db.query(Application).order_by(Application.created_at.desc()).all()
    sim_now = clock_service.now(db)
    results = []

    for app in apps:
        task = db.query(MonitoredTask).filter(MonitoredTask.entity_id == app.id).first()
        
        working_days_rem = None
        sla_status = "ON_TRACK"
        deadline_str = None
        sla_days_total = 15
        
        if task and task.calculated_due_date:
            deadline = task.calculated_due_date
            deadline_str = deadline.strftime("%d %b %Y, %I:%M %p")
            
            if deadline >= sim_now:
                working_days_rem = calendar_service.count_working_days(db, sim_now, deadline)
            else:
                working_days_rem = -calendar_service.count_working_days(db, deadline, sim_now)
            
            if app.current_stage in ("APPROVED", "BUREAU_APPROVED"):
                sla_status = "APPROVED"
            elif app.current_stage == "REJECTED":
                sla_status = "REJECTED"
            elif working_days_rem < 0:
                sla_status = "OVERDUE"
            elif working_days_rem <= 3:
                sla_status = "DUE_SOON"
            else:
                sla_status = "ON_TRACK"

        results.append({
            "id": app.id,
            "institution_name": app.institution_name,
            "application_number": app.application_number,
            "institution_permanent_id": app.institution_permanent_id or "1-XXXXXXX",
            "region": app.region or "Western",
            "state": app.state or "Maharashtra",
            "district": app.district or "General",
            "institution_type": app.institution_type or "ENGINEERING_TECH",
            "current_stage": app.current_stage or "SUBMITTED",
            "assigned_officer": "Regional Scrutiny Officer",
            "sla_deadline": deadline_str,
            "sla_status": sla_status,
            "sla_duration_days": sla_days_total,
            "working_days_remaining": working_days_rem,
            "created_at": app.created_at.strftime("%d %b %Y") if app.created_at else None
        })

    return results

@router.post("", status_code=status.HTTP_201_CREATED)
def create_college(payload: CollegeCreatePayload, db: Session = Depends(get_db)):
    """Intake a college application and initialize its SLA monitoring task."""
    app_id = str(uuid.uuid4())
    sim_now = clock_service.now(db)
    
    app_num = payload.application_number or f"1-{uuid.uuid4().hex[:10].upper()}"
    perm_id = payload.institution_permanent_id or f"1-{uuid.uuid4().hex[:7].upper()}"
    stage = payload.current_stage or "INITIAL_SCRUTINY"
    sla_days = payload.sla_working_days or 15

    # 1. Create Application
    new_app = Application(
        id=app_id,
        application_number=app_num,
        institution_permanent_id=perm_id,
        institution_name=payload.institution_name,
        region=payload.region,
        state=payload.state,
        district=payload.district or "General",
        institution_type=payload.institution_type or "ENGINEERING_TECH",
        current_stage=stage,
        created_at=sim_now,
        updated_at=sim_now
    )
    db.add(new_app)

    # 2. Compute Working-Day Deadline
    deadline_dt = calendar_service.add_working_days(db, sim_now, sla_days)

    # 3. Create MonitoredTask
    task_id = f"TSK-{app_id[:8].upper()}"
    task = MonitoredTask(
        id=task_id,
        task_number=f"TSK-{app_num}",
        entity_type="APPLICATION",
        entity_id=app_id,
        title=f"Application Approval SLA: {payload.institution_name}",
        process_category="APPLICATION_SLA",
        current_stage=stage,
        assigned_officer_id="usr-reg-01",
        start_date=sim_now,
        calculated_due_date=deadline_dt,
        status="ACTIVE",
        working_days_elapsed=0,
        working_days_remaining=sla_days,
        calendar_days_remaining=(deadline_dt.date() - sim_now.date()).days,
        escalation_level=0
    )
    db.add(task)

    # 4. Log Initial Transition
    transition = WorkflowTransition(
        id=str(uuid.uuid4()),
        application_id=app_id,
        from_stage="SUBMITTED",
        to_stage=stage,
        action_type="INTAKE",
        actor_id="admin-01",
        actor_role="SYSTEM_ADMIN",
        mandatory_reason=f"College dossier registered and placed into {stage} stage with {sla_days} working-day SLA.",
        created_at=sim_now
    )
    db.add(transition)

    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"College '{payload.institution_name}' registered successfully.",
        "college_id": app_id,
        "application_number": app_num,
        "current_stage": stage,
        "deadline": deadline_dt.strftime("%d %b %Y, %I:%M %p"),
        "working_days_sla": sla_days
    }

@router.get("/{college_id}")
def get_college_details(college_id: str, db: Session = Depends(get_db)):
    """Fetch complete college profile, timeline, and 'where is where' lifecycle progression."""
    app = db.query(Application).filter(Application.id == college_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="College not found")

    sim_now = clock_service.now(db)
    task = db.query(MonitoredTask).filter(MonitoredTask.entity_id == app.id).first()
    transitions = (
        db.query(WorkflowTransition)
        .filter(WorkflowTransition.application_id == app.id)
        .order_by(WorkflowTransition.created_at.desc())
        .all()
    )

    working_days_rem = None
    sla_status = "ON_TRACK"
    if task and task.calculated_due_date:
        if task.calculated_due_date >= sim_now:
            working_days_rem = calendar_service.count_working_days(db, sim_now, task.calculated_due_date)
        else:
            working_days_rem = -calendar_service.count_working_days(db, task.calculated_due_date, sim_now)
            
        if app.current_stage in ("APPROVED", "BUREAU_APPROVED"):
            sla_status = "APPROVED"
        elif app.current_stage == "REJECTED":
            sla_status = "REJECTED"
        elif working_days_rem < 0:
            sla_status = "OVERDUE"
        elif working_days_rem <= 3:
            sla_status = "DUE_SOON"

    return {
        "id": app.id,
        "institution_name": app.institution_name,
        "application_number": app.application_number,
        "institution_permanent_id": app.institution_permanent_id,
        "region": app.region,
        "state": app.state,
        "district": app.district,
        "institution_type": app.institution_type,
        "current_stage": app.current_stage,
        "assigned_officer": "Regional Scrutiny Officer",
        "sla_status": sla_status,
        "sla_deadline": task.calculated_due_date.strftime("%d %b %Y, %I:%M %p") if task and task.calculated_due_date else "N/A",
        "sla_duration_days": 15,
        "working_days_remaining": working_days_rem,
        "stages_pipeline": AICTE_STAGES,
        "history": [
            {
                "id": t.id,
                "from_stage": t.from_stage,
                "to_stage": t.to_stage,
                "action": t.action_type,
                "actor_name": t.actor_role,
                "reason": t.mandatory_reason or t.notes,
                "timestamp": t.created_at.strftime("%d %b %Y, %I:%M %p") if t.created_at else None
            }
            for t in transitions
        ]
    }

@router.post("/{college_id}/transition")
def transition_college_stage(college_id: str, payload: TransitionPayload, db: Session = Depends(get_db)):
    """Progresses or reverts the college's approval stage and updates SLA tracking."""
    app = db.query(Application).filter(Application.id == college_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="College not found")

    sim_now = clock_service.now(db)
    old_stage = app.current_stage
    new_stage = payload.to_stage

    stage_meta = next((s for s in AICTE_STAGES if s["stage"] == new_stage), None)
    sla_days = stage_meta["sla_days"] if stage_meta else 10

    # 1. Update Application stage
    app.current_stage = new_stage
    app.updated_at = sim_now

    # 2. Update MonitoredTask
    task = db.query(MonitoredTask).filter(MonitoredTask.entity_id == app.id).first()
    if task:
        task.current_stage = new_stage
        task.start_date = sim_now
        if sla_days > 0:
            task.calculated_due_date = calendar_service.add_working_days(db, sim_now, sla_days)
            task.working_days_remaining = sla_days
            task.status = "ACTIVE"
        else:
            task.status = "RESOLVED"
            task.working_days_remaining = 0

    # 3. Record Audit Transition
    transition = WorkflowTransition(
        id=str(uuid.uuid4()),
        application_id=app.id,
        from_stage=old_stage,
        to_stage=new_stage,
        action_type="STAGE_TRANSITION",
        actor_id="admin-01",
        actor_role="ADMIN_OFFICER",
        mandatory_reason=payload.reason or f"Transitioned from {old_stage} to {new_stage}.",
        created_at=sim_now
    )
    db.add(transition)

    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"College status updated to '{new_stage}'.",
        "previous_stage": old_stage,
        "new_stage": new_stage,
        "new_deadline": task.calculated_due_date.strftime("%d %b %Y, %I:%M %p") if task and task.calculated_due_date else "Completed"
    }

@router.delete("/{college_id}")
def delete_college(college_id: str, db: Session = Depends(get_db)):
    """Delete a college application and its associated tasks from monitoring."""
    app = db.query(Application).filter(Application.id == college_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="College not found")

    db.query(MonitoredTask).filter(MonitoredTask.entity_id == college_id).delete()
    db.query(WorkflowTransition).filter(WorkflowTransition.application_id == college_id).delete()
    db.delete(app)
    db.commit()

    return {"status": "SUCCESS", "message": f"College '{app.institution_name}' removed from monitoring."}

@router.post("/ai-update")
async def ai_update_college(payload: AIUpdatePayload, db: Session = Depends(get_db)):
    """Natural Language AI Update powered by Qwen 2.5 SLM."""
    from app.services.ai_update_service import apply_ai_college_update
    try:
        result = await apply_ai_college_update(db, payload.college_name, payload.update_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI update failed: {e}")

@router.post("/purge-all", status_code=status.HTTP_200_OK)
def purge_all_data():
    """Wipes all records for a clean slate."""
    from app.data.clear_database import clear_all_tables
    clear_all_tables()
    return {"status": "SUCCESS", "message": "All college monitoring data purged completely."}
