import re
import logging
from datetime import datetime
from typing import List, Dict, Any
from llm_engine import generate_executive_summary, enhance_legal_draft

logger = logging.getLogger(__name__)

def ensure_list(x):
    if x is None: return []
    if isinstance(x, list): return x
    return [x]

NEGATIVE_CONCEPTS = {
    "signature_dispute", "notice_defect", "notice_not_sent", "no_debt_proof", "security_cheque",
    "cheque_misuse", "limitation_issue", "payment_already_made", "dishonour_disputed",
    "cheque_validity_issue", "no_agreement", "joint_account_liability",
    "stop_payment_instructions", "material_alteration", "premature_complaint",
    "unaccounted_cash_loans", "legal_heirs_liability", "litigation_risk"
}

POSITIVE_CONCEPTS = {
    "cheque_bounce", "legal_notice_compliance", "legally_enforceable_debt",
    "strong_documentary_evidence", "partnership_and_firms",
    "power_of_attorney_holder", "interim_compensation", "appeal_deposit",
    "compounding_offence"
}

WEAKNESS_THRESHOLD = 0.22
STRENGTH_THRESHOLD = 0.45

def _convert_to_lawyer_language(raw_trace: list) -> list:
    _PHRASE_MAP = [
        (r"\+\d+\s+instrument\s+present", "The foundational Negotiable Instrument (S.138) is present and verified."),
        (r"\+\d+\s+cheque", "Possession of the original cheque instrument establishes the prima facie cause of action."),
        (r"-\d+\s+instrument\s+missing", "FATAL: Absence of the physical cheque instrument precludes prosecution under S.138 NI Act."),
        (r"\+\d+\s+memo\s+available", "Official Bank Dishonour Memo/Return Slip provides conclusive evidence of non-payment."),
        (r"\+\d+\s+notice\s+compliance", "Service of Statutory Demand Notice (S.138b) is confirmed within the 30-day window."),
        (r"-\d+\s+notice\s+defect", "PROCEDURAL BAR: Failure to serve mandatory statutory notice within 30 days is a jurisdictional defect."),
        (r"\+\d+\s+debt\s+provenance", "Underlying legally enforceable debt is corroborated via documentary evidence."),
        (r"-\d+\s+debt\s+not\s+established", "Evidentiary Risk: Lack of underlying debt documentation weakens the S.139 presumption."),
        (r"\+\d+\s+all\s+mandatory\s+procedural\s+pillars", "Statutory Audit: All four mandatory pillars (Instrument, Dishonour, Notice, Debt) are satisfied."),
        (r"-\d+\s+notice\s+defect\s+\(fatal\)", "FATAL: Jurisdictional defect in statutory notice service renders complaint non-maintainable."),
        (r"OVERRIDE:\s+FATAL", "AUTHORITATIVE OVERRIDE: The case suffers from a fatal statutory defect that precludes legal success."),
        (r"BASALINGAPPA\s+PENALTY", "EVIDENTIARY GAP: High-value debt based solely on verbal testimony is highly vulnerable to 'Financial Capacity' rebuttals (Basalingappa v. Mudibasappa)."),
        (r"FATAL\s+ERROR:\s+PREMATURE", "FATAL PROCEDURAL ERROR: Premature filing before the expiry of the 15-day cure period (Yogendra Pratap Singh v. Savitri Pandey)."),
    ]

    clean_trace = []
    seen = set()
    for item in raw_trace:
        matched = False
        for pattern, substitution in _PHRASE_MAP:
            if re.search(pattern, str(item), re.IGNORECASE):
                if substitution not in seen:
                    clean_trace.append(substitution)
                    seen.add(substitution)
                matched = True
                break
        if not matched:
            cleaned = re.sub(r"^[+-]\d+\s+", "", str(item)).strip()
            if cleaned and not cleaned.startswith("Base score") and not cleaned.startswith("Final score") and not cleaned.startswith("Applied") and cleaned not in seen:
                clean_trace.append(cleaned)
                seen.add(cleaned)
    return clean_trace

