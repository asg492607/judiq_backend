"""
JudiQ AI — Civil Suit Classifier & Procedural Milestones Engine
Maps civil suits into procedural tracks (Commercial, Order 37, Specific Performance, Partition, Execution).
"""

from typing import Dict, Any, List

class CivilSuitClassifier:
    """
    Classifies civil suit typology and constructs stateful procedural milestone graphs.
    """

    SUIT_TYPES = {
        "commercial_suit": "Commercial Suit (Commercial Courts Act, 2015)",
        "order_37_summary": "Summary Suit under Order XXXVII CPC",
        "specific_performance": "Suit for Specific Performance (Specific Relief Act, 1963)",
        "money_recovery": "Money Recovery Suit / Breach of Contract (Section 73 ICA)",
        "declaration_injunction": "Suit for Declaration & Permanent Injunction (Section 34/38 SRA)",
        "partition_possession": "Suit for Partition, Possession & Mesne Profits (O.XX R.18 CPC)",
        "execution_petition": "Execution Petition under Order XXI CPC"
    }

    @classmethod
    def classify(cls, case_data: Dict[str, Any]) -> str:
        st = str(case_data.get("suit_type") or case_data.get("case_type") or "").lower()
        if "summary" in st or "order 37" in st or "o.37" in st:
            return "order_37_summary"
        if "specific performance" in st:
            return "specific_performance"
        if "commercial" in st or bool(case_data.get("is_commercial")):
            return "commercial_suit"
        if "partition" in st:
            return "partition_possession"
        if "declaration" in st or "injunction" in st:
            return "declaration_injunction"
        if "execution" in st or "order 21" in st or "o.21" in st:
            return "execution_petition"
        return "money_recovery"

    @classmethod
    def build_procedural_graph(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        suit_type_key = cls.classify(case_data)
        stage = str(case_data.get("stage") or "Pleadings Stage")

        if suit_type_key == "commercial_suit":
            nodes = [
                {
                    "id": "s12a_pims",
                    "name": "Section 12A Pre-Institution Mediation (PIMS)",
                    "statute": "Section 12A Commercial Courts Act, 2015",
                    "authority": "Patil Automation v. Rakheja Engineers (2022) 10 SCC 1",
                    "completed": bool(case_data.get("s12a_mediation") or case_data.get("urgent_interim_relief_prayed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "plaint_and_sot",
                    "name": "Commercial Plaint & Statement of Truth",
                    "statute": "Order VI Rule 15A & Order VII Rule 1 CPC",
                    "authority": "SCG Contracts (India) Pvt Ltd (2019)",
                    "completed": bool(case_data.get("plaint_filed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "interim_injunction",
                    "name": "Order XXXIX Injunction Hearing (3-Prong Test)",
                    "statute": "Order XXXIX Rules 1 & 2 CPC",
                    "authority": "Dalpat Kumar v. Prahlad Singh (1992)",
                    "completed": bool(case_data.get("injunction_decided")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "written_statement_120d",
                    "name": "Written Statement Filing (Strict 120-Day Limit)",
                    "statute": "Order VIII Rule 1 CPC Proviso",
                    "authority": "SCG Contracts v. K.S. Chamankar (2019) 12 SCC 210",
                    "completed": bool(case_data.get("written_statement_filed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "case_management",
                    "name": "Case Management Hearing & Trial Schedule",
                    "statute": "Order XV-A CPC (Commercial Courts Act)",
                    "authority": "Order XV-A Rule 1 CPC",
                    "completed": bool(case_data.get("issues_framed") or case_data.get("case_management_held")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "commercial_judgment",
                    "name": "Pronouncement of Judgment (Within 90 Days)",
                    "statute": "Order XX Rule 1 CPC & Section 13 CCA",
                    "authority": "Section 13 Commercial Courts Act, 2015",
                    "completed": bool(case_data.get("decreed")),
                    "defect": None,
                    "severity": "NONE"
                }
            ]
        elif suit_type_key == "order_37_summary":
            nodes = [
                {
                    "id": "summary_plaint",
                    "name": "Presentation of Summary Plaint",
                    "statute": "Order XXXVII Rule 2 CPC",
                    "authority": "Order XXXVII Rule 1(2) CPC",
                    "completed": bool(case_data.get("plaint_filed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "summons_for_judgment",
                    "name": "Service of Summons for Judgment",
                    "statute": "Order XXXVII Rule 3(4) CPC",
                    "authority": "IDBI Trusteeship v. Hubtown (2017)",
                    "completed": bool(case_data.get("summons_served")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "leave_to_defend",
                    "name": "Leave to Defend Adjudication (10 Days)",
                    "statute": "Order XXXVII Rule 3(5) CPC",
                    "authority": "IDBI Trusteeship Services v. Hubtown Ltd (2017) 1 SCC 568",
                    "completed": bool(case_data.get("leave_to_defend_decided")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "summary_decree",
                    "name": "Summary Money Decree / Trial Referral",
                    "statute": "Order XXXVII Rule 3(6) CPC",
                    "authority": "Order XXXVII Rule 3(6) CPC",
                    "completed": bool(case_data.get("decreed")),
                    "defect": None,
                    "severity": "NONE"
                }
            ]
        elif suit_type_key == "specific_performance":
            nodes = [
                {
                    "id": "notice_of_breach",
                    "name": "Notice of Performance / Readiness Tender",
                    "statute": "Section 16(c) Specific Relief Act, 1963",
                    "authority": "U.N. Krishnamurthy v. A.M. Krishnamurthy (2022)",
                    "completed": bool(case_data.get("tender_notice_sent")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "sp_plaint_filing",
                    "name": "Specific Performance Plaint & Valuation",
                    "statute": "Section 10 SRA & Section 7(x) Court Fees Act",
                    "authority": "B. Santoshamma v. D. Sarala (2020) 19 SCC 80",
                    "completed": bool(case_data.get("plaint_filed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "status_quo_injunction",
                    "name": "Order XXXIX Status Quo on Possession & Alienation",
                    "statute": "Order XXXIX Rules 1 & 2 CPC",
                    "authority": "Dalpat Kumar v. Prahlad Singh (1992)",
                    "completed": bool(case_data.get("injunction_granted")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "readiness_trial",
                    "name": "Trial on Continuous Readiness & Willingness",
                    "statute": "Section 16(c) SRA & Order XVIII CPC",
                    "authority": "U.N. Krishnamurthy (2022)",
                    "completed": bool(case_data.get("evidence_closed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "execution_conveyance",
                    "name": "Specific Performance Decree & Deed Execution",
                    "statute": "Order XXI Rule 34 CPC",
                    "authority": "Order XXI Rule 34 CPC",
                    "completed": bool(case_data.get("decreed")),
                    "defect": None,
                    "severity": "NONE"
                }
            ]
        else:
            nodes = [
                {
                    "id": "plaint_filing",
                    "name": "Plaint Presentation & Valuation",
                    "statute": "Order VII Rule 1 CPC & Court Fees Act",
                    "authority": "Section 26 CPC",
                    "completed": bool(case_data.get("plaint_filed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "written_statement",
                    "name": "Written Statement Filing (Order VIII Rule 1 CPC)",
                    "statute": "Order VIII Rule 1 CPC",
                    "authority": "Kailash v. Nanhku (2005) 4 SCC 480",
                    "completed": bool(case_data.get("written_statement_filed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "framing_issues",
                    "name": "Framing of Issues & Preliminary Objections",
                    "statute": "Order XIV Rules 1 & 2 CPC",
                    "authority": "Order XIV CPC",
                    "completed": bool(case_data.get("issues_framed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "evidence_stage",
                    "name": "Trial Evidence & Cross Examination",
                    "statute": "Order XVIII Rule 4 CPC",
                    "authority": "Order XVIII CPC",
                    "completed": bool(case_data.get("evidence_closed")),
                    "defect": None,
                    "severity": "NONE"
                },
                {
                    "id": "final_decree",
                    "name": "Judgment, Decree & Execution (Order XX/XXI CPC)",
                    "statute": "Order XX & XXI CPC",
                    "authority": "Rahul S. Shah v. Jinendra Gandhi (2021) 6 SCC 418",
                    "completed": bool(case_data.get("decreed")),
                    "defect": None,
                    "severity": "NONE"
                }
            ]

        return {
            "suit_type_key": suit_type_key,
            "suit_type_label": cls.SUIT_TYPES.get(suit_type_key, "Ordinary Civil Suit"),
            "current_stage": stage,
            "nodes": nodes,
            "total_nodes": len(nodes),
            "completed_nodes": sum(1 for n in nodes if n["completed"])
        }
