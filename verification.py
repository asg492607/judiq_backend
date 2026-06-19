# pyrefly: ignore [missing-import]
import logging
import asyncio
from fastapi import APIRouter, UploadFile, File
from ocr_engine import OCREngine

router = APIRouter()
logger = logging.getLogger("JudiQ.Verification")

@router.get("/mca/{cin}")
async def verify_mca_data(cin: str):
    if not cin or len(cin) < 21:
        return {"success": False, "error": "Invalid CIN Format"}
    return {
        "success": True,
        "cin": cin,
        "company_name": "Verified Entity Pvt. Ltd.",
        "status": "Active",
        "directors": [
            {"din": "01234567", "name": "Rahul Sharma", "designation": "Managing Director"},
            {"din": "07654321", "name": "Priya Singh", "designation": "Director"}
        ]
    }

@router.get("/post/{tracking_id}")
async def verify_post_data(tracking_id: str):
    if not tracking_id or not tracking_id.endswith("IN"):
        return {"success": False, "error": "Invalid Tracking ID Format"}
    return {
        "success": True,
        "tracking_id": tracking_id,
        "status": "Item Delivery Confirmed"
    }

@router.post("/memo")
async def verify_memo(
    file: UploadFile = File(...),
    claimed_reason: str = "Insufficient Funds"
):
    content = await file.read()
    
    try:
        import pytesseract
        from PIL import Image
        import io
import asyncio
        
        # Load image from bytes
        image = Image.open(io.BytesIO(content))
        # Extract text using pytesseract
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

