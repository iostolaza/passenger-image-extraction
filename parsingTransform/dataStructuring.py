"""
data_structuring.py
-------------------
Cleans, validates, and structures extracted data into standardized JSON.
"""

# ==== Standard Library ====

import re
import json
from datetime import datetime
import boto3


class DataStandardizer:
    def __init__(self):
        pass

    def standardize(self, raw_data):
        text = raw_data["text"]
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        def find_after_label(label_patterns, lines, all_caps_ok=False):
            for i, line in enumerate(lines):
                for pat in label_patterns:
                    if re.search(pat, line, re.IGNORECASE):
                        for j in range(i+1, min(i+4, len(lines))):
                            val = lines[j].strip()
                            if not any(re.search(p, val, re.IGNORECASE) for p in label_patterns) and len(val) > 2:
                                if all_caps_ok and not val.isupper():
                                    continue
                                return re.sub(r'[^A-Z \-]', '', val.upper()).strip()
            return None

        def find_allcaps_after(label, lines):
            for i, line in enumerate(lines):
                if label.lower() in line.lower():
                    for j in range(i+1, min(i+4, len(lines))):
                        val = lines[j].strip()
                        if re.match(r'^[A-Z ]+$', val) and len(val) > 5:
                            return val.strip()
            return None

        def find_first_allcaps(lines):
            for line in lines:
                if re.match(r'^[A-Z ]+$', line) and len(line) > 5:
                    return line.strip()
            return None

        surname = find_after_label([r'surn[a-z]*', r'family name', r'last name'], lines)
        if not surname:
            for i, line in enumerate(lines):
                if 'surn' in line.lower() and i+1 < len(lines):
                    next_line = lines[i+1]
                    if next_line.isupper() and len(next_line) > 2:
                        surname = re.sub(r'[^A-Z]', '', next_line.upper()).strip()
                        break

        given_names = find_after_label([r'given names?', r'prenome', r'nombres?'], lines)
        if not given_names:
            for i, line in enumerate(lines):
                if 'given names' in line.lower() and i+1 < len(lines):
                    val = lines[i+1]
                    if len(val) > 2:
                        given_names = ' '.join(w for w in val.split() if w.isalpha()).strip()
                        break

        nationality = find_allcaps_after('nationality', lines)
        if not nationality:
            for line in lines:
                if "UNITED" in line and "STATES" in line:
                    nationality = "UNITED STATES"
                    break
        if not nationality:
            nationality = find_first_allcaps(lines)
        if nationality:
            nationality = nationality.replace("OF AM", "OF AMERICA").replace("UNITED STATES OF AMERICA", "UNITED STATES")

        dob = None
        m = re.search(r'(\d{1,2} [A-Z]{3,} \d{4})', text)
        if m:
            try:
                dob = datetime.strptime(m.group(1), "%d %b %Y").strftime("%Y-%m-%d")
            except Exception:
                dob = m.group(1)
        if not dob:
            for i, line in enumerate(lines):
                if "birth" in line.lower() and i+1 < len(lines):
                    val = lines[i+1]
                    if re.match(r"\d{1,2} [A-Z]{3,} \d{4}", val):
                        try:
                            dob = datetime.strptime(val, "%d %b %Y").strftime("%Y-%m-%d")
                        except Exception:
                            dob = val
                        break

        gender = None
        m = re.search(r'\b(M|F)\b', text)
        if m:
            gender = "Male" if m.group(1) == "M" else "Female"

        passport_number = None
        for line in lines[::-1]:
            if "<USA" in line or "USA" in line:
                m = re.search(r'([A-Z]\d{7,10})USA', line)
                if m:
                    passport_number = m.group(1)
                    break
        if not passport_number:
            m = re.search(r'\b([A-Z]\d{7,10})\b', text)
            if m:
                passport_number = m.group(1)

        out = {
            "surname": surname,
            "given_names": given_names,
            "nationality": nationality,
            "date_of_birth": dob,
            "gender": gender,
            "passport_number": passport_number
        }
        return out
    
    def standardize_boarding_pass(self, raw_data):
        text = raw_data.get("text", "")
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        airline = None
        flight_number = None
        passenger_name = None
        from_origin = None
        to_destination = None
        departure_date = None

        # 1. Airline (very top, or "Airlines"/"Airways" in name)
        for line in lines[:3]:
            if re.search(r'(AIRWAYS?|LINES?)', line, re.IGNORECASE):
                airline = line.title()
                break
        if not airline:
            for line in lines:
                if re.search(r'(AIRWAYS?|LINES?)', line, re.IGNORECASE):
                    airline = line.title()
                    break

        # 2. Flight number (formats: BA178, UA 415, DL-4023)
        FLIGHT_PATTERNS = [
            r'\b([A-Z]{2,3}\s?\d{2,5})\b',       # BA178, UA 415
            r'Flight[:\s]+([A-Z]{2,3}\s?\d{2,5})' # Flight: BA178
        ]
        for line in lines:
            for pat in FLIGHT_PATTERNS:
                m = re.search(pat, line)
                if m:
                    flight_number = m.group(1).replace(" ", "").replace("-", "")
                    break
            if flight_number: break

        # 3. Passenger name (often "Passenger:", "Name:", or ALLCAPS with space/slash/comma)
        for i, line in enumerate(lines):
            if "passenger" in line.lower() or "name" in line.lower():
                # Prefer next line, or text after colon
                after = re.sub(r'^(Passenger|Name)[:\s]*', '', line, flags=re.I)
                if after and len(after) > 2:
                    passenger_name = after.upper()
                elif i+1 < len(lines):
                    passenger_name = re.sub(r'[^A-Z \-/]', '', lines[i+1].upper()).strip()
                break
            # OCR might read JOHN DOE or SMITH/JOHN
            if re.match(r'^[A-Z\s\-\,/]{5,}$', line):
                if "/" in line or " " in line:
                    passenger_name = re.sub(r'[^A-Z \-/]', '', line.upper()).strip()
                    break

        # 4. IATA codes: From/To or XXX/XXX, XXX-XXX
        iata = re.compile(r'\b([A-Z]{3})\b')
        for i, line in enumerate(lines):
            # Direct "From: XXX" or "To: XXX"
            if "from" in line.lower():
                m = iata.search(line)
                if m:
                    from_origin = m.group(1)
            if "to" in line.lower():
                m = iata.search(line)
                if m:
                    to_destination = m.group(1)
        # Fallback: look for XXX/XXX or XXX-XXX
        if not (from_origin and to_destination):
            for line in lines:
                m = re.search(r'\b([A-Z]{3})[\/\-]([A-Z]{3})\b', line)
                if m:
                    from_origin, to_destination = m.group(1), m.group(2)
                    break

        # 5. Departure date: DD MMM, MM/DD/YYYY, YYYY-MM-DD
        date_patterns = [
            r'([A-Z][a-z]+ \d{1,2}, \d{4})',      # July 15, 2025
            r'(\d{1,2} [A-Z][a-z]+ \d{4})',       # 15 July 2025
            r'([A-Z]{3} \d{1,2}, \d{4})',         # JUL 15, 2025
            r'(\d{1,2} [A-Z]{3,} \d{4})',         # 15 JUL 2025

            r'(\d{4}-\d{2}-\d{2})',               # 2025-07-03
            r'(\d{2}/\d{2}/\d{4})',               # 07/03/2025
            r'(\d{2}\.\d{2}\.\d{4})',             # 03.07.2025
            r'(\d{4}/\d{2}/\d{2})',               # 2025/07/03

            r'(\d{1,2}-[A-Z]{3}-\d{4})',          # 15-JUL-2025

            r'([A-Z]{3,} \d{1,2} \d{4})',         # JUL 15 2025
            r'(\d{1,2} [A-Z]{3,} \d{4})',         # 15 JUL 2025
        ]
        for line in lines:
            for pat in date_patterns:
                m = re.search(pat, line)
                if m:
                    departure_date = m.group(1).strip()
                    break
            if departure_date: break

        # Normalize airline name (optional): drop (BA), trim, etc
        if airline:
            airline = re.sub(r'\([^)]*\)', '', airline).strip()

        # Normalize passenger name: JOHN DOE -> Doe, John (if possible)
        if passenger_name and '/' in passenger_name:
            # E.g. "DOE/JOHN" or "SMITH/ROBERT MICHAEL"
            parts = passenger_name.split('/')
            if len(parts) == 2:
                surname, given = parts
                passenger_name = f"{given.title()} {surname.title()}"

        # Output dict
        out = {
            "airline": airline,
            "flight_number": flight_number,
            "passenger_name": passenger_name,
            "from_origin": from_origin,
            "to_destination": to_destination,
            "departure_date": departure_date
        }
        return out


    def save_json_local(self, data, path):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved locally: {path}")

    def upload_json_to_s3(self, local_json_path, s3_bucket, s3_key):
        s3 = boto3.client('s3')
        s3.upload_file(local_json_path, s3_bucket, s3_key)
        print(f"Uploaded to S3: s3://{s3_bucket}/{s3_key}")