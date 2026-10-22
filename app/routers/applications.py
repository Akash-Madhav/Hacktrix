import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.application import Application, Program, LandDetail, BuiltupDetail
from app.models.document import Document
from app.models.validation import ValidationRun
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationDetailResponse,
    ProgramResponse,
    LandDetailResponse,
    BuiltupDetailResponse
)
from app.schemas.verdict import ApplicationStatusSummary
from app.services.verdict import get_application_status_summary

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("", response_model=ApplicationDetailResponse, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """Creates a new AICTE institutional application profile and provisions test scenario documents if requested."""
    from app.services.institution_service import create_and_provision_institution
    
    # Auto-generate application number if missing or empty
    if not payload.application_number or not payload.application_number.strip():
        payload.application_number = f"AICTE/2024/APP-{uuid.uuid4().hex[:6].upper()}"

    existing = db.query(Application).filter(Application.application_number == payload.application_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Application number '{payload.application_number}' already exists")

    app = create_and_provision_institution(db, payload)

    doc_count = db.query(Document).filter(Document.application_id == app.id).count()
    latest_run = (
        db.query(ValidationRun)
        .filter(ValidationRun.application_id == app.id)
        .order_by(ValidationRun.run_timestamp.desc())
        .first()
    )

    return ApplicationDetailResponse(
        id=app.id,
        application_number=app.application_number,
        institution_name=app.institution_name,
        institution_type=app.institution_type,
        application_type=app.application_type,
        state=app.state,
        district=app.district,
        address=app.address,
        created_at=app.created_at,
        updated_at=app.updated_at,
        programs=[ProgramResponse.from_orm(p) for p in app.programs],
        land_detail=LandDetailResponse.from_orm(app.land_detail) if app.land_detail else None,
        builtup_detail=BuiltupDetailResponse.from_orm(app.builtup_detail) if app.builtup_detail else None,
        uploaded_document_count=doc_count,
        latest_run_id=latest_run.id if latest_run else None,
        latest_readiness=latest_run.overall_readiness if latest_run else None
    )

@router.get("", response_model=List[ApplicationResponse])
def list_applications(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lists all submitted applications."""
    return db.query(Application).offset(skip).limit(limit).all()

@router.get("/{application_id}", response_model=ApplicationDetailResponse)
def get_application(application_id: str, db: Session = Depends(get_db)):
    """Retrieves full application details with programs and norms data."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    doc_count = db.query(Document).filter(Document.application_id == application_id).count()
    latest_run = (
        db.query(ValidationRun)
        .filter(ValidationRun.application_id == application_id)
        .order_by(ValidationRun.run_timestamp.desc())
        .first()
    )

    return ApplicationDetailResponse(
        id=app.id,
        application_number=app.application_number,
        institution_name=app.institution_name,
        institution_type=app.institution_type,
        application_type=app.application_type,
        state=app.state,
        district=app.district,
        address=app.address,
        created_at=app.created_at,
        updated_at=app.updated_at,
        programs=[ProgramResponse.from_orm(p) for p in app.programs],
        land_detail=LandDetailResponse.from_orm(app.land_detail) if app.land_detail else None,
        builtup_detail=BuiltupDetailResponse.from_orm(app.builtup_detail) if app.builtup_detail else None,
        uploaded_document_count=doc_count,
        latest_run_id=latest_run.id if latest_run else None,
        latest_readiness=latest_run.overall_readiness if latest_run else None
    )

@router.get("/{application_id}/status", response_model=ApplicationStatusSummary)
def get_application_status(application_id: str, db: Session = Depends(get_db)):
    """
    Returns live operational status dashboard:
    documents count, missing mandatory documents count, latest validation readiness.
    """
    try:
        return get_application_status_summary(db, application_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
