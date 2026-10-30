from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SLARule(Base):
    """Versioned, effective-dated SLA rules (Rules as Code)."""
    __tablename__ = "sla_rules"

    id = Column(String(36), primary_key=True)
    rule_code = Column(String(64), nullable=False, index=True) # e.g. APH-SLA-SCRUTINY, APH-SLA-EVC, APH-SLA-LEASE
    version = Column(String(32), default="v1.0")
    process_category = Column(String(64), nullable=False) # APPLICATION_STAGE, UNDERTAKING, DOCUMENT_EXPIRY, EVC_INSPECTION
    stage_name = Column(String(64), nullable=True) # Specific stage if applicable
    duration_days = Column(Integer, nullable=False) # e.g. 15 working days
    duration_type = Column(String(32), default="WORKING_DAYS") # WORKING_DAYS | CALENDAR_DAYS
    reminder_offsets_json = Column(Text, default="[-5, -2, 0]") # offsets relative to due date (days)
    escalation_ladder_json = Column(Text, default='[{"days_after": 0, "role": "SCRUTINY_OFFICER"}, {"days_after": 3, "role": "REGIONAL_OFFICER"}, {"days_after": 7, "role": "BUREAU_OFFICER"}]')
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(64), default="SYSTEM_ADMIN")
    approval_status = Column(String(32), default="APPROVED") # DRAFT | PENDING_APPROVAL | APPROVED | REJECTED
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MonitoredTask(Base):
    """Central unified task monitored by the SLA Monitoring Engine."""
    __tablename__ = "monitored_tasks"

    id = Column(String(36), primary_key=True)
    task_number = Column(String(64), unique=True, nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True) # APPLICATION, UNDERTAKING, LEASE_DOCUMENT, EVC_PANEL
    entity_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    process_category = Column(String(64), nullable=False) # APPLICATION_SLA, UNDERTAKING, LEASE_DOCUMENT, EVC_MONITORING
    current_stage = Column(String(64), nullable=False)
    assigned_officer_id = Column(String(36), nullable=True, index=True)
    sla_rule_id = Column(String(36), ForeignKey("sla_rules.id"), nullable=True)
    
    start_date = Column(DateTime, nullable=False)
    calculated_due_date = Column(DateTime, nullable=False, index=True)
    status = Column(String(32), default="ACTIVE", index=True)
    # NOT_STARTED, ACTIVE, DUE_SOON, REMINDER_SENT, OVERDUE, ESCALATED, RESOLVED, ON_HOLD, CANCELLED
    
    working_days_elapsed = Column(Integer, default=0)
    working_days_remaining = Column(Integer, default=0)
    calendar_days_remaining = Column(Integer, default=0)
    escalation_level = Column(Integer, default=0) # 0 = Officer, 1 = Regional Head, 2 = Bureau Head
    
    # Predictive Risk & Early Warning (WARN)
    risk_score = Column(Float, default=0.0) # P(breach within 7 days): 0.0 - 1.0
    risk_level = Column(String(32), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors_json = Column(Text, nullable=True) # Top 3 contributing factors
    recommended_intervention = Column(Text, nullable=True)
    
    resolution_timestamp = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rule = relationship("SLARule")
    events = relationship("SLAEvent", back_populates="task", cascade="all, delete-orphan")


class SLAEvent(Base):
    """Event triggered during SLA lifecycle tracking."""
    __tablename__ = "sla_events"

    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("monitored_tasks.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    # STARTED, REMINDER_SENT, DUE_REACHED, OVERDUE_BREACH, ESCALATED, RESOLVED, ON_HOLD_PAUSE, RESUMED
    triggering_rule_code = Column(String(64), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    task = relationship("MonitoredTask", back_populates="events")


class Holiday(Base):
    """Regional & national working-day calendar registry."""
    __tablename__ = "holidays"

    id = Column(String(36), primary_key=True)
    holiday_date = Column(String(10), nullable=False, index=True) # YYYY-MM-DD
    name = Column(String(128), nullable=False)
    state_code = Column(String(32), default="ALL") # ALL or state code (e.g. MH, KA, UP, TN)
    year = Column(Integer, nullable=False, index=True)
