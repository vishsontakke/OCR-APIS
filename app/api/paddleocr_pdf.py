from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
from pdf2image import convert_from_path
import os
from app.services.paddleocr_service import paddle_ocr_and_annotate
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='en')  # Load once, reuse for all pages

router = APIRouter(prefix="/paddleocr", tags=["PaddleOCR"])

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
        images = convert_from_path(tmp_path, dpi=120)  # Lower DPI for speed
        print(f"[PaddleOCR] PDF has {len(images)} pages. Limiting to first 3 pages for test.")
        max_pages = 3
        results = []
        annotated_paths = []
        import time
        for i, page in enumerate(images[:max_pages]):
            img_path = tmp_path + f"_page_{i+1}.png"
            page.save(img_path, "PNG")
            print(f"[PaddleOCR] Processing page {i+1} -> {img_path}")
            t0 = time.time()
            try:
                # Use the global OCR object for all pages
                result = paddle_ocr_and_annotate(img_path, ocr=ocr)
                results.append(result['texts'])
                annotated_paths.append(result['annotated_path'])
                print(f"[PaddleOCR] Page {i+1} done in {time.time() - t0:.2f} seconds.")
            except Exception as page_e:
                print(f"[PaddleOCR] Error processing page {i+1}: {page_e}")
                results.append([f"Error processing page {i+1}: {page_e}"])
                annotated_paths.append(None)
        return {
            "filename": file.filename,
            "pages": min(len(images), max_pages),
            "texts": results,
            "annotated_image_paths": annotated_paths
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PaddleOCR PDF failed: {str(e)}")
