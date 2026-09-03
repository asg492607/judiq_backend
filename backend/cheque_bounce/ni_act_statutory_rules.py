"""
JudiQ AI — Section 138 NI Act Statutory Rules Evaluator
High-performance statutory rule evaluations for Negotiable Instruments Act litigation.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date

class NIActStatutoryRules:
    """
    Statutory rule definitions and fast validation methods for Section 138 NI Act cases.
    """

    NOTICE_LIMIT_DAYS = 30
    PAYMENT_GRACE_DAYS = 15
    COMPLAINT_LIMIT_DAYS = 30
    MAX_INTERIM_COMPENSATION_PCT = 20

    LANDMARK_PRECEDENTS = {
        "statutory_notice": {
            "citation": "Central Bank of India v. Saxons Farms (1999) 8 SCC 221",
            "ratio": "Notice must clearly demand the specific cheque amount within 30 days of receiving bank dishonour memo."
        },
        "cause_of_action": {
            "citation": "Yogendra Pratap Singh v. Savitri Pandey (2014) 10 SCC 129",
            "ratio": "No cause of action arises prior to the completion of 15 days from notice receipt. Premature complaint is non-maintainable."
        },
        "legal_presumption": {
            "citation": "Rangappa v. Sri Mohan (2010) 11 SCC 441",
            "ratio": "Section 139 presumption includes the existence of a legally enforceable debt. Standard of rebuttal by accused is preponderance of probabilities."
        },
        "signed_blank_cheque": {
            "citation": "Bir Singh v. Mukesh Kumar (2019) 4 SCC 197",
            "ratio": "A person signing a cheque is presumed to be liable even if particulars are filled by another, unless rebutted by credible evidence."
        },
        "vicarious_liability": {
            "citation": "Aneeta Hada v. Godfather Travels & Tours (2012) 5 SCC 661",
            "ratio": "For maintaining prosecution against directors u/s 141, arraigning the company as an accused is a condition precedent."
        },
        "interim_compensation": {
            "citation": "Rakesh Ranjan Shahi v. State of U.P. (2024) INSC 583",
            "ratio": "Grant of Section 143A interim compensation (up to 20%) is discretionary and requires reasoned order on prima facie strength."
        }
    }

    @staticmethod
    def evaluate_notice_timeline(days_to_notice: Optional[int]) -> Dict[str, Any]:
        """Evaluates whether demand notice was dispatched within statutory 30-day window."""
        if days_to_notice is None:
            return {"valid": True, "defect": None, "fatal": False}
        
        if days_to_notice > NIActStatutoryRules.NOTICE_LIMIT_DAYS:
            return {
                "valid": False,
                "defect": f"Statutory demand notice dispatched on day {days_to_notice} (delayed by {days_to_notice - NIActStatutoryRules.NOTICE_LIMIT_DAYS} days; Limit: 30 days u/s 138(b)).",
                "fatal": True,
                "remedy": "Examine if date of receipt of bank memo (rather than date on memo) brings dispatch within 30 days."
            }
        return {"valid": True, "defect": None, "fatal": False}

    @staticmethod
    def evaluate_complaint_timeline(days_post_notice: Optional[int]) -> Dict[str, Any]:
        """Evaluates 15-day grace period and 30-day filing window."""
        if days_post_notice is None:
            return {"valid": True, "defect": None, "fatal": False}

        if days_post_notice < NIActStatutoryRules.PAYMENT_GRACE_DAYS:
            return {
                "valid": False,
                "defect": f"Complaint filed prematurely on day {days_post_notice}. Section 138 cause of action only matures on day 16.",
                "fatal": True,
                "remedy": "Withdraw premature complaint with liberty to refile upon maturity or explain service receipt timeline."
            }
        
        total_limit = NIActStatutoryRules.PAYMENT_GRACE_DAYS + NIActStatutoryRules.COMPLAINT_LIMIT_DAYS
        if days_post_notice > total_limit:
            delay_days = days_post_notice - total_limit
            return {
                "valid": False,
                "defect": f"Complaint filed after {days_post_notice} days (delayed by {delay_days} days u/s 142(1)(b)).",
                "fatal": True,
                "remedy": "File Section 142(1)(b) proviso application for condonation of delay showing sufficient cause."
            }

        return {"valid": True, "defect": None, "fatal": False}

    @staticmethod
    def evaluate_vicarious_liability(accused_type: str, company_arrayed: Optional[bool], directors_named: Optional[bool]) -> Dict[str, Any]:
        """Evaluates Aneeta Hada compliance for corporate drawers."""
        corporate_types = {
            "pvt ltd", "ltd company", "pvt ltd/ltd company", "public ltd",
            "public ltd company", "llp", "partnership firm", "trust", "society"
        }
        type_str = str(accused_type or "").strip().lower()
        if type_str in corporate_types or any(ct in type_str for ct in ["pvt", "ltd", "llp", "partnership", "firm", "company"]):
            if company_arrayed is False or company_arrayed == "No":
                return {
                    "valid": False,
                    "defect": "Company is not arrayed as principal accused. Prosecution against directors alone is fatal (Aneeta Hada v. Godfather Travels).",
                    "fatal": True,
                    "remedy": "Implead company as Accused No. 1 via amendment before summons are issued."
                }
            if not directors_named or directors_named == "No":
                return {
                    "valid": False,
                    "defect": "Specific averments regarding day-to-day management and in-charge status u/s 141 missing in complaint.",
                    "fatal": False,
                    "remedy": "Detail specific role of signatory and managing directors in affidavit."
                }
        return {"valid": True, "defect": None, "fatal": False}

    @staticmethod
    def calculate_interim_compensation_estimate(cheque_amount: float) -> float:
        """Calculates maximum 20% interim compensation under Section 143A."""
        if not cheque_amount or cheque_amount <= 0:
            return 0.0
        return round(float(cheque_amount) * (NIActStatutoryRules.MAX_INTERIM_COMPENSATION_PCT / 100.0), 2)
