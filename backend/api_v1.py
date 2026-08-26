from fastapi import APIRouter
import analysis, caseroom, verification, documents, cases, telemetry, criminal
from security import SecurityManager
import uuid
api_router = APIRouter()
@api_router.post("/auth/anonymous", tags=["Authentication"])
def create_anonymous_session():
    user_id = f"ANON_{uuid.uuid4().hex[:12]}"
    token = SecurityManager.create_access_token(data={"sub": user_id})
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}
from admin_router import router as admin_control_router, user_quota_router

api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(criminal.router, prefix="/criminal", tags=["Criminal Engine"])
api_router.include_router(caseroom.router, prefix="/caseroom", tags=["Caseroom"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(cases.router, prefix="/cases", tags=["Cases"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
api_router.include_router(admin_control_router, prefix="/admin", tags=["Admin Control"])
api_router.include_router(user_quota_router, prefix="/user", tags=["User Quota"])

from knowledge_pipeline import PrecedentIngestionPayload, PrecedentIngestionService
from fastapi import Body

@api_router.post("/ingest/precedents", tags=["Knowledge Pipeline"])
def ingest_precedent_endpoint(payload: PrecedentIngestionPayload = Body(...)):
    return PrecedentIngestionService.ingest_precedent(payload)

