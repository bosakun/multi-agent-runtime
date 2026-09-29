"""Verify original content seals with portable path keys, never reseal history."""

import hashlib
import json
from pathlib import Path
from typing import Any

from epistemic.benchmark_v2 import PILOT_IDS, SEED
from epistemic.freeze import FREEZE_PATH, frozen_files
from epistemic.paths import REPO, ROOT, digest


def verify_historical() -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    content = {k: v for k, v in payload.items() if k != "freeze_sha256"}
    actual = {Path(k).as_posix(): v for k, v in frozen_files().items()}
    expected = {Path(k).as_posix(): v for k, v in payload["files"].items()}
    changed = [name for name in expected if actual.get(name) != expected[name]]
    added = [name for name in actual if name not in expected]
    if digest(content) != payload["freeze_sha256"] or changed or added:
        raise ValueError(f"Historical freeze mismatch: changed={changed}, added={added}")
    if (
        payload["protocol_version"] != "pilot-2.3"
        or payload["benchmark_version"] != "2.0.0"
        or payload["task_ids"] != PILOT_IDS
        or payload["conditions"] != ["C2", "C3"]
        or payload["seed"] != SEED
        or payload["repetitions"] != 1
        or payload["planned_calls"] != 48
    ):
        raise ValueError("Historical protocol controls differ")
    return payload


def sources() -> dict[str, str]:
    base = verify_historical()
    paths = {REPO / name for name in base["files"]}
    paths.update((ROOT / "prospective_pilot").glob("*.py"))
    paths.update((ROOT / "operational_diagnostics").glob("*.py"))
    paths.update((ROOT / "operational_recovery").glob("*.py"))
    paths.update((ROOT / "host_support").glob("*.py"))
    paths.update(
        [
            ROOT / "pilot25.py",
            ROOT / "operational_recovery/pilot24.py",
            ROOT / "operational_recovery/observer.py",
            ROOT / "docs/protocol-2.5-amendment.md",
            ROOT / "tests/test_pilot25.py",
            FREEZE_PATH,
        ]
    )
    return {
        path.relative_to(REPO).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }
