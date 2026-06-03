from typing import Dict, List, Any
from .criminal_adversarial_engine import CriminalAdversarialEngine

class CriminalEngine:
    """
    Advanced Strategy Engine for Criminal Matters.
    Generates actionable litigation maps, procedural roadmaps, and bail predictability.
    """

    @staticmethod
    def generate_strategy(case_data: Dict, concepts: List[Dict], severity_score: int, adversarial_risk: float = 0.5) -> Dict[str, Any]:
        """Orchestrates all strategy components for the criminal core engine."""
        from .criminal_timeline_engine import CriminalTimelineEngine
        from .criminal_economics_engine import CriminalEconomicsEngine
        from .criminal_rules_engine import CriminalRulesEngine
        from .criminal_scoring_engine import CriminalScoringEngine
        
        contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
        scoring_data = CriminalScoringEngine.calculate_score(case_data, concepts, contradictions)
        
        return {
            "score": scoring_data["score"],
            "verdict": scoring_data["verdict"],
            "score_breakdown": scoring_data["score_breakdown"],
            "causality_map": scoring_data["causality_map"],
            "statutory_rules": CriminalRulesEngine.evaluate_rules(case_data),
            "litigation_map": CriminalEngine.generate_litigation_map(case_data, severity_score, concepts),
            "roadmap": CriminalAdversarialEngine.calculate_stage_survivability(severity_score, adversarial_risk),
            "bail_assessment": CriminalEngine.assess_bail_probability(case_data, concepts),
            "economics": CriminalEconomicsEngine.calculate_economics(case_data),
            "timeline_analysis": CriminalTimelineEngine.analyze_timelines(case_data),
            "checkpoints": CriminalEngine.get_advocate_checkpoints(severity_score, case_data)
        }

    @staticmethod
    def assess_bail_probability(case_data: Dict, concepts: List[Dict]) -> Dict[str, Any]:
        """Analyzes S.437/438 CrPC factors and section-specific bail intelligence."""
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
        """Creates aggressive vs defensive postures based on whether representing Prosecution/Complainant or Defence/Accused."""
        role = case_data.get("client_role", "Accused") # Default to Accused for criminal defence
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
        """Human override and validation points for criminal practice."""
        checkpoints = [
            "MANDATORY: Scrutinize FIR for S.154 CrPC delay. Unexplained delay is fatal to prosecution.",
            "STRATEGIC: Evaluate necessity of S.311 CrPC application for recalling key witnesses."
        ]
        if case_data.get("electronic_evidence"):
            checkpoints.append("CRITICAL: Ensure mandatory S.65B Evidence Act certificate is filed alongside electronic records.")
        return checkpoints
