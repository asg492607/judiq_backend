from typing import Dict, List, Any
from criminal_adversarial_engine import CriminalAdversarialEngine
class CriminalEngine:
    @classmethod
    def analyze(cls, case_data: Dict) -> Dict[str, Any]:
        from criminal_adversarial_engine import CriminalAdversarialEngine
        from criminal_scoring_engine import CriminalScoringEngine
        concepts = case_data.get("concepts", [])
        contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
        scoring_data = CriminalScoringEngine.calculate_score(case_data, concepts, contradictions)
        strategy = cls.generate_strategy(case_data, concepts, scoring_data["score"], 0.5)
        return {
            **scoring_data,
            "strategy": strategy,
            "contradictions": contradictions
        }

    @staticmethod
    def generate_strategy(case_data: Dict, concepts: List[Dict], severity_score: int, adversarial_risk: float = 0.5) -> Dict[str, Any]:
        from criminal_timeline_engine import CriminalTimelineEngine
        from criminal_economics_engine import CriminalEconomicsEngine
        from criminal_rules_engine import CriminalRulesEngine
        from criminal_scoring_engine import CriminalScoringEngine

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
    def assess_bail_probability(case_data: Dict, concepts: List[Dict]) -> Dict[str, Any]:
        offense_type = str(case_data.get("offense_type", "General")).upper()
        concept_names = [c["concept"] for c in concepts]
        is_heinous = "heinous_crime" in concept_names or offense_type in ["MURDER", "RAPE", "TERRORISM", "302", "376"]
        is_under_7_years = offense_type in ["498A", "420", "406", "323", "324"]
        flight_risk = case_data.get("flight_risk", False)
        evidence_tampering = case_data.get("evidence_tampering_risk", False)
        probability = "LOW"
        rationale = "Bail is the rule, jail is the exception; however, severity dictates outcomes."
        if is_heinous or flight_risk:
            probability = "VERY LOW"
            rationale = "Heinous offense or severe flight risk detected. Bar u/s 437 CrPC applies heavily."
        elif is_under_7_years and not evidence_tampering:
            probability = "VERY HIGH"
            rationale = "Offense punishable with <7 years. Governed by 'Arnesh Kumar v. State of Bihar' guidelines; automatic arrest is prohibited."
        elif not is_heinous and not flight_risk and not evidence_tampering:
            probability = "HIGH"
        else:
            probability = "MEDIUM"
        return {
            "probability": probability,
            "anticipatory_bail_viable": probability in ["HIGH", "VERY HIGH", "MEDIUM"],
            "factors": {
                "flight_risk": flight_risk,
                "evidence_tampering": evidence_tampering,
                "heinous_offense": is_heinous,
                "arnesh_kumar_applicable": is_under_7_years
            },
            "strategic_rationale": rationale
        }
    @staticmethod
    def generate_litigation_map(case_data: Dict, severity_score: int, concepts: List[Dict]) -> Dict[str, Any]:
        role = case_data.get("client_role", "Accused")                                          
        offense_type = str(case_data.get("offense_type", "")).upper()
        is_civil_dispute = offense_type in ["420", "406"] and case_data.get("contract_exists", False)
        is_matrimonial = offense_type in ["498A"]
        if role == "Accused":
            primary_objective = "Secure Acquittal or Quashing"
            tactical_moves = ["File S.438 Anticipatory Bail"]
            if is_civil_dispute or is_matrimonial:
                tactical_moves.append("File S.482 CrPC Quashing Petition (citing Bhajan Lal guidelines for malicious prosecution/civil nature).")
            else:
                tactical_moves.append("Argue Discharge under S.227/239 CrPC based on lack of prima facie evidence.")
            if case_data.get("witness_statements_inconsistent"):
                tactical_moves.append("File S.311 CrPC to recall witnesses to establish contradictions.")
        else:
            primary_objective = "Secure Conviction"
            tactical_moves = ["Ensure Custodial Interrogation", "Expedite FSL Reports"]
            if case_data.get("unnamed_accomplice"):
                tactical_moves.append("File S.319 CrPC to summon additional accused not named in charge sheet.")
        return {
            "client_role": role,
            "posture": {"primary_objective": primary_objective, "tactical_moves": tactical_moves},
            "overall_assessment": "High Risk" if severity_score > 70 else "Manageable"
        }
    @staticmethod
    def get_advocate_checkpoints(severity_score: int, case_data: Dict) -> List[str]:
        checkpoints = [
            "MANDATORY: Scrutinize FIR for S.154 CrPC delay. Unexplained delay is fatal to prosecution.",
            "STRATEGIC: Evaluate necessity of S.311 CrPC application for recalling key witnesses."
        ]
        if case_data.get("electronic_evidence"):
            checkpoints.append("CRITICAL: Ensure mandatory S.65B Evidence Act certificate is filed alongside electronic records.")
        return checkpoints
