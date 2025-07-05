
# config.py

import yaml
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/Users/franciscoostolaza/passenger-image-extraction/.env")

with open("config/settings.yaml", "r") as f:
    cfg = yaml.safe_load(f)

BUCKET_NAME = os.getenv("BUCKET_NAME", cfg["cloud_storage"]["aws_bucket"])

STORAGE_ROOT = os.getenv("STORAGE_ROOT", "/Users/franciscoostolaza/passenger-image-extraction")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", cfg["email"]["sendgrid_api_key"])
YOLO_WEIGHTS = cfg["ml_models"]["yolo_weights_path"]
