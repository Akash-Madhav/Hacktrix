import os
import uuid
import shutil
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.application import Application
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentDetailResponse
from app.services.extractor import compute_sha256, extract_text_from_pdf
from app.services.tamper import analyze_pdf_metadata_and_integrity

router = APIRouter(tags=["Documents"])

VALID_DOCUMENT_TYPES = [
    "LAND_REGISTRATION",
    "BUILDING_PLAN_APPROVAL",
    "FIRE_SAFETY_NOC",
    "AFFIDAVIT_TRUST",
    "ARCHITECT_CERTIFICATE",
    "SUPPORTING_ATTACHMENT"
]

@router.post("/applications/{application_id}/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a statutory document PDF for an application:
    - Stores file on disk
    - Computes cryptographic SHA-256 hash
    - Extracts raw text using PyMuPDF / pypdf
    - Analyzes metadata and structural stream
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if document_type not in VALID_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document_type. Allowed types: {', '.join(VALID_DOCUMENT_TYPES)}"
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported")

    doc_id = str(uuid.uuid4())
    app_dir = settings.UPLOAD_DIR / application_id
    app_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = app_dir / f"{doc_id}_{file.filename}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    sha256 = compute_sha256(str(file_path))
    text_content = extract_text_from_pdf(str(file_path))
    
    # Run preliminary integrity check
    integrity = analyze_pdf_metadata_and_integrity(str(file_path), document_type)

    doc = Document(
        id=doc_id,
        application_id=application_id,
        document_type=document_type,
        file_path=str(file_path),
        original_filename=file.filename,
        sha256_hash=sha256,
        upload_status="PROCESSED",
        mime_type="application/pdf",
        file_size_bytes=file_size,
        extracted_text=text_content,
        metadata_json=json.dumps(integrity)
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return DocumentResponse(
        id=doc.id,
        application_id=doc.application_id,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        sha256_hash=doc.sha256_hash,
        upload_status=doc.upload_status,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        created_at=doc.created_at,
        extracted_text_preview=text_content[:300] if text_content else None
    )

@router.get("/applications/{application_id}/documents", response_model=List[DocumentResponse])
def list_application_documents(application_id: str, db: Session = Depends(get_db)):
    """Lists all uploaded documents for an application."""
    docs = db.query(Document).filter(Document.application_id == application_id).all()
    results = []
    for d in docs:
        results.append(DocumentResponse(
            id=d.id,
            application_id=d.application_id,
            document_type=d.document_type,
            original_filename=d.original_filename,
            sha256_hash=d.sha256_hash,
            upload_status=d.upload_status,
            mime_type=d.mime_type,
            file_size_bytes=d.file_size_bytes,
            created_at=d.created_at,
            extracted_text_preview=d.extracted_text[:300] if d.extracted_text else None
        ))
    return results

@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """Retrieves full text and metadata for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentDetailResponse(
        id=doc.id,
        application_id=doc.application_id,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        sha256_hash=doc.sha256_hash,
        upload_status=doc.upload_status,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        created_at=doc.created_at,
        extracted_text_preview=doc.extracted_text[:300] if doc.extracted_text else None,
        extracted_text=doc.extracted_text,
        metadata_json=doc.metadata_json
    )
