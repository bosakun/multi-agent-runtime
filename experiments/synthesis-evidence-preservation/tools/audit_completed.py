"""Independent read-only ledger/export/resource audit; no model generation."""

import json
import sqlite3
import statistics
import sys
from contextlib import closing
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[1]
sys.path[:0] = [
    str(STUDY / "src"),
    str(REPO),
    str(REPO / "experiments/epistemic-diversity"),
    str(REPO / "experiments/epistemic-diversity/src"),
]
from external_benchmarks.models import PrivateGold  # noqa: E402
from external_benchmarks.scoring import score  # noqa: E402
from synthesis_study.io import digest, exclusive, file_hash, read  # noqa: E402
from synthesis_study.runner import verify_seal  # noqa: E402

campaign = STUDY / "runs/real-fixed-workers-20260930"
report_root = STUDY / "reports/real-fixed-workers-20260930"
manifest = read(STUDY / "data/replay-inputs/manifest.json")
result = read(campaign / "results.json")
analysis = read(report_root / "analysis.json")
verify_seal()
assert result["status"] == "completed" and result["provider"] == "real"
assert len(result["records"]) == result["reservations"] == 81
expected = [(p["phase"], p["qid"], p["arm"]) for p in manifest["calls"]]
actual = [(r["phase"], r["qid"], r["arm"]) for r in result["records"]]
assert actual == expected
with closing(
    sqlite3.connect(f"file:{(campaign / 'budget.sqlite').as_posix()}?mode=ro", uri=True)
) as db:
    rows = db.execute("SELECT number,phase,qid,arm FROM calls ORDER BY number").fetchall()
assert rows == [(number, *cell) for number, cell in enumerate(expected, 1)]
with closing(
    sqlite3.connect(f"file:{(campaign / 'replay.sqlite').as_posix()}?mode=ro", uri=True)
) as db:
    events = db.execute("SELECT type,payload FROM events ORDER BY seq").fetchall()
assert len(events) == 162
for number, (record, planned) in enumerate(
    zip(result["records"], manifest["calls"], strict=True), 1
):
    assert record["number"] == number and record["status"] == "succeeded"
    assert (
        record["request"] == planned["body"] and digest(record["request"]) == planned["body_sha256"]
    )
    reserved, succeeded = events[(number - 1) * 2 : number * 2]
    assert reserved[0] == "reserved" and succeeded[0] == "succeeded"
    assert json.loads(reserved[1]) == {
        "number": number,
        "phase": planned["phase"],
        "qid": planned["qid"],
        "arm": planned["arm"],
        "body_sha256": planned["body_sha256"],
    }
    assert json.loads(succeeded[1]) == {"number": number, "status": "succeeded"}
    assert record["input_tokens"] == planned["prompt_tokens"] <= 4096
    assert 0 < record["output_tokens"] <= 4096
    models = record["residency"]["models"]
    assert (
        len(models) == 1 and models[0]["digest"] == manifest["spec"]["generation"]["model_digest"]
    )
    assert models[0]["context_length"] == 8192 and models[0]["size_vram"] > 0

gold = [
    PrivateGold.model_validate(
        read(REPO / manifest["spec"]["private_evaluation_root"] / (qid + ".json"))
    )
    for qid in manifest["spec"]["main_question_ids"]
]
for arm in manifest["spec"]["arms"]:
    recomputed = score(read(report_root / ("predictions-" + arm + ".json")), gold)
    assert recomputed == analysis["conditions"][arm]

resources = {}
for arm in manifest["spec"]["arms"]:
    main = [r for r in result["records"] if r["phase"] == "main" and r["arm"] == arm]
    resources[arm] = {
        "calls": len(main),
        "mean_input_tokens": statistics.mean(r["input_tokens"] for r in main),
        "mean_output_tokens": statistics.mean(r["output_tokens"] for r in main),
        "mean_latency_seconds": statistics.mean(r["latency_seconds"] for r in main),
        "total_input_tokens": sum(r["input_tokens"] for r in main),
        "total_output_tokens": sum(r["output_tokens"] for r in main),
    }
public_review = list((report_root / "review/public").glob("*.json"))
assert len(public_review) == 72
assert len(list((STUDY / "reports/review/public-source").glob("*.md"))) == 30
audit = {
    "passed": True,
    "ledger_cells_exact": True,
    "events_exact": True,
    "native_input_counts_exact": True,
    "gpu_residency_all_81": True,
    "loaded_context_all_81": 8192,
    "official_exports_recomputed": True,
    "source_preserved": result["source_preservation"],
    "new_worker_calls": result["new_worker_calls"],
    "public_review_cases": len(public_review),
    "independent_review": "pending",
    "full_research_completed": False,
    "resources": resources,
    "input_manifest_sha256": file_hash(STUDY / "data/replay-inputs/manifest.json"),
    "results_sha256": file_hash(campaign / "results.json"),
    "analysis_sha256": file_hash(report_root / "analysis.json"),
}
exclusive(report_root / "independent-execution-audit.json", audit)
print(json.dumps(audit, indent=2))
