"""Hash existing protected research assets; verification never writes those assets."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = [
    "app",
    "demos",
    "experiments/epistemic-diversity",
    "pyproject.toml",
    "uv.lock",
    ".DS_Store",
    "experiments/.DS_Store",
]


def file_hash(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def snapshot() -> dict[str, Any]:
    paths: set[Path] = set()
    for name in PROTECTED:
        root = ROOT / name
        paths.update(
            p
            for p in (root.rglob("*") if root.is_dir() else [root])
            if p.is_file()
            and not {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} & set(p.parts)
        )
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "algorithm": "sha256",
        "files": {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(paths)},
    }


def compare(before: dict[str, Any]) -> dict[str, Any]:
    changes = []
    for name, expected in before["files"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Manifest path escapes repository")
        actual = file_hash(path) if path.is_file() else None
        if actual != expected:
            changes.append({"path": name, "before": expected, "after": actual})
    return {
        "checked_files": len(before["files"]),
        "passed": not changes,
        "changes": changes,
        "new_files": "Excluded from comparison, as requested",
    }


def write_new(path: Path, data: dict[str, Any]) -> None:
    path = path.resolve()
    if any(path.is_relative_to((ROOT / p).resolve()) for p in PROTECTED):
        raise ValueError("Audit output must be outside protected paths")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["snapshot", "verify"])
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        data = snapshot()
    else:
        if args.baseline is None:
            parser.error("verify requires --baseline")
        data = compare(json.loads(args.baseline.read_text(encoding="utf-8")))
    write_new(args.output, data)
    print(
        json.dumps(
            {
                "path": str(args.output),
                "files": len(data.get("files", {})),
                "passed": data.get("passed"),
                "checked_files": data.get("checked_files"),
            }
        )
    )
    if data.get("passed") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
