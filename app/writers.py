"""Pluggable sheet writers. All implement append(row)."""
import csv
import os
import threading
from pathlib import Path
from typing import Protocol

from .models import HEADER


class SheetWriter(Protocol):
    def append(self, row: list[str]) -> None: ...


class CsvWriter:
    """Local stand-in for Google Sheets (demo / tests)."""
    def __init__(self, path: str):
        self.path = Path(path); self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row):
        with self.lock:
            new = not self.path.exists()
            with open(self.path, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new: w.writerow(HEADER)
                w.writerow(row)


class GspreadWriter:
    """Real Google Sheets writer (service account). Share the sheet with the service-account email."""
    def __init__(self, sheet_id: str, worksheet: str, creds_file: str):
        import gspread
        gc = gspread.service_account(filename=creds_file)
        sh = gc.open_by_key(sheet_id)
        try:
            self.ws = sh.worksheet(worksheet)
        except gspread.WorksheetNotFound:
            self.ws = sh.add_worksheet(worksheet, rows=1000, cols=len(HEADER)); self.ws.append_row(HEADER)

    def append(self, row):
        self.ws.append_row(row, value_input_option="USER_ENTERED")


class MemoryWriter:
    """Test double; can be told to fail N times to exercise retries."""
    def __init__(self, fail_times: int = 0):
        self.rows, self.fail_times = [], fail_times

    def append(self, row):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionError("simulated Sheets API outage")
        self.rows.append(row)


def make_writer(s) -> SheetWriter:
    if s.writer == "gspread":
        return GspreadWriter(s.gsheet_id, s.gsheet_worksheet, s.google_creds)
    return CsvWriter(s.csv_path)
