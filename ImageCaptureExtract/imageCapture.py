"""
CaptureImageStreamlit
---------------------
Handles image upload or camera capture using Streamlit.
"""
# ==== Standard Library ====

import os
import streamlit as st
from PIL import Image


class CaptureImageStreamlit:
    def __init__(self, save_path=None):
        self.save_path = save_path

    def capture_or_upload(self):
        img_file_buffer = st.camera_input("Take a picture")
        if img_file_buffer is not None:
            img = Image.open(img_file_buffer)
            img.save(self.save_path)
            st.image(self.save_path)
            return self.save_path

        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            img.save(self.save_path)
            st.image(self.save_path)
            return self.save_path

        return None
