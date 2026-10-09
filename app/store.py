"""Idempotency store: each event_id is processed once. Status: pending -> done | failed."""
import sqlite3
import threading
from pathlib import Path


class EventStore:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.c = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.c.execute("CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY, status TEXT, attempts INT DEFAULT 0,"
                       " error TEXT, received_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        self.c.commit()

    def claim(self, event_id: str) -> str:
        """Returns 'new' if we should process it, otherwise the existing status ('done'/'pending')."""
        with self.lock:
            row = self.c.execute("SELECT status FROM events WHERE event_id=?", (event_id,)).fetchone()
            if row is None:
                self.c.execute("INSERT INTO events(event_id,status) VALUES(?, 'pending')", (event_id,)); self.c.commit()
                return "new"
            if row[0] == "failed":  # allow sender's retry after our failure
                self.c.execute("UPDATE events SET status='pending' WHERE event_id=?", (event_id,)); self.c.commit()
                return "new"
            return row[0]

    def finish(self, event_id, status, attempts, error=None):
        with self.lock:
            self.c.execute("UPDATE events SET status=?, attempts=attempts+?, error=? WHERE event_id=?",
                           (status, attempts, error, event_id)); self.c.commit()

    def stats(self):
        with self.lock:
            return dict(self.c.execute("SELECT status, COUNT(*) FROM events GROUP BY status").fetchall())
