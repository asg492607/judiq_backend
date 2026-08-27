"""
JudiQ OTS (One-Time Settlement) vs Litigation NPV Decision Engine
Calculates Net Present Value (NPV), time decay, legal fees, court costs,
and RBI NPA provisioning relief to give financial recovery officers a definitive Litigate vs Settle recommendation.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class OTSCalculationRequest(BaseModel):
    default_principal: float
    total_dues_with_interest: float
    ots_offer_amount: float
    anticipated_litigation_months: int = 24  # 12, 24, 36
    estimated_legal_and_court_costs: float = 150000.0
    estimated_recovery_probability: float = 0.70  # 70%
    bank_discount_rate_annual: float = 0.09  # 9% cost of funds
    npa_age_years: float = 1.5  # for RBI provisioning tier


class OTSCalculationResponse(BaseModel):
    success: bool
    default_principal: float
    total_dues_with_interest: float
    ots_offer_amount: float
    ots_haircut_percentage: float
    ots_net_immediate_cash: float
    litigation_expected_gross_recovery: float
    litigation_npv_discounted: float
    litigation_net_realizable_value: float
    rbi_provisioning_release_amount: float
    financial_delta_ots_vs_litigation: float
    recommendation_verdict: str  # "ACCEPT_OTS", "COUNTER_OFFER", "REJECT_AND_LITIGATE"
    recommendation_summary: str
    decision_drivers: List[str]
    time_decay_breakdown: List[Dict[str, Any]]


def calculate_ots_vs_litigation(req: OTSCalculationRequest) -> OTSCalculationResponse:
    principal = float(req.default_principal)
    total_dues = float(req.total_dues_with_interest)
    ots_offer = float(req.ots_offer_amount)
    months = int(req.anticipated_litigation_months)
    legal_costs = float(req.estimated_legal_and_court_costs)
    prob = float(req.estimated_recovery_probability)
    discount_annual = float(req.bank_discount_rate_annual)

    # 1. Haircut computation
    haircut_pct = max(0.0, ((total_dues - ots_offer) / total_dues) * 100) if total_dues > 0 else 0.0
    ots_immediate_cash = ots_offer

    # 2. Litigation Expected Value & Time Decay
    # Discount factor = 1 / (1 + r)^(t/12)
    years = months / 12.0
    discount_factor = 1.0 / ((1.0 + discount_annual) ** years)
    
    expected_gross = total_dues * prob
    npv_gross = expected_gross * discount_factor
    litigation_net = max(0.0, npv_gross - legal_costs)

    # 3. RBI NPA Provisioning Relief
    # Sub-standard (15%), Doubtful-1 (25%), Doubtful-2 (40%), Doubtful-3 (100%), Loss (100%)
    if req.npa_age_years < 1.0:
        prov_rate = 0.15
    elif req.npa_age_years < 2.0:
        prov_rate = 0.25
    elif req.npa_age_years < 4.0:
        prov_rate = 0.40
    else:
        prov_rate = 1.00

    provisioning_release = principal * prov_rate

    # 4. Financial Delta (OTS Cash - Litigation Net)
    delta = ots_immediate_cash - litigation_net

    # 5. Recommendation Logic
    drivers = []
    if delta > 0:
        if haircut_pct <= 35:
            verdict = "ACCEPT_OTS"
            rec_summary = (
                f"ACCEPT OTS: Immediate cash realization of ₹{ots_offer:,.2f} delivers ₹{delta:,.2f} "
                f"higher Net Present Value than {months} months of contested litigation (NPV: ₹{litigation_net:,.2f}). "
                f"Releases ₹{provisioning_release:,.2f} in RBI capital provisioning immediately."
            )
        else:
            verdict = "COUNTER_OFFER"
            rec_summary = (
                f"COUNTER-OFFER RECOMMENDED: While NPV favors immediate settlement, the current haircut of "
                f"{haircut_pct:.1f}% exceeds benchmark 35% threshold. Recommend counter-offering at ₹{litigation_net * 1.15:,.2f}."
            )
    else:
        verdict = "REJECT_AND_LITIGATE"
        rec_summary = (
            f"REJECT OTS & PROCEED WITH LITIGATION: Anticipated litigation recovery (NPV: ₹{litigation_net:,.2f}) "
            f"exceeds the low OTS offer of ₹{ots_offer:,.2f} by ₹{abs(delta):,.2f}. Proceed with concurrent S.138 + SARFAESI."
        )

    drivers.append(f"OTS Haircut: {haircut_pct:.1f}% on aggregate dues of ₹{total_dues:,.2f}")
    drivers.append(f"Litigation Timeline Decay: {months} months at {discount_annual*100:.1f}% annual discount rate reduces nominal value by {(1-discount_factor)*100:.1f}%")
    drivers.append(f"Expected Legal & Court Costs: ₹{legal_costs:,.2f}")
    drivers.append(f"RBI Provisioning Write-Back Benefit: ₹{provisioning_release:,.2f} added directly to bank Tier-1 capital")

    # Time decay breakdown (12, 24, 36 months)
    time_decay = []
    for m in [12, 24, 36]:
        y = m / 12.0
        df = 1.0 / ((1.0 + discount_annual) ** y)
        net_val = (total_dues * prob * df) - (legal_costs * (1.0 + (m-12)/24))
        time_decay.append({
            "duration_months": m,
            "discount_factor": round(df, 4),
            "expected_net_npv": round(net_val, 2),
            "ots_surplus_deficit": round(ots_offer - net_val, 2)
        })

    return OTSCalculationResponse(
        success=True,
        default_principal=principal,
        total_dues_with_interest=total_dues,
        ots_offer_amount=ots_offer,
        ots_haircut_percentage=round(haircut_pct, 2),
        ots_net_immediate_cash=round(ots_immediate_cash, 2),
        litigation_expected_gross_recovery=round(expected_gross, 2),
        litigation_npv_discounted=round(npv_gross, 2),
        litigation_net_realizable_value=round(litigation_net, 2),
        rbi_provisioning_release_amount=round(provisioning_release, 2),
        financial_delta_ots_vs_litigation=round(delta, 2),
        recommendation_verdict=verdict,
        recommendation_summary=rec_summary,
        decision_drivers=drivers,
        time_decay_breakdown=time_decay
    )
