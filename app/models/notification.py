from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base

class Notification(Base):
    """Event-driven, idempotent notification log across channels."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    # e.g. NOTIF-APP-123-REMINDER-T15-2026-10-30
    recipient_id = Column(String(36), nullable=False, index=True)
    recipient_name = Column(String(128), nullable=True)
    recipient_email = Column(String(128), nullable=True)
    recipient_phone = Column(String(32), nullable=True)
    recipient_role = Column(String(32), nullable=False)
    
    channel = Column(String(32), default="IN_APP") # IN_APP, EMAIL, SMS, WHATSAPP
    subject = Column(String(255), nullable=False)
    message_body = Column(Text, nullable=False)
    
    entity_type = Column(String(64), nullable=False) # APPLICATION, LEASE, UNDERTAKING, EVC
    entity_id = Column(String(36), nullable=False, index=True)
    triggering_rule_code = Column(String(64), nullable=True)
    escalation_level = Column(Integer, default=0)
    
    delivery_status = Column(String(32), default="SENT") # SENT, DELIVERED, READ, FAILED
    calendar_ics_content = Column(Text, nullable=True) # Optional .ics calendar invite content
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
