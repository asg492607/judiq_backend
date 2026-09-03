"""
JudiQ AI — Master Section 138 NI Act Cheque Bounce Engine
Production-grade Domain Engine for Negotiable Instruments Act (1881) litigation.
Evaluates statutory notices, debt enforceability, S.139/S.118 presumptions,
S.141 director liability, S.142(2) jurisdiction, S.143A interim compensation, S.148 appellate deposits.
"""

from typing import Dict, List, Any
from core.base_domain_engine import BaseDomainEngine
from scoring_engine import ScoringEngineV12
from adversarial_engine import AdversarialEngine
from utils import days_between, parse_date
from cheque_bounce.ni_act_statutory_rules import NIActStatutoryRules
from cheque_bounce.defence_catalogue import Section138DefenceCatalogue

class ChequeBounceEngine(BaseDomainEngine):
    """
    Production-grade Domain Engine for Section 138 Negotiable Instruments Act (1881) litigation.
    """

    @property
    def domain_name(self) -> str:
        return "cheque_bounce"

    def build_procedural_graph(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Returns stateful graph of Section 138 NI Act statutory milestones."""
        norm = NIActStatutoryRules.normalize_s138_payload(case_data)
        cheque_date = norm.get("cheque_date")
        presentation_date = norm.get("presentation_date")
        dishonour_date = norm.get("dishonour_date")
        notice_date = norm.get("notice_date")
        complaint_date = norm.get("complaint_date")

        # 1. Cheque Presentation Validity (RBI 90 Days)
        cheque_defect = None
        if cheque_date and presentation_date:
            eval_chk = NIActStatutoryRules.evaluate_cheque_validity(cheque_date, presentation_date)
            if not eval_chk["valid"]:
                cheque_defect = eval_chk["defect"]

        # 2. Notice Timeline (30 Days)
        notice_defect = None
        notice_days = case_data.get("notice_days")
        if notice_days is not None:
            eval_notice = NIActStatutoryRules.evaluate_notice_timeline(notice_days)
            if not eval_notice["valid"]:
                notice_defect = eval_notice["defect"]
        elif dishonour_date and notice_date:
            d = days_between(dishonour_date, notice_date)
            if d is not None:
                eval_notice = NIActStatutoryRules.evaluate_notice_timeline(d)
                if not eval_notice["valid"]:
                    notice_defect = eval_notice["defect"]

        # 3. Complaint Timeline (15 Grace + 30 Filing)
        complaint_defect = None
        days_post_notice = case_data.get("days_post_notice")
        if days_post_notice is not None:
            eval_complaint = NIActStatutoryRules.evaluate_complaint_timeline(days_post_notice)
            if not eval_complaint["valid"]:
                complaint_defect = eval_complaint["defect"]
        elif notice_date and complaint_date:
            d = days_between(notice_date, complaint_date)
            if d is not None:
                eval_complaint = NIActStatutoryRules.evaluate_complaint_timeline(d)
                if not eval_complaint["valid"]:
                    complaint_defect = eval_complaint["defect"]

        nodes = [
            {
                "id": "cheque_issuance_presentation",
                "name": "Cheque Presentation (Within 3 Months / 90 Days)",
                "statute": "Section 138 Proviso (a) NI Act & RBI 2011-12",
                "authority": "Section 138(a) NI Act",
                "completed": bool(presentation_date) or bool(dishonour_date) or case_data.get("dishonour_memo", False),
                "date": presentation_date or cheque_date,
                "defect": cheque_defect,
                "severity": "FATAL" if cheque_defect else "NONE"
            },
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
                "statute": "Section 142(1)(b) & Section 142(2) NI Act",
                "authority": "Yogendra Pratap Singh v. Savitri Pandey (2014)",
                "completed": bool(complaint_date) or case_data.get("complaint_filed", False) or days_post_notice is not None,
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
        if complaint_date or days_post_notice is not None:
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
        norm = NIActStatutoryRules.normalize_s138_payload(case_data)
        notice_sent = bool(norm.get("notice_date")) or case_data.get("notice_sent")
        complaint_filed = bool(norm.get("complaint_date")) or case_data.get("complaint_filed")
        amount = norm.get("cheque_amount", 0.0)

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
                "action": "File Section 138 Criminal Complaint before Judicial Magistrate (Payee Branch Jurisdiction)",
                "reason": "File within 1 month post expiry of 15-day grace period u/s 142(1)(b) & Section 142(2) (Bridgestone India).",
                "authority": "Section 142(1)(b) & Section 142(2) NI Act"
            })
            if amount > 0:
                interim_estimate = NIActStatutoryRules.calculate_interim_compensation_estimate(amount)
                actions.append({
                    "priority": 2,
                    "action": f"File Application under Section 143A for 20% Interim Compensation (Est: ₹{interim_estimate:,.2f})",
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

        accused_type = norm.get("accused_type", "")
        company_arrayed = case_data.get("company_arrayed")
        directors_named = case_data.get("directors_named")
        vicarious_eval = NIActStatutoryRules.evaluate_vicarious_liability(accused_type, company_arrayed, directors_named)
        if not vicarious_eval["valid"]:
            actions.append({
                "priority": 1,
                "action": "Implead Company & Active In-Charge Directors under Section 141",
                "reason": vicarious_eval["defect"],
                "authority": "Section 141 NI Act (Aneeta Hada v. Godfather Travels)"
            })

        return actions

    @classmethod
    def analyze(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        norm = NIActStatutoryRules.normalize_s138_payload(case_data)
        norm["case_type"] = "cheque_bounce"
        if concepts is None:
            concepts = norm.get("concepts", [])
        contradictions = AdversarialEngine.detect_contradictions(norm, concepts)
        scoring = ScoringEngineV12.calculate_score_with_trace(norm, concepts, contradictions, {}, {})
        
        instance = cls()
        procedural_graph = instance.build_procedural_graph(norm)
        next_actions = instance.get_next_actions(norm, scoring)
        defenses = Section138DefenceCatalogue.analyze_case_defenses(norm)

        cheque_amount = norm.get("cheque_amount", 0.0)
        interim_compensation = NIActStatutoryRules.calculate_interim_compensation_estimate(cheque_amount)
        appellate_deposit = NIActStatutoryRules.calculate_appellate_deposit_estimate(cheque_amount)
        jurisdiction_info = NIActStatutoryRules.evaluate_s142_jurisdiction(
            payee_branch=norm.get("branch_name") or norm.get("payee_branch"),
            drawer_branch=norm.get("drawer_branch")
        )

        return {
            **scoring,
            "domain": "cheque_bounce",
            "procedural_graph": procedural_graph,
            "next_actions": next_actions,
            "contradictions": contradictions,
            "identified_defenses": defenses,
            "interim_compensation_estimate": interim_compensation,
            "appellate_deposit_estimate": appellate_deposit,
            "territorial_jurisdiction_rule": jurisdiction_info,
            "statutory_authorities": NIActStatutoryRules.LANDMARK_PRECEDENTS
        }
