import logging
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AuditLedger:
    """
    Audit & Human Review Ledger:
    Logs input -> evidence relied upon -> rule fired -> precedent used -> AI finding -> Lawyer Override.
    """

    _LEDGER: List[Dict[str, Any]] = []

    @classmethod
    def record_entry(
        cls,
        case_id: str,
        finding_id: str,
        finding_text: str,
        evidence_relied: str,
        rule_applied: str,
        authority: str,
        confidence: float,
        verdict: str
    ) -> Dict[str, Any]:
        entry = {
            "timestamp": time.time(),
            "case_id": case_id,
            "finding_id": finding_id,
            "finding_text": finding_text,
            "evidence_relied": evidence_relied,
            "rule_applied": rule_applied,
            "authority": authority,
            "confidence": confidence,
            "ai_verdict": verdict,
            "review_status": "PENDING_REVIEW",  # ACCEPTED, MODIFIED, REJECTED
            "lawyer_override": None
        }
        cls._LEDGER.append(entry)
        logger.info(f"[AUDIT_LEDGER] Entry recorded for case '{case_id}': {finding_id}")
        return entry

    @classmethod
    def apply_lawyer_override(
        cls,
        case_id: str,
        finding_id: str,
        action: str,  # ACCEPT, MODIFY, REJECT
        override_reason: str,
        lawyer_name: str = "Counsel"
    ) -> Optional[Dict[str, Any]]:
        action_clean = action.upper().strip()
        if action_clean not in ["ACCEPT", "MODIFY", "REJECT"]:
            raise ValueError("Invalid review action. Must be ACCEPT, MODIFY, or REJECT.")

        status_map = {"ACCEPT": "ACCEPTED", "MODIFY": "MODIFIED", "REJECT": "REJECTED"}
        for entry in reversed(cls._LEDGER):
            if entry["case_id"] == case_id and entry["finding_id"] == finding_id:
                entry["review_status"] = status_map.get(action_clean, f"{action_clean}ED")
                entry["lawyer_override"] = {
                    "action": action_clean,
                    "reason": override_reason,
                    "lawyer_name": lawyer_name,
                    "overridden_at": time.time()
                }
                logger.info(f"[AUDIT_LEDGER] Lawyer override applied by {lawyer_name}: {action_clean} on {finding_id}")
                return entry
        return None

    @classmethod
    def get_case_audit_trail(cls, case_id: str) -> List[Dict[str, Any]]:
        return [e for e in cls._LEDGER if e["case_id"] == case_id]
