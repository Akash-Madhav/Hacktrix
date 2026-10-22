import json
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.document import Document
from app.models.validation import ValidationRun, Finding
from app.schemas.verdict import (
    FinalJudgmentVerdict,
    ApplicationStatusSummary,
    ActionableChecklist,
    CategoryVerdict,
    MissingItemDetail,
    FailedCheckDetail,
    TamperObservationDetail
)
from app.services.rules import MANDATORY_DOCUMENTS

def compute_application_verdict(db: Session, run_id: str) -> FinalJudgmentVerdict:
    """
    Synthesizes all findings from a validation run into an authoritative, actionable
    judgment with category breakdowns and clear statutory readiness status.
    """
    run = db.query(ValidationRun).filter(ValidationRun.id == run_id).first()
    if not run:
        raise ValueError(f"ValidationRun {run_id} not found")
        
    app = db.query(Application).filter(Application.id == run.application_id).first()
    if not app:
        raise ValueError(f"Application for run {run_id} not found")

    findings = db.query(Finding).filter(Finding.run_id == run_id).all()

    # Category buckets
    categories = ["COMPLETENESS", "VALIDITY", "CONSISTENCY", "TAMPERING_INDICATORS", "VERIFICATION"]
    cat_counts = {c: {"total": 0, "pass": 0, "fail": 0, "flag": 0} for c in categories}
    
    missing_docs: List[MissingItemDetail] = []
    critical_deficiencies: List[FailedCheckDetail] = []
    tampering_flags: List[TamperObservationDetail] = []
    advisories: List[FailedCheckDetail] = []
    passed_checks: List[str] = []

    has_critical_fail = False
    has_major_fail = False
    has_missing_docs = False
    has_tamper_flag = False

    for f in findings:
        cat = f.category if f.category in cat_counts else "VALIDITY"
        cat_counts[cat]["total"] += 1
        
        if f.outcome == "PASS":
            cat_counts[cat]["pass"] += 1
            passed_checks.append(f"{f.rule_id}: {f.check_name} — {f.explanation}")
        elif f.outcome in ["FAIL", "UNKNOWN"]:
            cat_counts[cat]["fail"] += 1
            
            if f.severity == "CRITICAL":
                has_critical_fail = True
                if f.category == "COMPLETENESS":
                    has_missing_docs = True
                    # Find matching mandate
                    desc = "Statutory requirement per AICTE Approval Process Handbook"
                    for m in MANDATORY_DOCUMENTS:
                        if m["type"] in f.id:
                            desc = m["description"]
                            break
                    missing_docs.append(MissingItemDetail(
                        item_type="DOCUMENT",
                        name=f.check_name.replace("Mandatory Document: ", ""),
                        description=f.explanation,
                        regulatory_mandate=f.rule_citation or "AICTE APH 2024-25",
                        impact="Application cannot be recommended to Scrutiny Committee without this statutory document."
                    ))
                else:
                    critical_deficiencies.append(FailedCheckDetail(
                        rule_id=f.rule_id,
                        check_name=f.check_name,
                        severity=f.severity,
                        category=f.category,
                        clause=f.rule_citation,
                        finding=f.explanation,
                        evidence=json.loads(f.evidence_json) if f.evidence_json else None,
                        required_remedy="Applicant institution must rectify this deficiency immediately to comply with statutory norms."
                    ))
            elif f.severity == "MAJOR":
                has_major_fail = True
                critical_deficiencies.append(FailedCheckDetail(
                    rule_id=f.rule_id,
                    check_name=f.check_name,
                    severity=f.severity,
                    category=f.category,
                    clause=f.rule_citation,
                    finding=f.explanation,
                    evidence=json.loads(f.evidence_json) if f.evidence_json else None,
                    required_remedy="Submit corrigendum or updated certified documents to reconcile discrepancy."
                ))
            else:
                advisories.append(FailedCheckDetail(
                    rule_id=f.rule_id,
                    check_name=f.check_name,
                    severity=f.severity,
                    category=f.category,
                    clause=f.rule_citation,
                    finding=f.explanation,
                    evidence=json.loads(f.evidence_json) if f.evidence_json else None,
                    required_remedy="Review and keep supporting records available for inspection."
                ))

        elif f.outcome == "FLAG":
            cat_counts[cat]["flag"] += 1
            has_tamper_flag = True
            doc_name = f.check_name.split("[")[-1].replace("]", "") if "[" in f.check_name else "Document"
            tampering_flags.append(TamperObservationDetail(
                rule_id=f.rule_id,
                document_name=doc_name,
                observation_type=f.check_name,
                severity=f.severity,
                details=f.explanation,
                recommendation="Physical verification of original certificate and cross-checking with state portal recommended."
            ))

    # Determine overall readiness
    if has_critical_fail and has_missing_docs:
        overall_readiness = "INCOMPLETE"
        verdict_headline = "DEFICIENT: Application Incomplete with Missing Statutory Documents"
        verdict_explanation = (
            f"The application for '{app.institution_name}' cannot be approved in its current state. "
            f"There are {len(missing_docs)} mandatory statutory document(s) missing, alongside "
            f"{len(critical_deficiencies)} critical norm non-compliances."
        )
    elif has_critical_fail:
        overall_readiness = "CRITICAL_ISSUES"
        verdict_headline = "DEFICIENT: Critical Statutory Norm Failures Detected"
        verdict_explanation = (
            f"The application for '{app.institution_name}' fails fundamental statutory minimums (e.g. land area or built-up space). "
            f"{len(critical_deficiencies)} critical/major deficiencies require rectification."
        )
    elif has_major_fail or has_tamper_flag:
        overall_readiness = "HAS_ISSUES"
        verdict_headline = "ACTION REQUIRED: Document Inconsistencies or Integrity Flags Detected"
        verdict_explanation = (
            f"The application for '{app.institution_name}' has met basic completeness but exhibits "
            f"{len(critical_deficiencies)} major discrepancy(ies) and {len(tampering_flags)} digital integrity observation(s). "
            "Scrutiny officer attention is required prior to committee hearing."
        )
    else:
        overall_readiness = "READY_FOR_REVIEW"
        verdict_headline = "COMPLIANT: Application Dossier Complete and Meets AICTE Norms"
        verdict_explanation = (
            f"The application for '{app.institution_name}' satisfies all examined AICTE APH 2024-25 procedural requirements. "
            "All mandatory documents are present, land and built-up norms are met, and cross-consistency is verified. "
            "Ready for onward submission to the AICTE Scrutiny Committee."
        )

    # Calculate compliance score
    total_checks = len(findings)
    score_pct = round((len(passed_checks) / total_checks * 100), 1) if total_checks > 0 else 0.0

    # Build category breakdown
    category_breakdown: Dict[str, CategoryVerdict] = {}
    for cat in categories:
        counts = cat_counts[cat]
        cat_status = "PASS"
        if counts["fail"] > 0:
            cat_status = "FAIL"
        elif counts["flag"] > 0:
            cat_status = "FLAG"
        elif counts["total"] == 0:
            cat_status = "NOT_APPLICABLE"
            
        summary_text = f"{counts['pass']} of {counts['total']} checks passed."
        if counts["fail"] > 0:
            summary_text += f" {counts['fail']} non-compliances recorded."
        if counts["flag"] > 0:
            summary_text += f" {counts['flag']} integrity observations flagged."

        category_breakdown[cat] = CategoryVerdict(
            category_name=cat,
            status=cat_status,
            summary=summary_text,
            total_checks=counts["total"],
            passed_checks=counts["pass"],
            failed_checks=counts["fail"] + counts["flag"]
        )

    # Persist readiness on run object
    run.overall_readiness = overall_readiness
    db.commit()

    return FinalJudgmentVerdict(
        application_id=app.id,
        application_number=app.application_number,
        institution_name=app.institution_name,
        institution_type=app.institution_type,
        state=app.state,
        district=app.district,
        run_id=run.id,
        run_timestamp=run.run_timestamp,
        rule_version=run.rule_version,
        engine_mode=run.engine_mode,
        overall_readiness=overall_readiness,
        readiness_score_pct=score_pct,
        verdict_headline=verdict_headline,
        verdict_explanation=verdict_explanation,
        category_breakdown=category_breakdown,
        actionable_checklist=ActionableChecklist(
            missing_mandatory_documents=missing_docs,
            critical_and_major_deficiencies=critical_deficiencies,
            tampering_integrity_flags=tampering_flags,
            advisories_and_warnings=advisories,
            passed_compliance_checks=passed_checks
        )
    )

