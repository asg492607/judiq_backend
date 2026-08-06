import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class EvidenceIntelligenceEngine:
    """
    Evidence Intelligence Engine:
    Document -> Fact -> Statutory Requirement -> Admissibility -> Gap Analysis -> Contradiction Graph.
    """

    DOCUMENT_TYPES = {
        "LOAN_AGREEMENT": "Sanction Letter / Loan Agreement & Equitable Mortgage Deed",
        "NPA_RECORD": "NPA Classification Record (RBI IRAC Compliance)",
        "NOTICE_13_2": "Section 13(2) Statutory Demand Notice",
        "POSTAL_PROOF": "Postal Speed Post Receipts / AD Card / Tracking Report",
        "BORROWER_REP": "Borrower Representation / Objection U/S 13(3A)",
        "REASONED_REPLY_13_3A": "Secured Creditor Reasoned Reply U/S 13(3A)",
        "POSSESSION_NOTICE_13_4": "Section 13(4) Possession Notice",
        "NEWSPAPER_PUBLICATION": "Rule 8(2) Newspaper Tear-sheets (2 Newspapers: 1 Vernacular + 1 English)",
        "CERSAI_CERTIFICATE": "Section 26D CERSAI Portal Security Interest Registration Certificate",
        "VALUATION_REPORT": "Approved Valuer Property Valuation Report & Reserve Price Fixation",
        "SEC_14_DM_ORDER": "Section 14 DM/CMM Physical Possession Application & Order",
        "AUCTION_NOTICE": "Rule 8(6) & 9(1) 30-Day Public Auction Sale Notice",
        "DRT_SA_PLEADINGS": "Section 17 Securitisation Application & DRT Interim Petitions"
    }

    @classmethod
    def classify_document(cls, doc_name: str, content: str = "") -> Dict[str, Any]:
        doc_lower = (doc_name + " " + content).lower()
        if "13(2)" in doc_lower or "demand notice" in doc_lower:
            return {"type": "NOTICE_13_2", "name": cls.DOCUMENT_TYPES["NOTICE_13_2"]}
        if "13(3a)" in doc_lower or "representation" in doc_lower or "objection" in doc_lower:
            return {"type": "BORROWER_REP", "name": cls.DOCUMENT_TYPES["BORROWER_REP"]}
        if "13(4)" in doc_lower or "possession notice" in doc_lower:
            return {"type": "POSSESSION_NOTICE_13_4", "name": cls.DOCUMENT_TYPES["POSSESSION_NOTICE_13_4"]}
        if "cersai" in doc_lower:
            return {"type": "CERSAI_CERTIFICATE", "name": cls.DOCUMENT_TYPES["CERSAI_CERTIFICATE"]}
        if "newspaper" in doc_lower or "publication" in doc_lower or "tear-sheet" in doc_lower:
            return {"type": "NEWSPAPER_PUBLICATION", "name": cls.DOCUMENT_TYPES["NEWSPAPER_PUBLICATION"]}
        if "section 14" in doc_lower or "district magistrate" in doc_lower:
            return {"type": "SEC_14_DM_ORDER", "name": cls.DOCUMENT_TYPES["SEC_14_DM_ORDER"]}
        if "auction" in doc_lower or "sale notice" in doc_lower:
            return {"type": "AUCTION_NOTICE", "name": cls.DOCUMENT_TYPES["AUCTION_NOTICE"]}
        return {"type": "LOAN_AGREEMENT", "name": cls.DOCUMENT_TYPES["LOAN_AGREEMENT"]}

    @classmethod
    def evaluate_evidence_gaps(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        gaps = []
        perspective = str(case_data.get("perspective", "creditor")).lower()
        is_borrower = perspective in ["borrower", "debtor", "applicant"]

        # Gap 0A: Missing Section 13(2) Demand Notice Proof
        if not case_data.get("notice_13_2_date"):
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["NOTICE_13_2"],
                "statutory_provision": "Section 13(2) SARFAESI Act",
                "severity": "CRITICAL",
                "consequence": "No statutory 60-day demand notice recorded; mandatory pre-condition for Chapter III enforcement.",
                "remediation": "Issue statutory demand notice U/S 13(2) to borrower and guarantors."
            })

        # Gap 0B: Missing Equitable Mortgage Property Document
        if not case_data.get("property_description") and not case_data.get("mortgage_survey_number"):
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["LOAN_AGREEMENT"],
                "statutory_provision": "Section 13(2) read with Section 2(1)(zb)",
                "severity": "CRITICAL",
                "consequence": "Mortgaged property description absent; cannot establish security interest enforcement identity.",
                "remediation": "Provide registered mortgage deed / title deed schedule."
            })

        # Gap 1: CERSAI Registration Proof
        cersai = case_data.get("cersai_registered") or str(case_data.get("cersai", "")).lower() in ["yes", "true", "1"]
        if not cersai:
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["CERSAI_CERTIFICATE"],
                "statutory_provision": "Section 26D SARFAESI Act",
                "severity": "CRITICAL" if not is_borrower else "HIGH",
                "consequence": "Absolute statutory bar against secured creditor exercising Chapter III rights.",
                "remediation": "Register security interest on CERSAI portal immediately."
            })

        # Gap 2: Rule 8(2) Newspaper Publication Proof
        if case_data.get("possession_13_4_date") and not case_data.get("newspaper_publication_done"):
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["NEWSPAPER_PUBLICATION"],
                "statutory_provision": "Rule 8(2) Security Interest Rules, 2002",
                "severity": "HIGH",
                "consequence": "Possession notice invalid unless published in 2 leading newspapers (1 in vernacular language) within 7 days.",
                "remediation": "Produce newspaper tear-sheets for both English and local vernacular publications."
            })

        # Gap 3: Section 13(3A) Reasoned Reply Proof
        if case_data.get("borrower_representation_date") and not case_data.get("bank_reply_13_3a_date") and case_data.get("possession_13_4_date"):
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["REASONED_REPLY_13_3A"],
                "statutory_provision": "Section 13(3A) SARFAESI Act",
                "severity": "CRITICAL",
                "consequence": "Vitiates Section 13(4) possession measures under Mardia Chemicals landmark rule.",
                "remediation": "Issue reasoned reply rejecting objections prior to enforcing Section 13(4)."
            })

        # Gap 4: Missing Service Proof for Notice
        if case_data.get("notice_13_2_date") and (case_data.get("missing_service_proof") or case_data.get("service_proof_available") == False or case_data.get("guarantor_service_missing")):
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["POSTAL_PROOF"],
                "statutory_provision": "Section 13(2) read with Rule 3 Security Interest Rules",
                "severity": "HIGH",
                "consequence": "Notice existence without proven delivery track record fails mandatory service requirement.",
                "remediation": "Obtain postal tracking delivery certificate / signed AD card."
            })

        # Gap 5: Partial CERSAI Registration for Multiple Assets
        if case_data.get("cersai_property_b_missing"):
            gaps.append({
                "document_required": cls.DOCUMENT_TYPES["CERSAI_CERTIFICATE"],
                "statutory_provision": "Section 26D SARFAESI Act",
                "severity": "CRITICAL",
                "consequence": "Secondary property B lacks CERSAI registration, barring enforcement against Property B.",
                "remediation": "Register Property B security interest on CERSAI portal."
            })

        return gaps

    @classmethod
    def detect_cross_document_contradictions(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        contradictions = []
        npa_date = case_data.get("npa_date")
        notice_13_2 = case_data.get("notice_13_2_date")
        rep_date = case_data.get("borrower_representation_date")
        reply_date = case_data.get("bank_reply_13_3a_date")

        from utils import days_between
        if npa_date and notice_13_2:
            d = days_between(npa_date, notice_13_2)
            if d is not None and d < 0:
                contradictions.append({
                    "issue": "Section 13(2) Notice Precedes NPA Classification Date",
                    "documents_involved": [cls.DOCUMENT_TYPES["NPA_RECORD"], cls.DOCUMENT_TYPES["NOTICE_13_2"]],
                    "details": f"Demand notice date ({notice_13_2}) is earlier than NPA classification date ({npa_date}).",
                    "severity": "FATAL"
                })

        if rep_date and reply_date:
            d = days_between(rep_date, reply_date)
            if d is not None and d > 15:
                contradictions.append({
                    "issue": "Section 13(3A) Reply Beyond Statutory 15-Day Cap",
                    "documents_involved": [cls.DOCUMENT_TYPES["BORROWER_REP"], cls.DOCUMENT_TYPES["REASONED_REPLY_13_3A"]],
                    "details": f"Reply delivered in {d} days, exceeding the mandatory 15-day limit.",
                    "severity": "HIGH"
                })

        # Check Property Identity Mismatch
        p_mort = case_data.get("mortgage_property_description") or case_data.get("mortgage_survey_number")
        p_poss = case_data.get("possession_property_description") or case_data.get("possession_survey_number")
        if p_mort and p_poss and str(p_mort).strip().lower() != str(p_poss).strip().lower():
            contradictions.append({
                "issue": "Property Identity Mismatch",
                "documents_involved": [cls.DOCUMENT_TYPES["LOAN_AGREEMENT"], cls.DOCUMENT_TYPES["POSSESSION_NOTICE_13_4"]],
                "details": f"Mortgage deed references '{p_mort}' while Possession Notice references '{p_poss}'.",
                "severity": "FATAL"
            })

        # Check Outstanding Amount Conflict
        amt_notice = case_data.get("notice_amount")
        amt_ledger = case_data.get("ledger_amount")
        if amt_notice and amt_ledger and abs(float(amt_notice) - float(amt_ledger)) > 1000:
            contradictions.append({
                "issue": "Outstanding Amount Discrepancy",
                "documents_involved": [cls.DOCUMENT_TYPES["NOTICE_13_2"], cls.DOCUMENT_TYPES["NPA_RECORD"]],
                "details": f"Section 13(2) notice claims ₹{amt_notice} whereas account statement reflects ₹{amt_ledger}.",
                "severity": "HIGH"
            })

        # Check Valuation Conflict
        val_a = case_data.get("valuation_amount_a")
        val_b = case_data.get("valuation_amount_b")
        if val_a and val_b and abs(float(val_a) - float(val_b)) > 500000:
            contradictions.append({
                "issue": "Valuation Report Discrepancy",
                "documents_involved": [cls.DOCUMENT_TYPES["VALUATION_REPORT"]],
                "details": f"Valuation Report A (₹{val_a}) conflicts materially with Valuation Report B (₹{val_b}).",
                "severity": "HIGH"
            })

        # Check Service Proof Contradiction
        if case_data.get("notice_received_date") and case_data.get("postal_return_unserved_date"):
            contradictions.append({
                "issue": "Service Proof Contradiction",
                "documents_involved": [cls.DOCUMENT_TYPES["POSTAL_PROOF"]],
                "details": f"Signed AD card receipt date ({case_data.get('notice_received_date')}) conflicts with postal unserved return report ({case_data.get('postal_return_unserved_date')}).",
                "severity": "FATAL"
            })

        # Check NCLT IBC Moratorium Conflict
        if case_data.get("nclt_ibc_moratorium_active"):
            contradictions.append({
                "issue": "NCLT IBC Section 14 Moratorium Conflict",
                "documents_involved": [cls.DOCUMENT_TYPES["DRT_SA_PLEADINGS"]],
                "details": "Active NCLT CIRP Moratorium under Section 14 IBC bars all SARFAESI enforcement measures.",
                "severity": "FATAL"
            })

        return contradictions
