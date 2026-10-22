import os
import uuid
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.config import settings
from app.models.application import Application, Program, LandDetail, BuiltupDetail
from app.models.document import Document
from app.models.validation import VerificationRecord, ValidationRun, Finding
from app.schemas.application import ApplicationCreate
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

def create_and_provision_institution(db: Session, payload: ApplicationCreate) -> Application:
    """
    Creates an institution application, attaches details, provisions scenario documents if requested,
    and runs initial compliance validation.
    """
    app_id = f"app-{uuid.uuid4().hex[:8]}"
    app = Application(
        id=app_id,
        application_number=payload.application_number,
        institution_name=payload.institution_name,
        institution_type=payload.institution_type,
        application_type=payload.application_type,
        state=payload.state,
        district=payload.district,
        address=payload.address
    )
    db.add(app)

    # Programs
    for p in payload.programs:
        prog = Program(
            id=str(uuid.uuid4()),
            application_id=app_id,
            program_name=p.program_name,
            level=p.level,
            approved_intake=p.approved_intake
        )
        db.add(prog)

    # Land
    if payload.land_detail:
        ld = LandDetail(
            id=str(uuid.uuid4()),
            application_id=app_id,
            total_area_acres=payload.land_detail.total_area_acres,
            is_single_plot=payload.land_detail.is_single_plot,
            ownership_type=payload.land_detail.ownership_type,
            survey_khasra_no=payload.land_detail.survey_khasra_no,
            land_registration_date=payload.land_detail.land_registration_date
        )
        db.add(ld)

    # Builtup
    if payload.builtup_detail:
        bd = BuiltupDetail(
            id=str(uuid.uuid4()),
            application_id=app_id,
            total_carpet_sqm=payload.builtup_detail.total_carpet_sqm,
            instructional_area_sqm=payload.builtup_detail.instructional_area_sqm,
            administrative_area_sqm=payload.builtup_detail.administrative_area_sqm,
            amenities_area_sqm=payload.builtup_detail.amenities_area_sqm
        )
        db.add(bd)

    db.commit()
    db.refresh(app)

    # Document generation based on test_scenario
    scenario = (payload.test_scenario or "COMPLIANT").upper()
    if scenario != "NONE":
        provision_scenario_documents(db, app, scenario)

    # Auto validate if requested
    if payload.auto_validate:
        run_id = f"run-{app_id}"
        run = ValidationRun(
            id=run_id,
            application_id=app_id,
            run_timestamp=datetime.utcnow(),
            rule_version="APH-2024-V1.0",
            engine_mode="DETERMINISTIC_RULES",
            status="COMPLETED",
            overall_readiness="PENDING"
        )
        db.add(run)
        db.commit()

        findings = run_deterministic_validation_engine(db, app_id, run_id)
        for f in findings:
            db.add(f)
        db.commit()

        compute_application_verdict(db, run_id)
        db.commit()

    db.refresh(app)
    return app

