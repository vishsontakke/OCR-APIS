from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
from app.services.tesseract_service import tesseract_best_ocr

router = APIRouter(prefix="/tesseract", tags=["Tesseract OCR"])

@router.post("/tes", name="Perform Tesseract OCR (Best Variant)")
async def perform_tesseract_ocr(file: UploadFile = File(...)):
    """
    Perform high-accuracy Tesseract OCR on uploaded image using multiple preprocessing variants.
    """
    try:
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        result = tesseract_best_ocr(tmp_path)
        return {
            "filename": file.filename,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tesseract OCR failed: {str(e)}")
