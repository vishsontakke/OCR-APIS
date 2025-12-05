from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import shutil
import re

from app.services.paddleocr_service import paddle_ocr_and_annotate, ocr  # Import preloaded OCR

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
            # Remove duplicates and clean up
            found_documents[doc_type] = list(set(matches))
    
    return found_documents

@router.post("/predict", name="PaddleOCR Fast Predict")
async def paddleocr_predict(file: UploadFile = File(...)):
    try:
        suffix = Path(file.filename).suffix.lower()
        allowed_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

        if suffix not in allowed_exts:
            raise HTTPException(status_code=400, detail="Only image files are supported for PaddleOCR.")

        # Fast temp save (no memory read)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Run FAST OCR with preloaded model
        result = paddle_ocr_and_annotate(tmp_path, ocr=ocr)
        
        # Extract document IDs from OCR text
        raw_text = result["raw_text"]
        document_ids = extract_document_ids(raw_text)

        return {
            "filename": file.filename,
            "texts": result["texts"],
            "raw_text": raw_text,
            "document_ids": document_ids,
            "document_type": list(document_ids.keys())[0] if document_ids else None,
            "execution_time": result["execution_time"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PaddleOCR failed: {str(e)}")
