import json
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.document import Document
from app.models.validation import Finding, ValidationRun, VerificationRecord
from app.services.tamper import analyze_pdf_metadata_and_integrity
from app.services.extractor import extract_structured_fields

MANDATORY_DOCUMENTS = [
    {
        "type": "LAND_REGISTRATION",
        "name": "Registered Land Sale Deed / Gift Deed / Govt Lease Deed",
        "clause": "AICTE Approval Process Handbook (APH) 2024-25, Clause 1.4.1 & Appendix 4.1",
        "description": "Proof of ownership or registered government lease of minimum prescribed land area in the name of the Applicant Trust/Society."
    },
    {
        "type": "BUILDING_PLAN_APPROVAL",
        "name": "Approved Building Plan from Competent Municipal / Town Planning Authority",
        "clause": "AICTE APH 2024-25, Clause 1.4.2 & Appendix 4.2",
        "description": "Sanctioned master plan and floor layout showing instructional, administrative, and amenities carpet areas."
    },
    {
        "type": "FIRE_SAFETY_NOC",
        "name": "Fire Safety Certificate / NOC from State Fire Department",
        "clause": "AICTE APH 2024-25, Clause 1.4.3 & Appendix 4.3",
        "description": "Valid Fire Safety NOC issued by the Chief Fire Officer / Competent State Disaster Management Authority."
    },
    {
        "type": "AFFIDAVIT_TRUST",
        "name": "Affidavit on Non-Judicial Stamp Paper (Trust / Society Registration)",
        "clause": "AICTE APH 2024-25, Appendix 1.1",
        "description": "Notarized affidavit by Chairman/Secretary stating establishment of institution, non-commercial use, and non-encumbrance."
    },
    {
        "type": "ARCHITECT_CERTIFICATE",
        "name": "Architect Certificate of Barrier-Free Built-up Environment",
        "clause": "AICTE APH 2024-25, Appendix 4.4",
        "description": "Certified structural and accessibility report by a registered architect with Council of Architecture registration number."
    }
]

