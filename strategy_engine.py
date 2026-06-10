from typing import Any, List, Dict
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
        amount = float(case_data.get("amount") or 0)
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
        concept_names = {c["concept"] for c in concepts}
        prosecution = {"primary_objective": "Secure Conviction", "tactical_moves": ["File S.143A application."]}
        defence = {"primary_objective": "Rebut S.139", "tactical_moves": ["Challenge debt provenance."]}
        
        return {
            "prosecution": prosecution,
            "defence": defence,
            "overall_posture": "Aggressive" if score > 70 else "Settlement-First"
        }
