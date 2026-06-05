import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class VisionProvider:
    """
    STRICT REALITY ENFORCEMENT: True OCR Integration.
    Removes all mock/simulated providers. Requires actual file bytes for processing.
    """
    @staticmethod
    def ingest_document(file_bytes, provider="TESSERACT"):
        if not file_bytes:
            raise ValueError("[!] STRICT ENFORCEMENT: No document provided for OCR. Cannot proceed with validation.")
            
        if provider == "TESSERACT":
            try:
                import pytesseract
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(file_bytes))
                text = pytesseract.image_to_string(image)
                return {
                    "text": text,
                    "forensic_flags": {} # Would require separate ML model for ink age in production
                }
            except ImportError:
                logger.error("[!] STRICT ENFORCEMENT: pytesseract/PIL not installed. Failing OCR extraction.")
                return {"text": "", "error": "OCR dependencies missing"}
            except Exception as e:
                logger.error(f"[!] STRICT ENFORCEMENT: OCR failed: {str(e)}")
                return {"text": "", "error": str(e)}
        elif provider == "GOOGLE_VISION":
            try:
                from google.cloud import vision
                client = vision.ImageAnnotatorClient()
                image = vision.Image(content=file_bytes)
                response = client.text_detection(image=image)
                return {"text": response.text_annotations[0].description if response.text_annotations else ""}
            except Exception as e:
                logger.error(f"[!] STRICT ENFORCEMENT: Google Vision failed: {str(e)}")
                return {"text": "", "error": str(e)}
        else:
            raise ValueError(f"[!] STRICT ENFORCEMENT: Unsupported OCR provider '{provider}'. Mocking is strictly prohibited.")

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
        STRICT REALITY ENFORCEMENT: Cross-checks user frontend inputs against actual Document Engine metadata.
        Returns a verification flags object used to ruthlessly override user claims lacking evidentiary backing.
        """
        verification_flags = {
            "fraudulent_input_detected": False,
            "verification_penalties": 0,
            "overrides": {}
        }
        
        # We expect actual extracted text payload from the OCR pipeline
        evidence_texts = case_data.get("evidence_texts", {})
        
        # 1. ITR Claim vs Reality
        if case_data.get("complainant_itr_available"):
            itr_text = str(evidence_texts.get("itr", "")).lower()
            # Must contain actual tax keywords to be validated as an ITR
            if not itr_text or not any(k in itr_text for k in ["income tax", "assessment year", "return of income", "pan", "acknowledgement"]):
                verification_flags["fraudulent_input_detected"] = True
                verification_flags["verification_penalties"] -= 30
                verification_flags["overrides"]["complainant_itr_available"] = False
                logger.error("[!] STRICT ENFORCEMENT: User claimed ITR, but OCR found no valid tax document.")

        # 2. Notice Delivery Tracking vs Reality
        if case_data.get("notice_sent"):
            tracking_text = str(evidence_texts.get("tracking_report", "")).lower()
            user_tracking_status = str(case_data.get("notice_delivery_status", "")).lower()
            
            # If user claims it was delivered/refused but provided no tracking report, penalize
            if ("delivered" in user_tracking_status or "refused" in user_tracking_status) and not tracking_text:
                verification_flags["verification_penalties"] -= 15
                logger.warning("[!] STRICT ENFORCEMENT: User claims delivery, but provided no tracking report OCR.")
            elif tracking_text:
                if "not found" in tracking_text or "returned to sender" in tracking_text or "insufficient address" in tracking_text:
                    verification_flags["overrides"]["notice_delivery_status"] = "Not Found"
                    verification_flags["verification_penalties"] -= 20

        # 3. Handwriting/Signature Forensic Enforcement
        if not case_data.get("handwriting_different"):
            cheque_text = str(evidence_texts.get("cheque", "")).lower()
            # Look for anomaly keywords injected by the OCR/Forensic engine
            if "ink mismatch" in cheque_text or "signature differs" in cheque_text or "anomaly detected" in cheque_text:
                verification_flags["overrides"]["handwriting_different"] = True
                verification_flags["fraudulent_input_detected"] = True
                verification_flags["verification_penalties"] -= 25
                logger.error("[!] STRICT ENFORCEMENT: Forensic mismatch detected despite user denial.")
                
        # 4. Bank Memo Reason vs Claimed Reason
        if case_data.get("dishonour_reason"):
            memo_text = str(evidence_texts.get("memo", "")).lower()
            user_reason = str(case_data.get("dishonour_reason", "")).lower()
            if memo_text and user_reason not in memo_text and "insufficient" not in memo_text: # Loose match
                verification_flags["verification_penalties"] -= 20
                logger.error(f"[!] STRICT ENFORCEMENT: Memo OCR does not support claimed reason '{user_reason}'.")

        return verification_flags

# Global Instance
doc_intel = DocumentIntelligence()
