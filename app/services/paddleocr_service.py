from paddleocr import PaddleOCR
from PIL import Image
import cv2
import numpy as np
import os

def paddle_ocr_and_annotate(img_path: str, save_annotated: bool = True, ocr=None):
    if ocr is None:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='en')
    result = ocr.predict(img_path)
    texts = result[0]['rec_texts']
    boxes = result[0]['rec_polys'] if 'rec_polys' in result[0] else result[0]['dt_polys']
    scores = result[0]['rec_scores']
    image = cv2.imread(img_path)
    if image is None:
        raise ValueError(f"Failed to load image for annotation: {img_path}")
    for box, text, score in zip(boxes, texts, scores):
        box = [(int(pt[0]), int(pt[1])) for pt in box]
        cv2.polylines(image, [np.array(box)], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.putText(image, text, box[0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    annotated_path = None
    if save_annotated:
        annotated_path = os.path.splitext(img_path)[0] + '_paddle_result.jpg'
        cv2.imwrite(annotated_path, image)
    return {
        'texts': texts,
        'annotated_path': annotated_path
    }
