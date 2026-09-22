"""
JudiQ AI — Chronology Validation & Legal Timeline Sanity Engine
==============================================================
Enforces strict chronological sequence for Section 138 Negotiable Instruments Act
and related commercial litigation workflows.

Statutory Timeline Milestones (Section 138 NI Act):
  1. Transaction / Debt Creation Date (transaction_date)
  2. Cheque Issue Date (cheque_date)
  3. Cheque Presentation Date (presentation_date) — Must be within 3 months of cheque_date (S.138 proviso a)
  4. Cheque Dishonour Date (dishonour_date) — Occurs upon bank return
  5. Bank Return Memo Date (memo_date) — Date memo is issued/received
  6. Statutory Demand Notice Sent Date (notice_date) — Must be within 30 days of memo/dishonour (S.138 proviso b)
  7. Notice Delivery / Service Date (notice_delivery_date)
  8. Statutory 15-day Cure Period Expiry (notice_delivery_date + 15 days)
  9. Court Complaint Filing Date (filing_date) — Must be within 30 days of cause of action (S.142(1)(b))

Any violation of prerequisite milestones (e.g., dishonour before cheque issuance,
or notice before dishonour) represents an impossible timeline that MUST BLOCK
legal analysis and drafting.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_iso_or_dmy(val: Any) -> Optional[date]:
    """Parse date from string (YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY) or date object."""
    if not val:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    s = str(val).strip()
    if not s or s.lower() in ("null", "none", "not provided", "undefined"):
        return None
    # ISO: YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # Try regex fallback for partial
    import re
    m_iso = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", s)
    if m_iso:
        try:
            return date(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
        except ValueError:
            pass
    m_dmy = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
    if m_dmy:
        try:
            return date(int(m_dmy.group(3)), int(m_dmy.group(2)), int(m_dmy.group(1)))
        except ValueError:
            pass
    return None


class ChronologyValidationResult:
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str], timeline_facts: Dict[str, Optional[date]]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.timeline_facts = timeline_facts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "fatal_block": not self.is_valid,
            "block_reason": "; ".join(self.errors) if self.errors else None,
            "timeline_facts": {k: (v.isoformat() if v else None) for k, v in self.timeline_facts.items()}
        }


class ChronologyEngine:
    """Validates chronological order of legal events and blocks analysis on impossible sequences."""

    @classmethod
    def validate_ni_act_chronology(cls, case_data: Dict[str, Any]) -> ChronologyValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        d_txn = parse_iso_or_dmy(case_data.get("transaction_date"))
        d_chq = parse_iso_or_dmy(case_data.get("cheque_date"))
        d_pres = parse_iso_or_dmy(case_data.get("presentation_date"))
        d_dis = parse_iso_or_dmy(case_data.get("dishonour_date") or case_data.get("date_of_dishonour"))
        d_memo = parse_iso_or_dmy(case_data.get("memo_date"))
        d_ntc = parse_iso_or_dmy(case_data.get("notice_date") or case_data.get("date_of_notice"))
        d_del = parse_iso_or_dmy(case_data.get("notice_delivery_date") or case_data.get("notice_received_date"))
        d_file = parse_iso_or_dmy(case_data.get("filing_date") or case_data.get("date_of_complaint"))

        timeline_facts = {
            "transaction_date": d_txn,
            "cheque_date": d_chq,
            "presentation_date": d_pres,
            "dishonour_date": d_dis,
            "memo_date": d_memo,
            "notice_date": d_ntc,
            "notice_delivery_date": d_del,
            "filing_date": d_file,
        }

        # 1. Transaction vs Cheque Date
        if d_txn and d_chq and d_txn > d_chq:
            errors.append(
                f"Chronology Inversion: Transaction / Debt Date ({d_txn}) cannot occur after Cheque Issue Date ({d_chq})."
            )

        # 2. Cheque vs Presentation Date
        if d_chq and d_pres:
            if d_pres < d_chq:
                errors.append(
                    f"Chronology Inversion: Cheque Presentation Date ({d_pres}) cannot precede Cheque Date ({d_chq})."
                )
            else:
                days_pres = (d_pres - d_chq).days
                if days_pres > 92:
                    warnings.append(
                        f"Cheque Validity Window Exceeded: Cheque presented {days_pres} days after issuance (Statutory limit: 3 months / ~90 days under S.138 proviso (a))."
                    )

        # 3. Dishonour vs Cheque Date
        if d_dis and d_chq and d_dis < d_chq:
            errors.append(
                f"Fatal Chronology Inversion: Cheque Dishonour Date ({d_dis}) cannot precede Cheque Issue Date ({d_chq})."
            )

        # 4. Dishonour vs Presentation Date
        if d_dis and d_pres and d_dis < d_pres:
            errors.append(
                f"Fatal Chronology Inversion: Cheque Dishonour Date ({d_dis}) cannot precede Presentation Date ({d_pres})."
            )

        # 5. Memo Date vs Dishonour Date
        if d_memo and d_dis and d_memo < d_dis:
            errors.append(
                f"Chronology Inversion: Bank Return Memo Date ({d_memo}) cannot precede Dishonour Date ({d_dis})."
            )

        # 6. Notice vs Dishonour Date
        if d_ntc and d_dis:
            if d_ntc < d_dis:
                errors.append(
                    f"Fatal Chronology Inversion: Statutory Notice Sent Date ({d_ntc}) cannot precede Cheque Dishonour Date ({d_dis})."
                )
            else:
                days_notice = (d_ntc - d_dis).days
                if days_notice > 30:
                    warnings.append(
                        f"Notice Dispatch Delayed: Statutory notice dispatched {days_notice} days after dishonour (Statutory limit: 30 days under S.138 proviso (b)). Condonation required."
                    )

        # 7. Notice vs Cheque Date
        if d_ntc and d_chq and d_ntc < d_chq:
            errors.append(
                f"Fatal Chronology Inversion: Statutory Notice Date ({d_ntc}) cannot precede Cheque Issue Date ({d_chq})."
            )

        # 8. Notice Delivery vs Notice Dispatch
        if d_del and d_ntc and d_del < d_ntc:
            errors.append(
                f"Chronology Inversion: Notice Delivery Date ({d_del}) cannot precede Notice Dispatch Date ({d_ntc})."
            )

        # 9. Filing Date vs Notice Delivery (Premature Complaint Check)
        if d_file and d_del:
            days_cure = (d_file - d_del).days
            if days_cure < 15:
                errors.append(
                    f"Premature Complaint: Complaint filed on {d_file}, only {days_cure} days after notice service ({d_del}). Section 138 proviso (c) requires a mandatory 15-day cure period for the accused."
                )

        # 10. Filing Date vs Notice Dispatch
        if d_file and d_ntc and d_file <= d_ntc:
            errors.append(
                f"Fatal Chronology Inversion: Complaint Filing Date ({d_file}) cannot precede or equal Notice Dispatch Date ({d_ntc})."
            )

        # 11. Filing Date vs Dishonour
        if d_file and d_dis and d_file < d_dis:
            errors.append(
                f"Fatal Chronology Inversion: Complaint Filing Date ({d_file}) cannot precede Cheque Dishonour Date ({d_dis})."
            )

        is_valid = len(errors) == 0
        return ChronologyValidationResult(is_valid, errors, warnings, timeline_facts)
