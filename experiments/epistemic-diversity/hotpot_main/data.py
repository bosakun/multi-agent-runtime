"""The same public ranking, first thirty; no outcome- or gold-based selection."""

import json
from pathlib import Path
from typing import Any

from epistemic.paths import ROOT
from external_benchmarks.dataset import SEED, private_gold, select
from external_benchmarks.provenance import (
    BUNDLE as PILOT_BUNDLE,
)
from external_benchmarks.provenance import (
    DATA,
    SCORER_COMMIT,
    SCORER_SHA256,
    file_sha256,
    verify_bundle,
)
from external_benchmarks.provenance import (
    sources as pilot_sources,
)
from operational_diagnostics.budget_experiment import exclusive
from operational_recovery.pilot24 import signed

BUNDLE = DATA / "prepared-thirty"


def sources() -> dict[str, str]:
    result = pilot_sources()
    paths = (
        list((ROOT / "hotpot_main").glob("*.py"))
        + [
            ROOT / "hotpot_full.py",
            ROOT / "ACTIVE_EXPERIMENT.md",
            ROOT / "docs/protocol-3.1-hotpotqa-main.md",
            ROOT / "tests/test_hotpot_main.py",
            ROOT / "hotpot_report.py",
            ROOT / "tests/test_hotpot_report.py",
        ]
        + list((ROOT / "hotpot_reporting").glob("*.py"))
    )
    result.update({p.relative_to(ROOT.parents[1]).as_posix(): file_sha256(p) for p in paths})
    return result


def prepare() -> Path:
    if BUNDLE.exists():
        raise ValueError("Thirty-question bundle exists; no overwrite/reselection")
    base = verify_bundle(PILOT_BUNDLE)
    raw = DATA / "hotpot_dev_distractor_v1.json"
    if file_sha256(raw) != base["raw_sha256"]:
        raise ValueError("Corpus drift from Pilot")
    rows: list[dict[str, Any]] = json.loads(raw.read_text(encoding="utf-8"))
    questions, selection = select(rows, count=30)
    if [q.id for q in questions[:6]] != base["task_ids"]:
        raise ValueError("The same public ranking must retain the Pilot prefix")
    originals = {row["_id"]: row for row in rows}
    gold = [private_gold(originals[q.id], q) for q in questions]
    BUNDLE.mkdir(parents=True, exist_ok=False)
    for question, annotation in zip(questions, gold, strict=True):
        exclusive(BUNDLE / "public" / f"{question.id}.json", question.model_dump(mode="json"))
        exclusive(BUNDLE / "gold" / f"{annotation.id}.json", annotation.model_dump(mode="json"))
    files = {p.relative_to(BUNDLE).as_posix(): file_sha256(p) for p in BUNDLE.rglob("*.json")}
    if any(files.get(name) != checksum for name, checksum in base["files"].items()):
        raise ValueError("Pilot public/gold bytes must remain identical")
    exclusive(
        BUNDLE / "manifest.json",
        signed(
            {
                **{
                    k: base[k]
                    for k in (
                        "benchmark",
                        "setting",
                        "split",
                        "source_url",
                        "original_source",
                        "download_provenance",
                        "raw_sha256",
                        "license",
                    )
                },
                "selection_seed": SEED,
                "selection": selection,
                "selection_rule": (
                    "same public <=12000-char eligibility and hash ranking; first thirty"
                ),
                "task_ids": [q.id for q in questions],
                "files": files,
                "pilot_task_ids": base["task_ids"],
                "pilot_dataset_sha256": base["sha256"],
                "scorer_commit": SCORER_COMMIT,
                "scorer_sha256": SCORER_SHA256,
            }
        ),
    )
    return BUNDLE / "manifest.json"
