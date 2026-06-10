# pyrefly: ignore [missing-import]
import logging
from fastapi import APIRouter, Request, Response
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

