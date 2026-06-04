# pyrefly: ignore [missing-import]
import os
import logging
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from caseroom_logic import CaseroomManager
from session import DatabaseManager
from config import settings
from cryptography.fernet import Fernet
from ocr_engine import OCREngine

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
                except:
                    pass

manager = ConnectionManager()

# Encryption setup — wrap in try/except to guard against invalid env var
_SAFE_KEY = b"c2VjcmV0X2tleV90aGF0X2lzX2V4YWN0bHlfMzJfYnl0ZXM="
try:
    _raw_key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
    fernet = Fernet(_raw_key)
except Exception:
    fernet = Fernet(_SAFE_KEY)

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
    success = CaseroomManager.post_comment(room_id, data.get("user_id"), data.get("content"))
    if success:
        await manager.broadcast({"type": "NEW_MESSAGE", "user_id": data.get("user_id"), "content": data.get("content")}, room_id)
    return {"success": success}

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WS messages if needed
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

    # Ensure uploads directory exists
    upload_dir = os.path.join(os.getcwd(), "uploads", room_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(upload_dir, safe_filename)
    content = await file.read()
    
    # Encrypt file content
    encrypted_content = fernet.encrypt(content)
    
    # Save encrypted file to disk
    with open(file_path, "wb") as f:
        f.write(encrypted_content)

    # Text extraction and verification
    extracted_text = "[Extraction logic here]" # Simplified for now
    verification_result = OCREngine.analyze_document(extracted_text, doc_type, claimed_reason)
    verification_status = "VERIFIED" if verification_result.get("is_verified") else "FAILED"

    # Save metadata to DB
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
        
    with open(file_path, "rb") as f:
        encrypted_content = f.read()
        
    try:
        decrypted_content = fernet.decrypt(encrypted_content)
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return JSONResponse(status_code=500, content={"error": "Decryption failed"})
        
    return Response(
        content=decrypted_content,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

