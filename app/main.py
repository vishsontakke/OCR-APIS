from fastapi import FastAPI
from app.api import users, ocr

app = FastAPI(title="Simple FastAPI App")

# Register routes
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])

@app.get("/")
def root():
    return {"message": "Welcome to FastAPI OCR APIs!"}
