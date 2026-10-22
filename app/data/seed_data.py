import os
import uuid
import json
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, Base, engine
from app.models.application import Application, Program, LandDetail, BuiltupDetail
from app.models.document import Document
from app.models.validation import VerificationRecord, ValidationRun, Finding
from app.services.extractor import compute_sha256, extract_text_from_pdf
from app.services.tamper import analyze_pdf_metadata_and_integrity
from app.services.rules import run_deterministic_validation_engine
from app.services.verdict import compute_application_verdict

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
    
    # Metadata
    now = datetime.utcnow()
    c_date = creation_date or now
    m_date = mod_date or now
    
    c.setTitle(title)
    c.setCreator(creator)
    c.setProducer(producer)
    
    # Draw header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, 750, title)
    c.setLineWidth(1)
    c.line(60, 740, 540, 740)
    
    c.setFont("Helvetica", 11)
    y = 710
    for line in lines:
        if line.startswith("# "):
            c.setFont("Helvetica-Bold", 13)
            c.drawString(60, y, line[2:])
            c.setFont("Helvetica", 11)
            y -= 22
        elif line.startswith("• "):
            c.drawString(75, y, line)
            y -= 18
        else:
            c.drawString(60, y, line)
            y -= 18
            
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(60, 50, f"Document verification ref: {os.path.basename(file_path)} | Generated for AICTE Scrutiny Dossier")
    c.save()

    # If tampering / incremental update simulation requested
    if add_extra_eof:
        with open(file_path, "ab") as f:
            f.write(b"\n% Incremental revision edit 2\n")
            f.write(b"10 0 obj\n<< /Type /Annot /Subtype /Text /Contents (Post-issuance alteration) >>\nendobj\n")
            f.write(b"xref\n0 1\n0000000000 65535 f \ntrailer\n<< /Size 11 /Root 1 0 R >>\nstartxref\n1200\n%%EOF\n")
            f.write(b"\n% Incremental revision edit 3 via third-party web tool\n")
            f.write(b"11 0 obj\n<< /Type /Annot /Subtype /FreeText >>\nendobj\n")
            f.write(b"trailer\n<< /Size 12 >>\nstartxref\n1400\n%%EOF\n")

