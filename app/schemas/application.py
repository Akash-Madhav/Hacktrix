from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class ProgramBase(BaseModel):
    program_name: str
    level: str = "UG"
    approved_intake: int = 60

class ProgramResponse(ProgramBase):
    id: str
    class Config:
        from_attributes = True

class LandDetailBase(BaseModel):
    total_area_acres: float
    is_single_plot: bool = True
    ownership_type: str = "OWNED_GOVERNMENT_REGISTERED"
    survey_khasra_no: Optional[str] = None
    land_registration_date: Optional[str] = None

class LandDetailResponse(LandDetailBase):
    id: str
    class Config:
        from_attributes = True

class BuiltupDetailBase(BaseModel):
    total_carpet_sqm: float
    instructional_area_sqm: float
    administrative_area_sqm: float
    amenities_area_sqm: float

class BuiltupDetailResponse(BuiltupDetailBase):
    id: str
    class Config:
        from_attributes = True

class ApplicationBase(BaseModel):
    application_number: str
    institution_name: str
    institution_type: str = "NEW_TECHNICAL_INSTITUTION"
    application_type: str = "NEW_INSTITUTION"
    state: str
    district: str
    address: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    programs: List[ProgramBase] = []
    land_detail: Optional[LandDetailBase] = None
    builtup_detail: Optional[BuiltupDetailBase] = None
    test_scenario: Optional[str] = "COMPLIANT" # "COMPLIANT", "DEFICIENT_LAND", "MISSING_DOCS", "TAMPERED_PDF", "NONE"
    auto_validate: Optional[bool] = True

class ApplicationResponse(ApplicationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ApplicationDetailResponse(ApplicationResponse):
    programs: List[ProgramResponse] = []
    land_detail: Optional[LandDetailResponse] = None
    builtup_detail: Optional[BuiltupDetailResponse] = None
    uploaded_document_count: int = 0
    latest_run_id: Optional[str] = None
    latest_readiness: Optional[str] = None
