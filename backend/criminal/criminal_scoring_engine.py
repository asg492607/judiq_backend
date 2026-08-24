from typing import Dict, List, Any
import logging
import json
import os
from base_scoring_engine import BaseScoringEngine

logger = logging.getLogger(__name__)

def _is_true(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    if isinstance(val, str):
        val_lower = val.strip().lower()
        return val_lower in ("true", "yes", "1") or val_lower.startswith("yes") or "violation" in val_lower or "unlawful" in val_lower or "missing" in val_lower or "without" in val_lower
    return False

def _is_false(val: Any) -> bool:
    if isinstance(val, bool):
        return not val
    if isinstance(val, str):
        val_lower = val.strip().lower()
        return val_lower in ("false", "no", "0") or val_lower.startswith("no")
    return False

class CriminalScoringEngine(BaseScoringEngine):
    """
    Calculates conviction probability for prosecution and acquittal/discharge probability for defense,
    evaluating evidentiary weight, statutory vulnerabilities, timeline penalties, and contradiction impact.
    """

    @classmethod
    def calculate_score(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]], contradictions: List[Dict[str, Any]], limitation: Dict[str, Any] = None) -> Dict[str, Any]:
        if limitation is None:
            try:
                from criminal.criminal_timeline_engine import CriminalTimelineEngine
                limitation = CriminalTimelineEngine.check_criminal_limitation(case_data)
            except Exception:
                limitation = {}

        concept_names = {c.get("concept", "") for c in concepts} if isinstance(concepts, list) else set()
        trace = []
        causality_map = []
        kb_models = {}

        try:
            kb_path = os.path.join(os.path.dirname(__file__), 'criminal_knowledge_base.json')
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    kb_models = json.load(f).get("vulnerability_models", {})
        except Exception:
            kb_models = {}

        score = 65 # Base conviction probability for standard criminal trial
        trace.append("Base Conviction Probability: 65 (Standard Trial Baseline)")

        # 1. Lack of Sanction (S.197 CrPC / S.218 BNSS / S.17A PC Act)
        is_public_servant = _is_true(case_data.get("is_public_servant"))
        sanction_obtained = _is_true(case_data.get("sanction_obtained"))
        if "CRPC_197" in concept_names or (is_public_servant and not sanction_obtained):
            score -= 60
            trace.append("FATAL: Cognizance barred under S.197 CrPC / S.218 BNSS (No Sanction).")
            causality_map.append({"fact": "No S.197/S.218 Sanction", "impact": -60, "type": "negative", "rationale": "Absolute bar on cognizance against public servant without statutory sanction."})

        # 2. Limitation Bar (S.468 CrPC / S.514 BNSS)
        if "CRPC_468" in concept_names or _is_true(case_data.get("limitation_barred")) or limitation.get("is_barred"):
            score -= 50
            trace.append("FATAL: Cognizance barred under S.468 CrPC / S.514 BNSS (Limitation Act).")
            causality_map.append({"fact": "Limitation Bar", "impact": -50, "type": "negative", "rationale": "Offence is time-barred."})

        # 3. NDPS S.50 Mandatory Procedural Violation
        offense_str = str(case_data.get("offense_type", "")).upper()
        if _is_true(case_data.get("ndps_case")) or "NDPS" in offense_str:
            if "NDPS_S50" in concept_names or _is_true(case_data.get("s50_violation")) or _is_true(case_data.get("s50_ndps_violation")):
                score -= 45
                trace.append("FATAL: S.50 NDPS Mandatory Search Violation.")
                causality_map.append({"fact": "S.50 NDPS Violation", "impact": -45, "type": "negative", "rationale": "Mandatory search procedure violated; recovery becomes inadmissible."})

        # 4. Unexplained FIR Delay
        if _is_true(case_data.get("fir_delay_unexplained")) or "fir_delay" in concept_names:
            score -= 25
            trace.append("-25 EVIDENTIARY: Unexplained FIR delay.")
            causality_map.append({"fact": "FIR Delay", "impact": -25, "type": "negative", "rationale": "Suggests deliberation, consultation, and afterthought."})

        # 5. Ocular vs Medical Contradiction
        if _is_true(case_data.get("medical_contradicts_ocular")) or "MEDICAL_OCULAR" in concept_names:
            score -= 30
            trace.append("-30 EVIDENTIARY: Eyewitness testimony contradicts medical evidence.")
            causality_map.append({"fact": "Medical Contradiction", "impact": -30, "type": "negative", "rationale": "Independent medical evidence casts massive doubt on eyewitnesses."})

        # 6. S.41A Notice Violation (Arnesh Kumar)
        if _is_true(case_data.get("no_s41a_notice")):
            score -= 20
            trace.append("-20 PROCEDURAL: Violation of S.41A CrPC / S.35 BNSS Mandatory Notice.")
            causality_map.append({"fact": "S.41A Notice Violation", "impact": -20, "type": "negative", "rationale": "Arrest without recording specific necessity is unlawful under Arnesh Kumar."})

        # 7. S.65B IEA / S.63 BSA Missing Certificate
        has_elec = _is_true(case_data.get("electronic_evidence"))
        has_cert = _is_true(case_data.get("s65b_certificate"))
        if has_elec and not has_cert:
            score -= 30
            trace.append("-30 EVIDENTIARY: Electronic evidence without S.65B/S.63 certificate.")
            causality_map.append({"fact": "Uncertified Electronic Evidence", "impact": -30, "type": "negative", "rationale": "Secondary electronic evidence is strictly inadmissible per Arjun Panditrao."})

        # 8. Contradictions Impact
        for cont in contradictions:
            penalty = cont.get("penalty", -15)
            score += penalty
            trace.append(f"{penalty} Contradiction: {cont.get('issue', '')} ({cont.get('severity', '')})")
            causality_map.append({
                "fact": cont.get("issue", ""),
                "impact": penalty,
                "type": "negative",
                "rationale": cont.get("detail", "")
            })

        # 9. KB Vulnerability Matching
        matched_kb = False
        if offense_str and kb_models:
            for kb_key, kb_data in kb_models.items():
                if any(k in offense_str for k in kb_key.split('_')) or kb_key in concept_names:
                    matched_kb = True
                    trigger_risk = kb_data.get("probability_collapse", 0.5)
                    if trigger_risk > 0.6:
                        severity = kb_data.get("severity", "HIGH")
                        penalties = {"FATAL": -30, "CRITICAL": -20, "HIGH": -15, "MEDIUM": -10}
                        penalty_val = penalties.get(severity, -15)
                        score += penalty_val
                        trace.append(f"{penalty_val} KB VULNERABILITY: {kb_data.get('name', kb_key)} risk triggered.")
                        causality_map.append({
                            "fact": f"Systemic Risk: {kb_data.get('name', kb_key)}",
                            "impact": penalty_val,
                            "type": "negative",
                            "rationale": kb_data.get("risk", "High structural vulnerability.")
                        })

        if not matched_kb and any(x in offense_str for x in ["IPC", "BNS", "CRPC", "BNSS"]):
            penalty_val = -10
            score += penalty_val
            trace.append(f"{penalty_val} KB VULNERABILITY: Unmapped Offence ({offense_str}) Generic Procedural Risk.")
            causality_map.append({
                "fact": f"Procedural Risk: {offense_str}",
                "impact": penalty_val,
                "type": "negative",
                "rationale": "Generic procedural or evidentiary vulnerabilities apply under standard criminal framework."
            })

        # 10. Final Score Calculation & Verdict Determination
        prosecution_conviction_prob = max(0, min(99, score))
        role = case_data.get("client_role", "Accused")

        if role == "Accused":
            final_client_score = 100 - prosecution_conviction_prob
            verdict = "HIGH CHANCE OF ACQUITTAL/DISCHARGE" if final_client_score > 70 else ("TRIAL READY - RISKY" if final_client_score > 40 else "HIGH CONVICTION RISK")
        else:
            final_client_score = prosecution_conviction_prob
            verdict = "STRONG PROSECUTION" if final_client_score > 70 else ("WEAK PROSECUTION" if final_client_score > 40 else "FATAL DEFECTS - WILL FAIL")

        return {
            "score": int(final_client_score),
            "final_score": int(final_client_score),
            "prosecution_conviction_probability": int(prosecution_conviction_prob),
            "accused_acquittal_probability": 100 - int(prosecution_conviction_prob),
            "verdict": verdict,
            "causality_map": causality_map,
            "reasoning_trace": trace,
            "score_breakdown": trace
        }
