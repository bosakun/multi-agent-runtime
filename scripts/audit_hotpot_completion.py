"""Read-only completion audit; only a new report is written, never models or old assets."""

import argparse
import csv
import json
import sqlite3
import statistics
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

REPO = Path(__file__).resolve().parents[1]
RESEARCH = REPO / "experiments/epistemic-diversity"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(RESEARCH / "src"))
sys.path.insert(0, str(RESEARCH))

import audit_preservation  # noqa: E402
from epistemic.analysis import COMPARISONS, holm, paired_inference  # noqa: E402
from external_benchmarks import runner as pilot  # noqa: E402
from external_benchmarks.dataset import private_gold, public_question, select  # noqa: E402
from external_benchmarks.provenance import DATA, file_sha256  # noqa: E402
from external_benchmarks.scoring import score, upstream  # noqa: E402
from hotpot_main import runner  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def grid_check(records: list[dict[str, Any]], ids: list[str]) -> None:
    expected = {(qid, c) for qid in ids for c in ["C0", "C1", "C2", "C3", "C4"]}
    actual = {(r["question_id"], r["condition"]) for r in records}
    require(len(ids) == len(set(ids)) == 30, "Not thirty distinct questions")
    require(len(records) == len(actual) == 150 and actual == expected, "Grid incomplete/duplicate")
    require(sum(r["calls"] for r in records) == 510, "Record calls are not 510")
    require(
        all(
            r["status"] == "succeeded" and not r["errors"] and not any(r["audit"].values())
            for r in records
        ),
        "Failed/access-invalid case",
    )


def database_check(path: Path, records: list[dict[str, Any]]) -> None:
    indexed = {r["run_id"]: r for r in records}
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        rows = db.execute("SELECT id,payload FROM runs").fetchall()
        require({row[0] for row in rows} == set(indexed), "Runtime database run inventory mismatch")
        for run_id, payload in rows:
            run = json.loads(payload)
            require(run["status"] == "succeeded", "Runtime DB has unsuccessful run")
            events = db.execute(
                "SELECT sequence FROM events WHERE run_id=? ORDER BY sequence", (run_id,)
            ).fetchall()
            require(
                [row[0] for row in events] == list(range(1, run["event_count"] + 1)),
                "Incomplete event trace",
            )
            agents = run["state"]["agent_runs"]
            require(
                len(agents) == indexed[run_id]["calls"], "Unexpected attempts/retries in runtime"
            )
            require(
                all(
                    a["status"] == "succeeded" and a["result"] and not a["result"]["error"]
                    for a in agents
                ),
                "Bad agent result",
            )


