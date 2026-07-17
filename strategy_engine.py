from typing import Any, List, Dict
def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default
class StrategyEngine:
    @staticmethod
    def generate_strategy(case_data: Dict, concepts: List[Dict], score: int, adversarial_risk: float = 0.4) -> Dict[str, Any]:
        from adversarial_engine import AdversarialEngine
        return {
            "litigation_map": StrategyEngine.generate_litigation_map(case_data, score, concepts),
            "economics": StrategyEngine.calculate_economics(case_data, score),
            "roadmap": AdversarialEngine.calculate_stage_survivability(score, adversarial_risk, case_data.get("condonation_attached", False)),
            "checkpoints": StrategyEngine.get_advocate_checkpoints(score, case_data)
        }
    @staticmethod
    def calculate_economics(case_data: Dict, score: int) -> Dict[str, Any]:
        amount = _number(case_data.get("amount") or case_data.get("cheque_amount") or case_data.get("debt_amount"))
        est_trial_duration = 36         
        legal_cost_est = amount * 0.10
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
    def generate_procedural_roadmap(score: int, case_data: Dict = None) -> List[Dict]:
        roadmap = []
        if case_data:
            accused_type = str(case_data.get("accused_type", "")).lower()
            accused_name = str(case_data.get("accused_name", "")).lower()
            is_company = accused_type in {"company", "pvt ltd/ltd company", "partnership firm"} or any(
                x in accused_name for x in ["pvt", "ltd", "corp", "inc", "co.", "company"]
            )
            directors_named = case_data.get("directors_named", False)
            if is_company and not directors_named:
                roadmap.append({
                    "stage": "Drafting", 
                    "objective": "1. Copy the injected Section 141 management clause into paragraph 3 of your complaint draft to reclaim +5 points and remove the threshold maintainability risk.", 
                    "priority": "FATAL"
                })
        agreement_type = str(case_data.get("agreement_type", "")).lower()
        if "invoice" in agreement_type or "commercial" in agreement_type or "business" in agreement_type:
            security_precedent = "Sunil Todi v. State of Gujarat (2021) for commercial supply security cheques"
        else:
            security_precedent = "Sampelly Satyanarayana Rao precedent for loan security cheques"
        roadmap.extend([
            {"stage": "Pre-Trial", "objective": "Secure Section 143A Interim Compensation (20% of cheque amount).", "priority": "CRITICAL"},
            {"stage": "Evidence", "objective": "Verify S.63(4) BSA Certificate for digital records.", "priority": "HIGH"},
            {"stage": "Cross-Exam", "objective": f"Rebut 'Security Cheque' defense via {security_precedent}.", "priority": "MEDIUM"}
        ])
        return roadmap
    @staticmethod
    def get_advocate_checkpoints(score: int, case_data: Dict = None) -> List[str]:
        checkpoints = []
        if case_data:
            accused_type = str(case_data.get("accused_type", "")).lower()
            accused_name = str(case_data.get("accused_name", "")).lower()
            is_company = accused_type in {"company", "pvt ltd/ltd company", "partnership firm"} or any(
                x in accused_name for x in ["pvt", "ltd", "corp", "inc", "co.", "company"]
            )
            directors_named = case_data.get("directors_named", False)
            if is_company and not directors_named:
                checkpoints.append("1. Copy the injected Section 141 management clause into paragraph 3 of your complaint draft to reclaim +5 points and remove the threshold maintainability risk.")
        checkpoints.extend([
            "MANDATORY: Verify original AD Card signature before filing affidavit of service.",
            "STRATEGIC: Consult Senior Counsel if 'Financial Capacity' is challenged via S.91 application.",
            "DISCRETIONARY: Evaluate accused's social standing for 'Stop Payment' tactic rebuttal."
        ])
        return checkpoints
    @staticmethod
    def generate_litigation_map(case_data: Dict, score: float, concepts: List[Dict], detected_defences: List[Dict] = None) -> Dict[str, Any]:
        concept_names = {c.get("concept") for c in concepts if isinstance(c, dict)}
        prosecution = {"primary_objective": "Secure Conviction", "tactical_moves": ["File S.143A application."]}
        accused_type = str(case_data.get("accused_type", "")).lower()
        accused_name = str(case_data.get("accused_name", "")).lower()
        is_company = accused_type in {"company", "pvt ltd/ltd company", "partnership firm"} or any(
            x in accused_name for x in ["pvt", "ltd", "corp", "inc", "co.", "company"]
        )
        directors_named = case_data.get("directors_named", False)
        if is_company and not directors_named:
            prosecution["tactical_moves"].insert(0, "1. Copy the injected Section 141 management clause into paragraph 3 of your complaint draft to reclaim +5 points and remove the threshold maintainability risk.")
        memo_signed_str = str(case_data.get("memo_signed", ""))
        if "Unsigned" in memo_signed_str:
            prosecution["tactical_moves"].append("Summon Bank Official as witness under S.311 CrPC to prove dishonour since memo is unsigned.")
        court_att = str(case_data.get("court_attendance", ""))
        if "Skipping Dates" in court_att or "Absconding" in str(case_data.get("evasive_conduct", "")):
            prosecution["tactical_moves"].append("Apply for Non-Bailable Warrants (NBW) & initiate S.82/83 CrPC proceedings to compel attendance.")
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
