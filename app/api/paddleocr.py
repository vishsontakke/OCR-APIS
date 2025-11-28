from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
from app.services.paddleocr_service import paddle_ocr_and_annotate

router = APIRouter(prefix="/paddleocr", tags=["PaddleOCR"])

@router.post("/predict", name="PaddleOCR Predict and Annotate")
async def paddleocr_predict(file: UploadFile = File(...)):
    try:
        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        result = paddle_ocr_and_annotate(tmp_path)
        return {
            "filename": file.filename,
            "texts": result['texts'],
            "annotated_image_path": result['annotated_path']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PaddleOCR failed: {str(e)}")
