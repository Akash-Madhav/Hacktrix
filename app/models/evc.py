from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class EVCExpert(Base):
    """Empanelled expert profile for EVC inspections."""
    __tablename__ = "evc_experts"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    phone = Column(String(32), nullable=True)
    department = Column(String(128), nullable=False)
    designation = Column(String(128), default="Professor")
    affiliation_university = Column(String(255), nullable=False) # For conflict of interest checks
    region = Column(String(64), nullable=False)
    expertise_area = Column(String(128), nullable=False) # ENGINEERING_TECH, PHARMACY, MANAGEMENT, etc.
    
    max_monthly_visits = Column(Integer, default=3)
    visits_this_month = Column(Integer, default=0)
    
    availability_dates_json = Column(Text, default="[]") # List of available ISO date strings
    conflict_institutions_json = Column(Text, default="[]") # List of barred institution IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EVCPanel(Base):
    """Inspection panel constitution and scheduling."""
    __tablename__ = "evc_panels"

    id = Column(String(36), primary_key=True)
    panel_number = Column(String(64), unique=True, nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    institution_id = Column(String(36), nullable=False, index=True)
    region = Column(String(64), nullable=False)
    scheduled_date = Column(DateTime, nullable=True)
    
    status = Column(String(32), default="PROPOSED", index=True)
    # PROPOSED, CONFIRMED, VISIT_COMPLETED, REPORT_SUBMITTED, CANCELLED, OVERDUE
    
    assigned_experts_json = Column(Text, default="[]") # List of selected expert IDs with roles
    selection_reasons_json = Column(Text, nullable=True) # Explanation why each expert was chosen
    excluded_candidates_json = Column(Text, nullable=True) # Conflict rules that excluded others
    
    visit_report_summary = Column(Text, nullable=True)
    deficiency_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", back_populates="evc_panels")
