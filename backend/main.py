import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from api_v1 import api_router
from session import DatabaseManager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JudiQ.Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing JudiQ Infrastructure...")
    DatabaseManager.init_db()
    logger.info("Infrastructure ready.")
    yield
    logger.info("Shutting down JudiQ Infrastructure...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="JudiQ AI Litigation Intelligence Platform Backend",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# SECURITY: Use an explicit allowlist only. No wildcard regex.
# allow_origin_regex is intentionally omitted to prevent bypassing the allowlist.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail})
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal Server Error"}
    )


@app.get("/health")
async def health_check():
    health_data = {"status": "healthy", "version": settings.VERSION, "timestamp": time.time()}
    try:
        import psutil
        health_data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        health_data["memory"] = psutil.virtual_memory()._asdict()
    except ImportError:
        health_data["cpu_percent"] = "psutil not installed"
    try:
        from engine_core import registry
        health_data["engine_registry_size"] = len(registry._instances)
    except Exception:
        pass
    return health_data


@app.get("/")
@app.head("/")
async def root_endpoint():
    return {"status": "online", "service": settings.PROJECT_NAME, "version": settings.VERSION}


# All routes are served exclusively under /api/v1 prefix.
# Legacy duplicate route registrations removed to eliminate route conflicts.
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
