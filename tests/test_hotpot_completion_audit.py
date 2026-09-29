"""Completion audit rejects incomplete grids and DB traces, without model requests."""

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_hotpot_completion import database_check, grid_check


def grid():
    ids = [f"question{i}" for i in range(30)]
    records = [
        {
            "question_id": qid,
            "condition": condition,
            "calls": 1 if condition == "C0" else 4,
            "status": "succeeded",
            "errors": [],
            "audit": {"violation": 0},
        }
        for qid in ids
        for condition in ["C0", "C1", "C2", "C3", "C4"]
    ]
    return ids, records


def test_complete_grid_includes_all150_cases_and_510_calls():
    ids, records = grid()
    grid_check(records, ids)
    with pytest.raises(ValueError, match="incomplete"):
        grid_check(records[:-1], ids)


@pytest.mark.parametrize("change", ["duplicate", "extra_call", "failed", "access_fault"])
def test_incomplete_or_invalid_grid_is_not_completion(change):
    ids, records = grid()
    if change == "duplicate":
        records[-1] = records[0]
    elif change == "extra_call":
        records[0]["calls"] = 2
    elif change == "failed":
        records[0]["status"] = "failed"
    else:
        records[0]["audit"]["violation"] = 1
    with pytest.raises(ValueError):
        grid_check(records, ids)


def test_database_completion_requires_successful_agents_and_contiguous_event_trace(tmp_path):
    path = tmp_path / "runtime.sqlite"
    payload = {
        "status": "succeeded",
        "event_count": 2,
        "state": {"agent_runs": [{"status": "succeeded", "result": {"error": None}}]},
    }
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE runs (id TEXT, payload TEXT)")
        db.execute("CREATE TABLE events (run_id TEXT, sequence INTEGER)")
        db.execute("INSERT INTO runs VALUES (?,?)", ("run1", json.dumps(payload)))
        db.executemany("INSERT INTO events VALUES (?,?)", [("run1", 1), ("run1", 2)])
    records = [{"run_id": "run1", "calls": 1}]
    database_check(path, records)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("DELETE FROM events WHERE sequence=2")
    with pytest.raises(ValueError, match="trace"):
        database_check(path, records)