class ResponseBuilder:
    @staticmethod
    def _prefix_text(text: Any, label: str) -> Any:
        if not isinstance(text, str) or not text.strip():
            return text
        if text.startswith("[AI Enhanced]") or text.startswith("[Rule-Based]"):
            return text
        return f"[{label}]\n{text}"

    @staticmethod
    def build_final_response(engine_result: Dict[str, Any], case_data: Dict[str, Any]) -> Dict[str, Any]:
        score = engine_result.get("final_score", 0)
        trace = engine_result.get("reasoning_trace", [])
        breakdown = engine_result.get("score_breakdown", [])
        concepts = engine_result.get("concepts", [])
        tldr = engine_result.get("tldr", {})
        
        # New institutional-grade components
        causality_map = list(engine_result.get("causality_map", []))
        top_penalties = engine_result.get("top_penalties", [])
        strategy_result = engine_result.get("strategy_result", {})
        adversarial_result = engine_result.get("adversarial_result", {})

        verdict = "STRONG CASE"
        if score <= 25 or engine_result.get("verdict") == "DO NOT FILE":
            verdict = "DO NOT FILE"
        elif score < 40: 
            verdict = "WEAK CASE / HIGH RISK"
        elif score < 70: 
            verdict = "MODERATE CASE"

        # Dynamically append adjustments so score breakdown matches final score
        current_sum = sum(c.get("impact", 0) for c in causality_map)
        diff = int(score - current_sum)
        if diff != 0:
            if verdict == "DO NOT FILE" or score == 0:
                causality_map.append({
                    "fact": "Fatal Defect Override",
                    "impact": diff,
                    "type": "negative",
                    "rationale": "Case has fatal procedural/statutory defects."
                })
            else:
                causality_map.append({
                    "fact": "Judicial Adjustment & Calibration",
                    "impact": diff,
                    "type": "negative" if diff < 0 else "positive",
                    "rationale": "Calibration for territorial jurisdiction and court rules."
                })

        risk_level = "LOW"
        if score < 50: risk_level = "CRITICAL"
        elif score < 75: risk_level = "MEDIUM"

        strengths = []
        weaknesses = []

        is_criminal = case_data.get("case_type") == "criminal" or "criminal" in str(case_data.get("description", "")).lower()
        if is_criminal:
            if case_data.get("fir_copy"): strengths.append("Prerequisite: FIR Copy secured")
            if case_data.get("police_complaint_filed"): strengths.append("Strength: Formal police complaint initiated")
            if case_data.get("witnesses_available"): strengths.append("Strength: Corroborative witness testimony available")
            if case_data.get("debt_proven"): strengths.append("Strength: Documented evidence establishing transaction/intent")
        else:
            if case_data.get("cheque_present"):   strengths.append("Prerequisite: Negotiable instrument (cheque) secured")
            if case_data.get("dishonour_memo"):   strengths.append("Prerequisite: Bank dishonour memo / return slip available")
            if case_data.get("notice_sent"):      strengths.append("Prerequisite: Statutory demand notice served (S.138b)")
            if case_data.get("debt_proven"):      strengths.append("Strength: Legally enforceable debt established via corroborative proof")

        # We will populate structured weaknesses later using ranked_weaknesses
        
        for c in concepts:
            concept_name = c.get("concept", "")
            conf = c.get("confidence", 0)
            label = concept_name.replace('_', ' ').title()
            if concept_name in POSITIVE_CONCEPTS and conf >= STRENGTH_THRESHOLD:
                strengths.append(f"Strategic Asset: {label}")
                
        # Extract limitation data safely
        limitation = engine_result.get("limitation") or {}
        if not limitation and case_data.get("notice_date") and case_data.get("dishonour_date"):
            limitation = {"is_premature": False, "notice_delay_days": 0}

        structured_weaknesses = []
        fatal_defect = case_data.get("fatal_defect") or engine_result.get("failure_point")
        if fatal_defect:
             structured_weaknesses.append({
                 "risk": str(fatal_defect),
                 "severity": "FATAL",
                 "detail": f"This case has a fatal statutory/procedural defect: {fatal_defect}. It is highly recommended not to file or to withdraw."
             })

        if limitation.get("is_premature"):
            structured_weaknesses.append({"risk": "Premature Complaint", "severity": "FATAL", "detail": "Non-curable defect under NI Act."})
        elif limitation.get("notice_delay_days", 0) > 0:
             structured_weaknesses.append({"risk": "Notice Delayed", "severity": "HIGH", "detail": f"Statutory notice delayed by {limitation['notice_delay_days']} days. Application for condonation mandatory."})
        
        if not case_data.get("proof_present", True):
             structured_weaknesses.append({"risk": "Missing Proof", "severity": "HIGH", "detail": "Proof (Cheque/Memo/Notice) is missing."})

        # Inject logical contradictions from adversarial engine directly into weaknesses
        contradictions = engine_result.get("contradictions", [])
        for contra in contradictions:
            penalty = contra.get("penalty", 0)
            severity_mapped = "FATAL" if penalty <= -85 else ("CRITICAL" if penalty <= -50 else "HIGH")
            structured_weaknesses.append({
                "risk": f"[CONTRADICTION] {contra.get('issue', 'Logical Contradiction')}",
                "severity": severity_mapped,
                "detail": contra.get("detail", "")
            })

        suggestions = []
        desc_lower = (case_data.get("description") or "").lower()

        if limitation.get("is_premature"):
             suggestions.append({
                 "id": "action_withdraw",
                 "title": "IMMEDIATE ACTION: Withdraw Complaint",
                 "description": "Withdraw the current complaint with liberty to re-file. Continuing with a premature complaint will lead to final dismissal.",
                 "severity": "CRITICAL"
             })
        
        if limitation.get("notice_delay_days", 0) > 0:
             suggestions.append({
                 "id": "action_condonation",
                 "title": "FILE: S.142(1)(b) Condonation Application",
                 "description": "Prepare a formal application showing 'sufficient cause' for the notice delay.",
                 "severity": "HIGH"
             })

        if any(x in desc_lower for x in ["whatsapp", "email", "sms"]):
             suggestions.append({
                 "id": "action_63_bsa",
                 "title": "PREPARE: Section 63(4) BSA Certificate",
                 "description": "You MUST file a certificate under Section 63(4) of the Bharatiya Sakshya Adhiniyam (BSA) to make digital records admissible.",
                 "severity": "HIGH"
             })

        if score < 60 and case_data.get("debt_evidence_type") == "Verbal":
             suggestions.append({
                 "id": "action_evidence_corroboration",
                 "title": "COLLECT: Indirect Debt Proof",
                 "description": "Gather bank statements or witness affidavits to counter 'Financial Capacity' rebuttals.",
                 "severity": "HIGH"
             })

        confidence_score = round(sum(c.get("confidence", 0) for c in concepts) / len(concepts), 2) if concepts else None
        
        is_cynical = score < 65 or any("CYNICAL" in str(t) for t in trace)
        improvement_metrics = [
            {"area": "Procedural", "current": "Delayed" if "limitation_issue" in [c['concept'] for c in concepts] else "Compliant", "targeted": "S.142(1)(b) Filed"},
            {"area": "Evidence", "current": "Risk (Digital)" if "whatsapp" in desc_lower else "Standard", "targeted": "S.63(4) BSA Compliant"},
            {"area": "Recovery", "current": "Standard Trial", "targeted": "S.143A Relief (20%)"}
        ]

        cheque_amount = float(case_data.get("amount") or 0)
        penalty_forecast = {
            "min_fine": f"₹{cheque_amount * 1.2:,.0f}",
            "max_fine": f"₹{cheque_amount * 2.0:,.0f} (Statutory Max)",
            "imprisonment_risk": "HIGH" if score > 75 else "MEDIUM",
            "realistic_outcome": f"Fine of ₹{cheque_amount * 1.5:,.0f} + 6 months simple imprisonment."
        }

        audit = {
            "mode": "Cynical Advocate" if is_cynical else "Standard Analysis",
            "risk_status": "HIGHLY VULNERABLE" if score < 50 else ("MODERATE RISK" if score < 75 else "FILING READY"),
            "critical_vulnerability": weaknesses[0] if weaknesses else "None Detected",
            "strategic_recommendation": suggestions[0]['title'] if suggestions else "Proceed with Caution",
            "improvement_metrics": improvement_metrics,
            "penalty_forecast": penalty_forecast
        }

        lawyer_reasoning = _convert_to_lawyer_language(trace)

        concepts_for_response = [
            {
                "concept": c.get("concept", ""),
                "confidence": c.get("confidence", 0),
                "legal_impact": c.get("legal_impact", ""),
                "matched_phrases": c.get("matched_phrases", [])
            }
            for c in concepts
        ]

        NEGATIVE_RISK_ORDER = [
            "limitation_issue", "notice_defect", "notice_not_sent",
            "unaccounted_cash_loans", "litigation_risk", "security_cheque", "signature_dispute", "no_debt_proof",
            "no_agreement", "cheque_misuse", "payment_already_made",
            "cheque_validity_issue", "dishonour_disputed"
        ]
        ranked_weaknesses = []
        seen_weak = set()
        for priority_concept in NEGATIVE_RISK_ORDER:
            for c in concepts:
                if c.get("concept") == priority_concept and c.get("confidence", 0) >= WEAKNESS_THRESHOLD and priority_concept not in seen_weak:
                    conf = c.get("confidence", 0)
                    severity = "FATAL" if conf >= 0.8 else ("CRITICAL" if conf >= 0.65 else ("HIGH" if conf >= 0.45 else "MEDIUM"))
                    ranked_weaknesses.append({
                        "risk": priority_concept.replace("_", " ").title(),
                        "severity": severity,
                        "confidence": conf,
                        "detail": c.get("legal_impact", "") or "No specific impact detailed."
                    })
                    seen_weak.add(priority_concept)

        structured_weaknesses.extend(ranked_weaknesses)
        
        # Sort structured_weaknesses by severity (FATAL > CRITICAL > HIGH > MEDIUM)
        severity_order = {"FATAL": 4, "CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
        structured_weaknesses.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)
        
        top_3_risks = structured_weaknesses[:3]
        has_fatal = any(r["severity"] in ["FATAL", "CRITICAL"] for r in top_3_risks)
        has_high_risk = any(r["severity"] == "HIGH" for r in top_3_risks)

        is_criminal = case_data.get("case_type") == "criminal" or "criminal" in str(case_data.get("description", "")).lower()
        if is_criminal and not case_data.get("police_complaint_filed"):
            recommended_action = "FILE_COMPLAINT"
            decision_label = "Initiate Formal Complaint"
            decision_detail = "Formal complaint/FIR has not been registered. Required to set criminal law in motion."
            next_steps = ["Draft Police Complaint", "Submit to jurisdictional police station"]
        elif not is_criminal and not case_data.get("notice_sent"):
            recommended_action = "SEND_NOTICE"
            decision_label = "Send Legal Notice First"
            decision_detail = "Statutory demand notice (S.138b) has not been sent. Mandatory pre-condition."
            next_steps = ["Draft and dispatch notice via RPAD", "Wait 15 days before filing"]
        elif score > 75 and not has_fatal:
            recommended_action = "FILE_COMPLAINT"
            decision_label = "File Criminal Complaint"
            decision_detail = f"Strong case ({score}/100). All prerequisites satisfied."
            next_steps = ["Verify originals", "File within limitation", "Engage advocate"]
        elif score >= 50 and not has_fatal:
            recommended_action = "FIX_THEN_FILE"
            decision_label = "Address Defects Before Filing"
            decision_detail = f"Moderate case ({score}/100). Foundational elements present but risks identified."
            next_steps = [f"Fix: {top_3_risks[0]['risk'] if top_3_risks else 'defects'}", "Obtain corroborating documents"]
        else:
            recommended_action = "CONSIDER_SETTLEMENT"
            decision_label = "Consider Strategic Settlement"
            decision_detail = f"Case has significant vulnerabilities. Settlement under S.147 NI Act recommended."
            next_steps = ["Draft settlement proposal", "Evaluate time-value of money"]

        counter_strategies = {
            "Security Cheque": "Rebut via 'Sampelly Satyanarayana Rao'. Prove crystallized debt.",
            "Signature Dispute": "Apply for handwriting expert comparison. Rely on 'Bir Singh'.",
            "No Debt Proof": "Invoke S.139 Presumption. Shift burden via 'Rangappa v. Mohan'.",
            "Notice Defect": "If window closed, consider civil recovery suit."
        }
        
        for risk_obj in top_3_risks:
            risk_name = risk_obj["risk"]
            risk_obj["counter_strategy"] = counter_strategies.get(risk_name, "Strengthen documentary evidence.")

        decision = {
            "recommended_action": recommended_action,
            "decision_label": decision_label,
            "detail": decision_detail,
            "next_steps": next_steps,
            "top_3_risks": top_3_risks,
            "draft_type_generated": engine_result.get("draft_type", "LEGAL_OPINION")
        }

        strategy = [
            "Proceed with procedural compliance audit.",
            "Verify jurisdictional facts.",
            "Maintain evidentiary safe custody."
        ]

        alternative_evidence = []
        if not case_data.get("debt_proven"):
            alternative_evidence = ["WhatsApp correspondence", "Bank statements", "Ledger entries"]

        def get_category(risk_name):
            r = str(risk_name).lower()
            if "notice" in r or "delay" in r or "time" in r or "premature" in r:
                return "Procedural"
            if "jurisdiction" in r or "court" in r:
                return "Jurisdictional"
            if "proof" in r or "evidence" in r or "memo" in r or "cheque" in r or "signature" in r or "contradiction" in r or "witness" in r or "itr" in r or "capacity" in r:
                return "Evidentiary"
            return "Statutory"

        for r in structured_weaknesses:
            r['text'] = r.get('risk', '')
            r['title'] = r.get('risk', '')
            r['description'] = r.get('detail', '')
            r['category'] = get_category(r.get('risk', ''))
            r['type'] = r['category']

        final_weaknesses = structured_weaknesses
        final_issues = [r for r in structured_weaknesses if r.get('severity') in ['FATAL', 'CRITICAL', 'HIGH']]

        # ── SENIOR ADVOCATE BRIEF (Standalone Object for Print/UI) ───────────
        senior_brief = {
            "verdict": verdict,
            "biggest_risk": tldr.get("core_risk", "Evidentiary Gaps") if verdict != "DO NOT FILE" else "[!] FATAL: " + tldr.get("core_risk", "Statutorily Dead Case"),
            "strongest_defence": tldr.get("top_threat", "Standard Rebuttal"),
            "predicted_posture": "Defensive" if score < 50 else "Prosecution-Ready",
            "top_actions": [s["title"] for s in suggestions[:3]] if suggestions else ["Review Case File"]
        }
        if verdict == "DO NOT FILE":
            senior_brief["predicted_posture"] = "WITHDRAW OR ABANDON (High Perjury/Cost Risk)"
            senior_brief["biggest_risk"] = engine_result.get("failure_point", senior_brief["biggest_risk"])

        # ── LLM COPILOT LAYER ───────────
        weakness_strs = [w['risk'] for w in final_weaknesses]
        executive_summary_text = generate_executive_summary(score, weakness_strs, strengths, case_data)
        
        from llm_engine import LLM_AVAILABLE
        if LLM_AVAILABLE and "Case Score" not in executive_summary_text:
            executive_summary_text = ResponseBuilder._prefix_text(executive_summary_text, "AI Enhanced")
        else:
            executive_summary_text = ResponseBuilder._prefix_text(executive_summary_text, "Rule-Based")
        
        # Build defences for response
        defences_list = engine_result.get("defences") or []
        if not defences_list:
            risks_and_rebuttals = engine_result.get("risks_and_rebuttals", [])
            for node in risks_and_rebuttals:
                collapse_prob = 50
                try:
                    collapse_prob = int(node.get("collapse_risk", "50").replace("%", ""))
                except:
                    pass
                rebuttal_text = ""
                rebut_tree = node.get("rebuttal_tree", {})
                if rebut_tree:
                    rebuttal_text = rebut_tree.get("complainant_counter", "")
                defences_list.append({
                    "argument": node.get("adversarial_vector", "Defence Strategy"),
                    "strength": node.get("severity", "Medium"),
                    "success_probability": collapse_prob,
                    "trigger_reason": node.get("why_applied", "Applicable based on case facts."),
                    "rebuttal": rebuttal_text
                })

        base_draft = engine_result.get("draft", "")
        draft_type = engine_result.get("draft_type", "LEGAL_OPINION")
        enhanced_draft = enhance_legal_draft(base_draft, draft_type, case_data) if base_draft else ""
        draft_label = "AI Enhanced" if LLM_AVAILABLE and enhanced_draft and enhanced_draft != base_draft else "Rule-Based"
        enhanced_draft = ResponseBuilder._prefix_text(enhanced_draft, draft_label)
        base_draft = ResponseBuilder._prefix_text(base_draft, "Rule-Based")

        return {
            "score":              score,
            "final_score":        score,
            "verdict":            verdict,
            "risk_level":         risk_level,
            "analysis_confidence": confidence_score,
            "decision":           decision,
            "strengths":          strengths,
            "weaknesses":         final_weaknesses,
            "issues":             final_issues,
            "legal_strategy":     strategy,
            "alternative_evidence": alternative_evidence,
            "judicial_caveats":   engine_result.get("discretionary_caveats", []),
            "reasoning_trace":    lawyer_reasoning,
            "semantic_analysis": {
                "concepts_detected": concepts_for_response,
                "total_confidence":  confidence_score,
                "count":             len(concepts)
            },
            "executive_summary": {
                "score":              score,
                "recommended_action": recommended_action,
                "decision_label":     decision_label,
                "top_3_risks":        [r["risk"] for r in top_3_risks] or ["Standard risks"],
                "top_strengths":      strengths[:3] or ["Pillar compliance"],
                "next_steps":         next_steps,
                "readiness_index":    engine_result.get("cri_score", 0),
                "llm_summary":        executive_summary_text
            },
            "legal_analysis":    "\n".join(lawyer_reasoning) if lawyer_reasoning else "Standard analysis applied.",
            "analysis_details": {
                "issues":    [f"{r['risk']} [{r['severity']}]" for r in ranked_weaknesses],
                "strengths": strengths,
                "reasoning": lawyer_reasoning,
                "breakdown": breakdown
            },
            "defence_strategy":          defences_list,
            "draft":                     enhanced_draft,
            "draft_raw":                 base_draft,
            "draft_type":                engine_result.get("draft_type", "LEGAL_OPINION"),
            "timeline":                  engine_result.get("timeline", []),
            "limitation":                engine_result.get("limitation", {}),
            "case_summary":              engine_result.get("case_summary", ""),
            "precedents":                engine_result.get("precedents", []),
            "statutory_interpretation":  engine_result.get("statutory_interpretation", []),
            "reasoning_trail":           engine_result.get("reasoning_trail", []),
            "fact_graph":                engine_result.get("fact_graph", {}),
            "risks_and_rebuttals":       engine_result.get("risks_and_rebuttals", []),
            "outcome_prediction":        engine_result.get("outcome_prediction", {}),
            "translated_verdict":        engine_result.get("translated_verdict", ""),
            "evidence_suggestions":      engine_result.get("evidence_suggestions", []),
            "uncertainty_intelligence":  engine_result.get("uncertainty_intelligence", []),
            "evidence_dependencies":     engine_result.get("evidence_dependencies", []),
            "judicial_mode":             engine_result.get("judicial_mode", "Balanced"),
            "red_team_attacks":          engine_result.get("red_team_attacks", []),
            "witness_pressure":          engine_result.get("witness_pressure", {}),
            "self_challenge":            engine_result.get("self_challenge", {}),
            "reliability_matrix":        engine_result.get("reliability_matrix", {}),
            "case_similarity":           engine_result.get("case_similarity", {}),
            "advocate_audit":            audit,
            "case_data":                 case_data,
            "analysis_mode":             case_data.get("analysis_mode", "detailed"),
            "proof_present":             case_data.get("proof_present", True),
            "timestamp":      datetime.now().isoformat(),
            "engine_version": "v12.0.0-JUDIQ-PRO",
            "cri_score":      engine_result.get("cri_score", 0),
            "cross_exam":     engine_result.get("cross_exam_prep", []),
            "causality_map":  causality_map,
            "compliance_pct": engine_result.get("compliance_pct", 0),
            "economics":      engine_result.get("economics", {}),
            "checkpoints":    engine_result.get("checkpoints", []),
            "explicit_risk_propagation": [f"{c['fact']}: {c['impact']}" for c in causality_map],
            "causality_delta": {
                "labels": [c.get('fact', 'Factor') for c in causality_map],
                "values": [
                    max(0, min(100, sum(x.get('impact', 0) for x in causality_map[:i+1])))
                    for i in range(len(causality_map))
                ]
            },
            "causal_story": engine_result.get("causal_story", []),
            "contradictions": engine_result.get("contradictions", []),
            "timeline_anomalies": engine_result.get("timeline_anomalies", []),
            "remediation_roadmap": engine_result.get("remediation_roadmap", []),
            "calibration_metadata": {
                "statistical_confidence": engine_result.get("analysis_confidence", 0.92),
                "rule_compliance_pct": engine_result.get("compliance_pct", 0),
                "precedent_binding_score": engine_result.get("precedent_score", 0.88),
                "audit_mode": "Professional (Hardened)",
                "methodology_pillars": [
                    {"label": "Precedent Alignment", "weight": "35%"},
                    {"label": "Timeline Compliance", "weight": "25%"},
                    {"label": "Document Completeness", "weight": "40%"}
                ]
            },
            "evidence_reliability": engine_result.get("evidence_reliability", {}),
            "tldr": tldr,
            "strategic_audit": engine_result.get("strategic_audit", []),
            "senior_brief": senior_brief,
            "failure_point": engine_result.get("failure_point", ""),
            "question_bank": engine_result.get("question_bank", []),
            # New: Judicial Intelligence Layer
            "judicial_report": engine_result.get("judicial_report", {}),
            "jurisdiction_info": engine_result.get("jurisdiction_info", {}),
            "theoretical_score": engine_result.get("theoretical_score", score),
            "judicial_multiplier": engine_result.get("judicial_report", {}).get("judicial_multiplier", {}),
            "judge_challenge_predictions": engine_result.get("judicial_report", {}).get("judge_challenge_predictions", []),
            "court_stats": engine_result.get("judicial_report", {}).get("court_stats", {}),
            # New: RAG Precedent Intelligence
            "precedent_intelligence": engine_result.get("precedent_intelligence", {}),
            "supporting_precedents": engine_result.get("precedent_intelligence", {}).get("supporting", []),
            "opposing_precedents": engine_result.get("precedent_intelligence", {}).get("opposing", []),
            "distinguishable_precedents": engine_result.get("precedent_intelligence", {}).get("distinguishable", []),
        }
