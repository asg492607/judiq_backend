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

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of CPC civil suit litigation milestones."""
        nodes = [
            {"id": "plaint_filing", "name": "Plaint Presentation (Order VI/VII CPC)", "completed": bool(case_data.get("plaint_filed"))},
            {"id": "written_statement", "name": "Written Statement Filing (Order VIII Rule 1 CPC)", "completed": bool(case_data.get("written_statement_filed"))},
            {"id": "framing_issues", "name": "Framing of Issues (Order XIV CPC)", "completed": bool(case_data.get("issues_framed"))},
            {"id": "evidence_stage", "name": "Trial Evidence & Cross Examination (Order XVIII CPC)", "completed": bool(case_data.get("evidence_closed"))},
            {"id": "final_arguments", "name": "Final Hearing & Judgment (Order XX CPC)", "completed": bool(case_data.get("decreed"))}
        ]
        return {
            "current_stage": case_data.get("stage", "Pleadings Stage"),
            "nodes": nodes,
            "total_nodes": len(nodes),
            "completed_nodes": sum(1 for n in nodes if n["completed"])
        }

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Returns prioritized next actions for civil litigation."""
        actions = []
        if case_data.get("urgency_injunction"):
            actions.append({
                "priority": 1,
                "action": "File Application for Temporary Injunction under Order XXXIX Rule 1 & 2 CPC",
                "reason": "Protect subject matter of suit from alienation or destruction pending trial.",
                "authority": "Order XXXIX Rules 1 & 2 Code of Civil Procedure, 1908"
            })
        elif not case_data.get("plaint_filed"):
            actions.append({
                "priority": 1,
                "action": "Draft and File Civil Plaint with Valuation & Court Fees",
                "reason": "Initiate suit proceedings before competent territorial & pecuniary jurisdiction court.",
                "authority": "Order VII Rule 1 Code of Civil Procedure, 1908"
            })
        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_data["case_type"] = "civil"
        if concepts is None:
            concepts = case_data.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(case_data, concepts)
        scoring = ScoringEngine.calculate_score(case_data, concepts, contradictions)
        return {
            **scoring,
            "domain": "civil",
            "contradictions": contradictions
        }
