from paddleocr import PaddleOCR

# ------------------------------
# Load OCR Once (Huge Speed Boost)
# ------------------------------
ocr = PaddleOCR(lang='hi')

def paddle_ocr_and_annotate(img_path: str, ocr=None):
    """
    FAST PaddleOCR extraction using predict() 
    Compatible with PaddleOCR 3.3.1
    Returns ONLY raw text (no boxes, no saving)
    """
    import time
    start_time = time.time()
    if ocr is None:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='hi')
        
    result = ocr.predict(img_path)
    texts = result[0]['rec_texts'] 
    raw_text = " ".join(texts)

    exec_time = time.time() - start_time

    return {
        "texts": texts,
        "raw_text": raw_text,
        "annotated_path": None,  # Annotation saving not implemented here
        "execution_time": exec_time
    }
