import os
import re
import hashlib
from typing import Dict, Any, Optional
import pymupdf

def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts all text from a PDF using PyMuPDF with pypdf fallback."""
    full_text = []
    try:
        doc = pymupdf.open(file_path)
        for page in doc:
            full_text.append(page.get_text() or "")
        doc.close()
        return "\n".join(full_text).strip()
    except Exception:
        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                full_text.append(page.extract_text() or "")
            return "\n".join(full_text).strip()
        except Exception:
            return ""

def extract_structured_fields(text: str, doc_type: str) -> Dict[str, Any]:
    """
    Applies regex patterns to extract key statutory metrics from document text.
    """
    fields: Dict[str, Any] = {}
    
    # Common Patterns
    # 1. Land Area (acres / hectares / sq m)
    # Examples: "Total Area: 7.5 Acres", "Area: 5.0 acres", "measuring 8.25 Acres"
    area_match = re.search(r'(?:total\s+area|land\s+area|measuring|extent\s+of)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:acres?|acre)', text, re.IGNORECASE)
    if area_match:
        fields["extracted_area_acres"] = float(area_match.group(1))

    # 2. Survey / Khasra Number
    # Examples: "Survey No. 142/1", "Khasra No: 204/B", "Plot No: 88"
    survey_match = re.search(r'(?:survey\s*(?:no\.?|number)|khasra\s*(?:no\.?|number)|plot\s*(?:no\.?|number))\s*[:=]?\s*([0-9A-Za-z\/\-]+)', text, re.IGNORECASE)
    if survey_match:
        fields["survey_khasra_no"] = survey_match.group(1).strip()

    # 3. Built-up / Carpet Area
    # Examples: "Total Carpet Area: 8500 Sq.m", "Instructional Area: 4200 sqm"
    carpet_match = re.search(r'(?:total\s+carpet\s+area|total\s+built[- ]up\s+area)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:sq\.?\s*m|sqm|sq\s*meters?)', text, re.IGNORECASE)
    if carpet_match:
        fields["total_carpet_sqm"] = float(carpet_match.group(1))

    instructional_match = re.search(r'(?:instructional\s+area)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:sq\.?\s*m|sqm|sq\s*meters?)', text, re.IGNORECASE)
    if instructional_match:
        fields["instructional_area_sqm"] = float(instructional_match.group(1))

    # 4. Certificate / Approval / NOC Number
    # Examples: "NOC Number: FS/2024/9912", "Approval No: BPA-2024-8871"
    cert_match = re.search(r'(?:noc\s*no\.?|certificate\s*no\.?|approval\s*no\.?|registration\s*no\.?)\s*[:=]?\s*([0-9A-Za-z\/\-\_]+)', text, re.IGNORECASE)
    if cert_match:
        fields["certificate_number"] = cert_match.group(1).strip()

    # 5. Validity / Issue Dates
    # Examples: "Valid up to: 31-12-2027", "Issued on: 15/04/2024"
    date_match = re.search(r'(?:valid\s*(?:up\s*to|until|till)|expiry\s*date|issued\s*on)\s*[:=]?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})', text, re.IGNORECASE)
    if date_match:
        fields["validity_date"] = date_match.group(1).strip()

    # 6. Institution / Trust Name Mentioned
    name_match = re.search(r'(?:in\s+the\s+name\s+of|favour\s+of|institution\s*name\s*[:=]|trust\s*name\s*[:=])\s*([A-Za-z0-9\s\,\.\-\&]{4,60})', text, re.IGNORECASE)
    if name_match:
        fields["entity_name_mentioned"] = name_match.group(1).strip()

    return fields
