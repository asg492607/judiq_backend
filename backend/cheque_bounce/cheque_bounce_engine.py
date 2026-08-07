from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from scoring_engine import ScoringEngine
from adversarial_engine import AdversarialEngine

class ChequeBounceEngine(BaseDomainEngine):
    """
    Domain engine for Cheque Bounce / S.138 Negotiable Instruments Act litigation.
    Extends BaseDomainEngine.
    """

    @property
    def domain_name(self) -> str:
        return "cheque_bounce"

    @classmethod
    def analyze(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_data["case_type"] = "cheque_bounce"
        concepts = case_data.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(case_data, concepts)
        scoring = ScoringEngine.calculate_score(case_data, concepts, contradictions)
        return {
            **scoring,
            "contradictions": contradictions
        }
