import pytesseract
from pathlib import Path
from typing import List, Tuple
import cv2
import numpy as np

def load_image(image_path: Path) -> np.ndarray:
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Failed to load image: {image_path}")
    return image

def preprocess_variants(image: np.ndarray) -> List[Tuple[str, np.ndarray]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, bin_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bin_adaptive = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )
    sharp = cv2.GaussianBlur(gray, (0, 0), 3)
    sharp = cv2.addWeighted(gray, 1.5, sharp, -0.5, 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morph = cv2.morphologyEx(bin_otsu, cv2.MORPH_OPEN, kernel)
    return [
        ("gray", gray),
        ("otsu", bin_otsu),
        ("adaptive", bin_adaptive),
        ("sharp", sharp),
        ("morph", morph),
    ]

def ocr_text(img: np.ndarray, psm: int) -> Tuple[str, float]:
    config = f"--oem 3 --psm {psm} -c tessedit_write_images=0"
    data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
    text = " ".join([w for w in data["text"] if w.strip() != ""])
    confs = [int(c) for c in data["conf"] if str(c).isdigit() and int(c) > -1]
    avg_conf = sum(confs) / len(confs) if confs else 0
    return text.strip(), avg_conf

def tesseract_best_ocr(image_path: str):
    img = load_image(Path(image_path))
    variants = preprocess_variants(img)
    best_text = ""
    best_conf = -1
    best_variant = ""
    for vname, vimg in variants:
        for psm in (6, 11, 12, 13):
            text, conf = ocr_text(vimg, psm)
            if conf > best_conf and len(text) > 5:
                best_conf = conf
                best_text = text
                best_variant = f"{vname} | psm={psm}"
    return {
        "text": best_text,
        "confidence": best_conf,
        "variant": best_variant
    }
