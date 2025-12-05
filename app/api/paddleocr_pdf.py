from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import fitz  # PyMuPDF
import os
import re
from app.services.paddleocr_service import paddle_ocr_and_annotate, ocr  # Use shared OCR instance

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

@router.post("/pdf", name="PaddleOCR PDF Predict and Annotate")
async def paddleocr_pdf_predict(file: UploadFile = File(...)):
    try:
        suffix = Path(file.filename).suffix.lower()
        if suffix != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are supported for this endpoint.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        print(f"[PaddleOCR] Converting PDF to images: {tmp_path}")
        
        # Use PyMuPDF to convert PDF to image (no poppler needed)
        pdf_document = fitz.open(tmp_path)
        print(f"[PaddleOCR] Processing first page only.")
        results = []
        annotated_paths = []
        import time
        
        # Process only the first page
        page = pdf_document[0]
        pix = page.get_pixmap(dpi=120)
        img_path = tmp_path + f"_page_1.png"
        pix.save(img_path)
        pdf_document.close()
        print(f"[PaddleOCR] Processing page 1 -> {img_path}")
        t0 = time.time()
        try:
            # Use the global OCR object
            result = paddle_ocr_and_annotate(img_path, ocr=ocr)
            results.append(result['texts'])
            annotated_paths.append(result['annotated_path'])
            print(f"[PaddleOCR] Page 1 done in {time.time() - t0:.2f} seconds.")
        except Exception as page_e:
            print(f"[PaddleOCR] Error processing page 1: {page_e}")
            results.append([f"Error processing page 1: {page_e}"])
            annotated_paths.append(None)
        
        # Extract document IDs from OCR text
        raw_text = result.get('raw_text', ' '.join(results[0]) if results else '')
        document_ids = extract_document_ids(raw_text)
        
        return {
            "filename": file.filename,
            "pages": 1,
            "texts": results,
            "raw_text": raw_text,
            "document_ids": document_ids,
            "document_type": list(document_ids.keys())[0] if document_ids else None,
            "annotated_image_paths": annotated_paths,
            "execution_time": result['execution_time']
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PaddleOCR PDF failed: {str(e)}")
