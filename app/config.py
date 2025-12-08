"""
Configuration settings for OCR API
"""
import os
from typing import Optional

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# Cache Configuration
CACHE_TTL_SECONDS = 86400  # 24 hours
CACHE_MAX_SIZE = 1000  # Max cached results

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

# OCR Configuration
OCR_MODEL_LANG = os.getenv("OCR_MODEL_LANG", "en")
OCR_WORKERS = int(os.getenv("OCR_WORKERS", "4"))
OCR_DPI = int(os.getenv("OCR_DPI", "150"))
OCR_GPU_ENABLED = os.getenv("OCR_GPU_ENABLED", "False").lower() == "true"

# File Configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/ocr")
ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
ALLOWED_PDF_EXTS = {".pdf"}

# API Configuration
API_TITLE = "OCR API Service"
API_VERSION = "1.0.0"
API_DESCRIPTION = "High-performance OCR API with PaddleOCR"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance
THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "4"))
TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "300"))  # 5 minutes
QUEUE_MAX_SIZE = int(os.getenv("QUEUE_MAX_SIZE", "10000"))

# Database Configuration (for job history)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ocr_db")
ENABLE_JOB_HISTORY = os.getenv("ENABLE_JOB_HISTORY", "True").lower() == "true"
