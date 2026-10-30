from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from app.database import Base

class AuditLedger(Base):
    """Schneier & Kelsey (1999) style tamper-evident hash-chained audit ledger.
    Each record binds to the cryptographic hash of the preceding record:
    h_i = SHA-256(h_{i-1} || canonical_json(event_i)).
    """
    __tablename__ = "audit_ledger"

    id = Column(String(36), primary_key=True)
    sequence_number = Column(Integer, unique=True, nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    # APPLICATION_SUBMITTED, STAGE_TRANSITION, REVERT_ACTION, SLA_OVERDUE_BREACH,
    # ESCALATION_LEVEL_CHANGE, UNDERTAKING_RECORDED, RULE_MODIFIED, RECORD_TAMPER_SIMULATION
    
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(36), nullable=False, index=True)
    actor_id = Column(String(36), nullable=False)
    actor_role = Column(String(32), nullable=False)
    action_summary = Column(String(255), nullable=False)
    
    previous_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    
    canonical_payload_json = Column(Text, nullable=False)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)
    
    is_tampered = Column(Boolean, default=False) # Controlled demonstration flag
    tamper_note = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
