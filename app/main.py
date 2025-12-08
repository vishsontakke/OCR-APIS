from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.api import tesseract, users, ocr, paddleocr_pdf
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

from app.api.paddleocr import router as paddleocr_router
from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, LOG_LEVEL

# Configure logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Health check state
app_state = {
    "status": "initializing",
    "started_at": datetime.utcnow(),
    "requests_processed": 0,
    "errors": 0
}

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 50)
    logger.info("[STARTUP] Loading OCR models...")
    app_state["status"] = "starting"
    
    try:
        from app.services.paddleocr_service import get_ocr_instance
        ocr = get_ocr_instance(lang="en")
        logger.info("[STARTUP] PaddleOCR model loaded successfully")
        app_state["status"] = "healthy"
    except Exception as e:
        logger.error(f"[STARTUP] Failed to load OCR model: {e}")
        app_state["status"] = "unhealthy"
    
    logger.info(f"[STARTUP] API started at {app_state['started_at']}")
    logger.info("=" * 50)
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info("[SHUTDOWN] Cleaning up resources...")
    app_state["status"] = "shutting_down"
    
    try:
        from app.services.paddleocr_service import clear_ocr_cache
        clear_ocr_cache()
        logger.info("[SHUTDOWN] OCR cache cleared")
    except Exception as e:
        logger.error(f"[SHUTDOWN] Cleanup failed: {e}")
    
    logger.info("[SHUTDOWN] Application shutdown complete")
    logger.info("=" * 50)


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    root_path="/ocr-api",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
class RequestTrackingMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        request.state.start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - request.state.start_time
            
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = str(time.time_ns())
            
            app_state["requests_processed"] += 1
            
            logger.info(
                f"Request: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            app_state["errors"] += 1
            logger.error(f"Request failed: {e}")
            raise

app.add_middleware(RequestTrackingMiddleware)


# Register routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(tesseract.router, prefix="/tesseract", tags=["Tesseract OCR"])
app.include_router(paddleocr_router)
app.include_router(paddleocr_pdf.router, prefix="/paddleocr", tags=["PaddleOCR"])


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": app_state["status"],
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - app_state["started_at"]).total_seconds(),
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Application metrics"""
    uptime = (datetime.utcnow() - app_state["started_at"]).total_seconds()
    
    return {
        "status": app_state["status"],
        "uptime_seconds": uptime,
        "requests_processed": app_state["requests_processed"],
        "errors": app_state["errors"],
        "error_rate": (
            app_state["errors"] / app_state["requests_processed"]
            if app_state["requests_processed"] > 0 else 0
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to OCR API Service",
        "version": API_VERSION,
        "status": app_state["status"],
        "documentation": "/ocr-api/docs"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    app_state["errors"] += 1
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    app_state["errors"] += 1
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
