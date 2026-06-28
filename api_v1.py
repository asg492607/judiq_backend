from fastapi import APIRouter
import analysis, caseroom, verification, documents, cases, telemetry
from security import SecurityManager
import uuid

api_router = APIRouter()

@api_router.post("/auth/anonymous", tags=["Authentication"])
def create_anonymous_session():
    """Generates a secure anonymous session JWT."""
    user_id = f"ANON_{uuid.uuid4().hex[:12]}"
    token = SecurityManager.create_access_token(data={"sub": user_id})
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}

api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(caseroom.router, prefix="/caseroom", tags=["Caseroom"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(cases.router, prefix="/cases", tags=["Cases"])

# Observability & Metrics
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
