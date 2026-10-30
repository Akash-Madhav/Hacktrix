import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.sla import MonitoredTask, SLARule
from app.models.validity import ValidityRecord
from app.models.user import User
from app.services.clock_service import clock_service
from app.services.audit_ledger import audit_ledger

class AlertEscalationEngine:
    @staticmethod
    def generate_ics_calendar(title: str, due_date: datetime, description: str) -> str:
        """Generates a standard iCalendar (.ics) format string for the deadline."""
        dt_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dt_start = due_date.strftime("%Y%m%dT%H%M%SZ")
        dt_end = (due_date).strftime("%Y%m%dT%H%M%SZ")
        
        return (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//AICTE NIRIKSHA//Control Room SLA//EN\n"
            "BEGIN:VEVENT\n"
            f"UID:{uuid.uuid4()}@aicte-niriksha.gov.in\n"
            f"DTSTAMP:{dt_stamp}\n"
            f"DTSTART:{dt_start}\n"
            f"DTEND:{dt_end}\n"
            f"SUMMARY:{title}\n"
            f"DESCRIPTION:{description}\n"
            "STATUS:CONFIRMED\n"
            "END:VEVENT\n"
            "END:VCALENDAR"
        )

    @staticmethod
    def send_notification_idempotent(
        db: Session,
        idempotency_key: str,
        recipient_id: str,
        recipient_name: str,
        recipient_email: str,
        recipient_role: str,
        channel: str,
        subject: str,
        message_body: str,
        entity_type: str,
        entity_id: str,
        triggering_rule_code: str,
        escalation_level: int = 0,
        calendar_ics: Optional[str] = None
    ) -> Optional[Notification]:
        """Dispatches a notification while strictly enforcing idempotency to prevent duplicate alerts."""
        existing = db.query(Notification).filter(Notification.idempotency_key == idempotency_key).first()
        if existing:
            return existing # Already sent, do not duplicate

        sim_now = clock_service.now(db)
        notif = Notification(
            id=str(uuid.uuid4()),
            idempotency_key=idempotency_key,
            recipient_id=recipient_id,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            recipient_role=recipient_role,
            channel=channel,
            subject=subject,
            message_body=message_body,
            entity_type=entity_type,
            entity_id=entity_id,
            triggering_rule_code=triggering_rule_code,
            escalation_level=escalation_level,
            delivery_status="DELIVERED",
            calendar_ics_content=calendar_ics,
            created_at=sim_now
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # Record in audit trail
        audit_ledger.record_event(
            db=db,
            event_type="NOTIFICATION_DISPATCHED",
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id="SYSTEM_ALERT_ENGINE",
            actor_role="SYSTEM",
            action_summary=f"Sent {channel} alert to {recipient_name} ({recipient_role}): {subject}",
            new_state=f"ESCALATION_L{escalation_level}",
            reason=f"Triggered by rule {triggering_rule_code}",
            payload={"recipient": recipient_email, "channel": channel, "idempotency_key": idempotency_key}
        )

        return notif

    @staticmethod
    def dispatch_sla_alert(db: Session, task: MonitoredTask, rule: Optional[SLARule]):
        """Dispatches appropriate ladder notification when SLA is overdue or escalated."""
        sim_now = clock_service.now(db)
        rule_code = rule.rule_code if rule else "APH-DEFAULT-SLA"
        escalation_level = task.escalation_level
        delay_days = abs(task.working_days_remaining)

        # Recipient determination based on escalation ladder
        recipient_role = "SCRUTINY_OFFICER"
        if escalation_level == 1:
            recipient_role = "REGIONAL_OFFICER"
        elif escalation_level >= 2:
            recipient_role = "BUREAU_OFFICER"

        user = db.query(User).filter(User.role == recipient_role).first()
        rec_id = user.id if user else "OFFICER-DEFAULT"
        rec_name = user.full_name if user else f"{recipient_role.replace('_', ' ').title()}"
        rec_email = user.email if user else f"{recipient_role.lower()}@aicte-niriksha.gov.in"

        subject = f"[NIRIKSHA ALERT - L{escalation_level}] {task.title} is {task.status}"
        body = (
            f"Dear {rec_name},\n\n"
            f"Statutory task '{task.title}' (ID: {task.task_number}) has exceeded its prescribed SLA.\n\n"
            f"• Stage: {task.current_stage}\n"
            f"• Delay: {delay_days} working day(s)\n"
            f"• Escalation Level: Level {escalation_level} ({recipient_role})\n"
            f"• Rule Citation: {rule_code}\n\n"
            f"Immediate review and intervention is required in the NIRIKSHA Control Room."
        )

        # Unique date-stamped idempotency key per escalation level
        idempotency_key = f"SLA-ALERT-{task.id}-L{escalation_level}-{sim_now.strftime('%Y%m%d')}"

        # Multi-channel simulation: In-App + Email + SMS
        for ch in ["IN_APP", "EMAIL", "SMS"]:
            ch_key = f"{idempotency_key}-{ch}"
            AlertEscalationEngine.send_notification_idempotent(
                db=db,
                idempotency_key=ch_key,
                recipient_id=rec_id,
                recipient_name=rec_name,
                recipient_email=rec_email,
                recipient_role=recipient_role,
                channel=ch,
                subject=subject,
                message_body=body,
                entity_type=task.entity_type,
                entity_id=task.entity_id,
                triggering_rule_code=rule_code,
                escalation_level=escalation_level
            )

    @staticmethod
    def dispatch_validity_alert(db: Session, record: ValidityRecord, days_remaining: int, offset_tag: str):
        """Sends T-30, T-15, T-7, T-1 advance alerts for expiring leases/NOCs with calendar .ics."""
        sim_now = clock_service.now(db)
        doc_type_human = record.document_type.replace('_', ' ').title()
        
        subject = f"[NIRIKSHA URGENT - {offset_tag}] {doc_type_human} Expiry in {days_remaining} Days"
        body = (
            f"Institutional Notice: Your {doc_type_human} (Cert No: {record.certificate_number}) "
            f"will expire on {record.expiry_date.strftime('%d-%B-%Y')}.\n\n"
            f"Please upload the verified renewed document to the NIRIKSHA Portal before the deadline "
            f"to prevent statutory approval lapses."
        )

        ics_cal = AlertEscalationEngine.generate_ics_calendar(
            title=f"AICTE Compliance: {doc_type_human} Expiry",
            due_date=record.expiry_date,
            description=body
        )

        idempotency_key = f"VAL-ALERT-{record.id}-{offset_tag}-{sim_now.strftime('%Y%m%d')}"

        # Multi-channel: In-App, Email, WhatsApp simulation
        for ch in ["IN_APP", "EMAIL", "WHATSAPP"]:
            ch_key = f"{idempotency_key}-{ch}"
            AlertEscalationEngine.send_notification_idempotent(
                db=db,
                idempotency_key=ch_key,
                recipient_id=record.institution_id,
                recipient_name="College Registrar",
                recipient_email="registrar@institution.edu.in",
                recipient_role="INSTITUTION",
                channel=ch,
                subject=subject,
                message_body=body,
                entity_type="VALIDITY_DOCUMENT",
                entity_id=record.id,
                triggering_rule_code="APH-SLA-VALIDITY-EXPIRY-V1",
                escalation_level=0 if days_remaining > 0 else 1,
                calendar_ics=ics_cal if ch == "EMAIL" else None
            )

alert_engine = AlertEscalationEngine()
