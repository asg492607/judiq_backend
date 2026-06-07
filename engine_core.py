import logging
from typing import Dict, List, Any
from datetime import datetime
import importlib

# â”€â”€ Logging Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
logger = logging.getLogger(__name__)

# â”€â”€ Safe Fallback Builder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _safe_call(fn, *args, fallback, context=""):
    """Call fn(*args); on any exception return fallback and log the error."""
    try:
        return fn(*args)
    except Exception as exc:
        logger.error(f"[ENGINE] {context} failed: {exc}", exc_info=True)
        return fallback

class EngineRegistry:
    """
    Enforces interface discipline and dependency governance.
    Addresses Scalability Governance weakness by decoupling module access.
    """
    def __init__(self):
        # Configuration for lazy loading
        self._modules = {
            "scoring":     "scoring_engine.ScoringEngineV12",
            "criminal_scoring": "criminal_scoring_engine.CriminalScoringEngine",
            "semantic":    "semantic_engine.SemanticEngineV12",
            "adversarial": "adversarial_engine.AdversarialEngine",
            "criminal_adversarial": "criminal_adversarial_engine.CriminalAdversarialEngine",
            "strategy":    "strategy_engine.StrategyEngine",
            "criminal_strategy": "criminal_engine.CriminalEngine",
            "draft":       "draft_engine.DraftEngine",
            "reasoning":   "reasoning_engine.ReasoningEngine",
            "timeline":    "timeline_engine.TimelineEngine",
            "simulator":   "simulator_engine.SimulatorEngine",
            "defence":     "defence_engine.DefenceEngineV12",
            "decision":    "decision_support_engine.DecisionSupportEngine",
            "document_intelligence": "document_intelligence.DocumentIntelligence"
        }
        self._instances = {}

    def get(self, module_name: str):
        if module_name not in self._modules:
            raise ImportError(f"Engine Component '{module_name}' not found in registry.")
        
        if module_name not in self._instances:
            path = self._modules[module_name]
            module_path, class_name = path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            self._instances[module_name] = getattr(module, class_name)
            
        return self._instances[module_name]

# Global Registry Instance
registry = EngineRegistry()

# LLM Availability Flag
from llm_engine import LLM_AVAILABLE

# RAG + Judicial Engine (new engines, imported once at module level)
try:
    from rag_engine import rag_manager
except Exception as _e:
    logger.warning(f"[ENGINE] rag_engine import failed: {_e}")
    rag_manager = None

try:
    from judicial_engine import judicial_engine as _judicial_engine
except Exception as _e:
    logger.warning(f"[ENGINE] judicial_engine import failed: {_e}")
    _judicial_engine = None

# â”€â”€ Synthetic Text Mapping (For Quick/Ghost Analysis) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SYNTHETIC_TEXT_MAP = {
    "cheque_present":  "cheque dishonoured and bounced by bank",
    "dishonour_memo":  "bank issued dishonour memo and return slip",
    "notice_sent":     "legal notice served on accused",
    "debt_proven":     "loan agreement executed and legally enforceable debt established",
}

