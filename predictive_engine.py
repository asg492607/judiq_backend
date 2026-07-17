import logging
from typing import Dict, Any
logger = logging.getLogger(__name__)
class PredictiveEngine:
    @staticmethod
    def calculate_settlement_probability(score: float, case_data: Dict[str, Any], concepts: list) -> Dict[str, Any]:
        base_prob = 50.0
        factors = []
        if score > 75:
            base_prob += 20
            factors.append("Strong complainant case puts heavy trial pressure on accused to settle.")
        elif score < 40:
            base_prob -= 30
            factors.append("Weak complainant case encourages accused to contest the trial.")
        if str(case_data.get("accused_type")).upper() == "CORPORATE":
            base_prob += 15
            factors.append("Corporate entities prefer to settle S.138 cases to avoid director liability and reputational damage.")
        defect_concepts = ["notice_defect", "limitation_barred", "timeline_violation"]
        if any(c.get("concept") in defect_concepts for c in concepts):
            base_prob -= 25
            factors.append("Statutory defects give accused a clear acquittal route, reducing settlement leverage.")
        try:
            amt = float(case_data.get("amount", 0))
            if amt > 1000000:             
                base_prob += 10
                factors.append("High-value disputes often result in structured EMI settlements during mediation.")
        except:
            pass
        final_prob = max(5.0, min(95.0, base_prob))
        recommendation = "PURSUE MEDIATION" if final_prob > 60 else ("TRIAL LIKELY" if final_prob < 40 else "NEUTRAL (EQUAL ODDS)")
        return {
            "probability_percentage": round(final_prob, 1),
            "recommendation": recommendation,
            "key_factors": factors
        }
    @staticmethod
    def forecast_penalty_and_compensation(score: float, case_data: Dict[str, Any], concepts: list) -> Dict[str, Any]:
        try:
            amt = float(case_data.get("amount", 0))
        except:
            amt = 0.0
        interim_likely = score > 60 and not any(c.get("concept") == "notice_defect" for c in concepts)
        if interim_likely:
            min_interim = round(amt * 0.10, 2)
            max_interim = round(amt * 0.20, 2)
            interim_statement = f"Eligible under Sec 143A. High probability of court ordering 10-20% (₹{min_interim} to ₹{max_interim}) during trial."
        else:
            interim_statement = "Low probability of Sec 143A interim compensation due to evidentiary or statutory weaknesses."
        if amt > 0:
            final_comp = f"Up to ₹{amt * 2} (twice the cheque amount) under Sec 138/357."
        else:
            final_comp = "Up to twice the cheque amount."
        if str(case_data.get("accused_type")).upper() == "CORPORATE":
            imprisonment = "Directors/Signatories face up to 2 years imprisonment under Sec 141 if vicarious liability is proven."
        else:
            imprisonment = "Standard Sec 138 penalty: Up to 2 years simple imprisonment."
        return {
            "interim_compensation_143a": interim_statement,
            "final_compensation_estimate": final_comp,
            "imprisonment_risk": imprisonment,
            "is_interim_likely": interim_likely
        }
