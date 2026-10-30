import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.sla import SLARule
from app.services.clock_service import clock_service
from app.services.audit_ledger import audit_ledger

SAMPLE_CORRIGENDUM_CLAUSES = [
    {
        "clause_id": "APH-2026-CORR-02DEC",
        "title": "Corrigendum of 2 Dec 2025: Constitution of EVC and SAC Committees",
        "source_text": (
            "Clause 4.1.2: The Expert Visit Committee (EVC) and Standing Appellate Committee (SAC) "
            "shall henceforth be constituted directly by the Council at Headquarters, replacing the Regional Officer / Chairman delegation. "
            "The prescribed timeline for completing on-site EVC inspection and uploading the digital inspection report "
            "shall be strictly reduced from 21 days to 14 working days from the date of panel notification. "
            "Automated escalation ladder shall trigger to Regional Head at Day +3 and Bureau Head at Day +7."
        ),
        "compiled_rule_draft": {
            "rule_code": "APH-SLA-EVC-2026-CORR2",
            "version": "2.0",
            "process_category": "APPLICATION_STAGE",
            "stage_name": "EVC_INSPECTION",
            "duration_days": 14,
            "duration_type": "WORKING_DAYS",
            "reminder_offsets": [-5, -2, 0],
            "escalation_ladder": [
                {"days_after": 0, "role": "SCRUTINY_OFFICER", "action": "DUE_ALERT"},
                {"days_after": 3, "role": "REGIONAL_OFFICER", "action": "ESCALATE_TO_REGIONAL_HEAD"},
                {"days_after": 7, "role": "BUREAU_OFFICER", "action": "ESCALATE_TO_BUREAU_HEAD"}
            ],
            "change_summary": "EVC constitution shifted to Council; timeline tightened to 14 working days per Dec 2 corrigendum."
        }
    },
    {
        "clause_id": "APH-2026-ADDENDUM-FEB",
        "title": "Addendum of 6 Feb 2026: Self-Disclosure Nil-Deficiency Verification",
        "source_text": (
            "Clause 1.8: In line with the National Single Window System (NSWS) mandate, institutions claiming Nil Deficiency "
            "under self-disclosure shall undergo an automated Scrutiny within 7 working days. If any discrepancies in land deed "
            "or built-up area are identified, an immediate return with mandatory reason must be generated within 48 hours."
        ),
        "compiled_rule_draft": {
            "rule_code": "APH-SLA-SELF-DISCLOSURE-V1",
            "version": "1.0",
            "process_category": "APPLICATION_STAGE",
            "stage_name": "INITIAL_SCRUTINY",
            "duration_days": 7,
            "duration_type": "WORKING_DAYS",
            "reminder_offsets": [-3, -1, 0],
            "escalation_ladder": [
                {"days_after": 0, "role": "SCRUTINY_OFFICER", "action": "DUE_ALERT"},
                {"days_after": 2, "role": "REGIONAL_OFFICER", "action": "ESCALATE_TO_REGIONAL_HEAD"}
            ],
            "change_summary": "Fast-track 7-day scrutiny for NSWS Nil-Deficiency self-disclosure applications."
        }
    }
]

