from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from pathlib import Path
import tempfile
import shutil
import re
import os
import asyncio
import logging
from typing import Optional
import hashlib

from app.services.paddleocr_service import paddle_ocr_and_annotate, ocr, get_cached_result, cache_result

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/paddleocr", tags=["PaddleOCR"])

# Document ID regex patterns
DOCUMENT_PATTERNS = {
    "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    "Aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "Driving_License": r"[A-Z]{2}[-\s]?\d{2}[-\s]?\d{4}[-\s]?\d{7}",
    "Passport": r"\b[A-Z]\d{7}\b",
    "UDYAM": r"UDYAM-[A-Z]{2}-\d{2}-\d{7}"
}


def extract_document_ids(text: str):
    """Extract document IDs from text using regex patterns"""
    found_documents = {}
    
    for doc_type, pattern in DOCUMENT_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_documents[doc_type] = list(set(matches))
    
    return found_documents


def cleanup_temp_file(file_path: str):
    """Background task to cleanup temporary files"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up temp file {file_path}: {e}")


@router.post("/predict", name="PaddleOCR Fast Predict")
async def paddleocr_predict(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Process image with PaddleOCR
    
    - Supports: PNG, JPG, JPEG, BMP, TIFF, WEBP
    - Includes caching by file hash
    - Extracts document IDs automatically
    - Returns execution time
    """
    tmp_path = None
    try:
        suffix = Path(file.filename).suffix.lower()
        allowed_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

        if suffix not in allowed_exts:
            raise HTTPException(status_code=400, detail="Only image files are supported for PaddleOCR.")

        # Save temp file
        tmp_path = tempfile.mktemp(suffix=suffix)
        content = await file.read()
        
        with open(tmp_path, "wb") as f:
            f.write(content)
        
        # Check cache first
        cached = get_cached_result(tmp_path)
        if cached:
            logger.info(f"Cache hit for: {file.filename}")
            if background_tasks and tmp_path:
                background_tasks.add_task(cleanup_temp_file, tmp_path)
            return {
                "filename": file.filename,
                "cached": True,
                **cached
            }
        
        # Run OCR with thread pool (non-blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, paddle_ocr_and_annotate, tmp_path, ocr)
        
        # Extract document IDs
        raw_text = result.get("raw_text", "")
        document_ids = extract_document_ids(raw_text)
        
        # Schedule cleanup
        if background_tasks and tmp_path:
            background_tasks.add_task(cleanup_temp_file, tmp_path)
        
        return {
            "filename": file.filename,
            "texts": result["texts"],
            "raw_text": raw_text,
            "document_ids": document_ids,
            "document_type": list(document_ids.keys())[0] if document_ids else None,
            "execution_time": result["execution_time"],
            "cached": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PaddleOCR error: {e}")
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"PaddleOCR failed: {str(e)}")


@router.post("/predict-async", name="PaddleOCR Async Predict")
async def paddleocr_predict_async(file: UploadFile = File(...)):
    """
    Async OCR processing with Celery queue
    Returns job ID for status tracking
    """
    try:
        from app.celery_app import process_image_ocr
        
        suffix = Path(file.filename).suffix.lower()
        allowed_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

        if suffix not in allowed_exts:
            raise HTTPException(status_code=400, detail="Only image files are supported.")

        # Save file
        tmp_path = tempfile.mktemp(suffix=suffix)
        content = await file.read()
        
        with open(tmp_path, "wb") as f:
            f.write(content)
        
        # Queue job
        task = process_image_ocr.delay(tmp_path)
        
        logger.info(f"Queued job {task.id} for file: {file.filename}")
        
        return {
            "job_id": task.id,
            "filename": file.filename,
            "status": "pending",
            "message": "Job queued for processing"
        }
        
    except Exception as e:
        logger.error(f"Async job error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")


@router.get("/status/{job_id}", name="Get OCR Job Status")
async def get_job_status(job_id: str):
    """Get status of async OCR job"""
    try:
        from app.celery_app import celery_app
        
        result = celery_app.AsyncResult(job_id)
        
        return {
            "job_id": job_id,
            "status": result.status,
            "result": result.result if result.status == "SUCCESS" else None,
            "error": str(result.info) if result.status == "FAILURE" else None
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")
