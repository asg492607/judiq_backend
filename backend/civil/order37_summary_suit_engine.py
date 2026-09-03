"""
JudiQ AI — Order XXXVII CPC Summary Suits Engine
Evaluates qualifying negotiable debt instruments, 10-day leave to defend limitations,
and Hubtown adjudication principles (Unconditional vs Conditional Leave vs Immediate Decree).
"""

from typing import Dict, Any, List

class Order37SummarySuitEngine:
    """
    Evaluates Summary Suits under Order XXXVII of the Code of Civil Procedure, 1908.
    """

    QUALIFYING_INSTRUMENTS = {
        "bill_of_exchange": "Bills of Exchange / Hundies (Order XXXVII Rule 1(2)(a))",
        "promissory_note": "Promissory Notes (Order XXXVII Rule 1(2)(a))",
        "written_contract_debt": "Written Contract for Liquidated Debt (Order XXXVII Rule 1(2)(b)(i))",
        "guarantee_debt": "Guarantees where claim against principal is in respect of a liquidated debt (Order XXXVII Rule 1(2)(b)(ii))"
    }

    LEAVE_TO_DEFEND_LIMITATION_DAYS = 10

    @classmethod
    def evaluate_summary_suit(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates instrument qualification and Leave to Defend standard under Hubtown principles.
        """
        instr_type = str(case_data.get("order37_instrument_type") or case_data.get("instrument_type") or "").lower()
        is_qualifying = any(k in instr_type for k in ["bill", "hundi", "promissory", "written contract", "guarantee", "liquidated"])

        leave_days = case_data.get("leave_to_defend_days")
        defense_nature = str(case_data.get("defense_nature") or case_data.get("leave_to_defend_merit") or "").lower()

        leave_granted_category = None
        leave_condition = None
        plaintiff_immediate_decree = False
        trace = []

        # 1. Limitation Check for Leave to Defend (10 Days u/O 37 R 3(5))
        if leave_days is not None:
            if leave_days > cls.LEAVE_TO_DEFEND_LIMITATION_DAYS:
                trace.append(f"Leave to defend filed on day {leave_days} (Statutory Limit: 10 days u/O 37 R 3(5)). Delay condonation application u/O 37 R 3(7) mandatory.")
                if not case_data.get("condonation_applied"):
                    plaintiff_immediate_decree = True
                    leave_granted_category = "LEAVE_REFUSED_TIMELINE_BAR"
                    trace.append("PLAINTIFF DECREE ENTITLEMENT: Failure to apply for leave within 10 days entitles Plaintiff to immediate decree under Order XXXVII Rule 3(6)(a) CPC.")

        # 2. Hubtown Principles (IDBI Trusteeship Services v. Hubtown Ltd (2017) 1 SCC 568)
        if not plaintiff_immediate_decree:
            if any(k in defense_nature for k in ["substantial", "genuine", "bona fide"]):
                leave_granted_category = "UNCONDITIONAL_LEAVE"
                leave_condition = "Defendant entitled to unconditional leave to defend suit on merits."
                trace.append("HUBTOWN PRINCIPLE 1: Defendant raises a substantial defense. Entitled to unconditional leave to defend.")
            elif any(k in defense_nature for k in ["triable", "doubtful", "plausible"]):
                leave_granted_category = "CONDITIONAL_LEAVE"
                leave_condition = "Conditional leave granted subject to depositing 20% to 50% of the suit claim into court within 4 weeks."
                trace.append("HUBTOWN PRINCIPLE 2: Triable issues raised but bona fides are doubtful. Conditional leave with monetary security deposit.")
            elif any(k in defense_nature for k in ["sham", "moonshine", "frivolous", "illusory"]):
                leave_granted_category = "LEAVE_REFUSED"
                leave_condition = "Leave to defend refused. Plaintiff entitled to judgment forthwith."
                plaintiff_immediate_decree = True
                trace.append("HUBTOWN PRINCIPLE 3: Defense is sham and moonshine. Leave refused; plaintiff entitled to immediate decree.")
            else:
                leave_granted_category = "CONDITIONAL_LEAVE"
                leave_condition = "Subject to judicial discretion based on summons for judgment hearing."

        return {
            "is_qualifying_instrument": is_qualifying,
            "leave_to_defend_category": leave_granted_category,
            "leave_condition": leave_condition,
            "plaintiff_entitled_to_immediate_decree": plaintiff_immediate_decree,
            "adjudication_trace": trace,
            "governing_authority": "IDBI Trusteeship Services Ltd v. Hubtown Ltd (2017) 1 SCC 568",
            "statute": "Order XXXVII Code of Civil Procedure, 1908"
        }
