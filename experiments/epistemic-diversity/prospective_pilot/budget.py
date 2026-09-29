"""Fresh Protocol 2.5 budget with explicit SQLite connection closure on Windows."""

import sqlite3
from contextlib import closing
from pathlib import Path

from epistemic.provider import BudgetExceeded, CallBudget


class ClosedCallBudget(CallBudget):
    def __init__(self, path: Path, limit: int) -> None:
        if limit < 1:
            raise ValueError("Call limit must be positive")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.limit = limit
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY, used INTEGER)")
            db.execute("INSERT OR IGNORE INTO budget VALUES (1, 0)")

    @property
    def used(self) -> int:
        with closing(sqlite3.connect(self.path)) as db:
            return int(db.execute("SELECT used FROM budget WHERE id=1").fetchone()[0])

    def reserve(self) -> None:
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            used = int(db.execute("SELECT used FROM budget WHERE id=1").fetchone()[0])
            if used >= self.limit:
                raise BudgetExceeded("Model-call budget exhausted")
            db.execute("UPDATE budget SET used=used+1 WHERE id=1")
