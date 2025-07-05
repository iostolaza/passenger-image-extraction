
"""
CameraOverlay
-------------
Handles live camera preview with overlay, guides, and saves captured images locally.
"""
# ==== Standard Library ====

import os
import cv2
import time
from datetime import datetime
from utils import generate_s3_key
from config.config import STORAGE_ROOT

class CameraOverlay:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id

    def capture_passport_with_overlay(self, doc_type, subtype, agency, country, state, airportcode):
        """Capture passport image with overlay (square)."""
        date = datetime.now().strftime("%Y%m%d")
        s3_key_full = generate_s3_key(
            images="Images", agency=agency, country=country, state=state,
            airportcode=airportcode, date=date, document_type=doc_type, subtype=subtype
        )
        s3_key_crop = s3_key_full.replace(f"/{subtype}/", f"/{subtype}-crop/")
        local_full_path = os.path.join(STORAGE_ROOT, s3_key_full)
        local_crop_path = os.path.join(STORAGE_ROOT, s3_key_crop)
        os.makedirs(os.path.dirname(local_full_path), exist_ok=True)
        os.makedirs(os.path.dirname(local_crop_path), exist_ok=True)

        cap = cv2.VideoCapture(self.camera_id)
        guide_color = (0, 255, 0)
        alpha = 0.4

        print("Align your PASSPORT inside the green box. Press SPACE to capture, ESC to exit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Camera error")
                break

            overlay = frame.copy()
            h, w, _ = frame.shape
            # Passport box is more square
            x1, y1 = int(0.20 * w), int(0.15 * h)
            x2, y2 = int(0.80 * w), int(0.85 * h)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), guide_color, 4)

            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                binarized_color = cv2.cvtColor(binarized, cv2.COLOR_GRAY2BGR)
                overlay[y1:y2, x1:x2] = cv2.addWeighted(binarized_color, alpha, roi, 1 - alpha, 0)
            out = cv2.addWeighted(overlay, 1, frame, 0, 0)

            cv2.putText(out, "Align PASSPORT in GREEN box. SPACE to capture. ESC to quit.",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Camera - Passport Overlay", out)

            key = cv2.waitKey(1)
            if key == 27:  # ESC
                print("User quit.")
                break
            elif key == 32:  # SPACE
                cv2.imwrite(local_full_path, frame)
                if roi.size > 0:
                    cv2.imwrite(local_crop_path, binarized)
                    print(f"Full image saved as: {local_full_path}")
                    print(f"Cropped doc region (binarized) saved as: {local_crop_path}")
                cap.release()
                cv2.destroyAllWindows()
                return local_full_path, local_crop_path, s3_key_full, s3_key_crop
        cap.release()
        cv2.destroyAllWindows()
        time.sleep(2) 
        return None, None, None, None

    def capture_boarding_pass_with_overlay(self, doc_type, subtype, agency, country, state, airportcode):
        time.sleep(4) 
        """Capture boarding pass image with overlay (rectangular)."""
        date = datetime.now().strftime("%Y%m%d")
        s3_key_full = generate_s3_key(
            images="Images", agency=agency, country=country, state=state,
            airportcode=airportcode, date=date, document_type=doc_type, subtype=subtype
        )
        s3_key_crop = s3_key_full.replace(f"/{subtype}/", f"/{subtype}-crop/")
        local_full_path = os.path.join(STORAGE_ROOT, s3_key_full)
        local_crop_path = os.path.join(STORAGE_ROOT, s3_key_crop)
        os.makedirs(os.path.dirname(local_full_path), exist_ok=True)
        os.makedirs(os.path.dirname(local_crop_path), exist_ok=True)

        cap = cv2.VideoCapture(self.camera_id)
        guide_color = (0, 255, 0)
        alpha = 0.4

        print(f"Align your BOARDING PASS ({subtype.upper()}) inside the green rectangle. Press SPACE to capture, ESC to exit.")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Camera error")
                break

            overlay = frame.copy()
            h, w, _ = frame.shape
            # Boarding pass is a wide rectangle
            x1, y1 = int(0.10 * w), int(0.25 * h)
            x2, y2 = int(0.90 * w), int(0.85 * h)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), guide_color, 4)

    
            roi = frame[y1:y2, x1:x2]
            if roi.size > 0:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                binarized_color = cv2.cvtColor(binarized, cv2.COLOR_GRAY2BGR)
                overlay[y1:y2, x1:x2] = cv2.addWeighted(binarized_color, alpha, roi, 1 - alpha, 0)
            out = cv2.addWeighted(overlay, 1, frame, 0, 0)

            cv2.putText(out, f"Align BOARDING PASS in GREEN box. SPACE to capture. ESC to quit.",
                        (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Camera - Boarding Pass Overlay", out)

            key = cv2.waitKey(1)
            if key == 27:  # ESC
                print("User quit.")
                break
            elif key == 32:  # SPACE
                cv2.imwrite(local_full_path, frame)
                if roi.size > 0:
                    cv2.imwrite(local_crop_path, binarized)
                    print(f"Full image saved as: {local_full_path}")
                    print(f"Cropped doc region (binarized) saved as: {local_crop_path}")
                cap.release()
                cv2.destroyAllWindows()
                return local_full_path, local_crop_path, s3_key_full, s3_key_crop
        cap.release()
        cv2.destroyAllWindows()
        return None, None, None, None