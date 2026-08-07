from typing import Dict, Any

class CriminalEconomicsEngine:
    """
    Evaluates financial dynamics, bail bond requirements, litigation expenditure,
    plea bargaining eligibility (Chapter XXI-A CrPC / Chapter XXII BNSS),
    and potential economic exposure in criminal proceedings.
    """

    @classmethod
    def calculate_economics(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        offense_type = str(case_data.get("offense_type", "General")).upper()
        severity = case_data.get("severity_score", 50)
        punishment = case_data.get("punishment_years", 3)
        amount = case_data.get("amount_involved") or case_data.get("financial_amount") or 0

        base_bond = 10000
        if punishment >= 10 or offense_type in ["302", "376", "NDPS", "103", "64"]:
            base_bond = 100000
        elif punishment >= 7 or offense_type in ["420", "406", "307", "318", "316"]:
            base_bond = 50000
        elif punishment >= 3:
            base_bond = 25000

        estimated_litigation_cost = base_bond * 2.5

        # Plea Bargaining Eligibility (S.265A CrPC / S.289 BNSS)
        # Eligible if punishment <= 7 years, and not affecting socio-economic condition or women/children
        plea_bargain_eligible = punishment <= 7 and offense_type not in ["302", "376", "304B", "103", "64", "80", "NDPS", "POCSO"]

        return {
            "bail_economics": {
                "estimated_surety_bond": base_bond,
                "cash_bail_viability": "Standard" if base_bond <= 50000 else "High Surety Required",
                "property_surety_required": base_bond >= 100000
            },
            "litigation_exposure": {
                "projected_trial_cost": estimated_litigation_cost,
                "financial_dispute_amount": amount,
                "economic_settlement_recommended": offense_type in ["420", "406", "318", "316"] and amount > 0
            },
            "trial_vs_plea": {
                "plea_bargain_eligible": plea_bargain_eligible,
                "plea_bargain_provision": "Chapter XXI-A CrPC (S.265A-265L) / Chapter XXII BNSS (S.289-300)",
                "recommended_path": "Plea Bargain Application" if plea_bargain_eligible and severity > 80 else "Contest on Merits"
            }
        }
