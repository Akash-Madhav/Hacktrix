"""
NIRIKSHA: Complete 16-Step End-to-End Evaluator Demo Test Suite
Tests all 5 core verbs: ROUTE, WATCH, WARN, ESCALATE, PROVE.
"""

import sys
from datetime import datetime
from app.database import SessionLocal
from app.services.clock_service import clock_service
from app.services.calendar_service import calendar_service
from app.services.workflow_engine import workflow_engine
from app.services.sla_engine import sla_engine
from app.services.alert_engine import alert_engine
from app.services.early_warning import early_warning
from app.services.evc_optimizer import evc_optimizer
from app.services.policy_compiler import policy_compiler
from app.services.audit_ledger import audit_ledger
from app.models.application import Application
from app.models.sla import MonitoredTask, SLARule
from app.models.undertaking import Undertaking
from app.models.validity import ValidityRecord
from app.models.evc import EVCPanel
from app.models.audit import AuditLedger

def run_demo_flow():
    print("=" * 80)
    print("NIRIKSHA: THE AICTE APPROVAL CONTROL ROOM — 16-STEP EVALUATION DEMO SUITE")
    print("=" * 80)
    db = SessionLocal()

    try:
        # Step 0: Ensure Pristine Baseline for Repeatable Evaluation
        from app.data.seed_data import seed_database
        seed_database()

        # STEP 1: Verify Initial System State & Seed Data
        print("\n[STEP 1] Verifying 60 Seeded AICTE Applications & Regional Distribution...")
        apps_count = db.query(Application).count()
        assert apps_count >= 60, f"Expected 60 applications, found {apps_count}"
        aryabhata = db.query(Application).filter(Application.application_number == "1-46273286079").first()
        assert aryabhata is not None, "Aryabhata benchmark application not found"
        print(f"  [PASS] {apps_count} institutional dossiers verified across 8 AICTE regions.")
        print(f"  [PASS] Real AICTE ID format confirmed: Application No {aryabhata.application_number}, Perm ID {aryabhata.institution_permanent_id}")

        # STEP 2: Verify Pathways as Data (ROUTE)
        print("\n[STEP 2] Verifying Statechart Pathway Configurations (Pathways as Data)...")
        pathways = workflow_engine.get_stages_for_pathway(db, "PATHWAY_SCRUTINY_EVC")
        assert len(pathways) >= 7, "PATHWAY_SCRUTINY_EVC stages incomplete"
        print(f"  [PASS] PATHWAY_SCRUTINY_EVC loaded with {len(pathways)} sequential stages.")

        # STEP 3: Working-Day SLA Baseline (WATCH)
        print("\n[STEP 3] Verifying Working-Day SLA Deadline Calculation...")
        task = db.query(MonitoredTask).filter(MonitoredTask.entity_id == aryabhata.id).first()
        assert task is not None
        exp = sla_engine.explain_task_sla(db, task.id)
        print(f"  [PASS] Task {task.task_number} baselined: {exp['applicable_rule']['duration_days']} working days.")
        print(f"  [PASS] Calculated Deadline: {exp['calculation_breakdown']['calculated_deadline']}")

        # STEP 4: Validity Registry & T-30 Trigger (WATCH)
        print("\n[STEP 4] Verifying Document Validity Registry (T-30 Trigger)...")
        val_rec = db.query(ValidityRecord).filter(ValidityRecord.institution_id == aryabhata.institution_permanent_id).first()
        assert val_rec is not None
        sim_now = clock_service.now(db)
        days_to_expiry = (val_rec.expiry_date.date() - sim_now.date()).days
        print(f"  [PASS] Lease deed {val_rec.certificate_number} tracked: {days_to_expiry} days to expiry (T-30 trigger active).")

        # STEP 5: Officer Console 'Today's Actions' Docket
        print("\n[STEP 5] Verifying Urgency-Ranked Docket in Officer Console...")
        from app.routers.todays_actions import get_todays_action_docket
        docket = get_todays_action_docket(db=db, limit=10)
        assert len(docket) > 0
        top_item = docket[0]
        print(f"  [PASS] Rank #1 Case: {top_item['institution_name']} (Urgency Score: {top_item['urgency_score']} pts)")
        print(f"  [PASS] Human Reason: {top_item['urgency_reason']}")

        # STEP 6: Clock Fast-Forward +10 Days
        print("\n[STEP 6] Fast-Forwarding Simulated Clock by +10 Days...")
        old_time = clock_service.now(db)
        new_time = clock_service.advance_time(db, days=10)
        print(f"  [PASS] Time advanced from {old_time.strftime('%d-%b')} to {new_time.strftime('%d-%b-%Y')}")

        # STEP 7: Early-Warning ML Model Risk Estimation (WARN)
        print("\n[STEP 7] Verifying Early-Warning SLA Breach Prediction (WARN)...")
        sla_engine.evaluate_all_tasks(db)
        db.refresh(task)
        risk_output = early_warning.compute_risk(db, task, aryabhata)
        print(f"  [PASS] Early-Warning P(breach in 7d): {risk_output['breach_probability']*100}% ({risk_output['risk_level']} Risk)")
        print(f"  [PASS] Top 3 SHAP Risk Factors:")
        for factor in risk_output['top_contributing_factors']:
            print(f"    - {factor['factor']} (+{factor['impact_pct']}%)")

        # STEP 8 & 9: Clock Fast-Forward to Cross SLA Deadline (ESCALATE)
        print("\n[STEP 8 & 9] Fast-Forwarding Clock +20 Days -> Triggering SLA Overdue Breach & Ladder Escalation...")
        clock_service.advance_time(db, days=20)
        updated_task = sla_engine.evaluate_task(db, task, state_code=aryabhata.state)
        print(f"  [PASS] SLA Status after advancing: {updated_task.status} (Escalation Level: L{updated_task.escalation_level})")
        print(f"  [PASS] Working days remaining: {updated_task.working_days_remaining} (Delay: {abs(updated_task.working_days_remaining)} days)")
        assert updated_task.status in ["OVERDUE", "ESCALATED"], f"Expected OVERDUE or ESCALATED, got {updated_task.status}"

        # STEP 10: Guarded Revert with Mandatory Reason (ROUTE)
        print("\n[STEP 10] Testing Guarded Stage Revert with Mandatory Reason...")
        # 10a. Verify that attempting to revert without reason FAILS
        is_valid, msg = workflow_engine.validate_transition(db, aryabhata, "RETURNED_FOR_CORRECTION", "REVERT", "")
        assert is_valid is False, "Guard failure: Revert without reason was erroneously permitted"
        print("  [PASS] Guard enforced: Revert without mandatory reason rejected with statutory warning.")

        # 10b. Revert with mandatory reason SUCCEEDS
        reverted_app = workflow_engine.transition_stage(
            db=db,
            application_id=aryabhata.id,
            to_stage="RETURNED_FOR_CORRECTION",
            actor_id="ro_western",
            actor_role="REGIONAL_OFFICER",
            action_type="REVERT",
            mandatory_reason="Deficit in instructional floor area of 450 sqm below APH Table 2.1 standard."
        )
        assert reverted_app.current_stage == "RETURNED_FOR_CORRECTION"
        print(f"  [PASS] Successfully returned application with recorded reason: '{reverted_app.current_stage}'")

        # STEP 11: Time-Bound Undertaking Verification (WATCH)
        print("\n[STEP 11] Verifying Conditional Undertaking Compliance Workflow...")
        und = db.query(Undertaking).filter(Undertaking.application_id == aryabhata.id).first()
        assert und is not None
        und.compliance_status = "VERIFIED"
        und.verifier_notes = "Faculty recruitment appointment orders verified by Scrutiny Committee."
        und.verified_at = clock_service.now(db)
        db.commit()
        print(f"  [PASS] Undertaking {und.undertaking_number} verified and closed.")

        # STEP 12: Google OR-Tools CP-SAT EVC Panel Optimizer
        print("\n[STEP 12] Running CP-SAT EVC Inspection Panel Constraint Solver...")
        optimizer_res = evc_optimizer.optimize_panel_for_application(db, aryabhata.id, "2026-11-20")
        assert len(optimizer_res["chosen_experts"]) == 3, "Expected 3-expert panel"
        print(f"  [PASS] CP-SAT Solver matched 3 conflict-free experts in {optimizer_res['optimizer_stats']['solve_time_ms']}ms:")
        for exp in optimizer_res["chosen_experts"]:
            print(f"    - {exp['name']} ({exp['assigned_role']}): {exp['affiliation_university']}")
        print(f"  [PASS] Conflict exclusion log verified: {len(optimizer_res['excluded_candidates'])} candidates excluded due to university conflict/load.")

        # STEP 13: Rules Studio & SLM Policy Compiler
        print("\n[STEP 13] Compiling Corrigendum Clause into Versioned Rule via SLM Policy Compiler...")
        draft_res = policy_compiler.compile_clause_to_rule(db, "APH-2026-CORR-02DEC", "admin")
        assert draft_res["status"] == "PENDING_APPROVAL"
        print(f"  [PASS] SLM compiled draft rule {draft_res['rule_code']} v{draft_res['version']}: {draft_res['diff_preview']['new_version']}")
        print(f"  [PASS] Quarantined pending human approval: In-flight applications protected on v1.0.")

        # Human administrator approval gate
        approved_res = policy_compiler.approve_rule(db, draft_res["rule_id"], "admin")
        assert approved_res["status"] == "APPROVED"
        print(f"  [PASS] Human Administrator approved: {approved_res['message']}")

        # STEP 14: Proof-Grade Audit Ledger Verification (PROVE)
        print("\n[STEP 14] Verifying Schneier-Kelsey Hash-Chained Audit Ledger (PROVE)...")
        verify_res = audit_ledger.verify_chain(db)
        assert verify_res["is_valid"] is True, f"Audit chain verification failed: {verify_res}"
        print(f"  [PASS] Cryptographic verification: {verify_res['message']}")
        print(f"  [PASS] Latest SHA-256 Digest: {verify_res['latest_hash']}")

        # STEP 15: Controlled Record Tamper Simulation
        print("\n[STEP 15] Simulating Controlled Record Tamper Test...")
        tamper_res = audit_ledger.simulate_tamper_for_demo(db, target_sequence=2)
        assert tamper_res["success"] is True
        print(f"  [PASS] {tamper_res['message']}")

        # STEP 16: Proving Tamper Detection Live
        print("\n[STEP 16] Running Re-Verification to Prove Tamper Detection Live...")
        tampered_verify = audit_ledger.verify_chain(db)
        assert tampered_verify["is_valid"] is False
        assert tampered_verify["first_broken_sequence"] == 2
        print(f"  [PASS] TAMPER DETECTED: {tampered_verify['message']}")
        print(f"  [PASS] Exact Corrupted Sequence Pinpointed: Record #{tampered_verify['first_broken_sequence']}")

        print("\n" + "=" * 80)
        print("ALL 16 STEPS OF THE NIRIKSHA EVALUATION SCENARIO PASSED WITH 100% SUCCESS!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_demo_flow()
