import os
import json
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SPREADSHEET_ID = "1e0nMqdJsCamaD8mBs3R0Ez3PWt5W3_jDPLR8q-N2sAM"

def get_sheets_service():
    cred_json = os.environ.get("ATTENDANCE_GOOGLE_CREDENTIALS")
    if not cred_json:
        raise Exception("ATTENDANCE_GOOGLE_CREDENTIALS not set.")
    creds = Credentials.from_service_account_info(json.loads(cred_json), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def get_available_dates(service, days_back=30):
    """Get list of sheet names that match YYYY-MM-DD Attendance format."""
    try:
        metadata = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        sheets = metadata.get("sheets", [])
        dates = []
        for sheet in sheets:
            title = sheet["properties"]["title"]
            if title.endswith(" Attendance") and len(title) == len("YYYY-MM-DD Attendance"):
                date_part = title.replace(" Attendance", "")
                try:
                    datetime.strptime(date_part, "%Y-%m-%d")
                    dates.append(date_part)
                except ValueError:
                    pass
        return sorted(dates, reverse=True)  # newest first
    except Exception as e:
        return []

def get_attendance_for_date(service, date_str):
    """Fetch attendance records for a specific date (YYYY-MM-DD)."""
    sheet_name = f"{date_str} Attendance"
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{sheet_name}'!A7:H100"  # skip rows 1-6 (title, meta, example row)
        ).execute()
        rows = result.get("values", [])
        records = []
        for row in rows:
            # Skip empty rows
            if not any(cell.strip() for cell in row if cell):
                continue
            padded = row + [""] * (8 - len(row))
            rec = {
                "id": padded[0],
                "name": padded[1],
                "course": padded[2],
                "time_in": padded[3],
                "task": padded[4],
                "accomplishment": padded[5],
                "time_out": padded[6],
            }
            # Only include rows that have at least a name
            if rec["name"].strip():
                records.append(rec)
        return records, None
    except Exception as e:
        return [], str(e)