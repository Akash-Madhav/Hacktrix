import os
import uuid
import json
import random
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, Base, engine
from app.models.application import Application, Program, LandDetail, BuiltupDetail
from app.models.document import Document
from app.models.validation import VerificationRecord, ValidationRun, Finding
from app.models.user import User
from app.models.workflow import WorkflowConfig, WorkflowTransition
from app.models.sla import SLARule, MonitoredTask, SLAEvent
from app.models.undertaking import Undertaking
from app.models.validity import ValidityRecord
from app.models.evc import EVCExpert, EVCPanel
from app.models.notification import Notification
from app.models.audit import AuditLedger
from app.models.system import SystemClock
from app.services.extractor import compute_sha256, extract_text_from_pdf
from app.services.tamper import analyze_pdf_metadata_and_integrity
from app.services.rules import run_deterministic_validation_engine
from app.services.verdict import compute_application_verdict
from app.services.workflow_engine import workflow_engine
from app.services.sla_engine import sla_engine
from app.services.calendar_service import calendar_service
from app.services.clock_service import clock_service
from app.services.audit_ledger import audit_ledger
from app.services.early_warning import early_warning
from app.services.evc_optimizer import evc_optimizer

def create_pdf(
    file_path: str,
    title: str,
    lines: list,
    creator: str = "Government Printing & Registration Dept",
    producer: str = "National e-Governance Division PDF Generator",
    creation_date: datetime = None,
    mod_date: datetime = None,
    add_extra_eof: bool = False
):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    c = canvas.Canvas(file_path, pagesize=letter)
    
    now = datetime.now()
    c_date = creation_date or now
    m_date = mod_date or now
    
    c.setTitle(title)
    c.setCreator(creator)
    c.setProducer(producer)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, 750, title)
    c.setLineWidth(1)
    c.line(60, 740, 540, 740)
    
    c.setFont("Helvetica", 11)
    y = 710
    for line in lines:
        if line.startswith("# "):
            c.setFont("Helvetica-Bold", 13)
            y -= 10
            c.drawString(60, y, line[2:])
            c.setFont("Helvetica", 11)
        elif line.startswith("- "):
            c.drawString(75, y, line)
        else:
            c.drawString(60, y, line)
        y -= 18
        if y < 60:
            c.showPage()
            y = 720
            c.setFont("Helvetica", 11)
            
    c.save()
    
    if add_extra_eof:
        with open(file_path, "ab") as f:
            f.write(b"\n%%EOF\n% AICTE PDF Tamper Demonstration Marker\n%%EOF\n")

def seed_users(db: Session) -> Dict[str, User]:
    users_data = [
        ("admin", "admin@aicte-niriksha.gov.in", "System Administrator", "ADMIN", None, False, None),
        ("bureau_officer", "bureau.chief@aicte-niriksha.gov.in", "Dr. K. S. Sundaram (Bureau Head)", "BUREAU_OFFICER", "All-India", False, None),
        ("ro_western", "ro.western@aicte-niriksha.gov.in", "Shri R. V. Deshmukh (Regional Officer)", "REGIONAL_OFFICER", "Western", False, None),
        ("ro_southern", "ro.southern@aicte-niriksha.gov.in", "Dr. P. Ramanathan (Regional Officer)", "REGIONAL_OFFICER", "Southern", False, None),
        ("officer_pune", "officer.pune@aicte-niriksha.gov.in", "Vikram More (Scrutiny Officer)", "SCRUTINY_OFFICER", "Western", False, None),
        ("officer_leave", "officer.leave@aicte-niriksha.gov.in", "Sunil Shinde (On Leave)", "SCRUTINY_OFFICER", "Western", True, datetime(2026, 11, 20)),
        ("registrar_aryabhata", "registrar@aryabhata.edu.in", "Registrar Aryabhata", "INSTITUTION", "Western", False, None),
    ]

    user_map = {}
    pune_user_id = None
    for username, email, name, role, region, on_leave, leave_until in users_data:
        u = db.query(User).filter(User.username == username).first()
        if not u:
            u = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                # Simple SHA-256 password hash for 'password123'
                password_hash="ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",
                full_name=name,
                role=role,
                region=region,
                is_on_leave=on_leave,
                leave_until=leave_until
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        user_map[username] = u
        if username == "officer_pune":
            pune_user_id = u.id

    # Set deputy for officer on leave
    if "officer_leave" in user_map and pune_user_id:
        user_map["officer_leave"].deputy_user_id = pune_user_id
        db.commit()

    return user_map