def get_application_status_summary(db: Session, application_id: str) -> ApplicationStatusSummary:
    """
    Returns quick operational status overview for an application.
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError(f"Application {application_id} not found")

    docs = db.query(Document).filter(Document.application_id == application_id).all()
    runs = db.query(ValidationRun).filter(ValidationRun.application_id == application_id).order_by(ValidationRun.run_timestamp.desc()).all()

    uploaded_types = {d.document_type for d in docs}
    required_types = {m["type"] for m in MANDATORY_DOCUMENTS}
    missing_count = len(required_types - uploaded_types)

    latest_run = runs[0] if runs else None
    
    current_status = "DRAFT"
    if docs and not runs:
        current_status = "DOCUMENTS_UPLOADED"
    elif latest_run:
        if latest_run.overall_readiness == "READY_FOR_REVIEW":
            current_status = "VALIDATION_COMPLETED"
        else:
            current_status = "ACTION_REQUIRED"

    return ApplicationStatusSummary(
        application_id=app.id,
        application_number=app.application_number,
        institution_name=app.institution_name,
        current_status=current_status,
        overall_readiness=latest_run.overall_readiness if latest_run else "PENDING",
        documents_count=len(docs),
        required_documents_count=len(MANDATORY_DOCUMENTS),
        missing_documents_count=missing_count,
        validation_runs_count=len(runs),
        latest_run_id=latest_run.id if latest_run else None,
        latest_run_timestamp=latest_run.run_timestamp if latest_run else None,
        last_updated=app.updated_at
    )