def provision_scenario_documents(db: Session, app: Application, scenario: str):
    """Generates synthetic statutory PDFs and verification records according to the test scenario."""
    synth_dir = settings.SYNTHETIC_DIR / app.id
    synth_dir.mkdir(parents=True, exist_ok=True)

    land_acres = app.land_detail.total_area_acres if app.land_detail else 8.0
    survey_no = app.land_detail.survey_khasra_no if app.land_detail else "Survey No. 101/A"
    carpet_sqm = app.builtup_detail.total_carpet_sqm if app.builtup_detail else 8500.0
    instructional_sqm = app.builtup_detail.instructional_area_sqm if app.builtup_detail else 4500.0

    docs_to_generate = []
    verif_records = []

    if scenario == "COMPLIANT":
        # 1. Land Deed
        f_land = str(synth_dir / f"{app.id}_land_deed.pdf")
        create_pdf(f_land, f"GOVERNMENT OF {app.state.upper()} - SUB REGISTRAR OFFICE", [
            "# REGISTERED SALE DEED FOR EDUCATIONAL PURPOSE",
            f"Registration Number: REG-{app.state[:3].upper()}-2023-8841",
            f"This registered deed confirms absolute freehold ownership of land parcel in favour of:",
            f"{app.institution_name} Trust for establishing technical education campus.",
            "",
            f"• Survey Number: {survey_no}",
            f"• Total Land Area: {land_acres} Acres (Single contiguous parcel)",
            "• Nature of Possession: Freehold with unencumbered clear title.",
            "• Sub-Registrar Seal & Attestation: Verified in Revenue Records."
        ])
        docs_to_generate.append((f_land, "LAND_REGISTRATION", f"{app.institution_name[:15].strip()}_Land_Deed.pdf"))

        # 2. Building Plan
        f_bldg = str(synth_dir / f"{app.id}_building_plan.pdf")
        create_pdf(f_bldg, f"{app.district.upper()} TOWN & COUNTRY PLANNING AUTHORITY", [
            "# SANCTIONED MASTER BUILDING PLAN APPROVAL",
            f"Sanction Reference: TCP/{app.district[:3].upper()}/2023/9102",
            f"Institutional Campus Building Plan sanctioned for {app.institution_name}.",
            "",
            f"• Total Carpet Area: {carpet_sqm} Sq.m",
            f"• Instructional Area: {instructional_sqm} Sqm",
            "• Administrative Area: 2000 Sqm",
            "• Structural Stability Certificate: Enclosed by Municipal Town Planner."
        ])
        docs_to_generate.append((f_bldg, "BUILDING_PLAN_APPROVAL", "Sanctioned_Building_Plan.pdf"))

        # 3. Fire NOC
        f_fire = str(synth_dir / f"{app.id}_fire_noc.pdf")
        create_pdf(f_fire, f"{app.state.upper()} STATE FIRE & EMERGENCY SERVICES", [
            "# FIRE SAFETY COMPLIANCE NO OBJECTION CERTIFICATE",
            f"NOC Number: MFS/{app.district[:3].upper()}/2024/7744",
            f"Institution Name: {app.institution_name}",
            "Validity Date: Valid up to: 31-12-2028",
            "",
            "Premises verified with compliant emergency exits, smoke detection, and sprinkler systems."
        ])
        docs_to_generate.append((f_fire, "FIRE_SAFETY_NOC", "State_Fire_Safety_NOC.pdf"))

        # 4. Affidavit
        f_aff = str(synth_dir / f"{app.id}_affidavit.pdf")
        create_pdf(f_aff, "NOTARIZED STATUTORY AFFIDAVIT", [
            "# AFFIDAVIT UNDER AICTE APPROVAL PROCESS HANDBOOK 2024-25",
            f"Deponent: Chairman, {app.institution_name} Educational Society",
            "We solemnly affirm non-commercial operation, clear land title, and strict compliance with AICTE norms."
        ])
        docs_to_generate.append((f_aff, "AFFIDAVIT_TRUST", "Statutory_Trust_Affidavit.pdf"))

        # 5. Architect Cert
        f_arch = str(synth_dir / f"{app.id}_architect_cert.pdf")
        create_pdf(f_arch, "COUNCIL OF ARCHITECTURE - ACCREDITED REPORT", [
            "# ARCHITECT BARRIER-FREE BUILT-UP ENVIRONMENT CERTIFICATE",
            "Architect Reg. No: CA/2015/67891",
            f"Institution: {app.institution_name}",
            f"Certified that total instructional carpet area exceeds {instructional_sqm} sqm with barrier-free accessibility."
        ])
        docs_to_generate.append((f_arch, "ARCHITECT_CERTIFICATE", "Architect_Accessibility_Cert.pdf"))

        # Simulated Verification Records
        verif_records.append(VerificationRecord(
            id=str(uuid.uuid4()),
            application_id=app.id,
            verification_type="STATE_LAND_REVENUE_PORTAL",
            external_reference_id=f"REV-{app.state[:3].upper()}-{app.id[:6]}",
            simulated_status="MATCH",
            simulated_response_json=json.dumps({"owner": app.institution_name, "status": "CLEAR_TITLE", "area_acres": land_acres})
        ))
        verif_records.append(VerificationRecord(
            id=str(uuid.uuid4()),
            application_id=app.id,
            verification_type="MUNICIPAL_TOWN_PLANNING_SYSTEM",
            external_reference_id=f"TCP/{app.district[:3].upper()}/2023/9102",
            simulated_status="MATCH",
            simulated_response_json=json.dumps({"plan_status": "APPROVED", "carpet_area_sqm": carpet_sqm})
        ))
        verif_records.append(VerificationRecord(
            id=str(uuid.uuid4()),
            application_id=app.id,
            verification_type="FIRE_SERVICE_DIRECTORATE",
            external_reference_id=f"MFS/{app.district[:3].upper()}/2024/7744",
            simulated_status="MATCH",
            simulated_response_json=json.dumps({"noc_status": "VALID", "valid_until": "2028-12-31"})
        ))

    elif scenario == "DEFICIENT_LAND":
        # Discrepant land deed: states 5.2 acres and mismatched plot
        f_land = str(synth_dir / f"{app.id}_land_deed_discrepant.pdf")
        create_pdf(f_land, f"GOVERNMENT OF {app.state.upper()} - SUB REGISTRAR OFFICE", [
            "# REGISTERED SALE DEED",
            "Registration Number: REG-DISCREPANT-4040",
            f"In favour of: {app.institution_name}",
            "",
            "• Survey Number: Plot-MISMATCH-999",
            "• Total Land Area: 5.2 Acres",
            "• Note: Land boundary disputed."
        ])
        docs_to_generate.append((f_land, "LAND_REGISTRATION", "Registered_Deed_Discrepant.pdf"))

        # Building Plan with deficit
        f_bldg = str(synth_dir / f"{app.id}_building_plan_deficit.pdf")
        create_pdf(f_bldg, "MUNICIPAL PLANNING DEPARTMENT", [
            "# SANCTIONED BUILDING PLAN",
            "• Total Carpet Area: 5200 Sq.m",
            "• Instructional Area: 2600 Sqm"
        ])
        docs_to_generate.append((f_bldg, "BUILDING_PLAN_APPROVAL", "Building_Plan_5200sqm.pdf"))

        # Fire NOC valid
        f_fire = str(synth_dir / f"{app.id}_fire_noc.pdf")
        create_pdf(f_fire, "FIRE SAFETY SERVICES", [
            "# FIRE SAFETY CERTIFICATE",
            f"Institution: {app.institution_name}",
            "Valid up to: 31-12-2027"
        ])
        docs_to_generate.append((f_fire, "FIRE_SAFETY_NOC", "Fire_Safety_NOC.pdf"))

        # Affidavit
        f_aff = str(synth_dir / f"{app.id}_affidavit.pdf")
        create_pdf(f_aff, "NOTARIZED AFFIDAVIT", ["# TRUST AFFIDAVIT"])
        docs_to_generate.append((f_aff, "AFFIDAVIT_TRUST", "Affidavit.pdf"))

        # Architect Cert
        f_arch = str(synth_dir / f"{app.id}_architect_cert.pdf")
        create_pdf(f_arch, "ARCHITECT CERTIFICATE", ["# BARRIER-FREE ENVIRONMENT CERTIFICATE"])
        docs_to_generate.append((f_arch, "ARCHITECT_CERTIFICATE", "Architect_Certificate.pdf"))

        verif_records.append(VerificationRecord(
            id=str(uuid.uuid4()),
            application_id=app.id,
            verification_type="STATE_LAND_REVENUE_PORTAL",
            external_reference_id="REV-ERR-999",
            simulated_status="MISMATCH",
            simulated_response_json=json.dumps({"error": "Deed survey number does not match revenue plot identification."})
        ))

    elif scenario == "MISSING_DOCS":
        # Only Land Deed & Affidavit; omits Building Plan, Fire NOC, Architect Cert!
        f_land = str(synth_dir / f"{app.id}_land_deed.pdf")
        create_pdf(f_land, "DEPARTMENT OF REGISTRATION", [
            "# REGISTERED LAND DEED",
            f"• Survey Number: {survey_no}",
            f"• Total Land Area: {land_acres} Acres"
        ])
        docs_to_generate.append((f_land, "LAND_REGISTRATION", "Land_Deed.pdf"))

        f_aff = str(synth_dir / f"{app.id}_affidavit.pdf")
        create_pdf(f_aff, "NOTARIZED AFFIDAVIT", ["# TRUST AFFIDAVIT"])
        docs_to_generate.append((f_aff, "AFFIDAVIT_TRUST", "Trust_Affidavit.pdf"))

    elif scenario == "TAMPERED_PDF":
        # Compliant Land & Building, but Tampered Fire NOC
        f_land = str(synth_dir / f"{app.id}_land_deed.pdf")
        create_pdf(f_land, "SUB REGISTRAR OFFICE", [
            "# REGISTERED LAND DEED",
            f"• Survey Number: {survey_no}",
            f"• Total Land Area: {land_acres} Acres"
        ])
        docs_to_generate.append((f_land, "LAND_REGISTRATION", "Land_Deed.pdf"))

        f_bldg = str(synth_dir / f"{app.id}_building_plan.pdf")
        create_pdf(f_bldg, "TOWN PLANNING AUTHORITY", [
            "# SANCTIONED MASTER BUILDING PLAN",
            f"• Total Carpet Area: {carpet_sqm} Sq.m",
            f"• Instructional Area: {instructional_sqm} Sqm"
        ])
        docs_to_generate.append((f_bldg, "BUILDING_PLAN_APPROVAL", "Sanctioned_Plan.pdf"))

        f_fire = str(synth_dir / f"{app.id}_fire_noc_tampered.pdf")
        create_pdf(
            f_fire,
            "STATE FIRE DEPARTMENT - NOC",
            [
                "# FIRE SAFETY COMPLIANCE CERTIFICATE",
                f"Institution: {app.institution_name}",
                "Valid up to: 31-12-2027",
                "Certified premises fire safety compliant."
            ],
            creator="Canva Design Studio Web",
            producer="Canva PDF Renderer v4.1 / PDFescape Post-Editor",
            add_extra_eof=True
        )
        docs_to_generate.append((f_fire, "FIRE_SAFETY_NOC", "State_Fire_NOC_Canva_Tampered.pdf"))

        f_aff = str(synth_dir / f"{app.id}_affidavit.pdf")
        create_pdf(f_aff, "TRUST AFFIDAVIT", ["# TRUST AFFIDAVIT"])
        docs_to_generate.append((f_aff, "AFFIDAVIT_TRUST", "Trust_Affidavit.pdf"))

        f_arch = str(synth_dir / f"{app.id}_architect_cert.pdf")
        create_pdf(f_arch, "ARCHITECT CERTIFICATE", ["# ACCESSIBILITY REPORT"])
        docs_to_generate.append((f_arch, "ARCHITECT_CERTIFICATE", "Architect_Certificate.pdf"))

        verif_records.append(VerificationRecord(
            id=str(uuid.uuid4()),
            application_id=app.id,
            verification_type="FIRE_SERVICE_DIRECTORATE",
            external_reference_id="MFS-TAMPER-7721",
            simulated_status="MISMATCH",
            simulated_response_json=json.dumps({"error": "Certificate number belongs to commercial plaza, not college."})
        ))

    # Ingest generated documents into database
    for path, dtype, orig_name in docs_to_generate:
        txt = extract_text_from_pdf(path)
        sha = compute_sha256(path)
        meta = analyze_pdf_metadata_and_integrity(path, dtype)
        d = Document(
            id=str(uuid.uuid4()),
            application_id=app.id,
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

    # Ingest verification records
    for vr in verif_records:
        db.add(vr)

    db.commit()
