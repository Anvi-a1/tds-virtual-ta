import base64
import io
from PIL import Image
import pytesseract

class OCR:
    def __init__(self, lang: str = "eng", config: str = ""):
        self.lang = lang
        self.config = config

    def extract_text(self, image_data: str) -> str:
        try:
            img_data = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_data)).convert("L")  # grayscale for better OCR
            return pytesseract.image_to_string(img, lang=self.lang, config=self.config)
        except Exception as e:
            raise ValueError(f"OCR decoding error: {e}")
