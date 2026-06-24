# pyrefly: ignore [missing-import]
import logging
from fastapi import APIRouter, Request, Response, Query
from fastapi.responses import JSONResponse
from pdf_generator import PDFGenerator
from jurisdiction_engine import map_jurisdiction

router = APIRouter()
logger = logging.getLogger("JudiQ.Documents")

@router.post("/generate-pdf")
async def generate_pdf(request: Request):
    data = await request.json()
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
async def jurisdiction_map(request: Request):
    data = await request.json()
    result = map_jurisdiction(data)
    return {"success": True, "jurisdiction": result}

@router.get("/draft/history/{case_id}/{draft_type}")
async def get_draft_history(case_id: str, draft_type: str):
    from session import DatabaseManager
    history = DatabaseManager.get_draft_history(case_id, draft_type)
    return {"success": True, "history": history}

@router.get("/draft/history")
async def get_draft_history_query(case_id: str = Query(...), draft_type: str = Query(...)):
    """Path-safe draft history lookup for case IDs that contain slashes."""
    from session import DatabaseManager
    history = DatabaseManager.get_draft_history(case_id, draft_type)
    return {"success": True, "history": history}

@router.post("/draft-pdf")
async def generate_draft_pdf(request: Request):
    data = await request.json()
    try:
        title = data.get("title", "Legal_Draft")
        content = data.get("content", "")
        pdf_bytes = PDFGenerator.generate_draft_pdf(title, content)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=JUDIQ_{title.replace(' ', '_')}.pdf"}
        )
    except Exception as e:
        logger.error(f"Draft PDF generation failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to generate draft PDF."})
