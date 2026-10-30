from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True)
    application_number = Column(String(64), unique=True, nullable=False, index=True) # e.g. 1-46273286079
    institution_permanent_id = Column(String(32), nullable=True, index=True) # e.g. 1-4627328
    eoa_file_number = Column(String(128), nullable=True) # e.g. Western/1-46273286079/2026/EOA
    
    institution_name = Column(String(255), nullable=False)
    institution_type = Column(String(64), nullable=False, default="NEW_TECHNICAL_INSTITUTION")
    application_type = Column(String(64), nullable=False, default="NEW_INSTITUTION")
    
    region = Column(String(64), nullable=False, default="Western") # Western, Northern, Southern, etc.
    state = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    address = Column(Text, nullable=True)
    
    # NIRIKSHA Statechart Pathway & Workflow
    pathway_code = Column(String(64), nullable=False, default="PATHWAY_SCRUTINY_EVC")
    current_stage = Column(String(64), nullable=False, default="INITIAL_SCRUTINY", index=True)
    # SUBMITTED, INITIAL_SCRUTINY, RE_SCRUTINY, EVC_INSPECTION, REGIONAL_COMMITTEE, SAC_SHC, APPROVED, REJECTED, RETURNED_FOR_CORRECTION
    assigned_officer_id = Column(String(36), nullable=True, index=True)
    priority = Column(String(32), default="NORMAL") # NORMAL, HIGH, CRITICAL
    sla_status = Column(String(32), default="ACTIVE", index=True) # ACTIVE, DUE_SOON, OVERDUE, ESCALATED, RESOLVED
    
    stage_entered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    runs = relationship("ValidationRun", back_populates="application", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="application", cascade="all, delete-orphan")
    land_detail = relationship("LandDetail", back_populates="application", uselist=False, cascade="all, delete-orphan")
    builtup_detail = relationship("BuiltupDetail", back_populates="application", uselist=False, cascade="all, delete-orphan")
    verification_records = relationship("VerificationRecord", back_populates="application", cascade="all, delete-orphan")
    
    transitions = relationship("WorkflowTransition", back_populates="application", cascade="all, delete-orphan")
    undertakings = relationship("Undertaking", back_populates="application", cascade="all, delete-orphan")
    evc_panels = relationship("EVCPanel", back_populates="application", cascade="all, delete-orphan")


class Program(Base):
    __tablename__ = "programs"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    program_name = Column(String(128), nullable=False)
    level = Column(String(32), nullable=False, default="UG")
    approved_intake = Column(Integer, nullable=False, default=60)

    application = relationship("Application", back_populates="programs")


class LandDetail(Base):
    __tablename__ = "land_details"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, unique=True)
    total_area_acres = Column(Float, nullable=False)
    is_single_plot = Column(Boolean, default=True)
    ownership_type = Column(String(64), default="OWNED_GOVERNMENT_REGISTERED")
    survey_khasra_no = Column(String(128), nullable=True)
    land_registration_date = Column(String(32), nullable=True)

    application = relationship("Application", back_populates="land_detail")


class BuiltupDetail(Base):
    __tablename__ = "builtup_details"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, unique=True)
    total_carpet_sqm = Column(Float, nullable=False)
    instructional_area_sqm = Column(Float, nullable=False)
    administrative_area_sqm = Column(Float, nullable=False)
    amenities_area_sqm = Column(Float, nullable=False)

    application = relationship("Application", back_populates="builtup_detail")
