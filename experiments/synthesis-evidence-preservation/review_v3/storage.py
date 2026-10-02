"""Canonical hashes and exclusive, append-only local records. No Git operations."""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(UTC).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def exclusive(path, value):
    path = Path(path)
    ensure_local_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical(value) + "\n")
    return file_hash(path)


def ensure_local_output(path):
    path = Path(path).resolve()
    namespace = Path(__file__).resolve().parent
    repo = namespace.parents[2]
    if path.is_relative_to(repo) and not any(
        path.is_relative_to(namespace / folder)
        for folder in ("local", "packets", "exports", "sessions")
    ):
        raise ValueError(
            "Outputs must stay in ignored v3 local namespaces; historical assets protected"
        )


def safe_id(value):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", value):
        raise ValueError("Unsafe record identifier")
    return value


class ReviewStore:
    """Coordinator-local store; reviewer export never contains the other raw ballot.

    Not an OS security sandbox. Coordinator must use separate per-reviewer exports
    and filesystem permissions; sharing this author store defeats blinding.
    """

    AREAS = {
        "registry_reviewer1_raw",
        "registry_reviewer2_raw",
        "stage_labels_reviewer1",
        "stage_labels_reviewer2",
        "pre_adjudication_agreement",
        "adjudication_log",
        "final_adjudicated_labels",
        "post_freeze_candidate",
        "workflow",
        "packets",
    }

    def __init__(self, root):
        self.root = Path(root).resolve()

    def append(self, area, unit_id, version, value):
        if area not in self.AREAS:
            raise ValueError("Unknown independent/versioned area")
        target = self.root / area / safe_id(unit_id) / (safe_id(version) + ".json")
        return exclusive(target, value)

    def load(self, area, unit_id, version):
        if area not in self.AREAS:
            raise ValueError("Unknown area")
        return read(self.root / area / safe_id(unit_id) / (safe_id(version) + ".json"))


def snapshot(root, paths):
    root = Path(root).resolve()
    result = {}
    for relative in paths:
        target = (root / relative).resolve()
        target.relative_to(root)
        if not target.is_file():
            raise ValueError(f"Missing preservation target: {relative}")
        result[relative] = file_hash(target)
    return result


def verify_snapshot(root, expected):
    root = Path(root).resolve()
    changed, missing = [], []
    for relative, expected_hash in expected.items():
        target = (root / relative).resolve()
        target.relative_to(root)
        if not target.is_file():
            missing.append(relative)
        elif file_hash(target) != expected_hash.lower():
            changed.append(relative)
    return {
        "checked_files": len(expected),
        "changed": changed,
        "missing": missing,
        "passed": not changed and not missing,
    }
