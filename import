import pandas as pd
import requests
import base64
import time
import re
import json

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
CSV_FILE = "freshservice_migration.csv"

# FRESHSERVICE CONFIG
FS_DOMAIN = ""
FS_API_KEY = "YOUR_FRESHSERVICE_API_KEY"  # <--- Enter FS Key
WORKSPACE_ID = 2

# ATERA CONFIG (For fetching missing descriptions)
ATERA_API_KEY = "YOUR_ATERA_API_KEY"  # <--- Enter Atera Key
ATERA_BASE_URL = "https://app.atera.com/api/v3"

# SETTINGS
TEST_MODE = False  # Set False to run ALL
TEST_LIMIT = 5
SKIP_COUNT = 0


# ==============================================================================
# 2. HELPER: FETCH MISSING DATA FROM ATERA
# ==============================================================================
def fetch_full_history_from_atera(ticket_id):
    """
    If CSV description is missing, this fetches the Ticket + Comments from Atera
    and reconstructs the '--- [ Header ] ---' format so the parser works.
    """
    headers = {"X-Api-Key": ATERA_API_KEY, "Accept": "application/json"}
    formatted_text = ""

    try:
        # 1. Fetch Main Ticket Body
        t_res = requests.get(f"{ATERA_BASE_URL}/tickets/{ticket_id}", headers=headers)
        if t_res.status_code == 200:
            t_data = t_res.json()
            requester = t_data.get("EndUserFullName", "End User")
            body = t_data.get("Description", "")
            # Reconstruct Header
            formatted_text += f"--- [ Original Request by {requester} ] ---\n{body}\n\n"

        # 2. Fetch Comments (Conversation)
        c_res = requests.get(f"{ATERA_BASE_URL}/tickets/{ticket_id}/comments", headers=headers)
        if c_res.status_code == 200:
            c_data = c_res.json()
            # Comments usually come in a list under 'items'
            items = c_data.get("items", [])
            # Sort by date if possible, otherwise trust API order
            for c in items:
                # Find who wrote it
                if c.get("EndUserId"):
                    author = "End User"  # Or lookup name if available
                elif c.get("TechnicianContactId"):
                    author = "Technician"  # Or lookup name
                else:
                    author = "System"

                comment_body = c.get("Comment", "")
                formatted_text += f"--- [ Reply by {author} ] ---\n{comment_body}\n\n"

        return formatted_text

    except Exception as e:
        print(f"   ⚠️ API Fetch Warning: {e}")
        return ""


# ==============================================================================
# 3. SHERLOCK HOLMES LOGIC
# ==============================================================================
def clean_text_for_ai(text):
    if pd.isna(text): return ""
    text = str(text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"(?s)p, strong, em,.*?\{.*?\}", "", text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()


def detect_technician_signature(body_text, tech_name):
    if pd.isna(tech_name) or len(str(tech_name)) < 2: return False
    first_name = str(tech_name).split()[0]
    snippet = body_text[-50:]
    if re.search(r"(?i)(?:Regards|Thanks|Best|Cheers|From).*?" + re.escape(first_name), snippet):
        return True
    return False


def extract_sender_from_body(body_text):
    match = re.search(r"\*\*From:\*\*.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", body_text)
    if match: return match.group(1).strip()
    match = re.search(r"From:.*<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>", body_text)
    if match: return match.group(1).strip()
    return None


def determine_sender(header_text, body_text, row):
    email_in_body = extract_sender_from_body(body_text)
    if email_in_body: return f"{email_in_body} wrote"

    tech_name = row.get('Legacy Technician')
    if detect_technician_signature(body_text, tech_name):
        return f"{tech_name} (Technician) wrote"

    match = re.search(r"by (.*?) ]", header_text)
    header_name = match.group(1).strip() if match else "System"

    if str(header_name).lower() == str(tech_name).lower():
        return f"{tech_name} (Technician) wrote"

    if header_name.lower() == "end user":
        return "Correspondent wrote"

    return f"{header_name} wrote"


def parse_conversation_sherlock(full_text, row):
    if pd.isna(full_text) or str(full_text).strip() == "": return ""

    parts = re.split(r'(--- \[.*?\] ---)', full_text)
    html_output = ""
    current_sender = "Original Description"
    last_body_hash = ""

    for i in range(len(parts)):
        part = parts[i].strip()
        if not part: continue

        if part.startswith("--- [") and part.endswith("] ---"):
            next_body = parts[i + 1] if i + 1 < len(parts) else ""
            current_sender = determine_sender(part, next_body, row)
        else:
            clean_body = clean_text_for_ai(part)
            if clean_body and clean_body[:50] != last_body_hash[:50]:
                html_output += (
                    f"<p><strong>{current_sender}:</strong><br>"
                    f"{clean_body}</p><hr>"
                )
                last_body_hash = clean_body
    return html_output


# ==============================================================================
# 4. RUNNER
# ==============================================================================
auth_bytes = f"{FS_API_KEY}:X".encode()
headers = {
    "Content-
