from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import shutil

from app.services.paddleocr_service import paddle_ocr_and_annotate, ocr  # Import preloaded OCR

router = APIRouter(prefix="/paddleocr", tags=["PaddleOCR"])

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

        return {
            "filename": file.filename,
            "texts": result["texts"],
            "raw_text": result["raw_text"],
            "execution_time": result["execution_time"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PaddleOCR failed: {str(e)}")
