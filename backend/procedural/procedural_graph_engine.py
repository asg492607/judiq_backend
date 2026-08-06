import logging
from typing import Dict, List, Any
from utils import parse_date, days_between

logger = logging.getLogger(__name__)

class ProceduralGraphEngine:
    """
    Stateful Procedural Node Graph:
    NPA -> 13(2) -> 13(3A) -> 13(4) -> Sec 14 DM -> Rule 8(6) Auction -> Sec 17 SA.
    Evaluates node compliance and computes legally permissible Next-Best-Actions.
    """

    NODE_DEFINITIONS = [
        {
            "id": "node_npa",
            "name": "NPA Classification",
            "statute": "RBI IRAC Guidelines",
            "authority": "RBI Master Circular on IRAC Norms",
            "description": "Continuous 90-day overdue default required before NPA tag."
        },
        {
            "id": "node_13_2",
            "name": "Section 13(2) Demand Notice",
            "statute": "Section 13(2) SARFAESI Act",
            "authority": "Transcore v. Union of India (2008)",
            "description": "60-day mandatory demand notice to clear liabilities."
        },
        {
            "id": "node_13_3a",
            "name": "Section 13(3A) Objection & Decision",
            "statute": "Section 13(3A) SARFAESI Act",
            "authority": "Mardia Chemicals Ltd. v. UOI (2004)",
            "description": "Mandatory 15-day reasoned decision on borrower's representation."
        },
        {
            "id": "node_13_4",
            "name": "Section 13(4) Possession Measure",
            "statute": "Section 13(4) & Rule 8 Security Interest Rules",
            "authority": "Mathew Varghese v. M. Amritha Kumar (2014)",
            "description": "Symbolic possession & Rule 8(2) 2-newspaper publication."
        },
        {
            "id": "node_sec_14",
            "name": "Section 14 DM/CMM Order Execution",
            "statute": "Section 14 SARFAESI Act",
            "authority": "Standard Chartered Bank v. V. Noble Kumar (2013)",
            "description": "Application for physical possession assistance from DM/CMM."
        },
        {
            "id": "node_auction",
            "name": "Rule 8(6)/9(1) Sale Auction Notice",
            "statute": "Rule 8(6) & Rule 9(1) Security Interest Rules",
            "authority": "Celir LLP v. Bafna Motors (2023)",
            "description": "Mandatory 30-day public auction notice to borrower."
        },
        {
            "id": "node_sec_17_sa",
            "name": "Section 17 Securitisation Application (DRT)",
            "statute": "Section 17(1) SARFAESI Act",
            "authority": "B. Arvind Kumar v. Govt. of India (2007)",
            "description": "Strict 45-day limitation period for borrower SA before DRT."
        }
    ]

    @classmethod
    def build_graph(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        nodes = []
        npa_date = case_data.get("npa_date")
        notice_13_2 = case_data.get("notice_13_2_date")
        rep_date = case_data.get("borrower_representation_date")
        reply_date = case_data.get("bank_reply_13_3a_date")
        possession_date = case_data.get("possession_13_4_date")
        dm_date = case_data.get("dm_application_date") or case_data.get("dm_order_date")
        auction_date = case_data.get("auction_notice_date")
        sa_date = case_data.get("sa_filing_date")

        # 1. NPA Node
        nodes.append({
            "id": "node_npa",
            "name": "NPA Classification",
            "required": True,
            "completed": bool(npa_date),
            "date": npa_date,
            "supporting_document": "NPA Classification Record",
            "authority": "RBI IRAC Guidelines",
            "defect": None,
            "severity": "LOW"
        })

        # 2. 13(2) Notice Node
        notice_defect = None
        if case_data.get("notice_withdrawn"):
            notice_defect = "Notice WITHDRAWN by Lender; fresh 60-day demand notice required."
        elif case_data.get("partial_payment_received"):
            notice_defect = f"Partial Payment of ₹{case_data.get('partial_payment_amount', 0)} accepted post-notice; ledger recalculation required."

        nodes.append({
            "id": "node_13_2",
            "name": "Section 13(2) Demand Notice",
            "required": True,
            "completed": bool(notice_13_2) and not case_data.get("notice_withdrawn"),
            "date": case_data.get("reissued_notice_date") or notice_13_2,
            "supporting_document": "Section 13(2) Demand Notice & Postal AD",
            "authority": "Section 13(2) SARFAESI Act",
            "defect": notice_defect,
            "severity": "HIGH" if notice_defect else "LOW"
        })

        # 3. 13(3A) Node
        rep_defect = None
        if rep_date and not reply_date and possession_date:
            rep_defect = "Failure to communicate reasoned decision on Section 13(3A) representation."
        elif rep_date and reply_date:
            d = days_between(rep_date, reply_date)
            if d is not None and d > 15:
                rep_defect = f"Section 13(3A) reply delayed to {d} days (Statutory limit: 15 days)."

        nodes.append({
            "id": "node_13_3a",
            "name": "Section 13(3A) Objection & Decision",
            "required": bool(rep_date),
            "completed": bool(reply_date),
            "date": reply_date,
            "supporting_document": "Section 13(3A) Reasoned Decision Letter",
            "authority": "Mardia Chemicals Ltd. v. UOI (2004)",
            "defect": rep_defect,
            "severity": "FATAL" if rep_defect else "NONE"
        })

        # 4. 13(4) Possession Node
        poss_defect = None
        if notice_13_2 and possession_date:
            d = days_between(notice_13_2, possession_date)
            if d is not None and d < 60:
                poss_defect = f"Section 13(4) action taken prematurely in {d} days (60 days required)."

        nodes.append({
            "id": "node_13_4",
            "name": "Section 13(4) Possession Measure",
            "required": True,
            "completed": bool(possession_date),
            "date": possession_date,
            "supporting_document": "Section 13(4) Possession Notice & Newspaper Tear-sheets",
            "authority": "Rule 8(1) & 8(2) Security Interest Rules",
            "defect": poss_defect,
            "severity": "HIGH" if poss_defect else "NONE"
        })

        # 5. Section 14 DM Node
        nodes.append({
            "id": "node_sec_14",
            "name": "Section 14 DM/CMM Order Execution",
            "required": False,
            "completed": bool(dm_date),
            "date": dm_date,
            "supporting_document": "Section 14 DM Order Affidavit",
            "authority": "Standard Chartered Bank v. V. Noble Kumar (2013)",
            "defect": None,
            "severity": "NONE"
        })

        # 6. Auction Node
        nodes.append({
            "id": "node_auction",
            "name": "Rule 8(6)/9(1) Sale Auction Notice",
            "required": False,
            "completed": bool(auction_date),
            "date": auction_date,
            "supporting_document": "Auction Notice & Valuer Report",
            "authority": "Celir LLP v. Bafna Motors (2023)",
            "defect": None,
            "severity": "NONE"
        })

        # 7. DRT SA 17 Node
        sa_defect = None
        if possession_date and sa_date:
            d = days_between(possession_date, sa_date)
            if d is not None and d > 45:
                sa_defect = f"Securitisation Application filed in DRT after {d} days (45 days limit)."

        nodes.append({
            "id": "node_sec_17_sa",
            "name": "Section 17 Securitisation Application (DRT)",
            "required": is_borrower,
            "completed": bool(sa_date),
            "date": sa_date,
            "supporting_document": "DRT Securitisation Application Petition",
            "authority": "B. Arvind Kumar v. Govt. of India (2007)",
            "defect": sa_defect,
            "severity": "FATAL" if (sa_defect and is_borrower) else "NONE"
        })

        current_stage = "NPA"
        if case_data.get("drt_stay_active") or case_data.get("interim_stay_granted"):
            current_stage = "STAYED / DRT INJUNCTION ACTIVE"
        elif sa_date:
            current_stage = "DRT Litigation U/S 17"
        elif auction_date:
            current_stage = "Auction / Public Sale"
        elif dm_date:
            current_stage = "Section 14 Physical Possession"
        elif possession_date:
            current_stage = "Section 13(4) Possession"
        elif reply_date:
            current_stage = "Section 13(3A) Reply Completed"
        elif notice_13_2:
            current_stage = "Section 13(2) Demand Window"

        return {
            "current_stage": current_stage,
            "nodes": nodes,
            "total_nodes": len(nodes),
            "completed_nodes": sum(1 for n in nodes if n["completed"])
        }

    @classmethod
    def determine_next_best_actions(cls, case_data: Dict[str, Any], evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions = []
        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        notice_13_2 = case_data.get("notice_13_2_date")
        rep_date = case_data.get("borrower_representation_date")
        reply_date = case_data.get("bank_reply_13_3a_date")
        possession_date = case_data.get("possession_13_4_date")
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        has_stay = case_data.get("drt_stay_active") or case_data.get("interim_stay_granted")

        if not is_borrower:
            # Bank Mode Actions
            if has_stay:
                actions.append({
                    "priority": 1,
                    "action": "File Application for Vacating Interim Stay Order before DRT",
                    "reason": "DRT interim order currently restricts enforcement; bank must seek vacation of stay before proceeding to physical possession or auction.",
                    "authority": "Section 17(7) SARFAESI Act read with DRT Rules"
                })
                return actions

            if not cersai:
                actions.append({
                    "priority": 1,
                    "action": "Register Security Interest on CERSAI Portal Immediately",
                    "reason": "Section 26D imposes absolute statutory bar on Chapter III enforcement without CERSAI registration.",
                    "authority": "Section 26D SARFAESI Act"
                })

            if rep_date and not reply_date:
                actions.append({
                    "priority": 1,
                    "action": "Issue Reasoned Reply U/S 13(3A) to Borrower Objections",
                    "reason": "Must communicate decision within 15 days to avoid vitiating future Section 13(4) possession.",
                    "authority": "Mardia Chemicals Ltd. v. UOI (2004)"
                })

            if notice_13_2 and not possession_date:
                actions.append({
                    "priority": 2,
                    "action": "Issue Section 13(4) Possession Notice & Publish in 2 Newspapers",
                    "reason": "60-day demand window elapsed; proceed to symbolic/physical possession.",
                    "authority": "Rule 8(1) & 8(2) Security Interest Rules"
                })

            if possession_date and not case_data.get("dm_order_date"):
                actions.append({
                    "priority": 3,
                    "action": "File Section 14 Application before Magistrate/DM for Physical Possession",
                    "reason": "Secure police assistance to take actual physical possession of mortgaged asset.",
                    "authority": "Section 14 SARFAESI Act"
                })
        else:
            # Borrower Mode Actions
            if possession_date and not case_data.get("sa_filing_date"):
                actions.append({
                    "priority": 1,
                    "action": "File Section 17 Securitisation Application (SA) before DRT",
                    "reason": "Must challenge Section 13(4) measures within 45 days of possession date.",
                    "authority": "Section 17(1) SARFAESI Act"
                })

            if not cersai:
                actions.append({
                    "priority": 1,
                    "action": "Seek Interim Stay on S.13(4) Action based on Section 26D CERSAI Bar",
                    "reason": "Bank cannot enforce SARFAESI rights without prior CERSAI registration.",
                    "authority": "Section 26D SARFAESI Act"
                })

            if case_data.get("is_agricultural_land"):
                actions.append({
                    "priority": 1,
                    "action": "Pray for Immediate Quashing of Proceedings U/S 31(i) Agricultural Land Exemption",
                    "reason": "Property is agricultural land, completely exempt from SARFAESI proceedings.",
                    "authority": "ITC Ltd. v. Blue Coast Hotels Ltd. (2018)"
                })

        return actions