def run_deterministic_validation_engine(db: Session, application_id: str, run_id: str) -> List[Finding]:
    """
    Executes AICTE deterministic compliance rules:
    - V01: Completeness (Mandatory document checklist)
    - V04: Land Norms (Area and single plot mandate)
    - V05: Built-up Space Norms (Carpet and instructional area)
    - V07: Cross-Document Consistency (Application vs Document evidence)
    - V10: Simulated Statutory Authority Verification
    - V12: PDF Metadata Anomaly Analysis (Tampering indication)
    - V13: PDF Revision & Incremental Save Analysis (Tampering indication)
    """
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError(f"Application {application_id} not found")

    docs = db.query(Document).filter(Document.application_id == application_id).all()
    docs_by_type: Dict[str, Document] = {d.document_type: d for d in docs}
    
    findings: List[Finding] = []

    # =========================================================================
    # RULE V01: Mandatory Document Checklist (Completeness)
    # =========================================================================
    for req in MANDATORY_DOCUMENTS:
        doc_type = req["type"]
        doc = docs_by_type.get(doc_type)
        if not doc:
            findings.append(Finding(
                id=f"{run_id}-V01-{doc_type}",
                run_id=run_id,
                rule_id="V01",
                check_name=f"Mandatory Document: {req['name']}",
                category="COMPLETENESS",
                severity="CRITICAL",
                outcome="FAIL",
                explanation=f"Required statutory document '{req['name']}' is missing from application dossier.",
                rule_citation=req["clause"],
                evidence_json=json.dumps({"document_type": doc_type, "status": "MISSING", "mandate": req["description"]}),
                source_document_id=None
            ))
        else:
            findings.append(Finding(
                id=f"{run_id}-V01-{doc_type}",
                run_id=run_id,
                rule_id="V01",
                check_name=f"Mandatory Document: {req['name']}",
                category="COMPLETENESS",
                severity="MINOR",
                outcome="PASS",
                explanation=f"Mandatory document '{req['name']}' uploaded and verified ({doc.original_filename}).",
                rule_citation=req["clause"],
                evidence_json=json.dumps({"document_id": doc.id, "filename": doc.original_filename, "sha256": doc.sha256_hash}),
                source_document_id=doc.id
            ))

    # =========================================================================
    # RULE V04: Land Norms (APH 2024-25 Clause 1.4.1)
    # =========================================================================
    land = app.land_detail
    MIN_LAND_ACRES = 7.5 # AICTE standard for technical engineering institute in normal/rural category
    if not land:
        findings.append(Finding(
            id=f"{run_id}-V04-DATA",
            run_id=run_id,
            rule_id="V04",
            check_name="Land Norms: Application Data Exists",
            category="VALIDITY",
            severity="CRITICAL",
            outcome="FAIL",
            explanation="Land detail record is completely absent in the institutional application profile.",
            rule_citation="AICTE APH 2024-25, Clause 1.4.1",
            evidence_json=json.dumps({"error": "No land_detail record"}),
            source_document_id=None
        ))
    else:
        # Check area
        if land.total_area_acres >= MIN_LAND_ACRES:
            findings.append(Finding(
                id=f"{run_id}-V04-AREA",
                run_id=run_id,
                rule_id="V04",
                check_name="Land Norms: Minimum Area Requirement",
                category="VALIDITY",
                severity="CRITICAL",
                outcome="PASS",
                explanation=f"Total declared land area ({land.total_area_acres} acres) satisfies the AICTE minimum norm of {MIN_LAND_ACRES} acres.",
                rule_citation="AICTE APH 2024-25, Appendix 4.1",
                evidence_json=json.dumps({"declared_acres": land.total_area_acres, "minimum_required_acres": MIN_LAND_ACRES}),
                source_document_id=None
            ))
        else:
            findings.append(Finding(
                id=f"{run_id}-V04-AREA",
                run_id=run_id,
                rule_id="V04",
                check_name="Land Norms: Minimum Area Requirement",
                category="VALIDITY",
                severity="CRITICAL",
                outcome="FAIL",
                explanation=f"Total declared land area ({land.total_area_acres} acres) is below the statutory minimum of {MIN_LAND_ACRES} acres for this category.",
                rule_citation="AICTE APH 2024-25, Appendix 4.1",
                evidence_json=json.dumps({"declared_acres": land.total_area_acres, "minimum_required_acres": MIN_LAND_ACRES, "deficit_acres": MIN_LAND_ACRES - land.total_area_acres}),
                source_document_id=None
            ))

        # Check single contiguous plot
        if land.is_single_plot:
            findings.append(Finding(
                id=f"{run_id}-V04-PLOT",
                run_id=run_id,
                rule_id="V04",
                check_name="Land Norms: Single Contiguous Plot Mandate",
                category="VALIDITY",
                severity="MAJOR",
                outcome="PASS",
                explanation="Land is declared as a single contiguous plot with no intervening public roads or private properties.",
                rule_citation="AICTE APH 2024-25, Clause 1.4.1(b)",
                evidence_json=json.dumps({"is_single_plot": True}),
                source_document_id=None
            ))
        else:
            findings.append(Finding(
                id=f"{run_id}-V04-PLOT",
                run_id=run_id,
                rule_id="V04",
                check_name="Land Norms: Single Contiguous Plot Mandate",
                category="VALIDITY",
                severity="MAJOR",
                outcome="FAIL",
                explanation="Non-contiguous land declared. AICTE mandates technical institution land to be a single contiguous parcel.",
                rule_citation="AICTE APH 2024-25, Clause 1.4.1(b)",
                evidence_json=json.dumps({"is_single_plot": False}),
                source_document_id=None
            ))

    # =========================================================================
    # RULE V05: Built-up Space Norms (APH 2024-25 Clause 1.4.2)
    # =========================================================================
    built = app.builtup_detail
    MIN_TOTAL_CARPET = 6000.0
    MIN_INSTRUCTIONAL = 3000.0
    if not built:
        findings.append(Finding(
            id=f"{run_id}-V05-DATA",
            run_id=run_id,
            rule_id="V05",
            check_name="Built-up Norms: Application Data Exists",
            category="VALIDITY",
            severity="CRITICAL",
            outcome="FAIL",
            explanation="Built-up infrastructure schedule is absent in application.",
            rule_citation="AICTE APH 2024-25, Clause 1.4.2",
            evidence_json=json.dumps({"error": "No builtup_detail record"}),
            source_document_id=None
        ))
    else:
        if built.total_carpet_sqm >= MIN_TOTAL_CARPET and built.instructional_area_sqm >= MIN_INSTRUCTIONAL:
            findings.append(Finding(
                id=f"{run_id}-V05-SPACE",
                run_id=run_id,
                rule_id="V05",
                check_name="Built-up Area Norms: Carpet & Instructional Area",
                category="VALIDITY",
                severity="MAJOR",
                outcome="PASS",
                explanation=(
                    f"Built-up area declared ({built.total_carpet_sqm} sq.m carpet, {built.instructional_area_sqm} sq.m instructional) "
                    f"meets or exceeds statutory norms ({MIN_TOTAL_CARPET} sq.m / {MIN_INSTRUCTIONAL} sq.m)."
                ),
                rule_citation="AICTE APH 2024-25, Appendix 4.2",
                evidence_json=json.dumps({
                    "total_carpet_sqm": built.total_carpet_sqm,
                    "min_required_carpet": MIN_TOTAL_CARPET,
                    "instructional_sqm": built.instructional_area_sqm,
                    "min_instructional": MIN_INSTRUCTIONAL
                }),
                source_document_id=None
            ))
        else:
            findings.append(Finding(
                id=f"{run_id}-V05-SPACE",
                run_id=run_id,
                rule_id="V05",
                check_name="Built-up Area Norms: Carpet & Instructional Area",
                category="VALIDITY",
                severity="MAJOR",
                outcome="FAIL",
                explanation=(
                    f"Declared built-up area deficiency: Carpet area is {built.total_carpet_sqm} sq.m (req: {MIN_TOTAL_CARPET}) "
                    f"or Instructional area is {built.instructional_area_sqm} sq.m (req: {MIN_INSTRUCTIONAL})."
                ),
                rule_citation="AICTE APH 2024-25, Appendix 4.2",
                evidence_json=json.dumps({
                    "total_carpet_sqm": built.total_carpet_sqm,
                    "min_required_carpet": MIN_TOTAL_CARPET,
                    "instructional_sqm": built.instructional_area_sqm,
                    "min_instructional": MIN_INSTRUCTIONAL
                }),
                source_document_id=None
            ))

    # =========================================================================
    # RULE V07: Cross-Document Consistency Analysis
    # =========================================================================
    land_doc = docs_by_type.get("LAND_REGISTRATION")
    if land_doc and land and land_doc.extracted_text:
        extracted = extract_structured_fields(land_doc.extracted_text, "LAND_REGISTRATION")
        
        # Check area consistency
        doc_acres = extracted.get("extracted_area_acres")
        if doc_acres is not None:
            diff = abs(doc_acres - land.total_area_acres)
            if diff <= 0.05:
                findings.append(Finding(
                    id=f"{run_id}-V07-LAND-AREA",
                    run_id=run_id,
                    rule_id="V07",
                    check_name="Cross-Consistency: Declared Land vs Deed Area",
                    category="CONSISTENCY",
                    severity="MAJOR",
                    outcome="PASS",
                    explanation=f"Land area in application ({land.total_area_acres} acres) matches extracted deed text ({doc_acres} acres).",
                    rule_citation="AICTE APH 2024-25, Clause 1.4.1",
                    evidence_json=json.dumps({"app_declared_acres": land.total_area_acres, "deed_extracted_acres": doc_acres, "delta": round(diff, 3)}),
                    source_document_id=land_doc.id
                ))
            else:
                findings.append(Finding(
                    id=f"{run_id}-V07-LAND-AREA",
                    run_id=run_id,
                    rule_id="V07",
                    check_name="Cross-Consistency: Declared Land vs Deed Area",
                    category="CONSISTENCY",
                    severity="MAJOR",
                    outcome="FAIL",
                    explanation=(
                        f"Discrepancy detected: Application states {land.total_area_acres} acres, but Land Registration Deed "
                        f"stipulates {doc_acres} acres (discrepancy of {round(diff, 2)} acres)."
                    ),
                    rule_citation="AICTE APH 2024-25, Clause 1.4.1",
                    evidence_json=json.dumps({"app_declared_acres": land.total_area_acres, "deed_extracted_acres": doc_acres, "delta": round(diff, 3)}),
                    source_document_id=land_doc.id
                ))
        
        # Check survey number consistency
        doc_survey = extracted.get("survey_khasra_no")
        if doc_survey and land.survey_khasra_no:
            # Clean and compare
            clean_app = "".join(filter(str.isalnum, land.survey_khasra_no.lower()))
            clean_doc = "".join(filter(str.isalnum, doc_survey.lower()))
            if clean_app in clean_doc or clean_doc in clean_app:
                findings.append(Finding(
                    id=f"{run_id}-V07-SURVEY",
                    run_id=run_id,
                    rule_id="V07",
                    check_name="Cross-Consistency: Survey/Khasra Number",
                    category="CONSISTENCY",
                    severity="MAJOR",
                    outcome="PASS",
                    explanation=f"Survey/Khasra number '{land.survey_khasra_no}' matches deed text '{doc_survey}'.",
                    rule_citation="AICTE APH 2024-25, Clause 1.4.1",
                    evidence_json=json.dumps({"app_survey": land.survey_khasra_no, "deed_survey": doc_survey}),
                    source_document_id=land_doc.id
                ))
            else:
                findings.append(Finding(
                    id=f"{run_id}-V07-SURVEY",
                    run_id=run_id,
                    rule_id="V07",
                    check_name="Cross-Consistency: Survey/Khasra Number",
                    category="CONSISTENCY",
                    severity="MAJOR",
                    outcome="FAIL",
                    explanation=f"Mismatch in Survey/Khasra identification: Application lists '{land.survey_khasra_no}', but Land Deed states '{doc_survey}'.",
                    rule_citation="AICTE APH 2024-25, Clause 1.4.1",
                    evidence_json=json.dumps({"app_survey": land.survey_khasra_no, "deed_survey": doc_survey}),
                    source_document_id=land_doc.id
                ))

    # =========================================================================
    # RULE V10: Simulated Statutory Authority Verification
    # =========================================================================
    verif_records = db.query(VerificationRecord).filter(VerificationRecord.application_id == application_id).all()
    if not verif_records:
        findings.append(Finding(
            id=f"{run_id}-V10-RECORDS",
            run_id=run_id,
            rule_id="V10",
            check_name="Statutory Authority Verification Status",
            category="VERIFICATION",
            severity="MAJOR",
            outcome="UNKNOWN",
            explanation="No external authority verification records currently logged for this application.",
            rule_citation="AICTE Inter-Departmental Verification Directive",
            evidence_json=json.dumps({"status": "PENDING_EXTERNAL_CHECKS"}),
            source_document_id=None
        ))
    else:
        for rec in verif_records:
            if rec.simulated_status == "MATCH":
                findings.append(Finding(
                    id=f"{run_id}-V10-{rec.verification_type}",
                    run_id=run_id,
                    rule_id="V10",
                    check_name=f"External Authority: {rec.verification_type}",
                    category="VERIFICATION",
                    severity="MAJOR",
                    outcome="PASS",
                    explanation=f"External verification with {rec.verification_type} returned confirmed MATCH (Ref: {rec.external_reference_id}). [SIMULATED]",
                    rule_citation="AICTE Verification Protocol",
                    evidence_json=json.dumps({"reference": rec.external_reference_id, "status": "MATCH", "watermark": rec.watermark}),
                    source_document_id=None
                ))
            else:
                findings.append(Finding(
                    id=f"{run_id}-V10-{rec.verification_type}",
                    run_id=run_id,
                    rule_id="V10",
                    check_name=f"External Authority: {rec.verification_type}",
                    category="VERIFICATION",
                    severity="MAJOR",
                    outcome="FAIL",
                    explanation=f"External verification with {rec.verification_type} failed: status {rec.simulated_status} (Ref: {rec.external_reference_id}). [SIMULATED]",
                    rule_citation="AICTE Verification Protocol",
                    evidence_json=json.dumps({"reference": rec.external_reference_id, "status": rec.simulated_status, "watermark": rec.watermark}),
                    source_document_id=None
                ))

    # =========================================================================
    # RULE V12 & V13: PDF Metadata & Revision Anomaly Analysis (Tampering Indicators)
    # =========================================================================
    for doc in docs:
        analysis = analyze_pdf_metadata_and_integrity(doc.file_path, doc.document_type)
        observations = analysis.get("observations", [])
        
        if not observations:
            # Clean document integrity
            findings.append(Finding(
                id=f"{run_id}-V12-{doc.id}",
                run_id=run_id,
                rule_id="V12",
                check_name=f"Document Integrity: {doc.original_filename}",
                category="TAMPERING_INDICATORS",
                severity="ADVISORY_OBSERVATION",
                outcome="PASS",
                explanation=f"Metadata analysis of '{doc.original_filename}' reveals consistent creation timestamps and standard structural stream.",
                rule_citation="ISO 32000-1 Digital Document Scrutiny Guidelines",
                evidence_json=json.dumps(analysis.get("metadata", {})),
                source_document_id=doc.id
            ))
        else:
            for obs in observations:
                rule_id = obs.get("rule_id", "V12")
                findings.append(Finding(
                    id=f"{run_id}-{rule_id}-{doc.id}-{len(findings)}",
                    run_id=run_id,
                    rule_id=rule_id,
                    check_name=f"{obs.get('check_name', 'Integrity Observation')} [{doc.original_filename}]",
                    category="TAMPERING_INDICATORS",
                    severity=obs.get("severity", "ADVISORY_OBSERVATION"),
                    outcome="FLAG",
                    explanation=obs.get("finding", "Structural anomaly noted in PDF stream."),
                    rule_citation="ISO 32000-1 Structural PDF Integrity Standards",
                    evidence_json=json.dumps(obs.get("evidence", {})),
                    source_document_id=doc.id
                ))

    return findings
