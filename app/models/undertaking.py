from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Undertaking(Base):
    """Institutional promises and conditional EoA obligations."""
    __tablename__ = "undertakings"

    id = Column(String(36), primary_key=True)
    undertaking_number = Column(String(64), unique=True, nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    institution_id = Column(String(36), nullable=False, index=True)
    category = Column(String(64), nullable=False)
    # FACULTY_RECRUITMENT, LAB_EQUIPMENT_UPGRADE, LAND_REGISTRATION_RECTIFICATION, CADRE_RATIO_COMPLIANCE
    title = Column(String(255), nullable=False)
    undertaking_text = Column(Text, nullable=False)
    
    issued_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False, index=True)
    compliance_status = Column(String(32), default="PENDING", index=True)
    # PENDING, SUBMITTED, VERIFIED, BREACHED, ESCALATED
    
    evidence_document_id = Column(String(36), nullable=True)
    submission_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    
    verifier_id = Column(String(36), nullable=True)
    verifier_role = Column(String(32), nullable=True)
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="undertakings")
