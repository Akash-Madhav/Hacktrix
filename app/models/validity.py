from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ValidityRecord(Base):
    """External validity registry for leases, NOCs, and time-bound statutory certificates."""
    __tablename__ = "validity_records"

    id = Column(String(36), primary_key=True)
    institution_id = Column(String(36), nullable=False, index=True)
    document_type = Column(String(64), nullable=False, index=True)
    # LEASE_DEED, FIRE_SAFETY_NOC, BUILDING_PLAN_APPROVAL, LAND_USE_CERTIFICATE
    certificate_number = Column(String(128), nullable=False)
    issuing_authority = Column(String(255), nullable=True)
    valid_from = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)
    
    status = Column(String(32), default="VALID", index=True)
    # VALID, EXPIRING_SOON, OVERDUE_EXPIRED, RENEWAL_SUBMITTED, RENEWED
    
    last_reminder_offset = Column(String(32), nullable=True) # e.g. T-30, T-15, T-7, T-1
    renewal_document_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
