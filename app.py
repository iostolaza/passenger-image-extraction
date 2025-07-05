"""
main.py
-------
Main entry point. Orchestrates the workflow using modular classes.
"""

# ==== Standard Library ====

import os
import json
from datetime import datetime
from matplotlib import pyplot as plt

from ImageCaptureExtract.imageCapture import CaptureImageStreamlit
from ImageCaptureExtract.cameraOverlay import CameraOverlay
from formOpLoad.formOperations import (
    load_json, merge_dicts, customs_declaration_cli_form, FormOperations
)
from cloudStorageExtract.storageS3 import S3Storage
from parsingTransform.dataStructuring import DataStandardizer
from processingTransform.ocrExtract import OCRExtractor
from submitLoad.email import send_submission_email
from utils import (
    process_passport_document, process_boarding_pass_document, get_completed_form_dir,
    generate_s3_key, completed_form_s3_key, extract_user_info_from_form,
    generate_confirmation_number
)
from config.config import BUCKET_NAME, STORAGE_ROOT



def main():
    agency, country, state, airportcode = "CPB", "US", "CA", "lax"
    camera = CameraOverlay(camera_id=1)
    s3 = S3Storage(bucket_name=BUCKET_NAME)

    passport_json_path = ""
    arrival_json_path = ""
    departure_json_path = ""

    WORKFLOW_STAGES = [
        {"type": "passport"},
        {"type": "boarding_pass", "subtype": "arrival"},
        {"type": "boarding_pass", "subtype": "departure"}
    ]

    for stage in WORKFLOW_STAGES:
        if stage["type"] == "passport":
            print("\n--- STAGE: PASSPORT ---")
            # Returns full result AND path
            passport_result = process_passport_document(
                camera, s3, agency, country, state, airportcode, BUCKET_NAME)
            passport_json_path = passport_result["json_path"]

        elif stage["type"] == "boarding_pass":
            print(f"\n--- STAGE: BOARDING PASS ({stage['subtype'].upper()}) ---")
            if stage["subtype"] == "departure":
                user_input = input("Process DEPARTURE boarding pass? (y/n): ").strip().lower()
                if not user_input.startswith("y"):
                    continue
            bp_result = process_boarding_pass_document(
                camera, s3, agency, country, state, airportcode, stage["subtype"], BUCKET_NAME
            )
            if stage["subtype"] == "arrival":
                arrival_json_path = bp_result["json_path"]
            else:
                departure_json_path = bp_result["json_path"]

        # --- Load, merge JSONs ---
    passport_data = load_json(passport_json_path)
    arrival_data = load_json(arrival_json_path)
    departure_data = load_json(departure_json_path) if departure_json_path and os.path.exists(departure_json_path) else {}

    prefill_data = merge_dicts(passport_data, arrival_data, departure_data)

    # --- Prefill form ---
    form = FormOperations()
    form.prefill(prefill_data)

    # --- Rest of form ---
    form_result = customs_declaration_cli_form(prefill_data)
    if form_result:
        # Generate confirmation number BEFORE saving
        confirmation_number = generate_confirmation_number(airportcode)
        form_result["confirmation_number"] = confirmation_number

        completed_dir = get_completed_form_dir(agency, country, state, airportcode)
        filename = f"declaration_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        local_path = os.path.join(completed_dir, filename)
        with open(local_path, "w") as f:
            json.dump(form_result, f, indent=2)
        print(f"Submission saved to {local_path}")

        s3_key = completed_form_s3_key(local_path)
        s3.upload_file(local_path, s3_key)
        print(f"Uploaded to S3: s3://{BUCKET_NAME}/{s3_key}")

     # Email confirmation
    name, user_email, data, confirmation_number = extract_user_info_from_form(local_path)
    if user_email:
        send_submission_email(user_email, name, confirmation_number, data)
    else:
        print("No user email provided, skipping email notification.")
  
    print("\nAll document types processed.")

if __name__ == "__main__":
    main()


