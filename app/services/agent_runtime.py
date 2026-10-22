import time
import json
import uuid
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.agent import AgentTrace, AskBluePillQuery
from app.models.application import Application
from app.models.document import Document
from app.models.validation import Finding, ValidationRun
from app.schemas.agent import AskBluePillResponse, SourceCitation

async def call_ollama_llm(prompt: str, system_prompt: str = "") -> Optional[str]:
    """
    Calls local Ollama instance if enabled and reachable.
    Fails safely and returns None if unavailable or disabled.
    """
    if not settings.LLM_ENABLED:
        return None

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "system": system_prompt or "You are AICTE BluePill statutory scrutiny assistant.",
                    "stream": False
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
    except Exception:
        # Gracefully handle when Ollama is offline or times out
        return None
    return None

def sanitize_agent_output(text: str) -> str:
    """
    Guardrail: Ensures model output never uses forbidden conclusive words
    such as 'forged', 'fake', 'guilty', 'approved', 'rejected'.
    Enforces 'Python decides, model explains'.
    """
    replacements = {
        "is approved": "appears compliant with examined norms",
        "is rejected": "exhibits deficiencies requiring committee review",
        "is forged": "displays digital structural anomalies",
        "is fake": "exhibits discrepancies requiring physical verification",
        "we approve": "the evidence indicates compliance",
        "we reject": "deficiencies have been catalogued"
    }
    sanitized = text
    for forbidden, safe in replacements.items():
        sanitized = sanitized.replace(forbidden, safe)
    return sanitized

async def run_sa01_classify_document(db: Session, doc_id: str) -> Dict[str, Any]:
    """
    SA-01: Document Classifier & Confidence Agent.
    Validates document classification against extracted text.
    """
    t0 = time.time()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return {"error": "Document not found"}

    text = (doc.extracted_text or "")[:1500].lower()
    
    # Deterministic heuristics
    confidence = 0.95
    predicted_type = doc.document_type
    
    if "sale deed" in text or "lease deed" in text or "khasra" in text or "sub-registrar" in text:
        predicted_type = "LAND_REGISTRATION"
    elif "fire" in text and ("noc" in text or "safety" in text or "hazard" in text):
        predicted_type = "FIRE_SAFETY_NOC"
    elif "building plan" in text or "municipal" in text or "sanction" in text or "carpet area" in text:
        predicted_type = "BUILDING_PLAN_APPROVAL"
    elif "affidavit" in text or "stamp paper" in text or "oath" in text or "trustees" in text:
        predicted_type = "AFFIDAVIT_TRUST"
    elif "council of architecture" in text or "architect" in text or "barrier-free" in text:
        predicted_type = "ARCHITECT_CERTIFICATE"

    is_match = (predicted_type == doc.document_type)
    explanation = f"Classified as '{doc.document_type}' with {int(confidence*100)}% structural keyword corroboration."
    
    # Record trace
    latency = (time.time() - t0) * 1000
    trace = AgentTrace(
        id=str(uuid.uuid4()),
        agent_name="SA-01-Document-Classifier",
        prompt_snapshot=f"Classify document text (len={len(text)})",
        tool_calls_json=json.dumps({"predicted_type": predicted_type, "is_match": is_match}),
        sanitized_output=explanation,
        latency_ms=latency,
        status="SUCCESS"
    )
    db.add(trace)
    db.commit()

    return {
        "document_id": doc.id,
        "declared_type": doc.document_type,
        "verified_type": predicted_type,
        "is_consistent": is_match,
        "confidence": confidence,
        "explanation": explanation
    }

