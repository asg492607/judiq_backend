# pyrefly: ignore [missing-import]
import logging
from fastapi import APIRouter, Request, Response
from pdf_generator import PDFGenerator
from jurisdiction_engine import map_jurisdiction

router = APIRouter()
logger = logging.getLogger("JudiQ.Documents")

@router.post("/generate-pdf")
async def generate_pdf(request: Request):
    data = await request.json()
    pdf_bytes = PDFGenerator.generate_report(data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=JudiQ_Legal_Report.pdf"}
    )

@router.post("/jurisdiction/map")
async def jurisdiction_map(request: Request):
    data = await request.json()
    result = map_jurisdiction(data)
    return {"success": True, "jurisdiction": result}

