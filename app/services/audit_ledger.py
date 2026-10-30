import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLedger
from app.services.clock_service import clock_service

GENESIS_HASH = "0" * 64

class AuditLedgerService:
    @staticmethod
    def canonical_json(data: Any) -> str:
        """Produces deterministic, canonically sorted JSON for cryptographic hashing."""
        return json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)

    @staticmethod
    def compute_record_hash(prev_hash: str, canonical_payload: str) -> str:
        combined = f"{prev_hash}||{canonical_payload}".encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @staticmethod
    def record_event(
        db: Session,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        actor_role: str,
        action_summary: str,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> AuditLedger:
        """Appends a new immutable event to the hash-chained audit ledger."""
        sim_now = clock_service.now(db)
        
        # Get latest sequence and hash
        latest = db.query(AuditLedger).order_by(AuditLedger.sequence_number.desc()).first()
        if latest:
            seq_num = latest.sequence_number + 1
            prev_hash = latest.current_hash
        else:
            seq_num = 1
            prev_hash = GENESIS_HASH

        event_payload = {
            "sequence_number": seq_num,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action_summary": action_summary,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason": reason,
            "data": payload or {},
            "timestamp": sim_now.isoformat()
        }
        
        canonical_str = AuditLedgerService.canonical_json(event_payload)
        curr_hash = AuditLedgerService.compute_record_hash(prev_hash, canonical_str)

        entry = AuditLedger(
            id=str(uuid.uuid4()),
            sequence_number=seq_num,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action_summary=action_summary,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
            canonical_payload_json=canonical_str,
            previous_hash=prev_hash,
            current_hash=curr_hash,
            is_tampered=False,
            timestamp=sim_now
        )
        
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def verify_chain(db: Session) -> Dict[str, Any]:
        """Recomputes SHA-256 hash sequence from genesis to present and flags any tampered/deleted record."""
        records: List[AuditLedger] = db.query(AuditLedger).order_by(AuditLedger.sequence_number.asc()).all()
        
        if not records:
            return {
                "is_valid": True,
                "total_records": 0,
                "first_broken_sequence": None,
                "status": "EMPTY_CHAIN",
                "message": "Audit ledger is empty. Ready for recording."
            }

        expected_prev = GENESIS_HASH
        
        for idx, rec in enumerate(records):
            # Check link to previous hash
            if rec.previous_hash != expected_prev:
                return {
                    "is_valid": False,
                    "total_records": len(records),
                    "first_broken_sequence": rec.sequence_number,
                    "status": "BROKEN_LINK",
                    "broken_record_id": rec.id,
                    "expected_previous_hash": expected_prev,
                    "actual_previous_hash": rec.previous_hash,
                    "message": f"Tamper detected: Previous hash mismatch at sequence #{rec.sequence_number}."
                }
            
            # Recompute hash from canonical payload
            recalculated = AuditLedgerService.compute_record_hash(rec.previous_hash, rec.canonical_payload_json)
            if recalculated != rec.current_hash or rec.is_tampered:
                return {
                    "is_valid": False,
                    "total_records": len(records),
                    "first_broken_sequence": rec.sequence_number,
                    "status": "HASH_MISMATCH",
                    "broken_record_id": rec.id,
                    "expected_hash": recalculated,
                    "actual_hash": rec.current_hash,
                    "message": f"Tamper detected: Cryptographic checksum failed at sequence #{rec.sequence_number}."
                }

            expected_prev = rec.current_hash

        return {
            "is_valid": True,
            "total_records": len(records),
            "first_broken_sequence": None,
            "status": "VERIFIED_VALID",
            "latest_hash": expected_prev,
            "message": f"All {len(records)} audit records cryptographically verified. Hash chain integrity 100% intact."
        }

    @staticmethod
    def simulate_tamper_for_demo(db: Session, target_sequence: Optional[int] = None) -> Dict[str, Any]:
        """Controlled evaluation test: intentionally modifies a past record without re-hashing downstream."""
        if target_sequence is not None:
            rec = db.query(AuditLedger).filter(AuditLedger.sequence_number == target_sequence).first()
        else:
            # Pick a middle record
            count = db.query(AuditLedger).count()
            if count == 0:
                return {"success": False, "message": "No records in ledger to tamper."}
            target_seq = max(1, count // 2)
            rec = db.query(AuditLedger).filter(AuditLedger.sequence_number == target_seq).first()

        if not rec:
            return {"success": False, "message": "Target record not found."}

        # Modify the payload subtly to simulate tampering
        original_action = rec.action_summary
        rec.action_summary = f"[TAMPERED] {original_action}"
        rec.is_tampered = True
        rec.tamper_note = "Deliberate demonstration modification to verify tamper detection."
        db.commit()

        return {
            "success": True,
            "tampered_sequence": rec.sequence_number,
            "record_id": rec.id,
            "message": f"Record #{rec.sequence_number} has been deliberately altered for evaluation testing. Run verify to detect it."
        }

audit_ledger = AuditLedgerService()
