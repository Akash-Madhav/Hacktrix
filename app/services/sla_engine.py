import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from app.models.sla import SLARule, MonitoredTask, SLAEvent
from app.models.application import Application
from app.models.undertaking import Undertaking
from app.models.validity import ValidityRecord
from app.models.evc import EVCPanel
from app.models.user import User
from app.services.clock_service import clock_service
from app.services.calendar_service import calendar_service
from app.services.audit_ledger import audit_ledger

# Standard default SLA rules from Approval Process Handbook
DEFAULT_SLA_RULES = [
    {
        "rule_code": "APH-SLA-SCRUTINY-V1",
        "version": "1.0",
        "process_category": "APPLICATION_STAGE",
        "stage_name": "INITIAL_SCRUTINY",
        "duration_days": 15,
        "duration_type": "WORKING_DAYS",
        "reminder_offsets": [-5, -2, 0],
        "escalation_ladder": [
            {"days_after": 0, "level": 0, "role": "SCRUTINY_OFFICER", "action": "DUE_ALERT"},
            {"days_after": 3, "level": 1, "role": "REGIONAL_OFFICER", "action": "ESCALATE_TO_REGIONAL_HEAD"},
            {"days_after": 7, "level": 2, "role": "BUREAU_OFFICER", "action": "ESCALATE_TO_BUREAU_HEAD"}
        ],
        "change_summary": "Initial statutory scrutiny period (15 working days)."
    },
    {
        "rule_code": "APH-SLA-RE-SCRUTINY-V1",
        "version": "1.0",
        "process_category": "APPLICATION_STAGE",
        "stage_name": "RE_SCRUTINY",
        "duration_days": 7,
        "duration_type": "WORKING_DAYS",
        "reminder_offsets": [-3, -1, 0],
        "escalation_ladder": [
            {"days_after": 0, "level": 0, "role": "SCRUTINY_OFFICER", "action": "DUE_ALERT"},
            {"days_after": 2, "level": 1, "role": "REGIONAL_OFFICER", "action": "ESCALATE_TO_REGIONAL_HEAD"}
        ],
        "change_summary": "Re-scrutiny after institutional correction upload."
    },
    {
        "rule_code": "APH-SLA-EVC-INSPECTION-V1",
        "version": "1.0",
        "process_category": "APPLICATION_STAGE",
        "stage_name": "EVC_INSPECTION",
        "duration_days": 15,
        "duration_type": "WORKING_DAYS",
        "reminder_offsets": [-5, -2, 0],
        "escalation_ladder": [
            {"days_after": 0, "level": 0, "role": "SCRUTINY_OFFICER", "action": "DUE_ALERT"},
            {"days_after": 3, "level": 1, "role": "REGIONAL_OFFICER", "action": "ESCALATE_TO_REGIONAL_HEAD"}
        ],
        "change_summary": "On-site EVC inspection scheduling and report submission."
    },
    {
        "rule_code": "APH-SLA-REGIONAL-COMMITTEE-V1",
        "version": "1.0",
        "process_category": "APPLICATION_STAGE",
        "stage_name": "REGIONAL_COMMITTEE",
        "duration_days": 10,
        "duration_type": "WORKING_DAYS",
        "reminder_offsets": [-3, -1, 0],
        "escalation_ladder": [
            {"days_after": 0, "level": 1, "role": "REGIONAL_OFFICER", "action": "DUE_ALERT"},
            {"days_after": 4, "level": 2, "role": "BUREAU_OFFICER", "action": "ESCALATE_TO_BUREAU_HEAD"}
        ],
        "change_summary": "Regional Committee evaluation and recommendation."
    },
    {
        "rule_code": "APH-SLA-UNDERTAKING-V1",
        "version": "1.0",
        "process_category": "UNDERTAKING",
        "stage_name": "UNDERTAKING_COMPLIANCE",
        "duration_days": 90,
        "duration_type": "CALENDAR_DAYS",
        "reminder_offsets": [-30, -15, -7, -1, 0],
        "escalation_ladder": [
            {"days_after": 0, "level": 0, "role": "INSTITUTION", "action": "DUE_ALERT"},
            {"days_after": 5, "level": 1, "role": "REGIONAL_OFFICER", "action": "ESCALATE_TO_REGIONAL_HEAD"}
        ],
        "change_summary": "Conditional approval undertaking compliance window (90 days)."
    },
    {
        "rule_code": "APH-SLA-VALIDITY-EXPIRY-V1",
        "version": "1.0",
        "process_category": "DOCUMENT_EXPIRY",
        "stage_name": "VALIDITY_RENEWAL",
        "duration_days": 30,
        "duration_type": "CALENDAR_DAYS",
        "reminder_offsets": [-30, -15, -7, -1],
        "escalation_ladder": [
            {"days_after": 0, "level": 0, "role": "INSTITUTION", "action": "EXPIRY_WARNING"},
            {"days_after": 1, "level": 1, "role": "REGIONAL_OFFICER", "action": "FLAG_EXPIRED_DOCUMENT"}
        ],
        "change_summary": "T-30/15/7/1 document validity advance alert schedule."
    }
]

