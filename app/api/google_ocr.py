from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
from app.services.vision_service import extract_text_from_image_gcv

router = APIRouter(prefix="/vision", tags=["Google Vision OCR"])

@router.post("/ocr", name="Google Vision OCR")
async def google_ocr(file: UploadFile = File(...)):
    """
    Perform OCR using Google Cloud Vision API.
    """
    try:
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        if suffix not in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

        result = extract_text_from_image_gcv(tmp_path)

        return {
            "filename": file.filename,
            "text": result["text"],
            "annotations": result["annotations"],
            "total_words": len(result["annotations"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
