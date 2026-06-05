import logging
import time
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from config import settings
from api_v1 import api_router
from session import DatabaseManager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JudiQ.Main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="JudiQ AI Litigation Intelligence Platform Backend"
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to settings.ALLOWED_HOSTS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Error Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal Server Error", "detail": str(exc)}
    )

# Startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing JudiQ Infrastructure...")
    DatabaseManager.init_db()
    logger.info("âœ… Infrastructure Ready.")

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION, "timestamp": time.time()}

# Include API Router
app.include_router(api_router, prefix="/api/v1")

# ═══════════════════════════════════════════════════════════════
# LEGACY FALLBACK ROUTES (For cached frontend clients)
# ═══════════════════════════════════════════════════════════════
import analysis, verification, documents

app.include_router(analysis.router, prefix="/analyze", tags=["Legacy Analysis"])
app.include_router(verification.router, prefix="/verify-memo", tags=["Legacy Verification"])
app.include_router(verification.router, prefix="/upload-doc", tags=["Legacy Upload"])
app.include_router(documents.router, prefix="/generate-pdf", tags=["Legacy Documents"])

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

