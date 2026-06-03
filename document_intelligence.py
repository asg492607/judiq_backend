import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VisionProvider:
    """
    Priority: OCR Integration Foundation (Decoupled Architecture)
    Abstracts the document-to-text ingestion layer.
    """
    @staticmethod
    def ingest_document(file_bytes, provider="MOCK"):
        if provider == "MOCK":
            return "Sample OCR Text: Cheque #882104, Reason Code 1, HDFC Bank."
        elif provider == "TESSERACT":
            # import pytesseract; return pytesseract.image_to_string(file_bytes)
            pass
        elif provider == "GOOGLE_VISION":
            # return cloud_vision.detect_text(file_bytes)
            pass
        return ""

class DocumentIntelligence:
    """
    Priority: Actual OCR / Document Intelligence (Moat Foundation)
    Performs forensic parsing of legal documents to extract actionable facts.
    """

    # NI Act S.138 Bank Return Reason Codes
    REASON_CODES = {
        "1": "Insufficient Funds",
        "2": "Exceeds Arrangement",
        "3": "Effects not cleared",
        "4": "Refer to Drawer",
        "5": "Account Closed",
        "6": "Stops Payment",
        "7": "Signature Differs",
        "8": "Image not found",
        "9": "Stale Cheque"
    }

    @classmethod
    def extract_memo_data(cls, raw_text: str) -> Dict[str, Any]:
        """
        Parses raw OCR text from a Bank Return Memo to extract S.138 ingredients.
        """
        data = {
            "bank_name": None,
            "cheque_number": None,
            "return_reason": None,
            "return_date": None,
            "confidence_score": 0.0,
            "is_valid_s138_trigger": False
        }

        # 1. Extract Cheque Number (6 digits)
        chq_match = re.search(r"(?:Cheque|Chq|No)\.?\s*#?(\d{6})", raw_text, re.I)
        if chq_match:
            data["cheque_number"] = chq_match.group(1)
            data["confidence_score"] += 0.25

        # 2. Extract Return Reason (Code or Text)
        for code, reason in cls.REASON_CODES.items():
            if f"Code {code}" in raw_text or reason.lower() in raw_text.lower():
                data["return_reason"] = reason
                data["is_valid_s138_trigger"] = True
                data["confidence_score"] += 0.4
                break

        # 3. Extract Date
        date_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{2,4})", raw_text)
        if date_match:
            data["return_date"] = date_match.group(1)
            data["confidence_score"] += 0.25

        # 4. Extract Bank Name
        banks = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "PUNJAB NATIONAL", "CANARA"]
        for bank in banks:
            if bank in raw_text.upper():
                data["bank_name"] = bank
                data["confidence_score"] += 0.1
                break

        return data

    @classmethod
    def perform_forensic_audit(cls, doc_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determines the 'Legal Effect' and 'Case Delta' based on extracted data.
        """
        audit = {
            "legal_effect": "Neutral",
            "case_delta": 0,
            "remediation_needed": None
        }

        if doc_type == "BANK_MEMO":
            if extracted_data.get("is_valid_s138_trigger"):
                audit["legal_effect"] = "Valid NI 138 Trigger"
                audit["case_delta"] = 5
            else:
                audit["legal_effect"] = "Ambiguous Return Reason"
                audit["remediation_needed"] = "Manually verify bank memo code."
        
        elif doc_type == "BSA_CERTIFICATE":
            audit["legal_effect"] = "S.63(4) Compliance Secured"
            audit["case_delta"] = 15

        return audit

# Global Instance
doc_intel = DocumentIntelligence()
