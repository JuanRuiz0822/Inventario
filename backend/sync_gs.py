cat > backend/sync_gs.py << 'EOF'
import os
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "inventario.db"
CREDENTIALS_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", str(BASE_DIR / "credentials.json"))
SHEET_ID = os.environ.get("GS_SHEET_ID", None)
SHEET_NAME = os.environ.get("GS_SHEET_NAME", "Sheet1")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gspread_client():
    creds = Credentials.from_service_account_file(CREDENTIALS_JSON, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def normalize_cols(cols):
    return [str(c).strip().replace(" ", "_").lower() for c in cols]

def pull_sheet_to_sqlite(sheet_id: str = None, sheet_name: str = None):
    sheet_id = sheet_id or SHEET_ID
    sheet_name = sheet_name or SHEET_NAME
    if not sheet_id:
        raise ValueError("SHEET_ID no configurado. Define GS_SHEET_ID env var.")
    client = get_gspread_client()
    sh = client.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except Exception:
        ws = sh.sheet1

    records = ws.get_all_records()
    df = pd.DataFrame.from_records(records) if records else pd.DataFrame()
    df.columns = normalize_cols(df.columns)

    if "last_updated" not in df.columns:
        df["last_updated"] = datetime.utcnow().isoformat(timespec='seconds')

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("articulos", conn, if_exists="replace", index=False)
    conn.close()
    return {"ok": True, "rows": len(df)}

def push_sqlite_to_sheet(sheet_id: str = None, sheet_name: str = None):
    sheet_id = sheet_id or SHEET_ID
    sheet_name = sheet_name or SHEET_NAME
    if not sheet_id:
        raise ValueError("SHEET_ID no configurado. Define GS_SHEET_ID env var.")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM articulos", conn)
    conn.close()

    client = get_gspread_client()
    sh = client.open_by_key(sheet_id)
    try:
        worksheet = sh.worksheet(sheet_name)
        worksheet.clear()
    except Exception:
        worksheet = sh.add_worksheet(title=sheet_name, rows="1000", cols="20")

    headers = list(df.columns)
    values = [headers] + df.fillna("").astype(str).values.tolist()
    worksheet.update(values)
    return {"ok": True, "rows": len(df)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["pull","push"])
    parser.add_argument("--sheet-id", default=None)
    parser.add_argument("--sheet-name", default=None)
    args = parser.parse_args()
    if args.action == "pull":
        print(pull_sheet_to_sqlite(sheet_id=args.sheet_id, sheet_name=args.sheet_name))
    else:
        print(push_sqlite_to_sheet(sheet_id=args.sheet_id, sheet_name=args.sheet_name))
EOF