def seed_database():
    """Generates synthetic applications, generates PDFs, and runs initial validation runs."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Clear existing
    db.query(Finding).delete()
    db.query(ValidationRun).delete()
    db.query(VerificationRecord).delete()
    db.query(Document).delete()
    db.query(Program).delete()
    db.query(LandDetail).delete()
    db.query(BuiltupDetail).delete()
    db.query(Application).delete()
    db.commit()

    print("--- Generating Synthetic PDFs & Applications ---")
    synth_dir = settings.SYNTHETIC_DIR

    # =========================================================================
    # APP 1: Compliant Institution (Aryabhata Institute of Technology)
    # =========================================================================
    app1_id = "app-001-aryabhata"
    app1 = Application(
        id=app1_id,
        application_number="AICTE/2024/APP-001-COMPLIANT",
        institution_name="Aryabhata Institute of Technology & Management",
        institution_type="NEW_TECHNICAL_INSTITUTION",
        application_type="NEW_INSTITUTION",
        state="Maharashtra",
        district="Pune",
        address="Survey No. 142/1, Knowledge Park, Hinjewadi Phase 3, Pune - 411057"
    )
    db.add(app1)

    p1 = Program(id=str(uuid.uuid4()), application_id=app1_id, program_name="Computer Science & Engineering", level="UG", approved_intake=120)
    p2 = Program(id=str(uuid.uuid4()), application_id=app1_id, program_name="Electronics & Communication", level="UG", approved_intake=60)
    db.add_all([p1, p2])

    ld1 = LandDetail(
        id=str(uuid.uuid4()),
        application_id=app1_id,
        total_area_acres=8.5,
        is_single_plot=True,
        ownership_type="OWNED_GOVERNMENT_REGISTERED",
        survey_khasra_no="Survey No. 142/1",
        land_registration_date="2022-03-15"
    )
    db.add(ld1)

    bd1 = BuiltupDetail(
        id=str(uuid.uuid4()),
        application_id=app1_id,
        total_carpet_sqm=9200.0,
        instructional_area_sqm=4800.0,
        administrative_area_sqm=2200.0,
        amenities_area_sqm=2200.0
    )
    db.add(bd1)

    # Compliant PDFs
    f1_land = str(synth_dir / "app1_land_deed.pdf")
    create_pdf(f1_land, "GOVERNMENT OF MAHARASHTRA - SUB REGISTRAR OFFICE", [
        "# REGISTERED SALE DEED FOR EDUCATIONAL PURPOSE",
        "Registration Number: PNE-SUB-2022-99120",
        "This deed confirms absolute freehold ownership of land parcel in favour of:",
        "Aryabhata Educational Trust for establishing Aryabhata Institute of Technology.",
        "",
        "• Survey Number: Survey No. 142/1",
        "• Total Land Area: 8.5 Acres (Single contiguous parcel)",
        "• Nature of Possession: Freehold with unencumbered clear title.",
        "• Sub-Registrar Seal: Haveli Pune, 15 March 2022."
    ])

    f1_bldg = str(synth_dir / "app1_building_plan.pdf")
    create_pdf(f1_bldg, "PUNE METROPOLITAN REGION DEVELOPMENT AUTHORITY", [
        "# SANCTIONED MASTER BUILDING PLAN APPROVAL",
        "Sanction Reference: PMRDA/BP/2023/4412",
        "Institutional Building Layout Approval granted for Technical Education Campus.",
        "",
        "• Total Carpet Area: 9200 Sq.m",
        "• Instructional Area: 4800 Sqm",
        "• Administrative Area: 2200 Sqm",
        "• Structural Stability Certificate: Enclosed by Chief Town Planner."
    ])

    f1_fire = str(synth_dir / "app1_fire_noc.pdf")
    create_pdf(f1_fire, "MAHARASHTRA FIRE SERVICES - FIRE SAFETY NOC", [
        "# FIRE SAFETY COMPLIANCE NO OBJECTION CERTIFICATE",
        "NOC Number: MFS/PUN/2023/8821",
        "Institution Name: Aryabhata Institute of Technology & Management",
        "Validity Date: Valid up to: 31-12-2027",
        "",
        "Certified that the premises has installed automatic sprinkler systems, fire hydrants,",
        "and adequate emergency egress stairways in full compliance with National Building Code."
    ])

    f1_affidavit = str(synth_dir / "app1_affidavit.pdf")
    create_pdf(f1_affidavit, "NOTARIZED STATUTORY AFFIDAVIT", [
        "# AFFIDAVIT UNDER AICTE APPROVAL PROCESS HANDBOOK 2024-25",
        "Deponent: Chairman, Aryabhata Educational Trust",
        "We solemnly affirm that the institution shall be run strictly on a non-profit basis,",
        "the land is unencumbered and all infrastructure standards strictly adhere to AICTE norms."
    ])

    f1_arch = str(synth_dir / "app1_architect_cert.pdf")
    create_pdf(f1_arch, "COUNCIL OF ARCHITECTURE - ACCREDITED REPORT", [
        "# ARCHITECT BARRIER-FREE BUILT-UP ENVIRONMENT CERTIFICATE",
        "Architect Reg. No: CA/2012/58129",
        "Institution: Aryabhata Institute of Technology & Management",
        "Certified that total instructional carpet area exceeds 4500 sqm with full barrier-free ramps and elevators."
    ])

    # Save docs for app1
    for path, dtype, orig_name in [
        (f1_land, "LAND_REGISTRATION", "Registered_Land_Deed_Pune_142_1.pdf"),
        (f1_bldg, "BUILDING_PLAN_APPROVAL", "PMRDA_Sanctioned_Building_Plan.pdf"),
        (f1_fire, "FIRE_SAFETY_NOC", "State_Fire_Safety_NOC_2023.pdf"),
        (f1_affidavit, "AFFIDAVIT_TRUST", "Aryabhata_Trust_Affidavit.pdf"),
        (f1_arch, "ARCHITECT_CERTIFICATE", "Architect_Accessibility_Certificate.pdf")
    ]:
        txt = extract_text_from_pdf(path)
        sha = compute_sha256(path)
        meta = analyze_pdf_metadata_and_integrity(path, dtype)
        d = Document(
            id=str(uuid.uuid4()),
            application_id=app1_id,
            document_type=dtype,
            file_path=path,
            original_filename=orig_name,
            sha256_hash=sha,
            upload_status="PROCESSED",
            mime_type="application/pdf",
            file_size_bytes=os.path.getsize(path),
            extracted_text=txt,
            metadata_json=json.dumps(meta)
        )
        db.add(d)

    # Simulated verification records for app 1
    vr1 = VerificationRecord(
        id=str(uuid.uuid4()),
        application_id=app1_id,
        verification_type="STATE_LAND_REVENUE_PORTAL",
        external_reference_id="MAHA-BHOOMI-PNE-142-1",
        simulated_status="MATCH",
        simulated_response_json=json.dumps({"owner": "Aryabhata Educational Trust", "status": "CLEAR_TITLE", "area_acres": 8.5})
    )
    vr2 = VerificationRecord(
        id=str(uuid.uuid4()),
        application_id=app1_id,
        verification_type="MUNICIPAL_TOWN_PLANNING_SYSTEM",
        external_reference_id="PMRDA/BP/2023/4412",
        simulated_status="MATCH",
        simulated_response_json=json.dumps({"plan_status": "APPROVED", "carpet_area_sqm": 9200})
    )
    vr3 = VerificationRecord(
        id=str(uuid.uuid4()),
        application_id=app1_id,
        verification_type="FIRE_SERVICE_DIRECTORATE",
        external_reference_id="MFS/PUN/2023/8821",
        simulated_status="MATCH",
        simulated_response_json=json.dumps({"noc_status": "VALID", "valid_until": "2027-12-31"})
    )
    db.add_all([vr1, vr2, vr3])

    # =========================================================================
    # APP 2: Incomplete Institution (Vikas Technical Academy - Missing 3 Docs)
    # =========================================================================
    app2_id = "app-002-vikas"
    app2 = Application(
        id=app2_id,
        application_number="AICTE/2024/APP-002-INCOMPLETE",
        institution_name="Vikas Technical Academy",
        institution_type="NEW_TECHNICAL_INSTITUTION",
        application_type="NEW_INSTITUTION",
        state="Karnataka",
        district="Bengaluru Rural",
        address="Khasra No. 89/2, Devanahalli Industrial Corridor, Bengaluru"
    )
    db.add(app2)

    p3 = Program(id=str(uuid.uuid4()), application_id=app2_id, program_name="Mechanical Engineering", level="UG", approved_intake=60)
    db.add(p3)

    ld2 = LandDetail(
        id=str(uuid.uuid4()),
        application_id=app2_id,
        total_area_acres=7.8,
        is_single_plot=True,
        ownership_type="OWNED_GOVERNMENT_REGISTERED",
        survey_khasra_no="Khasra No. 89/2",
        land_registration_date="2023-01-10"
    )
    db.add(ld2)

    bd2 = BuiltupDetail(
        id=str(uuid.uuid4()),
        application_id=app2_id,
        total_carpet_sqm=7500.0,
        instructional_area_sqm=3900.0,
        administrative_area_sqm=1800.0,
        amenities_area_sqm=1800.0
    )
    db.add(bd2)

    f2_land = str(synth_dir / "app2_land_deed.pdf")
    create_pdf(f2_land, "DEPARTMENT OF STAMPS & REGISTRATION - KARNATAKA", [
        "# REGISTERED TITLE DEED",
        "Registration No: BNG-DEV-2023-7721",
        "Vikas Educational Society",
        "• Survey Number: Khasra No. 89/2",
        "• Total Land Area: 7.8 Acres"
    ])

    f2_affidavit = str(synth_dir / "app2_affidavit.pdf")
    create_pdf(f2_affidavit, "NOTARIZED AFFIDAVIT - VIKAS SOCIETY", [
        "# AFFIDAVIT OF TRUSTEES",
        "Deponent: Secretary, Vikas Educational Society"
    ])

    # Note: Deliberately MISSING Building Plan, Fire NOC, and Architect Certificate!
    for path, dtype, orig_name in [
        (f2_land, "LAND_REGISTRATION", "Vikas_Registered_Deed_89_2.pdf"),
        (f2_affidavit, "AFFIDAVIT_TRUST", "Vikas_Trust_Affidavit.pdf")
    ]:
        txt = extract_text_from_pdf(path)
        sha = compute_sha256(path)
        meta = analyze_pdf_metadata_and_integrity(path, dtype)
        d = Document(
            id=str(uuid.uuid4()),
            application_id=app2_id,
            document_type=dtype,
            file_path=path,
            original_filename=orig_name,
            sha256_hash=sha,
            upload_status="PROCESSED",
            mime_type="application/pdf",
            file_size_bytes=os.path.getsize(path),
            extracted_text=txt,
            metadata_json=json.dumps(meta)
        )
        db.add(d)

    # =========================================================================
    # APP 3: Deficient & Tampered Institution (Shree Ram Engineering College)
    # Discrepancies:
    # 1. Land stated in app: 8.0 acres vs Deed extracted: 5.2 acres (Deficit & Mismatch)
    # 2. Survey No mismatch: App: "Plot-88" vs Deed: "Plot-12/A"
    # 3. Builtup area deficit: Carpet 5200 sqm < 6000 sqm norm
    # 4. Tampering: Fire NOC generated with suspicious producer ("Canva Web Tool") + 3 incremental %%EOF updates!
    # 5. External verification: Fire department status = MISMATCH
    # =========================================================================
    app3_id = "app-003-shree-ram"
    app3 = Application(
        id=app3_id,
        application_number="AICTE/2024/APP-003-ISSUES",
        institution_name="Shree Ram Engineering College",
        institution_type="NEW_TECHNICAL_INSTITUTION",
        application_type="NEW_INSTITUTION",
        state="Uttar Pradesh",
        district="Ghaziabad",
        address="Plot-88, Knowledge Zone, Industrial Area, Ghaziabad - 201001"
    )
    db.add(app3)

    p4 = Program(id=str(uuid.uuid4()), application_id=app3_id, program_name="Civil Engineering", level="UG", approved_intake=60)
    db.add(p4)

    ld3 = LandDetail(
        id=str(uuid.uuid4()),
        application_id=app3_id,
        total_area_acres=8.0, # Claimed 8.0 in app
        is_single_plot=True,
        ownership_type="OWNED_GOVERNMENT_REGISTERED",
        survey_khasra_no="Plot-88", # Claimed Plot-88
        land_registration_date="2021-08-20"
    )
    db.add(ld3)

    bd3 = BuiltupDetail(
        id=str(uuid.uuid4()),
        application_id=app3_id,
        total_carpet_sqm=5200.0, # Deficit! Below 6000 sqm
        instructional_area_sqm=2600.0, # Deficit! Below 3000 sqm
        administrative_area_sqm=1300.0,
        amenities_area_sqm=1300.0
    )
    db.add(bd3)

    # Discrepant land deed: actual text has 5.2 acres and Plot-12/A
    f3_land = str(synth_dir / "app3_land_deed_discrepant.pdf")
    create_pdf(f3_land, "SUB REGISTRAR REGISTRATION OFFICE - GHAZIABAD", [
        "# REGISTERED SALE DEED",
        "Document Reg No: GZB-2021-4410",
        "Purchaser: Shree Ram Charitable Society",
        "",
        "• Survey Number: Plot-12/A",
        "• Total Land Area: 5.2 Acres",
        "• Land usage: Agricultural converted."
    ])

    f3_bldg = str(synth_dir / "app3_building_plan.pdf")
    create_pdf(f3_bldg, "GHAZIABAD DEVELOPMENT AUTHORITY", [
        "# SANCTIONED BUILDING PLAN",
        "• Total Carpet Area: 5200 Sq.m",
        "• Instructional Area: 2600 Sqm"
    ])

    # Tampered Fire NOC: Canva producer + 3 %%EOF incremental updates!
    f3_fire = str(synth_dir / "app3_fire_noc_altered.pdf")
    create_pdf(
        f3_fire,
        "FIRE & EMERGENCY SERVICES - NOC",
        [
            "# FIRE SAFETY CERTIFICATE",
            "NOC Number: FS/UP/2024/9912",
            "Valid up to: 31-12-2026",
            "Certified that premises inspected and verified."
        ],
        creator="Canva Design Studio Web",
        producer="Canva PDF Renderer v4.1 / PDFescape Post-Editor",
        add_extra_eof=True
    )

    f3_affidavit = str(synth_dir / "app3_affidavit.pdf")
    create_pdf(f3_affidavit, "AFFIDAVIT - SHREE RAM SOCIETY", [
        "# TRUST AFFIDAVIT",
        "Deponent: Secretary, Shree Ram Educational Society"
    ])

    f3_arch = str(synth_dir / "app3_architect_cert.pdf")
    create_pdf(f3_arch, "ARCHITECT CERTIFICATE", [
        "# ACCESSIBILITY CERTIFICATE",
        "Architect CA/2018/99112"
    ])

    for path, dtype, orig_name in [
        (f3_land, "LAND_REGISTRATION", "Registered_Deed_Discrepant_5_2Acres.pdf"),
        (f3_bldg, "BUILDING_PLAN_APPROVAL", "GDA_Sanctioned_Plan_5200sqm.pdf"),
        (f3_fire, "FIRE_SAFETY_NOC", "State_Fire_NOC_Altered_Canva.pdf"),
        (f3_affidavit, "AFFIDAVIT_TRUST", "Shree_Ram_Affidavit.pdf"),
        (f3_arch, "ARCHITECT_CERTIFICATE", "Architect_Certificate.pdf")
    ]:
        txt = extract_text_from_pdf(path)
        sha = compute_sha256(path)
        meta = analyze_pdf_metadata_and_integrity(path, dtype)
        d = Document(
            id=str(uuid.uuid4()),
            application_id=app3_id,
            document_type=dtype,
            file_path=path,
            original_filename=orig_name,
            sha256_hash=sha,
            upload_status="PROCESSED",
            mime_type="application/pdf",
            file_size_bytes=os.path.getsize(path),
            extracted_text=txt,
            metadata_json=json.dumps(meta)
        )
        db.add(d)

    # Simulated verification record showing MISMATCH for Fire NOC
    vr_app3 = VerificationRecord(
        id=str(uuid.uuid4()),
        application_id=app3_id,
        verification_type="STATE_FIRE_SERVICES_PORTAL",
        external_reference_id="FS/UP/2024/9912",
        simulated_status="MISMATCH",
        simulated_response_json=json.dumps({"error": "Certificate number exists for commercial mall, not educational institute."})
    )
    db.add(vr_app3)

    db.commit()
    print("Database seeded successfully with 3 diverse applications!")

    # Now execute initial validation runs on all 3
    print("Running initial validation runs & verdicts on all 3 applications...")
    for app_obj in [app1, app2, app3]:
        run_id = f"run-{app_obj.id}"
        run = ValidationRun(
            id=run_id,
            application_id=app_obj.id,
            run_timestamp=datetime.utcnow(),
            rule_version="APH-2024-V1.0",
            engine_mode="DETERMINISTIC_RULES",
            status="COMPLETED",
            overall_readiness="PENDING"
        )
        db.add(run)
        db.commit()

        findings = run_deterministic_validation_engine(db, app_obj.id, run_id)
        for f in findings:
            db.add(f)
        db.commit()

        verdict = compute_application_verdict(db, run_id)
        print(f"[{app_obj.application_number}] => Verdict: {verdict.overall_readiness} (Score: {verdict.readiness_score_pct}%)")

    db.close()
    print("Seeding and initial validation completed successfully!")

if __name__ == "__main__":
    seed_database()