class SLAMonitoringEngine:
    @staticmethod
    def ensure_default_rules(db: Session):
        for r in DEFAULT_SLA_RULES:
            existing = db.query(SLARule).filter(SLARule.rule_code == r["rule_code"]).first()
            if not existing:
                rule = SLARule(
                    id=str(uuid.uuid4()),
                    rule_code=r["rule_code"],
                    version=r["version"],
                    process_category=r["process_category"],
                    stage_name=r.get("stage_name"),
                    duration_days=r["duration_days"],
                    duration_type=r["duration_type"],
                    reminder_offsets_json=json.dumps(r["reminder_offsets"]),
                    escalation_ladder_json=json.dumps(r["escalation_ladder"]),
                    effective_from=datetime(2026, 1, 1),
                    is_active=True,
                    created_by="SYSTEM_AICTE",
                    approval_status="APPROVED",
                    change_summary=r["change_summary"]
                )
                db.add(rule)
        db.commit()

    @staticmethod
    def get_applicable_rule(db: Session, process_category: str, stage_name: Optional[str] = None) -> Optional[SLARule]:
        SLAMonitoringEngine.ensure_default_rules(db)
        sim_now = clock_service.now(db)
        
        query = db.query(SLARule).filter(
            SLARule.process_category == process_category,
            SLARule.is_active == True,
            SLARule.effective_from <= sim_now
        )
        if stage_name:
            # First attempt specific stage match
            stage_match = query.filter(SLARule.stage_name == stage_name).first()
            if stage_match:
                return stage_match
        return query.first()

    @staticmethod
    def register_or_update_task(
        db: Session,
        entity_type: str,
        entity_id: str,
        title: str,
        process_category: str,
        current_stage: str,
        assigned_officer_id: Optional[str] = None,
        state_code: str = "ALL"
    ) -> MonitoredTask:
        """Registers a process for unified SLA tracking or updates its stage and deadline."""
        sim_now = clock_service.now(db)
        task = db.query(MonitoredTask).filter(
            MonitoredTask.entity_type == entity_type,
            MonitoredTask.entity_id == entity_id
        ).first()

        rule = SLAMonitoringEngine.get_applicable_rule(db, process_category, current_stage)
        duration_days = rule.duration_days if rule else 15
        duration_type = rule.duration_type if rule else "WORKING_DAYS"

        # Calculate deadline
        if duration_type == "WORKING_DAYS":
            due_date = calendar_service.add_working_days(db, sim_now, duration_days, state_code)
        else:
            due_date = sim_now + timedelta(days=duration_days)

        if not task:
            task = MonitoredTask(
                id=str(uuid.uuid4()),
                task_number=f"TSK-{entity_type[:3]}-{str(uuid.uuid4())[:8].upper()}",
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                process_category=process_category,
                current_stage=current_stage,
                assigned_officer_id=assigned_officer_id,
                sla_rule_id=rule.id if rule else None,
                start_date=sim_now,
                calculated_due_date=due_date,
                status="ACTIVE",
                working_days_elapsed=0,
                working_days_remaining=duration_days if duration_type == "WORKING_DAYS" else (due_date.date() - sim_now.date()).days,
                calendar_days_remaining=(due_date.date() - sim_now.date()).days,
                escalation_level=0,
                created_at=sim_now
            )
            db.add(task)
        else:
            # Update stage and re-baseline SLA
            task.current_stage = current_stage
            task.title = title
            task.assigned_officer_id = assigned_officer_id or task.assigned_officer_id
            task.sla_rule_id = rule.id if rule else task.sla_rule_id
            task.start_date = sim_now
            task.calculated_due_date = due_date
            task.status = "ACTIVE"
            task.escalation_level = 0
            task.working_days_elapsed = 0
            task.working_days_remaining = duration_days if duration_type == "WORKING_DAYS" else (due_date.date() - sim_now.date()).days
            task.calendar_days_remaining = (due_date.date() - sim_now.date()).days

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def evaluate_task(db: Session, task: MonitoredTask, state_code: str = "ALL") -> MonitoredTask:
        """Evaluates SLA status, calculates working days remaining, and detects breaches & leave-aware delegation."""
        if task.status in ["RESOLVED", "CANCELLED"]:
            return task

        sim_now = clock_service.now(db)
        rule = task.rule or db.query(SLARule).filter(SLARule.id == task.sla_rule_id).first()
        duration_type = rule.duration_type if rule else "WORKING_DAYS"

        # Calculate elapsed and remaining
        if duration_type == "WORKING_DAYS":
            elapsed = calendar_service.count_working_days(db, task.start_date, sim_now, state_code)
            task.working_days_elapsed = elapsed
            if sim_now < task.calculated_due_date:
                remaining = calendar_service.count_working_days(db, sim_now, task.calculated_due_date, state_code)
                task.working_days_remaining = remaining
            else:
                overdue_days = calendar_service.count_working_days(db, task.calculated_due_date, sim_now, state_code)
                task.working_days_remaining = -overdue_days
        else:
            elapsed = (sim_now.date() - task.start_date.date()).days
            remaining = (task.calculated_due_date.date() - sim_now.date()).days
            task.working_days_elapsed = elapsed
            task.working_days_remaining = remaining

        task.calendar_days_remaining = (task.calculated_due_date.date() - sim_now.date()).days

        # Check for Leave-Aware Auto-Delegation
        if task.assigned_officer_id:
            assigned_user = db.query(User).filter(User.id == task.assigned_officer_id).first()
            if assigned_user and assigned_user.is_on_leave:
                if assigned_user.deputy_user_id:
                    # Auto-delegate to deputy
                    old_officer = assigned_user.full_name
                    deputy = db.query(User).filter(User.id == assigned_user.deputy_user_id).first()
                    if deputy:
                        task.assigned_officer_id = deputy.id
                        audit_ledger.record_event(
                            db=db,
                            event_type="LEAVE_AUTO_DELEGATION",
                            entity_type="TASK",
                            entity_id=task.id,
                            actor_id="SYSTEM_AUTO_DELEGATE",
                            actor_role="SYSTEM",
                            action_summary=f"Reassigned task {task.task_number} from {old_officer} (On Leave) to {deputy.full_name}",
                            previous_state=old_officer,
                            new_state=deputy.full_name,
                            reason=f"Officer {old_officer} is on leave until {assigned_user.leave_until.strftime('%d-%b-%Y') if assigned_user.leave_until else 'further notice'}."
                        )

        # Derive Status
        prev_status = task.status
        if task.working_days_remaining < 0:
            delay_days = abs(task.working_days_remaining)
            if delay_days >= 7:
                task.status = "ESCALATED"
                task.escalation_level = 2 # Bureau Head
            elif delay_days >= 3:
                task.status = "ESCALATED"
                task.escalation_level = 1 # Regional Head
            else:
                task.status = "OVERDUE"
                task.escalation_level = 0 # Assigned Officer
        elif task.working_days_remaining <= 3:
            task.status = "DUE_SOON"
        else:
            task.status = "ACTIVE"

        # Update application SLA status if entity is application
        if task.entity_type == "APPLICATION":
            app = db.query(Application).filter(Application.id == task.entity_id).first()
            if app:
                app.sla_status = task.status

        # If status transitioned to OVERDUE or ESCALATED, record event
        if prev_status != task.status and task.status in ["OVERDUE", "ESCALATED"]:
            event = SLAEvent(
                id=str(uuid.uuid4()),
                task_id=task.id,
                event_type=f"{task.status}_TRIGGERED",
                triggering_rule_code=rule.rule_code if rule else "UNKNOWN",
                details_json=json.dumps({
                    "delay_days": abs(task.working_days_remaining),
                    "escalation_level": task.escalation_level,
                    "evaluated_at": sim_now.isoformat()
                }),
                created_at=sim_now
            )
            db.add(event)

            # Trigger notification dispatch
            from app.services.alert_engine import alert_engine
            alert_engine.dispatch_sla_alert(db, task, rule)

        task.last_checked_at = sim_now
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def evaluate_all_tasks(db: Session) -> Dict[str, Any]:
        """Sweeps and evaluates all active tasks across all modules."""
        tasks = db.query(MonitoredTask).filter(MonitoredTask.status.notin_(["RESOLVED", "CANCELLED"])).all()
        summary = {"total": len(tasks), "active": 0, "due_soon": 0, "overdue": 0, "escalated": 0}
        
        for t in tasks:
            app = db.query(Application).filter(Application.id == t.entity_id).first() if t.entity_type == "APPLICATION" else None
            state_code = app.state if app else "ALL"
            updated = SLAMonitoringEngine.evaluate_task(db, t, state_code)
            status_key = updated.status.lower()
            if status_key in summary:
                summary[status_key] += 1

        # Also sweep Validity Registry (T-30, T-15, T-7, T-1)
        SLAMonitoringEngine.sweep_validity_registry(db)
        return summary

    @staticmethod
    def sweep_validity_registry(db: Session):
        """Monitors externally expiring leases, NOCs, and certificates with T-30, 15, 7, 1 reminders."""
        sim_now = clock_service.now(db)
        records = db.query(ValidityRecord).filter(ValidityRecord.status.notin_(["RENEWED"])).all()
        from app.services.alert_engine import alert_engine

        for rec in records:
            days_to_expiry = (rec.expiry_date.date() - sim_now.date()).days
            if days_to_expiry <= 0:
                rec.status = "OVERDUE_EXPIRED"
            elif days_to_expiry <= 30:
                rec.status = "EXPIRING_SOON"
            
            # Check T-30/15/7/1 thresholds
            for offset in [30, 15, 7, 1]:
                if days_to_expiry <= offset:
                    offset_tag = f"T-{offset}"
                    if rec.last_reminder_offset != offset_tag:
                        rec.last_reminder_offset = offset_tag
                        alert_engine.dispatch_validity_alert(db, rec, days_to_expiry, offset_tag)
                        break
        db.commit()

    @staticmethod
    def explain_task_sla(db: Session, task_id: str) -> Dict[str, Any]:
        """CRITICAL EXPLAINABILITY REQUIREMENT: Returns exact deterministic calculation explanation."""
        task = db.query(MonitoredTask).filter(MonitoredTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        sim_now = clock_service.now(db)
        rule = task.rule or db.query(SLARule).filter(SLARule.id == task.sla_rule_id).first()
        
        duration_days = rule.duration_days if rule else 15
        duration_type = rule.duration_type if rule else "WORKING_DAYS"
        rule_code = rule.rule_code if rule else "APH-DEFAULT-SLA"
        rule_version = rule.version if rule else "v1.0"

        # Determine responsible officer / recipient
        assigned_name = "Unassigned"
        assigned_role = "SCRUTINY_OFFICER"
        if task.assigned_officer_id:
            user = db.query(User).filter(User.id == task.assigned_officer_id).first()
            if user:
                assigned_name = user.full_name
                assigned_role = user.role

        is_overdue = task.working_days_remaining < 0
        delay_days = abs(task.working_days_remaining) if is_overdue else 0

        next_action = "Routine scrutiny review in progress"
        if task.status == "DUE_SOON":
            next_action = f"Complete review within {task.working_days_remaining} working day(s) to avoid SLA breach."
        elif task.status == "OVERDUE":
            next_action = f"Immediate action required by {assigned_name}. At +3 days delay, case escalates to Regional Head."
        elif task.status == "ESCALATED":
            ladder_role = "Regional Head" if task.escalation_level == 1 else "Bureau Head"
            next_action = f"Case escalated to {ladder_role}. Officer intervention memo issued."

        return {
            "task_id": task.id,
            "task_number": task.task_number,
            "title": task.title,
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
            "process_category": task.process_category,
            "current_stage": task.current_stage,
            "applicable_rule": {
                "rule_code": rule_code,
                "version": rule_version,
                "duration_days": duration_days,
                "duration_type": duration_type,
                "approval_status": rule.approval_status if rule else "APPROVED"
            },
            "calculation_breakdown": {
                "start_date": task.start_date.strftime("%d %B %Y, %I:%M %p"),
                "calculated_deadline": task.calculated_due_date.strftime("%d %B %Y, %I:%M %p"),
                "current_simulated_date": sim_now.strftime("%d %B %Y, %I:%M %p"),
                "working_days_elapsed": task.working_days_elapsed,
                "working_days_remaining": task.working_days_remaining,
                "calendar_days_remaining": task.calendar_days_remaining,
                "is_overdue": is_overdue,
                "delay_working_days": delay_days
            },
            "status": task.status,
            "escalation_level": task.escalation_level,
            "assigned_responsible": {
                "name": assigned_name,
                "role": assigned_role
            },
            "trigger_reason": f"SLA duration of {duration_days} {duration_type.lower()} exceeded by {delay_days} days." if is_overdue else f"Normal progression with {task.working_days_remaining} working days remaining.",
            "next_action": next_action
        }

sla_engine = SLAMonitoringEngine()