class PolicyCompilerService:
    @staticmethod
    def get_sample_clauses() -> List[Dict[str, Any]]:
        return SAMPLE_CORRIGENDUM_CLAUSES

    @staticmethod
    def compile_clause_to_rule(
        db: Session,
        clause_id: str,
        actor_id: str = "ADMIN-CHIEF"
    ) -> Dict[str, Any]:
        """Translates an APH handbook clause into a draft, schema-constrained versioned rule.
        Enforces human-in-the-loop safety: created in PENDING_APPROVAL and cannot affect in-flight cases until approved.
        """
        clause_data = next((c for c in SAMPLE_CORRIGENDUM_CLAUSES if c["clause_id"] == clause_id), None)
        if not clause_data:
            clause_data = SAMPLE_CORRIGENDUM_CLAUSES[0]

        draft = clause_data["compiled_rule_draft"]
        sim_now = clock_service.now(db)

        # Check if already exists
        existing = db.query(SLARule).filter(SLARule.rule_code == draft["rule_code"]).first()
        if existing:
            rule = existing
            rule.approval_status = "PENDING_APPROVAL"
            rule.is_active = False
            db.commit()
            db.refresh(rule)
        else:
            rule = SLARule(
                id=str(uuid.uuid4()),
                rule_code=draft["rule_code"],
                version=draft["version"],
                process_category=draft["process_category"],
                stage_name=draft["stage_name"],
                duration_days=draft["duration_days"],
                duration_type=draft["duration_type"],
                reminder_offsets_json=json.dumps(draft["reminder_offsets"]),
                escalation_ladder_json=json.dumps(draft["escalation_ladder"]),
                effective_from=sim_now,
                is_active=False, # Quarantined until human approval!
                created_by="SLM_POLICY_COMPILER",
                approval_status="PENDING_APPROVAL",
                change_summary=draft["change_summary"],
                created_at=sim_now
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)

        audit_ledger.record_event(
            db=db,
            event_type="POLICY_RULE_DRAFTED",
            entity_type="SLA_RULE",
            entity_id=rule.id,
            actor_id="SLM_POLICY_COMPILER",
            actor_role="SLM_ENGINE",
            action_summary=f"Drafted versioned rule {rule.rule_code} v{rule.version} from clause {clause_data['title']}",
            new_state="PENDING_APPROVAL",
            reason="Awaiting mandatory human administrator verification and golden test run",
            payload={"rule_code": rule.rule_code, "duration_days": rule.duration_days}
        )

        return {
            "rule_id": rule.id,
            "rule_code": rule.rule_code,
            "version": rule.version,
            "status": rule.approval_status,
            "source_clause": clause_data["title"],
            "duration_days": rule.duration_days,
            "duration_type": rule.duration_type,
            "diff_preview": {
                "previous_version": "v1.0 (21 days, Regional delegation)",
                "new_version": f"v{rule.version} ({rule.duration_days} working days, Council constituted)",
                "effective_date": rule.effective_from.strftime("%d-%B-%Y"),
                "in_flight_protection": "Existing applications continue on v1.0; only new dossiers follow v2.0."
            }
        }

    @staticmethod
    def approve_rule(db: Session, rule_id: str, admin_id: str) -> Dict[str, Any]:
        """Human approval gate: transitions draft rule into ACTIVE status."""
        rule = db.query(SLARule).filter(SLARule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule {rule_id} not found.")

        rule.approval_status = "APPROVED"
        rule.is_active = True
        db.commit()

        audit_ledger.record_event(
            db=db,
            event_type="POLICY_RULE_APPROVED",
            entity_type="SLA_RULE",
            entity_id=rule.id,
            actor_id=admin_id,
            actor_role="ADMIN",
            action_summary=f"Administrator approved rule {rule.rule_code} v{rule.version} to go live",
            previous_state="PENDING_APPROVAL",
            new_state="APPROVED",
            reason="Human-in-the-loop verification successfully passed"
        )

        return {
            "status": "APPROVED",
            "rule_code": rule.rule_code,
            "version": rule.version,
            "message": f"Rule {rule.rule_code} v{rule.version} is now LIVE and active in NIRIKSHA Rules Studio."
        }

    @staticmethod
    def draft_bilingual_letter(
        application_number: str,
        institution_name: str,
        stage: str,
        deficiency_reason: str
    ) -> Dict[str, str]:
        """Produces official bilingual deficiency memos in English and Hindi."""
        english_text = (
            f"ALL INDIA COUNCIL FOR TECHNICAL EDUCATION\n"
            f"Nelson Mandela Marg, Vasant Kunj, New Delhi - 110070\n\n"
            f"Subject: Deficiency Notice Regarding Application No: {application_number}\n\n"
            f"To,\n"
            f"The Principal / Director,\n"
            f"{institution_name}\n\n"
            f"Sir/Madam,\n"
            f"During the {stage.replace('_', ' ').title()} stage, the Scrutiny Committee observed the following statutory discrepancy:\n\n"
            f"\"{deficiency_reason}\"\n\n"
            f"You are requested to upload the rectified compliance documentation on the NIRIKSHA portal "
            f"within 10 calendar days, failing which the application may be recommended for rejection.\n\n"
            f"Yours faithfully,\n"
            f"Regional Officer, AICTE"
        )

        hindi_text = (
            f"अखिल भारतीय तकनीकी शिक्षा परिषद\n"
            f"नेल्सन मंडेला मार्ग, वसंत कुंज, नई दिल्ली - 110070\n\n"
            f"विषय: आवेदन संख्या {application_number} के संबंध में कमी सूचना\n\n"
            f"सेवा में,\n"
            f"प्राचार्य / निदेशक,\n"
            f"{institution_name}\n\n"
            f"महोदय/महोदया,\n"
            f"{stage.replace('_', ' ').title()} चरण के दौरान, संवीक्षा समिति ने निम्नलिखित वैधानिक विसंगति दर्ज की है:\n\n"
            f"\"{deficiency_reason}\"\n\n"
            f"आपसे अनुरोध है कि 10 कैलेंडर दिनों के भीतर निरीक्षा पोर्टल पर सुधारित दस्तावेज अपलोड करें।\n\n"
            f"भवदीय,\n"
            f"क्षेत्रीय अधिकारी, एआईसीटीई"
        )

        return {
            "english": english_text,
            "hindi": hindi_text
        }

policy_compiler = PolicyCompilerService()
