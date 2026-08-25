from typing import Dict, List, Any
import logging
import json
import os
from base_scoring_engine import BaseScoringEngine
from criminal.criminal_utils import _is_true, _is_false

logger = logging.getLogger(__name__)

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

        score = 60 # Base conviction probability for standard contested criminal trial
        trace.append("Base Conviction Probability: 60 (Standard Trial Baseline)")

        # --- Positive Prosecution Corroboration Factors ---
        if _is_true(case_data.get("has_eyewitness")):
            score += 15
            trace.append("+15 EVIDENTIARY: Direct ocular eyewitness testimony available.")
            causality_map.append({"fact": "Eyewitness Testimony", "impact": 15, "type": "positive", "rationale": "Direct ocular evidence establishes foundational prosecution narrative."})

        if _is_true(case_data.get("weapon_recovered")):
            score += 15
            trace.append("+15 FORENSIC: Weapon of offence recovered under Section 27 IEA / Section 23 BSA.")
            causality_map.append({"fact": "Weapon Recovery", "impact": 15, "type": "positive", "rationale": "Direct nexus between accused and crime instrument."})

        if _is_true(case_data.get("dna_match")) or _is_true(case_data.get("medical_corroboration")):
            score += 20
            trace.append("+20 SCIENTIFIC: Forensic FSL DNA match / corroborative medical injury report.")
            causality_map.append({"fact": "Forensic / DNA Match", "impact": 20, "type": "positive", "rationale": "Objective scientific evidence corroborated by expert medical findings."})

        if _is_true(case_data.get("motive_established")):
            score += 10
            trace.append("+10 MOTIVE: Clear prior enmity or financial motive established.")
            causality_map.append({"fact": "Motive Established", "impact": 10, "type": "positive", "rationale": "Prior motive substantiates intent and mens rea."})

        if _is_true(case_data.get("fake_identity_used")) or _is_true(case_data.get("forged_seals_recovered")):
            score += 20
            trace.append("+20 MENS REA: Recovery of fake identity documents / fabricated seals.")
            causality_map.append({"fact": "Fabricated Identity/Seals", "impact": 20, "type": "positive", "rationale": "Indicates premeditated deceptive intent at inception."})

        # --- Fact Deduplication Set ---
        applied_facts = set()

        # --- Fatal Jurisdictional & Statutory Bars ---
        # 1. Juvenile Justice Act Check (Age < 18 at Incident)
        age_at_incident = case_data.get("age_at_incident")
        is_juvenile = _is_true(case_data.get("is_juvenile"))
        if age_at_incident is not None:
            try:
                if int(age_at_incident) < 18:
                    is_juvenile = True
            except (ValueError, TypeError):
                pass
        if is_juvenile:
            score -= 75
            applied_facts.add("juvenile_bar")
            trace.append("FATAL: Accused is a Juvenile (JJ Act 2015). Regular Court has zero jurisdiction.")
            causality_map.append({"fact": "Juvenile Justice Act Bar", "impact": -75, "type": "negative", "rationale": "Regular criminal court has no jurisdiction to try or convict a juvenile."})

        # 2. Lack of Sanction (S.197 CrPC / S.218 BNSS / S.17A PC Act)
        is_public_servant = _is_true(case_data.get("is_public_servant"))
        sanction_obtained = _is_true(case_data.get("sanction_obtained"))
        if "CRPC_197" in concept_names or (is_public_servant and not sanction_obtained):
            score -= 60
            applied_facts.add("sanction_bar")
            trace.append("FATAL: Cognizance barred under S.197 CrPC / S.218 BNSS (No Sanction).")
            causality_map.append({"fact": "No S.197/S.218 Sanction", "impact": -60, "type": "negative", "rationale": "Absolute bar on cognizance against public servant without statutory sanction."})

        # 3. Limitation Bar (S.468 CrPC / S.514 BNSS)
        lim_years_passed = case_data.get("limitation_years_passed")
        punishment_val = case_data.get("max_punishment_years") or case_data.get("punishment_years")
        is_lim_barred = _is_true(case_data.get("limitation_barred")) or limitation.get("is_barred")
        if lim_years_passed is not None and punishment_val is not None:
            try:
                p_years = float(punishment_val)
                p_passed = float(lim_years_passed)
                if (p_years <= 1 and p_passed > 1) or (p_years <= 3 and p_passed > 3):
                    is_lim_barred = True
            except (ValueError, TypeError):
                pass
        if "CRPC_468" in concept_names or is_lim_barred:
            score -= 50
            applied_facts.add("limitation_bar")
            trace.append("FATAL: Cognizance barred under S.468 CrPC / S.514 BNSS (Limitation Act).")
            causality_map.append({"fact": "Limitation Bar", "impact": -50, "type": "negative", "rationale": "Offence is time-barred."})

        # 4. S.167(2) Default Bail Ripe (Statutory outer threshold exceeded without chargesheet)
        days_in_custody = int(case_data.get("days_in_custody") or 0)
        chargesheet_filed = _is_true(case_data.get("chargesheet_filed")) or bool(case_data.get("chargesheet_date"))
        if days_in_custody > 0 and not chargesheet_filed:
            try:
                p_years = int(punishment_val or 7)
                statutory_threshold = 90 if p_years >= 10 or any(x in str(case_data.get("offense_type", "")).upper() for x in ["302", "304", "376", "395", "409", "103", "64", "310", "316", "MURDER", "RAPE", "NDPS"]) else 60
                if days_in_custody >= statutory_threshold:
                    score -= 30
                    applied_facts.add("default_bail_ripe")
                    trace.append(f"STATUTORY RIGHT: S.167(2) Default Bail accrued ({days_in_custody} days custody >= {statutory_threshold} days threshold).")
                    causality_map.append({"fact": "S.167(2) Default Bail Accrued", "impact": -30, "type": "negative", "rationale": "Investigation not completed within statutory window; indefeasible right to bail accrued."})
            except Exception:
                pass

        # 5. NDPS S.50 Mandatory Procedural Violation
        offense_str = str(case_data.get("offense_type", "")).upper()
        if _is_true(case_data.get("ndps_case")) or "NDPS" in offense_str:
            if "NDPS_S50" in concept_names or _is_true(case_data.get("s50_violation")) or _is_true(case_data.get("s50_ndps_violation")):
                score -= 45
                applied_facts.add("ndps_s50_violation")
                trace.append("FATAL: S.50 NDPS Mandatory Search Violation.")
                causality_map.append({"fact": "S.50 NDPS Violation", "impact": -45, "type": "negative", "rationale": "Mandatory search procedure violated; recovery becomes inadmissible."})

        # 6. Unexplained FIR Delay
        if _is_true(case_data.get("fir_delay_unexplained")) or "fir_delay" in concept_names:
            score -= 25
            applied_facts.add("fir_delay")
            trace.append("-25 EVIDENTIARY: Unexplained FIR delay.")
            causality_map.append({"fact": "FIR Delay", "impact": -25, "type": "negative", "rationale": "Suggests deliberation, consultation, and afterthought."})

        # 7. Ocular vs Medical Contradiction
        if _is_true(case_data.get("medical_contradicts_ocular")) or "MEDICAL_OCULAR" in concept_names:
            score -= 30
            applied_facts.add("medical_ocular")
            trace.append("-30 EVIDENTIARY: Eyewitness testimony contradicts medical evidence.")
            causality_map.append({"fact": "Medical Contradiction", "impact": -30, "type": "negative", "rationale": "Independent medical evidence casts massive doubt on eyewitnesses."})

        # 8. S.41A Notice Violation (Arnesh Kumar)
        if _is_true(case_data.get("no_s41a_notice")):
            score -= 20
            applied_facts.add("s41a_notice")
            trace.append("-20 PROCEDURAL: Violation of S.41A CrPC / S.35 BNSS Mandatory Notice.")
            causality_map.append({"fact": "S.41A Notice Violation", "impact": -20, "type": "negative", "rationale": "Arrest without recording specific necessity is unlawful under Arnesh Kumar."})

        # 9. S.65B IEA / S.63 BSA Missing Certificate
        has_elec = _is_true(case_data.get("electronic_evidence"))
        has_cert = _is_true(case_data.get("s65b_certificate"))
        if has_elec and not has_cert:
            score -= 30
            applied_facts.add("missing_65b")
            trace.append("-30 EVIDENTIARY: Electronic evidence without S.65B/S.63 certificate.")
            causality_map.append({"fact": "Uncertified Electronic Evidence", "impact": -30, "type": "negative", "rationale": "Secondary electronic evidence is strictly inadmissible per Arjun Panditrao."})

        # 10. S.27 IEA / S.23 BSA Inadmissible Open Place / Joint Recovery
        if _is_true(case_data.get("open_place_recovery")) or _is_true(case_data.get("joint_disclosure_recovery")):
            score -= 20
            applied_facts.add("inadmissible_s27_recovery")
            trace.append("-20 EVIDENTIARY: Recovery memo invalid under S.27 IEA / S.23 BSA (Open place / Joint disclosure).")
            causality_map.append({"fact": "Inadmissible S.27 Recovery", "impact": -20, "type": "negative", "rationale": "Open place or joint statement discovery is strictly inadmissible per Gian Chand & Pulukuri Kottaya."})

        # 11. Matrimonial In-Laws Living Separately (Kahkashan Kausar)
        if ("498A" in offense_str or "85" in offense_str) and _is_true(case_data.get("relative_impleaded")) and _is_true(case_data.get("separate_residence")):
            score -= 20
            applied_facts.add("kahkashan_kausar")
            trace.append("-20 QUASHING: Extended family members living separately impleaded without specific overt acts.")
            causality_map.append({"fact": "Kahkashan Kausar Quashing Ground", "impact": -20, "type": "negative", "rationale": "Omnibus allegations against in-laws living separately are quashed per Kahkashan Kausar (2022)."})

        # 10. Contradictions Impact (Only add if not already directly penalized)
        for cont in contradictions:
            issue_title = cont.get("issue", "")
            if "FIR Delay" in issue_title and "fir_delay" in applied_facts:
                continue
            if "S.65B" in issue_title and "missing_65b" in applied_facts:
                continue
            if "Medical vs Ocular" in issue_title and "medical_ocular" in applied_facts:
                continue

            penalty = cont.get("penalty", -15)
            score += penalty
            trace.append(f"{penalty} Contradiction: {issue_title} ({cont.get('severity', '')})")
            causality_map.append({
                "fact": issue_title,
                "impact": penalty,
                "type": "negative",
                "rationale": cont.get("detail", "")
            })

        # 11. KB Vulnerability Matching (Factually Grounded)
        is_minor_victim = False
        v_age = case_data.get("victim_age")
        if v_age is not None:
            try:
                is_minor_victim = int(v_age) < 18
            except (ValueError, TypeError):
                pass
        if "POCSO" in offense_str or _is_true(case_data.get("pocso_case")):
            is_minor_victim = True

        # Factually verify if specific defense vulnerability model applies
        def _kb_model_factually_applicable(key: str) -> bool:
            if key == "IPC_420":
                if _is_true(case_data.get("fake_identity_used")) or _is_true(case_data.get("forged_seals_recovered")):
                    return False
                return bool(case_data.get("contract_exists") or case_data.get("commercial_dispute") or case_data.get("partial_performance_done") or "civil_dispute" in concept_names)
            if key == "IPC_406":
                return bool(case_data.get("commercial_dispute") or case_data.get("partnership_dispute") or case_data.get("accounts_settlement"))
            if key == "IPC_467_468":
                return bool(case_data.get("original_document_missing") or case_data.get("fsl_inconclusive") or case_data.get("signature_disputed") or (case_data.get("contract_exists") and case_data.get("commercial_dispute")))
            if key == "IPC_498A":
                return bool(case_data.get("relative_impleaded") or case_data.get("separate_residence") or case_data.get("omnibus_allegations"))
            if key == "IPC_302_307":
                return bool(case_data.get("sudden_quarrel") or case_data.get("premeditation_absent") or case_data.get("grave_provocation"))
            if key == "IPC_376":
                return not is_minor_victim and bool(case_data.get("consensual_relationship") or case_data.get("courtship_failed") or "consensual_courtship" in concept_names)
            if key == "NDPS_OFFENSES":
                return bool(case_data.get("s50_violation") or case_data.get("s52a_violation") or "NDPS_S50" in concept_names)
            if key == "CORRUPTION_PMLA":
                return bool(case_data.get("is_public_servant") or case_data.get("pmla_trial_delay") or case_data.get("predicate_acquittal"))
            return False

        matched_kb = False
        if offense_str and kb_models:
            for kb_key, kb_data in kb_models.items():
                if any(k in offense_str for k in kb_key.split('_')) or kb_key in concept_names:
                    if _kb_model_factually_applicable(kb_key):
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
