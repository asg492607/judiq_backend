from typing import Any, List, Dict

def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default

class StrategyEngine:
    """
    Advanced Litigation Strategy Engine — generates actionable litigation maps,
    litigation economics, and procedural roadmaps.
    """

    @staticmethod
    def generate_strategy(case_data: Dict, concepts: List[Dict], score: int, adversarial_risk: float = 0.4) -> Dict[str, Any]:
        """Orchestrates all strategy components for the core engine."""
        from adversarial_engine import AdversarialEngine
        return {
            "litigation_map": StrategyEngine.generate_litigation_map(case_data, score, concepts),
            "economics": StrategyEngine.calculate_economics(case_data, score),
            "roadmap": AdversarialEngine.calculate_stage_survivability(score, adversarial_risk),
            "checkpoints": StrategyEngine.get_advocate_checkpoints(score)
        }

    @staticmethod
    def calculate_economics(case_data: Dict, score: int) -> Dict[str, Any]:
        """Models delay economics and settlement pressure."""
        amount = _number(case_data.get("amount") or case_data.get("cheque_amount") or case_data.get("debt_amount"))
        est_trial_duration = 36 # Months
        legal_cost_est = amount * 0.10
        
        # Settlement preference logic
        settlement_preference = "HIGH" if score < 65 else "LOW"
        if amount > 1000000 and score < 75: settlement_preference = "VERY HIGH"

        return {
            "recovery_modeling": {
                "immediate_settlement": f"₹{amount * 0.85:,.0f} (Recommended 15% haircut)",
                "trial_outcome_3yr": f"₹{amount * 1.5:,.0f} (Incl. 9% Interest + 20% Penalty)",
                "cost_of_delay": f"₹{amount * 0.12:,.0f} (Inflation + Opportunity Cost)"
            },
            "settlement_posture": settlement_preference,
            "estimated_trial_duration_months": est_trial_duration,
            "estimated_legal_cost": legal_cost_est,
            "economic_rationale": "Immediate liquidity is preferable given the 36-month standard trial duration in jurisdictional courts."
        }

    @staticmethod
    def generate_procedural_roadmap(score: int) -> List[Dict]:
        """Actionable tactical roadmap."""
        return [
            {"stage": "Pre-Trial", "objective": "Secure Section 143A Interim Compensation (20% of cheque amount).", "priority": "CRITICAL"},
            {"stage": "Evidence", "objective": "Verify S.65B Certificate for digital records.", "priority": "HIGH"},
            {"stage": "Cross-Exam", "objective": "Rebut 'Security Cheque' defense via Sampelly Satyanarayana Rao precedent.", "priority": "MEDIUM"}
        ]

    @staticmethod
    def get_advocate_checkpoints(score: int) -> List[str]:
        """Human override and validation points."""
        return [
            "MANDATORY: Verify original AD Card signature before filing affidavit of service.",
            "STRATEGIC: Consult Senior Counsel if 'Financial Capacity' is challenged via S.91 application.",
            "DISCRETIONARY: Evaluate accused's social standing for 'Stop Payment' tactic rebuttal."
        ]

    @staticmethod
    def generate_litigation_map(case_data: Dict, score: float, concepts: List[Dict], detected_defences: List[Dict] = None) -> Dict[str, Any]:
        # Keep existing map logic but wrap it
        concept_names = {c.get("concept") for c in concepts if isinstance(c, dict)}
        prosecution = {"primary_objective": "Secure Conviction", "tactical_moves": ["File S.143A application."]}
        defence_moves = ["Challenge debt provenance."]
        if detected_defences:
            defence_moves.extend(
                str(item.get("argument"))
                for item in detected_defences
                if isinstance(item, dict) and item.get("argument")
            )
        defence = {"primary_objective": "Rebut S.139", "tactical_moves": defence_moves}
        
        return {
            "prosecution": prosecution,
            "defence": defence,
            "overall_posture": "Aggressive" if score > 70 else "Settlement-First"
        }
