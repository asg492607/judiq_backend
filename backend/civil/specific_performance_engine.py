"""
JudiQ AI — Specific Performance Statutory Evaluator (Specific Relief Act, 1963)
Evaluates Section 10 mandatory performance, Section 16(c) continuous readiness & willingness,
Section 20 substituted performance, and Section 20A infrastructure injunction bar.
"""

from typing import Dict, Any, List

class SpecificPerformanceEngine:
    """
    Evaluates suits for Specific Performance under the Specific Relief Act, 1963 (amended 2018).
    """

    @classmethod
    def evaluate_specific_performance_claim(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates Section 16(c) continuous readiness & willingness and statutory enforceability.
        """
        readiness_proof = str(case_data.get("readiness_and_willingness_proof") or case_data.get("financial_capacity_proof") or "").lower()
        stamping_status = str(case_data.get("agreement_registered_and_stamped") or case_data.get("stamping_status") or "").lower()

        fatal_defect = None
        remediation = None
        score = 60

        # 1. Section 16(c) Readiness & Willingness Verification (U.N. Krishnamurthy v. A.M. Krishnamurthy)
        has_financial_proof = any(k in readiness_proof for k in ["bank", "solvency", "deposit", "loan", "tender", "available", "ready"])
        missing_financial_proof = any(k in readiness_proof for k in ["no financial", "unproven", "missing", "lack of proof"])

        if missing_financial_proof or (not has_financial_proof and "readiness_and_willingness_proof" in case_data):
            fatal_defect = "SECTION_16C_READINESS_FATAL: Plaintiff failed to produce documentary proof of financial capacity (bank balance / credit line / tender letter) on the date of breach. Mandatory statutory bar u/s 16(c) Specific Relief Act."
            remediation = "Procure certified bank account statements, fixed deposit receipts, or loan sanction letters covering the entire contractual duration."
            score = 15
        elif has_financial_proof:
            score += 25

        # 2. Section 35 Indian Stamp Act / Registration Act Section 17 & 49
        if any(k in stamping_status for k in ["insufficiently stamped", "unstamped"]):
            fatal_defect = "STAMP_ACT_SECTION_35_BAR: Agreement of sale is insufficiently stamped and inadmissible in evidence until impounded and 10x penalty paid."
            remediation = "Deposit deficit stamp duty and 10x penalty before the Collector of Stamps / Court under Section 35 Stamp Act."
            score = min(score, 30)

        # 3. Section 20 Substituted Performance
        sub_perf = bool(case_data.get("substituted_performance_invoked"))
        if sub_perf:
            notice_served = bool(case_data.get("substituted_performance_notice_30_days"))
            if not notice_served:
                fatal_defect = "SECTION_20_SRA_DEFECT: Substituted performance undertaken without serving mandatory 30-day prior written notice."

        # 4. Section 20A Infrastructure Project Bar
        if bool(case_data.get("infrastructure_project")):
            fatal_defect = "SECTION_20A_INFRASTRUCTURE_BAR: Absolute statutory bar on injunctions impeding infrastructure contracts."

        is_maintainable = fatal_defect is None

        return {
            "maintainable": is_maintainable,
            "readiness_willingness_established": has_financial_proof and not missing_financial_proof,
            "fatal_defect": fatal_defect,
            "remediation": remediation,
            "score": score,
            "statutory_mandate": "Section 10 Specific Relief Act (Mandatory Enforcement post-2018 Amendment)",
            "key_precedent": "U.N. Krishnamurthy v. A.M. Krishnamurthy (2022) SCC OnLine SC 840"
        }