class JudiQEngine:
    """
    Central orchestrator -- fully fault-tolerant.
    Each pipeline step is independently guarded so a failure in one layer
    NEVER crashes the entire analysis.
    """

    @classmethod
    def analyze_case(cls, raw_data: dict, analysis_mode: str = "detailed") -> dict:
        """
        Hardened Orchestrator - uses EngineRegistry for all sub-module calls.
        """
        from normalizer import normalize_input, validate_minimum_viability, ValidationError
        from response_builder import ResponseBuilder

        from schemas import CaseInput
        from pydantic import ValidationError as PydanticValidationError

        # -- 1. Normalization & Validation -----------------------------------
        try:
            normalized_raw = normalize_input(raw_data)
            validated_input = CaseInput(**normalized_raw)
            case_data = validated_input.dict()
        except PydanticValidationError as e:
            logger.error(f"Schema Validation failed: {e}")
            raise ValueError(f"Invalid case input schema: {e}")
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            raise
            
        # WhatsApp Paradox Fix: Map frontend bsa_certificate string to expected boolean
        if "has_65b_certificate" not in case_data:
            case_data["has_65b_certificate"] = str(case_data.get("bsa_certificate", "")).lower() == "yes"
        if "has_bsa_certificate" not in case_data:
            case_data["has_bsa_certificate"] = case_data["has_65b_certificate"]
            
        case_data["analysis_mode"] = analysis_mode
        logger.info(f"[JUDIQ] Core analysis triggered for: {case_data.get('case_id', 'ANON')}")

        # -- 1.5 Document Intelligence Override -------------------------------
        try:
            doc_intel = registry.get("document_intelligence")
            verification_flags = doc_intel.validate_claims(case_data)
            
            # Apply overrides to case_data to defeat 'User Honesty' trap
            if verification_flags.get("overrides"):
                for k, v in verification_flags["overrides"].items():
                    case_data[k] = v
                    logger.warning(f"[ENGINE] Overriding user input {k} -> {v}")
                    
            # Inject penalties directly into case_data so scoring engine can catch it
            case_data["verification_penalties"] = verification_flags.get("verification_penalties", 0)
        except Exception as e:
            logger.error(f"[ENGINE] Document Intelligence Override failed: {e}")

        # -- 2. Semantic Extraction & Fact Graph (Hybrid Architecture) --------
        text = case_data.get("description", "").strip()
        if not text:
            parts = [phrase for key, phrase in SYNTHETIC_TEXT_MAP.items() if case_data.get(key)]
            text = ". ".join(parts)
            
        fact_graph = None
        if LLM_AVAILABLE:
            try:
                from llm_engine import extract_fact_graph
                fact_graph = _safe_call(
                    extract_fact_graph, text,
                    fallback=None,
                    context="LLM_FactGraph"
                )
            except Exception as e:
                logger.error(f"Failed to load LLM fact graph: {e}")
            
        case_data["fact_graph"] = fact_graph

        semantic_engine = registry.get("semantic")
        semantic_result = _safe_call(
            semantic_engine.analyze_text, text,
            fallback={"concepts_detected": [], "entities": []},
            context="SemanticEngine"
        )
        concepts = semantic_result.get("concepts_detected") or []

        # -- 2.5 Case Type Detection ------------------------------------------
        text_lower = text.lower()
        is_criminal = case_data.get("case_type") == "criminal" or "criminal" in text_lower or "fir" in text_lower or case_data.get("offense_type") is not None
        is_cheque_bounce = case_data.get("case_type") == "cheque_bounce" or "cheque" in text_lower or case_data.get("cheque_present")

        if is_criminal and is_cheque_bounce:
            logger.info("Mixed case detected (Criminal + Cheque Bounce). Orchestrating combined analysis.")
            adv_modules = ["adversarial", "criminal_adversarial"]
            strat_modules = ["strategy", "criminal_strategy"]
            scoring_modules = ["scoring", "criminal_scoring"]
        elif is_criminal:
            adv_modules = ["criminal_adversarial"]
            strat_modules = ["criminal_strategy"]
            scoring_modules = ["criminal_scoring"]
        else:
            adv_modules = ["adversarial"]
            strat_modules = ["strategy"]
            scoring_modules = ["scoring"]

        # -- 3. Adversarial Audit ---------------------------------------------
        attack_chains = []
        for adv_module in adv_modules:
            adversarial_engine = registry.get(adv_module)
            adversarial_result = _safe_call(
                adversarial_engine.audit_case, case_data, concepts,
                fallback={"risks_and_rebuttals": [], "contradictions": []},
                context=f"{adv_module}"
            )
            attack_chains.extend(adversarial_result.get("risks_and_rebuttals", []))
        
        # NEW: Contradiction Engine
        contradictions = _safe_call(
            adversarial_engine.detect_contradictions, case_data, concepts,
            fallback=[],
            context="ContradictionEngine"
        )
        
        # NEW: Timeline Anomaly Detector
        timeline_anomalies = _safe_call(
            adversarial_engine.detect_timeline_anomalies, case_data,
            fallback=[],
            context="TimelineAnomalyDetector"
        )
        
        # Risk Metric
        adversarial_risk = _safe_call(
            adversarial_engine.calculate_adversarial_risk, attack_chains,
            fallback=0.2,
            context="AdversarialEngine.risk"
        )

        evidence_dependencies = _safe_call(
            adversarial_engine.map_evidence_dependencies, case_data,
            fallback=[],
            context="EvidenceDependencyMapping"
        )

        # NEW: Strategic Audit
        red_team_attacks = _safe_call(
            adversarial_engine.run_strategic_audit, case_data, concepts,
            fallback=[],
            context="StrategicAudit"
        )
        
        # NEW: Witness Pressure Simulation
        witness_pressure = _safe_call(
            adversarial_engine.simulate_witness_pressure, case_data, adversarial_risk,
            fallback={},
            context="WitnessPressure"
        )

        # -- 4. Scoring Engine ------------------------------------------------
        scoring_results = []
        for scoring_module in scoring_modules:
            scoring_engine = registry.get(scoring_module)
            if "criminal" in scoring_module:
                res = _safe_call(
                    scoring_engine.calculate_score, case_data, concepts, contradictions,
                    fallback={"score": 50, "final_score": 50, "reasoning_trace": ["Internal scoring error."]},
                    context="CriminalScoringEngine"
                )
            else:
                res = _safe_call(
                    scoring_engine.calculate_score_with_trace, case_data, concepts, contradictions, {},
                    fallback={"score": 50, "final_score": 50, "reasoning_trace": ["Internal scoring error."]},
                    context="ScoringEngine"
                )
            scoring_results.append(res)
        
        # Aggregate scores (average if multiple)
        scoring_result = scoring_results[0]
        if len(scoring_results) > 1:
            avg_score = sum(float(r.get("final_score") or r.get("score") or 50) for r in scoring_results) / len(scoring_results)
            scoring_result["final_score"] = avg_score
            scoring_result["score"] = avg_score
            scoring_result["reasoning_trace"] = scoring_results[0].get("reasoning_trace", []) + ["Mixed Case Adjustments applied."] + scoring_results[1].get("reasoning_trace", [])

        final_score = float(scoring_result.get("final_score") or scoring_result.get("score") or 50)

        # -- 5. Strategic Layer -----------------------------------------------
        strategy_results = []
        for strat_module in strat_modules:
            strategy_engine = registry.get(strat_module)
            strategy_result = _safe_call(
                strategy_engine.generate_strategy if hasattr(strategy_engine, 'generate_strategy') else strategy_engine.generate_litigation_map, 
                case_data, concepts, int(final_score), adversarial_risk,
                fallback={"litigation_strategy": "Maintain standard procedural posture."},
                context="StrategyEngine"
            )
            strategy_results.append(strategy_result)
        
        # Merge strategy results if multiple
        strategy_result = strategy_results[0]
        if len(strategy_results) > 1:
            strategy_result["litigation_strategy"] = strategy_results[0].get("litigation_strategy", "") + "\n\nCRIMINAL OVERLAY:\n" + strategy_results[1].get("litigation_strategy", "")

        # -- 6. Reasoning & Traceability (Explainable AI) --------------------
        reasoning_engine = registry.get("reasoning")
        
        # NEW: Causal Story Flow
        causal_story = _safe_call(
            reasoning_engine.generate_causal_story, case_data, concepts,
            fallback=[],
            context="CausalStoryBuilder"
        )

        # -- 10. Reasoning Trail (Provenance & Explainability) ----------------
        reasoning_trail = _safe_call(
            reasoning_engine.generate_reasoning_trail, 
            case_data, 
            semantic_result.get("concepts_detected", []), 
            scoring_result.get("score", 0),
            scoring_result, # Pass calibrated result
            fallback=[],
            context="Reasoning Trail"
        )
        
        # NEW: Precedents & Citations
        precedents = _safe_call(
            reasoning_engine.match_precedents, case_data, concepts,
            fallback=[],
            context="ReasoningEngine.precedents"
        )
        
        # LLM Precedent Relationship Analysis
        try:
            from llm_engine import analyze_precedent_relationships
            enriched_precedents = _safe_call(
                analyze_precedent_relationships, case_data, precedents,
                fallback=precedents,
                context="LLM_PrecedentRelationships"
            )
            precedents = enriched_precedents or precedents
        except Exception as e:
            logger.error(f"Failed to load LLM precedent relationships: {e}")
        
        # NEW: Statutory Interpretation
        statutory_interpretation = _safe_call(
            reasoning_engine.interpret_statutes, case_data, concepts,
            fallback=[],
            context="Statutes"
        )
        
        case_summary = _safe_call(
            reasoning_engine.summarize_case, case_data,
            fallback="Case assessment based on statutory pillars.",
            context="ReasoningEngine.summary"
        )

        # -- 6.5 RAG Precedent Intelligence -----------------------------------
        if rag_manager is not None:
            precedent_intelligence = _safe_call(
                rag_manager.get_precedent_intelligence, case_data,
                fallback={"supporting": [], "opposing": [], "distinguishable": [], "all_relevant": []},
                context="RAGManager"
            )
        else:
            precedent_intelligence = {"supporting": [], "opposing": [], "distinguishable": [], "all_relevant": []}

        # -- 8. Judicial & Jurisdiction Analysis ------------------------------
        try:
            from jurisdiction_engine import map_jurisdiction
            jurisdiction_info = map_jurisdiction(case_data)
        except Exception as e:
            logger.error(f"[ENGINE] Jurisdiction mapping failed: {e}")
            jurisdiction_info = {"status": "ERROR"}

        judicial_report = {}
        if _judicial_engine:
            judicial_report = _safe_call(
                _judicial_engine.generate_judicial_report, case_data, final_score,
                fallback={},
                context="JudicialEngine"
            )

        # Apply Jurisdiction Fatal Defect Check
        if jurisdiction_info.get("status") == "INVALID" or jurisdiction_info.get("confidence") == "NONE":
            # Jurisdiction is territorial and critical under S.142(2) NI Act. Applying severe penalty.
            judicially_adjusted_score = max(0, final_score - 35)
            if "jurisdictional_defect" not in {c.get("concept") for c in concepts}:
                concepts.append({"concept": "jurisdictional_defect", "confidence": 0.95, "legal_impact": "FATAL: Wrong territorial jurisdiction. Complaint will be returned under Dashrath Rupsingh Rathod precedent."})
        else:
            judicially_adjusted_score = final_score

        # -- 6.7 Fatal Defect Hard Override -----------------------------------
        # -- 6.6 Timeline Engine (Moved up for Fatal Check) -------------------
        timeline_engine = registry.get("timeline")
        timeline = _safe_call(
            timeline_engine.generate_timeline, case_data,
            fallback=[],
            context="TimelineEngine.generate"
        )
        limitation = _safe_call(
            timeline_engine.check_limitation, case_data,
            fallback={"is_barred": False, "status": "CALCULATION_ERROR"},
            context="TimelineEngine.limitation"
        )

        # -- 6.7 Fatal Defect Hard Override -----------------------------------
        is_fatal = False
        fatal_reason = ""
        for contra in contradictions:
            if contra.get("penalty", 0) <= -50 or "Fatal" in contra.get("remediation", "") or "DO NOT FILE" in contra.get("remediation", ""):
                is_fatal = True
                fatal_reason = contra.get("issue", "Critical Defect")
                break
        
        if not is_fatal and case_data.get("fatal_defect"):
            is_fatal = True
            fatal_reason = str(case_data.get("fatal_defect"))

        if not is_fatal and "analysis_nodes" in adversarial_result:
            for node in adversarial_result["analysis_nodes"]:
                if node.get("severity") == "FATAL":
                    is_fatal = True
                    fatal_reason = node.get("risk_explained", "Fatal Adversarial Risk")
                    break

        # Check OCR/Evidentiary fraud override directly
        if case_data.get("verification_penalties", 0) < 0:
            is_fatal = True
            fatal_reason = "Evidentiary Fraud / Document Intelligence Override"
            
        # Check Timeline / Notice Service Fatalities
        if limitation.get("fatal_defect") or limitation.get("is_premature") or limitation.get("status") == "NOTICE_INVALID":
            is_fatal = True
            fatal_reason = limitation.get("fatal_defect", "Invalid Timeline/Notice Issue")

        if is_fatal:
            final_score = min(final_score, 25.0)
            judicially_adjusted_score = min(judicially_adjusted_score, 25.0)

        # -- 7. Draft Generation ----------------------------------------------
        draft_engine = registry.get("draft")
        from draft_engine import decide_draft_type
        
        # Priority: Forced Draft Type > Decision Logic
        if is_fatal:
            draft_type = "LEGAL_OPINION"
            logger.warning(f"GLOBAL FATAL OVERRIDE: Forcing draft_type to LEGAL_OPINION due to {fatal_reason}")
        else:
            draft_type = raw_data.get("force_draft_type") or decide_draft_type(int(final_score), concepts, case_data)
        
        case_data["failure_point_injected"] = fatal_reason if is_fatal else scoring_result.get("failure_point", "")
        
        draft_content = _safe_call(
            draft_engine.generate_draft, draft_type, int(final_score), concepts, case_data,
            fallback="Legal draft generation failed. Please use manual templates.",
            context="DraftEngine"
        )

        logger.info(f"DRAFT_ENGINE: Type={draft_type}, Size={len(draft_content) if draft_content else 0}")
        
        # -- 8. Decision Support & Intelligence -------------------------------
        decision_engine = registry.get("decision")
        outcome_prediction = _safe_call(
            decision_engine.predict_outcome, final_score,
            fallback={"prediction": "Unknown", "probability": "0%"},
            context="DecisionSupportEngine.outcome"
        )
        
        if is_fatal:
            outcome_prediction = {"prediction": f"DO NOT FILE - {fatal_reason}", "probability": "0%"}
            scoring_result["verdict"] = "DO NOT FILE"
        translated_verdict = _safe_call(
            decision_engine.translate_verdict, scoring_result.get("verdict", "MODERATE"), case_data.get("target_lang", "hindi"),
            fallback="à¤®à¤œà¤¬à¥‚à¤¤ à¤®à¤¾à¤®à¤²à¤¾",
            context="DecisionSupportEngine.translate"
        )
        evidence_suggestions = _safe_call(
            decision_engine.suggest_evidence_gaps, case_data,
            fallback=[],
            context="DecisionSupportEngine.evidence"
        )
        decision_risks = _safe_call(
            decision_engine.identify_risks_and_rebuttals, concepts, case_data,
            fallback=[],
            context="DecisionSupportEngine.risks"
        )
        
        # -- 8. Integrated Adversarial Analysis -------------------------------
        # Merge risks from both engines with Deduplication (Contextual Severity Engine)
        if "risks_and_rebuttals" not in adversarial_result:
            adversarial_result["risks_and_rebuttals"] = []
            
        existing_risk_titles = {str(r.get("adversarial_vector", r.get("risk", ""))).lower() for r in adversarial_result["risks_and_rebuttals"]}
        
        for dr in decision_risks:
            dr_title = str(dr["risk"]).lower()
            if dr_title not in existing_risk_titles:
                existing_risk_titles.add(dr_title)
                adversarial_result["risks_and_rebuttals"].append({
                    "adversarial_vector": dr["risk"],
                    "risk": dr["risk"],
                    "severity": dr.get("severity", "HIGH"),
                    "description": dr.get("description", ""),
                    "rebuttal": dr.get("rebuttal", ""),
                    "strategic_chain": [dr.get("description", "")],
                    "rebuttal_tree": {
                        "complainant_counter": dr.get("rebuttal", ""),
                        "magistrate_view": f"High attention to {dr.get('case_law', 'relevant statutes')}"
                    },
                    "survival_probability": "65%",
                    "collapse_risk": "35%"
                })

        # -- 9. Timeline & Simulation -----------------------------------------
        # (Timeline generated earlier at step 6.6 for fatal checks)
        # -- 10. Executive TL;DR Layer (New) ----------------------------------
        # Fulfills User Request: Executive-first UX for busy lawyers
        tldr = {
            "core_risk": "Procedural Technicality" if final_score < 40 else ("Evidentiary Gap" if final_score < 70 else "Minimal"),
            "top_threat": adversarial_result["risks_and_rebuttals"][0]["adversarial_vector"] if adversarial_result["risks_and_rebuttals"] else "None identified",
            "best_move": scoring_result.get("remediation_roadmap", [{"action": "Maintain posture"}])[0]["action"],
            "confidence": f"{int(final_score)}%",
            "one_liner": f"Case is {outcome_prediction.get('prediction', 'stable')} with {len(contradictions)} logical inconsistencies detected."
        }

        # -- 11. Response Assembly ---------------------------------------------
        # Prepare the flat dict for ResponseBuilder
        engine_output = {
            "final_score": judicially_adjusted_score,
            "theoretical_score": final_score,
            "judicial_report": judicial_report,
            "jurisdiction_info": jurisdiction_info,
            "precedent_intelligence": precedent_intelligence,
            "tldr": tldr,
            "reasoning_trace": scoring_result.get("reasoning_trace", []),
            "reasoning_trail": reasoning_trail,
            "causal_story": causal_story,
            "contradictions": contradictions,
            "timeline_anomalies": timeline_anomalies,
            "evidence_dependencies": evidence_dependencies,
            "strategic_audit": red_team_attacks,
            "witness_pressure": witness_pressure,
            "uncertainty_intelligence": scoring_result.get("uncertainty_intelligence", []),
            "judicial_mode": scoring_result.get("judicial_mode", "Balanced"),
            "self_challenge": scoring_result.get("self_challenge", {}),
            "reliability_matrix": scoring_result.get("reliability_matrix", {}),
            "case_similarity": scoring_result.get("case_similarity", {}),
            "failure_point": scoring_result.get("failure_point", ""),
            "senior_brief": scoring_result.get("senior_brief", {}),
            "score_breakdown": scoring_result.get("breakdown", {}),
            "concepts": concepts,
            "adversarial_result": adversarial_result,
            "outcome_prediction": outcome_prediction,
            "translated_verdict": translated_verdict,
            "evidence_suggestions": evidence_suggestions,
            "case_summary": case_summary,
            "precedents": precedents,
            "statutory_interpretation": statutory_interpretation,
            "fact_graph": case_data.get("fact_graph", {}),
            "draft": draft_content,
            "draft_type": draft_type,
            "timeline": timeline,
            "limitation": limitation,
            "strategy_result": strategy_result,
            "adversarial_risk": adversarial_risk
        }
        # Merge results into the structure ResponseBuilder expects
        full_result = {**engine_output, **scoring_result, **adversarial_result}
        
        return ResponseBuilder.build_final_response(full_result, case_data)

