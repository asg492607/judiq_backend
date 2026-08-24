from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from criminal.criminal_adversarial_engine import CriminalAdversarialEngine
from criminal.criminal_scoring_engine import CriminalScoringEngine
from criminal.criminal_timeline_engine import CriminalTimelineEngine
from criminal.criminal_economics_engine import CriminalEconomicsEngine
from criminal.criminal_rules_engine import CriminalRulesEngine

class CriminalEngine(BaseDomainEngine):
    """
    Primary orchestrator for Criminal Law Analytics under both legacy (IPC/CrPC/IEA)
    and modern Bharatiya Nyaya Sanhita (BNS/BNSS/BSA) statutory frameworks.
    Extends BaseDomainEngine for CaseRegistry integration.
    """

    @property
    def domain_name(self) -> str:
        return "criminal"

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of criminal litigation procedural milestones."""
        severity_score = case_data.get("severity_score", 50)
        roadmap = CriminalAdversarialEngine.calculate_stage_survivability(severity_score, 0.5)
        return {
            "current_stage": case_data.get("procedural_stage", "Investigation / Pre-Trial"),
            "nodes": roadmap,
            "total_nodes": len(roadmap),
            "completed_nodes": 0
        }

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Returns prioritized next best actions for criminal litigation."""
        rules = CriminalRulesEngine.evaluate_rules(case_data)
        actions = []
        for r in rules:
            actions.append({
                "priority": 1 if "ABSOLUTE" in r.get("severity", "") or "FATAL" in r.get("status", "") else 2,
                "action": r.get("action", ""),
                "reason": r.get("legal_effect", ""),
                "authority": r.get("rule_name", "")
            })
        if not actions:
            role = case_data.get("client_role", "Accused")
            if role == "Accused":
                actions.append({
                    "priority": 1,
                    "action": "File Section 438 CrPC / Section 484 BNSS Anticipatory Bail Application",
                    "reason": "Protect against custodial detention during ongoing investigation.",
                    "authority": "Section 438 CrPC / Section 484 BNSS"
                })
            else:
                actions.append({
                    "priority": 1,
                    "action": "Ensure Custodial Interrogation and Recovery u/s 27 IEA / S.23 BSA",
                    "reason": "Expedite investigation and recovery of material evidence.",
                    "authority": "Section 27 Evidence Act / Section 23 BSA"
                })
        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if concepts is None:
            concepts = case_data.get("concepts", [])
        contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
        scoring_data = CriminalScoringEngine.calculate_score(case_data, concepts, contradictions)
        strategy = cls.generate_strategy(case_data, concepts, scoring_data["score"], 0.5)

        return {
            **scoring_data,
            "domain": "criminal",
            "strategy": strategy,
            "bail_assessment": strategy.get("bail_assessment"),
            "statutory_rules": strategy.get("statutory_rules"),
            "litigation_map": strategy.get("litigation_map"),
            "timeline_analysis": strategy.get("timeline_analysis"),
            "checkpoints": strategy.get("checkpoints"),
            "contradictions": contradictions
        }

    @staticmethod
    def generate_strategy(case_data: Dict[str, Any], concepts: List[Dict[str, Any]], severity_score: int, adversarial_risk: float = 0.5) -> Dict[str, Any]:
        contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
        scoring_data = CriminalScoringEngine.calculate_score(case_data, concepts, contradictions)
        litigation_map = CriminalEngine.generate_litigation_map(case_data, severity_score, concepts)
        bail_assessment = CriminalEngine.assess_bail_probability(case_data, concepts)
        checkpoints = CriminalEngine.get_advocate_checkpoints(severity_score, case_data)
        rules = CriminalRulesEngine.evaluate_rules(case_data)
        economics = CriminalEconomicsEngine.calculate_economics(case_data)
        timeline_analysis = CriminalTimelineEngine.analyze_timelines(case_data)

        strategy_text_parts = [
            f"PRIMARY OBJECTIVE ({litigation_map['client_role']}): {litigation_map['posture']['primary_objective']}",
            "TACTICAL MOVES:\n" + "\n".join(f"- {m}" for m in litigation_map['posture']['tactical_moves']),
            f"BAIL STRATEGY: {bail_assessment['probability']} probability. Rationale: {bail_assessment['strategic_rationale']}"
        ]
        if checkpoints:
            strategy_text_parts.append("ADVOCATE CHECKPOINTS:\n" + "\n".join(f"- {c}" for c in checkpoints))
        if rules:
            strategy_text_parts.append("STATUTORY RULES TRIGGERED:\n" + "\n".join(f"- {r['rule_name']} ({r['severity']}): {r['legal_effect']}" for r in rules))

        litigation_strategy_str = "\n\n".join(strategy_text_parts)

        return {
            "score": scoring_data["score"],
            "verdict": scoring_data["verdict"],
            "score_breakdown": scoring_data["score_breakdown"],
            "causality_map": scoring_data["causality_map"],
            "statutory_rules": rules,
            "litigation_map": litigation_map,
            "litigation_strategy": litigation_strategy_str,
            "roadmap": CriminalAdversarialEngine.calculate_stage_survivability(severity_score, adversarial_risk),
            "bail_assessment": bail_assessment,
            "economics": economics,
            "timeline_analysis": timeline_analysis,
            "checkpoints": checkpoints
        }

    @staticmethod
    def assess_bail_probability(case_data: Dict[str, Any], concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        offense_type = str(case_data.get("offense_type", "General")).upper()
        concept_names = [c.get("concept", "") for c in concepts] if isinstance(concepts, list) else []

        is_heinous = "heinous_crime" in concept_names or offense_type in ["MURDER", "RAPE", "TERRORISM", "NDPS", "302", "376", "395", "103", "64", "310"]
        is_under_7_years = offense_type in ["498A", "420", "406", "323", "324", "85", "318", "316", "115"] or case_data.get("punishment_years", 10) <= 7

        flight_risk = case_data.get("flight_risk", False)
        evidence_tampering = case_data.get("evidence_tampering_risk", False)
        in_custody = case_data.get("in_custody", False)
        days_in_custody = case_data.get("days_in_custody", 0)

        probability = "LOW"
        rationale = "Bail is the rule, jail is the exception (State of Rajasthan v. Balchand); however, offence gravity dictates outcomes."

        if is_heinous or flight_risk:
            probability = "VERY LOW"
            rationale = "Heinous offence or severe flight risk detected. Statutory bar under Section 437 CrPC / 480 BNSS applies heavily."
        elif is_under_7_years and not evidence_tampering:
            probability = "VERY HIGH"
            rationale = "Offence punishable up to 7 years. Governed by Satender Kumar Antil & Arnesh Kumar v. State of Bihar guidelines; custodial detention should not be granted routinely."
        elif not is_heinous and not flight_risk and not evidence_tampering:
            probability = "HIGH"
            rationale = "Triple test (flight risk, evidence tampering, witness intimidation) satisfied in favor of accused."
        else:
            probability = "MEDIUM"
            rationale = "Bail viable upon imposing strict conditions (surrender of passport, periodic attendance at police station)."

        if in_custody and days_in_custody > 60 and not is_heinous:
            probability = "VERY HIGH"
            rationale += " Protracted undertrial incarceration strengthens right to bail under Article 21 (Union of India v. K.A. Najeeb)."

        return {
            "probability": probability,
            "anticipatory_bail_viable": probability in ["HIGH", "VERY HIGH", "MEDIUM"],
            "regular_bail_viable": True,
            "factors": {
                "flight_risk": flight_risk,
                "evidence_tampering": evidence_tampering,
                "heinous_offense": is_heinous,
                "arnesh_kumar_applicable": is_under_7_years,
                "days_in_custody": days_in_custody
            },
            "strategic_rationale": rationale
        }

    @staticmethod
    def generate_litigation_map(case_data: Dict[str, Any], severity_score: int, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        role = case_data.get("client_role", "Accused")
        offense_type = str(case_data.get("offense_type", "")).upper()
        is_civil_dispute = offense_type in ["420", "406", "318", "316"] and case_data.get("contract_exists", False)
        is_matrimonial = offense_type in ["498A", "85"]

        if role == "Accused":
            primary_objective = "Secure Acquittal, Discharge, or S.482 / S.528 BNSS Quashing"
            tactical_moves = ["File Section 438 CrPC / Section 484 BNSS Anticipatory Bail Application"]
            if is_civil_dispute or is_matrimonial:
                tactical_moves.append("File Section 482 CrPC / Section 528 BNSS Quashing Petition (citing Bhajan Lal guidelines for civil dispute / omnibus allegations).")
            else:
                tactical_moves.append("Argue Discharge under Section 227/239 CrPC / Section 250/262 BNSS based on absence of prima facie case.")

            if case_data.get("witness_statements_inconsistent"):
                tactical_moves.append("Invoke Section 311 CrPC / Section 348 BNSS to recall witnesses for establishing material contradictions.")
        else:
            primary_objective = "Ensure Custodial Interrogation, Chargesheet, and Conviction"
            tactical_moves = ["Ensure Custodial Interrogation and Recovery u/s 27 IEA / S.23 BSA", "Expedite FSL / Forensic Reports"]
            if case_data.get("unnamed_accomplice"):
                tactical_moves.append("File Section 319 CrPC / Section 357 BNSS application to summon additional co-accused not named in chargesheet.")

        return {
            "client_role": role,
            "posture": {"primary_objective": primary_objective, "tactical_moves": tactical_moves},
            "overall_assessment": "High Risk" if severity_score > 70 else "Manageable"
        }

    @staticmethod
    def get_advocate_checkpoints(severity_score: int, case_data: Dict[str, Any]) -> List[str]:
        checkpoints = [
            "MANDATORY: Scrutinize FIR for S.154 CrPC / S.173 BNSS delay. Unexplained delay is fatal to prosecution.",
            "STRATEGIC: Evaluate necessity of S.311 CrPC / S.348 BNSS application for recalling key witnesses."
        ]
        if case_data.get("electronic_evidence"):
            checkpoints.append("CRITICAL: Verify mandatory Section 65B IEA / Section 63 BSA certificate filing alongside electronic exhibits.")
        if case_data.get("is_public_servant"):
            checkpoints.append("JURISDICTIONAL: Verify compliance with Section 197 CrPC / Section 218 BNSS sanction requirement.")
        return checkpoints
