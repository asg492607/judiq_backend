import os
import logging
from fastapi import APIRouter, Request, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, Response
from caseroom_logic import CaseroomManager
from config import settings
from cryptography.fernet import Fernet
from ocr_engine import OCREngine
from llm_engine import _invoke_llm
import json
import asyncio
router = APIRouter()
logger = logging.getLogger("JudiQ.Caseroom")
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections and websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)
    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
manager = ConnectionManager()
try:
    _raw_key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
    fernet = Fernet(_raw_key)
except Exception as e:
    raise RuntimeError(f"FATAL: ENCRYPTION_KEY is invalid or missing. Do not fallback to ephemeral keys. Error: {e}")
@router.post("/create")
async def create_caseroom(request: Request):
    data = await request.json()
    cid = data.get("case_id")
    uid = data.get("user_id")
    room_id = CaseroomManager.initialize_caseroom_for_case(cid, uid)
    return {"success": True, "caseroom_id": room_id}
@router.get("/{room_id}")
async def get_caseroom(room_id: str):
    data = CaseroomManager.get_full_caseroom_state(room_id)
    if not data: return JSONResponse(status_code=404, content={"error": "Room not found"})
    return {"success": True, "data": data}
@router.post("/{room_id}/invite")
async def invite_to_caseroom(room_id: str, request: Request):
    data = await request.json()
    success = CaseroomManager.invite_collaborator(room_id, data.get("user_id"), data.get("role"))
    return {"success": success}
@router.post("/{room_id}/message")
async def send_caseroom_message(room_id: str, request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    content = data.get("content", "")
    success = CaseroomManager.post_comment(room_id, user_id, content)
    if success:
        await manager.broadcast({"type": "NEW_MESSAGE", "user_id": user_id, "content": content}, room_id)
        if "@JudiQ" in content:
            state = CaseroomManager.get_full_caseroom_state(room_id)
            latest_analysis = state.get("latest_analysis") or {} if state else {}
            causality_map = latest_analysis.get("causality_map", [])
            vulnerabilities = [c["fact"] for c in causality_map if c.get("impact", 0) < 0]
            vuln_str = ", ".join(vulnerabilities) if vulnerabilities else "none"
            prompt = f"You are an adversarial opposing counsel in an Indian courtroom. The case currently has the following lingering vulnerabilities: {vuln_str}. Target these specific gaps. The defense lawyer just said: '{content}'. Cross-examine them aggressively but professionally to find logical gaps based on these vulnerabilities. Keep it to 2-3 sentences."
            try:
                llm_response = await asyncio.to_thread(_invoke_llm, prompt, 200, None)
                ai_text = llm_response if llm_response else "Objection, your honor. The statement lacks merit."
            except Exception as e:
                logger.error(f"Simulator LLM Error: {e}")
                ai_text = "I am currently unable to process your argument."
            CaseroomManager.post_comment(room_id, "JudiQ_AI", ai_text)
            await manager.broadcast({"type": "NEW_MESSAGE", "user_id": "JudiQ_AI", "content": ai_text}, room_id)
    return {"success": success}
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
            except Exception:
                parsed = {"type": data}
            if parsed.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
@router.post("/{room_id}/task")
async def add_caseroom_task(room_id: str, request: Request):
    data = await request.json()
    success = CaseroomManager.add_milestone(room_id, data.get("title"), data.get("due_date"), data.get("description", ""))
    return {"success": success}
@router.post("/{room_id}/upload")
async def upload_caseroom_document(
    room_id: str,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    doc_type: str = Form("EVIDENCE"),
    claimed_reason: str = Form("None")
):
    ALLOWED_MIMES = {"application/pdf", "image/jpeg", "image/png"}
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, JPEG, and PNG are allowed.")
    upload_dir = os.path.join(os.getcwd(), "uploads", room_id)
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(upload_dir, safe_filename)
    content = await file.read()
    header = content[:4]
    if not (header.startswith(b'%PDF') or header.startswith(b'\x89PNG') or header.startswith(b'\xff\xd8')):
        raise HTTPException(status_code=400, detail="Invalid file signature. File contents do not match extension.")
    encrypted_content = fernet.encrypt(content)
    def write_file():
        with open(file_path, "wb") as f:
            f.write(encrypted_content)
    await asyncio.to_thread(write_file)
    extracted_text = "[Extraction logic here]"                     
    verification_result = await asyncio.to_thread(OCREngine.analyze_document, extracted_text, doc_type, claimed_reason)
    verification_status = "VERIFIED" if verification_result.get("is_verified") else "FAILED"
    doc_id = CaseroomManager.upload_document(room_id, user_id, safe_filename, file_path, doc_type, verification_status, verification_result)
    return {
        "success": bool(doc_id),
        "doc_id": doc_id,
        "filename": safe_filename,
        "verification_status": verification_status,
        "verification_details": verification_result
    }
@router.post("/{room_id}/reanalyze")
async def reanalyze_caseroom(room_id: str):
    success, result = CaseroomManager.reanalyze_case_from_documents(room_id)
    if not success:
        return JSONResponse(status_code=400, content={"error": result})
    return {"success": True, "message": "Case re-analyzed successfully.", "new_analysis_result": result}
@router.get("/{room_id}/download/{filename}")
async def download_caseroom_document(room_id: str, filename: str):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(os.getcwd(), "uploads", room_id, safe_filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    def read_file():
        with open(file_path, "rb") as f:
            return f.read()
    encrypted_content = await asyncio.to_thread(read_file)
    try:
        decrypted_content = fernet.decrypt(encrypted_content)
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Decryption failed"})
    return Response(
        content=decrypted_content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
