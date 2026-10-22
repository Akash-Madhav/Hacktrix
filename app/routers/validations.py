import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.application import Application
from app.models.validation import ValidationRun, Finding
from app.schemas.validation import ValidationRunCreate, ValidationRunResponse, FindingResponse
from app.schemas.verdict import FinalJudgmentVerdict
from app.services.rules import run_deterministic_validation_engine
from app.services.verdict import compute_application_verdict

router = APIRouter(tags=["Validation & Verdict"])

@router.post("/applications/{application_id}/validate", response_model=ValidationRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_validation_run(
    application_id: str,
    payload: ValidationRunCreate = ValidationRunCreate(),
    db: Session = Depends(get_db)
):
    """
    Triggers an end-to-end statutory compliance validation run:
    - V01: Completeness / Mandatory Checklist
    - V04: Land Norms (area & contiguity)
    - V05: Built-up Space Norms
    - V07: Cross-Document Consistency
    - V10: Authority Verifications (simulated)
    - V12: Metadata Anomaly Analysis (tampering detection)
    - V13: Revision & Incremental Save Analysis (tampering detection)
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    run_id = str(uuid.uuid4())
    run = ValidationRun(
        id=run_id,
        application_id=application_id,
        run_timestamp=datetime.utcnow(),
        rule_version="APH-2024-V1.0",
        engine_mode=payload.engine_mode,
        status="RUNNING",
        overall_readiness="PENDING"
    )
    db.add(run)
    db.commit()

    # Execute rules
    try:
        findings = run_deterministic_validation_engine(db, application_id, run_id)
        for f in findings:
            db.add(f)
        
        run.status = "COMPLETED"
        db.commit()

        # Compute initial verdict to update run.overall_readiness
        compute_application_verdict(db, run_id)
        db.refresh(run)

    except Exception as e:
        run.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Validation run failed: {str(e)}")

    all_findings = db.query(Finding).filter(Finding.run_id == run_id).all()

    return ValidationRunResponse(
        id=run.id,
        application_id=run.application_id,
        run_timestamp=run.run_timestamp,
        rule_version=run.rule_version,
        engine_mode=run.engine_mode,
        status=run.status,
        overall_readiness=run.overall_readiness,
        findings_count=len(all_findings),
        findings=[FindingResponse.from_orm(f) for f in all_findings]
    )

@router.get("/runs/{run_id}", response_model=ValidationRunResponse)
def get_validation_run(run_id: str, db: Session = Depends(get_db)):
    """Retrieves all statutory findings for a validation run."""
    run = db.query(ValidationRun).filter(ValidationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Validation run not found")

    findings = db.query(Finding).filter(Finding.run_id == run_id).all()

    return ValidationRunResponse(
        id=run.id,
        application_id=run.application_id,
        run_timestamp=run.run_timestamp,
        rule_version=run.rule_version,
        engine_mode=run.engine_mode,
        status=run.status,
        overall_readiness=run.overall_readiness,
        findings_count=len(findings),
        findings=[FindingResponse.from_orm(f) for f in findings]
    )

@router.get("/runs/{run_id}/verdict", response_model=FinalJudgmentVerdict)
def get_run_verdict(run_id: str, db: Session = Depends(get_db)):
    """
    Returns the Final Judgment Verdict for the scrutiny committee:
    - Overall statutory readiness (READY_FOR_REVIEW | HAS_ISSUES | INCOMPLETE | CRITICAL_ISSUES)
    - Compliance score percentage
    - Breakdown by Category (Completeness, Validity, Consistency, Tampering, Verification)
    - Actionable Checklist of WHAT IS MISSING, critical deficiencies, and digital integrity flags
    """
    try:
        return compute_application_verdict(db, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
