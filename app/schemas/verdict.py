from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class MissingItemDetail(BaseModel):
    item_type: str # DOCUMENT | DATA_FIELD
    name: str
    description: str
    regulatory_mandate: str
    impact: str

class FailedCheckDetail(BaseModel):
    rule_id: str
    check_name: str
    severity: str
    category: str
    clause: Optional[str] = None
    finding: str
    evidence: Optional[Dict[str, Any]] = None
    required_remedy: str

class TamperObservationDetail(BaseModel):
    rule_id: str
    document_name: str
    observation_type: str
    severity: str
    details: str
    recommendation: str

class CategoryVerdict(BaseModel):
    category_name: str
    status: str # PASS | FAIL | INCOMPLETE | FLAG | NOT_APPLICABLE
    summary: str
    total_checks: int
    passed_checks: int
    failed_checks: int

class ApplicationStatusSummary(BaseModel):
    application_id: str
    application_number: str
    institution_name: str
    current_status: str # DRAFT | DOCUMENTS_UPLOADED | VALIDATION_COMPLETED | ACTION_REQUIRED
    overall_readiness: str # READY_FOR_REVIEW | HAS_ISSUES | INCOMPLETE | CRITICAL_ISSUES
    documents_count: int
    required_documents_count: int
    missing_documents_count: int
    validation_runs_count: int
    latest_run_id: Optional[str] = None
    latest_run_timestamp: Optional[datetime] = None
    last_updated: datetime

class ActionableChecklist(BaseModel):
    missing_mandatory_documents: List[MissingItemDetail] = []
    critical_and_major_deficiencies: List[FailedCheckDetail] = []
    tampering_integrity_flags: List[TamperObservationDetail] = []
    advisories_and_warnings: List[FailedCheckDetail] = []
    passed_compliance_checks: List[str] = []

class FinalJudgmentVerdict(BaseModel):
    application_id: str
    application_number: str
    institution_name: str
    institution_type: str
    state: str
    district: str
    run_id: str
    run_timestamp: datetime
    rule_version: str
    engine_mode: str
    
    # The Core Judgment
    overall_readiness: str # READY_FOR_REVIEW | HAS_ISSUES | INCOMPLETE | CRITICAL_ISSUES
    readiness_score_pct: float
    verdict_headline: str
    verdict_explanation: str
    
    # Status by Category
    category_breakdown: Dict[str, CategoryVerdict]
    
    # Complete What's Missing and Status Action Items
    actionable_checklist: ActionableChecklist
    
    # SLM (Qwen 2.5) Scrutiny Analysis
    slm_analysis: Optional[Dict[str, Any]] = None
    
    # Statutory Safeguard
    statutory_disclaimer: str = (
        "BluePill is an automated assistive scrutiny tool. All findings, readiness classifications, "
        "and metadata observations constitute decision-support advisory analyses. Final statutory "
        "approval or deficiency determinations rest solely with the competent AICTE Scrutiny Committee."
    )
