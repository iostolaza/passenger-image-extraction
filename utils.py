"""
utils.py
--------
Helper functions: logging, config loading, error handling, general utilities.
"""

# ==== Standard Library ====

import os
import json
from datetime import datetime
import uuid

from parsingTransform.dataStructuring import DataStandardizer
from processingTransform.ocrExtract import OCRExtractor

def get_daypart(hour):
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"
    
def generate_confirmation_number(airport_code):
    """Example: LAX-25-18429 (5 digits from uuid)"""
    year = datetime.now().strftime("%y")
    code = str(uuid.uuid4().int)[-5:]  
    return f"{airport_code.upper()}-{year}-{code}"

def generate_s3_key(images, agency, country, state, airportcode, date, document_type, subtype):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S-%f")
    uuid_part = uuid.uuid4().hex
    daypart = get_daypart(now.hour)
    key = (
        f"{images}/{agency}/{country}/{state}/{airportcode}/{date}/"
        f"{document_type}/{subtype}/{daypart}/"
        f"img-{uuid_part}-{timestamp}.jpg"
    )
    return key

def process_passport_document(camera, s3, agency, country, state, airportcode, BUCKET_NAME):
    doc_type, subtype = "passport", "main"
    # --- 1. Capture image
    full_img_path, crop_img_path, s3_key_full, s3_key_crop = camera.capture_passport_with_overlay(
        doc_type, subtype, agency, country, state, airportcode
    )
    if not all([full_img_path, crop_img_path, s3_key_full, s3_key_crop]):
        print("Passport image not captured.")
        return None

    # --- 2. Upload to S3
    s3.upload_file(full_img_path, s3_key_full)
    s3.upload_file(crop_img_path, s3_key_crop)

    # --- 3. OCR extraction & save raw OCR JSON
    ocr = OCRExtractor(crop_img_path)
    ocr_raw_path = crop_img_path.rsplit('.', 1)[0] + "-ocr_raw.json"
    raw_data = ocr.extract(save_json_path=ocr_raw_path)
    # Optional: Upload raw OCR to S3
    s3.upload_file(ocr_raw_path, s3_key_crop.rsplit('.', 1)[0] + "-ocr_raw.json")

    # --- 4. Data Standardizing
    standardizer = DataStandardizer()
    clean_data = standardizer.standardize(raw_data)
    local_json_path = crop_img_path + ".passenger.json"
    standardizer.save_json_local(clean_data, local_json_path)
    s3.upload_file(local_json_path, s3_key_crop + ".passenger.json")


    print(f"Passport processed: {clean_data} JSON Path: {local_json_path}")
    return {"data": clean_data, "json_path": local_json_path}

    # print(f"Passport processed: {clean_data}")
    # return clean_data

def process_boarding_pass_document(camera, s3, agency, country, state, airportcode, subtype, BUCKET_NAME):
    doc_type = "boarding_pass"
    # --- 1. Capture image
    full_img_path, crop_img_path, s3_key_full, s3_key_crop = camera.capture_boarding_pass_with_overlay(
        doc_type, subtype, agency, country, state, airportcode
    )
    if not all([full_img_path, crop_img_path, s3_key_full, s3_key_crop]):
        print(f"Boarding pass ({subtype}) image not captured.")
        return None

    # --- 2. Upload to S3
    s3.upload_file(full_img_path, s3_key_full)
    s3.upload_file(crop_img_path, s3_key_crop)

    # --- 3. OCR extraction & save raw OCR JSON
    ocr = OCRExtractor(crop_img_path)
    ocr_raw_path = crop_img_path.rsplit('.', 1)[0] + "-ocr_raw.json"
    raw_data = ocr.extract(save_json_path=ocr_raw_path)
    # Optional: Upload raw OCR to S3
    s3.upload_file(ocr_raw_path, s3_key_crop.rsplit('.', 1)[0] + "-ocr_raw.json")

    # --- 4. Data Standardizing
    standardizer = DataStandardizer()
    clean_data = standardizer.standardize_boarding_pass(raw_data)
    local_json_path = crop_img_path + ".passenger.json"
    standardizer.save_json_local(clean_data, local_json_path)
    s3.upload_file(local_json_path, s3_key_crop + ".passenger.json")

    print(f"Boarding pass {subtype} processed: {clean_data} JSON Path: {local_json_path}")
    return {"data": clean_data, "json_path": local_json_path}
    # return clean_data

def get_completed_form_dir(agency, country, state, airportcode, base_dir=None):
    """
    Returns the full local directory for completed forms, ensures directory exists.
    """
    if base_dir is None:
        from config.config import STORAGE_ROOT
        base_dir = os.path.join(STORAGE_ROOT, "Images")
    today = datetime.now().strftime("%Y%m%d")
    folder = os.path.join(
        base_dir, agency, country, state, airportcode, today, "completedformsjson"
    )
    os.makedirs(folder, exist_ok=True)
    return folder

def completed_form_s3_key(local_path):
    """
    Given a completed form local path, return the S3 key with Images/ prefix.
    """
    key = local_path.split("/Images/", 1)[-1]
    return f"Images/{key}"

def extract_user_info_from_form(form_json_path):
    """Returns (name, email, form dict) from completed form JSON path."""
    with open(form_json_path) as f:
        data = json.load(f)
    surname = data.get("surname", "")
    given_names = data.get("given_names", "")
    email = data.get("email", "")
    full_name = f"{given_names} {surname}".strip()
    confirmation_number = data.get("confirmation_number")
    return full_name, email, data, confirmation_number