REGIONS_AND_STATES = [
    ("Western", "Maharashtra", "Pune"),
    ("Western", "Maharashtra", "Mumbai"),
    ("Western", "Goa", "Panaji"),
    ("Northern", "Uttar Pradesh", "Kanpur"),
    ("Northern", "Uttar Pradesh", "Ghaziabad"),
    ("Northern", "Uttarakhand", "Dehradun"),
    ("North-Western", "Punjab", "Ludhiana"),
    ("North-Western", "Haryana", "Gurugram"),
    ("North-Western", "Rajasthan", "Jaipur"),
    ("Central", "Madhya Pradesh", "Bhopal"),
    ("Central", "Madhya Pradesh", "Indore"),
    ("Central", "Chhattisgarh", "Raipur"),
    ("Eastern", "West Bengal", "Kolkata"),
    ("Eastern", "Bihar", "Patna"),
    ("Eastern", "Odisha", "Bhubaneswar"),
    ("Southern", "Tamil Nadu", "Chennai"),
    ("Southern", "Tamil Nadu", "Coimbatore"),
    ("South-Western", "Karnataka", "Bengaluru"),
    ("South-Western", "Kerala", "Thiruvananthapuram"),
    ("South-Central", "Telangana", "Hyderabad"),
    ("South-Central", "Andhra Pradesh", "Visakhapatnam")
]

INSTITUTION_NAMES_POOL = [
    "Swami Vivekananda Institute of Technology", "Rajarshi Shahu College of Engineering",
    "Netaji Subhas Technical University", "Sir C. V. Raman Institute of Applied Sciences",
    "Maharana Pratap College of Technology", "Chanakya School of Management Studies",
    "Dr. Homi Bhabha National Institute of Technology", "Sardar Patel Institute of Engineering",
    "Birla Technical Academy", "Rani Rashmoni College of Pharmacy",
    "Visvesvaraya Institute of Technology & Research", "Ashoka School of Advanced Studies",
    "Kalinga Institute of Industrial Engineering", "St. Xavier's Technical Campus",
    "Acharya P. C. Ray Institute of Technology", "Malviya Institute of Engineering & Tech",
    "Gautam Buddha College of Management", "Thiruvalluvar Institute of Technology",
    "Kakatiya Institute of Engineering & Applied Sciences", "Maratha Vidya Prasarak Institute of Tech",
    "Hindustan Institute of Engineering & Management", "Guru Gobind Singh College of Technology",
    "Dronacharya Institute of Engineering", "Vidyasagar Technical Campus",
    "Sri Aurobindo College of Engineering", "Karpagam Academy of Technical Studies",
    "PES Institute of Applied Technology", "Siddhartha Institute of Engineering & Tech",
    "Shivaji Maharaj Institute of Technology", "Lokmanya Tilak Technical College",
    "Meghnad Saha Engineering College", "Indira Gandhi Institute of Technology",
    "Bhilai Technical Institute", "Jabalpur Engineering & Management Academy",
    "Ranchi Technical Campus", "Bhubaneswar Engineering College",
    "Amrita Institute of Advanced Engineering", "PSG College of Applied Science & Tech",
    "Vellore Technical Campus", "Osmania Technical Institute",
    "JNTU Affiliated Institute of Technology", "Nalanda Institute of Technology",
    "Chaitanya Bharathi Technical College", "Andhra Loyola Institute of Tech",
    "Dayananda Sagar College of Engineering", "BMS Technical Academy",
    "RV College of Applied Studies", "Rajagiri School of Engineering",
    "Model Engineering College", "Saintgits Institute of Technology",
    "Chandigarh Technical Institute", "Jaipur National Technical College",
    "Poornima Institute of Engineering", "Kalaniketan Technical Institute",
    "IPS Academy of Engineering", "Rungta College of Engineering",
    "Techno India Technical Campus", "Heritage Institute of Technology",
    "Siliguri Institute of Technology", "Durgapur Institute of Advanced Studies"
]

