"""
JudiQ AI — Civil Injunction & Interim Relief Evaluator (Order XXXIX & XXXVIII CPC)
Evaluates Golden Triad (Prima Facie, Balance of Convenience, Irreparable Injury),
Section 20A Infrastructure project bar, and Attachment Before Judgment thresholds.
"""

from typing import Dict, Any, List

class InjunctionEvaluator:
    """
    Evaluates Temporary Injunction applications under Order XXXIX Rules 1 & 2 CPC
    and Attachment Before Judgment under Order XXXVIII Rule 5 CPC.
    """

    @classmethod
    def evaluate_order_39_injunction(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates interim injunction viability score (0 to 100) and identifies statutory bars.
        """
        score = 0
        factors = []
        fatal_bar = None

        # Check Section 20A Specific Relief Act Infrastructure Project Bar
        is_infra = bool(case_data.get("infrastructure_project") or case_data.get("is_infrastructure"))
        if is_infra:
            fatal_bar = "SECTION_20A_INFRASTRUCTURE_BAR: Absolute statutory prohibition on grant of injunctions that cause hindrance/delay to Infrastructure Projects (Section 20A Specific Relief Act)."
            return {
                "injunction_granted_probability": 0.0,
                "golden_triad_satisfied": False,
                "prima_facie_score": 0,
                "balance_of_convenience_score": 0,
                "irreparable_injury_score": 0,
                "fatal_bar": fatal_bar,
                "authority": "Section 20A Specific Relief Act, 1963 & NHAI v. Ganga Enterprises (2020)",
                "remedy": "Pursue solely monetary damages or dispute resolution through conciliation without interim injunction."
            }

        # 1. Prima Facie Case (Weight: 40 points)
        pf_val = str(case_data.get("prima_facie_case_evidence") or case_data.get("prima_facie_case") or "").lower()
        if any(k in pf_val for k in ["strong", "clear", "registered", "unbroken"]):
            score += 40
            factors.append("Strong documentary prima facie case established (Title / Unbroken Contract).")
        elif any(k in pf_val for k in ["triable", "disputed", "arguable"]):
            score += 25
            factors.append("Triable issue on disputed facts established.")
        else:
            score += 10
            factors.append("Weak or uncorroborated prima facie assertion.")

        # 2. Balance of Convenience (Weight: 30 points)
        boc_val = str(case_data.get("balance_of_convenience") or "").lower()
        if any(k in boc_val for k in ["plaintiff", "applicant", "favours plaintiff"]):
            score += 30
            factors.append("Balance of convenience substantially favours Plaintiff / Applicant.")
        elif any(k in boc_val for k in ["equal", "balanced", "both"]):
            score += 18
            factors.append("Balance of convenience is equally poised.")
        else:
            score += 5
            factors.append("Balance of convenience tilts towards Defendant (disproportionate business hardship).")

        # 3. Irreparable Injury (Weight: 30 points)
        ii_val = str(case_data.get("irreparable_injury_pleaded") or case_data.get("irreparable_injury") or "").lower()
        if any(k in ii_val for k in ["irreversible", "incapable", "severe", "demolition", "alienation"]):
            score += 30
            factors.append("Irreparable injury incapable of monetary restitution conclusively pleaded.")
        elif any(k in ii_val for k in ["monetary", "damages adequate", "quantifiable"]):
            score += 10
            factors.append("Monetary damages provide adequate alternative relief (Section 41(h) SRA risk).")
        else:
            score += 5
            factors.append("No material evidentiary proof of immediate irreparable loss.")

        probability = round(score / 100.0 * 100, 1)
        satisfied = probability >= 65.0

        return {
            "injunction_granted_probability": probability,
            "golden_triad_satisfied": satisfied,
            "score": score,
            "factors": factors,
            "fatal_bar": None,
            "authority": "Dalpat Kumar v. Prahlad Singh (1992) 1 SCC 719 & Wander Ltd v. Antox India (1990)",
            "compliance_checklist": [
                {"item": "Order XXXIX Rule 3 Ex-Parte Service Affidavit within 24 hours", "status": "REQUIRED"},
                {"item": "Order XXXIX Rule 3A 30-Day Disposal Window Tracking", "status": "ACTIVE"}
            ]
        }

    @classmethod
    def evaluate_order_38_attachment(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates Order XXXVIII Rule 5 CPC threshold for Attachment Before Judgment.
        """
        disposing = bool(case_data.get("debtor_disposing_assets") or case_data.get("alienation_threat"))
        intent_to_obstruct = bool(case_data.get("intent_to_obstruct_execution") or case_data.get("fraudulent_removal"))

        if disposing and intent_to_obstruct:
            return {
                "attachment_viable": True,
                "confidence": "HIGH",
                "authority": "Order XXXVIII Rule 5 CPC (Raman Tech v. Quality Buildcon)",
                "action": "File Application for Attachment Before Judgment with specific asset schedule and encumbrance proof."
            }
        return {
            "attachment_viable": False,
            "confidence": "LOW",
            "authority": "Raman Tech & Process Engg Co v. Quality Buildcon (2008) 2 SCC 302",
            "warning": "Attachment before judgment is a drastic power; vague apprehension without documentary proof of fraudulent asset removal will be dismissed with costs."
        }
