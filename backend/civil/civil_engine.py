from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from scoring_engine import ScoringEngine
from adversarial_engine import AdversarialEngine

class CivilEngine(BaseDomainEngine):
    """
    Domain engine for Civil & Commercial litigation (Code of Civil Procedure, 1908).
    Extends BaseDomainEngine.
    """

    @property
    def domain_name(self) -> str:
        return "civil"

    @classmethod
    def analyze(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_data["case_type"] = "civil"
        concepts = case_data.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(case_data, concepts)
        scoring = ScoringEngine.calculate_score(case_data, concepts, contradictions)
        return {
            **scoring,
            "contradictions": contradictions
        }
