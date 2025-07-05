
"""
S3Storage
---------
Handles uploading images to S3.
"""
# ==== Standard Library ====
import os
import boto3

from utils import generate_s3_key

class S3Storage:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3')

    def upload_file(self, local_path, s3_key):
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"{local_path} does not exist")
        self.s3.upload_file(local_path, self.bucket_name, s3_key)
        print(f"Uploaded to S3: s3://{self.bucket_name}/{s3_key}")
        return f"s3://{self.bucket_name}/{s3_key}"

