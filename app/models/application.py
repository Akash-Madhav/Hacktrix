from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True)
    application_number = Column(String(64), unique=True, nullable=False, index=True)
    institution_name = Column(String(255), nullable=False)
    institution_type = Column(String(64), nullable=False, default="NEW_TECHNICAL_INSTITUTION")
    application_type = Column(String(64), nullable=False, default="NEW_INSTITUTION")
    state = Column(String(64), nullable=False)
    district = Column(String(64), nullable=False)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    runs = relationship("ValidationRun", back_populates="application", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="application", cascade="all, delete-orphan")
    land_detail = relationship("LandDetail", back_populates="application", uselist=False, cascade="all, delete-orphan")
    builtup_detail = relationship("BuiltupDetail", back_populates="application", uselist=False, cascade="all, delete-orphan")
    verification_records = relationship("VerificationRecord", back_populates="application", cascade="all, delete-orphan")


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
