import logging
from typing import Dict, List, Any
from adversarial_engine import AdversarialEngine

logger = logging.getLogger(__name__)

class SarfaesiAdversarialEngine(AdversarialEngine):
    PROCEDURAL_STAGES = [
        {"id": "notice_13_2", "name": "Section 13(2) Demand Notice", "baseline_prob": 0.90},
        {"id": "rep_13_3a", "name": "Section 13(3A) Representation Reply", "baseline_prob": 0.85},
        {"id": "possession_13_4", "name": "Section 13(4) Possession & Publication", "baseline_prob": 0.80},
        {"id": "dm_sec_14", "name": "Section 14 DM/CMM Order Execution", "baseline_prob": 0.75},
        {"id": "drt_sa_17", "name": "Section 17 Securitisation Application (DRT)", "baseline_prob": 0.55},
        {"id": "drt_final", "name": "DRT Final Judgment & Order", "baseline_prob": 0.65},
        {"id": "drat_sec_18", "name": "Section 18 DRAT Appeal (Pre-Deposit)", "baseline_prob": 0.50}
    ]

    @classmethod
    def audit_case(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if concepts is None:
            concepts = []

        risks = []
        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        # Check 1: CERSAI Non-Registration
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai:
            vector = "CERSAI Registration Missing (Section 26D)"
            desc = "Security interest is not registered on CERSAI portal, creating an statutory prohibition under Section 26D against enforcement."
            rebuttal = "Register security interest immediately on CERSAI portal before initiating Chapter III measures." if not is_borrower else "Seek absolute stay on Section 13(4) measures under Section 26D statutory bar."
            risks.append({
                "adversarial_vector": vector,
                "risk": vector,
                "severity": "CRITICAL" if not is_borrower else "HIGH",
                "description": desc,
                "rebuttal": rebuttal,
                "survival_probability": "15%" if not is_borrower else "85%",
                "collapse_risk": "85%" if not is_borrower else "15%",
                "why_applied": "Mandatory CERSAI portal registration check U/S 26D."
            })

        # Check 2: Section 13(3A) Objection Reply Defect
        borrower_rep = case_data.get("borrower_representation_date")
        bank_reply = case_data.get("bank_reply_13_3a_date")
        if borrower_rep and not bank_reply and case_data.get("possession_13_4_date"):
            vector = "Unanswered Section 13(3A) Representation (Mardia Chemicals Trap)"
            desc = "Bank proceeded to Section 13(4) possession without serving a reasoned reply rejecting borrower's objections."
            rebuttal = "Withdraw premature Section 13(4) notice, issue reasoned reply under 13(3A), and re-issue possession notice." if not is_borrower else "Implead Mardia Chemicals rule to set aside Section 13(4) possession as illegal and void."
            risks.append({
                "adversarial_vector": vector,
                "risk": vector,
                "severity": "CRITICAL",
                "description": desc,
                "rebuttal": rebuttal,
                "survival_probability": "20%",
                "collapse_risk": "80%",
                "why_applied": "Mardia Chemicals Ltd. v. UOI landmark precedent."
            })

        # Check 3: Agricultural Property Exemption
        is_agri = case_data.get("is_agricultural_land") or str(case_data.get("agricultural_land", "")).lower() in ["yes", "true", "1"]
        if is_agri:
            vector = "Agricultural Land Exemption (Section 31(i))"
            desc = "Secured property is classified as agricultural land, which is completely exempted from SARFAESI enforcement."
            rebuttal = "Initiate recovery via Civil Suit or DRT Original Application (OA 1993) instead of SARFAESI." if not is_borrower else "File Section 17 SA to quash SARFAESI proceedings based on Section 31(i) statutory exemption."
            risks.append({
                "adversarial_vector": vector,
                "risk": vector,
                "severity": "CRITICAL",
                "description": desc,
                "rebuttal": rebuttal,
                "survival_probability": "10%" if not is_borrower else "90%",
                "collapse_risk": "90%" if not is_borrower else "10%",
                "why_applied": "ITC Ltd. v. Blue Coast Hotels & Section 31(i) statutory bar."
            })

        adversarial_risk = cls.calculate_adversarial_risk(risks)

        return {
            "risks_and_rebuttals": risks,
            "contradictions": cls.detect_contradictions(case_data, concepts),
            "adversarial_risk": adversarial_risk,
            "analysis_nodes": [
                {
                    "severity": r["severity"],
                    "risk_explained": r["description"]
                } for r in risks if r["severity"] in ["CRITICAL", "FATAL"]
            ]
        }

    @classmethod
    def detect_contradictions(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        contradictions = []
        notice_13_2 = case_data.get("notice_13_2_date")
        npa_date = case_data.get("npa_date")

        from utils import days_between
        if npa_date and notice_13_2:
            days = days_between(npa_date, notice_13_2)
            if days is not None and days < 0:
                contradictions.append({
                    "severity": "CRITICAL",
                    "issue": "Section 13(2) Notice Precedes NPA Date",
                    "description": f"Demand notice dated {notice_13_2} precedes the formal NPA classification date of {npa_date}.",
                    "impact": "Incalculable procedural flaw; renders demand notice invalid."
                })

        return contradictions

    @classmethod
    def detect_timeline_anomalies(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        anomalies = []
        possession_date = case_data.get("possession_13_4_date")
        sa_filing = case_data.get("sa_filing_date")

        from utils import days_between
        if possession_date and sa_filing:
            days = days_between(possession_date, sa_filing)
            if days is not None and days > 45:
                anomalies.append({
                    "anomaly_type": "Limitation Breach",
                    "description": f"Securitisation Application filed in DRT after {days} days from possession date (Statutory limit: 45 days)."
                })

        return anomalies
