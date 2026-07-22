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
        return sorted(dates, reverse=True)
    except Exception as e:
        return []

def get_attendance_for_date(service, date_str):
    """Fetch attendance records for a specific date (YYYY-MM-DD)."""
    sheet_name = f"{date_str} Attendance"
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{sheet_name}'!A7:H100"
        ).execute()
        rows = result.get("values", [])
        records = []
        for row in rows:
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
            # Determine if late (after 8:00 AM)
            late = False
            if rec["time_in"].strip():
                try:
                    t = datetime.strptime(rec["time_in"].strip(), "%I:%M %p")
                    late = t.hour > 8 or (t.hour == 8 and t.minute > 0)
                except ValueError:
                    pass
            rec["late"] = late

            if rec["name"].strip():
                records.append(rec)
        return records, None
    except Exception as e:
        return [], str(e)

import requests
from urllib.parse import quote

SHEET_ACTION_URL = os.environ.get("ATTENDANCE_SHEET_ACTION_URL")  # your Apps Script /exec URL

def _post_to_sheet(payload):
    """POST an action to the same Apps Script Web App the ESP32 uses."""
    if not SHEET_ACTION_URL:
        raise Exception("ATTENDANCE_SHEET_ACTION_URL not configured.")
    resp = requests.post(SHEET_ACTION_URL, data=payload, timeout=15)
    text = resp.text.strip()
    if text.startswith("ERROR"):
        raise Exception(text)
    return text

def update_task_accomplishment(sr_code, name, course, task, accomplishment, date_str):
    return _post_to_sheet({
        "action": "UPDATE_TASK_ACCOMPLISHMENT",
        "id": sr_code, "name": name, "course": course,
        "task": task, "accomplishment": accomplishment, "date": date_str,
    })

def add_student_to_sheet(sr_code, name, course):
    """Registers a student in the Sheet so the ESP32 can later enroll their fingerprint under this ID."""
    return _post_to_sheet({
        "action": "ADD_STUDENT",
        "id": sr_code, "name": name, "course": course,
        "date": None,
    })

def update_student_in_sheet(sr_code, name, course):
    return _post_to_sheet({
        "action": "UPDATE_STUDENT",
        "id": sr_code, "name": name, "course": course,
    })

def delete_student_from_sheet(sr_code, name):
    return _post_to_sheet({
        "action": "DELETE_STUDENT",
        "id": sr_code, "name": name,
    })

def upload_signature(sr_code, name, date_str, base64_png):
    return _post_to_sheet({
        "action": "UPLOAD_SIGNATURE",
        "id": sr_code, "name": name, "date": date_str,
        "signature": base64_png,
    })