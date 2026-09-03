"""
JudiQ AI — CPC & Commercial Courts Statutory Rules Engine
Evaluates limitation periods, Commercial Courts Act compliance, Section 12A PIMS, and procedural mandates.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from utils import parse_date, days_between

class CPCStatutoryRules:
    """
    Statutory rule evaluator for Code of Civil Procedure (1908),
    Commercial Courts Act (2015), and Limitation Act (1963).
    """

    COMMERCIAL_SPECIFIED_VALUE_MIN = 300000.0  # INR 3 Lakhs minimum
    COMMERCIAL_WS_MAX_DAYS = 120               # Strict 120-day outer limit u/O VIII R 1
    ORDINARY_WS_MAX_DAYS = 90                  # 30 + 60 days u/O VIII R 1
    SECTION_80_NOTICE_DAYS = 60                # 2 months statutory notice to Government

    LIMITATION_ARTICLES = {
        "article_14": {"years": 3, "label": "Article 14 - Goods Sold & Delivered (3 Years)"},
        "article_22": {"years": 3, "label": "Article 22 - Money Deposited on Demand (3 Years)"},
        "article_54": {"years": 3, "label": "Article 54 - Specific Performance of Contract (3 Years)"},
        "article_55": {"years": 3, "label": "Article 55 - Compensation for Breach of Contract (3 Years)"},
        "article_58": {"years": 3, "label": "Article 58 - Declaration of Status or Right (3 Years)"},
        "article_64": {"years": 12, "label": "Article 64 - Possession based on Dispossession (12 Years)"},
        "article_65": {"years": 12, "label": "Article 65 - Possession based on Title / Adverse Possession (12 Years)"},
        "article_113": {"years": 3, "label": "Article 113 - Residuary Civil Limitation (3 Years)"},
        "article_136": {"years": 12, "label": "Article 136 - Execution of Decrees and Orders (12 Years)"}
    }

    @classmethod
    def evaluate_limitation(
        cls,
        cause_of_action_date: Optional[str],
        filing_date: Optional[str],
        article_key: str = "article_113",
        written_acknowledgment_date: Optional[str] = None,
        last_payment_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates statutory limitation window under Limitation Act, 1963
        accounting for Section 18 (acknowledgment) and Section 19 (payment) extensions.
        """
        if not cause_of_action_date or not filing_date:
            return {
                "valid": True,
                "defect": None,
                "fatal": False,
                "status": "ASSUMED_TIMELY",
                "message": "Filing or cause of action date not specified; assuming timely filing."
            }

        start_dt = parse_date(cause_of_action_date)
        filing_dt = parse_date(filing_date)
        if not start_dt or not filing_dt:
            return {"valid": True, "defect": None, "fatal": False, "status": "UNKNOWN_DATE"}

        # Check for Section 18 Written Acknowledgment renewal
        effective_start_dt = start_dt
        renewal_reason = None
        if written_acknowledgment_date:
            ack_dt = parse_date(written_acknowledgment_date)
            if ack_dt and ack_dt > effective_start_dt and ack_dt <= filing_dt:
                effective_start_dt = ack_dt
                renewal_reason = f"Section 18 Limitation Act renewal applied from written acknowledgment on {written_acknowledgment_date}."

        # Check for Section 19 Payment renewal
        if last_payment_date:
            pay_dt = parse_date(last_payment_date)
            if pay_dt and pay_dt > effective_start_dt and pay_dt <= filing_dt:
                effective_start_dt = pay_dt
                renewal_reason = f"Section 19 Limitation Act renewal applied from part payment on {last_payment_date}."

        art_cfg = cls.LIMITATION_ARTICLES.get(article_key.lower(), cls.LIMITATION_ARTICLES["article_113"])
        statutory_years = art_cfg["years"]
        statutory_days = statutory_years * 365

        elapsed_days = (filing_dt - effective_start_dt).days
        if elapsed_days < 0:
            return {"valid": True, "defect": None, "fatal": False, "status": "PRE_INCEPTION"}

        if elapsed_days > statutory_days:
            overdue_days = elapsed_days - statutory_days
            return {
                "valid": False,
                "defect": f"Suit is barred by limitation under {art_cfg['label']}. Inception to filing elapsed {elapsed_days} days (Statutory Limit: {statutory_days} days; delayed by {overdue_days} days).",
                "fatal": True,
                "status": "BARRED_BY_LIMITATION",
                "authority": "Section 3 Limitation Act, 1963 & Order VII Rule 11(d) CPC (Dahiben v. Arvindbhai Bhanusali)",
                "remedy": "Examine if any Section 18 written acknowledgment, balance confirmation, or Section 14 exclusion of bona fide time applies."
            }

        return {
            "valid": True,
            "defect": None,
            "fatal": False,
            "status": "WITHIN_LIMITATION",
            "message": f"Suit filed within {statutory_years}-year limitation period ({elapsed_days}/{statutory_days} days elapsed).",
            "renewal_applied": renewal_reason
        }

    @classmethod
    def evaluate_commercial_courts_compliance(
        cls,
        case_data: Dict[str, Any],
        is_commercial: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates Section 12A PIMS, Specified Value threshold, and Statement of Truth under CCA 2015.
        """
        if not is_commercial:
            return {"valid": True, "defects": [], "fatal": False}

        defects = []
        fatal = False
        remedies = []

        valuation = float(case_data.get("suit_valuation_amount") or case_data.get("suit_valuation") or case_data.get("claim_amount") or 0.0)
        if valuation > 0 and valuation < cls.COMMERCIAL_SPECIFIED_VALUE_MIN:
            defects.append(f"Suit valuation ₹{valuation:,.2f} is below Specified Value threshold of ₹3,00,000 u/s 2(1)(i) Commercial Courts Act.")
            remedies.append("Transfer suit to Ordinary Civil Court jurisdiction.")

        # Section 12A PIMS Evaluation (Patil Automation v. Rakheja Engineers)
        pims_status = str(case_data.get("s12a_pims_status") or case_data.get("s12a_mediation") or "").lower()
        urgent_relief = bool(case_data.get("urgent_interim_relief_prayed") or case_data.get("order_39_injunction") or case_data.get("urgency_injunction"))

        if not urgent_relief:
            if any(k in pims_status for k in ["not initiated", "no", "omitted", "skipped", "none"]):
                defects.append("MANDATORY_PIMS_BREACH: Section 12A Pre-Institution Mediation omitted without seeking urgent interim relief. Plaint is liable to be rejected under Order VII Rule 11 CPC.")
                fatal = True
                remedies.append("File application for leave to initiate urgent interim relief u/O XXXIX CPC or withdraw plaint and approach Legal Services Authority for PIMS.")

        # Statement of Truth (Order VI Rule 15A CPC)
        sot = case_data.get("statement_of_truth_signed")
        if sot is False or str(sot).lower() in ["no", "missing", "false"]:
            defects.append("STATEMENT_OF_TRUTH_DEFECT: Mandatory Statement of Truth under Order VI Rule 15A CPC missing. Unverified pleadings cannot be read in evidence.")
            remedies.append("File verified Statement of Truth affidavit signed by authorized representative.")

        return {
            "valid": len(defects) == 0,
            "defects": defects,
            "fatal": fatal,
            "remedies": remedies,
            "authority": "Commercial Courts Act, 2015 & Patil Automation (2022) 10 SCC 1"
        }

    @classmethod
    def evaluate_written_statement_timeline(
        cls,
        days_to_ws: Optional[int],
        is_commercial: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates 30/90/120 days deadline for Written Statement under Order VIII Rule 1.
        """
        if days_to_ws is None:
            return {"valid": True, "defect": None, "fatal": False}

        if is_commercial:
            if days_to_ws > cls.COMMERCIAL_WS_MAX_DAYS:
                return {
                    "valid": False,
                    "defect": f"COMMERCIAL_WS_FORFEITURE: Written Statement delayed to day {days_to_ws} (exceeds non-extendable 120-day outer limit). Right to file WS stands forfeited under Order VIII Rule 1 proviso.",
                    "fatal": True,
                    "authority": "SCG Contracts (India) Pvt Ltd v. K.S. Chamankar Infrastructure (2019) 12 SCC 210",
                    "remedy": "Right to file WS cannot be condoned even under Section 151 CPC; participate in trial only for cross-examination."
                }
            elif days_to_ws > 30:
                return {
                    "valid": True,
                    "defect": f"Written Statement filed on day {days_to_ws} (beyond 30 days; within 120-day condonation window subject to costs).",
                    "fatal": False,
                    "remedy": "File application demonstrating sufficient cause for delay with nominal costs."
                }
        else:
            if days_to_ws > cls.ORDINARY_WS_MAX_DAYS:
                return {
                    "valid": False,
                    "defect": f"Written Statement delayed to day {days_to_ws} (exceeds 90-day guideline under Order VIII Rule 1).",
                    "fatal": False,
                    "authority": "Kailash v. Nanhku (2005) 4 SCC 480",
                    "remedy": "Demonstrate exceptional and unavoidable circumstances under Section 151 CPC to seek delayed acceptance."
                }

        return {"valid": True, "defect": None, "fatal": False}
