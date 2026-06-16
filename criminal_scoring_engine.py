from typing import Dict, List, Any
import logging
from base_scoring_engine import BaseScoringEngine

logger = logging.getLogger(__name__)

class CriminalScoringEngine(BaseScoringEngine):
    """
    Realistic Scoring Engine for Criminal Matters.
    Calculates numerical 'Survivability' and 'Acquittal Probability' scores
    based on harsh realities of procedural bars (S.197, Limitation) and evidence.
    """

    @classmethod
    def calculate_score(cls, case_data: Dict, concepts: List[Dict], contradictions: List[Dict], limitation: Dict = None) -> Dict:
        if limitation is None:
            try:
                from timeline_engine import TimelineEngine
                limitation = TimelineEngine.check_criminal_limitation(case_data)
            except Exception:
                limitation = {}

        concept_names = {c["concept"] for c in concepts}
        trace = []
        causality_map = []
        
        # Load Criminal Knowledge Base for deep structural analysis
        kb_models = {}
        try:
            import json, os
            kb_path = os.path.join(os.path.dirname(__file__), 'criminal_knowledge_base.json')
            with open(kb_path, 'r', encoding='utf-8') as f:
                kb_models = json.load(f).get("vulnerability_models", {})
        except Exception as e:
            pass
        
        
        # Base Score for Prosecution (100 = Guaranteed Conviction, 0 = Quashed/Discharged)
        score = 65
        trace.append("Base Conviction Probability: 65 (Standard Trial Baseline)")

        # 1. FATAL STATUTORY BARS
        if "CRPC_197" in concept_names or case_data.get("public_servant_no_sanction"):
            score -= 60
            trace.append("FATAL: Cognizance barred under S.197 CrPC (No Sanction).")
            causality_map.append({"fact": "No S.197 Sanction", "impact": -60, "rationale": "Absolute bar on cognizance against public servant without sanction."})

        if "CRPC_468" in concept_names or case_data.get("limitation_barred"):
            score -= 50
            trace.append("FATAL: Cognizance barred under S.468 CrPC (Limitation Act).")
            causality_map.append({"fact": "Limitation Bar", "impact": -50, "rationale": "Offense is time-barred."})

        if case_data.get("ndps_case") and "NDPS_S50" in concept_names:
            score -= 45
            trace.append("FATAL: S.50 NDPS Procedural Violation.")
            causality_map.append({"fact": "S.50 NDPS Violation", "impact": -45, "rationale": "Mandatory search procedure violated; recovery becomes inadmissible."})

        # 2. SEVERE EVIDENTIARY DEFECTS
        if case_data.get("fir_delay_unexplained"):
            score -= 25
            trace.append("-25 EVIDENTIARY: Unexplained FIR delay.")
            causality_map.append({"fact": "FIR Delay", "impact": -25, "rationale": "Suggests afterthought and fabrication."})

        if case_data.get("medical_contradicts_ocular"):
            score -= 30
            trace.append("-30 EVIDENTIARY: Ocular evidence contradicts medical evidence.")
            causality_map.append({"fact": "Medical Contradiction", "impact": -30, "rationale": "Independent medical evidence casts massive doubt on eyewitnesses."})

        if "electronic_evidence" in case_data:
            case_data.setdefault("has_electronic_evidence", True)

        timeline_penalties = cls.apply_timeline_penalties(case_data, concepts, limitation)
        score += timeline_penalties["score_delta"]
        trace.extend(timeline_penalties["trace"])
        causality_map.extend(timeline_penalties["causality_map"])

        bsa_result = cls.apply_s63_4_penalty(case_data)
        score += bsa_result["score_delta"]
        trace.extend(bsa_result["trace"])
        causality_map.extend(bsa_result["causality_map"])

        # 3. CONTRADICTIONS
        for cont in contradictions:
            penalty = cont.get("penalty", 0)
            score += penalty
            trace.append(f"{penalty} Contradiction: {cont['issue']} ({cont['severity']})")
            causality_map.append({
                "fact": cont["issue"],
                "impact": penalty,
                "type": "negative",
                "rationale": cont["detail"]
            })

        # 3.5. KNOWLEDGE BASE PENALTIES (Deep Wiring)
        offense_type = str(case_data.get("offense_type", "")).upper()
        matched_kb = False
        if offense_type and kb_models:
            for kb_key, kb_data in kb_models.items():
                if offense_type in kb_key or kb_key in concept_names:
                    matched_kb = True
                    # Determine if the vulnerability is actually triggered by the facts
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
        
        # Generic Fallback for 100+ unmapped sections
        if not matched_kb and ("IPC" in offense_type or "BNS" in offense_type or "CRPC" in offense_type):
            penalty_val = -10
            score += penalty_val
            trace.append(f"{penalty_val} KB VULNERABILITY: Unmapped Offence ({offense_type}) Generic Procedural Risk.")
            causality_map.append({
                "fact": f"Procedural Risk: {offense_type}",
                "impact": penalty_val,
                "type": "negative",
                "rationale": "Generic procedural or evidentiary vulnerabilities apply under standard criminal framework."
            })

        # 4. EVIDENCE RELIABILITY MATRIX
        evidence_reliability = cls.calculate_evidence_reliability(case_data)
        for name, data in evidence_reliability.items():
            if data.get("score", 1.0) < 0.5:
                penalty = -15
                score += penalty
                trace.append(f"{penalty} EVIDENTIARY: Low reliability on critical evidence ({name}).")
                causality_map.append({"fact": f"Low Reliability: {name}", "impact": penalty, "type": "negative", "rationale": data.get("reason", "Evidence is vulnerable to challenge.")})

        # Cap score
        final_score = max(0, min(99, score))

        # Role inversion: If client is Accused, the score represents their chance of ACQUITTAL
        role = case_data.get("client_role", "Accused")
        if role == "Accused":
            final_client_score = 100 - final_score
            verdict = "HIGH CHANCE OF ACQUITTAL/DISCHARGE" if final_client_score > 70 else ("TRIAL READY - RISKY" if final_client_score > 40 else "HIGH CONVICTION RISK")
        else:
            final_client_score = final_score
            verdict = "STRONG PROSECUTION" if final_client_score > 70 else ("WEAK PROSECUTION" if final_client_score > 40 else "FATAL DEFECTS - WILL FAIL")

        return {
            "score": int(final_client_score),
            "prosecution_conviction_probability": int(final_score),
            "accused_acquittal_probability": 100 - int(final_score),
            "verdict": verdict,
            "causality_map": causality_map,
            "evidence_reliability": evidence_reliability,
            "reasoning_trace": trace,
            "score_breakdown": trace,
        }
