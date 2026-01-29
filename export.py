import requests
import csv
import time

# ==========================================
#              CONFIGURATION
# ==========================================

# 1. YOUR API KEY
ATERA_API_KEY = ""  # <--- PASTE KEY HERE

# 2. API SETTINGS (Based on Atera Documentation)
BASE_URL = "https://app.atera.com/api/v3"
ENDPOINT = "tickets"

# 3. OUTPUT FILE NAME
OUTPUT_FILE = "atera_all_tickets_dump.csv"


# ==========================================
#              MAIN SCRIPT
# ==========================================

def get_all_tickets():
    """
    Fetches all tickets from Atera using pagination parameters.
    Ref: https://support.atera.com/hc/en-us/articles/219083397-APIs
    """
    all_tickets = []
    page = 1
    items_per_page = 50  # Max allowed by Atera API

    print("--- STARTING EXTRACTION ---")

    while True:
        print(f"   Requesting Page {page}...")

        # DEFINING THE CORRECT PARAMETERS
        params = {
            "page": page,
            "itemsInPage": items_per_page
        }

        headers = {
            "X-Api-Key": ATERA_API_KEY,
            "Accept": "application/json"
        }

        try:
            response = requests.get(f"{BASE_URL}/{ENDPOINT}", headers=headers, params=params)

            if response.status_code != 200:
                print(f"❌ Error: API returned status {response.status_code}")
                print(response.text)
                break

            data = response.json()

            # CHECK IF PAGE IS EMPTY (End of data)
            current_batch = data.get("items", [])
            if not current_batch:
                print("   -> No more items found. Finished downloading.")
                break

            all_tickets.extend(current_batch)
            page += 1

            # Optional: Short pause to be gentle on the API
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Critical Error: {e}")
            break

    return all_tickets


# ==========================================
#              WRITE TO CSV
# ==========================================

tickets = get_all_tickets()

if tickets:
    print(f"--- WRITING {len(tickets)} TICKETS TO CSV ---")

    # Define the columns we want to see in the Excel file
    # We map 'FirstComment' to 'Description' here
    fieldnames = [
        "TicketID",
        "TicketTitle",
        "Description (FirstComment)",
        "TicketStatus",
        "TicketPriority",
        "EndUserEmail",
        "TechnicianFullName",
        "TicketCreatedDate",
        "TicketClosedDate"
    ]

    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for t in tickets:
            # We create a clean row dictionary
            row = {
                "TicketID": t.get("TicketID"),
                "TicketTitle": t.get("TicketTitle"),
                # The Fix: Use FirstComment as the Description
                "Description (FirstComment)": t.get("FirstComment") or t.get("Description") or "No Content",
                "TicketStatus": t.get("TicketStatus"),
                "TicketPriority": t.get("TicketPriority"),
                "EndUserEmail": t.get("EndUserEmail"),
                "TechnicianFullName": t.get("TechnicianFullName"),
                "TicketCreatedDate": t.get("TicketCreatedDate"),
                "TicketClosedDate": t.get("TicketClosedDate")
            }
            writer.writerow(row)

    print(f"✅ SUCCESS! Data saved to: {OUTPUT_FILE}")
else:
    print("⚠️ No tickets were found or authentication failed.")
