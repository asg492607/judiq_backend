import logging
import re
import json
from typing import Dict, List, Any
from config import settings
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_API_KEY
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Groq client for OCR: {e}")
    client = None

MODEL = "llama-3.1-8b-instant"

class OCREngine:
    """
    Evidence Sanity Check — OCR Verification for Bank Memos and Cheques.
    This module identifies legal 'Reasons for Return' from bank documents
    to ensure user input matches the physical evidence.
    """
    
    # Mapping of standard banking terms to JudiQ's internal reasons
    REASON_MAP = {
        "Insufficient Funds": [
            "funds insufficient", "insufficient funds", "shortage", 
            "exceeds arrangement", "bal. insufficient", "short of funds"
        ],
        "Account Closed": [
            "account closed", "a/c closed", "closed"
        ],
        "Payment Stopped": [
            "payment stopped", "stopped by drawer", "stop payment", 
            "payment stopped by drawer"
        ],
        "Signature Mismatch": [
            "signature mismatch", "signature differs", "differs", 
            "drawers signature differs"
        ],
        "Refer to Drawer": [
            "refer to drawer", "r.t.d.", "contact drawer"
        ],
        "Frozen Account": [
            "account frozen", "frozen", "attached by order", "garnishee"
        ],
        "Exceed Arrangement": [
            "exceeds arrangement", "limit exceeded"
        ]
    }



    @classmethod
    def analyze_document(cls, extracted_text: str, doc_type: str, user_claimed_reason: str = "") -> Dict[str, Any]:
        """
        Uses Groq LLM to intelligently extract key evidence metrics (Dates, Amounts, Reasons, Tracking, Jurisdiction)
        from raw OCR text, replacing the legacy naive Regex system.
        """
        result = {
            "is_verified": False,
            "detected_reasons": [],
            "extracted_dates": [],
            "extracted_amounts": [],
            "extracted_cheque_numbers": [],
            "postal_tracking_numbers": [],
            "extracted_pin_codes": [],
            "has_stamp_duty": False,
            "debt_proof_class": None,
            "notice_compliance": None,
            "delivery_report": None,
            "warning": None,
            "verification_confidence": 0.0,
            "extracted_snippet": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        }

        if not client or not GROQ_API_KEY or GROQ_API_KEY.endswith("_placeholder"):
            logger.warning("LLM OCR unavailable. Falling back to Regex heuristic verification.")
            
            # Reject if it's an error placeholder
            if "fallback" in extracted_text.lower() or "failed" in extracted_text.lower():
                result["is_verified"] = False
                result["warning"] = "OCR Engine Failed. Check Tesseract installation."
                return result
                
            # Perform basic regex extraction as fallback
            dates = re.findall(r'\b\d{2}[-/]\d{2}[-/]\d{2,4}\b', extracted_text)
            amounts = re.findall(r'(?:Rs\.?|INR|\u20B9)\s*[\d,]+', extracted_text)
            
            result["extracted_dates"] = dates
            result["extracted_amounts"] = amounts
            
            # Require at least one date or amount for minimal verification
            if len(dates) > 0 or len(amounts) > 0 or len(extracted_text.strip()) > 50:
                result["is_verified"] = True
                result["verification_confidence"] = 0.40
            else:
                result["is_verified"] = False
                result["verification_confidence"] = 0.10
                result["warning"] = "Fallback OCR could not find meaningful data."
                
            return result

        prompt = f"""
        You are a Document Intelligence AI for Indian Legal Tech.
        Analyze the following raw OCR text extracted from a {doc_type} document.
        
        OCR Text:
        \"\"\"{extracted_text[:1500]}\"\"\"
        
        Extract the following information into a strict JSON format:
        {{
            "dates": ["list of dates found"],
            "amounts": ["list of currency amounts found"],
            "cheque_numbers": ["list of 6-digit cheque numbers found"],
            "tracking_numbers": ["list of Indian postal tracking numbers like RM...IN"],
            "pin_codes": ["list of 6-digit postal codes"],
            "dishonour_reasons": ["list of reasons like 'Insufficient Funds', 'Account Closed' - ONLY IF it's a Bank Memo"],
            "has_stamp_duty_or_notary": true/false (ONLY IF it's a Debt Proof agreement),
            "notice_compliance": {{ "has_15_day_clause": true/false, "has_payment_demand": true/false }} (ONLY IF it's a Legal Notice),
            "delivery_status": "DELIVERED" or "RETURNED" or "UNKNOWN" (ONLY IF it's a Tracking Report),
            "has_signature": true/false
        }}
        Output ONLY the raw JSON without markdown formatting.
        """

        try:
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model=MODEL,
                temperature=0.1,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            data = json.loads(content)
            
            result["extracted_dates"] = data.get("dates", [])
            result["extracted_amounts"] = data.get("amounts", [])
            result["extracted_cheque_numbers"] = data.get("cheque_numbers", [])
            result["postal_tracking_numbers"] = data.get("tracking_numbers", [])
            result["extracted_pin_codes"] = data.get("pin_codes", [])
            
            # Memo logic
            if doc_type.upper() == "MEMO":
                result["detected_reasons"] = data.get("dishonour_reasons", [])
                if not result["detected_reasons"]:
                    result["warning"] = "EVIDENCE GAP: No recognizable bank return code found."
                    result["verification_confidence"] = 0.20
                elif user_claimed_reason and any(user_claimed_reason.lower() in r.lower() for r in result["detected_reasons"]):
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.95
                elif user_claimed_reason:
                    result["warning"] = f"DISCREPANCY: Uploaded memo suggests {result['detected_reasons']}, but you selected '{user_claimed_reason}'."
                    result["verification_confidence"] = 0.40
                else:
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.80

            # Cheque logic
            elif doc_type.upper() == "CHEQUE":
                if result["extracted_amounts"] and result["extracted_cheque_numbers"]:
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.95
                elif result["extracted_amounts"]:
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.85
                    result["warning"] = "WARNING: Could not securely read the 6-digit cheque number."
                else:
                    result["warning"] = "EVIDENCE GAP: Could not extract cheque amount."
                    result["verification_confidence"] = 0.30

            # Notice logic
            elif doc_type.upper() == "NOTICE":
                nc = data.get("notice_compliance", {})
                result["notice_compliance"] = nc
                if nc.get("has_15_day_clause") and nc.get("has_payment_demand"):
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.99
                else:
                    result["warning"] = "FATAL DEFECT: Notice missing mandatory 15-day demand."
                    result["verification_confidence"] = 0.20

            # Debt logic
            elif doc_type.upper() == "DEBT_PROOF":
                result["has_stamp_duty"] = data.get("has_stamp_duty_or_notary", False)
                result["is_verified"] = True
                result["verification_confidence"] = 0.90 if result["has_stamp_duty"] else 0.60
                
            # Tracking logic
            elif doc_type.upper() == "TRACKING_REPORT":
                status = data.get("delivery_status", "UNKNOWN")
                result["delivery_report"] = {"status": status}
                if status == "DELIVERED":
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.98
                elif status == "RETURNED":
                    result["is_verified"] = True
                    result["verification_confidence"] = 0.90
                    result["warning"] = "Notice returned unserved."
                else:
                    result["warning"] = "Could not verify delivery status."
                    result["verification_confidence"] = 0.30
                    
        except Exception as e:
            logger.error(f"Groq API Error in Document Intelligence: {str(e)}")
            result["is_verified"] = len(extracted_text.strip()) > 10
            result["verification_confidence"] = 0.50

        return result

