"""
JudiQ AI — Section 138 NI Act Statutory Rules Evaluator
High-performance statutory rule evaluations for Negotiable Instruments Act litigation.
Includes Section 142(2) territorial jurisdiction, RBI 3-month presentation rules,
Section 143A interim compensation, Section 148 appellate deposits, and Aneeta Hada compliance.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from utils import parse_date, days_between

class NIActStatutoryRules:
    """
    Statutory rule definitions and fast validation methods for Section 138 NI Act cases.
    """

    CHEQUE_VALIDITY_DAYS = 90          # RBI Circular DBOD.AML.BC.No.47/2011-12 (3 Months)
    NOTICE_LIMIT_DAYS = 30             # Section 138(b) statutory notice window
    PAYMENT_GRACE_DAYS = 15            # Section 138(c) statutory grace window
    COMPLAINT_LIMIT_DAYS = 30          # Section 142(1)(b) filing window
    MAX_INTERIM_COMPENSATION_PCT = 20  # Section 143A interim compensation limit (up to 20%)
    MIN_APPELLATE_DEPOSIT_PCT = 20     # Section 148 appellate minimum deposit (at least 20%)

    LANDMARK_PRECEDENTS = {
        "statutory_notice": {
            "citation": "Central Bank of India v. Saxons Farms (1999) 8 SCC 221",
            "court": "Supreme Court of India",
            "ratio": "Notice must clearly demand the specific cheque amount within 30 days of receiving bank dishonour memo."
        },
        "premature_complaint": {
            "citation": "Yogendra Pratap Singh v. Savitri Pandey (2014) 10 SCC 129",
            "court": "Supreme Court of India",
            "ratio": "No cause of action arises prior to the completion of 15 days from notice receipt. Premature complaint is non-est and cannot be cured."
        },
        "legal_presumption": {
            "citation": "Rangappa v. Sri Mohan (2010) 11 SCC 441",
            "court": "Supreme Court of India",
            "ratio": "Section 139 presumption includes the existence of a legally enforceable debt. Standard of rebuttal by accused is preponderance of probabilities."
        },
        "signed_blank_cheque": {
            "citation": "Bir Singh v. Mukesh Kumar (2019) 4 SCC 197",
            "court": "Supreme Court of India",
            "ratio": "A person signing a cheque is presumed to be liable even if particulars are filled by another, unless rebutted by credible evidence."
        },
        "financial_capacity": {
            "citation": "Basalingappa v. Mudibasappa (2019) 5 SCC 418",
            "court": "Supreme Court of India",
            "ratio": "Accused can rebut Section 139 presumption by raising probable doubt regarding complainant's financial capacity to advance large cash loan."
        },
        "vicarious_liability": {
            "citation": "Aneeta Hada v. Godfather Travels & Tours (2012) 5 SCC 661",
            "court": "Supreme Court of India",
            "ratio": "For maintaining prosecution against directors u/s 141, arraigning the company as an accused is an indispensable condition precedent."
        },
        "interim_compensation": {
            "citation": "Rakesh Ranjan Shahi v. State of U.P. (2024) INSC 583",
            "court": "Supreme Court of India",
            "ratio": "Grant of Section 143A interim compensation (up to 20%) is discretionary and requires a reasoned order evaluating prima facie strength."
        },
        "appellate_deposit": {
            "citation": "Surinder Singh Deswal v. Virender Gandhi (2019) 11 SCC 341",
            "court": "Supreme Court of India",
            "ratio": "Appellate Court under Section 148 NI Act ordinarily directs deposit of minimum 20% of fine/compensation to suspend sentence on appeal."
        },
        "territorial_jurisdiction": {
            "citation": "Bridgestone India Pvt Ltd v. Inderpal Singh (2016) 2 SCC 341",
            "court": "Supreme Court of India",
            "ratio": "Section 142(2) (2015 Amendment) governs territorial jurisdiction. Cheque delivered for collection through account gives exclusive jurisdiction to court where payee maintains bank account branch."
        }
    }

    @staticmethod
    def normalize_s138_payload(case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fast typed normalizer consolidating all field aliases in Section 138 data.
        """
        normalized = dict(case_data)
        
        # Cheque Amount
        amt = case_data.get("amount") or case_data.get("cheque_amount") or case_data.get("debt_amount") or 0.0
        try:
            normalized["cheque_amount"] = float(amt)
            normalized["amount"] = float(amt)
        except (ValueError, TypeError):
            normalized["cheque_amount"] = 0.0
            normalized["amount"] = 0.0

        # Key Dates
        normalized["cheque_date"] = case_data.get("cheque_date") or case_data.get("date_of_cheque")
        normalized["presentation_date"] = case_data.get("presentation_date") or case_data.get("date_of_presentation")
        normalized["dishonour_date"] = case_data.get("dishonour_date") or case_data.get("date_of_dishonour")
        normalized["notice_date"] = case_data.get("notice_date") or case_data.get("date_of_notice")
        normalized["notice_delivery_date"] = case_data.get("notice_delivery_date") or case_data.get("notice_received_date")
        normalized["complaint_date"] = case_data.get("complaint_date") or case_data.get("date_of_complaint") or case_data.get("filing_date")

        # Accused / Complainant
        normalized["complainant_name"] = case_data.get("complainant_name") or case_data.get("payee_name") or case_data.get("plaintiff_name")
        normalized["accused_name"] = case_data.get("accused_name") or case_data.get("drawer_name") or case_data.get("defendant_name")
        normalized["accused_type"] = case_data.get("accused_type") or case_data.get("accused_entity_type") or "Individual"

        return normalized

    @classmethod
    def evaluate_cheque_validity(cls, cheque_date: Optional[str], presentation_date: Optional[str]) -> Dict[str, Any]:
        """
        Evaluates whether cheque was presented within 3 months (90 days) under RBI regulations.
        """
        if not cheque_date or not presentation_date:
            return {"valid": True, "defect": None, "fatal": False}

        days = days_between(cheque_date, presentation_date)
        if days is None:
            return {"valid": True, "defect": None, "fatal": False}

        if days < 0:
            return {
                "valid": False,
                "defect": f"Presentation date ({presentation_date}) precedes cheque issuance date ({cheque_date}). Post-dated cheque presented prematurely.",
                "fatal": True,
                "remedy": "Re-present cheque on or after the actual date of the cheque."
            }

        if days > cls.CHEQUE_VALIDITY_DAYS:
            return {
                "valid": False,
                "defect": f"Cheque presented on day {days} after issuance (Limit: 90 days / 3 months under RBI Circular DBOD.AML.BC.No.47/2011-12). Outdated / stale cheque.",
                "fatal": True,
                "authority": "Section 138 Proviso (a) NI Act & RBI Circular 2011-12",
                "remedy": "Section 138 cannot be maintained on a stale cheque; pursue civil recovery under Order 37 CPC / Ordinary Suit if debt is not time-barred."
            }

        return {"valid": True, "defect": None, "fatal": False, "days_elapsed": days}

    @classmethod
    def evaluate_notice_timeline(cls, days_to_notice: Optional[int]) -> Dict[str, Any]:
        """Evaluates whether demand notice was dispatched within statutory 30-day window."""
        if days_to_notice is None:
            return {"valid": True, "defect": None, "fatal": False}
        
        if days_to_notice > cls.NOTICE_LIMIT_DAYS:
            return {
                "valid": False,
                "defect": f"Statutory demand notice dispatched on day {days_to_notice} (delayed by {days_to_notice - cls.NOTICE_LIMIT_DAYS} days; Limit: 30 days u/s 138(b)).",
                "fatal": True,
                "authority": "Central Bank of India v. Saxons Farms (1999) 8 SCC 221",
                "remedy": "Examine if date of receipt of bank memo (rather than date on memo) brings dispatch within 30 days."
            }
        return {"valid": True, "defect": None, "fatal": False}

    @classmethod
    def evaluate_complaint_timeline(cls, days_post_notice: Optional[int]) -> Dict[str, Any]:
        """Evaluates 15-day grace period and 30-day filing window."""
        if days_post_notice is None:
            return {"valid": True, "defect": None, "fatal": False}

        if days_post_notice < cls.PAYMENT_GRACE_DAYS:
            return {
                "valid": False,
                "defect": f"PREMATURE COMPLAINT: Complaint filed prematurely on day {days_post_notice}. Section 138 cause of action only matures on day 16 post receipt of notice.",
                "fatal": True,
                "authority": "Yogendra Pratap Singh v. Savitri Pandey (2014) 10 SCC 129",
                "remedy": "Withdraw premature complaint before summons and refile upon cause of action maturity."
            }
        
        total_limit = cls.PAYMENT_GRACE_DAYS + cls.COMPLAINT_LIMIT_DAYS
        if days_post_notice > total_limit:
            delay_days = days_post_notice - total_limit
            return {
                "valid": False,
                "defect": f"Complaint filed after {days_post_notice} days (delayed by {delay_days} days u/s 142(1)(b)).",
                "fatal": True,
                "authority": "Section 142(1)(b) NI Act",
                "remedy": "File Section 142(1)(b) proviso application for condonation of delay showing sufficient cause."
            }

        return {"valid": True, "defect": None, "fatal": False}

    @classmethod
    def evaluate_s142_jurisdiction(
        cls,
        payee_branch: Optional[str] = None,
        drawer_branch: Optional[str] = None,
        presentation_mode: str = "account_collection"
    ) -> Dict[str, Any]:
        """
        Evaluates Section 142(2) territorial jurisdiction under the 2015 Amendment.
        """
        if "account" in presentation_mode.lower() or "clearing" in presentation_mode.lower() or presentation_mode == "account_collection":
            competent_court = f"Court having territorial jurisdiction over Payee's Bank Branch ({payee_branch or 'Payee Branch'})"
            rule = "Section 142(2)(a) NI Act: Cheque delivered for collection through an account; jurisdiction lies where branch of bank maintaining payee's account is situated."
        else:
            competent_court = f"Court having territorial jurisdiction over Drawer's Bank Branch ({drawer_branch or 'Drawer Branch'})"
            rule = "Section 142(2)(b) NI Act: Cheque presented for payment otherwise through an account (over-the-counter); jurisdiction lies where drawer's branch is situated."

        return {
            "competent_jurisdiction": competent_court,
            "statutory_rule": rule,
            "governing_precedent": "Bridgestone India Pvt Ltd v. Inderpal Singh (2016) 2 SCC 341",
            "section": "Section 142(2) Negotiable Instruments Act, 1881"
        }

    @classmethod
    def evaluate_vicarious_liability(cls, accused_type: str, company_arrayed: Optional[bool], directors_named: Optional[bool]) -> Dict[str, Any]:
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
                    "authority": "Aneeta Hada v. Godfather Travels & Tours (2012) 5 SCC 661",
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

    @classmethod
    def calculate_interim_compensation_estimate(cls, cheque_amount: float) -> float:
        """Calculates maximum 20% interim compensation under Section 143A."""
        if not cheque_amount or cheque_amount <= 0:
            return 0.0
        return round(float(cheque_amount) * (cls.MAX_INTERIM_COMPENSATION_PCT / 100.0), 2)

    @classmethod
    def calculate_appellate_deposit_estimate(cls, fine_amount: float) -> float:
        """Calculates minimum 20% appellate deposit under Section 148."""
        if not fine_amount or fine_amount <= 0:
            return 0.0
        return round(float(fine_amount) * (cls.MIN_APPELLATE_DEPOSIT_PCT / 100.0), 2)
