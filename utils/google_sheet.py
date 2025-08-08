import os
import gspread
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "CourtData")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")


def get_gsheet_client():
    """Authenticate and return a gspread client."""
    return gspread.service_account(filename=CREDENTIALS_FILE)


def read_case_ids(sheet_name: str = SHEET_NAME) -> List[str]:
    """Read case IDs from the first column of the Google Sheet."""
    gc = get_gsheet_client()
    sh = gc.open(sheet_name)
    worksheet = sh.sheet1
    case_ids = worksheet.col_values(1)[1:]  # Skip header
    return case_ids


def write_results(results: List[Dict], sheet_name: str = SHEET_NAME):
    """Write results to the Google Sheet, starting from row 2."""
    gc = get_gsheet_client()
    sh = gc.open(sheet_name)
    worksheet = sh.sheet1
    headers = list(results[0].keys())
    worksheet.update('A1', [headers])
    rows = [[r.get(h, "") for h in headers] for r in results]
    worksheet.update(f'A2', rows)
