from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import fitz  # PyMuPDF
import os
from app.services.paddleocr_service import paddle_ocr_and_annotate
from paddleocr import PaddleOCR
from PIL import Image
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
        return {
            "filename": file.filename,
            "pages": 1,
            "texts": results,
            "annotated_image_paths": annotated_paths,
            "execution_time": result['execution_time']
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"PaddleOCR PDF failed: {str(e)}")
