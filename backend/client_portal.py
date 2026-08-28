"""
JudiQ Client Portal & Communication Hub Engine
Provides client-facing case tracking, timeline milestones, document upload checklists,
hearing calendars, and transparent recovery progress updates.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger("JudiQ.ClientPortal")


class ClientMilestone(BaseModel):
    milestone_id: str
    title: str
    stage: str  # "PRE_NOTICE", "STATUTORY_NOTICE", "FILING", "SUMMONS", "INTERIM_RELIEF", "EVIDENCE", "JUDGMENT", "RECOVERY"
    status: str  # "COMPLETED", "IN_PROGRESS", "PENDING", "ACTION_REQUIRED"
    target_date: str
    completed_date: Optional[str] = None
    statutory_provision: str
    lawyer_note: str


class DocumentChecklistItem(BaseModel):
    document_id: str
    document_title: str
    mandatory_for_statutory_admissibility: bool
    status: str  # "VERIFIED", "UPLOADED_PENDING_REVIEW", "ACTION_REQUIRED_MISSING", "REJECTED_DEFECTIVE"
    statutory_purpose: str
    upload_date: Optional[str] = None
    defect_notes: Optional[str] = None


class ClientCaseDossier(BaseModel):
    case_access_token: str
    case_id: str
    case_title: str
    client_name: str
    client_email: str
    lead_advocate_name: str
    advocate_contact: str
    court_forum: str
    presiding_judge: str
    claim_amount: float
    current_status_summary: str
    next_hearing_date: Optional[str] = None
    next_hearing_purpose: Optional[str] = None
    action_required_from_client: Optional[str] = None
    milestones: List[ClientMilestone]
    document_checklist: List[DocumentChecklistItem]
    recovery_received_amount: float
    interim_deposit_secured: float
    fee_invoiced: float
    fee_paid: float
    last_updated: str


# In-memory store for client dossiers (seeded with institutional template)
CLIENT_DOSSIERS_STORE: Dict[str, ClientCaseDossier] = {
    "CLIENT_TKN_2026_01": ClientCaseDossier(
        case_access_token="CLIENT_TKN_2026_01",
        case_id="CC-BLR-2026-8912",
        case_title="Complainant Enterprise v. Accused Debtor Entity",
        client_name="Complainant Enterprise (Attn: Authorized Officer)",
        client_email="legal.desk@enterprise-client.in",
        lead_advocate_name="Designated Panel Counsel",
        advocate_contact="counsel.desk@legalpanel.in",
        court_forum="Special Court for Economic Offences, CMM Court",
        presiding_judge="Presiding Metropolitan Magistrate",
        claim_amount=2450000.0,
        current_status_summary="Summons issued to Accused Directors; Section 143A application filed for 20% interim deposit.",
        next_hearing_date="2026-09-15",
        next_hearing_purpose="Framing of Notice of Accusation & Hearing on Section 143A 20% Deposit Application",
        action_required_from_client="Provide physical signed copy of Banker's Books Evidence Affidavit.",
        milestones=[
            ClientMilestone(
                milestone_id="M1",
                title="Statutory Demand Notice Dispatched",
                stage="STATUTORY_NOTICE",
                status="COMPLETED",
                target_date="2026-01-25",
                completed_date="2026-01-22",
                statutory_provision="Section 138(b) Negotiable Instruments Act",
                lawyer_note="Dispatched via Speed Post with AD to all 3 registered corporate addresses."
            ),
            ClientMilestone(
                milestone_id="M2",
                title="15-Day Cure Window Monitored",
                stage="STATUTORY_NOTICE",
                status="COMPLETED",
                target_date="2026-02-08",
                completed_date="2026-02-08",
                statutory_provision="Section 138(c) Negotiable Instruments Act",
                lawyer_note="No payment received. Cause of action crystallized on Day 16 (2026-02-09)."
            ),
            ClientMilestone(
                milestone_id="M3",
                title="Criminal Complaint Filed before Magistrate",
                stage="FILING",
                status="COMPLETED",
                target_date="2026-03-05",
                completed_date="2026-02-24",
                statutory_provision="Section 142(1)(b) NI Act (Filed on Day 16 of limitation)",
                lawyer_note="Complaint registered under CC No. 8912/2026."
            ),
            ClientMilestone(
                milestone_id="M4",
                title="Pre-Summoning Sworn Statement & S.143A Petition",
                stage="INTERIM_RELIEF",
                status="COMPLETED",
                target_date="2026-04-10",
                completed_date="2026-04-02",
                statutory_provision="Section 143A NI Act (20% Interim Compensation)",
                lawyer_note="Complainant affidavit tendered; Court issued summons to Managing Director."
            ),
            ClientMilestone(
                milestone_id="M5",
                title="Accused Appearance & Framing of Notice",
                stage="SUMMONS",
                status="IN_PROGRESS",
                target_date="2026-09-15",
                statutory_provision="Section 251 CrPC / Section 274 BNSS",
                lawyer_note="Accused counsel has appeared; order on 20% interim deposit pending next date."
            ),
            ClientMilestone(
                milestone_id="M6",
                title="Complainant Cross-Examination & Defense Evidence",
                stage="EVIDENCE",
                status="PENDING",
                target_date="2026-11-20",
                statutory_provision="Section 145(2) NI Act",
                lawyer_note="Will tender certified ledger statements and Delivery Challans."
            ),
            ClientMilestone(
                milestone_id="M7",
                title="Final Judgment & Conviction",
                stage="JUDGMENT",
                status="PENDING",
                target_date="2027-02-15",
                statutory_provision="Section 138 NI Act (Double Cheque Amount + Imprisonment)",
                lawyer_note="Targeting full claim recovery plus statutory interest."
            )
        ],
        document_checklist=[
            DocumentChecklistItem(
                document_id="DOC_01",
                document_title="Original Dishonoured Cheque (Leaf #809123)",
                mandatory_for_statutory_admissibility=True,
                status="VERIFIED",
                statutory_purpose="Substantive Negotiable Instrument corpus under Section 138",
                upload_date="2026-01-15"
            ),
            DocumentChecklistItem(
                document_id="DOC_02",
                document_title="Bank Return Memo with CTS Reason Code",
                mandatory_for_statutory_admissibility=True,
                status="VERIFIED",
                statutory_purpose="Section 146 NI Act presumption of dishonour",
                upload_date="2026-01-18"
            ),
            DocumentChecklistItem(
                document_id="DOC_03",
                document_title="Speed Post Receipt & India Post Delivery Track Report",
                mandatory_for_statutory_admissibility=True,
                status="VERIFIED",
                statutory_purpose="Proof of Section 138(b) demand notice delivery under Section 27 GCA",
                upload_date="2026-01-26"
            ),
            DocumentChecklistItem(
                document_id="DOC_04",
                document_title="Sworn Custodian Affidavit for Electronic Account Statements",
                mandatory_for_statutory_admissibility=True,
                status="ACTION_REQUIRED_MISSING",
                statutory_purpose="Mandatory electronic evidence certification under Arjun Panditrao (2020) / Sec. 63 BSA",
                defect_notes="Client must sign and notarize the template generated by JudiQ."
            )
        ],
        recovery_received_amount=0.0,
        interim_deposit_secured=490000.0,  # 20% of ₹24.5L
        fee_invoiced=75000.0,
        fee_paid=50000.0,
        last_updated="2026-08-28"
    )
}


class ClientPortalService:
    """
    Service for retrieving and updating client portal dossiers.
    """

    @classmethod
    def get_dossier_by_token(cls, token: str) -> Optional[ClientCaseDossier]:
        return CLIENT_DOSSIERS_STORE.get(token)

    @classmethod
    def get_dossier_by_case_id(cls, case_id: str) -> Optional[ClientCaseDossier]:
        for d in CLIENT_DOSSIERS_STORE.values():
            if d.case_id == case_id:
                return d
        return None

    @classmethod
    def record_client_document_upload(cls, token: str, document_id: str, file_name: str) -> Dict[str, Any]:
        dossier = CLIENT_DOSSIERS_STORE.get(token)
        if not dossier:
            raise ValueError("Invalid client access token.")

        for item in dossier.document_checklist:
            if item.document_id == document_id:
                item.status = "UPLOADED_PENDING_REVIEW"
                item.upload_date = datetime.now().strftime("%Y-%m-%d")
                dossier.last_updated = datetime.now().strftime("%Y-%m-%d")
                return {
                    "success": True,
                    "message": f"Document '{item.document_title}' uploaded successfully and queued for advocate review.",
                    "document_id": document_id,
                    "status": item.status
                }

        raise ValueError(f"Document ID '{document_id}' not found in case checklist.")
