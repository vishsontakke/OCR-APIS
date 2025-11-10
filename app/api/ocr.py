from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
from app.services.ocr_service import extract_text_from_image, extract_text_from_video, extract_text_from_pdf

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/", name="Perform OCR (Image or Video)")
async def perform_ocr(file: UploadFile = File(...)):
    """
    Perform OCR on uploaded image or video.
    """
    try:
        # Save temporarily
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        if suffix in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
            results = extract_text_from_image(tmp_path)
        elif suffix in [".mp4", ".mov", ".avi", ".mkv"]:
            results = extract_text_from_video(tmp_path, frame_skip=15)
        elif suffix in [".pdf"]:
            results = extract_text_from_pdf(tmp_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

          # Combine all recognized text for convenience
        full_text = " ".join(
            [item.get("text", "") for item in results if item.get("text")]
        ).strip()

        return {
            "filename": file.filename,
            "total_items": len(results),
            "results": results,
            "full_text": full_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
