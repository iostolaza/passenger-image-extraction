"""
email.py
--------
Handles confirmation and notification email logic (e.g., SendGrid, SES).
"""

# ==== Standard Library ====

import os
from email.message import EmailMessage
import smtplib
from dotenv import load_dotenv

def send_zoho_email(to_email, subject, body, from_email, password):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.zoho.com", 465) as smtp:
        smtp.login(from_email, password)
        smtp.send_message(msg)
    print(f"Zoho Email sent to {to_email}")

def send_submission_email(user_email, name, confirmation_number, data):
    load_dotenv()
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    subject = "Your Travel Form Submission Received"
    body = f"""Dear {name},

Your travel form has been received.

Confirmation Number: {confirmation_number}

Proceed to the appropriate counter to check in.

Thank you and safe travels!
"""
    send_zoho_email(
        to_email=user_email,
        subject=subject,
        body=body,
        from_email=SMTP_USER,
        password=SMTP_PASS
    )
