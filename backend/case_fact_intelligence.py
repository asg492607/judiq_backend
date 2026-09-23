"""
JudiQ AI — Document & Case Fact Intelligence
============================================
Pipeline:
  Upload → OCR → Document Classification → Fact Extraction (per-doc, with source evidence)
  → Cross-document comparison (NO silent merge — contradictions preserved)
  → Contradictions + Missing Facts/Docs (workflow-specific)
  → Auto Timeline
  → Lawyer Fact Review (mandatory)
  → Verified Facts
  → Case Story / Summary (generated ONLY from verified facts)
  → Confidence-aware Smart Fill → Existing JudiQ Analysis Engine

API Routes:
  POST /api/v1/doc-intel/extract          — Upload files → OCR → per-doc facts
  POST /api/v1/doc-intel/analyze          — Cross-doc analysis → contradictions/missing/timeline
  POST /api/v1/doc-intel/verify           — Submit lawyer-verified facts
  POST /api/v1/doc-intel/case-story       — Generate case story from VERIFIED facts only
"""

import io
import re
import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from pydantic import BaseModel, Field
from security import get_current_user_optional
from session import DatabaseManager

logger = logging.getLogger(__name__)
router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class SourceEvidence(BaseModel):
    source_document: str           # e.g. "bank_memo.pdf"
    source_page: Optional[int]     # 1-indexed page number
    source_snippet: Optional[str]  # raw text snippet (up to 200 chars) where fact was found
    confidence: float = 0.0        # 0.0 – 1.0

class ExtractedFact(BaseModel):
    field: str
    value: Optional[Any]
    evidence: List[SourceEvidence] = Field(default_factory=list)
    # Multiple evidence entries = same field found in multiple docs (possible contradiction)
    is_contradicted: bool = False
    contradiction_details: Optional[str] = None

class ExtractedDocument(BaseModel):
    document_id: str
    filename: str
    doc_type: str
    ocr_method: str                # "pdfplumber" | "pdf2image+tesseract" | "tesseract"
    page_count: int
    raw_text_preview: str          # first 500 chars for display
    facts: Dict[str, Any] = Field(default_factory=dict)          # raw extracted fields from LLM
    fact_confidences: Dict[str, float] = Field(default_factory=dict)
    fact_snippets: Dict[str, str] = Field(default_factory=dict)  # snippet for each field
    fact_pages: Dict[str, int] = Field(default_factory=dict)     # page number for each field

class Contradiction(BaseModel):
    field: str
    severity: str  # "CRITICAL" | "WARNING"
    values: List[Dict[str, Any]]   # [{doc, value, confidence, snippet}]
    description: str

class TimelineEvent(BaseModel):
    date: str
    label: str
    source_document: str
    field_name: str
    is_missing: bool = False
    is_conflicted: bool = False

class CaseFactPackage(BaseModel):
    session_id: str
    documents: List[ExtractedDocument]
    all_extracted_facts: Dict[str, List[ExtractedFact]]  # field → [all values across docs]
    contradictions: List[Contradiction]
    missing_facts: List[Dict[str, str]]    # [{field, reason, required_for}]
    missing_documents: List[Dict[str, str]] # [{doc_type, reason}]
    timeline: List[TimelineEvent]
    workflow_type: str

class VerifyPayload(BaseModel):
    session_id: str
    verified_facts: Dict[str, Any]   # field → lawyer-confirmed value
    resolved_contradictions: Optional[List[str]] = None  # fields explicitly resolved by lawyer

class CaseStoryPayload(BaseModel):
    session_id: str
    verified_facts: Optional[Dict[str, Any]] = None
    workflow_type: str = "cheque_bounce"

class AnalyzePayload(BaseModel):
    session_id: str
    workflow_type: str = "cheque_bounce"


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT TYPE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

DOC_TYPE_SIGNATURES: Dict[str, List[str]] = {
    "SECTION_138_COMPLAINT": [
        "complaint under section 138", "complaint u/s 138", "section 138 ni act",
        "section 138 of the negotiable", "in the court of the", "metropolitan magistrate",
        "judicial magistrate", "versus", "complainant", "accused", "criminal complaint",
        "formal complaint", "complaint under section", "prayer", "take cognizance",
        "verification on oath", "c.c. no", "criminal case", "complaint no"
    ],
    "INVOICE_LEDGER": [
        "tax invoice", "invoice no", "ledger account", "statement of account",
        "invoice and ledger", "bill of supply", "commercial invoice", "ledger balance",
        "debit", "credit", "balance", "part payment", "invoice date", "ledger statement",
        "particulars", "voucher no"
    ],
    "CHEQUE": [
        "cheque no", "chq no", "account payee", "a/c payee", "pay to", "payee",
        "micr", "ifsc", "drawn on", "bearer", "order", "rupees only",
        "amount in words", "in words", "date of issue"
    ],
    "BANK_MEMO": [
        "return memo", "dishonour", "dishonored", "insufficient funds", "funds insufficient",
        "exceeds arrangement", "payment stopped", "stop payment", "signature mismatch",
        "signature differs", "account closed", "a/c closed", "refer to drawer",
        "return reason", "cheque return", "unpaid", "bank return", "memo of return",
        "dishonour memo", "returned cheque"
    ],
    "LEGAL_NOTICE": [
        "legal notice", "demand notice", "statutory notice", "section 138",
        "negotiable instruments act", "15 days", "advocate for",
        "advocate on behalf", "take notice", "cause of action",
        "demand under section", "by registered post", "rpad"
    ],
    "TRACKING_REPORT": [
        "speed post", "consignment no", "consignment number", "shipment tracking",
        "india post", "postal department", "booking date", "delivery date",
        "attempted delivery", "not delivered", "tracking id", "article number",
        "dispatched on", "out for delivery", "item delivered"
    ],
    "AGREEMENT": [
        "this agreement", "memorandum of understanding", "mou", "loan agreement",
        "executed this day", "between the parties", "repayment", "borrowed",
        "interest at", "promissory note", "supply agreement", "purchase order",
        "sale agreement", "deed of", "contract"
    ],
    "COURT_ORDER": [
        "in the court of", "before the hon'ble", "before the honourable",
        "cnr", "order", "judgment", "summons", "warrant",
        "sessions court", "magistrate", "high court", "tribunal"
    ],
    "FIR": [
        "first information report", "fir no", "police station", "f.i.r",
        "information to police", "cognizable offence"
    ],
    "ITR": [
        "income tax return", "assessment year", "return of income",
        "pan", "acknowledgement", "form itr"
    ],
    "EMAIL_EXCHANGE": [
        "email chain", "email exchange", "mailbox export", "from:", "to:",
        "subject: re:", "subject:", "re:", "fwd:", "sent:", "cc:", "bcc:",
        "fictional senders", "mail", "gmail", "outlook", "email conversation",
        "email thread", "correspondence"
    ],
    "OTHER": [],
}

# Filename token map — weighted 10x over OCR keyword scores
# These are substring matches against the lowercased filename
FILENAME_TYPE_TOKENS: Dict[str, List[str]] = {
    "SECTION_138_COMPLAINT": ["complaint", "sec_138", "section_138", "s138", "complaint_section_138"],
    "INVOICE_LEDGER":        ["invoice", "ledger", "bill", "invoice_and_ledger"],
    "CHEQUE":                ["cheque", "chq", "check", "_chq", "-chq"],
    "BANK_MEMO":             ["memo", "return_memo", "bank_return", "return memo", "dishonour", "bank memo"],
    "LEGAL_NOTICE":          ["legal_notice", "demand_notice", "legal notice", "demand notice",
                              "notice", "demand"],
    "TRACKING_REPORT":       ["tracking", "postal", "speed_post", "booking", "track", "dispatch"],
    "AGREEMENT":             ["agreement", "mou", "loan", "deed", "contract", "supply", "purchase"],
    "EMAIL_EXCHANGE":        ["email", "email_exchange", "mail", "correspondence", "email_chain"],
    "COURT_ORDER":           ["order", "judgment", "summons", "warrant", "tribunal"],
    "FIR":                   ["fir", "first_information"],
    "ITR":                   ["itr", "income_tax", "tax_return"],
}


def classify_document(filename: str, ocr_text: str) -> str:
    """
    Hybrid document classifier — combines:
      1. Filename token matching (weight: 10 pts per match)
      2. OCR text keyword matching  (weight: 1 pt per keyword)
    Falls back to 'OTHER' only when no signal at all is found.
    """
    scores: Dict[str, int] = {}
    filename_lower = filename.lower()
    # Strip extension and replace separators with spaces for easier matching
    filename_clean = re.sub(r'[_\-\.]+', ' ', filename_lower)

    # --- Filename signal (high weight) ---
    for doc_type, tokens in FILENAME_TYPE_TOKENS.items():
        for token in tokens:
            # Match against both raw and cleaned filename
            if token in filename_lower or token in filename_clean:
                scores[doc_type] = scores.get(doc_type, 0) + 10

    # --- OCR text keyword signal (lower weight) ---
    if ocr_text and ocr_text.strip():
        text_lower = ocr_text.lower()
        for doc_type, keywords in DOC_TYPE_SIGNATURES.items():
            if doc_type == "OTHER":
                continue
            for kw in keywords:
                if kw in text_lower:
                    scores[doc_type] = scores.get(doc_type, 0) + 1

    if not scores:
        return "OTHER"

    best = max(scores, key=lambda k: scores[k])
    logger.debug(f"classify_document('{filename}'): scores={scores} → {best}")
    return best


# Keep old function as alias for backward compatibility
def detect_doc_type(text: str) -> str:
    """Deprecated: use classify_document(filename, text) instead."""
    return classify_document("", text)

WORKFLOW_REQUIRED_FACTS: Dict[str, List[Dict[str, str]]] = {
    "cheque_bounce": [
        {"field": "complainant_name",    "required_for": "Party Identification"},
        {"field": "accused_name",        "required_for": "Party Identification"},
        {"field": "cheque_number",       "required_for": "Cheque Evidence (S.138 NI Act)"},
        {"field": "cheque_amount",       "required_for": "Cheque Evidence (S.138 NI Act)"},
        {"field": "cheque_date",         "required_for": "Cheque Evidence (S.138 NI Act)"},
        {"field": "bank_name",           "required_for": "Cheque Evidence (S.138 NI Act)"},
        {"field": "dishonour_date",      "required_for": "Cause of Action (S.138)"},
        {"field": "dishonour_reason",    "required_for": "Cause of Action (S.138)"},
        {"field": "notice_date",         "required_for": "Statutory Notice (S.138/S.142)"},
        {"field": "notice_mode",         "required_for": "Statutory Notice (S.138/S.142)"},
        {"field": "notice_delivery_date","required_for": "Statutory Notice (S.138/S.142)"},
        {"field": "transaction_date",    "required_for": "Debt Proof"},
        {"field": "filing_date",         "required_for": "Limitation (S.142 — 30 days)"},
    ],
    "sarfaesi": [
        {"field": "borrower_name",       "required_for": "Party Identification"},
        {"field": "bank_name",           "required_for": "Secured Creditor"},
        {"field": "outstanding_amount",  "required_for": "Debt Amount"},
        {"field": "npa_date",            "required_for": "NPA Classification"},
        {"field": "notice_date",         "required_for": "S.13(2) Demand Notice"},
        {"field": "property_description","required_for": "Secured Asset"},
    ],
    "criminal": [
        {"field": "complainant_name",    "required_for": "Party Identification"},
        {"field": "accused_name",        "required_for": "Party Identification"},
        {"field": "fir_number",          "required_for": "FIR Registration"},
        {"field": "incident_date",       "required_for": "Offence Timeline"},
        {"field": "ipc_section",         "required_for": "Charges"},
    ],
    "civil": [
        {"field": "complainant_name",    "required_for": "Party Identification"},
        {"field": "accused_name",        "required_for": "Party Identification"},
        {"field": "transaction_date",    "required_for": "Agreement / Contract"},
        {"field": "cheque_amount",       "required_for": "Suit Valuation"},
    ],
}

