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

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of Section 138 NI Act statutory milestones."""
        nodes = [
            {"id": "cheque_dishonour", "name": "Cheque Dishonour Memo", "completed": bool(case_data.get("dishonour_date"))},
            {"id": "statutory_notice", "name": "Section 138 Statutory Demand Notice (Within 30 Days)", "completed": bool(case_data.get("notice_date"))},
            {"id": "payment_window", "name": "15-Day Payment Statutory Grace Window", "completed": bool(case_data.get("grace_period_expired"))},
            {"id": "complaint_filing", "name": "Filing Complaint u/s 138 before Magistrate (Within 1 Month)", "completed": bool(case_data.get("complaint_filed"))}
        ]
        return {
            "current_stage": "Statutory Demand / Trial Stage",
            "nodes": nodes,
            "total_nodes": len(nodes),
            "completed_nodes": sum(1 for n in nodes if n["completed"])
        }

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Returns prioritized next actions for S.138 NI Act litigation."""
        actions = []
        if not case_data.get("notice_sent"):
            actions.append({
                "priority": 1,
                "action": "Issue Section 138 Statutory Demand Notice within 30 days of memo date",
                "reason": "Mandatory statutory prerequisite under Section 138(b) NI Act.",
                "authority": "Section 138(b) Negotiable Instruments Act, 1881"
            })
        elif case_data.get("notice_sent") and not case_data.get("complaint_filed"):
            actions.append({
                "priority": 1,
                "action": "File S.138 Criminal Complaint before Judicial Magistrate within 1 month of cause of action",
                "reason": "Cause of action arises on 16th day following receipt of notice by drawer.",
                "authority": "Section 142(1)(b) Negotiable Instruments Act, 1881"
            })
        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_data["case_type"] = "cheque_bounce"
        if concepts is None:
            concepts = case_data.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(case_data, concepts)
        scoring = ScoringEngine.calculate_score(case_data, concepts, contradictions)
        return {
            **scoring,
            "domain": "cheque_bounce",
            "contradictions": contradictions
        }