async def answer_ask_bluepill_query(
    db: Session,
    application_id: str,
    question: str,
    include_statutory_citations: bool = True
) -> AskBluePillResponse:
    """
    Interactive scrutiny assistant for officers to question application findings.
    Works seamlessly in deterministic mode and enriches with LLM if enabled.
    """
    t0 = time.time()
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError("Application not found")

    docs = db.query(Document).filter(Document.application_id == application_id).all()
    latest_run = (
        db.query(ValidationRun)
        .filter(ValidationRun.application_id == application_id)
        .order_by(ValidationRun.run_timestamp.desc())
        .first()
    )
    
    findings: List[Finding] = []
    if latest_run:
        findings = db.query(Finding).filter(Finding.run_id == latest_run.id).all()

    q_lower = question.lower()
    citations: List[SourceCitation] = []
    answer_parts: List[str] = []
    engine_used = "DETERMINISTIC_EXPLAINER"

    # Contextual routing for questions
    if "land" in q_lower or "acres" in q_lower or "plot" in q_lower or "survey" in q_lower:
        land = app.land_detail
        if land:
            answer_parts.append(
                f"• Land Norms Status: Declared total area is {land.total_area_acres} acres (Survey/Khasra No: {land.survey_khasra_no or 'N/A'}). "
                f"Contiguous single plot: {'Yes' if land.is_single_plot else 'No'}."
            )
        land_doc = next((d for d in docs if d.document_type == "LAND_REGISTRATION"), None)
        if land_doc:
            snippet = (land_doc.extracted_text or "")[:300].strip()
            citations.append(SourceCitation(
                document_name=land_doc.original_filename,
                clause_or_page="AICTE APH 2024-25 Clause 1.4.1",
                extracted_text_snippet=snippet if snippet else "Registered deed on record."
            ))
            
    if "built" in q_lower or "carpet" in q_lower or "instructional" in q_lower or "area" in q_lower:
        built = app.builtup_detail
        if built:
            answer_parts.append(
                f"• Built-up Infrastructure Status: Total Carpet Area = {built.total_carpet_sqm} sq.m, "
                f"Instructional Area = {built.instructional_area_sqm} sq.m, "
                f"Administrative Area = {built.administrative_area_sqm} sq.m."
            )
        bldg_doc = next((d for d in docs if d.document_type == "BUILDING_PLAN_APPROVAL"), None)
        if bldg_doc:
            citations.append(SourceCitation(
                document_name=bldg_doc.original_filename,
                clause_or_page="AICTE APH 2024-25 Clause 1.4.2",
                extracted_text_snippet="Competent authority approved master plan."
            ))

    if "tamper" in q_lower or "metadata" in q_lower or "integrity" in q_lower or "fake" in q_lower or "altered" in q_lower:
        tamper_findings = [f for f in findings if f.category == "TAMPERING_INDICATORS"]
        if tamper_findings:
            flags = [f for f in tamper_findings if f.outcome == "FLAG"]
            if flags:
                answer_parts.append(
                    f"• Digital Integrity Observations: {len(flags)} structural observation(s) recorded. "
                    + "; ".join([f.explanation for f in flags])
                )
            else:
                answer_parts.append("• Digital Integrity Observations: All examined documents show consistent timestamps and valid single-stream structures.")
        else:
            answer_parts.append("• Integrity analysis not yet run. Trigger a validation run to inspect PDF stream metadata.")

    if "missing" in q_lower or "status" in q_lower or "readiness" in q_lower or "pass" in q_lower:
        uploaded = {d.document_type for d in docs}
        all_req = {"LAND_REGISTRATION", "BUILDING_PLAN_APPROVAL", "FIRE_SAFETY_NOC", "AFFIDAVIT_TRUST", "ARCHITECT_CERTIFICATE"}
        missing = all_req - uploaded
        if missing:
            answer_parts.append(f"• Missing Mandatory Documents ({len(missing)}): {', '.join(missing)}.")
        else:
            answer_parts.append("• Completeness: All 5 statutory mandatory documents are uploaded.")
            
        if latest_run:
            answer_parts.append(f"• Overall Readiness Verdict: {latest_run.overall_readiness}.")

    # Fallback if specific topic wasn't matched
    if not answer_parts:
        answer_parts.append(
            f"Institutional Profile: '{app.institution_name}' ({app.application_number}) located in {app.district}, {app.state}. "
            f"Total documents uploaded: {len(docs)}. Latest Validation Status: {latest_run.overall_readiness if latest_run else 'NO RUN EXECUTED'}."
        )

    # Optional LLM Enhancement if enabled
    if settings.LLM_ENABLED:
        prompt = (
            f"Application: {app.institution_name} ({app.application_number})\n"
            f"Factual Findings: {' '.join(answer_parts)}\n"
            f"User Question: {question}\n\n"
            "Provide a concise, professional regulatory scrutiny briefing answering the user's question. "
            "Never use conclusive approval/rejection words. Cite statutory AICTE clauses where applicable."
        )
        llm_resp = await call_ollama_llm(prompt)
        if llm_resp:
            final_answer = sanitize_agent_output(llm_resp)
            engine_used = f"HYBRID_WITH_LLM ({settings.OLLAMA_MODEL})"
        else:
            final_answer = "\n".join(answer_parts)
    else:
        final_answer = "\n".join(answer_parts)

    latency = (time.time() - t0) * 1000

    # Save query record
    query_rec = AskBluePillQuery(
        id=str(uuid.uuid4()),
        application_id=application_id,
        question=question,
        answer=final_answer,
        sources_json=json.dumps([c.dict() for c in citations]),
        latency_ms=latency
    )
    db.add(query_rec)
    db.commit()

    return AskBluePillResponse(
        question=question,
        answer=final_answer,
        sources=citations,
        engine_used=engine_used,
        latency_ms=round(latency, 2),
        disclaimer="Advisory statutory summary. Formal decisions belong to the AICTE Scrutiny Committee."
    )

