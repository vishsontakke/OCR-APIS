from fastapi import FastAPI
from app.api import tesseract, users,ocr,paddleocr_pdf
from fastapi.middleware.cors import CORSMiddleware

from app.api.paddleocr import router as paddleocr_router

app = FastAPI(title="Simple FastAPI App",root_path="/ocr-api" )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


# Register routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(tesseract.router, prefix="/tesseract", tags=["Tesseract OCR"])
app.include_router(paddleocr_router)
app.include_router(paddleocr_pdf.router, prefix="/paddleocr", tags=["PaddleOCR"])
# app.include_router(google_ocr.router, prefix="/vision", tags=["Google Vision OCR"])

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI OCR APIs!"}
