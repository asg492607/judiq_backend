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


from metrics import prometheus_metrics_endpoint, JUDIQ_REQUESTS_TOTAL, JUDIQ_REQUEST_DURATION_SECONDS

@app.middleware("http")
async def add_process_time_and_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record Prometheus Metrics
    try:
        endpoint = request.url.path
        method = request.method
        status = str(response.status_code)
        JUDIQ_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status).inc()
        JUDIQ_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(process_time)
    except Exception:
        pass

    # Prevent browser from serving stale cached static files in development
    if not request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Prometheus scraping endpoint
app.add_api_route("/metrics", prometheus_metrics_endpoint, methods=["GET"], tags=["Observability"])


# CORS Configuration supporting explicit production origins and Netlify/Workers deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https?://(.*\.)?(netlify\.app|workers\.dev|pages\.dev|vercel\.app|github\.io|onrender\.com|localhost|127\.0\.0\.1)(:\d+)?$",
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


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    fav_svg = frontend_dir / "favicon.svg"
    if fav_svg.exists():
        return FileResponse(str(fav_svg), media_type="image/svg+xml")
    fav_icon = frontend_dir / "favicon.ico"
    if fav_icon.exists():
        return FileResponse(str(fav_icon))
    return JSONResponse(status_code=204, content={})

# All routes are served under /api/v1 prefix and banking direct aliases
app.include_router(api_router, prefix="/api/v1")
from banking.router import router as banking_direct_router
app.include_router(banking_direct_router, tags=["Banking & Recovery OS Direct"])

# Mount frontend directory for seamless local development & single-port hosting
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    @app.get("/")
    @app.head("/")
    async def root_endpoint():
        return {"status": "online", "service": settings.PROJECT_NAME, "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

