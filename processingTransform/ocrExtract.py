"""
ocrExtract.py
--------------
Runs OCR (Tesseract/EasyOCR) on images and returns structured data.
"""

# ==== Standard Library ====

import os
import cv2
import pytesseract
import json

class OCRExtractor:
    def __init__(self, image_path=None):
        self.image_path = image_path

    def extract(self, image_path=None, save_json_path=None):
        if image_path is None:
            image_path = self.image_path
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Cannot load image: {image_path}")

        # 1. Run OCR for raw text only
        text = pytesseract.image_to_string(img)

        # 2. Always save the raw OCR text as JSON
        if save_json_path:
            # If save_json_path is given, use it directly
            save_path = save_json_path
        else:
            # If not, save in the same directory as the image, with -ocr_raw.json suffix
            base = os.path.splitext(image_path)[0]
            save_path = base + "-ocr_raw.json"
        # Make sure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save as JSON: just the raw text
        with open(save_path, "w") as f:
            json.dump({"text": text}, f, indent=2)
        print(f"OCR raw output saved as {save_path}")

        # 3. Return as dict (unchanged)
        return {"text": text}

