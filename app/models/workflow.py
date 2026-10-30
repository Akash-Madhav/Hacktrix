from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, synonym
from app.database import Base

class WorkflowConfig(Base):
    """Pathways stored as data in the statechart engine."""
    __tablename__ = "workflow_configs"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    pathway_code = Column(String(64), unique=True, nullable=False, index=True)
    # Examples: PATHWAY_SCRUTINY_ONLY, PATHWAY_SCRUTINY_EVC, PATHWAY_EVC_SAC_SHC, PATHWAY_EVC_ONLY
    description = Column(Text, nullable=True)
    version = Column(String(32), default="APH-2026-V1.0")
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    stages_json = Column(Text, nullable=False) # JSON array of ordered stage definitions with allowed transitions
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowTransition(Base):
    """Immutable transition event log for guarded moves and mandatory revert reasons."""
    __tablename__ = "workflow_transitions"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    from_stage = Column(String(64), nullable=False)
    to_stage = Column(String(64), nullable=False)
    action_type = Column(String(32), nullable=False) # ADVANCE, REVERT, ESCALATE, ON_HOLD, RESUME, CLOSE
    actor_id = Column(String(36), nullable=False) # user id
    actor_role = Column(String(32), nullable=False)
    mandatory_reason = Column(Text, nullable=True) # Required if action_type is REVERT or ON_HOLD
    notes = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    timestamp = synonym("created_at")

    application = relationship("Application", back_populates="transitions")
