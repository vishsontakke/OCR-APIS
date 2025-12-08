from paddleocr import PaddleOCR
import logging
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive OCR operations
executor = ThreadPoolExecutor(max_workers=4)

# OCR instance cache
_ocr_instances: Dict[str, PaddleOCR] = {}

# Result cache
_result_cache: Dict[str, tuple] = {}
CACHE_MAX_SIZE = 1000
CACHE_TTL = 86400  # 24 hours


def get_file_hash(file_path: str) -> str:
    """Calculate file hash for caching"""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def get_ocr_instance(lang: str = "en") -> PaddleOCR:
    """
    Get or create OCR instance for language
    Uses cache to avoid reloading models
    """
    if lang not in _ocr_instances:
        logger.info(f"Loading OCR model for language: {lang}")
        _ocr_instances[lang] = PaddleOCR(
            lang=lang,
            use_gpu=False,
            show_log=False,
            det_model_dir=None,
            rec_model_dir=None,
        )
        logger.info(f"OCR model loaded for: {lang}")
    
    return _ocr_instances[lang]


def clear_ocr_cache():
    """Clear OCR instance cache"""
    _ocr_instances.clear()
    logger.info("OCR instance cache cleared")


def get_cached_result(file_path: str) -> Optional[Dict[str, Any]]:
    """Get cached result if available and not expired"""
    try:
        file_hash = get_file_hash(file_path)
        if file_hash in _result_cache:
            result, timestamp = _result_cache[file_hash]
            if time.time() - timestamp < CACHE_TTL:
                logger.info(f"Cache hit for file: {file_path}")
                return result
            else:
                del _result_cache[file_hash]
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
    
    return None


def cache_result(file_path: str, result: Dict[str, Any]):
    """Cache OCR result"""
    try:
        if len(_result_cache) >= CACHE_MAX_SIZE:
            # Remove oldest entry
            oldest_key = min(_result_cache.keys(), key=lambda k: _result_cache[k][1])
            del _result_cache[oldest_key]
        
        file_hash = get_file_hash(file_path)
        _result_cache[file_hash] = (result, time.time())
        logger.info(f"Cached result for: {file_path}")
    except Exception as e:
        logger.warning(f"Cache storage failed: {e}")


def paddle_ocr_and_annotate(img_path: str, ocr: Optional[PaddleOCR] = None) -> Dict[str, Any]:
    """
    FAST PaddleOCR extraction with caching
    Returns ONLY raw text (no boxes, no saving)
    
    Args:
        img_path: Path to image file
        ocr: OCR instance (optional, will use cached)
    
    Returns:
        dict: OCR results with texts, raw_text, execution_time
    """
    start_time = time.time()
    
    try:
        # Check cache first
        cached = get_cached_result(img_path)
        if cached:
            return cached
        
        # Get or create OCR instance
        if ocr is None:
            ocr = get_ocr_instance(lang="en")
        
        # Run OCR
        result = ocr.predict(img_path)
        
        # Handle empty results
        if not result or len(result) == 0:
            output = {
                "texts": [],
                "raw_text": "",
                "annotated_path": None,
                "execution_time": time.time() - start_time,
                "cached": False
            }
        else:
            texts = result[0].get("rec_texts", [])
            raw_text = " ".join(texts)
            
            output = {
                "texts": texts,
                "raw_text": raw_text,
                "annotated_path": None,
                "execution_time": time.time() - start_time,
                "cached": False
            }
        
        # Cache the result
        cache_result(img_path, output)
        
        return output
        
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        return {
            "texts": [],
            "raw_text": "",
            "annotated_path": None,
            "execution_time": time.time() - start_time,
            "error": str(e),
            "cached": False
        }


# Pre-load default OCR instance at startup
ocr = get_ocr_instance(lang="en")
