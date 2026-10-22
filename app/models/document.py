from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False)
    document_type = Column(String(64), nullable=False)  # e.g., LAND_REGISTRATION, BUILDING_PLAN_APPROVAL, etc.
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    upload_status = Column(String(32), default="PROCESSED")
    mime_type = Column(String(64), default="application/pdf")
    file_size_bytes = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="documents")
