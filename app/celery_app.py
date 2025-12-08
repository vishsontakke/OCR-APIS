"""
Celery task queue for OCR processing
Handles async job processing for high-volume requests
"""
import os
from celery import Celery, Task
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
import logging

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "ocr_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=280,  # 4.5 minutes soft limit
    worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
)

class CallbackTask(Task):
    """Task with callback support for success/failure"""
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True

celery_app.Task = CallbackTask


@celery_app.task(bind=True, name="process_image_ocr")
def process_image_ocr(self, file_path: str, lang: str = "en"):
    """
    Process image OCR in background
    
    Args:
        file_path: Path to image file
        lang: OCR language
    
    Returns:
        dict: OCR results
    """
    try:
        from app.services.paddleocr_service import paddle_ocr_and_annotate, get_ocr_instance
        
        logger.info(f"[Task {self.request.id}] Processing image: {file_path}")
        
        # Get OCR instance
        ocr = get_ocr_instance(lang=lang)
        
        # Process OCR
        result = paddle_ocr_and_annotate(file_path, ocr=ocr)
        
        logger.info(f"[Task {self.request.id}] Completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Failed: {exc}")
        raise


@celery_app.task(bind=True, name="process_pdf_ocr")
def process_pdf_ocr(self, file_path: str, page_num: int = 1, lang: str = "en"):
    """
    Process PDF OCR in background
    
    Args:
        file_path: Path to PDF file
        page_num: Page number to process
        lang: OCR language
    
    Returns:
        dict: OCR results
    """
    try:
        import fitz
        from app.services.paddleocr_service import paddle_ocr_and_annotate, get_ocr_instance
        from app.api.paddleocr_pdf import extract_document_ids
        
        logger.info(f"[Task {self.request.id}] Processing PDF page {page_num}")
        
        # Convert PDF to image
        pdf_doc = fitz.open(file_path)
        page = pdf_doc[page_num - 1]
        pix = page.get_pixmap(dpi=150)
        img_path = file_path + f"_page_{page_num}.png"
        pix.save(img_path)
        pdf_doc.close()
        
        # Get OCR instance
        ocr = get_ocr_instance(lang=lang)
        
        # Process OCR
        result = paddle_ocr_and_annotate(img_path, ocr=ocr)
        
        # Extract document IDs
        document_ids = extract_document_ids(result.get("raw_text", ""))
        result["document_ids"] = document_ids
        result["document_type"] = list(document_ids.keys())[0] if document_ids else None
        
        logger.info(f"[Task {self.request.id}] Completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Failed: {exc}")
        raise


@celery_app.task(name="health_check")
def health_check():
    """Health check task"""
    return {"status": "healthy", "timestamp": str(__import__("datetime").datetime.utcnow())}