def audit(*, mock: bool) -> dict[str, Any]:
    manifest = runner.verify_data()
    if not mock:
        pilot.verify_binding()
        runner.verify_binding()
    base_path, base = runner.base_gate(mock)
    additional = (
        runner.MOCK / "results.json" if mock else runner.CAMPAIGN / "additional/results.json"
    )
    data = load(additional)
    require(
        runner.integral(data, manifest) and bool(data["metadata"].get("finished_at")),
        "Additional phase unfinished",
    )
    require(data["metadata"]["fingerprint"] == runner.fingerprint(mock), "Executed source drift")
    ledger = runner.MOCK / "budget.sqlite" if mock else runner.CAMPAIGN / "budget.sqlite"
    require(runner.ledger_used(ledger) == 456, "Additional ledger is not 456")
    analysis_dir = (
        REPO / "reports/hotpotqa-main-mock-analysis" if mock else runner.CAMPAIGN / "analysis"
    )
    analysis = load(analysis_dir / "analysis.json")
    require(analysis["source_files"] == runner.sources(), "Analysis source inventory drift")
    require(analysis["analysis_controls"] == runner.controls(), "Analysis controls drift")
    cumulative = load(analysis_dir / "cumulative-results.json")
    records = base["records"] + data["records"]
    grid_check(records, manifest["task_ids"])
    require(cumulative["records"] == records, "Cumulative records differ from immutable phases")
    database_check(base_path.parent / "runtime.sqlite", base["records"])
    database_check(additional.parent / "runtime.sqlite", data["records"])

    raw = DATA / "hotpot_dev_distractor_v1.json"
    require(file_sha256(raw) == manifest["raw_sha256"], "Raw corpus checksum drift")
    rows = load(raw)
    selected, counts = select(rows, count=30)
    require(
        [q.id for q in selected] == manifest["task_ids"] and counts == manifest["selection"],
        "Public ranking changed",
    )
    original = {row["_id"]: row for row in rows}
    gold = {}
    for qid in manifest["task_ids"]:
        public = public_question(original[qid])
        annotation = private_gold(original[qid], public)
        require(
            load(runner.BUNDLE / "public" / f"{qid}.json") == public.model_dump(mode="json"),
            "Original public text changed",
        )
        require(
            load(runner.BUNDLE / "gold" / f"{qid}.json") == annotation.model_dump(mode="json"),
            "Original gold changed",
        )
        gold[qid] = annotation
    upstream()  # Verifies the pinned byte-identical scorer before invoking it.
    indexed = {(r["question_id"], r["condition"]): r for r in records}
    for label, ids in (
        ("cumulative30_exploratory", manifest["task_ids"]),
        ("fresh24_prospective", manifest["task_ids"][6:]),
    ):
        for condition in ["C0", "C1", "C2", "C3", "C4"]:
            predictions: dict[str, Any] = {"answer": {}, "sp": {}}
            for qid in ids:
                for key in predictions:
                    predictions[key].update(indexed[qid, condition]["predictions"][key])
            require(
                load(analysis_dir / f"predictions-{label}-{condition}.json") == predictions,
                "Official export mismatch",
            )
            require(
                analysis["summaries"][label][condition]
                == score(predictions, [gold[qid] for qid in ids]),
                "Official condition score mismatch",
            )
    secondary = []
    for name, a, b in COMPARISONS:
        differences = [
            indexed[qid, a]["metrics"]["f1"] - indexed[qid, b]["metrics"]["f1"]
            for qid in manifest["task_ids"][6:]
        ]
        expected = paired_inference(differences, seed=20260928)
        actual = analysis["fresh24_comparisons"][name]
        require(
            all(actual[k] == v for k, v in expected.items()), "Fresh24 paired inference mismatch"
        )
        require(actual["contrast"] == f"{a}-{b}", "Comparison label mismatch")
        if name != "P1":
            secondary.append(actual["p"])
    for name, adjusted in zip(["P2", "P3", "P4", "P5"], holm(secondary), strict=True):
        require(
            analysis["fresh24_comparisons"][name]["holm_secondary_p"] == adjusted,
            "Secondary Holm family mismatch",
        )
    interaction = [
        (indexed[qid, "C4"]["metrics"]["f1"] - indexed[qid, "C3"]["metrics"]["f1"])
        - (indexed[qid, "C2"]["metrics"]["f1"] - indexed[qid, "C1"]["metrics"]["f1"])
        for qid in manifest["task_ids"][6:]
    ]

    diagnostic = analysis_dir / "descriptive"
    report = load(diagnostic / "report.json")
    require(
        len(report["records"]) == 150 and all(r["cost_usd"] is None for r in report["records"]),
        "Incomplete diagnostics/unknown pricing not null",
    )
    for path, checksum in report["input_hashes"].items():
        require(file_sha256(Path(path)) == checksum, "Reviewed input changed")
    csv_rows = list(
        csv.DictReader((diagnostic / "cases.csv").read_text(encoding="utf-8").splitlines())
    )
    require(
        {(r["question_id"], r["condition"]) for r in csv_rows} == set(indexed)
        and len(csv_rows) == 150,
        "CSV grid incomplete",
    )
    review = (diagnostic / "saved-output-review.md").read_text(encoding="utf-8")
    require(
        all(f"## {qid} / {condition}" in review for qid, condition in indexed),
        "Review missing cases",
    )
    figures = list(diagnostic.glob("*.svg"))
    require(len(figures) == 6, "Expected six figures")
    for figure in figures:
        content = " ".join(ElementTree.parse(figure).getroot().itertext())
        require(
            "n=30 per condition" in content
            and ("MOCK" in content if mock else "REAL HOTPOTQA" in content),
            "Figure provider/sample labels missing",
        )
    disagreements = [
        {
            "question_id": qid,
            "C2_EM": indexed[qid, "C2"]["metrics"]["em"],
            "C3_EM": indexed[qid, "C3"]["metrics"]["em"],
        }
        for qid in manifest["task_ids"]
        if indexed[qid, "C2"]["metrics"]["em"] != indexed[qid, "C3"]["metrics"]["em"]
    ]
    require(
        load(diagnostic / "discordant-C2-C3.json")["cases"] == disagreements,
        "Invented/missing disagreement case",
    )

    call_count = 0
    native_count = 0
    for result_path, phase in ((base_path, base), (additional, data)):
        all_journals = list((result_path.parent / "call-journal").rglob("*.json"))
        require(
            len(all_journals) == phase["metadata"]["model_calls"], "Orphan/missing call journal"
        )
        for record in phase["records"]:
            paths = list(
                (
                    result_path.parent
                    / "call-journal"
                    / record["question_id"]
                    / record["condition"]
                ).glob("*.json")
            )
            require(len(paths) == record["calls"], "Case call inventory mismatch")
            calls = [load(p) for p in paths]
            for key in ("input_tokens", "output_tokens", "model_calls"):
                require(
                    sum(c["response"]["usage"][key] for c in calls) == record["usage"][key],
                    "Token/call usage accounting mismatch",
                )
        call_count += len(all_journals)
        if not mock:
            observations = list((result_path.parent / "http-observations").glob("*.json"))
            require(len(observations) == len(all_journals), "Orphan/missing native observation")
            for path in observations:
                obs = load(path)
                require(
                    obs["done"] is True
                    and obs["finish_reason"] == "stop"
                    and obs["thinking_chars"] == 0,
                    "Native stop/thinking failure",
                )
            native_count += len(observations)
    require(call_count == 510 and (mock or native_count == 510), "All 510 calls not proven")
    preservation = audit_preservation.compare(
        load(REPO / "reports/hotpot-main-preservation-before.json")
    )
    require(preservation["passed"], "Historical preservation failed")
    return {
        "passed": True,
        "provider": "mock" if mock else "real",
        "scope": "30 questions x five conditions",
        "checked_at": datetime.now(UTC).isoformat(),
        "cases": 150,
        "calls": call_count,
        "native_observations": native_count,
        "runtime_databases": 2,
        "figures": 6,
        "primary_inference_questions": 24,
        "cumulative_questions": 30,
        "historical_preservation": preservation,
        "analysis_sha256": file_sha256(analysis_dir / "analysis.json"),
        "fresh24_descriptive_interaction": {
            "contrast": "(C4-C3)-(C2-C1) answer F1",
            "n_questions": 24,
            "mean_difference": statistics.mean(interaction),
            "task_differences": interaction,
            "inference": "descriptive only; not an additional significance test",
        },
        "audit_source_sha256": file_sha256(Path(__file__)),
        "limitations": (
            "Length-selected public dev subset; "
            "no independent human or contamination-free validation"
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(mock=args.mock)
    audit_preservation.write_new(args.output, report)
    print(json.dumps(report, ensure_ascii=False))