def seed_database():
    """Initializes and seeds 60 diverse AICTE institutions with realistic formats and lifecycle states."""
    db = SessionLocal()
    try:
        print("[NIRIKSHA SEEDER] Initializing database tables and default configs...")
        Base.metadata.create_all(bind=engine)
        
        # 1. Ensure Clock & Holidays
        clock_service.get_clock(db)
        calendar_service.ensure_default_holidays(db, 2026)
        
        # 2. Ensure Statecharts & SLA Rules
        workflow_engine.ensure_default_configs(db)
        sla_engine.ensure_default_rules(db)
        evc_optimizer.ensure_default_experts(db)
        
        # 3. Seed Users
        user_map = seed_users(db)
        default_officer_id = user_map["officer_pune"].id
        leave_officer_id = user_map["officer_leave"].id

        # 4. Clean previous application records to ensure clean idempotent seeding
        db.query(Finding).delete()
        db.query(ValidationRun).delete()
        db.query(VerificationRecord).delete()
        db.query(Document).delete()
        db.query(Program).delete()
        db.query(LandDetail).delete()
        db.query(BuiltupDetail).delete()
        db.query(WorkflowTransition).delete()
        db.query(Undertaking).delete()
        db.query(ValidityRecord).delete()
        db.query(EVCPanel).delete()
        db.query(MonitoredTask).delete()
        db.query(Notification).delete()
        db.query(AuditLedger).delete()
        db.query(Application).delete()
        db.commit()

        print("[NIRIKSHA SEEDER] Seeding benchmark and 59 synthetic AICTE institutions (Total: 60)...")
        # Reset clock to a fixed demo start date in 2026 for consistent demo runs
        sim_now = clock_service.set_time(db, datetime(2026, 10, 1, 9, 0, 0))

        # SEED 1: Aryabhata Institute (COMPLIANT Benchmark)
        app_num_1 = "1-46273286079"
        perm_id_1 = "1-4627328"
        app1 = Application(
            id=str(uuid.uuid4()),
            application_number=app_num_1,
            institution_permanent_id=perm_id_1,
            eoa_file_number=f"Western/{app_num_1}/2026/EOA",
            institution_name="Aryabhata Institute of Technology & Science",
            institution_type="NEW_TECHNICAL_INSTITUTION",
            application_type="NEW_INSTITUTION",
            region="Western",
            state="Maharashtra",
            district="Pune",
            address="Plot No. 42, Hinjawadi Phase-II, Pune, Maharashtra 411057",
            pathway_code="PATHWAY_SCRUTINY_EVC",
            current_stage="INITIAL_SCRUTINY",
            assigned_officer_id=default_officer_id,
            priority="HIGH",
            sla_status="ACTIVE",
            stage_entered_at=sim_now - timedelta(days=2),
            created_at=sim_now - timedelta(days=2)
        )
        db.add(app1)
        db.flush()

        # Add programs, land, builtup
        prog1 = Program(id=str(uuid.uuid4()), application_id=app1.id, program_name="Computer Engineering", level="UG", approved_intake=120)
        land1 = LandDetail(id=str(uuid.uuid4()), application_id=app1.id, total_area_acres=8.5, is_single_plot=True, ownership_type="OWNED_GOVERNMENT_REGISTERED", survey_khasra_no="Survey-104/A", land_registration_date="2020-04-12")
        built1 = BuiltupDetail(id=str(uuid.uuid4()), application_id=app1.id, total_carpet_sqm=9200.0, instructional_area_sqm=5100.0, administrative_area_sqm=1800.0, amenities_area_sqm=2300.0)
        db.add_all([prog1, land1, built1])

        # Register task and audit event
        task1 = sla_engine.register_or_update_task(db, "APPLICATION", app1.id, f"{app1.institution_name} - Initial Scrutiny", "APPLICATION_STAGE", "INITIAL_SCRUTINY", default_officer_id, "MH")
        
        # Add a lease validity record for Aryabhata (expires in 30 days)
        val1 = ValidityRecord(
            id=str(uuid.uuid4()),
            institution_id=perm_id_1,
            document_type="LEASE_DEED",
            certificate_number="LD-MH-2021-99812",
            issuing_authority="Sub-Registrar Haveli, Pune",
            valid_from=sim_now - timedelta(days=365*5),
            expiry_date=sim_now + timedelta(days=30), # T-30 trigger!
            status="EXPIRING_SOON"
        )
        db.add(val1)

        # Add an undertaking for Aryabhata
        und1 = Undertaking(
            id=str(uuid.uuid4()),
            undertaking_number="UND-2026-0041",
            application_id=app1.id,
            institution_id=perm_id_1,
            category="FACULTY_RECRUITMENT",
            title="Recruitment of Cadre-Ratio Certified Professors in AI/ML",
            undertaking_text="The institution undertakes to appoint 2 full-time Professors and 4 Associate Professors within 90 days of EoA grant.",
            issued_date=sim_now - timedelta(days=15),
            due_date=sim_now + timedelta(days=75),
            compliance_status="PENDING"
        )
        db.add(und1)

        # Audit
        audit_ledger.record_event(
            db=db,
            event_type="APPLICATION_SUBMITTED",
            entity_type="APPLICATION",
            entity_id=app1.id,
            actor_id=user_map["registrar_aryabhata"].id,
            actor_role="INSTITUTION",
            action_summary=f"Submitted new institution application {app_num_1} under Scrutiny+EVC pathway",
            new_state="INITIAL_SCRUTINY",
            payload={"institution": app1.institution_name, "acres": 8.5}
        )

        # Generate synthetic PDF documents for Aryabhata
        pdf_dir = settings.SYNTHETIC_DIR / f"app-{app1.id[:8]}"
        os.makedirs(pdf_dir, exist_ok=True)
        doc1_path = str(pdf_dir / "land_deed.pdf")
        create_pdf(doc1_path, "REGISTERED SALE DEED & TITLE CONVEYANCE", [
            "# GOVERNMENT OF MAHARASHTRA - REGISTRATION DEPARTMENT",
            "This document certifies that the land bearing Survey-104/A measuring 8.50 Acres",
            "is legally owned and registered in the name of Aryabhata Trust.",
            "- Total Area: 8.50 Acres",
            "- Single Contiguous Plot: YES",
            "- Encumbrance Certificate: NIL DEFICIENCY"
        ])
        doc1 = Document(
            id=str(uuid.uuid4()),
            application_id=app1.id,
            document_type="LAND_REGISTRATION",
            file_path=doc1_path,
            original_filename="land_deed.pdf",
            sha256_hash=compute_sha256(doc1_path),
            mime_type="application/pdf",
            file_size_bytes=os.path.getsize(doc1_path),
            extracted_text=extract_text_from_pdf(doc1_path),
            metadata_json=json.dumps(analyze_pdf_metadata_and_integrity(doc1_path, "LAND_REGISTRATION"))
        )
        db.add(doc1)

        # 5. Programmatically seed remaining 59 institutions with realistic distribution
        stages_cycle = [
            ("INITIAL_SCRUTINY", 4, 15, "ACTIVE"),
            ("INITIAL_SCRUTINY", 13, 15, "DUE_SOON"),
            ("INITIAL_SCRUTINY", 18, 15, "OVERDUE"),
            ("EVC_INSPECTION", 19, 15, "ESCALATED"),
            ("RETURNED_FOR_CORRECTION", 3, 10, "RETURNED"),
            ("RE_SCRUTINY", 5, 7, "ACTIVE"),
            ("REGIONAL_COMMITTEE", 8, 10, "DUE_SOON"),
            ("SAC_SHC", 12, 15, "ACTIVE"),
            ("APPROVED", 15, 0, "RESOLVED")
        ]

        for idx, inst_name in enumerate(INSTITUTION_NAMES_POOL[:59]):
            reg_info = REGIONS_AND_STATES[idx % len(REGIONS_AND_STATES)]
            region, state, district = reg_info
            
            perm_id = f"1-{3000000 + idx * 173}"
            app_number = f"1-{46000000000 + idx * 831}"
            
            stage_tuple = stages_cycle[idx % len(stages_cycle)]
            curr_stage, days_spent, max_sla, status = stage_tuple
            
            # Use officer on leave for every 7th application to test auto-delegation!
            assigned_officer = leave_officer_id if (idx % 7 == 0) else default_officer_id
            
            pathway = "PATHWAY_SCRUTINY_EVC" if (idx % 3 != 0) else "PATHWAY_SCRUTINY_ONLY"
            
            app_entry = Application(
                id=str(uuid.uuid4()),
                application_number=app_number,
                institution_permanent_id=perm_id,
                eoa_file_number=f"{region}/{app_number}/2026/EOA",
                institution_name=inst_name,
                institution_type="TECHNICAL_INSTITUTION",
                application_type="EXTENSION_OF_APPROVAL" if idx % 2 == 0 else "NEW_INSTITUTION",
                region=region,
                state=state,
                district=district,
                address=f"Campus Plot {10 + idx}, Knowledge Park, {district}, {state}",
                pathway_code=pathway,
                current_stage=curr_stage,
                assigned_officer_id=assigned_officer,
                priority="HIGH" if status in ["OVERDUE", "ESCALATED"] else "NORMAL",
                sla_status=status,
                stage_entered_at=sim_now - timedelta(days=days_spent),
                created_at=sim_now - timedelta(days=days_spent + 5)
            )
            db.add(app_entry)
            db.flush()

            # Land & built-up details
            acres = round(7.5 + (idx % 5) * 0.8, 2)
            carpet = round(6200.0 + (idx % 6) * 500, 1)
            land_e = LandDetail(
                id=str(uuid.uuid4()),
                application_id=app_entry.id,
                total_area_acres=acres,
                is_single_plot=True,
                ownership_type="OWNED_GOVERNMENT_REGISTERED",
                survey_khasra_no=f"Survey-{200 + idx}/1",
                land_registration_date="2018-06-15"
            )
            built_e = BuiltupDetail(
                id=str(uuid.uuid4()),
                application_id=app_entry.id,
                total_carpet_sqm=carpet,
                instructional_area_sqm=carpet * 0.55,
                administrative_area_sqm=carpet * 0.20,
                amenities_area_sqm=carpet * 0.25
            )
            prog_e = Program(
                id=str(uuid.uuid4()),
                application_id=app_entry.id,
                program_name="Mechanical Engineering" if idx % 2 == 0 else "Information Technology",
                level="UG",
                approved_intake=60 if idx % 2 == 0 else 120
            )
            db.add_all([land_e, built_e, prog_e])

            # Monitored Task
            due_date = app_entry.stage_entered_at + timedelta(days=max_sla)
            task_entry = MonitoredTask(
                id=str(uuid.uuid4()),
                task_number=f"TSK-APP-{app_number[-6:]}",
                entity_type="APPLICATION",
                entity_id=app_entry.id,
                title=f"{inst_name} - {curr_stage.replace('_', ' ').title()}",
                process_category="APPLICATION_STAGE",
                current_stage=curr_stage,
                assigned_officer_id=assigned_officer,
                start_date=app_entry.stage_entered_at,
                calculated_due_date=due_date,
                status=status,
                working_days_elapsed=days_spent,
                working_days_remaining=max_sla - days_spent,
                calendar_days_remaining=(due_date.date() - sim_now.date()).days,
                escalation_level=2 if status == "ESCALATED" else (1 if status == "OVERDUE" and days_spent > 16 else 0),
                created_at=app_entry.stage_entered_at
            )
            db.add(task_entry)

            # Compute early warning risk score
            early_warning.compute_risk(db, task_entry, app_entry)

            # Add sample undertakings for ~10 institutions
            if idx % 6 == 0:
                und = Undertaking(
                    id=str(uuid.uuid4()),
                    undertaking_number=f"UND-2026-{1000 + idx}",
                    application_id=app_entry.id,
                    institution_id=perm_id,
                    category="LAB_EQUIPMENT_UPGRADE" if idx % 12 == 0 else "FACULTY_RECRUITMENT",
                    title=f"Statutory Undertaking for {inst_name}",
                    undertaking_text="The institution guarantees full procurement of advanced computing cluster equipment.",
                    issued_date=sim_now - timedelta(days=20),
                    due_date=sim_now + timedelta(days=40 if idx % 4 != 0 else -3), # Some overdue!
                    compliance_status="BREACHED" if idx % 4 == 0 else "PENDING"
                )
                db.add(und)

            # Add sample validity records (leases/NOCs) for ~12 institutions
            if idx % 5 == 0:
                is_expired = (idx % 10 == 0)
                val_rec = ValidityRecord(
                    id=str(uuid.uuid4()),
                    institution_id=perm_id,
                    document_type="LEASE_DEED" if idx % 2 == 0 else "FIRE_SAFETY_NOC",
                    certificate_number=f"NOC-{state[:2].upper()}-2024-{3000 + idx}",
                    issuing_authority=f"State Disaster Management Authority, {state}",
                    valid_from=sim_now - timedelta(days=365*3),
                    expiry_date=sim_now + timedelta(days=-5 if is_expired else (15 if idx % 2 == 0 else 75)),
                    status="OVERDUE_EXPIRED" if is_expired else ("EXPIRING_SOON" if idx % 2 == 0 else "VALID"),
                    last_reminder_offset="T-15" if idx % 2 == 0 else None
                )
                db.add(val_rec)

            # Add sample EVC panel proposals for ~6 institutions
            if curr_stage == "EVC_INSPECTION":
                evc_optimizer.optimize_panel_for_application(db, app_entry.id)

        db.commit()
        
        # 6. Re-evaluate all tasks to align with clock
        print("[NIRIKSHA SEEDER] Running global SLA sweep across all 60 institutions...")
        eval_summary = sla_engine.evaluate_all_tasks(db)
        print(f"[NIRIKSHA SEEDER] Seeding complete! Active SLA Summary: {eval_summary}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
