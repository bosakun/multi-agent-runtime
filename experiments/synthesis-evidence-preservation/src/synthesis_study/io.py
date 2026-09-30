"""Read-only source helpers and exclusive, append-only output publication."""

import hashlib
import json
import os
import sqlite3
import sys
import threading
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STUDY = Path(__file__).resolve().parents[2]
REPO = STUDY.parents[1]


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def exclusive(path: Path, value: Any, *, text: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{uuid.uuid4().hex}.tmp"
    operation = "create"
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            operation = "write"
            handle.write(value if text else json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            operation = "fsync"
            os.fsync(handle.fileno())
            operation = "close"
        operation = "publish"
        os.link(temporary, path)
    except OSError as exc:
        details = {
            "time": datetime.now(UTC).isoformat(),
            "pid": os.getpid(),
            "thread_id": threading.get_ident(),
            "operation": operation,
            "path": path.resolve().relative_to(REPO).as_posix()
            if path.resolve().is_relative_to(REPO)
            else "external-test-temp",
            "errno": exc.errno,
            "winerror": getattr(exc, "winerror", None),
            "error_type": type(exc).__name__,
            "payload_stored": False,
        }
        diagnostic = STUDY / "reports/storage-diagnostics" / f"{uuid.uuid4().hex}.json"
        try:
            diagnostic.parent.mkdir(parents=True, exist_ok=True)
            with diagnostic.open("x", encoding="utf-8") as report:
                json.dump(details, report)
        except OSError:
            pass
        print(json.dumps(details), file=sys.stderr, flush=True)
        raise
    finally:
        # Publication is complete before cleanup. A third-party sharing lock on
        # our temporary hard link must not invalidate a durable result, nor mask
        # the original publication error. Retain that link; never retry writes.
        try:
            temporary.unlink(missing_ok=True)
        except OSError as cleanup_error:
            details = {
                "time": datetime.now(UTC).isoformat(),
                "pid": os.getpid(),
                "thread_id": threading.get_ident(),
                "operation": "cleanup_own_temporary_link",
                "errno": cleanup_error.errno,
                "winerror": getattr(cleanup_error, "winerror", None),
                "temporary_retained": True,
                "canonical_path_exists": path.exists(),
                "payload_stored": False,
            }
            diagnostic = STUDY / "reports/storage-diagnostics" / f"{uuid.uuid4().hex}.json"
            try:
                diagnostic.parent.mkdir(parents=True, exist_ok=True)
                with diagnostic.open("x", encoding="utf-8") as report:
                    json.dump(details, report)
            except OSError:
                pass
            print(json.dumps(details), file=sys.stderr, flush=True)


def snapshot(root: Path, value: Any) -> None:
    exclusive(root / f"{uuid.uuid4().hex}.json", value)


class Budget:
    def __init__(self, path: Path, limit: int = 81):
        if path.exists() or limit < 1:
            raise ValueError("Require a fresh positive-limit reservation ledger")
        self.path, self.limit = path, limit
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute(
                "CREATE TABLE calls (number INTEGER PRIMARY KEY, phase TEXT, qid TEXT, arm TEXT)"
            )

    @property
    def used(self) -> int:
        with closing(sqlite3.connect(self.path)) as db:
            return int(db.execute("SELECT COUNT(*) FROM calls").fetchone()[0])

    def reserve(self, phase: str, qid: str, arm: str) -> int:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            used = int(db.execute("SELECT COUNT(*) FROM calls").fetchone()[0])
            smoke = int(db.execute("SELECT COUNT(*) FROM calls WHERE phase='smoke'").fetchone()[0])
            if used >= self.limit or (phase == "smoke" and smoke >= 9):
                raise ValueError("Reservation budget exhausted")
            number = used + 1
            db.execute("INSERT INTO calls VALUES (?, ?, ?, ?)", (number, phase, qid, arm))
            return number
