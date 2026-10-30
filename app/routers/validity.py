from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.validity import ValidityRecord
from app.models.application import Application
from app.services.clock_service import clock_service

router = APIRouter(prefix="/api/validity", tags=["Validity Registry (Lease/NOC Expiry)"])

@router.get("")
def list_validity_records(
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ValidityRecord)
    if status:
        query = query.filter(ValidityRecord.status == status)
    if document_type:
        query = query.filter(ValidityRecord.document_type == document_type)

    records = query.order_by(ValidityRecord.expiry_date.asc()).all()
    sim_now = clock_service.now(db)

    results = []
    for r in records:
        days_left = (r.expiry_date.date() - sim_now.date()).days
        app = db.query(Application).filter(Application.institution_permanent_id == r.institution_id).first()

        results.append({
            "id": r.id,
            "institution_id": r.institution_id,
            "institution_name": app.institution_name if app else f"Institution {r.institution_id}",
            "region": app.region if app else "Western",
            "document_type": r.document_type,
            "certificate_number": r.certificate_number,
            "issuing_authority": r.issuing_authority,
            "valid_from": r.valid_from.isoformat() if r.valid_from else None,
            "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
            "days_until_expiry": days_left,
            "status": r.status,
            "last_reminder_offset": r.last_reminder_offset,
            "is_overdue": days_left <= 0
        })
    return results
