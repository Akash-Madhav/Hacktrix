import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pymupdf

def parse_pdf_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse PDF date format like D:20240415120000+05'30' or 2024-04-15."""
    if not date_str:
        return None
    try:
        cleaned = date_str.strip()
        if cleaned.startswith("D:"):
            cleaned = cleaned[2:]
        # Remove timezone suffix like +05'30'
        cleaned = cleaned.split("+")[0].split("-")[0].replace("'", "")
        if len(cleaned) >= 8:
            year = int(cleaned[0:4])
            month = int(cleaned[4:6])
            day = int(cleaned[6:8])
            hour = int(cleaned[8:10]) if len(cleaned) >= 10 else 0
            minute = int(cleaned[10:12]) if len(cleaned) >= 12 else 0
            second = int(cleaned[12:14]) if len(cleaned) >= 14 else 0
            return datetime(year, month, day, hour, minute, second)
    except Exception:
        pass
    return None

def analyze_pdf_metadata_and_integrity(file_path: str, doc_type: str) -> Dict[str, Any]:
    """
    Analyzes PDF metadata and xref structure for tampering indicators (V12 & V13).
    Follows statutory guidelines:
    - Language is strictly advisory ('ADVISORY_OBSERVATION')
    - Never uses inflammatory words like 'forged' or 'fake'
    - Flags discrepancies for human scrutiny officer inspection
    """
    observations: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    
    if not os.path.exists(file_path):
        return {
            "v12_status": "UNKNOWN",
            "v13_status": "UNKNOWN",
            "observations": [{
                "rule_id": "V12",
                "severity": "MINOR",
                "finding": "File could not be accessed on disk for integrity inspection",
                "recommendation": "Re-upload file"
            }]
        }

    try:
        doc = pymupdf.open(file_path)
        metadata = doc.metadata or {}
        page_count = len(doc)
        
        # 1. Extraction of metadata attributes
        creator = (metadata.get("creator") or "").strip()
        producer = (metadata.get("producer") or "").strip()
        creation_raw = metadata.get("creationDate") or ""
        mod_raw = metadata.get("modDate") or ""
        
        creation_dt = parse_pdf_date(creation_raw)
        mod_dt = parse_pdf_date(mod_raw)
        
        # -------------------------------------------------------------
        # Rule V12: PDF Metadata Anomaly Analysis
        # -------------------------------------------------------------
        v12_flagged = False
        
        # Check A: Future dates (allowing 24h timezone tolerance)
        now = datetime.now()
        if creation_dt and creation_dt > (now + timedelta(days=1)):
            v12_flagged = True
            observations.append({
                "rule_id": "V12",
                "check_name": "Creation Date Consistency",
                "severity": "ADVISORY_OBSERVATION",
                "finding": f"Document CreationDate ({creation_raw}) is stamped in the future relative to system clock.",
                "evidence": {"creation_date": creation_raw, "system_time": str(now)},
                "recommendation": "Physical verification of original certificate recommended."
            })
            
        # Check B: CreationDate later than ModDate (with 5 minute tolerance for clock skews)
        if creation_dt and mod_dt and (creation_dt - mod_dt).total_seconds() > 300:
            v12_flagged = True
            observations.append({
                "rule_id": "V12",
                "check_name": "Timestamp Chronology",
                "severity": "ADVISORY_OBSERVATION",
                "finding": f"Inverted timestamp chronology detected: CreationDate ({creation_raw}) is later than ModificationDate ({mod_raw}).",
                "evidence": {"creation_date": creation_raw, "modification_date": mod_raw},
                "recommendation": "Advisory flag for scrutiny committee to examine timeline of issuance."
            })
            
        # Check C: Producer/Creator indicative of manual PDF modification software on official certificate
        # E.g. Canva, iLovePDF, Sejda, PDFescape on a registered Land Deed or Fire NOC
        suspicious_editors = ["canva", "ilovepdf", "sejda", "pdfescape", "smallpdf", "pdfedit", "photoshop"]
        combined_tools = f"{creator.lower()} {producer.lower()}"
        matched_editors = [tool for tool in suspicious_editors if tool in combined_tools]
        
        if matched_editors and doc_type in ["LAND_REGISTRATION", "FIRE_SAFETY_NOC", "BUILDING_PLAN_APPROVAL"]:
            v12_flagged = True
            observations.append({
                "rule_id": "V12",
                "check_name": "Producer Software Anomaly",
                "severity": "ADVISORY_OBSERVATION",
                "finding": (
                    f"Statutory authority document ({doc_type}) appears generated/modified by third-party editing tool "
                    f"({', '.join(matched_editors)}). Official certificates typically originate from institutional or government issuing software."
                ),
                "evidence": {"creator": creator, "producer": producer, "matched_tools": matched_editors},
                "recommendation": "Cross-verify certificate registration number directly with the state revenue or fire department records."
            })
            
        # Check D: Significant delta between creation and modification
        if creation_dt and mod_dt and (mod_dt - creation_dt).total_seconds() > 86400 * 30: # > 30 days
            # Noticeable modification long after creation
            observations.append({
                "rule_id": "V12",
                "check_name": "Post-Issuance Modification Interval",
                "severity": "ADVISORY_OBSERVATION",
                "finding": (
                    f"Document modification date is {(mod_dt - creation_dt).days} days after initial creation date. "
                    "Indicates post-creation content revision or resaving."
                ),
                "evidence": {"creation_date": creation_raw, "modification_date": mod_raw, "days_delta": (mod_dt - creation_dt).days},
                "recommendation": "Confirm whether post-issuance endorsements or endorsements by issuing officer exist."
            })

        # -------------------------------------------------------------
        # Rule V13: PDF Revision and Incremental Update Analysis
        # -------------------------------------------------------------
        # Analyze file bytes for number of '%%EOF' markers (each incremental update appends %%EOF)
        v13_flagged = False
        eof_count = 0
        is_repaired = getattr(doc, "is_repaired", False)
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                eof_count = content.count(b"%%EOF")
        except Exception:
            eof_count = 1

        if eof_count > 2:
            v13_flagged = True
            observations.append({
                "rule_id": "V13",
                "check_name": "Incremental Revision Count",
                "severity": "ADVISORY_OBSERVATION",
                "finding": (
                    f"PDF contains {eof_count} incremental update revisions (multiple %%EOF sections). "
                    "Official statutory certificates typically comprise a single unified file stream."
                ),
                "evidence": {"incremental_revisions": eof_count, "is_repaired": is_repaired},
                "recommendation": "Inspect document layers in PDF viewer to confirm no superseded or overlaid text blocks exist."
            })

        if is_repaired:
            v13_flagged = True
            observations.append({
                "rule_id": "V13",
                "check_name": "PDF Structure Repair Flag",
                "severity": "ADVISORY_OBSERVATION",
                "finding": "PDF xref table required repair during parser initialization. Possible corrupted or altered stream dictionary.",
                "evidence": {"is_repaired": True},
                "recommendation": "Request clean digital export from source applicant."
            })

        doc.close()

        return {
            "v12_status": "FLAG" if v12_flagged else "PASS",
            "v13_status": "FLAG" if v13_flagged else "PASS",
            "metadata": {
                "creator": creator,
                "producer": producer,
                "creation_date": creation_raw,
                "modification_date": mod_raw,
                "page_count": page_count,
                "eof_count": eof_count,
                "is_repaired": is_repaired
            },
            "observations": observations
        }

    except Exception as e:
        return {
            "v12_status": "UNKNOWN",
            "v13_status": "UNKNOWN",
            "metadata": {},
            "observations": [{
                "rule_id": "V12",
                "check_name": "Integrity Inspection Error",
                "severity": "MINOR",
                "finding": f"Unable to parse document structure: {str(e)}",
                "recommendation": "Manual document review required."
            }]
        }
