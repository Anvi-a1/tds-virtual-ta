import io
import json
import base64
from typing import Any, Dict, Union
from PIL import Image
import pytesseract


def load_json(file_path: str) -> Union[Dict[str, Any], list]:
    """Load a JSON file and return its contents."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: str, data: Union[Dict[str, Any], list]) -> None:
    """Save data (dict or list) to a JSON file with UTF-8 encoding."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def extract_text_from_image(image_data: str) -> str:
    """Decode a base64-encoded image and extract text using OCR."""
    img_data = base64.b64decode(image_data)
    img = Image.open(io.BytesIO(img_data))
    return pytesseract.image_to_string(img)


def handle_ocr(image_data: str) -> str:
    """Wrapper for OCR with error handling."""
    try:
        return extract_text_from_image(image_data)
    except Exception as e:
        raise ValueError(f"OCR decoding error: {e}")
