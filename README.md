# AICTE BluePill Validation Workbench

AI-powered assistive validation and scrutiny workbench for AICTE institution approval applications.

Built strictly according to the **AICTE Approval Process Handbook (APH) 2024-25** norms, featuring:
1. **Deterministic Statutory Rules Engine** (Python decides, model explains).
2. **Digital Integrity & Tampering Anomaly Detection** (V12 Metadata and V13 Incremental Revision analysis).
3. **Application Verdict & Status Dashboard** (Comprehensive final judgment, overall readiness, and actionable checklists of what is missing).
4. **Interactive "Ask BluePill" Scrutiny Assistant** (Evidence-backed natural language Q&A with statutory citations).
5. **Fail-Closed Architecture & LLM Kill-Switch** (Identical deterministic operation regardless of LLM availability).

---

## Quick Start

### 1. Activate Environment & Run Seeder
```powershell
# Activate Python Virtual Environment
.\venv\Scripts\Activate.ps1

# (Optional) Re-seed synthetic applications & PDFs
python -m app.data.seed_data
```

### 2. Run Test Suite
```powershell
python test_api.py
```

### 3. Launch the API & Frontend Server
```powershell
python run_server.py
```
- **Live Scrutiny Dashboard (Frontend)**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger UI (API Docs)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Active Local Model**: `Qwen 2.5 (3B)` loaded in Ollama on GPU

---

## Seeded Benchmark Applications

| Application Number | Institution Name | Status | Overall Readiness | Description |
|---|---|---|---|---|
| `AICTE/2024/APP-001-COMPLIANT` | Aryabhata Institute of Tech & Mgmt | `VALIDATION_COMPLETED` | `READY_FOR_REVIEW` (100%) | 8.5 acres (norm >= 7.5), 9,200 sqm carpet, all 5 mandatory statutory documents verified, clean metadata. |
| `AICTE/2024/APP-002-INCOMPLETE` | Vikas Technical Academy | `ACTION_REQUIRED` | `INCOMPLETE` (69.2%) | Missing 3 statutory documents: Building Plan Approval, Fire Safety NOC, and Architect Certificate. Actionable checklist itemizes missing files. |
| `AICTE/2024/APP-003-ISSUES` | Shree Ram Engineering College | `ACTION_REQUIRED` | `HAS_ISSUES` (61.1%) | Area deficit, cross-consistency mismatches (Plot-88 vs Plot-12/A, 8.0 acres vs 5.2 acres), Fire NOC altered via Canva with 3 incremental %%EOF updates. |

---

## Core API Endpoints

### 1. Applications & Live Status
- `GET /applications` — List all registered institution applications.
- `GET /applications/{id}` — Full institutional profile (programs, land, built-up areas).
- `GET /applications/{id}/status` — **Live Status Dashboard**: overall readiness, required vs uploaded docs, missing count.

### 2. Document Processing & Extraction
- `POST /applications/{id}/documents/upload` — Upload PDF: runs cryptographic SHA-256, PyMuPDF text extraction, and metadata inspection.
- `GET /applications/{id}/documents` — List uploaded documents for an application.
- `GET /documents/{id}` — View extracted text and structural metadata.

### 3. Validation & Final Judgment Verdict
- `POST /applications/{id}/validate` — Triggers deterministic rule engine (V01, V04, V05, V07, V10, V12, V13).
- `GET /runs/{id}` — Detailed list of all statutory findings and evidence.
- `GET /runs/{id}/verdict` — **Final Judgment**:
  - `overall_readiness`: `READY_FOR_REVIEW`, `INCOMPLETE`, `HAS_ISSUES`, `CRITICAL_ISSUES`.
  - `category_breakdown`: Completeness, Validity, Consistency, Tampering Indicators, Verification.
  - `actionable_checklist`:
    - `missing_mandatory_documents` (what's missing + statutory mandate + impact).
    - `critical_and_major_deficiencies` (finding + evidence + required remedy).
    - `tampering_integrity_flags` (document name + details + recommendation).
    - `passed_compliance_checks`.

### 4. Agent & Scrutiny Assistant
- `POST /agent/ask` — Ask BluePill: Questions regarding land, built-up, tampering flags, or readiness with exact evidence citations.
- `POST /agent/classify/{doc_id}` — SA-01 Document Classification Subagent.
- `GET /agent/traces` — Immutable audit logs.
- `POST /agent/config/toggle-llm?enable=true|false` — Toggle dynamic LLM kill-switch.