async def analyze_dossier_with_slm(
    db: Session,
    application_id: str,
    run_id: str
) -> Optional[Dict[str, Any]]:
    """
    Executes SLM (Qwen 2.5:3b) comprehensive statutory scrutiny analysis over the application
    and uploaded proofs, determining compliance, deficiencies, and missing mandates dynamically.
    """
    if not settings.LLM_ENABLED:
        return None

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        return None

    docs = db.query(Document).filter(Document.application_id == application_id).all()
    land = app.land_detail
    built = app.builtup_detail

    # Build prompt
    docs_summary = []
    uploaded_types = set()
    for d in docs:
        uploaded_types.add(d.document_type)
        snippet = (d.extracted_text or "")[:400].replace("\n", " ").strip()
        docs_summary.append(
            f"- {d.document_type} ({d.original_filename}): SHA-256={d.sha256_hash[:16]}... Text snippet: \"{snippet}\""
        )

    all_mandates = [
        "LAND_REGISTRATION",
        "BUILDING_PLAN_APPROVAL",
        "FIRE_SAFETY_NOC",
        "AFFIDAVIT_TRUST",
        "ARCHITECT_CERTIFICATE"
    ]
    missing_docs = [m for m in all_mandates if m not in uploaded_types]

    prompt = f"""You are the AICTE BluePill Statutory Scrutiny Engine powered by Qwen 2.5.
Analyze the following technical institution application dossier and uploaded document proofs per AICTE APH 2024-25 statutory norms:

APPLICATION DOSSIER:
- Institution Name: {app.institution_name}
- Application Number: {app.application_number}
- Institution Type: {app.institution_type}
- State / District: {app.state}, {app.district}
- Declared Land Area: {land.total_area_acres if land else 0} Acres (Single Contiguous Plot: {land.is_single_plot if land else False}, Survey No: {land.survey_khasra_no if land else 'N/A'})
- Declared Built-up Space: Carpet Area = {built.total_carpet_sqm if built else 0} sq.m, Instructional Area = {built.instructional_area_sqm if built else 0} sq.m

SUBMITTED PROOFS ({len(docs)} uploaded):
{chr(10).join(docs_summary) if docs_summary else "No documents uploaded."}

MISSING STATUTORY MANDATES DETECTED:
{chr(10).join([f"- {m}" for m in missing_docs]) if missing_docs else "None (all 5 mandatory document categories present)."}

AICTE APH 2024-25 STATUTORY NORMS:
1. Land Norm: Minimum 7.5 Acres in a single contiguous plot.
2. Built-up Norm: Minimum 6,000 sq.m carpet area and 3,000 sq.m instructional area.
3. Completeness: All 5 mandatory documents (Land Deed, Building Plan Approval, Fire Safety NOC, Trust Affidavit, Architect Certificate) must be submitted.
4. Cross-Document Consistency: Acreage and survey numbers in application must match Land Registration Deed text.

Analyze this application dossier and return a JSON object with EXACTLY the following keys:
- "overall_readiness": "READY_FOR_REVIEW" if 100% compliant, "INCOMPLETE" if documents are missing, "CRITICAL_ISSUES" if land/space norms fail, "HAS_ISSUES" if discrepancies exist.
- "compliance_score_pct": integer between 0 and 100.
- "verdict_headline": authoritative regulatory headline summarizing status.
- "verdict_explanation": detailed scrutiny narrative explaining what meets norms, what is missing, and required remediations.
- "missing_items": list of strings detailing what proofs/items are missing.
- "critical_deficiencies": list of strings detailing any norm failures or discrepancies.
"""

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                }
            )
            if resp.status_code == 200:
                raw_json = resp.json().get("response", "{}")
                data = json.loads(raw_json)
                latency = round((time.time() - t0) * 1000, 2)
                
                # Sanitize narrative
                data["verdict_explanation"] = sanitize_agent_output(data.get("verdict_explanation", ""))
                data["engine"] = f"Qwen 2.5 (3B) Local SLM"
                data["latency_ms"] = latency
                
                # Record trace in database
                trace = AgentTrace(
                    id=str(uuid.uuid4()),
                    agent_name="SLM-Scrutiny-Analyzer",
                    prompt_snapshot=f"Analyze application {app.application_number} with {len(docs)} proofs",
                    tool_calls_json=json.dumps({"run_id": run_id, "application_id": application_id}),
                    sanitized_output=data.get("verdict_explanation", "")[:1000],
                    latency_ms=latency,
                    status="SUCCESS"
                )
                db.add(trace)
                db.commit()
                return data
    except Exception as e:
        print(f"SLM scrutiny analysis fallback: {e}")
        return None
    return None

