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
            # Simulated forensic metadata for demo
            return {
                "text": "Sample OCR Text: Cheque #882104, Reason Code 1, HDFC Bank.",
                "forensic_flags": {
                    "ink_age_mismatch": True,
                    "signature_velocity_anomalous": False
                }
            }
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

    @classmethod
    def validate_claims(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cross-checks user frontend inputs against Document Engine metadata.
        Returns a verification flags object used to override user honesty.
        """
        verification_flags = {
            "fraudulent_input_detected": False,
            "verification_penalties": 0,
            "overrides": {}
        }
        
        # 1. ITR Claim vs OCR Validation
        if case_data.get("complainant_itr_available"):
            # Mock OCR check: if user claims ITR but we didn't receive an ITR doc or it's unreadable
            itr_ocr_valid = case_data.get("_debug_itr_ocr_valid", True) # Default true for tests, but mock hook here
            if not itr_ocr_valid:
                verification_flags["fraudulent_input_detected"] = True
                verification_flags["verification_penalties"] -= 25
                verification_flags["overrides"]["complainant_itr_available"] = False
                logger.warning("Document Engine Override: User claimed ITR available, but OCR found no valid ITR.")

        # 2. Notice Delivery vs Postal API
        if case_data.get("notice_sent"):
            tracking_status = str(case_data.get("notice_delivery_status", "delivered")).lower()
            if "not found" in tracking_status or "returned to sender" in tracking_status:
                verification_flags["overrides"]["notice_received"] = "No"
            elif "refused" in tracking_status or "unclaimed" in tracking_status:
                verification_flags["overrides"]["notice_received"] = "Deemed Served (S.27 General Clauses Act)"
                
        # 3. Handwriting Forensic Override
        # If user claims 'handwriting_different = False' but Tesseract/Forensic detects anomaly
        forensic_mock_anomaly = case_data.get("_debug_forensic_anomaly", False)
        if forensic_mock_anomaly and not case_data.get("handwriting_different"):
            verification_flags["overrides"]["handwriting_different"] = True
            verification_flags["verification_penalties"] -= 15
            logger.warning("Forensic Override: Detected different ink age despite user claim.")

        return verification_flags

# Global Instance
doc_intel = DocumentIntelligence()
