"""
formOperations.py
------------------
Handles form data structure, prefill, validation, and UI mapping.
"""
# ==== Standard Library ====

import os
import json
from datetime import datetime


def load_json(path):
    """Load JSON from a file, return empty dict if missing."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def merge_dicts(*dicts):
    """Merge any number of dicts, later ones overwrite earlier."""
    result = {}
    for d in dicts:
        result.update(d)
    return result

def prompt_with_prefill(prompt_text, prefill=None, allow_empty=False):
    """Prompt user with prefilled value (for CLI), allow editing or skipping."""
    if prefill:
        prompt = f"{prompt_text} [{prefill}]: "
    else:
        prompt = f"{prompt_text}: "
    while True:
        response = input(prompt)
        if response:
            return response
        elif prefill is not None:
            return prefill
        elif allow_empty:
            return ""
        else:
            print("This field is required.")

def prompt_yes_no(prompt_text, prefill=None):
    """Prompt Yes/No question, with prefilled answer."""
    yes_no = "[y/N]" if prefill is None else f"[{prefill[0].upper()}/{'N' if prefill.lower()=='no' else 'Y'}]"
    while True:
        response = input(f"{prompt_text} {yes_no}: ").strip().lower()
        if not response and prefill is not None:
            return prefill
        if response in ("y", "yes"):
            return "Yes"
        elif response in ("n", "no"):
            return "No"
        else:
            print("Please enter yes or no.")

def customs_declaration_cli_form(prefill_data):
    print("\n--- Customs Declaration Form ---\n")

    result = {}
    # Prefilled/Editable fields
    result["surname"] = prompt_with_prefill("Surname", prefill_data.get("surname"))
    result["given_names"] = prompt_with_prefill("Given Names", prefill_data.get("given_names"))
    result["nationality"] = prompt_with_prefill("Nationality", prefill_data.get("nationality"))
    result["date_of_birth"] = prompt_with_prefill("Date of Birth (YYYY-MM-DD)", prefill_data.get("date_of_birth"))
    result["gender"] = prompt_with_prefill("Gender (Male/Female)", prefill_data.get("gender"), allow_empty=True)
    result["passport_number"] = prompt_with_prefill("Passport Number", prefill_data.get("passport_number"))
    result["airline"] = prompt_with_prefill("Airline", prefill_data.get("airline"))
    result["flight_number"] = prompt_with_prefill("Flight Number", prefill_data.get("flight_number"))
    result["phone"] = prompt_with_prefill("Phone Number", prefill_data.get("phone"), allow_empty=True)
    result["email"] = prompt_with_prefill("Email (for confirmation)", prefill_data.get("email"), allow_empty=True)
    result["purpose"] = prompt_with_prefill("Purpose of trip", prefill_data.get("purpose"), allow_empty=True)

    print("\n--- Declarations (yes/no) ---\n")
    result["animals_plants"] = prompt_yes_no("1. Are you carrying animals or plants, or items that require quarantine?", prefill_data.get("animals_plants"))
    if result["animals_plants"] == "Yes":
        result["animals_plants_details"] = prompt_with_prefill("  Details (describe what you are carrying):", prefill_data.get("animals_plants_details"), allow_empty=True)
    result["commercial_articles"] = prompt_yes_no("2. Are you carrying commercial articles exceeding duty-free exemption?", prefill_data.get("commercial_articles"))
    if result["commercial_articles"] == "Yes":
        result["commercial_articles_details"] = prompt_with_prefill("  Details (describe what you are carrying):", prefill_data.get("commercial_articles_details"), allow_empty=True)
    result["currency"] = prompt_yes_no("3. Are you carrying $10,000 USD or more in currency/instruments?", prefill_data.get("currency"))
    if result["currency"] == "Yes":
        result["currency_amount"] = prompt_with_prefill("  Enter the amount and type of currency/instrument carried:", prefill_data.get("currency_amount"), allow_empty=True)
    result["prohibited_items"] = prompt_yes_no("4. Are you carrying prohibited items?", prefill_data.get("prohibited_items"))
    if result["prohibited_items"] == "Yes":
        result["prohibited_items_details"] = prompt_with_prefill("  Details (describe what you are carrying):", prefill_data.get("prohibited_items_details"), allow_empty=True)

    print("\n--- Final Declaration ---\n")
    truthful = input("I declare this form is truthful and in good faith. Type 'yes' to confirm: ")
    result["truthful"] = True if truthful.lower().startswith("y") else False
    result["signature"] = prompt_with_prefill("Provide your full name as electronic signature", prefill_data.get("signature"), allow_empty=False)
    result["date_signed"] = prompt_with_prefill("Date (YYYY-MM-DD)", prefill_data.get("date_signed") or str(datetime.now().date()))
    
    print("\n--- Preview of Your Submission ---\n")
    for k, v in result.items():
        print(f"{k}: {v}")

    submit = input("\nConfirm and Submit? (yes/no): ")
    if not result["truthful"] or not result["signature"] or not submit.lower().startswith("y"):
        print("\nSubmission NOT completed. (Missing confirmation, truthfulness, or signature.)")
        return None
    print("\nForm submitted!")
    return result



class FormOperations:
    def __init__(self):
        self.fields = {}

    def prefill(self, data):
        # Prefill fields from extracted/standardized data
        pass

    def validate(self):
        # Validate fields before submission
        pass

    def get_field(self, key):
        return self.fields.get(key)
    
