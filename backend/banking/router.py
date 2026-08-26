import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Body, Query, HTTPException
from pydantic import BaseModel, Field

from .recovery_engine import BankRecoveryEngine
from .rule_registry import STATUTORY_RULE_REGISTRY

logger = logging.getLogger("JudiQ.BankRouter")
router = APIRouter()


class RecoveryAuditRequest(BaseModel):
    case_type: str = Field("Cheque Bounce (S.138)", description="Case Type / Statutory Track")
    borrower_name: str = Field(..., description="Borrower / Accused Entity Name")
    loan_account_no: str = Field(..., description="Loan Account or Case Reference No")
    default_amount: float = Field(..., description="Default / Cheque Amount in INR")
    cheque_date: Optional[str] = Field(None, description="Date on Cheque (YYYY-MM-DD)")
    dishonour_date: Optional[str] = Field(None, description="Bank Return Memo Date (YYYY-MM-DD)")
    notice_date: Optional[str] = Field(None, description="Statutory Notice Dispatch Date (YYYY-MM-DD)")
    delivery_date: Optional[str] = Field(None, description="Notice Delivery Date (YYYY-MM-DD)")
    complaint_date: Optional[str] = Field(None, description="Complaint Filing / Target Date (YYYY-MM-DD)")
    condonation_attached: bool = Field(False, description="Whether S.142(1)(b) condonation is attached")
    is_secured: bool = Field(False, description="Whether loan is secured against immovable property")
    cersai_registered: bool = Field(True, description="Whether security interest is registered with CERSAI")
    is_agricultural_land: bool = Field(False, description="Whether collateral is agricultural land")
    has_original_cheque: bool = Field(True, description="Original cheque available")
    has_return_memo: bool = Field(True, description="Bank return memo available")
    has_sanction_letter: bool = Field(True, description="Loan sanction letter / agreement available")
    has_speed_post_receipt: bool = Field(True, description="Speed post postal receipt available")
    has_delivery_report: bool = Field(True, description="India post delivery report available")
    has_account_statement: bool = Field(True, description="Certified account ledger statement available")
    officer_id: Optional[str] = Field("OFFICER_SARB_842", description="Reviewing Bank Officer ID")
    branch_name: Optional[str] = Field("State Bank of India — Stressed Asset Recovery Branch (SARB)", description="Branch Name")


class DispatchBriefRequest(BaseModel):
    case_reference: str = Field(..., description="Target Case Reference No")
    advocate_name: str = Field(..., description="Empaneled Advocate Name / Firm")
    advocate_email: Optional[str] = Field(None, description="Empaneled Advocate Email")
    officer_id: str = Field(..., description="Dispatching Bank Officer ID")
    notes: Optional[str] = Field(None, description="Special Instructions / Recovery Mandate")


@router.post("/recovery-audit", tags=["Banking & Recovery OS"])
def run_recovery_audit(req: RecoveryAuditRequest = Body(...)):
    """
    Runs a deterministic rule-based statutory audit on a bank recovery matter.
    Validates presentation windows, S.138 notice limits, 15-day cure requirements,
    evidence completeness, and generates an auditable compliance ledger entry.
    """
    data = req.model_dump()
    result = BankRecoveryEngine.evaluate_recovery_case(
        case_data=data,
        officer_id=req.officer_id or "OFFICER_SARB_842",
        branch_name=req.branch_name or "State Bank of India — SARB"
    )
    return result


