import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.workflow import WorkflowConfig, WorkflowTransition
from app.models.sla import MonitoredTask, SLARule
from app.services.clock_service import clock_service

# Default statechart pathways definitions
DEFAULT_PATHWAYS = [
    {
        "pathway_code": "PATHWAY_SCRUTINY_ONLY",
        "name": "Standard Scrutiny Pathway (Minor Amendments / EoA)",
        "description": "Streamlined single-committee review for routine approvals.",
        "version": "APH-2026-V1.0",
        "stages": [
            {"stage_name": "SUBMITTED", "order": 1, "sla_days": 2, "sla_type": "WORKING_DAYS", "allowed_next": ["INITIAL_SCRUTINY"]},
            {"stage_name": "INITIAL_SCRUTINY", "order": 2, "sla_days": 15, "sla_type": "WORKING_DAYS", "allowed_next": ["RE_SCRUTINY", "APPROVED", "REJECTED", "RETURNED_FOR_CORRECTION"]},
            {"stage_name": "RETURNED_FOR_CORRECTION", "order": 3, "sla_days": 10, "sla_type": "CALENDAR_DAYS", "allowed_next": ["RE_SCRUTINY", "INITIAL_SCRUTINY"]},
            {"stage_name": "RE_SCRUTINY", "order": 4, "sla_days": 7, "sla_type": "WORKING_DAYS", "allowed_next": ["APPROVED", "REJECTED", "RETURNED_FOR_CORRECTION"]},
            {"stage_name": "APPROVED", "order": 5, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []},
            {"stage_name": "REJECTED", "order": 6, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": ["SAC_SHC"]}
        ]
    },
    {
        "pathway_code": "PATHWAY_SCRUTINY_EVC",
        "name": "Full Scrutiny + EVC Pathway (New Institutions & Expansions)",
        "description": "Multi-tier scrutiny followed by on-site Expert Visit Committee inspection and Regional Committee review.",
        "version": "APH-2026-V1.0",
        "stages": [
            {"stage_name": "SUBMITTED", "order": 1, "sla_days": 2, "sla_type": "WORKING_DAYS", "allowed_next": ["INITIAL_SCRUTINY"]},
            {"stage_name": "INITIAL_SCRUTINY", "order": 2, "sla_days": 15, "sla_type": "WORKING_DAYS", "allowed_next": ["EVC_INSPECTION", "RE_SCRUTINY", "RETURNED_FOR_CORRECTION", "REJECTED"]},
            {"stage_name": "RETURNED_FOR_CORRECTION", "order": 3, "sla_days": 10, "sla_type": "CALENDAR_DAYS", "allowed_next": ["RE_SCRUTINY"]},
            {"stage_name": "RE_SCRUTINY", "order": 4, "sla_days": 7, "sla_type": "WORKING_DAYS", "allowed_next": ["EVC_INSPECTION", "REJECTED"]},
            {"stage_name": "EVC_INSPECTION", "order": 5, "sla_days": 15, "sla_type": "WORKING_DAYS", "allowed_next": ["REGIONAL_COMMITTEE", "SAC_SHC"]},
            {"stage_name": "REGIONAL_COMMITTEE", "order": 6, "sla_days": 10, "sla_type": "WORKING_DAYS", "allowed_next": ["APPROVED", "SAC_SHC", "REJECTED"]},
            {"stage_name": "SAC_SHC", "order": 7, "sla_days": 15, "sla_type": "WORKING_DAYS", "allowed_next": ["APPROVED", "REJECTED"]},
            {"stage_name": "APPROVED", "order": 8, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []},
            {"stage_name": "REJECTED", "order": 9, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []}
        ]
    },
    {
        "pathway_code": "PATHWAY_EVC_SAC_SHC",
        "name": "EVC + SAC/SHC Appellate Review Pathway",
        "description": "Appellate pathway for institutions appealing previous committee findings.",
        "version": "APH-2026-V1.0",
        "stages": [
            {"stage_name": "SUBMITTED", "order": 1, "sla_days": 3, "sla_type": "WORKING_DAYS", "allowed_next": ["EVC_INSPECTION"]},
            {"stage_name": "EVC_INSPECTION", "order": 2, "sla_days": 15, "sla_type": "WORKING_DAYS", "allowed_next": ["SAC_SHC"]},
            {"stage_name": "SAC_SHC", "order": 3, "sla_days": 20, "sla_type": "WORKING_DAYS", "allowed_next": ["APPROVED", "REJECTED"]},
            {"stage_name": "APPROVED", "order": 4, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []},
            {"stage_name": "REJECTED", "order": 5, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []}
        ]
    },
    {
        "pathway_code": "PATHWAY_EVC_ONLY",
        "name": "Unannounced / Surprise Compliance EVC Pathway",
        "description": "Direct EVC inspection triggered by complaints or statutory compliance verifications.",
        "version": "APH-2026-V1.0",
        "stages": [
            {"stage_name": "SUBMITTED", "order": 1, "sla_days": 2, "sla_type": "WORKING_DAYS", "allowed_next": ["EVC_INSPECTION"]},
            {"stage_name": "EVC_INSPECTION", "order": 2, "sla_days": 10, "sla_type": "WORKING_DAYS", "allowed_next": ["REGIONAL_COMMITTEE"]},
            {"stage_name": "REGIONAL_COMMITTEE", "order": 3, "sla_days": 7, "sla_type": "WORKING_DAYS", "allowed_next": ["APPROVED", "REJECTED"]},
            {"stage_name": "APPROVED", "order": 4, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []},
            {"stage_name": "REJECTED", "order": 5, "sla_days": 0, "sla_type": "CALENDAR_DAYS", "allowed_next": []}
        ]
    }
]

class WorkflowEngine:
    @staticmethod
    def ensure_default_configs(db: Session):
        for pw in DEFAULT_PATHWAYS:
            cfg = db.query(WorkflowConfig).filter(WorkflowConfig.pathway_code == pw["pathway_code"]).first()
            if not cfg:
                cfg = WorkflowConfig(
                    id=str(uuid.uuid4()),
                    name=pw["name"],
                    pathway_code=pw["pathway_code"],
                    description=pw["description"],
                    version=pw["version"],
                    effective_from=datetime(2026, 1, 1),
                    is_active=True,
                    stages_json=json.dumps(pw["stages"])
                )
                db.add(cfg)
        db.commit()

    @staticmethod
    def get_pathway_config(db: Session, pathway_code: str) -> Optional[WorkflowConfig]:
        WorkflowEngine.ensure_default_configs(db)
        return db.query(WorkflowConfig).filter(
            WorkflowConfig.pathway_code == pathway_code,
            WorkflowConfig.is_active == True
        ).first()

    @staticmethod
    def get_stages_for_pathway(db: Session, pathway_code: str) -> List[Dict]:
        cfg = WorkflowEngine.get_pathway_config(db, pathway_code)
        if not cfg:
            return []
        return json.loads(cfg.stages_json)

    @staticmethod
    def validate_transition(
        db: Session,
        application: Application,
        to_stage: str,
        action_type: str,
        mandatory_reason: Optional[str]
    ) -> Tuple[bool, str]:
        """Guarded state machine validation for stage transitions."""
        current_stage = application.current_stage
        stages = WorkflowEngine.get_stages_for_pathway(db, application.pathway_code)
        
        stage_map = {s["stage_name"]: s for s in stages}
        
        if current_stage not in stage_map:
            return False, f"Current stage '{current_stage}' not configured in pathway '{application.pathway_code}'."
        if to_stage not in stage_map:
            return False, f"Target stage '{to_stage}' not recognized in pathway '{application.pathway_code}'."

        allowed_next = stage_map[current_stage].get("allowed_next", [])
        
        # Check if transition is defined in statechart
        if to_stage not in allowed_next and action_type not in ["ESCALATE", "ON_HOLD", "RESUME"]:
            return False, f"Transition from '{current_stage}' to '{to_stage}' is not permitted by pathway rules. Allowed: {allowed_next}"

        # Guard: Mandatory reason required for revert or return
        if (action_type == "REVERT" or to_stage == "RETURNED_FOR_CORRECTION") and not (mandatory_reason and mandatory_reason.strip()):
            return False, "A specific mandatory reason is legally required when returning or reverting an application."

        # Guard: Cannot approve with unverified documents or critical issues
        if to_stage == "APPROVED":
            from app.models.document import Document
            doc_count = db.query(Document).filter(Document.application_id == application.id).count()
            if doc_count < 2:
                return False, f"Statutory guard: Application has only {doc_count} documents uploaded. Minimum required documents not met."

        return True, "Transition validated."

    @staticmethod
    def transition_stage(
        db: Session,
        application_id: str,
        to_stage: str,
        actor_id: str,
        actor_role: str,
        action_type: str = "ADVANCE",
        mandatory_reason: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Application:
        """Executes a validated stage transition, logs immutable transition history, and triggers SLA realignment."""
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        is_valid, err_msg = WorkflowEngine.validate_transition(db, app, to_stage, action_type, mandatory_reason)
        if not is_valid:
            raise ValueError(err_msg)

        sim_now = clock_service.now(db)
        from_stage = app.current_stage

        # Create transition record
        transition = WorkflowTransition(
            id=str(uuid.uuid4()),
            application_id=app.id,
            from_stage=from_stage,
            to_stage=to_stage,
            action_type=action_type,
            actor_id=actor_id,
            actor_role=actor_role,
            mandatory_reason=mandatory_reason,
            notes=notes,
            created_at=sim_now
        )
        db.add(transition)

        # Update application state
        app.current_stage = to_stage
        app.stage_entered_at = sim_now
        app.updated_at = sim_now
        
        if to_stage in ["APPROVED", "REJECTED"]:
            app.sla_status = "RESOLVED"
        elif action_type == "REVERT" or to_stage == "RETURNED_FOR_CORRECTION":
            app.sla_status = "RETURNED"

        db.commit()
        db.refresh(app)

        # Log into audit ledger
        from app.services.audit_ledger import audit_ledger
        audit_ledger.record_event(
            db=db,
            event_type="STAGE_TRANSITION",
            entity_type="APPLICATION",
            entity_id=app.id,
            actor_id=actor_id,
            actor_role=actor_role,
            action_summary=f"{action_type} application {app.application_number} from {from_stage} to {to_stage}",
            previous_state=from_stage,
            new_state=to_stage,
            reason=mandatory_reason or notes,
            payload={"application_number": app.application_number, "action": action_type}
        )

        return app

workflow_engine = WorkflowEngine()
