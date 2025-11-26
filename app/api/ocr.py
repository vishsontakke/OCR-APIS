from fastapi import APIRouter, File, UploadFile, HTTPException,Form
from pathlib import Path
import tempfile
import re
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


@router.post("/verify-ocr", name="Perform OCR and Verify Name/DOB")
async def verify_ocr(
    file: UploadFile = File(...),
    name: str = Form(...),
    dob: str = Form(...),
    Pan:str = Form(...)
):
    """
    Perform OCR on uploaded image/video/PDF and check if provided name and DOB exist in extracted text.
    """
    try:
        # Save temporarily
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Determine type and extract text
        if suffix in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
            results = extract_text_from_image(tmp_path)
        elif suffix in [".mp4", ".mov", ".avi", ".mkv"]:
            results = extract_text_from_video(tmp_path, frame_skip=15)
        elif suffix in [".pdf"]:
            results = extract_text_from_pdf(tmp_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

        # # Combine all recognized text
        # full_text = " ".join(
        #     [item.get("text", "") for item in results if item.get("text")]
        # ).strip().lower()

        # # Normalize and check presence
        # name_present = name.lower() in full_text
        # dob_present = dob.lower() in full_text
        # Pan_present = Pan.lower() in full_text


        # Combine all recognized text
        full_text = " ".join(
            [item.get("text", "") for item in results if item.get("text")]
        ).strip().lower()


        def exact_phrase(text, phrase):
            if not phrase:
                return False
            phrase = phrase.lower().strip()
            # \b → ensures exact full-word boundary (no partial matches)
            pattern = r"\b" + re.escape(phrase) + r"\b"
            return re.search(pattern, text) is not None


        # Exact match checks
        name_present = exact_phrase(full_text, name)
        dob_present = exact_phrase(full_text, dob)
        Pan_present = exact_phrase(full_text, Pan)

        verification_status = "verified" if (name_present and dob_present and Pan_present) else "not_verified"

        return {
            # "filename": file.filename,
            # "total_items": len(results),
            # "results": results,
            "full_text": full_text,
            "name_found": name_present,
            "dob_found": dob_present,
            "Pan_found": Pan_present,
            "status": verification_status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR verification failed: {str(e)}")