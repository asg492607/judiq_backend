from typing import Dict, Any

class CriminalEconomicsEngine:
    """
    S.138-Style Economics modeling for Criminal Trials.
    Calculates Trial vs Plea Bargain costs, Bail Bonds, and Compounding Leverage.
    """

    @classmethod
    def calculate_economics(cls, case_data: Dict) -> Dict[str, Any]:
        """Models the financial physics of a criminal prosecution."""
        punishment_years = case_data.get("punishment_years", 3)
        offense_type = str(case_data.get("offense_type", "")).upper()
        
        # 1. Bail Bond Estimator
        base_surety = 10000
        if punishment_years > 7:
            base_surety = 50000
        elif punishment_years > 3:
            base_surety = 25000
            
        is_economic_offense = offense_type in ["420", "406", "409"] or case_data.get("pmla_case")
        if is_economic_offense:
            amount_involved = float(case_data.get("amount_involved") or 0)
            if amount_involved > 0:
                # Courts often demand 10-20% of the cheated amount as FDR/Surety
                base_surety = max(base_surety, amount_involved * 0.15)
                
        # 2. Trial Cost vs Plea Bargaining (Chapter XXIA)
        average_trial_duration_years = 5
        monthly_legal_cost = 5000
        total_trial_cost = average_trial_duration_years * 12 * monthly_legal_cost
        
        plea_eligible = punishment_years <= 7 and not case_data.get("pocso_case") and not case_data.get("crime_against_woman")
        
        # 3. Compounding Leverage (S.320 CrPC)
        is_compoundable = offense_type in ["323", "420", "406", "324", "379"]
        requires_court_permission = offense_type in ["420", "324", "379"]
        
        compounding_status = "NOT COMPOUNDABLE"
        if is_compoundable:
            if requires_court_permission:
                compounding_status = "COMPOUNDABLE (With Court Permission)"
            else:
                compounding_status = "COMPOUNDABLE (Without Court Permission)"

        return {
            "bail_economics": {
                "estimated_surety_amount": f"₹{base_surety:,.0f}",
                "note": "Economic offenses may require Fixed Deposit Receipts (FDR) equivalent to 10-20% of the disputed amount." if is_economic_offense else "Standard surety bonds required."
            },
            "trial_vs_plea": {
                "estimated_trial_duration": f"{average_trial_duration_years} Years",
                "estimated_trial_cost": f"₹{total_trial_cost:,.0f} (Opportunity & Legal Costs)",
                "plea_bargain_eligible": plea_eligible,
                "plea_bargain_note": "Eligible for Mutually Satisfactory Disposition under Chapter XXIA CrPC." if plea_eligible else "Not eligible for Plea Bargaining (Offense > 7 years or excludes women/children)."
            },
            "settlement_leverage": {
                "status": compounding_status,
                "strategic_advice": "Leverage cross-FIRs (if any) to force a compromise deed." if is_compoundable else "Cannot be settled out of court legally. Must pursue Trial or Quashing."
            }
        }
