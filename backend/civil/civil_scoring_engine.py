"""
JudiQ AI — Civil & Commercial Litigation Deterministic Scoring Engine
Calculates 5-Pillar Courtroom Survivability Score (0 to 100), statutory penalties,
bonuses, fatality decision rules, and causality tracing for CPC & Commercial suits.
"""

import logging
from typing import Dict, List, Any
from civil.cpc_statutory_rules import CPCStatutoryRules
from civil.injunction_evaluator import InjunctionEvaluator
from civil.specific_performance_engine import SpecificPerformanceEngine
from civil.order37_summary_suit_engine import Order37SummarySuitEngine
from civil.civil_defence_catalogue import CivilDefenceCatalogue

logger = logging.getLogger(__name__)

class CivilScoringEngine:
    """
    Law-Firm Grade Deterministic Scoring Engine for Indian Civil & Commercial litigation.
    """

    BASE_SCORE = 50.0

    @classmethod
    def calculate_score(
        cls,
        case_data: Dict[str, Any],
        concepts: List[Dict[str, Any]] = None,
        contradictions: List[Dict[str, Any]] = None,
        extra: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if concepts is None:
            concepts = []
        if contradictions is None:
            contradictions = []
        if extra is None:
            extra = {}

        posture = str(case_data.get("party_posture") or case_data.get("perspective") or "plaintiff").lower()
        is_defendant = any(k in posture for k in ["defendant", "respondent", "judgment debtor"])
        suit_type = str(case_data.get("suit_type") or case_data.get("case_type") or "Commercial Suit").lower()
        is_commercial = "commercial" in suit_type or bool(case_data.get("is_commercial"))

        score = cls.BASE_SCORE
        bonuses = 0
        penalties = 0
        trace = []
        causality_map = []
        fatal_defect = None
        remediation_roadmap = []

        trace.append(f"Initiating Civil & Commercial Statutory Audit (Track: {'Commercial Division' if is_commercial else 'Ordinary Civil'}, Posture: {'Defendant' if is_defendant else 'Plaintiff'}).")

        # ---------------------------------------------------------
        # PILLAR 1: STATUTORY LIMITATION & INCEPTION TIMELINE (25 Pts)
        # ---------------------------------------------------------
        coa_date = case_data.get("cause_of_action_date") or case_data.get("breach_date") or case_data.get("breach_or_default_date") or case_data.get("agreement_date")
        filing_date = case_data.get("filing_date") or case_data.get("date_of_complaint") or case_data.get("complaint_date")
        art_key = case_data.get("limitation_article") or "article_113"
        ack_date = case_data.get("written_acknowledgment_date")
        pay_date = case_data.get("last_payment_date")

        lim_res = CPCStatutoryRules.evaluate_limitation(coa_date, filing_date, art_key, ack_date, pay_date)
        if not lim_res["valid"]:
            if not is_defendant:
                penalties += 50
                fatal_defect = lim_res["defect"]
                trace.append(f"FATAL DEFECT (-50): {lim_res['defect']}")
                causality_map.append({
                    "fact": "Statutory Limitation Expired",
                    "impact": -50,
                    "type": "fatal",
                    "rationale": lim_res["authority"]
                })
                remediation_roadmap.append({"action": "Examine if Section 18 written balance confirmation or Section 14 exclusion of bona fide time applies.", "priority": "CRITICAL"})
            else:
                bonuses += 45
                trace.append("DEFENDANT THRESHOLD BAR (+45): Plaint is barred by limitation on its face under Order VII Rule 11(d) CPC.")
                causality_map.append({
                    "fact": "Limitation Bar Available",
                    "impact": 45,
                    "type": "positive",
                    "rationale": "Order VII Rule 11(d) CPC mandates dismissal at threshold."
                })
        else:
            if not is_defendant:
                bonuses += 15
                trace.append("TIMELY FILING (+15): Suit presented within statutory limitation window.")
                if lim_res.get("renewal_applied"):
                    bonuses += 10
                    trace.append(f"SECTION 18/19 RENEWAL (+10): {lim_res['renewal_applied']}")

        # ---------------------------------------------------------
        # PILLAR 2: COMMERCIAL COURTS ACT & SECTION 12A PIMS (20 Pts)
        # ---------------------------------------------------------
        if is_commercial:
            cca_res = CPCStatutoryRules.evaluate_commercial_courts_compliance(case_data, is_commercial=True)
            if not cca_res["valid"]:
                for d in cca_res["defects"]:
                    if "MANDATORY_PIMS_BREACH" in d:
                        if not is_defendant:
                            penalties += 40
                            if not fatal_defect:
                                fatal_defect = d
                            trace.append("FATAL DEFECT (-40): Section 12A PIMS omitted without urgent interim relief (Patil Automation).")
                            causality_map.append({
                                "fact": "Section 12A PIMS Omission",
                                "impact": -40,
                                "type": "fatal",
                                "rationale": "Patil Automation v. Rakheja Engineers (2022) 10 SCC 1 mandates rejection u/O VII R 11."
                            })
                            remediation_roadmap.append({"action": "File application for leave to seek urgent interim injunction or approach DLSA/SLSA for PIMS.", "priority": "CRITICAL"})
                        else:
                            bonuses += 40
                            trace.append("DEFENDANT THRESHOLD REJECTION (+40): Plaint vulnerable to Order VII Rule 11 rejection for Section 12A non-compliance.")
                    elif "STATEMENT_OF_TRUTH" in d:
                        if not is_defendant:
                            penalties += 15
                            trace.append("PROCEDURAL DEFECT (-15): Statement of Truth under Order VI Rule 15A CPC missing.")
                            remediation_roadmap.append({"action": "File verified Statement of Truth affidavit signed by authorized representative.", "priority": "HIGH"})
            else:
                if not is_defendant:
                    bonuses += 15
                    trace.append("COMMERCIAL COMPLIANCE (+15): Section 12A PIMS and Statement of Truth fully satisfied.")

        # Section 80 CPC Notice Check (Government Suits)
        if case_data.get("is_government_party") or "government" in str(case_data.get("defendant_type", "")).lower():
            s80_status = str(case_data.get("s80_cpc_govt_notice_served") or "").lower()
            if not any(k in s80_status for k in ["yes", "expired", "leave"]):
                if not is_defendant:
                    penalties += 35
                    if not fatal_defect:
                        fatal_defect = "SECTION_80_CPC_BAR: Mandatory 2-month prior statutory notice to Government not served."
                    trace.append("FATAL DEFECT (-35): Section 80 CPC notice omitted without seeking urgency leave u/s 80(2).")
                else:
                    bonuses += 30
                    trace.append("DEFENDANT STATUTORY BAR (+30): Suit against Government filed without Section 80 notice.")

        # ---------------------------------------------------------
        # PILLAR 3: EVIDENTIARY PROOF, STAMPING & REGISTRATION (20 Pts)
        # ---------------------------------------------------------
        stamping = str(case_data.get("agreement_registered_and_stamped") or case_data.get("stamping_status") or "").lower()
        if any(k in stamping for k in ["duly stamped", "registered", "duly stamped & registered"]):
            bonuses += 15
            trace.append("EVIDENTIARY RIGOR (+15): Agreement is duly stamped and registered under Registration Act, 1908.")
        elif any(k in stamping for k in ["insufficiently stamped", "unstamped"]):
            penalties += 20
            trace.append("STAMP ACT RISK (-20): Document is insufficiently stamped; subject to impounding & 10x penalty u/s 35 Stamp Act.")
            remediation_roadmap.append({"action": "Pay deficit stamp duty and penalty before entering document in evidence.", "priority": "MEDIUM"})
        elif any(k in stamping for k in ["unregistered"]):
            penalties += 25
            trace.append("REGISTRATION ACT BAR (-25): Document is compulsorily registrable u/s 17; inadmissible for substantive title u/s 49.")

        # Electronic Evidence Certificate
        if bool(case_data.get("electronic_evidence_65b_bsa") or case_data.get("s65b_certificate")):
            bonuses += 5
            trace.append("ELECTRONIC EVIDENCE (+5): Section 65B IEA / Section 63 BSA electronic certificate attached.")

        # ---------------------------------------------------------
        # PILLAR 4: INTERIM INJUNCTION & URGENT RELIEF (20 Pts)
        # ---------------------------------------------------------
        if bool(case_data.get("urgent_interim_relief_prayed") or case_data.get("order_39_injunction")):
            inj_res = InjunctionEvaluator.evaluate_order_39_injunction(case_data)
            if inj_res.get("fatal_bar"):
                if not is_defendant:
                    penalties += 35
                    if not fatal_defect:
                        fatal_defect = inj_res["fatal_bar"]
                    trace.append(f"STATUTORY INJUNCTION BAR (-35): {inj_res['fatal_bar']}")
            else:
                if not is_defendant:
                    if inj_res["golden_triad_satisfied"]:
                        bonuses += 20
                        trace.append(f"GOLDEN TRIAD SATISFIED (+20): Order XXXIX Injunction viability probability: {inj_res['injunction_granted_probability']}%.")
                    else:
                        trace.append(f"INTERIM RELIEF CAUTION: Injunction probability is {inj_res['injunction_granted_probability']}%.")

        # ---------------------------------------------------------
        # PILLAR 5: DOMAIN-SPECIFIC MERITS & ADVERSARIAL DEFENSES (15 Pts)
        # ---------------------------------------------------------
        # Specific Performance Sub-engine
        if "specific performance" in suit_type or case_data.get("primary_prayer") == "Specific Performance of Contract":
            sp_res = SpecificPerformanceEngine.evaluate_specific_performance_claim(case_data)
            if not sp_res["maintainable"]:
                if not is_defendant:
                    penalties += 45
                    if not fatal_defect:
                        fatal_defect = sp_res["fatal_defect"]
                    trace.append(f"SPECIFIC RELIEF FATAL (-45): {sp_res['fatal_defect']}")
                else:
                    bonuses += 35
                    trace.append("DEFENDANT STATUTORY DEFENSE (+35): Specific performance barred under Section 16(c) SRA.")
            else:
                if not is_defendant:
                    bonuses += 15
                    trace.append("SPECIFIC RELIEF SATISFIED (+15): Section 16(c) continuous readiness & willingness established.")

        # Order 37 Summary Suit Sub-engine
        if "order 37" in suit_type or "summary suit" in suit_type:
            o37_res = Order37SummarySuitEngine.evaluate_summary_suit(case_data)
            if o37_res.get("plaintiff_entitled_to_immediate_decree"):
                if not is_defendant:
                    bonuses += 25
                    trace.append("ORDER 37 DECREE (+25): Plaintiff entitled to judgment forthwith under Order XXXVII Rule 3(6) CPC.")
                else:
                    penalties += 40
                    trace.append("DEFENDANT VULNERABILITY (-40): Defense is sham/moonshine; high risk of summary decree.")

        # Adversarial Defenses
        defenses = CivilDefenceCatalogue.analyze_defenses(case_data)
        for defn in defenses:
            if defn["priority"] == "CRITICAL" and "section_8" in defn.get("statute", "").lower():
                if not is_defendant:
                    penalties += 30
                    trace.append("ARBITRATION BAR (-30): Mandatory Section 8 reference to arbitration applicable.")
                    remediation_roadmap.append({"action": "Invoke arbitration proceedings under Arbitration & Conciliation Act, 1996.", "priority": "HIGH"})
                else:
                    bonuses += 30
                    trace.append("DEFENDANT SECTION 8 BAR (+30): Valid arbitration agreement bars court adjudication.")
            elif defn["priority"] == "HIGH" and "order_2_rule_2" in defn.get("name", "").lower():
                if not is_defendant:
                    penalties += 35
                    trace.append("ORDER II RULE 2 BAR (-35): Relinquished claim from prior suit without leave.")
                else:
                    bonuses += 25
                    trace.append("DEFENDANT CLAIM SPLITTING BAR (+25): Order II Rule 2 bars subsequent suit.")
            elif defn["priority"] == "FATAL" and "section_11" in defn.get("name", "").lower():
                if not is_defendant:
                    penalties += 40
                    trace.append("RES JUDICATA BAR (-40): Directly and substantially adjudicated in former suit.")
                else:
                    bonuses += 35
                    trace.append("DEFENDANT RES JUDICATA BAR (+35): Section 11 CPC bars re-litigation.")

        # Compute Final Score
        final_score = max(0.0, min(100.0, score + bonuses - penalties))

        # Determine Verdict
        if fatal_defect or final_score < 40.0:
            verdict = "FATAL_PROCEDURAL_DEFECT"
            risk_level = "CRITICAL"
        elif final_score >= 75.0:
            verdict = "STRONG_SUIT_VIABILITY"
            risk_level = "LOW"
        elif final_score >= 60.0:
            verdict = "MODERATE_SUIT_VIABILITY"
            risk_level = "MEDIUM"
        else:
            verdict = "CONTESTED_EVIDENTIARY_RISK"
            risk_level = "HIGH"

        return {
            "score": round(final_score, 1),
            "verdict": verdict,
            "risk_level": risk_level,
            "fatal_defect": fatal_defect,
            "bonuses": bonuses,
            "penalties": penalties,
            "trace": trace,
            "causality_map": causality_map,
            "remediation_roadmap": remediation_roadmap,
            "active_defenses": defenses,
            "statutory_track": "Commercial Division (CCA 2015)" if is_commercial else "Ordinary Civil Court (CPC 1908)"
        }
