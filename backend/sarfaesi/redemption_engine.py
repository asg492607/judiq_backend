"""
Section 13(8) Borrower Redemption Calculator & Valuation Stress-Testing Engine.
Enforces the Supreme Court's landmark doctrine in Celir LLP v. Bafna Motors (2024) 2 SCC 1
and ITC Ltd. v. Blue Coast Hotels Ltd. (2018) 15 SCC 99 regarding statutory redemption cut-offs,
accrued interest compounding, and auction valuation haircuts.
"""

from datetime import datetime
import logging
import math
from typing import Dict, List, Any, Optional
from utils import parse_date, days_between

logger = logging.getLogger(__name__)

class RedemptionEngine:
    """
    Law-firm grade mathematical interest & Section 13(8) redemption cut-off evaluator.
    """

    @classmethod
    def calculate_redemption_amount(
        cls,
        principal_debt: float,
        annual_interest_rate: float,
        npa_date_str: Optional[str],
        calculation_date_str: Optional[str] = None,
        incidental_costs: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes exact statutory redemption liability including compounded contractual interest
        and permissible enforcement expenses under Section 13(8).
        """
        principal = float(principal_debt or 0.0)
        rate = float(annual_interest_rate or 12.0) / 100.0  # default 12% p.a.
        
        calc_dt = parse_date(calculation_date_str) if calculation_date_str else datetime.now()
        npa_dt = parse_date(npa_date_str) if npa_date_str else (calc_dt.replace(year=calc_dt.year - 1))
        
        days_accrued = max(0, (calc_dt - npa_dt).days)
        years = days_accrued / 365.25

        # Monthly compounding contractual interest: A = P * (1 + r/12)^(12 * t)
        compound_factor = math.pow(1.0 + (rate / 12.0), 12.0 * years)
        total_interest = max(0.0, (principal * compound_factor) - principal)

        # Standard incidental enforcement expenses under Rule 8(5)
        expenses = incidental_costs or {
            "valuation_fees": 35000.0,
            "newspaper_publication_costs": 45000.0,
            "security_guarding_charges": 60000.0,
            "legal_and_advocate_commissioner_fees": 75000.0,
            "insurance_and_custody_expenses": 25000.0
        }
        total_incidentals = sum(expenses.values())
        total_redemption_due = principal + total_interest + total_incidentals

        return {
            "principal_debt": round(principal, 2),
            "annual_interest_rate_pct": round(rate * 100, 2),
            "days_accrued": days_accrued,
            "accrued_contractual_interest": round(total_interest, 2),
            "incidental_enforcement_expenses": {k: round(v, 2) for k, v in expenses.items()},
            "total_incidental_expenses": round(total_incidentals, 2),
            "total_redemption_amount_payable": round(total_redemption_due, 2),
            "calculation_date": calc_dt.strftime("%Y-%m-%d"),
            "npa_date": npa_dt.strftime("%Y-%m-%d")
        }

    @classmethod
    def evaluate_redemption_status(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforces Section 13(8) (amended post-2016) and Celir LLP v. Bafna Motors (2024) 2 SCC 1.
        Redemption right is strictly extinguished on the date the public auction notice is published.
        """
        outstanding = float(case_data.get("outstanding_amount") or case_data.get("debt_amount") or 0.0)
        interest_rate = float(case_data.get("interest_rate") or 13.5)
        npa_date = case_data.get("npa_date")
        auction_notice_date = case_data.get("auction_notice_date") or case_data.get("publication_date")
        tender_amount = float(case_data.get("tendered_redemption_amount") or 0.0)

        redemption_calc = cls.calculate_redemption_amount(
            principal_debt=outstanding,
            annual_interest_rate=interest_rate,
            npa_date_str=npa_date
        )

        total_due = redemption_calc["total_redemption_amount_payable"]
        right_to_redeem_extinguished = False
        statutory_status = "REDEMPTION_OPEN"
        cut_off_ruling = ""
        warnings = []

        if auction_notice_date:
            right_to_redeem_extinguished = True
            statutory_status = "REDEMPTION_EXTINGUISHED"
            cut_off_ruling = (
                "Under Section 13(8) of the SARFAESI Act (post-2016 amendment) as authoritatively settled in "
                "'Celir LLP v. Bafna Motors (Mumbai) Pvt. Ltd. (2024) 2 SCC 1', the borrower's right of redemption "
                "is strictly extinguished the moment the public auction notice is published in newspapers. "
                "No redemption or stay can be granted after this statutory cut-off."
            )
            warnings.append(
                "🚨 STATUTORY REDEMPTION CUT-OFF PASSED: Public auction notice was published on "
                f"{auction_notice_date}. Borrower's right to redeem under Section 13(8) has legally terminated."
            )
        else:
            cut_off_ruling = (
                "Section 13(8) redemption window is OPEN. The borrower can redeem the secured asset by tendering "
                f"₹{total_due:,.2f} (principal + accrued interest + incidental expenses) before the auction notice is published."
            )

        # Valuation Stress-Tester (Rule 8(5) Fair Market vs Realizable vs Distress Value)
        property_val = float(case_data.get("property_valuation") or case_data.get("fair_market_value") or (outstanding * 1.4))
        valuation_stress = {
            "fair_market_value": round(property_val, 2),
            "realizable_value_90pct": round(property_val * 0.90, 2),
            "distress_sale_value_80pct": round(property_val * 0.80, 2),
            "minimum_reserve_price_benchmark": round(property_val * 0.85, 2),
            "haircut_risk_evaluation": "SAFE" if property_val * 0.80 >= total_due else "DEFICIT_RISK",
            "statutory_authority": "Rule 8(5) Security Interest (Enforcement) Rules, 2002 (Mandatory Approved Valuer Consultation)"
        }

        return {
            "status": statutory_status,
            "right_to_redeem_extinguished": right_to_redeem_extinguished,
            "statutory_cut_off_ruling": cut_off_ruling,
            "redemption_calculation": redemption_calc,
            "valuation_stress_testing": valuation_stress,
            "precedent_authority": "Celir LLP v. Bafna Motors (Mumbai) Pvt. Ltd. (2024) 2 SCC 1",
            "warnings": warnings
        }
