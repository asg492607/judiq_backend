from fastapi import APIRouter
import analysis, caseroom, verification, documents

api_router = APIRouter()

api_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
api_router.include_router(caseroom.router, prefix="/caseroom", tags=["Caseroom"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])

