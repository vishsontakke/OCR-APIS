from google.cloud import vision
from google.oauth2 import service_account
import io, json

# 👇 Paste your JSON key content here (just for local testing)


# Create credentials from the dictionary
credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_JSON)

def extract_text_from_image_gcv(image_path: str):
    client = vision.ImageAnnotatorClient(credentials=credentials)

    with io.open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    texts = response.text_annotations
    if not texts:
        return {"text": "", "annotations": []}

    full_text = texts[0].description
    annotations = [
        {
            "description": t.description,
            "bounding_poly": [
                {"x": v.x, "y": v.y}
                for v in t.bounding_poly.vertices
            ]
        }
        for t in texts[1:]
    ]

    return {"text": full_text.strip(), "annotations": annotations}
