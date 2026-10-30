import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_pipeline():
    print("==================================================")
    print("AICTE BLUEPILL VALIDATION WORKBENCH - TEST SUITE")
    print("==================================================")

    # 0. Local Model Verification (/models)
    from app.config import settings
    assert settings.MODELS_DIR.exists(), "models directory does not exist"
    assert settings.MODEL_PATH.exists(), f"Model file not found at {settings.MODEL_PATH}"
    size_mb = settings.MODEL_PATH.stat().st_size / (1024 * 1024)
    print(f"\n[0] Local Model Vault: {settings.MODEL_PATH.name} ({size_mb:.1f} MB) in /models")
    assert size_mb > 1000, f"Model file seems incomplete: {size_mb} MB"

    # Config endpoint check
    r_cfg = client.get("/agent/config")
    assert r_cfg.status_code == 200
    cfg = r_cfg.json()
    assert cfg["local_model_exists"] is True
    print(f"    Config API: Active Model = {cfg['ollama_model']} | Local File Exists: {cfg['local_model_exists']}")

    # 1. Health
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    health_data = r.json()
    print(f"\n[1] Health Check: {health_data['status']} | DB Connected: {health_data['database_connected']}")

    # 2. List Applications
    r = client.get("/applications")
    assert r.status_code == 200
    apps = r.json()
    print(f"[2] Applications Listed: {len(apps)} applications in DB")
    assert len(apps) >= 3

    # 3. Status Dashboard for all 3 apps
    print("\n[3] Testing Live Status Dashboard per Application:")
    for app_info in apps:
        app_id = app_info["id"]
        r = client.get(f"/applications/{app_id}/status")
        assert r.status_code == 200
        st = r.json()
        print(f"   • [{st['application_number']}] {st['institution_name']}")
        print(f"     Status: {st['current_status']} | Readiness: {st['overall_readiness']} | Docs: {st['documents_count']}/{st['required_documents_count']} (Missing: {st['missing_documents_count']})")

    # 4. Final Judgment Verdict for App 1 (Compliant)
    print("\n[4] Final Judgment Verdict: Compliant Institution (Aryabhata)")
    r = client.get("/runs/run-app-001-aryabhata/verdict")
    assert r.status_code == 200
    v1 = r.json()
    print(f"   Verdict: {v1['overall_readiness']} ({v1['readiness_score_pct']}%)")
    print(f"   Headline: {v1['verdict_headline']}")
    print(f"   Passed Checks: {len(v1['actionable_checklist']['passed_compliance_checks'])}")
    assert v1["overall_readiness"] == "READY_FOR_REVIEW"
    assert len(v1["actionable_checklist"]["missing_mandatory_documents"]) == 0

    # 5. Final Judgment Verdict for App 2 (Incomplete - Missing Items)
    print("\n[5] Final Judgment Verdict: Incomplete Institution (Vikas)")
    r = client.get("/runs/run-app-002-vikas/verdict")
    assert r.status_code == 200
    v2 = r.json()
    print(f"   Verdict: {v2['overall_readiness']} ({v2['readiness_score_pct']}%)")
    print(f"   Headline: {v2['verdict_headline']}")
    missing = v2["actionable_checklist"]["missing_mandatory_documents"]
    print(f"   What's Missing ({len(missing)} documents):")
    for m in missing:
        print(f"     - Missing: {m['name']} | Mandate: {m['regulatory_mandate']}")
    assert v2["overall_readiness"] == "INCOMPLETE"
    assert len(missing) == 3

    # 6. Final Judgment Verdict for App 3 (Deficient + Tampering Flags)
    print("\n[6] Final Judgment Verdict: Issues & Tampering Flags (Shree Ram)")
    r = client.get("/runs/run-app-003-shree-ram/verdict")
    assert r.status_code == 200
    v3 = r.json()
    print(f"   Verdict: {v3['overall_readiness']} ({v3['readiness_score_pct']}%)")
    print(f"   Headline: {v3['verdict_headline']}")
    deficiencies = v3["actionable_checklist"]["critical_and_major_deficiencies"]
    print(f"   Critical/Major Deficiencies ({len(deficiencies)} items):")
    for d in deficiencies:
        print(f"     - [{d['rule_id']}] {d['check_name']} ({d['severity']}): {d['finding']}")
    
    tamper_flags = v3["actionable_checklist"]["tampering_integrity_flags"]
    print(f"   Digital Tampering / Integrity Flags ({len(tamper_flags)} items):")
    for t in tamper_flags:
        print(f"     - [{t['rule_id']}] {t['document_name']} -> {t['details']}")
    assert len(tamper_flags) > 0, "Expected tampering flags on App 3"

    # 7. Ask BluePill Scrutiny Assistant Q&A
    print("\n[7] Testing 'Ask BluePill' Q&A Assistant:")
    q_payload = {
        "application_id": "app-003-shree-ram",
        "question": "What is the status of the land and are there any tampering indicators detected in the uploaded PDFs?",
        "include_statutory_citations": True
    }
    r = client.post("/agent/ask", json=q_payload)
    assert r.status_code == 200
    ans = r.json()
    print(f"   Question: {ans['question']}")
    print(f"   Engine: {ans['engine_used']} (Latency: {ans['latency_ms']}ms)")
    print(f"   Answer:\n{ans['answer']}")
    print(f"   Sources Cited: {len(ans['sources'])}")

    # 8. SA-01 Document Classification Subagent
    print("\n[8] Testing SA-01 Document Classifier Subagent:")
    r_docs = client.get("/applications/app-001-aryabhata/documents")
    docs = r_docs.json()
    first_doc_id = docs[0]["id"]
    r_cls = client.post(f"/agent/classify/{first_doc_id}")
    assert r_cls.status_code == 200
    cls_res = r_cls.json()
    print(f"   SA-01 Classification: Declared: {cls_res['declared_type']} | Verified: {cls_res['verified_type']} | Confidence: {cls_res['confidence']}")
    assert cls_res["is_consistent"] is True

    # 9. Audit Logs / Traces
    print("\n[9] Checking Immutable Agent Audit Traces:")
    r_tr = client.get("/agent/traces")
    assert r_tr.status_code == 200
    traces = r_tr.json()
    print(f"   Logged Agent Traces Count: {len(traces)}")

    # 10. Dynamic New College Addition & Automated Statutory Audit
    print("\n[10] Testing Dynamic College Addition & Automated Audit Testing:")
    new_college_payload = {
        "application_number": "AICTE/2024/APP-TEST-DELHI-TECH",
        "institution_name": "Delhi Institute of Advanced Technology & AI",
        "institution_type": "NEW_TECHNICAL_INSTITUTION",
        "application_type": "NEW_INSTITUTION",
        "state": "Delhi",
        "district": "South Delhi",
        "address": "Okhla Industrial Area Phase III, New Delhi - 110020",
        "programs": [
            {"program_name": "Artificial Intelligence & Data Science", "level": "UG", "approved_intake": 120}
        ],
        "land_detail": {
            "total_area_acres": 9.2,
            "is_single_plot": True,
            "survey_khasra_no": "Khasra No. 712/3",
            "land_registration_date": "2023-08-15"
        },
        "builtup_detail": {
            "total_carpet_sqm": 9500.0,
            "instructional_area_sqm": 5000.0,
            "administrative_area_sqm": 2300.0,
            "amenities_area_sqm": 2200.0
        },
        "test_scenario": "COMPLIANT",
        "auto_validate": True
    }
    r_create = client.post("/applications", json=new_college_payload)
    assert r_create.status_code == 201, f"Failed to create new college: {r_create.text}"
    created_college = r_create.json()
    print(f"   Created College: [{created_college['application_number']}] {created_college['institution_name']}")
    print(f"   Uploaded Docs: {created_college['uploaded_document_count']} | Run ID: {created_college['latest_run_id']}")
    assert created_college["uploaded_document_count"] == 5
    assert created_college["latest_run_id"] is not None

    # Verify Verdict
    r_verdict = client.get(f"/runs/{created_college['latest_run_id']}/verdict")
    assert r_verdict.status_code == 200
    v_new = r_verdict.json()
    print(f"   Automated Audit Verdict: {v_new['overall_readiness']} ({v_new['readiness_score_pct']}%)")
    print(f"   Headline: {v_new['verdict_headline']}")
    assert v_new["overall_readiness"] == "READY_FOR_REVIEW"
    assert len(v_new["actionable_checklist"]["missing_mandatory_documents"]) == 0

    print("\n==================================================")
    print("ALL API & STATUTORY VALIDATION TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