WORKFLOW_REQUIRED_DOCS: Dict[str, List[Dict[str, str]]] = {
    "cheque_bounce": [
        {"doc_type": "CHEQUE",        "reason": "Original Cheque is primary evidence under S.138 NI Act"},
        {"doc_type": "BANK_MEMO",     "reason": "Bank Return Memo establishes dishonour — mandatory cause of action"},
        {"doc_type": "LEGAL_NOTICE",  "reason": "Statutory Demand Notice under S.138 NI Act is mandatory prerequisite"},
        {"doc_type": "TRACKING_REPORT","reason": "Proof of notice delivery / service is required for S.138 complaint"},
        {"doc_type": "AGREEMENT",     "reason": "Debt proof / transaction document supports legally enforceable debt"},
    ],
    "sarfaesi": [
        {"doc_type": "LEGAL_NOTICE",  "reason": "S.13(2) Demand Notice is the mandatory first step"},
        {"doc_type": "COURT_ORDER",   "reason": "DM Order u/s 14 or DRT proceedings may be relevant"},
        {"doc_type": "AGREEMENT",     "reason": "Loan / Mortgage Agreement establishes secured debt"},
    ],
    "criminal": [
        {"doc_type": "FIR",           "reason": "FIR is the foundation of criminal proceedings"},
    ],
    "civil": [
        {"doc_type": "AGREEMENT",     "reason": "Contract / Agreement is primary evidence of civil claim"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# OCR PIPELINE  — 3-path: pdfplumber | pdf2image+tesseract | tesseract
# ─────────────────────────────────────────────────────────────────────────────


def _ocr_native_pdf(file_bytes: bytes) -> Tuple[str, List[Dict], str]:
    """Extract text from a native (text-layer) PDF using pdfplumber.

    Speed notes:
    - Capped at 6 pages (legal docs rarely need more for fact extraction).
    - Blank / near-blank pages are skipped immediately.
    """
    try:
        import pdfplumber
        pages_data = []
        full_text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            max_pages = min(len(pdf.pages), 6)  # was 12 — 6 is enough for legal docs
            for i in range(max_pages):
                page = pdf.pages[i]
                page_text = page.extract_text() or ""
                if len(page_text.strip()) < 10:  # skip virtually blank pages fast
                    continue
                pages_data.append({"page_num": i + 1, "text": page_text})
                full_text_parts.append(page_text)
        full_text = "\n".join(full_text_parts)
        return full_text, pages_data, "pdfplumber"
    except ImportError:
        return "", [], "pdfplumber_unavailable"
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        return "", [], "pdfplumber_error"


def _ocr_win_media(file_bytes: bytes) -> str:
    """Run native Windows Media OCR on Windows without external binaries."""
    import sys, subprocess, tempfile
    from pathlib import Path
    if sys.platform != "win32":
        return ""
    ps_script = Path(__file__).resolve().parent / "win_ocr_helper.ps1"
    if not ps_script.exists():
        return ""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        res = subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(ps_script), "-imgPath", tmp_path.replace("/", "\\")
        ], capture_output=True, text=True, encoding="utf-8", timeout=25)
        out = res.stdout.strip()
        if "OCR_SUCCESS:" in out:
            return out.split("OCR_SUCCESS:", 1)[1].strip()
        return ""
    except Exception as e:
        logger.warning(f"Windows Media OCR failed: {e}")
        return ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _ocr_scanned_pdf(file_bytes: bytes) -> Tuple[str, List[Dict], str]:
    """Convert scanned PDF pages to images, then OCR each page.

    Speed notes:
    - PyMuPDF render DPI lowered 150→120 (still crisp, ~36% fewer pixels).
    - Page cap: 4 pages max (covers all standard legal doc types).
    - pdf2image fallback also capped at 4 pages.
    """
    # Method 1: Try PyMuPDF (fitz) direct text extraction + page rendering
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_data = []
        full_text_parts = []
        max_pages = min(len(doc), 4)  # cap at 4 pages — fast path
        for i in range(max_pages):
            page = doc[i]
            # 1a. Check direct text stream first
            page_text = (page.get_text() or "").strip()
            # 1b. If page has no text layer, render pixmap for OCR
            if not page_text:
                try:
                    pix = page.get_pixmap(dpi=120)  # was 150 — 120 is fast enough
                    png_bytes = pix.tobytes("png")
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(io.BytesIO(png_bytes))
                        page_text = pytesseract.image_to_string(img, lang="eng").strip()
                    except Exception:
                        pass
                    if not page_text:
                        page_text = _ocr_win_media(png_bytes)
                except Exception as pix_err:
                    logger.debug(f"PyMuPDF pixmap OCR error: {pix_err}")
            if page_text.strip():  # skip blank pages
                pages_data.append({"page_num": i + 1, "text": page_text})
                full_text_parts.append(page_text)
        full_text = "\n".join(full_text_parts)
        if len(full_text.strip()) > 30:
            return full_text, pages_data, "pymupdf"
    except Exception as e:
        logger.debug(f"PyMuPDF scanned OCR attempt: {e}")

    # Method 2: pdf2image + pytesseract fallback
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        from PIL import Image

        images = convert_from_bytes(file_bytes, dpi=120, first_page=1, last_page=4)  # was dpi=150, last=6
        pages_data = []
        full_text_parts = []
        for i, img in enumerate(images, start=1):
            page_text = pytesseract.image_to_string(img, lang="eng")
            pages_data.append({"page_num": i, "text": page_text})
            full_text_parts.append(page_text)
        full_text = "\n".join(full_text_parts)
        return full_text, pages_data, "pdf2image+tesseract"
    except Exception as e:
        logger.info(f"pdf2image fallback skipped or unavailable: {e}")
        return "", [], "pdf2image_unavailable"


def _ocr_image(file_bytes: bytes) -> Tuple[str, List[Dict], str]:
    """OCR a raw image file (JPEG, PNG, WEBP).

    Speed notes:
    - Only upscale if image is < 800px on the short side (was 1000).
    - Use BILINEAR instead of LANCZOS for resize (3× faster, imperceptible difference for OCR).
    """
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(file_bytes))
        min_dim = min(image.width, image.height)
        if min_dim < 800:  # was 1000 — 800 is still fine for Tesseract
            scale = 800 / min_dim
            new_size = (int(image.width * scale), int(image.height * scale))
            # BILINEAR is ~3× faster than LANCZOS for OCR pre-processing
            resample_filter = getattr(getattr(Image, "Resampling", None), "BILINEAR", 2)
            image = image.resize(new_size, resample_filter)
        text = pytesseract.image_to_string(image, lang="eng").strip()
        if text:
            return text, [{"page_num": 1, "text": text}], "tesseract"
    except Exception as e:
        logger.debug(f"pytesseract failed, trying Windows Media OCR: {e}")

    # Fallback to Windows Media OCR
    win_text = _ocr_win_media(file_bytes)
    if win_text:
        return win_text, [{"page_num": 1, "text": win_text}], "windows_media_ocr"

    return "", [], "ocr_unavailable"


