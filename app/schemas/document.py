from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: str
    application_id: str
    document_type: str
    original_filename: str
    sha256_hash: str
    upload_status: str
    mime_type: str
    file_size_bytes: int
    created_at: datetime
    extracted_text_preview: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    extracted_text: Optional[str] = None
    metadata_json: Optional[str] = None
