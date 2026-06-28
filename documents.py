# pyrefly: ignore [missing-import]
import logging
from fastapi import APIRouter, Response, Query, Body
from fastapi.responses import JSONResponse
from pdf_generator import PDFGenerator
from jurisdiction_engine import map_jurisdiction

router = APIRouter()
logger = logging.getLogger("JudiQ.Documents")

@router.post("/generate-pdf")
def generate_pdf(data: dict = Body(...)):
    try:
        pdf_bytes = PDFGenerator.generate_report(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=JudiQ_Legal_Report.pdf"}
        )
    except ImportError as e:
        logger.error(f"PDF library missing: {e}")
        return JSONResponse(status_code=500, content={"error": "PDF generation library is not installed on this server."})
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to generate PDF report."})

@router.post("/jurisdiction/map")
def jurisdiction_map(data: dict = Body(...)):
    result = map_jurisdiction(data)
    return {"success": True, "jurisdiction": result}

@router.get("/draft/history/{case_id}/{draft_type}")
def get_draft_history(case_id: str, draft_type: str):
    from session import DatabaseManager
    history = DatabaseManager.get_draft_history(case_id, draft_type)
    return {"success": True, "history": history}

@router.get("/draft/history")
def get_draft_history_query(case_id: str = Query(...), draft_type: str = Query(...)):
    """Path-safe draft history lookup for case IDs that contain slashes."""
    from session import DatabaseManager
    history = DatabaseManager.get_draft_history(case_id, draft_type)
    return {"success": True, "history": history}
@router.post("/draft-word")
def generate_draft_word_endpoint(data: dict = Body(...)):
    from word_generator import WordGenerator
    try:
        title = data.get("title", "Legal_Draft")
        content = data.get("content", "")
        metadata = data.get("metadata", {})
        word_bytes = WordGenerator.generate_draft_word(title, content, metadata)
        return Response(
            content=word_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=JUDIQ_{title.replace(' ', '_')}.docx"}
        )
    except Exception as e:
        logger.error(f"Draft Word generation failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to generate draft Word document."})

@router.post("/draft-pdf")
def generate_draft_pdf(data: dict = Body(...)):
    try:
        title = data.get("title", "Legal_Draft")
        content = data.get("content", "")
        metadata = data.get("metadata", {})
        pdf_bytes = PDFGenerator.generate_draft_pdf(title, content, metadata)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=JUDIQ_{title.replace(' ', '_')}.pdf"}
        )
    except Exception as e:
        logger.error(f"Draft PDF generation failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to generate draft PDF."})