def run_ocr_pipeline(file_bytes: bytes, mime_type: str, filename: str) -> Dict[str, Any]:
    """
    Three-path OCR pipeline:
      - Native PDF  → pdfplumber (text layer)
      - Scanned PDF → pdf2image → page images → tesseract
      - Image       → tesseract directly
    Fallback chain: pdfplumber → pdf2image+tesseract → plain tesseract.
    """
    full_text = ""
    pages_data = []
    method = "unknown"
    warnings = []

    is_pdf = mime_type == "application/pdf" or filename.lower().endswith(".pdf")
    is_image = mime_type in ("image/jpeg", "image/png", "image/webp", "image/tiff") or \
               filename.lower().split(".")[-1] in ("jpg", "jpeg", "png", "webp", "tiff", "bmp")

    if is_pdf:
        # Try native PDF first
        full_text, pages_data, method = _ocr_native_pdf(file_bytes)
        text_density = len(full_text.strip())

        if text_density < 50:
            # Likely a scanned PDF — try pdf2image → tesseract
            logger.info(f"pdfplumber yielded sparse text ({text_density} chars) for '{filename}'; trying pdf2image+tesseract")
            scanned_text, scanned_pages, scanned_method = _ocr_scanned_pdf(file_bytes)
            if len(scanned_text.strip()) > text_density:
                full_text, pages_data, method = scanned_text, scanned_pages, scanned_method
            elif "unavailable" in scanned_method or "error" in scanned_method:
                warnings.append(f"pdf2image/Poppler not available ({scanned_method}). Install Poppler for scanned PDF support. Using pdfplumber result.")

    elif is_image:
        full_text, pages_data, method = _ocr_image(file_bytes)
    else:
        warnings.append(f"Unsupported MIME type '{mime_type}' — attempting image OCR as fallback.")
        full_text, pages_data, method = _ocr_image(file_bytes)

    page_count = len(pages_data) if pages_data else 1
    return {
        "text": full_text,
        "pages": pages_data,
        "page_count": page_count,
        "method": method,
        "char_count": len(full_text.strip()),
        "warnings": warnings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LLM FACT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

FACT_EXTRACTION_SCHEMA = """
Return a JSON object with this exact structure. For each field:
- "value": extracted value or null if not found
- "confidence": float 0.0-1.0
- "page": page number (integer) where found, or null
- "snippet": the exact text excerpt (max 120 chars) from which this was extracted, or null

{
  "doc_type_detected": "<one of: SECTION_138_COMPLAINT|INVOICE_LEDGER|CHEQUE|BANK_MEMO|LEGAL_NOTICE|TRACKING_REPORT|AGREEMENT|EMAIL_EXCHANGE|COURT_ORDER|FIR|ITR|OTHER>",
  "complainant_name":     {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "accused_name":         {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "authorized_person":    {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "case_number":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "complaint_number":     {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "fir_number":           {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "cheque_number":        {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "cheque_date":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "cheque_amount":        {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "cheque_type":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "bank_name":            {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "branch_name":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "account_number":       {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "ifsc_code":            {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "dishonour_date":       {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "dishonour_reason":     {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "memo_date":            {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "notice_date":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "notice_mode":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "notice_delivery_date": {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "notice_15day_clause":  {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "agreement_date":       {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "transaction_date":     {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "invoice_date":         {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "part_payment_date":    {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "filing_date":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "cheque_amount_words":  {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "outstanding_amount":   {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "npa_date":             {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "property_description": {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "ipc_section":          {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "incident_date":        {"value": null, "confidence": 0.0, "page": null, "snippet": null},
  "all_dates_found":      {"value": [], "confidence": 0.0, "page": null, "snippet": null},
  "key_facts":            {"value": [], "confidence": 0.0, "page": null, "snippet": null}
}
"""


def extract_facts_with_llm(
    text: str,
    doc_type: str,
    filename: str,
    pages_data: List[Dict],
    file_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract structured facts from OCR text using Groq or Gemini LLM.
    If OCR text is empty/sparse and file bytes are available (image/PDF),
    utilizes Gemini multimodal extraction directly.
    Falls back to regex-based deterministic extraction if no LLM available.
    """
    from llm_engine import _invoke_llm, LLM_AVAILABLE
    import base64

    # Prepare multimodal inline data if OCR text is sparse
    inline_data = None
    clean_mime = (mime_type or "").lower().split(";")[0].strip()
    if file_bytes and (not text or len(text.strip()) < 40):
        if clean_mime in ("image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf") or \
           filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".pdf")):
            if not clean_mime or clean_mime == "application/octet-stream":
                if filename.lower().endswith(".pdf"):
                    clean_mime = "application/pdf"
                elif filename.lower().endswith((".jpg", ".jpeg")):
                    clean_mime = "image/jpeg"
                elif filename.lower().endswith(".png"):
                    clean_mime = "image/png"
            # Cap at 8MB to prevent network bloat
            if len(file_bytes) <= 8 * 1024 * 1024:
                try:
                    inline_data = {
                        "mime_type": clean_mime or "application/pdf",
                        "data": base64.b64encode(file_bytes).decode("utf-8")
                    }
                    logger.info(f"Multimodal payload prepared for '{filename}' ({clean_mime}, {len(file_bytes)} bytes)")
                except Exception as b64_err:
                    logger.debug(f"Failed to prepare multimodal payload: {b64_err}")

    # If OCR text is completely empty and no multimodal data exists, fail-fast to deterministic
    if not text.strip() and not inline_data:
        logger.info(f"Skipping LLM for '{filename}': OCR text is empty and multimodal is unavailable.")
        return _deterministic_fact_extraction("", doc_type)

    # Compose page-indexed text for the prompt — send up to 3500 chars per page
    # (was 6000 / 8 pages — reduced to cut LLM input tokens and latency)
    page_context = ""
    if pages_data:
        for p in pages_data[:5]:  # max 5 pages (covers all standard legal docs)
            page_text = (p.get('text') or '').strip()
            if page_text:
                page_context += f"\n[PAGE {p['page_num']}]\n{page_text[:3500]}\n"
    if not page_context and text:
        page_context = text[:5000]

    system_prompt = (
        "You are a Senior Indian Legal Document Analyst with 20+ years of experience. "
        "Extract ALL structured facts from Indian legal documents with precision. "
        "Return ONLY valid JSON matching the schema exactly. "
        "For amounts: return numeric value only (no commas, no currency prefix). "
        "  Example: '₹15,00,000' → 1500000 "
        "For dates: return in YYYY-MM-DD format where possible. "
        "  Example: '25th March, 2026' → '2026-03-25' "
        "For doc_type_detected: classify based on document content AND filename. "
        "IMPORTANT: An email conversation or mailbox export MUST be classified as EMAIL_EXCHANGE, never INVOICE_LEDGER. "
        "For agreement execution dates: extract into agreement_date (do NOT put into transaction_date). "
        "Only populate transaction_date when a specific debt/transaction date is established. "
        "Never guess — if a field is not clearly present, set value to null and confidence to 0.0. "
        "Extract party names exactly as written. For cheque amounts also capture the words form."
    )

    prompt = (
        f'Analyze this document carefully:\n'
        f'Filename: "{filename}"\n'
        f'Pre-classified document type (use as strong hint): {doc_type}\n'
        f'\nDocument text (page-indexed):\n{page_context}\n'
        f'\nExtract ALL facts visible in this document. '
        f'Pay special attention to:\n'
        f'- Party names (complainant, accused, payee, drawer, advocate, bank officer)\n'
        f'- ALL dates (cheque date, dishonour date, notice date, delivery date, transaction date)\n'
        f'- Amounts in digits AND words\n'
        f'- Cheque number (usually 6 digits)\n'
        f'- Bank name, branch, IFSC, account number\n'
        f'- Dishonour reason (exact text from bank memo)\n'
        f'- Notice mode (speed post / RPAD / email / courier)\n'
        f'\nUse ONLY this exact JSON schema. Output ONLY the JSON, no markdown:\n'
        f'{FACT_EXTRACTION_SCHEMA}'
    )

    if LLM_AVAILABLE:
        result = _invoke_llm(
            prompt,
            max_tokens=1800,  # was 3000 — schema output rarely exceeds 900 tokens
            temperature=0.0,
            expect_json=True,
            system_prompt=system_prompt,
            inline_data=inline_data
        )
        if result and isinstance(result, dict):
            # Overlay with deterministic results for fields LLM missed
            det = _deterministic_fact_extraction(text, doc_type)
            for field, det_val in det.items():
                if field == "doc_type_detected":
                    continue
                llm_val = result.get(field, {})
                if isinstance(llm_val, dict) and llm_val.get("value") is None:
                    if isinstance(det_val, dict) and det_val.get("value") is not None:
                        result[field] = det_val  # use deterministic if LLM missed it
            return result

    # Deterministic regex fallback (comprehensive)
    return _deterministic_fact_extraction(text, doc_type)


def _extract_date_near(text: str, anchors: List[str], context_chars: int = 60) -> Optional[Tuple[str, int, str]]:
    """
    Find a date string near one of the anchor phrases.
    Prefers dates immediately AFTER the anchor; falls back to dates immediately BEFORE.
    Returns (raw_date, char_position, raw_snippet) or None.
    """
    DATE_PATTERNS = [
        r'\b(\d{4}[-/]\d{2}[-/]\d{2})\b',            # YYYY-MM-DD / YYYY/MM/DD
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',         # DD-MM-YYYY / DD/MM/YYYY
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2})\b',          # DD/MM/YY
        r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|'
        r'Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
        r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b',   # 25 March 2026
        r'\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
        r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        r'\s+\d{1,2},?\s+\d{4})\b',                   # March 25, 2026
    ]
    tl = text.lower()
    for anchor in anchors:
        pos = tl.find(anchor.lower())
        if pos == -1:
            continue

        anchor_end = pos + len(anchor)

        # 1. First check window AFTER the anchor (e.g. "cheque dated 25/03/2026", "return memo dated 03-04-2026")
        after_window_end = min(len(text), anchor_end + context_chars)
        after_window = text[anchor_end:after_window_end]
        for pat in DATE_PATTERNS:
            m = re.search(pat, after_window, re.IGNORECASE)
            if m:
                raw = m.group(1)
                snip_start = max(0, anchor_end + m.start() - 15)
                snip_end = min(len(text), anchor_end + m.end() + 15)
                return raw, anchor_end + m.start(), text[snip_start:snip_end].strip()

        # 2. Fallback: check window BEFORE the anchor (e.g. "25/03/2026 was the cheque date")
        before_window_start = max(0, pos - context_chars)
        before_window = text[before_window_start:pos]
        best_match = None
        for pat in DATE_PATTERNS:
            for m in re.finditer(pat, before_window, re.IGNORECASE):
                if best_match is None or m.start() > best_match.start():
                    best_match = m
        if best_match:
            raw = best_match.group(1)
            snip_start = max(0, before_window_start + best_match.start() - 15)
            snip_end = min(len(text), before_window_start + best_match.end() + 15)
            return raw, before_window_start + best_match.start(), text[snip_start:snip_end].strip()

    return None


def _normalize_date(raw: str) -> str:
    """Attempt to convert any date string to YYYY-MM-DD; return raw if parse fails."""
    MONTH_MAP = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }
    raw = raw.strip()
    # Already ISO-ish
    m = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', raw)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    # DD/MM/YY
    m = re.match(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2})$', raw)
    if m:
        year = 2000 + int(m.group(3))
        return f"{year}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    # 25 March 2026 / 25th March 2026
    m = re.match(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})', raw, re.IGNORECASE)
    if m:
        mo = MONTH_MAP.get(m.group(2)[:3].lower())
        if mo:
            return f"{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}"
    # March 25, 2026
    m = re.match(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', raw, re.IGNORECASE)
    if m:
        mo = MONTH_MAP.get(m.group(1)[:3].lower())
        if mo:
            return f"{m.group(3)}-{mo:02d}-{int(m.group(2)):02d}"
    return raw  # Return as-is if unparseable


def _words_to_number(words: str) -> Optional[float]:
    """Convert Indian amount-in-words to float. E.g. 'fifteen lakh only' → 1500000."""
    UNITS = {
        'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,
        'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,
        'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,
        'nineteen':19,'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,
        'seventy':70,'eighty':80,'ninety':90
    }
    MULTIPLIERS = {'lakh':100000,'lakhs':100000,'lac':100000,'crore':10000000,'crores':10000000,
                   'thousand':1000,'hundred':100}
    words = re.sub(r'[^a-z\s]', '', words.lower())
    tokens = words.split()
    total = 0.0
    current = 0.0
    for t in tokens:
        if t in UNITS:
            current += UNITS[t]
        elif t in MULTIPLIERS:
            current = (current if current > 0 else 1) * MULTIPLIERS[t]
            total += current
            current = 0.0
        # skip 'only', 'rupees', 'and', etc.
    total += current
    return total if total > 0 else None


LABEL_BLACKLIST = {
    "cheque", "bank", "amount", "date", "invoice", "account",
    "notice", "memo", "ledger", "payment", "loan", "section",
    "schedule", "annexure", "exhibit", "total", "subject", "ref",
    "reference", "challan", "receipt", "order", "case", "cr", "cc",
    "branch", "ifsc", "pin", "code", "pincode", "speed", "post",
    "tracking", "consignment", "article", "complaint", "statutory",
    "client", "behalf", "undersigned", "advocate", "counsel", "pleader",
    "instructions", "solicitor", "representative", "signatory",
}

ADVOCACY_PHRASES = [
    "and on behalf of my client", "on behalf of my client",
    "and on behalf of", "on behalf of", "under instructions from",
    "instructions from", "my client", "our client", "the client",
    "the complainant", "the undersigned", "advocate for",
    "counsel for", "legal notice", "statutory demand",
]


NAME_BLACKLIST_WORDS = {
    "shall", "will", "would", "should", "could", "can", "may", "might", "must", "ought",
    "be", "been", "being", "is", "am", "are", "was", "were",
    "have", "has", "had", "having",
    "do", "does", "did", "done",
    "take", "takes", "pay", "pays", "paid", "funded", "provide", "provides", "provided",
    "receive", "receives", "received", "rely", "relies", "relied", "state", "states", "stated",
    "demand", "demands", "demanded", "deliver", "delivers", "delivered",
    "record", "records", "recorded", "failing", "which", "such", "proceedings",
    "ordinary", "course", "postal", "service", "security", "desk", "within", "days",
    "presentation", "collection", "drawn", "issued", "presented", "returned", "unpaid",
    "subject", "notices", "disputes", "acknowledgment", "goods", "consideration",
}


def _clean_party_candidate(candidate: Optional[str]) -> Optional[str]:
    """Clean OCR prefixes, salutations and artifacts from extracted party names."""
    if not candidate:
        return None
    c = candidate.strip()
    c = re.sub(r'^(?:(?:and\s+)?(?:on\s+behalf\s+of\s+)?(?:my\s+client|our\s+client|the\s+client)?|(?:under\s+instructions\s+from\s+))\s*[,:]?\s*', '', c, flags=re.IGNORECASE)
    c = re.sub(r'^(?:mer|omer|ustomer|customer|consumer|former|client|buyer|purchaser|party|drawer|drawee|payee|accused|complainant|to|from|m/s\.?|messrs\.?|shri\.?|smt\.?|mr\.?|ms\.?|mrs\.?|dr\.?)\b\s*[:\-\s]*', '', c, flags=re.IGNORECASE)
    c = re.sub(r'^[\W\d_]+', '', c)
    c = re.sub(r'[\r\n\t]+', ' ', c)
    c = c.strip(" \t\n\r,.:;\"'()")
    return c if len(c) >= 3 else None


def _is_valid_name(candidate: Optional[str]) -> bool:
    """Validate candidate person or corporate entity name; rejects field labels, verbs, and boilerplate."""
    if not candidate:
        return False
    c = candidate.strip().rstrip(".,;:- ")
    if len(c) < 4:
        return False
    c_lower = c.lower()
    for phrase in ADVOCACY_PHRASES:
        if c_lower == phrase or c_lower.startswith(phrase + " "):
            return False
        if phrase in c_lower and len(c_lower.replace(phrase, "").strip()) < 4:
            return False
    # If it contains digits (e.g. Cheque No 582914 or Account 12345), reject as party name
    if any(ch.isdigit() for ch in c):
        return False
    words = [w.lower().rstrip('.:,') for w in re.split(r'[\s/]+', c) if w]
    if not words:
        return False
    # Reject if first word is a preposition, conjunction, pronoun, article or label
    if words[0] in {"and", "under", "from", "on", "in", "to", "for", "with", "by", "of", "the", "my", "our", "a", "an", "all", "any", "this", "that", "these", "those", "we", "you", "they", "it"}:
        return False
    if words[0] in LABEL_BLACKLIST:
        return False
    # Reject if ANY word is a strong blacklist keyword or verb
    if any(w in LABEL_BLACKLIST for w in words if w not in ("limited", "pvt")):
        return False
    if any(w in NAME_BLACKLIST_WORDS for w in words):
        return False
    # Must have at least one alphabetic token >= 3 chars
    if not any(len(w) >= 3 and w.isalpha() for w in words):
        return False
    return True


def normalize_entity_name(name: Optional[str]) -> str:
    """
    Normalizes corporate and individual party names to remove OCR artifacts,
    salutations, prefixes, suffixes, and punctuation variations.
    """
    if not name:
        return ""
    s = name.strip()
    # 1. Strip leading OCR artifact fragments like "mer ", "omer ", "mer.", "customer ", "client ", "party "
    s = re.sub(
        r'^(?:mer|omer|ustomer|customer|consumer|former|client|party|accused|complainant|drawer|drawee|payee|to|from|m/s\.?|messrs\.?|shri\.?|smt\.?|mr\.?|mrs\.?|dr\.?)\s*[:\-]?\s*',
        '', s, flags=re.IGNORECASE
    )
    # Strip any lingering leading/trailing punctuation or numbers
    s = re.sub(r'^[\W\d_]+', '', s)
    s = re.sub(r'[\W_]+$', '', s)
    # 2. Normalize legal form abbreviations (case-insensitive)
    s = re.sub(r'\b(?:pvt\.?\s*ltd\.?|private\s+limited)\b', 'private limited', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(?:ltd\.?|limited)\b', 'limited', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(?:co\.?|company)\b', 'company', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(?:corp\.?|corporation)\b', 'corporation', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(?:inc\.?|incorporated)\b', 'incorporated', s, flags=re.IGNORECASE)
    s = re.sub(r'\bllp\b', 'limited liability partnership', s, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', s).strip().lower()


def _is_party_match(val_a: Any, val_b: Any) -> bool:
    """Determine if two party strings refer to the same entity despite OCR noise."""
    norm_a = normalize_entity_name(str(val_a))
    norm_b = normalize_entity_name(str(val_b))
    if not norm_a or not norm_b:
        return True
    if norm_a == norm_b:
        return True
    if norm_a in norm_b or norm_b in norm_a:
        return True
    tokens_a = set(re.findall(r'\w+', norm_a))
    tokens_b = set(re.findall(r'\w+', norm_b))
    if not tokens_a or not tokens_b:
        return True
    intersection = tokens_a.intersection(tokens_b)
    generic = {"private", "limited", "company", "systems", "solutions", "enterprises", "traders", "associates", "corporation", "industrial", "components"}
    core_a = tokens_a - generic
    core_b = tokens_b - generic
    if core_a and core_b and core_a == core_b:
        return True
    overlap = len(intersection) / len(tokens_a.union(tokens_b))
    return overlap >= 0.70


def _deterministic_fact_extraction(text: str, doc_type: str) -> Dict[str, Any]:
    """Comprehensive regex-based fact extraction — 26+ fields. No LLM required."""
    result: Dict[str, Any] = {}
    t = text.lower()

    def _field(val, conf, page=None, snip=None):
        return {"value": val, "confidence": conf, "page": page, "snippet": snip}

    result["doc_type_detected"] = doc_type

    # ── All dates ─────────────────────────────────────────────────────────────
    all_dates_raw = re.findall(
        r'\b(\d{1,2}[-/]\d{1,2}[-/](?:\d{2}|\d{4})|\d{4}[-/]\d{2}[-/]\d{2}|'
        r'\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|'
        r'Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|'
        r'Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b',
        text, re.IGNORECASE
    )
    all_dates = [_normalize_date(d) for d in all_dates_raw]
    result["all_dates_found"] = _field(all_dates, 0.7 if all_dates else 0.0)

    # ── Cheque number ─────────────────────────────────────────────────────────
    # STRICT: only explicit label within 15 chars of number.
    # No standalone 6-digit fallback (to prevent PIN codes like 411045 being extracted).
    chq_m = re.search(
        r'(?:cheque|chq|ch(?:eque)?)\s*(?:no\.?|number|num\.?|#)?\s*[:#\-]?\s*([0-9]{6,8})',
        t
    )
    chq_no_val = None
    if chq_m:
        chq_no_val = chq_m.group(1)
        snip_start = max(0, chq_m.start() - 20)
        snip = text[snip_start:chq_m.end() + 20]
        result["cheque_number"] = _field(chq_no_val, 0.88, snip=snip)
    else:
        result["cheque_number"] = _field(None, 0.0)

    # ── Cheque amount in words (Checked first as most authoritative legal proof) ──
    words_m = re.search(
        r'(?:rupees|rs\.?|sum\s+of\s+rupees|pay\s+[^,\n]+?rupees)?\s*([a-z\s]+?(?:lakh|lakhs|lac|crore|crores|thousand)[a-z\s]*?(?:only|/-|\b))',
        t
    )
    amt_in_words = None
    numeric_from_words = None
    if words_m:
        raw_words = words_m.group(1).strip()
        amt_in_words = raw_words.title()
        numeric_from_words = _words_to_number(raw_words)

    # ── Cheque amount (numeric) ───────────────────────────────────────────────
    # Specific patterns targeting the cheque / debt amount specifically (avoiding stray fee numbers)
    specific_amt_patterns = [
        r'(?:(?:cheque|chk)[^\n\r]{0,120}?(?:for|of|amounting\s+to|sum\s+of|towards|bearing\s+amount\s+of|drawn\s+for|issued\s+for|received)[^\n\r]{0,60}?)\s*[:\s\-]+(?:(?:rs\.?|inr|₹|[nI])\s*)?([0-9]{1,3}(?:,[0-9]{2,3})+|\b[0-9]{5,8}\b(?:\.\d{1,2})?)',
        r'(?:notice[^\n]{0,40}?(?:for|amount)\s*[:\s]*(?:(?:rs\.?|inr|₹|[nI])\s*)?)([0-9]{1,3}(?:,[0-9]{2,3})+|\b[0-9]{5,8}\b(?:\.\d{1,2})?)',
        r'(?:legally\s+enforceable\s+debt\s+of|debt\s+amount\s+of|amount\s+of\s+rs\.?)\s*(?:(?:rs\.?|inr|₹|[nI])\s*)?([0-9]{1,3}(?:,[0-9]{2,3})+|\b[0-9]{5,8}\b(?:\.\d{1,2})?)',
        r'(?:₹|[nI])\s*([0-9]{1,3}(?:,[0-9]{2,3})+(?:\.\d{1,2})?)\s*(?:/-|/[-–]|only)\b',
        r'([0-9]{1,3}(?:,[0-9]{2,3})+(?:\.\d{1,2})?)\s*/[-–]\s*(?:only|/-)',
        r'[\*#₹\s]*([1-9]\d{0,2}(?:,\d{2,3})*(?:\.\d{2})?)\s*(?:/-|/[-–]|\*|#)',
    ]
    general_amt_patterns = [
        r'(?:₹|[nI])\s*([\d,]+(?:\.\d{1,2})?)',
        r'(?:rs\.?|inr|rupees)\s*([\d,]+(?:\.\d{1,2})?)',
    ]

    found_amt = None
    amt_snip = None

    # For Legal Notice, specifically look for the notice demand amount (e.g. n14,50,000)
    if doc_type == "LEGAL_NOTICE":
        notice_amt_m = re.search(
            r'(?:demand\s+(?:the\s+)?(?:sum|amount)\s+of|pay\s+(?:the\s+)?(?:sum|amount)\s+of|called\s+upon\s+to\s+pay|demanding\s+payment\s+of|sum\s+of|issued\s+cheque[^\n]{0,80}?for)\s*[:\s]*(?:(?:rs\.?|inr|₹|[nI])\s*)?([0-9]{1,3}(?:,[0-9]{2,3})+|\b[0-9]{5,8}\b)',
            text, re.IGNORECASE
        )
        if notice_amt_m:
            try:
                n_val = float(notice_amt_m.group(1).replace(",", "").strip())
                if n_val >= 5000 and (not chq_no_val or str(int(n_val)) != str(chq_no_val)):
                    found_amt = n_val
                    amt_snip = notice_amt_m.group(0)
            except ValueError:
                pass

    # Step A: On physical CHEQUE, amount in words is the primary legal specification (Sec 18 NI Act)
    if doc_type == "CHEQUE" and numeric_from_words:
        found_amt = numeric_from_words
        amt_snip = amt_in_words

    # Step B: Try specific cheque patterns first
    if not found_amt:
        for pat in specific_amt_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                clean = m.group(1).replace(",", "").strip()
                try:
                    val = float(clean)
                    if chq_no_val and (clean == chq_no_val or str(int(val)) == str(chq_no_val)):
                        continue
                    if val >= 5000:
                        found_amt = val
                        amt_snip = text[max(0, m.start() - 15):m.end() + 15].strip()
                        break
                except ValueError:
                    pass
            if found_amt:
                break

    # Step C: If amount in words exists, words take precedence over stray fee amounts or rejected cheque numbers
    if numeric_from_words and (not found_amt or (chq_no_val and str(int(found_amt)) == str(chq_no_val)) or (found_amt < 10000 and numeric_from_words >= 10000)):
        found_amt = numeric_from_words
        amt_snip = amt_in_words

    # Step D: Fallback to general patterns only if not found (exclude INVOICE_LEDGER and AGREEMENT to avoid item rates)
    if not found_amt and doc_type not in ("INVOICE_LEDGER", "AGREEMENT"):
        candidate_amts = []
        for pat in general_amt_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                clean = m.group(1).replace(",", "").strip()
                try:
                    val = float(clean)
                    if chq_no_val and (clean == chq_no_val or str(int(val)) == str(chq_no_val)):
                        continue
                    surround = text[max(0, m.start() - 30):min(len(text), m.end() + 30)].lower()
                    is_fee = any(kw in surround for kw in ("fee", "charges", "postal", "stamp", "speed post", "drafting", "counsel"))
                    candidate_amts.append((val, is_fee, text[max(0, m.start() - 15):m.end() + 15].strip()))
                except ValueError:
                    pass
        valid_large = [c for c in candidate_amts if not c[1] and c[0] >= 5000]
        if valid_large:
            found_amt = valid_large[0][0]
            amt_snip = valid_large[0][2]
        elif candidate_amts:
            valid_any = [c for c in candidate_amts if not c[1] and c[0] > 99]
            if valid_any:
                found_amt = valid_any[0][0]
                amt_snip = valid_any[0][2]

    result["cheque_amount"] = _field(found_amt, 0.88 if found_amt else 0.0, snip=amt_snip)
    result["cheque_amount_words"] = _field(amt_in_words, 0.85 if amt_in_words else 0.0)

    # ── Dishonour reason ──────────────────────────────────────────────────────
    REASON_MAP = {
        "Insufficient Funds": ["insufficient funds", "funds insufficient", "insufficient balance",
                                "shortage of funds", "balance insufficient"],
        "Account Closed":     ["account closed", "a/c closed", "account has been closed"],
        "Payment Stopped":    ["payment stopped", "stop payment", "payment countermanded"],
        "Signature Mismatch": ["signature mismatch", "signature differs", "signature does not match",
                                "signature differ"],
        "Refer to Drawer":    ["refer to drawer", "r/d"],
        "Exceeds Arrangement":["exceeds arrangement", "exceeds the arrangement"],
    }
    found_reason = None
    reason_snip = None
    for reason, kws in REASON_MAP.items():
        for kw in kws:
            pos = t.find(kw)
            if pos != -1:
                found_reason = reason
                reason_snip = text[max(0,pos-10):pos+len(kw)+20].strip()
                break
        if found_reason:
            break
    result["dishonour_reason"] = _field(found_reason, 0.82 if found_reason else 0.0, snip=reason_snip)

    # ── Bank name ─────────────────────────────────────────────────────────────
    BANKS = [
        ("HDFC Bank",        ["hdfc bank", "hdfc"]),
        ("ICICI Bank",       ["icici bank", "icici"]),
        ("State Bank of India", ["state bank of india", "sbi", "state bank"]),
        ("Axis Bank",        ["axis bank", "axis"]),
        ("Kotak Mahindra Bank", ["kotak mahindra", "kotak bank", "kotak"]),
        ("Punjab National Bank", ["punjab national bank", "pnb"]),
        ("Canara Bank",      ["canara bank", "canara"]),
        ("Union Bank of India", ["union bank of india", "union bank"]),
        ("Bank of Baroda",   ["bank of baroda", "bob"]),
        ("IndusInd Bank",    ["indusind bank", "indusind"]),
        ("Yes Bank",         ["yes bank"]),
        ("Federal Bank",     ["federal bank"]),
        ("Bank of India",    ["bank of india"]),
        ("Indian Bank",      ["indian bank"]),
        ("Central Bank",     ["central bank"]),
        ("UCO Bank",         ["uco bank"]),
        ("IDBI Bank",        ["idbi bank", "idbi"]),
        ("Karnataka Bank",   ["karnataka bank"]),
    ]
    found_bank = None
    bank_snip = None
    for name, variants in BANKS:
        for v in variants:
            pos = t.find(v)
            if pos != -1:
                found_bank = name
                bank_snip = text[max(0,pos-5):pos+len(v)+20].strip()
                break
        if found_bank:
            break
    result["bank_name"] = _field(found_bank, 0.80 if found_bank else 0.0, snip=bank_snip)

    # ── Branch name ───────────────────────────────────────────────────────────
    branch_m = re.search(r'(?:branch)[:\s]+([A-Z][a-zA-Z\s,]{2,40}?)(?:\n|\.|,|$)', text, re.MULTILINE)
    result["branch_name"] = _field(
        branch_m.group(1).strip() if branch_m else None,
        0.70 if branch_m else 0.0
    )

    # ── IFSC code ─────────────────────────────────────────────────────────────
    ifsc_m = re.search(r'\b([A-Z]{4}0[A-Z0-9]{6})\b', text)
    result["ifsc_code"] = _field(
        ifsc_m.group(1) if ifsc_m else None,
        0.92 if ifsc_m else 0.0,
        snip=ifsc_m.group(0) if ifsc_m else None
    )

    # ── Account number ────────────────────────────────────────────────────────
    acc_m = re.search(
        r'(?:account\s*(?:no\.?|number)?|a/?c\s*(?:no\.?)?)[:\s]*([\d\s]{9,18})',
        t
    )
    if acc_m:
        acc_val = acc_m.group(1).replace(" ", "").strip()
        result["account_number"] = _field(acc_val if len(acc_val) >= 9 else None, 0.75)
    else:
        result["account_number"] = _field(None, 0.0)

    # ── Cheque date ───────────────────────────────────────────────────────────
    # Only search from CHEQUE, LEGAL_NOTICE, SECTION_138_COMPLAINT, BANK_MEMO, or OTHER docs
    chq_date_val = None
    chq_date_snip = None
    if doc_type in ("CHEQUE", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT", "BANK_MEMO", "OTHER", ""):
        # Pattern 1: explicitly near "cheque ... dated" or "cheque date"
        m = re.search(
            r'(?:cheque|instrument|chq)[^\n,]{0,40}?\s*(?:dated|bearing\s+date|date|dt\.?)\s*[:\s]*'
            r'(\d{1,2}[-/ ]\d{1,2}[-/ ]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})',
            text, re.IGNORECASE
        )
        if not m:
            # Pattern 1b: complaint format "On or about 25 March 2026, the accused delivered Cheque No. 582914"
            m = re.search(
                r'(?:on\s+or\s+about\s+)?(\d{1,2}[-/ ]\d{1,2}[-/ ]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})[^\n]{0,40}?(?:delivered|issued|handed\s+over)[^\n]{0,30}?cheque',
                text, re.IGNORECASE
            )
        if not m and doc_type == "CHEQUE":
            # Space-separated date on physical cheque: "Date 25 03 2026"
            m = re.search(r'\bDate\s*[:\s]*(\d{2}\s+\d{2}\s+\d{4})\b', text, re.IGNORECASE)
        if m:
            chq_date_val = _normalize_date(m.group(1))
            chq_date_snip = m.group(0)
        else:
            chq_date = _extract_date_near(text, [
                "cheque date", "date of cheque", "cheque dated",
                "date of instrument", "date on cheque",
            ], context_chars=60)
            if chq_date:
                chq_date_val = _normalize_date(chq_date[0])
                chq_date_snip = chq_date[2]
            elif doc_type == "CHEQUE" and all_dates:
                # Heuristic: on a CHEQUE document only, the first date found is the cheque date
                chq_date_val = all_dates[0]
    result["cheque_date"] = _field(chq_date_val, 0.80 if chq_date_val else 0.0, snip=chq_date_snip)

    # ── Dishonour date ────────────────────────────────────────────────────────
    dis_date = _extract_date_near(text, [
        "cheque dishonoured on", "cheque dishonored on",
        "dishonoured on", "dishonored on",
        "date of dishonour", "returned unpaid on",
        "presented and returned on", "dishonoured", "dishonored",
    ], context_chars=60)
    result["dishonour_date"] = _field(
        _normalize_date(dis_date[0]) if dis_date else None,
        0.82 if dis_date else 0.0,
        snip=dis_date[2] if dis_date else None
    )

    # ── Bank Return Memo date (separate from dishonour date) ───────────────────
    memo_date = _extract_date_near(text, [
        "memo dated", "return memo dated", "memo date",
        "memo issued on", "date of memo", "bank memo dated",
    ], context_chars=60)
    result["memo_date"] = _field(
        _normalize_date(memo_date[0]) if memo_date else None,
        0.82 if memo_date else 0.0,
        snip=memo_date[2] if memo_date else None
    )

    # ── Notice date ───────────────────────────────────────────────────────────
    ntc_date = _extract_date_near(text, [
        "notice dated", "legal notice dated", "demand notice dated",
        "notice is dated", "this notice dated", "dated this notice",
        "legal notice", "statutory notice",
    ], context_chars=60)
    if not ntc_date and (doc_type == "LEGAL_NOTICE" or "legal notice" in t):
        header_date = _extract_date_near(text, ["date:", "dated:", "date :", "dated :"], context_chars=30)
        if header_date:
            ntc_date = header_date
    result["notice_date"] = _field(
        _normalize_date(ntc_date[0]) if ntc_date else None,
        0.82 if ntc_date else 0.0,
        snip=ntc_date[2] if ntc_date else None
    )

    # ── Notice delivery / service date ───────────────────────────────────────
    del_date_val = None
    del_date_snip = None
    if doc_type in ("TRACKING_REPORT", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT", "OTHER", ""):
        # Pattern 1: Delivery tracking table format: "Event: Delivered ... Event Date: 19/04/2026"
        m = re.search(
            r'(?:Event:\s*Delivered|Delivered)[\s\S]{0,60}?(?:Event\s*Date|Date)\s*[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            text, re.IGNORECASE
        )
        if not m:
            # Pattern 2: Notice dispatch recital: "records the notice as delivered on 18 April 2026"
            m = re.search(
                r'(?:records\s+(?:the\s+)?notice\s+as\s+delivered\s+on|notice\s+delivered\s+on)\s*[:\s]*'
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})',
                text, re.IGNORECASE
            )
        if not m and doc_type == "TRACKING_REPORT":
            # Pattern 3: general tracking delivered date
            m = re.search(
                r'(?:item\s+delivered|article\s+delivered|consignment\s+delivered|delivered\s+on)\s*[:\s]*'
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})',
                text, re.IGNORECASE
            )
        if m:
            del_date_val = _normalize_date(m.group(1))
            del_date_snip = m.group(0)
    result["notice_delivery_date"] = _field(
        del_date_val,
        0.82 if del_date_val else 0.0,
        snip=del_date_snip
    )

    # ── Agreement executed date (specifically from agreement documents / recitals) ──
    agr_date = _extract_date_near(text, [
        "agreement date", "date of agreement", "agreement dated",
        "executed on", "date of execution", "this agreement executed",
        "contract date", "contract dated", "supply agreement",
    ], context_chars=60)
    result["agreement_date"] = _field(
        _normalize_date(agr_date[0]) if agr_date else None,
        0.82 if agr_date else 0.0,
        snip=agr_date[2] if agr_date else None
    )

    # ── Transaction / debt date (generic only when explicitly stated) ──────────
    txn_date = _extract_date_near(text, [
        "transaction date", "date of transaction", "loan dated", "loan date",
        "debt incurred on", "debt date",
    ], context_chars=60)
    result["transaction_date"] = _field(
        _normalize_date(txn_date[0]) if txn_date else None,
        0.75 if txn_date else 0.0,
        snip=txn_date[2] if txn_date else None
    )

    # ── Invoice / bill date ───────────────────────────────────────────────────
    inv_date = _extract_date_near(text, [
        "invoice date", "invoice dated", "date of invoice",
        "bill date", "bill dated", "tax invoice dated",
    ], context_chars=60)
    result["invoice_date"] = _field(
        _normalize_date(inv_date[0]) if inv_date else None,
        0.78 if inv_date else 0.0,
        snip=inv_date[2] if inv_date else None
    )

    # ── Part payment date ─────────────────────────────────────────────────────
    part_date_val = None
    part_date_snip = None
    # Pattern 1: date before part payment (e.g. ledger row: "10-02-2026 NEFT/88421 Part payment received")
    m_part1 = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})[^\n]{0,40}?part\s+payment', text, re.IGNORECASE)
    if m_part1:
        part_date_val = _normalize_date(m_part1.group(1))
        part_date_snip = m_part1.group(0)
    else:
        # Pattern 2: date after part payment / remitted: "remitted n3,75,000 on 10 February 2026"
        m_part2 = re.search(r'(?:part\s+payment[^\n]{0,40}?(?:on|dated)|remitted[^\n]{0,40}?on)\s*[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})', text, re.IGNORECASE)
        if m_part2:
            part_date_val = _normalize_date(m_part2.group(1))
            part_date_snip = m_part2.group(0)
        else:
            part_date = _extract_date_near(text, [
                "part payment", "partial payment", "payment on account",
                "part-payment date", "paid on",
            ], context_chars=60)
            if part_date:
                part_date_val = _normalize_date(part_date[0])
                part_date_snip = part_date[2]

    result["part_payment_date"] = _field(
        part_date_val,
        0.80 if part_date_val else 0.0,
        snip=part_date_snip
    )

    # ── Filing date ───────────────────────────────────────────────────────────
    fil_date = _extract_date_near(text, [
        "filed on", "filing date", "complaint filed", "date of filing", "presented before"
    ], context_chars=60)
    result["filing_date"] = _field(
        _normalize_date(fil_date[0]) if fil_date else None,
        0.70 if fil_date else 0.0,
        snip=fil_date[2] if fil_date else None
    )

    # ── Notice mode ───────────────────────────────────────────────────────────
    NOTICE_MODES = [
        ("Speed Post (RPAD)", ["speed post", "rpad", "registered post ad"]),
        ("Registered Post",   ["registered post", "r/p"]),
        ("Courier",           ["courier"]),
        ("Email",             ["email", "e-mail", "electronic mail"]),
        ("Hand Delivery",     ["hand delivery", "in person", "personally served"]),
        ("WhatsApp",          ["whatsapp"]),
    ]
    found_mode = None
    for mode, kws in NOTICE_MODES:
        if any(kw in t for kw in kws):
            found_mode = mode
            break
    result["notice_mode"] = _field(found_mode, 0.80 if found_mode else 0.0)

    # ── 15-day notice clause ──────────────────────────────────────────────────
    clause_15 = "15 days" in t or "fifteen days" in t or "15-day" in t
    result["notice_15day_clause"] = _field("Present" if clause_15 else None, 0.85 if clause_15 else 0.0)

    # ── Party names ───────────────────────────────────────────────────────────
    # Complainant — look for "under instructions from", "on behalf of", "complainant:", "payee:", "sender:"
    comp_patterns = [
        r'(?:under instructions from|on behalf of|advocate for)\s+(?:(?:and\s+)?(?:on\s+behalf\s+of\s+)?(?:my|our|the)\s+client)?\s*[,:]?\s*(?:m/s\.?|shri|smt\.?|mr\.?|dr\.?)?\s*([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\s+this\s+notice|\s+having|$)',
        r'(?:^|\n|\b)(?:complainant|petitioner|plaintiff)\b[:\s\-]+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\d|$)',
        r'(?:^|\n|\b)(?:sender)\b[:\s\.\-]+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\bDestination|$)',
        r'(?:^|\n|\b)(?:payee)\b[:\s\-]+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\bReason|\bAmount|$)',
        r'(?:^|\n|\b)(?:pay|pay\s+to)\b\s*[/:]\s*([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\bDate|\bRupees|\bINR|\bRs|$)',
        r'between\s+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)\s+and\s+',
    ]
    found_comp = None
    for pat in comp_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            cand = _clean_party_candidate(m.group(1))
            if cand and _is_valid_name(cand):
                found_comp = cand
                break
        if found_comp:
            break
    result["complainant_name"] = _field(found_comp, 0.75 if found_comp else 0.0)

    # Accused — look for "accused:", "drawer:", "customer:", "To:", "between ... and [Accused]"
    acc_patterns = [
        r'(?:^|\n|\b)(?:accused|defendant|respondent)[:\s\-]+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\d|$)',
        r'(?:^|\n|\b)(?:drawer|drawee)[:\s\-]+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\bPayee|\bAmount|$)',
        r'(?:^|\n|\b)(?:customer|destination)[:\s\.\-]+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|\bCustomer\s+Address|\bAddress|$)',
        r'(?:^|\n)\s*(?:To|Notice\s+to|Demand\s+to)\s*[:,\-]\s*(?:m/s\.?|shri|smt\.?|mr\.?|dr\.?)?\s*([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|,|\.|$)',
        r'between\s+[A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?\s+and\s+([A-Z][a-zA-Z0-9 \t\.\/&,-]{3,60}?)(?:\n|\.|\bAgreement|\bDate|$)',
    ]
    found_accused = None
    for pat in acc_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            cand = _clean_party_candidate(m.group(1))
            if cand and _is_valid_name(cand):
                found_accused = cand
                break
        if found_accused:
            break
    result["accused_name"] = _field(found_accused, 0.75 if found_accused else 0.0)

    # Authorized person
    auth_m = re.search(
        r'(?:authorized person|authorised person|signing authority|signatory)[:\s]+'
        r'([A-Z][a-zA-Z\s\.]{3,50}?)(?:\n|,|\.)',
        text, re.IGNORECASE | re.MULTILINE
    )
    result["authorized_person"] = _field(
        auth_m.group(1).strip() if auth_m else None,
        0.65 if auth_m else 0.0
    )

    # ── Case / complaint numbers ───────────────────────────────────────────────
    case_m = re.search(
        r'(?:case\s*(?:no\.?|number|ref\.?|reference)|complaint\s*(?:no\.?|number|ref\.?)|court\s*ref\.?)\s*[:#\-\/]?\s*([A-Za-z0-9\/\-]{3,30})',
        text, re.IGNORECASE
    )
    if not case_m:
        case_m = re.search(
            r'\b(CC\s*[\/\-]\s*\d{4}\s*[\/\-]\s*\d{3,8})\b',
            text, re.IGNORECASE
        )
    case_val = None
    if case_m:
        cand = case_m.group(1).strip().rstrip(".,;:-")
        if len(cand) >= 3 and any(ch.isdigit() for ch in cand):
            case_val = cand
    result["case_number"] = _field(case_val, 0.85 if case_val else 0.0)
    result["complaint_number"] = result["case_number"]

    # FIR number
    fir_m = re.search(r'(?:fir no\.?|f\.i\.r\s*no\.?)[:\s#]*(\d[\d/\-]{1,15})', t)
    result["fir_number"] = _field(fir_m.group(1).strip() if fir_m else None, 0.85 if fir_m else 0.0)

    # ── Cheque type ───────────────────────────────────────────────────────────
    chq_type = None
    if "account payee" in t or "a/c payee" in t:
        chq_type = "Account Payee"
    elif "bearer" in t:
        chq_type = "Bearer"
    result["cheque_type"] = _field(chq_type, 0.80 if chq_type else 0.0)

    # ── Outstanding / loan amount ─────────────────────────────────────────────
    out_m = re.search(
        r'(?:outstanding|due|dues|loan amount|principal)[:\s]*(?:rs\.?|₹|inr)?[\s]*([\d,]+(?:\.\d{1,2})?)',
        t
    )
    if out_m:
        try:
            result["outstanding_amount"] = _field(float(out_m.group(1).replace(",", "")), 0.72)
        except ValueError:
            result["outstanding_amount"] = _field(None, 0.0)
    else:
        result["outstanding_amount"] = _field(None, 0.0)

    # ── NPA date (Only for SARFAESI, suppressed for Section 138) ──────────────
    npa_date_val = None
    if "sarfaesi" in text.lower() or doc_type == "SARFAESI_NOTICE":
        npa_date = _extract_date_near(text, ["npa", "non-performing", "classified as npa"])
        if npa_date:
            npa_date_val = _normalize_date(npa_date[0])
    result["npa_date"] = _field(npa_date_val, 0.75 if npa_date_val else 0.0)

    # ── Property description ──────────────────────────────────────────────────
    prop_m = re.search(
        r'(?:property|premises|land|flat|plot|building)[:\s]+([A-Za-z0-9\s,\.\-#/]{10,150}?)(?:\n|$)',
        text, re.IGNORECASE | re.MULTILINE
    )
    result["property_description"] = _field(
        prop_m.group(1).strip() if prop_m else None,
        0.65 if prop_m else 0.0
    )

    # ── NI Act / IPC / BNS sections ───────────────────────────────────────────
    ni_m = re.search(r'(?:section|s\.|sec\.)\s*(138|141|142|143|148)\b', t, re.IGNORECASE)
    ipc_m = re.search(r'(?:section|u/?s\.?|u/s|under)\s+(\d+(?:[A-Z])?(?:/\d+(?:[A-Z])?)*)', t)
    if ni_m:
        result["ipc_section"] = _field(ni_m.group(1), 0.85)
    elif ipc_m:
        result["ipc_section"] = _field(ipc_m.group(1), 0.75)
    else:
        result["ipc_section"] = _field(None, 0.0)

    # ── Incident date ─────────────────────────────────────────────────────────
    inc_date = _extract_date_near(text, ["incident", "offence", "offense", "occurred on", "happened on"])
    result["incident_date"] = _field(
        _normalize_date(inc_date[0]) if inc_date else None,
        0.70 if inc_date else 0.0
    )

    # ── Key facts (any notable entities or phrases) ───────────────────────────
    key_facts = []
    if found_bank:    key_facts.append(f"Bank: {found_bank}")
    if found_reason:  key_facts.append(f"Dishonour: {found_reason}")
    if found_mode:    key_facts.append(f"Notice via: {found_mode}")
    if clause_15:     key_facts.append("15-day clause present")
    result["key_facts"] = _field(key_facts, 0.6 if key_facts else 0.0)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-DOCUMENT COMPARISON ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# Fields where a mismatch between documents is CRITICAL
CRITICAL_FIELDS = {"cheque_amount", "cheque_number", "cheque_date", "dishonour_reason",
                   "dishonour_date", "complainant_name", "accused_name"}
# Fields where a mismatch is a WARNING
WARNING_FIELDS = {"bank_name", "branch_name", "memo_date", "notice_date", "transaction_date",
                  "notice_mode", "notice_delivery_date"}

# Numeric fields: allow ≤2% variance before flagging as contradiction
NUMERIC_FIELDS = {"cheque_amount", "outstanding_amount"}

# Fields to compare across documents
COMPARABLE_FIELDS = CRITICAL_FIELDS | WARNING_FIELDS

# Map each field → its authoritative document types for cross-document comparison
FIELD_AUTHORITATIVE_TYPES: Dict[str, Set[str]] = {
    "cheque_number":        {"CHEQUE", "BANK_MEMO", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "cheque_date":          {"CHEQUE", "LEGAL_NOTICE", "BANK_MEMO", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "cheque_amount":        {"CHEQUE", "LEGAL_NOTICE", "BANK_MEMO", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "dishonour_date":       {"BANK_MEMO", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "memo_date":            {"BANK_MEMO", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "dishonour_reason":     {"BANK_MEMO", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "notice_date":          {"LEGAL_NOTICE", "TRACKING_REPORT", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "notice_delivery_date": {"TRACKING_REPORT", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT"},
    "notice_mode":          {"LEGAL_NOTICE", "TRACKING_REPORT"},
    "agreement_date":       {"AGREEMENT"},
    "transaction_date":     {"AGREEMENT"},
    "complainant_name":     {"LEGAL_NOTICE", "AGREEMENT", "INVOICE_LEDGER", "SECTION_138_COMPLAINT", "COMPLAINT", "CHEQUE"},
    "accused_name":         {"LEGAL_NOTICE", "AGREEMENT", "INVOICE_LEDGER", "SECTION_138_COMPLAINT", "COMPLAINT", "CHEQUE"},
    "bank_name":            {"CHEQUE", "BANK_MEMO", "LEGAL_NOTICE", "SECTION_138_COMPLAINT", "COMPLAINT"},
}


def _format_field_label(field: str, workflow_type: str = "cheque_bounce") -> str:
    if field == "ipc_section":
        return "NI Act Section" if workflow_type == "cheque_bounce" else "Penal Sections / Charges"
    if field == "agreement_date":
        return "Agreement Executed Date"
    if field == "transaction_date":
        return "Transaction Date"
    custom_labels = {
        "complainant_name": "Complainant",
        "accused_name": "Accused",
        "cheque_number": "Cheque Number",
        "cheque_amount": "Cheque Amount",
        "cheque_amount_words": "Cheque Amount in Words",
        "cheque_date": "Cheque Date",
        "bank_name": "Bank Name",
        "dishonour_date": "Dishonour Date",
        "dishonour_reason": "Dishonour Reason",
        "memo_date": "Bank Memo Date",
        "notice_date": "Legal Notice Date",
        "notice_delivery_date": "Notice Delivery Date",
        "notice_mode": "Notice Mode",
        "invoice_date": "Invoice Date",
        "part_payment_date": "Part Payment Date",
        "filing_date": "Filing Date",
        "case_number": "Case / Complaint Number",
    }
    return custom_labels.get(field, field.replace("_", " ").title())


def _infer_type_from_facts(doc: "ExtractedDocument") -> str:
    """
    If doc_type is OTHER (likely due to poor OCR or zero-text image),
    infer the real document type from extracted facts.
    """
    if doc.doc_type != "OTHER":
        return doc.doc_type
    facts = doc.facts

    def _has_value(field: str) -> bool:
        raw = facts.get(field, {})
        return isinstance(raw, dict) and raw.get("value") is not None and raw.get("confidence", 0) >= 0.30

    # Cheque: has cheque number or account+bank+amount combo
    if _has_value("cheque_number") or (
        _has_value("bank_name") and _has_value("cheque_amount") and not _has_value("dishonour_reason")
    ):
        return "CHEQUE"
    # Bank memo: has dishonour reason or memo_date
    if _has_value("dishonour_reason") or _has_value("dishonour_date") or _has_value("memo_date"):
        return "BANK_MEMO"
    # Legal notice: has notice date + 15-day clause
    if _has_value("notice_date") and _has_value("notice_15day_clause"):
        return "LEGAL_NOTICE"
    # Tracking: has notice delivery date or notice mode involving post
    if _has_value("notice_delivery_date"):
        mode = (facts.get("notice_mode") or {}).get("value", "")
        if mode and "post" in str(mode).lower():
            return "TRACKING_REPORT"
    # Agreement: has transaction date or invoice date + parties
    if (_has_value("transaction_date") or _has_value("invoice_date")) and (_has_value("complainant_name") or _has_value("accused_name")):
        return "AGREEMENT"

    return "OTHER"  # Still unknown


def _normalize_for_compare(field: str, value: Any) -> str:
    """Normalize a value for contradiction comparison."""
    if value is None:
        return ""
    v = str(value).strip().lower()
    if field in NUMERIC_FIELDS:
        # Strip formatting, keep numeric
        v = re.sub(r"[^0-9.]", "", v)
    v = re.sub(r"\s+", " ", v)
    return v


def _numeric_mismatch(field: str, val_a: Any, val_b: Any) -> bool:
    """Returns True if numeric values differ by more than 2%."""
    try:
        a = float(re.sub(r"[^0-9.]", "", str(val_a)))
        b = float(re.sub(r"[^0-9.]", "", str(val_b)))
        if a == 0 and b == 0:
            return False
        return abs(a - b) / max(abs(a), abs(b)) > 0.02
    except (ValueError, ZeroDivisionError):
        return False


def detect_contradictions(documents: List[ExtractedDocument]) -> List[Contradiction]:
    """
    Compare extracted facts across all documents.
    NEVER silently discard a conflicting value — every conflict becomes a Contradiction.
    Only compares documents that are authoritative sources for each field.
    Normalizes entities before comparison to prevent false party contradictions.
    """
    contradictions: List[Contradiction] = []

    for field in COMPARABLE_FIELDS:
        auth_types = FIELD_AUTHORITATIVE_TYPES.get(field)

        # Collect all non-null values with their source info from authoritative documents
        doc_values = []
        for doc in documents:
            effective_type = _infer_type_from_facts(doc)
            if auth_types and effective_type not in auth_types:
                continue

            raw = doc.facts.get(field, {})
            if not isinstance(raw, dict):
                continue
            val = raw.get("value")
            conf = raw.get("confidence", 0.0)
            snip = raw.get("snippet") or doc.raw_text_preview[:100]
            if val is not None and conf > 0.15:
                doc_values.append({
                    "doc": doc.filename,
                    "doc_type": effective_type,
                    "value": val,
                    "confidence": conf,
                    "snippet": snip,
                })

        if len(doc_values) < 2:
            continue  # Need at least 2 authoritative sources to compare

        # Compare all pairs
        for i in range(len(doc_values)):
            for j in range(i + 1, len(doc_values)):
                a = doc_values[i]
                b = doc_values[j]
                norm_a = _normalize_for_compare(field, a["value"])
                norm_b = _normalize_for_compare(field, b["value"])

                mismatch = False
                if field in ("complainant_name", "accused_name", "authorized_person"):
                    # Normalize party names to strip OCR truncation and prefixes
                    mismatch = not _is_party_match(a["value"], b["value"])
                elif field in NUMERIC_FIELDS:
                    mismatch = _numeric_mismatch(field, a["value"], b["value"])
                else:
                    mismatch = norm_a != norm_b and bool(norm_a) and bool(norm_b)

                if mismatch:
                    severity = "CRITICAL" if field in CRITICAL_FIELDS else "WARNING"
                    human_field = field.replace("_", " ").title()

                    # High-fidelity custom descriptions for genuine Section 138 discrepancies
                    if field == "cheque_amount":
                        try:
                            notice_v = next((v["value"] for v in doc_values if v["doc_type"] == "LEGAL_NOTICE"), None)
                            other_v = next((v["value"] for v in doc_values if v["doc_type"] in ("CHEQUE", "SECTION_138_COMPLAINT", "COMPLAINT", "BANK_MEMO")), None)
                            if notice_v is not None and other_v is not None:
                                c_amt, n_amt = float(other_v), float(notice_v)
                            else:
                                va, vb = float(a["value"]), float(b["value"])
                                c_amt, n_amt = max(va, vb), min(va, vb)
                            desc = (
                                f"⚠ CHEQUE AMOUNT CONFLICT: Cheque / supporting evidence: ₹{c_amt:,.0f} "
                                f"vs Legal Notice: ₹{n_amt:,.0f}. Lawyer must resolve before filing."
                            )
                        except Exception:
                            desc = f"⚠ CHEQUE AMOUNT CONFLICT: {a['value']} vs {b['value']}. Lawyer must resolve before filing."
                    elif field == "cheque_date":
                        notice_v = next((v["value"] for v in doc_values if v["doc_type"] == "LEGAL_NOTICE"), a["value"])
                        other_v = next((v["value"] for v in doc_values if v["doc_type"] in ("CHEQUE", "SECTION_138_COMPLAINT", "COMPLAINT", "BANK_MEMO")), b["value"])
                        desc = (
                            f"⚠ CHEQUE DATE CONFLICT: Cheque / complaint: {other_v} "
                            f"vs Legal Notice: {notice_v}. Lawyer must resolve before filing."
                        )
                    elif field == "notice_delivery_date":
                        notice_v = next((v["value"] for v in doc_values if v["doc_type"] == "LEGAL_NOTICE"), a["value"])
                        other_v = next((v["value"] for v in doc_values if v["doc_type"] in ("TRACKING_REPORT", "SECTION_138_COMPLAINT", "COMPLAINT")), b["value"])
                        desc = (
                            f"⚠ NOTICE DELIVERY DATE CONFLICT: Postal tracking: {other_v} "
                            f"vs Legal Notice: {notice_v}. Lawyer must resolve before filing."
                        )
                    else:
                        desc = (
                            f"{human_field} mismatch: "
                            f"'{a['doc']}' ({a['doc_type']}) shows {a['value']!r} "
                            f"vs '{b['doc']}' ({b['doc_type']}) shows {b['value']!r}. "
                            f"Lawyer must resolve before filing."
                        )

                    # Check if we already have this contradiction (avoid duplicates)
                    existing = next((c for c in contradictions if c.field == field), None)
                    if existing:
                        existing_vals = [str(ev["value"]) for ev in existing.values]
                        if str(b["value"]) not in existing_vals:
                            existing.values.append(b)
                    else:
                        contradictions.append(Contradiction(
                            field=field,
                            severity=severity,
                            values=doc_values,
                            description=desc,
                        ))
                    break  # one contradiction per field is enough
            if any(c.field == field for c in contradictions):
                break

    return contradictions


# ─────────────────────────────────────────────────────────────────────────────
# MISSING FACTS & DOCUMENTS DETECTOR (workflow-specific)
# ─────────────────────────────────────────────────────────────────────────────

def detect_missing_facts(documents: List[ExtractedDocument], workflow_type: str) -> List[Dict[str, str]]:
    """Identify required facts for this workflow that were not found in any uploaded document."""
    required = WORKFLOW_REQUIRED_FACTS.get(workflow_type, [])
    missing = []

    for req in required:
        field = req["field"]
        # Check if any document found this field with decent confidence
        found = False
        for doc in documents:
            raw = doc.facts.get(field, {})
            if isinstance(raw, dict) and raw.get("value") is not None and raw.get("confidence", 0) >= 0.30:
                found = True
                break
        if not found:
            # If field is transaction_date, but agreement_date or invoice_date was established, debt proof is satisfied
            if field == "transaction_date":
                has_alt_debt = any(
                    (isinstance(d.facts.get("agreement_date"), dict) and d.facts["agreement_date"].get("value"))
                    or (isinstance(d.facts.get("invoice_date"), dict) and d.facts["invoice_date"].get("value"))
                    for d in documents
                )
                if has_alt_debt:
                    continue
            missing.append({
                "field": field,
                "required_for": req["required_for"],
                "hint": f"Upload a document containing '{_format_field_label(field, workflow_type)}' or enter it manually in the wizard.",
            })

    return missing



def detect_missing_documents(documents: List["ExtractedDocument"], workflow_type: str) -> List[Dict[str, str]]:
    """Identify required document types for this workflow that were not uploaded.
    Uses a fact-based fallback re-classification for docs that got stuck as OTHER.
    """
    required = WORKFLOW_REQUIRED_DOCS.get(workflow_type, [])
    # Build effective type set: use fact-based re-classification for OTHER docs
    uploaded_types = set()
    for doc in documents:
        effective_type = _infer_type_from_facts(doc)
        uploaded_types.add(effective_type)
        if effective_type != doc.doc_type:
            logger.info(
                f"Re-classified '{doc.filename}' from {doc.doc_type} → {effective_type} "
                f"based on extracted facts"
            )

    missing = []
    for req in required:
        if req["doc_type"] not in uploaded_types:
            missing.append({
                "doc_type": req["doc_type"],
                "reason": req["reason"],
                "hint": f"Upload a '{req['doc_type'].replace('_', ' ').title()}' document.",
            })

    return missing


# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

DATE_FIELD_LABELS: Dict[str, str] = {
    "agreement_date":      "Agreement Executed Date",
    "invoice_date":        "Tax Invoice / Bill Raised",
    "part_payment_date":   "Part Payment Received",
    "transaction_date":    "Transaction Date",
    "cheque_date":         "Cheque Issued",
    "dishonour_date":      "Cheque Dishonoured",
    "memo_date":           "Bank Return Memo Issued",
    "notice_date":         "Legal Demand Notice Dispatched",
    "notice_delivery_date":"Legal Notice Delivered / Served",
    "filing_date":         "Complaint / Case Filed",
    "npa_date":            "Account Classified NPA",
    "incident_date":       "Incident / Offence Date",
}


def _parse_date_for_sort(date_str: str) -> datetime:
    """Parse various date formats for sorting."""
    if not date_str:
        return datetime(9999, 12, 31)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
                "%d %B %Y", "%d %b %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime(9999, 12, 31)


DOC_PRIORITY_FOR_DATE: Dict[str, List[str]] = {
    "agreement_date":      ["AGREEMENT", "SECTION_138_COMPLAINT", "COMPLAINT"],
    "cheque_date":         ["CHEQUE", "BANK_MEMO", "SECTION_138_COMPLAINT", "COMPLAINT", "LEGAL_NOTICE"],
    "notice_delivery_date":["TRACKING_REPORT", "SECTION_138_COMPLAINT", "COMPLAINT", "LEGAL_NOTICE"],
    "invoice_date":        ["INVOICE_LEDGER", "SECTION_138_COMPLAINT", "COMPLAINT"],
    "part_payment_date":   ["INVOICE_LEDGER", "SECTION_138_COMPLAINT", "COMPLAINT"],
    "dishonour_date":      ["BANK_MEMO", "SECTION_138_COMPLAINT", "COMPLAINT"],
    "memo_date":           ["BANK_MEMO", "SECTION_138_COMPLAINT", "COMPLAINT"],
    "notice_date":         ["LEGAL_NOTICE", "TRACKING_REPORT", "SECTION_138_COMPLAINT", "COMPLAINT"],
    "filing_date":         ["SECTION_138_COMPLAINT", "COMPLAINT", "COURT_ORDER"],
}


def build_timeline(
    documents: List[ExtractedDocument],
    missing_facts: List[Dict],
    contradictions: Optional[List[Contradiction]] = None
) -> List[TimelineEvent]:
    """Build a chronological event timeline from all extracted date fields."""
    events: List[TimelineEvent] = []
    seen_dates: Dict[str, Tuple[str, str, str]] = {}  # field → (date, filename, doc_type)

    conflicted_fields = set()
    if contradictions:
        for c in contradictions:
            if hasattr(c, "field"):
                conflicted_fields.add(c.field)
            elif isinstance(c, dict) and "field" in c:
                conflicted_fields.add(c["field"])

    # Collect best authoritative date for each field
    for field, label in DATE_FIELD_LABELS.items():
        doc_pref = DOC_PRIORITY_FOR_DATE.get(field, [])
        best_entry = None

        for doc in documents:
            raw = doc.facts.get(field, {})
            if not isinstance(raw, dict):
                continue
            val = raw.get("value")
            conf = raw.get("confidence", 0.0)
            if not val or conf < 0.25:
                continue

            eff_type = _infer_type_from_facts(doc)
            prio = doc_pref.index(eff_type) if eff_type in doc_pref else 999
            if best_entry is None or prio < best_entry[0] or (prio == best_entry[0] and conf > best_entry[1]):
                best_entry = (prio, conf, str(val), doc.filename, eff_type)

        if best_entry:
            val_str = best_entry[2]
            src_doc = best_entry[3]
            is_conf = field in conflicted_fields
            display_label = f"{label} ⚠" if is_conf else label
            seen_dates[field] = (val_str, src_doc, best_entry[4])
            events.append(TimelineEvent(
                date=val_str,
                label=display_label,
                source_document=src_doc,
                field_name=field,
                is_missing=False,
                is_conflicted=is_conf,
            ))

    # Add missing date fields as placeholder events (skip transaction_date if invoice/part payment/agreement exists)
    has_invoice_or_debt = "invoice_date" in seen_dates or "part_payment_date" in seen_dates or "agreement_date" in seen_dates
    missing_fields = {m["field"] for m in missing_facts}
    for field, label in DATE_FIELD_LABELS.items():
        if field == "transaction_date" and has_invoice_or_debt:
            continue
        if field in missing_fields and field not in seen_dates:
            events.append(TimelineEvent(
                date="",
                label=f"{label} ← MISSING",
                source_document="",
                field_name=field,
                is_missing=True,
                is_conflicted=False,
            ))

    # Sort by parsed date, missing events go to end
    events.sort(key=lambda e: _parse_date_for_sort(e.date))
    return events


# ─────────────────────────────────────────────────────────────────────────────
# CASE STORY — ONLY FROM VERIFIED FACTS
# ─────────────────────────────────────────────────────────────────────────────

def generate_case_story(
    verified_facts: Dict[str, Any],
    workflow_type: str,
    contradictions: Optional[List[Dict[str, Any]]] = None,
    missing_facts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """
    Generates safe, fact-grounded case story and formal summary.
    Distinguishes:
    1. Verified facts (only facts with no conflicts and confirmed values)
    2. Unresolved contradictions (neutral conflict statements)
    3. Missing / pending items (requires lawyer verification)
    Never uses bracket placeholders [Like This] or assumes 15-day non-payment
    without verified delivery proof.
    """
    from llm_engine import _invoke_llm, LLM_AVAILABLE

    vf = verified_facts or {}
    contras = contradictions or []
    missing = missing_facts or []
    contra_fields = {c.get("field") for c in contras if isinstance(c, dict)}

    # Helper: only use fact if it is not in contradiction
    def _safe_get(field: str) -> Optional[str]:
        if field in contra_fields:
            return None
        val = vf.get(field)
        if val is None or str(val).strip() == "" or str(val).startswith("["):
            return None
        return str(val).strip()

    comp = _safe_get("complainant_name")
    accused = _safe_get("accused_name")
    chq_no = _safe_get("cheque_number")
    bank = _safe_get("bank_name")
    chq_amt = _safe_get("cheque_amount")
    if chq_amt and chq_amt.replace(".", "").isdigit():
        try:
            chq_amt = f"₹{float(chq_amt):,.0f}"
        except (ValueError, TypeError):
            pass
    chq_date = _safe_get("cheque_date")
    dis_date = _safe_get("dishonour_date")
    dis_reason = _safe_get("dishonour_reason")
    memo_date = _safe_get("memo_date")
    notice_date = _safe_get("notice_date")
    notice_mode = _safe_get("notice_mode")
    delivery_date = _safe_get("notice_delivery_date")
    filing_date = _safe_get("filing_date")
    txn_date = _safe_get("transaction_date")
    auth_person = _safe_get("authorized_person")

    verified_sentences = []
    conflict_sentences = []
    unknown_sentences = []

    # 1. Verified facts construction
    if workflow_type == "cheque_bounce":
        # Parties
        if comp and accused:
            comp_desc = f"{comp}" + (f" represented by authorized representative {auth_person}" if auth_person else "")
            verified_sentences.append(f"{comp_desc} engaged in commercial dealings with {accused}.")
        elif comp:
            verified_sentences.append(f"Proceedings initiated on behalf of {comp}.")
        elif accused:
            verified_sentences.append(f"Proceedings initiated against {accused}.")
        else:
            unknown_sentences.append("Complainant and accused party identities require advocate verification.")

        # Transaction
        if txn_date:
            verified_sentences.append(f"The underlying transaction was recorded on {txn_date}.")

        # Cheque issuance
        chq_parts = []
        if chq_no:
            chq_parts.append(f"No. {chq_no}")
        if bank:
            chq_parts.append(f"drawn on {bank}")
        if chq_amt:
            chq_parts.append(f"for {chq_amt}")
        if chq_date:
            chq_parts.append(f"dated {chq_date}")

        if chq_parts:
            verified_sentences.append(f"Cheque ({', '.join(chq_parts)}) was issued in discharge of liability.")

        # Dishonour
        if dis_date:
            reason_str = f" with endorsement '{dis_reason}'" if dis_reason else ""
            memo_str = f" (return memo dated {memo_date})" if memo_date else ""
            verified_sentences.append(f"The cheque was reported dishonoured on {dis_date}{reason_str}{memo_str}.")

        # Legal notice
        if notice_date:
            mode_str = f" via {notice_mode}" if notice_mode else ""
            verified_sentences.append(f"A statutory demand notice under Section 138 of the Negotiable Instruments Act was dispatched on {notice_date}{mode_str}.")

        # Delivery & Statutory period (STRICT: only if delivery date verified and no notice/delivery conflict)
        if delivery_date and "notice_delivery_date" not in contra_fields:
            if filing_date:
                verified_sentences.append(f"Notice was served on {delivery_date}. The formal complaint was registered on {filing_date}.")
            else:
                verified_sentences.append(f"Notice was recorded as delivered on {delivery_date}.")
        else:
            if "notice_delivery_date" not in contra_fields:
                unknown_sentences.append("The notice delivery date requires verification from postal tracking records.")

    elif workflow_type == "sarfaesi":
        borrower = _safe_get("borrower_name")
        bank_name = _safe_get("bank_name")
        npa_date = _safe_get("npa_date")
        out_amt = _safe_get("outstanding_amount")
        if bank_name and borrower:
            verified_sentences.append(f"{bank_name} extended credit facilities to {borrower}.")
        if npa_date:
            verified_sentences.append(f"The borrower's loan account was classified as Non-Performing Asset (NPA) on {npa_date}.")
        if out_amt:
            verified_sentences.append(f"The recorded outstanding balance is ₹{out_amt}.")
        if notice_date:
            verified_sentences.append(f"Demand notice under Section 13(2) of the SARFAESI Act was issued on {notice_date}.")
    else:
        if comp and accused:
            verified_sentences.append(f"Matter involving {comp} and {accused}.")
        if txn_date:
            verified_sentences.append(f"Relevant transaction executed on {txn_date}.")

    # 2. Contradiction sentences
    for c in contras:
        if not isinstance(c, dict):
            continue
        c_field = c.get("field", "")
        c_desc = c.get("description", "")
        human_field = c_field.replace("_", " ").title()
        c_vals = c.get("values", [])
        if len(c_vals) >= 2:
            val_strs = [f"'{v.get('value')}' ({v.get('doc', v.get('doc_type', 'doc'))})" for v in c_vals]
            conflict_sentences.append(f"The uploaded documents contain conflicting {human_field.lower()} entries: {' vs '.join(val_strs)}. Advocate verification is required before filing.")
        elif c_desc:
            conflict_sentences.append(c_desc)
        else:
            conflict_sentences.append(f"Unresolved contradiction in {human_field}.")

    # 3. Missing / Unknown sentences
    for m in missing:
        if isinstance(m, dict):
            fld = m.get("field", "")
            if fld not in contra_fields and fld not in vf:
                req = m.get("required_for", "Case analysis")
                unknown_sentences.append(f"{fld.replace('_', ' ').title()} is not verified (required for {req}).")

    # Combine into clean, structured sections
    sections = []
    if verified_sentences:
        sections.append("Verified Case Facts:\n" + "\n".join(f"• {s}" for s in verified_sentences))
    if conflict_sentences:
        sections.append("⚠ Unresolved Contradictions (Review Required):\n" + "\n".join(f"• {s}" for s in conflict_sentences))
    if unknown_sentences:
        sections.append("Pending / Unverified Information:\n" + "\n".join(f"• {s}" for s in unknown_sentences))

    case_story = "\n\n".join(sections) if sections else "No verified case facts available yet. Upload documents and complete advocate review."

    # Build concise summary
    status_label = "✅ Verified Case Facts" if (not conflict_sentences and not unknown_sentences) else f"⚠ Review Required ({len(conflict_sentences)} Conflicts / {len(unknown_sentences)} Missing)"
    summary_parts = [f"Status: {status_label}"]
    if comp: summary_parts.append(f"Complainant: {comp}")
    if accused: summary_parts.append(f"Accused: {accused}")
    if chq_no: summary_parts.append(f"Cheque No: {chq_no}")
    if chq_amt: summary_parts.append(f"Amount: {chq_amt}")
    if dis_date: summary_parts.append(f"Dishonour Date: {dis_date}")
    if notice_date: summary_parts.append(f"Notice Date: {notice_date}")
    if filing_date: summary_parts.append(f"Filing Date: {filing_date}")
    case_summary = " | ".join(summary_parts)

    return {
        "case_story": case_story,
        "case_summary": case_summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STORE (in-memory, keyed by session_id)
# ─────────────────────────────────────────────────────────────────────────────

_sessions: Dict[str, Dict[str, Any]] = {}


def _get_session(session_id: str) -> Dict[str, Any]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found. Please call /extract first.")
    return _sessions[session_id]


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/extract", summary="Upload documents → OCR → Fact Extraction")
async def extract_facts(
    request: Request,
    files: List[UploadFile] = File(...),
    doc_types: Optional[str] = Form(""),    # Comma-separated list, one per file
    workflow_type: str = Form("cheque_bounce"),
    user_id: str = Depends(get_current_user_optional),
):
    """
    Upload one or more legal documents. For each file:
    1. Run OCR (3-path pipeline)
    2. Detect document type
    3. Extract structured facts with source evidence (value, confidence, page, snippet)
    Returns a session_id and list of per-document extraction results.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    ALLOWED_MIMES = {
        "application/pdf", "image/jpeg", "image/png", "image/webp",
        "image/tiff", "image/bmp", "text/plain",
    }

    doc_type_hints = [dt.strip().upper() for dt in (doc_types or "").split(",") if dt.strip()]

    session_id = f"DI-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

    # ── Fast concurrent file read ──────────────────────────────────────────────
    # Read all uploaded files concurrently instead of sequentially, removing
    # sequential await overhead when multiple files are uploaded at once.
    import asyncio as _asyncio
    async def _read_file(idx, file):
        content = await file.read()
        return idx, file.filename or f"document_{idx+1}", content, file.content_type or "application/octet-stream"

    read_results = await _asyncio.gather(*[_read_file(i, f) for i, f in enumerate(files)])

    file_items = []
    for idx, filename, content, mime in read_results:
        if mime not in ALLOWED_MIMES:
            logger.warning(f"Unsupported MIME '{mime}' for '{filename}' — attempting anyway.")
        if len(content) == 0:
            logger.warning(f"Empty file uploaded: {filename}")
            continue
        doc_hint = doc_type_hints[idx] if idx < len(doc_type_hints) else ""
        file_items.append((idx, filename, content, mime, doc_hint))

    def _process_single_doc(item):
        idx, filename, content, mime, doc_hint = item
        ocr_result = run_ocr_pipeline(content, mime, filename)
        full_text = ocr_result["text"]
        pages_data = ocr_result["pages"]
        ocr_method = ocr_result["method"]

        if doc_hint and doc_hint in DOC_TYPE_SIGNATURES and doc_hint != "OTHER":
            doc_type = doc_hint
        else:
            doc_type = classify_document(filename, full_text)

        logger.info(f"Processing '{filename}' → doc_type={doc_type}, OCR={ocr_method}, chars={ocr_result['char_count']}")

        raw_facts = extract_facts_with_llm(
            full_text,
            doc_type,
            filename,
            pages_data,
            file_bytes=content,
            mime_type=mime
        )
        return (idx, filename, content, mime, doc_type, ocr_result, raw_facts)

    import concurrent.futures
    # Increase max workers: each doc is IO-bound (OCR + LLM network call)
    max_workers = min(len(file_items), 6) if file_items else 1  # was 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        processed_results = list(executor.map(_process_single_doc, file_items))

    processed_results.sort(key=lambda x: x[0])

    extracted_documents: List[ExtractedDocument] = []
    for (idx, filename, content, mime, doc_type, ocr_result, raw_facts) in processed_results:
        full_text = ocr_result["text"]
        page_count = ocr_result["page_count"]
        ocr_method = ocr_result["method"]

        # Build structured confidence / snippet maps
        fact_confidences: Dict[str, float] = {}
        fact_snippets: Dict[str, str] = {}
        fact_pages: Dict[str, int] = {}
        clean_facts: Dict[str, Any] = {}

        for field, entry in raw_facts.items():
            if field == "doc_type_detected":
                continue
            if isinstance(entry, dict):
                clean_facts[field] = entry
                fact_confidences[field] = float(entry.get("confidence", 0.0))
                fact_snippets[field] = str(entry.get("snippet") or "")
                pg = entry.get("page")
                if pg is not None:
                    try:
                        fact_pages[field] = int(pg)
                    except (TypeError, ValueError):
                        pass

        # Accept LLM doc_type refinement only if current classification is OTHER
        llm_detected = raw_facts.get("doc_type_detected", "")
        if llm_detected and llm_detected in DOC_TYPE_SIGNATURES and doc_type == "OTHER":
            doc_type = llm_detected
            logger.info(f"LLM refined doc_type of '{filename}' to {doc_type}")

        doc_obj = ExtractedDocument(
            document_id=f"{session_id}-DOC{idx+1}",
            filename=filename,
            doc_type=doc_type,
            ocr_method=ocr_method,
            page_count=page_count,
            raw_text_preview=(full_text[:500] + "...") if len(full_text) > 500 else full_text,
            facts=clean_facts,
            fact_confidences=fact_confidences,
            fact_snippets=fact_snippets,
            fact_pages=fact_pages,
        )
        extracted_documents.append(doc_obj)

    # Automatically synthesize extracted facts to register case in cases_v2
    creditor_name = ""
    debtor_name = ""
    case_amount = ""
    for doc in extracted_documents:
        for fname, fentry in (doc.facts or {}).items():
            val = fentry.get("value") if isinstance(fentry, dict) else fentry
            if not val:
                continue
            s_val = str(val).strip()
            if not s_val or s_val.lower() in ("null", "none", "unknown"):
                continue
            if fname in ("payee_name", "complainant_name", "creditor_name", "applicant_name", "lender_name") and not creditor_name:
                creditor_name = s_val
            elif fname in ("drawer_name", "accused_name", "debtor_name", "respondent_name", "borrower_name") and not debtor_name:
                debtor_name = s_val
            elif fname in ("cheque_amount", "loan_amount", "claimed_amount", "amount", "total_outstanding") and not case_amount:
                case_amount = s_val

    first_filename = files[0].filename if files and files[0].filename else "Document"
    if creditor_name and debtor_name:
        case_name = f"{creditor_name} vs {debtor_name}"
    elif creditor_name:
        case_name = f"{creditor_name} - Matter"
    elif debtor_name:
        case_name = f"In re: {debtor_name}"
    else:
        clean_fn = re.sub(r'\.[a-zA-Z0-9]+$', '', first_filename).replace('_', ' ').replace('-', ' ').title()
        case_name = f"{clean_fn} - Auto Docket"

    actual_user = user_id or "ANONYMOUS"
    now_dt = datetime.now()
    case_id = f"CSE-{now_dt.strftime('%Y-%m')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        creditor_dict = {"name": creditor_name} if creditor_name else {}
        debtor_dict = {"name": debtor_name} if debtor_name else {}
        fin_dict = {"amount": case_amount} if case_amount else {}
        DatabaseManager.cms_create_case(
            case_id=case_id,
            user_id=actual_user,
            case_name=case_name,
            case_type=workflow_type or "section_138",
            priority="medium",
            description=f"Auto-created case from {len(extracted_documents)} uploaded document(s). Primary doc: {first_filename}",
            tags=["auto-created", workflow_type],
            creditor_data=creditor_dict,
            debtor_data=debtor_dict,
            financial_data=fin_dict,
            access_level="private"
        )
        logger.info(f"Auto-created case {case_id} ('{case_name}') for user '{actual_user}'")
    except Exception as e:
        logger.error(f"Failed to auto-create case in cms_create_case: {e}")

    # Store in session
    _sessions[session_id] = {
        "documents": extracted_documents,
        "workflow_type": workflow_type,
        "created_at": datetime.now().isoformat(),
        "verified_facts": None,
        "case_id": case_id,
        "case_name": case_name,
    }

    return {
        "success": True,
        "session_id": session_id,
        "case_id": case_id,
        "case_name": case_name,
        "workflow_type": workflow_type,
        "documents_processed": len(extracted_documents),
        "documents": [doc.model_dump() for doc in extracted_documents],
    }


@router.post("/analyze", summary="Cross-document analysis → Contradictions, Missing Facts, Timeline")
async def analyze_case(payload: AnalyzePayload):
    """
    Cross-document comparison engine:
    - Detects contradictions (NEVER silently discards conflicting values)
    - Detects missing facts and documents (workflow-specific)
    - Builds chronological timeline
    """
    session = _get_session(payload.session_id)
    documents: List[ExtractedDocument] = session["documents"]
    workflow_type = payload.workflow_type or session.get("workflow_type", "cheque_bounce")
    session["workflow_type"] = workflow_type

    contradictions = detect_contradictions(documents)
    missing_facts = detect_missing_facts(documents, workflow_type)
    missing_docs = detect_missing_documents(documents, workflow_type)
    timeline = build_timeline(documents, missing_facts, contradictions)

    # Build all_extracted_facts: field → list of [value, source, confidence, snippet]
    all_facts: Dict[str, List[Dict[str, Any]]] = {}
    for doc in documents:
        for field, raw in doc.facts.items():
            if not isinstance(raw, dict):
                continue
            val = raw.get("value")
            conf = raw.get("confidence", 0.0)
            snip = raw.get("snippet") or ""
            pg = raw.get("page")
            if val is not None:
                if field not in all_facts:
                    all_facts[field] = []
                all_facts[field].append({
                    "value": val,
                    "confidence": conf,
                    "source_document": doc.filename,
                    "source_page": pg,
                    "source_snippet": snip,
                    "doc_type": doc.doc_type,
                })

    session["all_facts"] = all_facts
    session["contradictions"] = [c.model_dump() for c in contradictions]
    session["missing_facts"] = missing_facts
    session["missing_docs"] = missing_docs
    session["timeline"] = [t.model_dump() for t in timeline]

    is_fully_verified = len(contradictions) == 0 and len(missing_facts) == 0
    verification_status = "verified" if is_fully_verified else "review_required"
    status_label = (
        "✅ Verified Case Facts"
        if is_fully_verified
        else f"⚠ Review Required — {len(contradictions)} unresolved contradiction{'s' if len(contradictions) != 1 else ''} / {len(missing_facts)} missing fact{'s' if len(missing_facts) != 1 else ''}"
    )

    return {
        "success": True,
        "session_id": payload.session_id,
        "workflow_type": workflow_type,
        "documents_analyzed": len(documents),
        "status": verification_status,
        "status_label": status_label,
        "is_fully_verified": is_fully_verified,
        "all_extracted_facts": all_facts,
        "contradictions": [c.model_dump() for c in contradictions],
        "missing_facts": missing_facts,
        "missing_documents": missing_docs,
        "timeline": [t.model_dump() for t in timeline],
        "stats": {
            "total_contradictions": len(contradictions),
            "critical_contradictions": sum(1 for c in contradictions if c.severity == "CRITICAL"),
            "missing_facts_count": len(missing_facts),
            "missing_docs_count": len(missing_docs),
        }
    }


@router.post("/verify", summary="Submit lawyer-verified facts")
async def verify_facts(payload: VerifyPayload):
    """
    Receive the lawyer's reviewed and corrected fact set.
    Stores verified facts in session — these are the authoritative facts
    that will be used for case story generation and wizard auto-fill.
    """
    session = _get_session(payload.session_id)

    if not payload.verified_facts:
        raise HTTPException(status_code=400, detail="verified_facts cannot be empty.")

    session["verified_facts"] = payload.verified_facts
    session["verified_at"] = datetime.now().isoformat()

    # Contradictions in session
    contradictions = session.get("contradictions", [])
    contra_fields = {c.get("field") for c in contradictions if isinstance(c, dict)}
    resolved_contras = set(payload.resolved_contradictions or [])
    active_conflicts = contra_fields - resolved_contras

    # Compute confidence-aware smart fill recommendation
    all_facts = session.get("all_facts", {})
    fill_recommendations: Dict[str, str] = {}

    for field, val in payload.verified_facts.items():
        if val is None:
            continue
        field_entries = all_facts.get(field, [])
        max_conf = max((e.get("confidence", 0.0) for e in field_entries), default=0.0) if field_entries else 0.0

        # Exact user rules:
        # High confidence + no conflict + approved -> AUTO_FILL
        # High confidence + conflict -> REVIEW REQUIRED (never auto-fill conflicting fields)
        # Medium confidence -> REVIEW REQUIRED
        # Low confidence -> DO NOT FILL
        if field in active_conflicts:
            fill_recommendations[field] = "REVIEW"
        elif max_conf >= 0.80:
            fill_recommendations[field] = "AUTO_FILL"
        elif max_conf >= 0.50:
            fill_recommendations[field] = "REVIEW"
        else:
            fill_recommendations[field] = "DO_NOT_FILL"

    # Evaluate verification status
    workflow_type = session.get("workflow_type", "cheque_bounce")
    required = WORKFLOW_REQUIRED_FACTS.get(workflow_type, [])
    unverified_required = [
        req["field"] for req in required
        if req["field"] not in payload.verified_facts
        or payload.verified_facts[req["field"]] is None
        or str(payload.verified_facts[req["field"]]).strip() == ""
        or req["field"] in active_conflicts
    ]

    is_fully_verified = len(active_conflicts) == 0 and len(unverified_required) == 0
    verification_status = "verified" if is_fully_verified else "review_required"
    status_label = (
        "✅ Verified Case Facts"
        if is_fully_verified
        else f"⚠ Review Required — {len(active_conflicts)} unresolved contradiction{'s' if len(active_conflicts) != 1 else ''} / {len(unverified_required)} missing fact{'s' if len(unverified_required) != 1 else ''}"
    )

    return {
        "success": True,
        "session_id": payload.session_id,
        "status": verification_status,
        "status_label": status_label,
        "is_fully_verified": is_fully_verified,
        "unresolved_contradictions_count": len(active_conflicts),
        "missing_facts_count": len(unverified_required),
        "verified_facts": payload.verified_facts,
        "fill_recommendations": fill_recommendations,
        "message": status_label,
    }


@router.post("/case-story", summary="Generate case story from VERIFIED facts only")
async def generate_story(payload: CaseStoryPayload):
    """
    Generate case story and formal summary.
    ONLY called after lawyer verification — uses verified_facts, not raw extracted facts.
    This prevents incorrect extractions from becoming confident-looking narratives.
    """
    session = _get_session(payload.session_id)

    # Prefer session-stored verified facts; payload can override
    verified = payload.verified_facts or session.get("verified_facts")
    if not verified:
        raise HTTPException(
            status_code=400,
            detail=(
                "No verified facts found. "
                "Call POST /verify with lawyer-reviewed facts before generating the case story."
            )
        )

    workflow_type = payload.workflow_type or session.get("workflow_type", "cheque_bounce")
    contradictions = session.get("contradictions", [])
    missing_facts = session.get("missing_facts", [])

    result = generate_case_story(verified, workflow_type, contradictions, missing_facts)
    session["case_story"] = result

    # Check status
    contra_fields = {c.get("field") for c in contradictions if isinstance(c, dict)}
    required = WORKFLOW_REQUIRED_FACTS.get(workflow_type, [])
    unverified_required = [
        req["field"] for req in required
        if req["field"] not in verified
        or verified[req["field"]] is None
        or str(verified[req["field"]]).strip() == ""
        or req["field"] in contra_fields
    ]
    is_fully_verified = len(contra_fields) == 0 and len(unverified_required) == 0
    verification_status = "verified" if is_fully_verified else "review_required"
    status_label = (
        "✅ Verified Case Facts"
        if is_fully_verified
        else f"⚠ Review Required — {len(contra_fields)} unresolved contradiction{'s' if len(contra_fields) != 1 else ''} / {len(unverified_required)} missing fact{'s' if len(unverified_required) != 1 else ''}"
    )

    return {
        "success": True,
        "session_id": payload.session_id,
        "workflow_type": workflow_type,
        "status": verification_status,
        "status_label": status_label,
        "is_fully_verified": is_fully_verified,
        "case_story": result["case_story"],
        "case_summary": result["case_summary"],
    }


@router.get("/session/{session_id}", summary="Get full session state")
async def get_session(session_id: str):
    """Retrieve full session data for a doc-intel session."""
    session = _get_session(session_id)
    return {"success": True, "session_id": session_id, **session}
