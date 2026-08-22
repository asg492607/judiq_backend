import logging
import asyncio
from fastapi import APIRouter, UploadFile, File
from ocr_engine import OCREngine

router = APIRouter()
logger = logging.getLogger("JudiQ.Verification")


@router.get("/mca/{cin}")
async def verify_mca_data(cin: str):
    """
    CIN verification endpoint.

    NOTE: This is currently a format-validation stub.
    Real MCA21 data retrieval would require integration with the MCA API
    (https://www.mca.gov.in/content/mca/global/en/data-and-reports/mca-data-products.html)
    or a licensed data provider. No live MCA data is fetched here.
    """
    # Validate CIN format: 21 alphanumeric characters
    # Format: L/U + 5 digits + state code + year + 3 chars + 6 digits
    import re
    CIN_PATTERN = re.compile(r'^[LUlu][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$')
    if not cin or not CIN_PATTERN.match(cin.upper()):
        return {
            "success": False,
            "error": "Invalid CIN format. A valid CIN is 21 characters: e.g. L17110MH1973PLC019786"
        }
    return {
        "success": True,
        "cin": cin.upper(),
        "status": "FORMAT_VALID",
        "note": "Live MCA21 database integration is not yet active. CIN format is valid — verify company details manually at https://www.mca.gov.in/content/mca/global/en/fo/search-company.html",
        "mca_search_url": f"https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do?cin={cin.upper()}"
    }


@router.get("/post/{tracking_id}")
async def verify_post_data(tracking_id: str):
    """
    India Post tracking endpoint.

    NOTE: This is a format-validation stub.
    Real tracking requires India Post API integration.
    """
    # India Post tracking IDs follow the S/13-char alphanumeric format
    import re
    TRACKING_PATTERN = re.compile(r'^[A-Z]{2}[0-9]{9}IN$', re.IGNORECASE)
    if not tracking_id or not TRACKING_PATTERN.match(tracking_id):
        return {
            "success": False,
            "error": "Invalid tracking ID format. Valid format: 2 letters + 9 digits + 'IN' (e.g. EW123456789IN)"
        }
    return {
        "success": True,
        "tracking_id": tracking_id.upper(),
        "status": "FORMAT_VALID",
        "note": "Live India Post tracking is not yet integrated. Verify delivery status at https://www.indiapost.gov.in/VAS/Pages/TrackmailArticles.aspx",
        "india_post_url": f"https://www.indiapost.gov.in/VAS/Pages/TrackmailArticles.aspx"
    }


@router.post("/memo")
async def verify_memo(
    file: UploadFile = File(...),
    claimed_reason: str = "Insufficient Funds"
):
    """OCR-based bank dishonour memo verification."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        return {"success": False, "error": "File too large. Maximum allowed size is 10 MB."}
    try:
        import pytesseract
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(content))
        extracted_text = await asyncio.to_thread(pytesseract.image_to_string, image)
    except ImportError:
        logger.error("pytesseract or PIL not installed. Falling back to placeholder.")
        extracted_text = "[Memo text extracted fallback]"
    except Exception as e:
        logger.error(f"OCR Extraction failed: {e}")
        extracted_text = "[Memo text extraction failed]"
    verification_result = OCREngine.analyze_document(extracted_text, "MEMO", claimed_reason)
    return {
        "success": True,
        "filename": file.filename,
        "verification": verification_result
    }