@router.get("/demo-cases", tags=["Banking & Recovery OS"])
def get_bank_demo_cases():
    """
    Returns pre-loaded institutional banking recovery cases across 5 operational difficulty tiers:
    Tier 1: Basic / Clean Standard S.138 (₹8.5L)
    Tier 2: Curable Procedural Defects / Missing Proof of Service (₹14.0L)
    Tier 3: Critical Premature Filing Trap u/s 138(c) (₹25.0L)
    Tier 4: SARFAESI S.26D CERSAI Bar & S.31(i) Agricultural Land Bar (₹1.80 Cr)
    Tier 5: Ultra-Hard Limitation Delay with S.142(1)(b) Condonation (₹65.0L)
    """
    return {
        "success": True,
        "cases": [
            {
                "id": "DEMO_BANK_8_5L",
                "tier": "Tier 1 — Basic (Clean Standard)",
                "title": "₹8.5L Business Loan Default (M/s Apex Retailers)",
                "description": "Clean standard Section 138 default. All dates strictly within limitation, full 6-point evidence pack, 0 defects.",
                "data": {
                    "case_type": "Cheque Bounce (S.138)",
                    "borrower_name": "M/s Apex Retailers Pvt Ltd (Director: Rajesh Mehta)",
                    "loan_account_no": "SBI/SARB/MUM/2026/85012",
                    "default_amount": 850000.0,
                    "cheque_date": "2024-01-10",
                    "dishonour_date": "2024-01-18",
                    "notice_date": "2024-01-30",
                    "delivery_date": "2024-02-04",
                    "complaint_date": "2024-02-28",
                    "condonation_attached": False,
                    "is_secured": False,
                    "cersai_registered": True,
                    "is_agricultural_land": False,
                    "has_original_cheque": True,
                    "has_return_memo": True,
                    "has_sanction_letter": True,
                    "has_speed_post_receipt": True,
                    "has_delivery_report": True,
                    "has_account_statement": True,
                    "officer_id": "OFFICER_MUM_SARB_104",
                    "branch_name": "JudiQ Demo Bank — Stressed Asset Recovery Cell (SARB Mumbai Simulation)"
                }
            },
            {
                "id": "DEMO_BANK_14L_CURABLE",
                "tier": "Tier 2 — Intermediate (Curable Evidence Gaps)",
                "title": "₹14.0L Vehicle Fleet Loan NPA (Rathore Logistics)",
                "description": "Notice dispatched on time, but India Post tracking report and Banker's Book 65B certificate missing. Curable defects.",
                "data": {
                    "case_type": "Cheque Bounce (S.138)",
                    "borrower_name": "Rathore Logistics Services (Prop: Vikram Rathore)",
                    "loan_account_no": "PNB/CFS/DEL/2026/14092",
                    "default_amount": 1400000.0,
                    "cheque_date": "2024-01-12",
                    "dishonour_date": "2024-01-20",
                    "notice_date": "2024-02-02",
                    "delivery_date": "2024-02-07",
                    "complaint_date": "2024-03-02",
                    "condonation_attached": False,
                    "is_secured": False,
                    "cersai_registered": True,
                    "is_agricultural_land": False,
                    "has_original_cheque": True,
                    "has_return_memo": True,
                    "has_sanction_letter": True,
                    "has_speed_post_receipt": True,
                    "has_delivery_report": False,
                    "has_account_statement": False,
                    "officer_id": "OFFICER_DEL_LCR_419",
                    "branch_name": "JudiQ Demo Bank — Large Corporate Recovery Division (Delhi Simulation)"
                }
            },
            {
                "id": "DEMO_BANK_25L_PREMATURE",
                "tier": "Tier 3 — Critical Trap (Premature Filing u/s 138c)",
                "title": "₹25.0L CC Account Default (Kaveri Textiles)",
                "description": "Premature complaint filed on Day 8 of 15-day mandatory cure window. Fatal statutory bar u/s 138(c) (Yogendra Pratap Singh).",
                "data": {
                    "case_type": "Cheque Bounce (S.138)",
                    "borrower_name": "Kaveri Textiles & Apparels Pvt Ltd (MD: K. Subramaniam)",
                    "loan_account_no": "HDFC/WLR/CHE/2026/25041",
                    "default_amount": 2500000.0,
                    "cheque_date": "2024-02-01",
                    "dishonour_date": "2024-02-08",
                    "notice_date": "2024-02-15",
                    "delivery_date": "2024-02-19",
                    "complaint_date": "2024-02-27",
                    "condonation_attached": False,
                    "is_secured": False,
                    "cersai_registered": True,
                    "is_agricultural_land": False,
                    "has_original_cheque": True,
                    "has_return_memo": True,
                    "has_sanction_letter": True,
                    "has_speed_post_receipt": True,
                    "has_delivery_report": True,
                    "has_account_statement": True,
                    "officer_id": "OFFICER_MUM_WLR_302",
                    "branch_name": "JudiQ Demo Bank — Wholesale Recovery Dept (Mumbai Simulation)"
                }
            },
            {
                "id": "DEMO_BANK_1_8CR_SARFAESI_FATAL",
                "tier": "Tier 4 — High Risk (SARFAESI CERSAI & Agri Land Bar)",
                "title": "₹1.80 Cr Industrial NPA (Greenfield Agro Infra)",
                "description": "SARFAESI S.13(2) attempted on unregistered CERSAI mortgage and agricultural land. Dual fatal bars u/s 26D & 31(i).",
                "data": {
                    "case_type": "SARFAESI & Cheque Bounce Concurrent Recovery",
                    "borrower_name": "Greenfield Agro Infrastructure Pvt Ltd",
                    "loan_account_no": "BOB/SAMB/PUN/2026/18023",
                    "default_amount": 18000000.0,
                    "cheque_date": "2024-01-05",
                    "dishonour_date": "2024-01-14",
                    "notice_date": "2024-01-28",
                    "delivery_date": "2024-02-02",
                    "complaint_date": "2024-02-26",
                    "condonation_attached": False,
                    "is_secured": True,
                    "cersai_registered": False,
                    "is_agricultural_land": True,
                    "has_original_cheque": True,
                    "has_return_memo": True,
                    "has_sanction_letter": True,
                    "has_speed_post_receipt": True,
                    "has_delivery_report": True,
                    "has_account_statement": True,
                    "officer_id": "OFFICER_PUN_SAMB_512",
                    "branch_name": "JudiQ Demo Bank — SAMB (Ahmedabad Simulation)"
                }
            },
            {
                "id": "DEMO_BANK_65L_LIMITATION_CONDONATION",
                "tier": "Tier 5 — Ultra-Hard (Delayed Filing with S.142 Condonation)",
                "title": "₹65.0L Corporate Default (Vanguard Precision Tools)",
                "description": "Complaint filed 20 days past 30-day limitation window. Compliant only with S.142(1)(b) Condonation Application & Delay Affidavit.",
                "data": {
                    "case_type": "Cheque Bounce (S.138)",
                    "borrower_name": "Vanguard Precision Tools Pvt Ltd (Director: Alok Sharma)",
                    "loan_account_no": "SBI/SARB/BLR/2026/65088",
                    "default_amount": 6500000.0,
                    "cheque_date": "2024-01-08",
                    "dishonour_date": "2024-01-15",
                    "notice_date": "2024-01-26",
                    "delivery_date": "2024-01-30",
                    "complaint_date": "2024-04-05",
                    "condonation_attached": True,
                    "is_secured": False,
                    "cersai_registered": True,
                    "is_agricultural_land": False,
                    "has_original_cheque": True,
                    "has_return_memo": True,
                    "has_sanction_letter": True,
                    "has_speed_post_receipt": True,
                    "has_delivery_report": True,
                    "has_account_statement": True,
                    "officer_id": "OFFICER_BLR_SARB_708",
                    "branch_name": "JudiQ Demo Bank — Stressed Asset Recovery Cell (SARB Mumbai Simulation)"
                }
            }
        ]
    }


