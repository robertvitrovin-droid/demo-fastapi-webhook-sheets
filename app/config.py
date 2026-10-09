import os
from dataclasses import dataclass


@dataclass
class Settings:
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "dev-secret-change-me")
    writer: str = os.getenv("SHEETS_WRITER", "csv")          # csv | gspread
    csv_path: str = os.getenv("CSV_PATH", "data/sheet.csv")
    db_path: str = os.getenv("IDEMPOTENCY_DB", "data/events.sqlite3")
    gsheet_id: str = os.getenv("GSHEET_ID", "")
    gsheet_worksheet: str = os.getenv("GSHEET_WORKSHEET", "Orders")
    google_creds: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    max_skew_s: int = int(os.getenv("MAX_TIMESTAMP_SKEW", "300"))
    retries: int = int(os.getenv("WRITE_RETRIES", "4"))
