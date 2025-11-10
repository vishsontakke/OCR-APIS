import easyocr
import ssl
import re
import cv2
import numpy as np
from pathlib import Path
from pdf2image import convert_from_path

# Fix SSL certificate verification issue on macOS
ssl._create_default_https_context = ssl._create_unverified_context


# -------------------------------------------------------------
# Utility: English text filtering
# -------------------------------------------------------------
def is_english(text):
    """Check if a string contains only English-like characters."""
    pattern = re.compile(r'^[a-zA-Z0-9\s\.\,\!\?\-\:\;\'\"\/\(\)\@\#\$\%\&\*\+\=\_]+$')
    return bool(pattern.match(text))


def contains_english_words(text):
    """Check if a string contains at least 50% English characters."""
    english_chars = sum(1 for c in text if c.isascii() and (c.isalnum() or c.isspace()))
    total_chars = len(text.replace(' ', ''))
    return total_chars > 0 and (english_chars / total_chars) >= 0.5


def filter_english_only(text):
    """Remove non-English characters but keep valid English words."""
    words = text.split()
    english_words = [
        ''.join(char for char in w if char.isascii())
        for w in words
        if is_english(w) or contains_english_words(w)
    ]
    return ' '.join(w.strip() for w in english_words if w.strip())


# -------------------------------------------------------------
# Utility: Clean numpy types for JSON serialization
# -------------------------------------------------------------
def clean_numpy_types(obj):
    """Recursively convert NumPy types to native Python types."""
    if isinstance(obj, dict):
        return {k: clean_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_numpy_types(v) for v in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj


# -------------------------------------------------------------
# OCR from Image
# -------------------------------------------------------------
def extract_text_from_image(image_path: str, languages=['en']):
    """
    Extract text from an image using EasyOCR.
    Args:
        image_path (str): Path to image file
        languages (list): OCR language codes (default: ['en'])
    Returns:
        list: OCR results with text, confidence, and bounding boxes
    """
    try:
        reader = easyocr.Reader(languages, gpu=False)
        results = reader.readtext(image_path)

        extracted = []
        for (bbox, text, confidence) in results:
            cleaned = filter_english_only(text)
            bbox_py = [[float(x), float(y)] for (x, y) in np.array(bbox).tolist()]
            extracted.append({
                "text": cleaned,
                "confidence": round(float(confidence), 2),
                "bbox": bbox_py
            })

        return clean_numpy_types(extracted)
    except Exception as e:
        raise RuntimeError(f"OCR image processing failed: {str(e)}")


# -------------------------------------------------------------
# OCR from Video
# -------------------------------------------------------------
def extract_text_from_video(video_path: str, languages=['en'], frame_skip=10):
    """
    Extract text from a video by running OCR on every nth frame.
    Args:
        video_path (str): Path to video file
        languages (list): OCR language codes
        frame_skip (int): Number of frames to skip between OCR reads
    Returns:
        list: OCR results for each processed frame
    """
    try:
        reader = easyocr.Reader(languages, gpu=False)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        frame_count = 0
        results = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_skip != 0:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ocr_results = reader.readtext(frame_rgb)

            for (bbox, text, confidence) in ocr_results:
                cleaned = filter_english_only(text)
                bbox_py = [[float(x), float(y)] for (x, y) in np.array(bbox).tolist()]
                results.append({
                    "frame": int(frame_count),
                    "text": cleaned,
                    "confidence": round(float(confidence), 2),
                    "bbox": bbox_py
                })

        cap.release()
        return clean_numpy_types(results)

    except Exception as e:
        raise RuntimeError(f"OCR video processing failed: {str(e)}")


# -------------------------------------------------------------
# OCR from PDF
# -------------------------------------------------------------
def extract_text_from_pdf(pdf_path: str, languages=['en']):
    """
    Extract text from each page of a PDF using EasyOCR.
    Args:
        pdf_path (str): Path to PDF file
        languages (list): OCR language codes
    Returns:
        list: OCR results for each page
    """
    try:
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path, dpi=300)
        reader = easyocr.Reader(languages, gpu=False)
        results = []

        for page_num, page in enumerate(pages, start=1):
            image_np = np.array(page)
            ocr_results = reader.readtext(image_np)

            for (bbox, text, confidence) in ocr_results:
                cleaned = filter_english_only(text)
                bbox_py = [[float(x), float(y)] for (x, y) in np.array(bbox).tolist()]
                results.append({
                    "page": int(page_num),
                    "text": cleaned,
                    "confidence": round(float(confidence), 2),
                    "bbox": bbox_py
                })

        return clean_numpy_types(results)

    except Exception as e:
        raise RuntimeError(f"OCR PDF processing failed: {str(e)}")
