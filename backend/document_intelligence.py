import re
import logging
from typing import Dict, Any
logger = logging.getLogger(__name__)
class VisionProvider:
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
                    "forensic_flags": {}                                                            
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
        data = {
            "bank_name": None,
            "cheque_number": None,
            "return_reason": None,
            "return_date": None,
            "confidence_score": 0.0,
            "is_valid_s138_trigger": False
        }
        chq_match = re.search(r"(?:Cheque|Chq|No)\.?\s*#?(\d{6})", raw_text, re.I)
        if chq_match:
            data["cheque_number"] = chq_match.group(1)
            data["confidence_score"] += 0.25
        for code, reason in cls.REASON_CODES.items():
            if f"Code {code}" in raw_text or reason.lower() in raw_text.lower():
                data["return_reason"] = reason
                data["is_valid_s138_trigger"] = True
                data["confidence_score"] += 0.4
                break
        date_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{2,4})", raw_text)
        if date_match:
            data["return_date"] = date_match.group(1)
            data["confidence_score"] += 0.25
        banks = ["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "PUNJAB NATIONAL", "CANARA"]
        for bank in banks:
            if bank in raw_text.upper():
                data["bank_name"] = bank
                data["confidence_score"] += 0.1
                break
        return data
    @classmethod
    def perform_forensic_audit(cls, doc_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
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
        verification_flags = {
            "fraudulent_input_detected": False,
            "verification_penalties": 0,
            "overrides": {}
        }
        evidence_texts = case_data.get("evidence_texts", {})
        if not evidence_texts or not any(val and str(val).strip() for val in evidence_texts.values()):
            return verification_flags
        try:
            from ocr_engine import OCREngine
        except ImportError:
            OCREngine = None
        claimed_amount = str(case_data.get("cheque_amount") or case_data.get("amount", ""))
        cheque_text = str(evidence_texts.get("cheque") or "").lower()
        ocr_confidence = 100 if len(cheque_text) > 50 else (len(cheque_text) * 2)
        if claimed_amount and cheque_text and OCREngine:
            amounts = OCREngine.extract_amounts(cheque_text)
            clean_claimed = claimed_amount.replace(",", "").split(".")[0]
            clean_extracted = [a.replace(",", "").split(".")[0] for a in amounts]
            if clean_claimed not in clean_extracted:
                if ocr_confidence < 80:
                    verification_flags["verification_penalties"] -= 10
                    logger.warning(f"[!] MANUAL REVIEW REQUIRED: Claimed Amount {claimed_amount} not found, but OCR confidence is {ocr_confidence}%.")
                else:
                    verification_flags["fraudulent_input_detected"] = True
                    verification_flags["verification_penalties"] -= 40
                    logger.error(f"[!] STRICT ENFORCEMENT: Claimed Amount {claimed_amount} NOT FOUND in Cheque OCR.")
        claimed_chq_no = str(case_data.get("cheque_number", ""))
        if claimed_chq_no and cheque_text and OCREngine:
            extracted_chq_nos = OCREngine.extract_cheque_numbers(cheque_text)
            if extracted_chq_nos and claimed_chq_no not in extracted_chq_nos:
                if ocr_confidence < 80:
                    verification_flags["verification_penalties"] -= 5
                    logger.warning(f"[!] MANUAL REVIEW REQUIRED: Cheque No. {claimed_chq_no} not found, OCR confidence {ocr_confidence}%.")
                else:
                    verification_flags["verification_penalties"] -= 25
                    logger.error(f"[!] STRICT ENFORCEMENT: Claimed Cheque No. {claimed_chq_no} NOT FOUND in Cheque OCR.")
        claimed_chq_date = str(case_data.get("cheque_date", ""))
        if claimed_chq_date and cheque_text and OCREngine:
            extracted_dates = OCREngine.extract_dates(cheque_text)
            if extracted_dates:
                year_claimed = claimed_chq_date.split("-")[0] if "-" in claimed_chq_date else claimed_chq_date[-4:]
                year_found = any(year_claimed in d for d in extracted_dates)
                if not year_found:
                    if ocr_confidence < 80:
                        verification_flags["verification_penalties"] -= 5
                        logger.warning(f"[!] MANUAL REVIEW REQUIRED: Cheque Year {year_claimed} not found, OCR confidence {ocr_confidence}%.")
                    else:
                        verification_flags["verification_penalties"] -= 20
                        logger.error(f"[!] STRICT ENFORCEMENT: Claimed Cheque Year {year_claimed} NOT FOUND in Cheque OCR.")
        if case_data.get("complainant_itr_available"):
            itr_text = str(evidence_texts.get("itr") or "").lower()
            if itr_text:
                if not any(k in itr_text for k in ["income tax", "assessment year", "return of income", "pan", "acknowledgement"]):
                    verification_flags["fraudulent_input_detected"] = True
                    verification_flags["verification_penalties"] -= 30
                    verification_flags["overrides"]["complainant_itr_available"] = False
                    logger.error("[!] STRICT ENFORCEMENT: User claimed ITR, but OCR found no valid tax document.")
        if case_data.get("notice_sent"):
            tracking_text = str(evidence_texts.get("tracking_report") or "").lower()
            user_tracking_status = str(case_data.get("notice_delivery_status", "")).lower()
            tracking_confidence = 100 if len(tracking_text) > 30 else (len(tracking_text) * 3)
            if ("delivered" in user_tracking_status or "refused" in user_tracking_status) and not tracking_text:
                verification_flags["verification_penalties"] -= 10
                logger.warning("[!] MANUAL REVIEW REQUIRED: User claims delivery, but provided no tracking report OCR.")
            elif tracking_text and OCREngine:
                status_obj = OCREngine.verify_delivery_status(tracking_text)
                if status_obj["is_returned"]:
                    if tracking_confidence < 80:
                        logger.warning("[!] MANUAL REVIEW REQUIRED: Tracking says returned, confidence low.")
                    else:
                        verification_flags["overrides"]["notice_delivery_status"] = "Not Found / Returned"
                        verification_flags["verification_penalties"] -= 20
                elif "not found" in tracking_text or "insufficient address" in tracking_text:
                    if tracking_confidence >= 80:
                        verification_flags["overrides"]["notice_delivery_status"] = "Not Found"
                        verification_flags["verification_penalties"] -= 20
        if not case_data.get("handwriting_different"):
            if "ink mismatch" in cheque_text or "signature differs" in cheque_text or "anomaly detected" in cheque_text:
                verification_flags["overrides"]["handwriting_different"] = True
                verification_flags["fraudulent_input_detected"] = True
                verification_flags["verification_penalties"] -= 25
                logger.error("[!] STRICT ENFORCEMENT: Forensic mismatch detected despite user denial.")
        if case_data.get("dishonour_reason"):
            memo_text = str(evidence_texts.get("memo") or "").lower()
            user_reason = str(case_data.get("dishonour_reason", "")).lower()
            memo_confidence = 100 if len(memo_text) > 40 else (len(memo_text) * 2)
            if memo_text and OCREngine:
                memo_analysis = OCREngine.analyze_document(memo_text, "MEMO", user_reason)
                if memo_analysis["detected_reasons"]:
                    reason_matched = False
                    for dr in memo_analysis["detected_reasons"]:
                        if user_reason and (dr.lower() in user_reason or user_reason in dr.lower()):
                            reason_matched = True
                            break
                    if not reason_matched:
                        if memo_confidence < 80:
                            verification_flags["verification_penalties"] -= 10
                            logger.warning(f"[!] MANUAL REVIEW REQUIRED: Memo OCR detected {memo_analysis['detected_reasons']}, but user claimed '{user_reason}'.")
                        else:
                            verification_flags["verification_penalties"] -= 35
                            verification_flags["fraudulent_input_detected"] = True
                            logger.error(f"[!] STRICT ENFORCEMENT: Memo OCR detected {memo_analysis['detected_reasons']}, but user claimed '{user_reason}'.")
                else:
                    if "insufficient" not in memo_text and "exceed" not in memo_text and "signature" not in memo_text and "closed" not in memo_text and "stop" not in memo_text:
                        verification_flags["verification_penalties"] -= 10
        return verification_flags
doc_intel = DocumentIntelligence()
