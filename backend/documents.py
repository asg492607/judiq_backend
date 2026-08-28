import logging
from fastapi import APIRouter, Response, Query, Body
from fastapi.responses import JSONResponse
from pdf_generator import PDFGenerator
from jurisdiction_engine import map_jurisdiction
router = APIRouter()
logger = logging.getLogger("JudiQ.Documents")
import re

@router.post("/generate-pdf")
def generate_pdf(data: dict = Body(...)):
    try:
        from session import DatabaseManager
        case_data = data.get("case_data", {}) if isinstance(data, dict) else {}
        user_id = data.get("user_id") or case_data.get("user_id") or ""
        email = data.get("email") or ""
        
        if user_id and user_id not in {"ANONYMOUS", "demo_user_123"}:
            quota_res = DatabaseManager.check_and_consume_report_quota(user_id, email, cost=1)
            if not quota_res["allowed"]:
                return JSONResponse(status_code=429, content={
                    "error": quota_res["message"],
                    "reason": quota_res["reason"],
                    "quota": quota_res.get("quota")
                })

        pdf_bytes = PDFGenerator.generate_report(data)
        case_title = case_data.get("case_title") or case_data.get("case_caption") or data.get("case_title") or data.get("case_id") or "Legal_Report"
        safe_title = re.sub(r'[^a-zA-Z0-9_\-\s]', '', str(case_title)).strip().replace(' ', '_')[:60] or "Legal_Report"
        filename = f"JUDIQ_Report_{safe_title}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
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
    from session import DatabaseManager
    history = DatabaseManager.get_draft_history(case_id, draft_type)
    return {"success": True, "history": history}
@router.post("/draft-word")
def generate_draft_word_endpoint(data: dict = Body(...)):
    from word_generator import WordGenerator
    from session import DatabaseManager
    try:
        user_id = data.get("user_id") or ""
        email = data.get("email") or ""
        if user_id and user_id not in {"ANONYMOUS", "demo_user_123"}:
            quota_res = DatabaseManager.check_and_consume_report_quota(user_id, email, cost=1)
            if not quota_res["allowed"]:
                return JSONResponse(status_code=403, content={
                    "error": quota_res["message"],
                    "reason": quota_res["reason"],
                    "quota": quota_res.get("quota")
                })

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
    from session import DatabaseManager
    try:
        user_id = data.get("user_id") or ""
        email = data.get("email") or ""
        if user_id and user_id not in {"ANONYMOUS", "demo_user_123"}:
            quota_res = DatabaseManager.check_and_consume_report_quota(user_id, email, cost=1)
            if not quota_res["allowed"]:
                return JSONResponse(status_code=403, content={
                    "error": quota_res["message"],
                    "reason": quota_res["reason"],
                    "quota": quota_res.get("quota")
                })

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
