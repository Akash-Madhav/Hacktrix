from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow)
    rule_version = Column(String(32), default="APH-2024-V1.0")
    engine_mode = Column(String(32), default="DETERMINISTIC_RULES") # DETERMINISTIC_RULES | HYBRID_WITH_LLM
    status = Column(String(32), default="COMPLETED") # RUNNING | COMPLETED | FAILED
    overall_readiness = Column(String(32), default="PENDING") # READY_FOR_REVIEW | HAS_ISSUES | INCOMPLETE | CRITICAL_ISSUES
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="runs")
    findings = relationship("Finding", back_populates="run", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), ForeignKey("validation_runs.id"), nullable=False)
    rule_id = Column(String(32), nullable=False) # e.g. V01, V04, V05, V07, V10, V12, V13
    check_name = Column(String(128), nullable=False)
    category = Column(String(32), nullable=False) # COMPLETENESS | VALIDITY | CONSISTENCY | TAMPERING_INDICATORS | VERIFICATION
    severity = Column(String(32), nullable=False) # CRITICAL | MAJOR | MINOR | ADVISORY_OBSERVATION
    outcome = Column(String(32), nullable=False) # PASS | FAIL | UNKNOWN | FLAG
    explanation = Column(Text, nullable=False)
    rule_citation = Column(String(255), nullable=True) # e.g. APH 2024-25 Clause 1.4.1
    evidence_json = Column(Text, nullable=True) # JSON with exact matched numbers/spans
    source_document_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ValidationRun", back_populates="findings")


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    verification_type = Column(String(64), nullable=False) # LAND_REGISTRY | MUNICIPAL_BUILDING_APPROVAL | FIRE_SAFETY_PORTAL
    external_reference_id = Column(String(128), nullable=False)
    simulated_status = Column(String(32), nullable=False) # MATCH | MISMATCH | NOT_FOUND
    simulated_response_json = Column(Text, nullable=True)
    watermark = Column(String(128), default="SIMULATED DATA - DEMONSTRATION USE ONLY")
    verified_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="verification_records")
