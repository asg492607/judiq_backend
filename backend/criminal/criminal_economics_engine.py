from typing import Dict, Any

class CriminalEconomicsEngine:
    """
    Evaluates financial dynamics, bail bond requirements, litigation expenditure,
    compounding viability (S.320 CrPC / S.359 BNSS), plea bargaining eligibility
    (Chapter XXI-A CrPC / Chapter XXII BNSS), and victim compensation exposure.
    """

    @classmethod
    def calculate_economics(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        offense_type = str(case_data.get("offense_type", "General")).upper()
        severity = case_data.get("severity_score", 50)
        punishment = int(case_data.get("max_punishment_years") or case_data.get("punishment_years") or 3)
        amount = case_data.get("amount_involved") or case_data.get("financial_amount") or case_data.get("amount") or 0

        # 1. Surety & Bail Bond Valuation
        base_bond = 15000
        if punishment >= 10 or any(x in offense_type for x in ["302", "376", "NDPS", "103", "64", "PMLA"]):
            base_bond = 100000
        elif punishment >= 7 or any(x in offense_type for x in ["420", "406", "307", "318", "316", "467"]):
            base_bond = 50000
        elif punishment >= 3:
            base_bond = 25000

        estimated_litigation_cost = base_bond * 2.5

        # 2. Compounding Viability (S.320 CrPC / S.359 BNSS)
        compoundable_without_permission = any(x in offense_type for x in ["323", "341", "426", "447", "504", "506", "115(2)", "329", "351(2)"])
        compoundable_with_permission = any(x in offense_type for x in ["420", "406", "324", "325", "384", "417", "318(4)", "316(2)", "117", "308"])
        
        if compoundable_without_permission:
            compounding_status = "Compoundable without Court Permission (S.320(1) CrPC / S.359(1) BNSS)"
            compounding_viable = True
        elif compoundable_with_permission:
            compounding_status = "Compoundable with Permission of Court (S.320(2) CrPC / S.359(2) BNSS)"
            compounding_viable = True
        else:
            compounding_status = "Non-Compoundable Offense (Settlement requires S.482 CrPC / S.528 BNSS HC Quashing per Gian Singh v. State of Punjab)"
            compounding_viable = False

        # 3. Plea Bargaining Eligibility (S.265A CrPC / S.289 BNSS)
        # Excluded if punishment > 7 years, or affects women/children (S.376, 498A, POCSO), or socio-economic offense
        is_barred_plea = punishment > 7 or any(x in offense_type for x in ["302", "304B", "376", "498A", "POCSO", "NDPS", "PMLA", "103", "80", "64", "85"])
        plea_bargain_eligible = not is_barred_plea

        # 4. Victim Compensation Exposure (S.357 / S.357A CrPC <-> S.395 / S.396 BNSS)
        victim_compensation_likely = any(x in offense_type for x in ["302", "304", "307", "376", "POCSO", "326", "HIT & RUN", "103", "109", "64", "118"])

        return {
            "bail_economics": {
                "estimated_surety_bond": base_bond,
                "cash_bail_viability": "Standard (Solvent Surety)" if base_bond <= 50000 else "Substantial Property Surety Required",
                "property_surety_required": base_bond >= 100000,
                "passport_deposit_risk": base_bond >= 50000
            },
            "litigation_exposure": {
                "projected_trial_cost": estimated_litigation_cost,
                "financial_dispute_amount": amount,
                "victim_compensation_exposure": "High" if victim_compensation_likely else "Minimal",
                "economic_settlement_recommended": any(x in offense_type for x in ["420", "406", "318", "316"]) and amount > 0
            },
            "compounding_and_settlement": {
                "is_compoundable": compounding_viable,
                "statutory_mechanism": compounding_status,
                "supreme_court_benchmark": "Gian Singh v. State of Punjab (2012) 10 SCC 303 (Inherent powers to quash non-compoundable private disputes upon compromise)"
            },
            "trial_vs_plea": {
                "plea_bargain_eligible": plea_bargain_eligible,
                "plea_bargain_provision": "Chapter XXI-A CrPC (S.265A-265L) / Chapter XXII BNSS (S.289-300)",
                "recommended_path": "Plea Bargain Application" if plea_bargain_eligible and severity > 80 else ("Compromise Quashing u/s 482" if compounding_viable else "Contest on Merits")
            }
        }
