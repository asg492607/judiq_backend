from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from scoring_engine import ScoringEngineV12
from adversarial_engine import AdversarialEngine
from utils import days_between, parse_date

class ChequeBounceEngine(BaseDomainEngine):
    """
    Production-grade Domain Engine for Section 138 Negotiable Instruments Act (1881) litigation.
    Evaluates statutory notices, debt enforceability, S.139/S.118 presumptions,
    S.141 director vicarious liability, S.143A interim compensation, and defense strategies.
    """

    @property
    def domain_name(self) -> str:
        return "cheque_bounce"

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of Section 138 NI Act statutory milestones."""
        dishonour_date = case_data.get("date_of_dishonour") or case_data.get("dishonour_date")
        notice_date = case_data.get("date_of_notice") or case_data.get("notice_date")
        complaint_date = case_data.get("date_of_complaint") or case_data.get("complaint_date")

        notice_defect = None
        if dishonour_date and notice_date:
            d = days_between(dishonour_date, notice_date)
            if d is not None and d > 30:
                notice_defect = f"Statutory Notice delayed to {d} days post-dishonour (Limit: 30 days u/s 138(b))."

        complaint_defect = None
        if notice_date and complaint_date:
            d = days_between(notice_date, complaint_date)
            if d is not None and d < 15:
                complaint_defect = f"Complaint filed prematurely on day {d}. Cause of action arises only on 16th day post notice receipt."
            elif d is not None and d > 45:
                complaint_defect = f"Complaint filed after {d} days. Exceeds 1-month statutory window u/s 142(1)(b). Condonation application required."

        nodes = [
            {
                "id": "cheque_dishonour",
                "name": "Cheque Dishonour & Bank Return Memo",
                "statute": "Section 138 & Section 146 NI Act",
                "authority": "Section 146 Presumption of Bank Slip",
                "completed": bool(dishonour_date) or case_data.get("dishonour_memo", False),
                "date": dishonour_date,
                "defect": None,
                "severity": "NONE"
            },
            {
                "id": "statutory_notice",
                "name": "Section 138(b) Statutory Demand Notice (30 Days)",
                "statute": "Section 138(b) NI Act",
                "authority": "Central Bank of India v. Saxons Farms (1999)",
                "completed": bool(notice_date) or case_data.get("notice_sent", False),
                "date": notice_date,
                "defect": notice_defect,
                "severity": "FATAL" if notice_defect else "NONE"
            },
            {
                "id": "payment_grace_window",
                "name": "15-Day Statutory Grace Window for Payment",
                "statute": "Section 138(c) NI Act",
                "authority": "Subodh S. Salaskar v. Jayprakash M. Shah (2008)",
                "completed": bool(case_data.get("grace_period_expired", True)),
                "date": None,
                "defect": None,
                "severity": "NONE"
            },
            {
                "id": "complaint_filing",
                "name": "Section 142 Criminal Complaint before Magistrate (1 Month)",
                "statute": "Section 142(1)(b) NI Act",
                "authority": "Yogendra Pratap Singh v. Savitri Pandey (2014)",
                "completed": bool(complaint_date) or case_data.get("complaint_filed", False),
                "date": complaint_date,
                "defect": complaint_defect,
                "severity": "FATAL" if complaint_defect else "NONE"
            },
            {
                "id": "interim_compensation",
                "name": "Section 143A Interim Compensation (Up to 20%)",
                "statute": "Section 143A NI Act",
                "authority": "Rakesh Ranjan Shahi v. State of UP (2024)",
                "completed": bool(case_data.get("interim_compensation_ordered")),
                "date": None,
                "defect": None,
                "severity": "NONE"
            }
        ]

        current_stage = "Pre-Notice Stage"
        if complaint_date:
            current_stage = "Magistrate Trial / Summons Stage"
        elif notice_date:
            current_stage = "Statutory Demand Window / Cause of Action"
        elif dishonour_date:
            current_stage = "Post-Dishonour Notice Drafting Window"

        return {
            "current_stage": current_stage,
            "nodes": nodes,
            "total_nodes": len(nodes),
            "completed_nodes": sum(1 for n in nodes if n["completed"])
        }

    def get_next_actions(self, case_data: Dict[str, Any], evaluation_result: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Returns prioritized next best actions for Section 138 NI Act litigation."""
        actions = []
        notice_sent = case_data.get("notice_sent") or bool(case_data.get("date_of_notice"))
        complaint_filed = case_data.get("complaint_filed") or bool(case_data.get("date_of_complaint"))
        amount = case_data.get("amount") or case_data.get("cheque_amount") or 0

        if not notice_sent:
            actions.append({
                "priority": 1,
                "action": "Draft and Dispatch Section 138 Statutory Demand Notice via Registered Post AD",
                "reason": "Must be dispatched within 30 days of receiving the bank dishonour return memo.",
                "authority": "Section 138(b) Negotiable Instruments Act, 1881"
            })
        elif notice_sent and not complaint_filed:
            actions.append({
                "priority": 1,
                "action": "File Section 138 Criminal Complaint before Judicial Magistrate",
                "reason": "File within 1 month post expiry of 15-day grace period. Invoke S.139 presumption.",
                "authority": "Section 142(1)(b) & Section 139 NI Act"
            })
            if amount > 0:
                actions.append({
                    "priority": 2,
                    "action": "File Application under Section 143A for 20% Interim Compensation",
                    "reason": "Court may order drawer to pay up to 20% of cheque amount as interim compensation upon framing of notice.",
                    "authority": "Section 143A NI Act (Rakesh Ranjan Shahi v. State of UP)"
                })
        else:
            actions.append({
                "priority": 1,
                "action": "File Application under Section 143A for 20% Interim Deposit",
                "reason": "Secure immediate interim monetary relief pending trial.",
                "authority": "Section 143A NI Act"
            })

        if case_data.get("accused_type") == "Pvt Ltd/Ltd Company" and not case_data.get("directors_named"):
            actions.append({
                "priority": 1,
                "action": "Implead Company & Active In-Charge Directors under Section 141",
                "reason": "Failure to implead company or state specific role of directors is fatal to prosecution.",
                "authority": "Section 141 NI Act (Anita Hada v. Godfather Travels)"
            })

        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_data["case_type"] = "cheque_bounce"
        if concepts is None:
            concepts = case_data.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(case_data, concepts)
        scoring = ScoringEngineV12.calculate_score_with_trace(case_data, concepts, contradictions, {}, {})
        
        instance = cls()
        procedural_graph = instance.build_procedural_graph(case_data)
        next_actions = instance.get_next_actions(case_data, scoring)

        return {
            **scoring,
            "domain": "cheque_bounce",
            "procedural_graph": procedural_graph,
            "next_actions": next_actions,
            "contradictions": contradictions
        }
