import logging
from typing import Dict, List, Any
from sarfaesi_timeline_engine import SarfaesiTimelineEngine

logger = logging.getLogger(__name__)

class SarfaesiScoringEngine:
    """
    Law-Firm Grade Deterministic SARFAESI & DRT Scoring Engine.
    Evaluates statutory compliance under SARFAESI Act, 2002 & Security Interest Rules, 2002.
    """

    @classmethod
    def calculate_score(
        cls,
        case_data: Dict[str, Any],
        concepts: List[Dict[str, Any]] = None,
        contradictions: List[Dict[str, Any]] = None,
        limitation: Dict[str, Any] = None,
        extra: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if concepts is None:
            concepts = []
        if contradictions is None:
            contradictions = []
        if limitation is None:
            limitation = SarfaesiTimelineEngine.check_limitation(case_data)

        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        base_score = 65
        penalties = 0
        bonuses = 0
        trace = []
        causality_map = []
        fatal_defect = None
        remediation_roadmap = []

        trace.append(f"Initiating SARFAESI & DRT Statutory Audit (Mode: {'Borrower SA Defense' if is_borrower else 'Secured Creditor Enforcement'}).")

        # 1. CERSAI Mandatory Registration Check (Section 26D)
        cersai_reg = case_data.get("cersai_registered") or case_data.get("cersai_registration") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai_reg:
            if not is_borrower:
                penalties += 40
                fatal_defect = "NON_REGISTRATION_CERSAI: Security interest not registered on CERSAI portal (Section 26D statutory bar)."
                trace.append("CRITICAL PENALTY (-40): CERSAI registration missing. Section 26D bars secured creditors from taking enforcement action.")
                causality_map.append({
                    "fact": "Section 26D Non-Compliance",
                    "impact": -40,
                    "type": "negative",
                    "rationale": "Section 26D imposes absolute prohibition on SARFAESI enforcement without CERSAI registration."
                })
                remediation_roadmap.append({"action": "Register security interest immediately on CERSAI portal before taking Section 13(4) measures.", "priority": "HIGH"})
            else:
                bonuses += 35
                trace.append("BORROWER STAY GROUND (+35): Secured creditor failed to register security interest with CERSAI U/S 26D.")
        else:
            if not is_borrower:
                bonuses += 15
                trace.append("STATUTORY COMPLIANCE (+15): Security Interest duly registered on CERSAI portal U/S 26D.")

        # 2. Agricultural Land Exemption Check (Section 31(i))
        is_agri = case_data.get("is_agricultural_land") or str(case_data.get("agricultural_land", "")).lower() in ["yes", "true", "1"]
        if is_agri:
            if not is_borrower:
                penalties += 50
                fatal_defect = "AGRICULTURAL_LAND_EXEMPTION: Mortgaged property is agricultural land, completely exempt from SARFAESI U/S 31(i)."
                trace.append("FATAL DEFECT (-50): Property is agricultural land; SARFAESI Act is inapplicable U/S 31(i) (ITC v. Blue Coast Hotels).")
                causality_map.append({
                    "fact": "Section 31(i) Agricultural Land Exemption",
                    "impact": -50,
                    "type": "negative",
                    "rationale": "SARFAESI Act completely excludes agricultural land from security enforcement."
                })
                remediation_roadmap.append({"action": "Withdraw SARFAESI notices and file Civil Suit / DRT Original Application (OA under RDDBFI Act 1993).", "priority": "CRITICAL"})
            else:
                bonuses += 45
                trace.append("BORROWER WINNING GROUND (+45): Property is agricultural land; SARFAESI action is void ab initio U/S 31(i).")

        # 3. De Minimis Debt Limit Check (Section 31(g))
        outstanding = float(case_data.get("outstanding_amount") or case_data.get("debt_amount") or 0.0)
        sanction = float(case_data.get("sanction_amount") or 0.0)
        if outstanding > 0 and outstanding < 100000:
            if not is_borrower:
                penalties += 45
                fatal_defect = "SECTION_31_G_EXEMPTION: Outstanding debt is less than ₹100,000, exempt from SARFAESI U/S 31(g)."
                trace.append("FATAL DEFECT (-45): Outstanding debt is below ₹1 Lakh statutory minimum U/S 31(g).")
            else:
                bonuses += 40
                trace.append("BORROWER DEFENSE (+40): Debt is below ₹1 Lakh limit U/S 31(g).")
        elif sanction > 0 and outstanding > 0 and (outstanding / sanction) < 0.20:
            if not is_borrower:
                penalties += 40
                fatal_defect = "SECTION_31_G_LESS_THAN_20_PERCENT: Remaining debt is less than 20% of principal & interest, exempt U/S 31(g)."
                trace.append("FATAL DEFECT (-40): Less than 20% principal remaining unpaid U/S 31(g).")
            else:
                bonuses += 35
                trace.append("BORROWER DEFENSE (+35): Less than 20% principal remaining unpaid; SARFAESI barred U/S 31(g).")

        # 4. NCLT IBC Moratorium Conflict Check (Section 14 IBC)
        ibc_active = case_data.get("ibc_moratorium") or str(case_data.get("cirp_active", "")).lower() in ["yes", "true", "1"]
        if ibc_active:
            if not is_borrower:
                penalties += 50
                fatal_defect = "IBC_SECTION_14_MORATORIUM: Active NCLT CIRP Moratorium bars all SARFAESI enforcement measures."
                trace.append("FATAL BAR (-50): Active IBC Moratorium U/S 14 overrides SARFAESI (Indian Overseas Bank v. RCM Infrastructure).")
            else:
                bonuses += 45
                trace.append("BORROWER INJUNCTION GROUND (+45): Active IBC CIRP Moratorium statutorily stays all SARFAESI actions.")

        # 5. Section 13(3A) Objection Reply Procedure
        borrower_rep = case_data.get("borrower_representation_date") or case_data.get("borrower_objection")
        bank_reply = case_data.get("bank_reply_13_3a_date") or case_data.get("bank_reply_13_3a")
        poss_date = case_data.get("possession_13_4_date")
        if borrower_rep and not bank_reply and poss_date:
            if not is_borrower:
                penalties += 40
                fatal_defect = "MISSING_13_3A_REPLY: Took Section 13(4) possession without communicating reasoned decision on Section 13(3A) objection."
                trace.append("CRITICAL BREACH (-40): Possession taken without 13(3A) reply (Mardia Chemicals Ltd. v. UOI rule).")
            else:
                bonuses += 40
                trace.append("BORROWER WINNING GROUND (+40): Bank violated mandatory Section 13(3A) procedure before taking possession.")
        elif borrower_rep and bank_reply:
            from utils import days_between
            r_days = days_between(borrower_rep, bank_reply) if (isinstance(borrower_rep, str) and isinstance(bank_reply, str)) else None
            if r_days is not None and r_days > 15:
                if not is_borrower:
                    penalties += 30
                    trace.append(f"PROCEDURAL PENALTY (-30): Section 13(3A) reply delayed to {r_days} days (statutory limit is 15 days).")
                else:
                    bonuses += 30
                    trace.append(f"BORROWER DEFENSE (+30): Bank breached 15-day statutory cap for Section 13(3A) reply ({r_days} days elapsed).")

        # 6. Rule 8(2) Newspaper Publication Check (7-Day Limit)
        pub_done = case_data.get("newspaper_publication_done") or case_data.get("publication_in_newspapers") or str(case_data.get("newspaper_pub", "")).lower() in ["yes", "true", "1"]
        if poss_date and not pub_done:
            if not is_borrower:
                penalties += 25
                trace.append("PROCEDURAL PENALTY (-25): Possession notice not published in 2 leading newspapers within 7 days under Rule 8(2).")
                remediation_roadmap.append({"action": "Publish possession notice in 2 newspapers (1 vernacular) immediately as required under Rule 8(2).", "priority": "HIGH"})
            else:
                bonuses += 25
                trace.append("BORROWER DEFENSE (+25): Failure to comply with mandatory 7-day newspaper publication under Rule 8(2).")

        # 7. Rule 8(6) & 9(1) 30-Day Auction Notice Audit
        auction_notice = case_data.get("auction_notice_date")
        auction_date = case_data.get("auction_date")
        if auction_notice and auction_date:
            from utils import days_between
            a_days = days_between(auction_notice, auction_date)
            if a_days is not None and a_days < 30:
                if not is_borrower:
                    penalties += 45
                    fatal_defect = f"INVALID_AUCTION_NOTICE: Only {a_days} days notice provided before auction (mandatory 30 days under Rule 8(6)/9(1))."
                    trace.append(f"FATAL DEFECT (-45): Auction notice period is {a_days} days (Mathew Varghese v. M. Amritha Kumar requires 30 days).")
                else:
                    bonuses += 45
                    trace.append(f"BORROWER INJUNCTION GROUND (+45): Auction sale notice breaches mandatory 30-day period ({a_days} days provided).")

        # 8. Section 17 Limitation Check (45 Days for Borrower SA)
        if limitation.get("is_barred"):
            if is_borrower and "SA_LIMITATION_EXPIRED" in str(limitation.get("fatal_defect", "")):
                penalties += 45
                fatal_defect = limitation.get("fatal_defect")
                trace.append("FATAL DEFECT (-45): Borrower Securitisation Application filed beyond 45-day statutory limitation period U/S 17(1).")
            elif not is_borrower and "PREMATURE_POSSESSION" in str(limitation.get("fatal_defect", "")):
                penalties += 40
                fatal_defect = limitation.get("fatal_defect")
                trace.append("FATAL DEFECT (-40): Section 13(4) measure taken prematurely before 60-day demand notice window elapsed.")

        # 9. Section 18 DRAT Pre-Deposit Requirement Calculation
        pre_deposit_amount_standard = 0.50 * outstanding if outstanding else 0.0
        pre_deposit_amount_min = 0.25 * outstanding if outstanding else 0.0

        # Calculate Final Score
        final_score = base_score + bonuses - penalties
        final_score = max(10, min(95, final_score))

        verdict = "STRONG" if final_score >= 75 else ("MODERATE" if final_score >= 45 else "HIGH_RISK")
        if fatal_defect and not is_borrower:
            verdict = "HIGH STAY RISK / FATAL DEFECT"
        elif fatal_defect and is_borrower and "SA_LIMITATION_EXPIRED" in fatal_defect:
            verdict = "TIME_BARRED SA"
        elif not fatal_defect and is_borrower and final_score >= 70:
            verdict = "STRONG STAY PROBABILITY"

        return {
            "score": int(final_score),
            "final_score": float(final_score),
            "verdict": verdict,
            "fatal_defect": fatal_defect,
            "reasoning_trace": trace,
            "causality_map": causality_map,
            "drat_pre_deposit": {
                "standard_50_percent": pre_deposit_amount_standard,
                "minimum_25_percent": pre_deposit_amount_min,
                "statutory_authority": "Section 18(1) SARFAESI Act, 2002"
            },
            "breakdown": {
                "base_score": base_score,
                "bonuses": bonuses,
                "penalties": penalties,
                "final_score": final_score
            },
            "remediation_roadmap": remediation_roadmap or [
                {"action": "Verify CERSAI registration certificate and newspaper publication clippings.", "priority": "HIGH"}
            ]
        }

    @classmethod
    def calculate_score_with_trace(cls, case_data, concepts, contradictions, limitation, extra):
        return cls.calculate_score(case_data, concepts, contradictions, limitation, extra)

