import logging
from typing import Dict, List, Any
from sarfaesi_timeline_engine import SarfaesiTimelineEngine

logger = logging.getLogger(__name__)

class SarfaesiScoringEngine:
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

        base_score = 60
        penalties = 0
        bonuses = 0
        trace = []
        causality_map = []
        fatal_defect = None

        trace.append(f"Starting SARFAESI Engine evaluation (Perspective: {'Borrower SA' if is_borrower else 'Secured Creditor/Bank'}).")

        # 1. CERSAI Mandatory Registration Check (Section 26D)
        cersai_reg = case_data.get("cersai_registered") or case_data.get("cersai_registration") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai_reg:
            if not is_borrower:
                penalties += 45
                fatal_defect = "NON_REGISTRATION_CERSAI: Security interest not registered on CERSAI portal (Section 26D statutory bar on enforcement)."
                trace.append("FATAL PENALTY (-45): Security Interest not registered on CERSAI portal (Section 26D).")
                causality_map.append({
                    "fact": "Section 26D Non-Compliance",
                    "impact": -45,
                    "type": "negative",
                    "rationale": "Section 26D imposes absolute bar on SARFAESI enforcement without CERSAI registration."
                })
            else:
                bonuses += 35
                trace.append("BORROWER DEFENSE (+35): Secured creditor failed to register security interest with CERSAI U/S 26D.")
        else:
            if not is_borrower:
                bonuses += 15
                trace.append("PILLAR (+15): Security Interest duly registered on CERSAI portal U/S 26D.")

        # 2. Agricultural Land Exemption Check (Section 31(i))
        is_agri = case_data.get("is_agricultural_land") or str(case_data.get("agricultural_land", "")).lower() in ["yes", "true", "1"]
        if is_agri:
            if not is_borrower:
                penalties += 50
                fatal_defect = "AGRICULTURAL_LAND_EXEMPTION: Property is agricultural land, exempt from SARFAESI U/S 31(i)."
                trace.append("FATAL PENALTY (-50): Security interest created over agricultural land (Section 31(i) exemption).")
                causality_map.append({
                    "fact": "Section 31(i) Agricultural Land",
                    "impact": -50,
                    "type": "negative",
                    "rationale": "SARFAESI Act completely inapplicable to agricultural property (ITC v. Blue Coast Hotels)."
                })
            else:
                bonuses += 45
                trace.append("BORROWER DEFENSE (+45): Property is agricultural land; SARFAESI action is void ab initio U/S 31(i).")

        # 3. Section 13(3A) Objection Reply Compliance
        borrower_rep = case_data.get("borrower_representation_date")
        bank_reply = case_data.get("bank_reply_13_3a_date")
        if borrower_rep and not bank_reply and case_data.get("possession_13_4_date"):
            if not is_borrower:
                penalties += 40
                fatal_defect = "MISSING_13_3A_REPLY: Bank took Section 13(4) possession without serving reasoned reply to Section 13(3A) objection."
                trace.append("FATAL PENALTY (-40): Failure to communicate decision on Section 13(3A) representation (Mardia Chemicals rule).")
            else:
                bonuses += 40
                trace.append("BORROWER DEFENSE (+40): Bank violated mandatory Section 13(3A) procedure by taking possession without replying.")
        elif borrower_rep and bank_reply:
            from utils import days_between
            r_days = days_between(borrower_rep, bank_reply)
            if r_days is not None and r_days > 15:
                if not is_borrower:
                    penalties += 35
                    fatal_defect = f"LATE_13_3A_REPLY: Reasoned reply served in {r_days} days (exceeding mandatory 15-day limit)."
                    trace.append(f"PENALTY (-35): Section 13(3A) reply delayed to {r_days} days.")
                else:
                    bonuses += 30
                    trace.append(f"BORROWER DEFENSE (+30): Bank delayed Section 13(3A) reply to {r_days} days.")

        # 4. Section 17 Limitation Check (45 Days for Borrower SA)
        if limitation.get("is_barred"):
            if is_borrower and "SA_LIMITATION_EXPIRED" in limitation.get("fatal_defect", ""):
                penalties += 45
                fatal_defect = limitation.get("fatal_defect")
                trace.append(f"FATAL PENALTY (-45): Borrower Securitisation Application filed beyond 45-day statutory limitation period.")
            elif not is_borrower and "PREMATURE_POSSESSION" in limitation.get("fatal_defect", ""):
                penalties += 40
                fatal_defect = limitation.get("fatal_defect")
                trace.append(f"FATAL PENALTY (-40): Section 13(4) measure taken prematurely before 60-day demand window elapsed.")

        # 5. Calculate Final Score
        if not is_borrower:
            final_score = base_score + bonuses - penalties
        else:
            final_score = base_score + bonuses - penalties

        final_score = max(10, min(95, final_score))

        verdict = "STRONG" if final_score >= 75 else ("MODERATE" if final_score >= 45 else "HIGH_RISK")
        if fatal_defect and not is_borrower:
            verdict = "DO NOT FILE / FATAL DEFECT"
        elif fatal_defect and is_borrower and "SA_LIMITATION_EXPIRED" in fatal_defect:
            verdict = "TIME_BARRED"

        return {
            "score": int(final_score),
            "final_score": float(final_score),
            "verdict": verdict,
            "fatal_defect": fatal_defect,
            "reasoning_trace": trace,
            "causality_map": causality_map,
            "breakdown": {
                "base_score": base_score,
                "bonuses": bonuses,
                "penalties": penalties,
                "final_score": final_score
            },
            "remediation_roadmap": [
                {
                    "action": "Curate CERSAI registration record" if not cersai_reg else "Verify possession publication in 2 newspapers",
                    "priority": "HIGH"
                }
            ]
        }

    @classmethod
    def calculate_score_with_trace(cls, case_data, concepts, contradictions, limitation, extra):
        return cls.calculate_score(case_data, concepts, contradictions, limitation, extra)