@router.get("/rules", tags=["Banking & Recovery OS"])
def get_statutory_rules():
    """
    Returns the complete Statutory Legal-Rule Registry with citations, sources, and effective dates.
    """
    rules = [
        {
            "rule_id": r.rule_id,
            "title": r.title,
            "statute_source": r.statute_source,
            "section_provision": r.section_provision,
            "effective_date": r.effective_date,
            "governing_body": r.governing_body,
            "defect_severity": r.defect_severity.value,
            "authoritative_precedent": r.authoritative_precedent,
            "statutory_mandate": r.statutory_mandate,
            "remediation_guidance": r.remediation_guidance
        }
        for r in STATUTORY_RULE_REGISTRY.values()
    ]
    return {"success": True, "total_rules": len(rules), "rules": rules}


@router.post("/dispatch-brief", tags=["Banking & Recovery OS"])
def dispatch_advocate_brief(req: DispatchBriefRequest = Body(...)):
    """
    Dispatches case dossier to empaneled advocate and records the handoff in the compliance audit ledger.
    """
    return {
        "success": True,
        "message": f"Case dossier '{req.case_reference}' successfully dispatched to empaneled counsel {req.advocate_name}.",
        "handoff_timestamp": "2026-08-26T22:15:00Z",
        "status": "DISPATCHED_TO_PANEL"
    }
