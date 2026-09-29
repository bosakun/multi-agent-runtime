"""Independent completion audit including the retained failure and exact reuse provenance."""

import argparse
import csv
import json
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

REPO = Path(__file__).resolve().parents[1]
RESEARCH = REPO / "experiments/epistemic-diversity"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(RESEARCH / "src"))
sys.path.insert(0, str(RESEARCH))

import audit_preservation  # noqa: E402
from audit_hotpot_completion import database_check, grid_check, load, require  # noqa: E402
from epistemic.analysis import COMPARISONS, holm, paired_inference  # noqa: E402
from external_benchmarks import runner as pilot  # noqa: E402
from external_benchmarks.dataset import private_gold, public_question, select  # noqa: E402
from external_benchmarks.provenance import DATA, file_sha256  # noqa: E402
from external_benchmarks.scoring import score, upstream  # noqa: E402
from hotpot_main import runner as main  # noqa: E402
from hotpot_recovery import runner  # noqa: E402


def old_database_check(path: Path, records: list[dict[str, Any]]) -> None:
    indexed = {r["run_id"]: r for r in records}
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        rows = db.execute("SELECT id,payload FROM runs").fetchall()
        require({r[0] for r in rows} == set(indexed), "Prior DB run inventory drift")
        for run_id, payload in rows:
            run = json.loads(payload)
            record = indexed[run_id]
            require(run["status"] == record["status"], "Prior DB status drift")
            sequence = db.execute(
                "SELECT sequence FROM events WHERE run_id=? ORDER BY sequence", (run_id,)
            ).fetchall()
            require(
                [r[0] for r in sequence] == list(range(1, run["event_count"] + 1)),
                "Prior DB event gaps",
            )
            agents = run["state"]["agent_runs"]
            require(len(agents) == record["calls"], "Prior agent inventory mismatch")
            errors = [
                a["result"]["error"]["code"] for a in agents if a["result"] and a["result"]["error"]
            ]
            require(errors == record["errors"], "Prior error evidence mismatch")


def audit(*, mock: bool) -> dict[str, Any]:
    base, previous, manifest = runner.prior()
    if not mock:
        runner.verify_binding()
    target = runner.MOCK if mock else runner.CAMPAIGN / "recovery"
    data = load(target / "results.json")
    require(
        runner.integral(data)
        and data["metadata"]["operational_integrity"]
        and bool(data["metadata"]["finished_at"]),
        "Recovery unfinished",
    )
    require(data["metadata"]["fingerprint"] == runner.fingerprint(mock), "Recovery source drift")
    ledger = target / "budget.sqlite" if mock else runner.CAMPAIGN / "budget.sqlite"
    require(main.ledger_used(ledger) == 206, "Recovery reservation ledger is not 206")
    require(
        main.ledger_used(pilot.CAMPAIGN / "budget.sqlite") == 54
        and main.ledger_used(main.CAMPAIGN / "budget.sqlite") == 251,
        "Old reservation ledger drift",
    )
    analysis_dir = (
        runner.MOCK.parent / "hotpotqa-recovery-mock-analysis"
        if mock
        else runner.CAMPAIGN / "analysis"
    )
    analysis = load(analysis_dir / "analysis.json")
    cumulative = load(analysis_dir / "cumulative-results.json")
    records = (
        base["records"]
        + [r for r in previous["records"] if r["status"] == "succeeded"]
        + data["records"]
    )
    grid_check(records, manifest["task_ids"])
    require(cumulative["records"] == records, "Cumulative records are not exact source records")
    require(
        analysis["source_files"] == runner.sources()
        and analysis["analysis_controls"] == runner.controls(),
        "Analysis source/control drift",
    )
    require(
        cumulative["metadata"]["total_reservations"] == 511
        and cumulative["metadata"]["unsuccessful_pre_dispatch_reservations"] == 1,
        "Retained failure not accounted",
    )
    database_check(pilot.CAMPAIGN / "pilot/runtime.sqlite", base["records"])
    old_database_check(main.CAMPAIGN / "additional/runtime.sqlite", previous["records"])
    database_check(target / "runtime.sqlite", data["records"])
    recovered = next(r for r in data["records"] if r["reused_calls"])
    require(
        (recovered["question_id"], recovered["condition"]) == (runner.FAILED_QID, "C1")
        and recovered["new_calls"] == recovered["reused_calls"] == 2,
        "Unexpected reuse allocation",
    )
    old_run = runner.source_run()
    with closing(
        sqlite3.connect((target / "runtime.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    ) as db:
        run = json.loads(
            db.execute("SELECT payload FROM runs WHERE id=?", (recovered["run_id"],)).fetchone()[0]
        )
        events = [
            json.loads(row[0])
            for row in db.execute(
                "SELECT payload FROM events WHERE run_id=?", (recovered["run_id"],)
            )
        ]
    restoration = [event for event in events if event["kind"] == "IMMUTABLE_WORKERS_RESTORED"]
    require(
        len(restoration) == 1 and restoration[0]["data"]["source_run_id"] == old_run.id,
        "Missing restoration provenance event",
    )
    for attribute, key in [
        ("agent_runs", "agent_id"),
        ("artifacts", "producer"),
        ("messages", "sender"),
    ]:
        originals = [
            item.model_dump(mode="json")
            for item in getattr(old_run.state, attribute)
            if getattr(item, key) in runner.REUSED
        ]
        copies = [item for item in run["state"][attribute] if item[key] in runner.REUSED]
        require(copies == originals, "Reused state was changed")
    for receipt in recovered["reuse_provenance"]:
        require(
            file_sha256(Path(receipt["journal"]))
            == receipt["journal_sha256"]
            == file_sha256(Path(receipt["copy"])),
            "Reused journal bytes changed",
        )
        require(
            file_sha256(Path(receipt["observation"]))
            == file_sha256(Path(receipt["observation_copy"])),
            "Reused observation bytes changed",
        )
    synthesizer = next(
        load(p)
        for p in (target / "call-journal" / runner.FAILED_QID / "C1").glob("*.json")
        if load(p)["agent_id"] == "synthesizer"
    )
    context = synthesizer["request"]["context"]
    require(
        [a["producer"] for a in context["artifacts"]] == ["worker_0", "worker_1", "worker_2"],
        "Synthesis worker order changed",
    )
    require(
        not context["knowledge"] and not context["inputs"],
        "Recovered synthesizer sees raw/private data",
    )

    raw = DATA / "hotpot_dev_distractor_v1.json"
    require(file_sha256(raw) == manifest["raw_sha256"], "Raw corpus drift")
    rows = load(raw)
    selected, counts = select(rows, count=30)
    require(
        [q.id for q in selected] == manifest["task_ids"] and counts == manifest["selection"],
        "Public ranking drift",
    )
    original = {row["_id"]: row for row in rows}
    gold = {}
    for qid in manifest["task_ids"]:
        public = public_question(original[qid])
        annotation = private_gold(original[qid], public)
        require(
            load(main.BUNDLE / "public" / f"{qid}.json") == public.model_dump(mode="json"),
            "Public text drift",
        )
        require(
            load(main.BUNDLE / "gold" / f"{qid}.json") == annotation.model_dump(mode="json"),
            "Gold drift",
        )
        gold[qid] = annotation
    upstream()
    indexed = {(r["question_id"], r["condition"]): r for r in records}
    for r in records:
        require(
            r["metrics"] == score(r["predictions"], [gold[r["question_id"]]]),
            "Per-case official score mismatch",
        )
    for label, ids in [
        ("cumulative30_exploratory", manifest["task_ids"]),
        ("fresh24_prospective", manifest["task_ids"][6:]),
    ]:
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
                "Summary score mismatch",
            )
    secondary = []
    for name, a, b in COMPARISONS:
        expected = paired_inference(
            [
                indexed[qid, a]["metrics"]["f1"] - indexed[qid, b]["metrics"]["f1"]
                for qid in manifest["task_ids"][6:]
            ],
            seed=20260928,
        )
        actual = analysis["fresh24_comparisons"][name]
        require(
            all(actual[k] == v for k, v in expected.items()) and actual["contrast"] == f"{a}-{b}",
            "Fresh24 inference mismatch",
        )
        if name != "P1":
            secondary.append(actual["p"])
    for name, adjusted in zip(["P2", "P3", "P4", "P5"], holm(secondary), strict=True):
        require(
            analysis["fresh24_comparisons"][name]["holm_secondary_p"] == adjusted,
            "Holm family mismatch",
        )
    original_partial = next(r for r in previous["records"] if r["status"] == "partial")
    require(
        analysis["operational_recovery_sensitivity"]["original_failed_record"] == original_partial,
        "Original failure omitted/changed",
    )
    diagnostic = analysis_dir / "descriptive"
    report = load(diagnostic / "report.json")
    require(
        len(report["records"]) == 150 and all(r["cost_usd"] is None for r in report["records"]),
        "Diagnostic grid/cost invalid",
    )
    for path, checksum in report["input_hashes"].items():
        require(file_sha256(Path(path)) == checksum, "Reviewed source changed")
    csv_rows = list(
        csv.DictReader((diagnostic / "cases.csv").read_text(encoding="utf-8").splitlines())
    )
    require(
        len(csv_rows) == 150
        and {(r["question_id"], r["condition"]) for r in csv_rows} == set(indexed),
        "CSV incomplete",
    )
    review = (diagnostic / "saved-output-review.md").read_text(encoding="utf-8")
    require(all(f"## {qid} / {c}" in review for qid, c in indexed), "Saved review incomplete")
    figures = list(diagnostic.glob("*.svg"))
    require(len(figures) == 6, "Expected six figures")
    for figure in figures:
        content = " ".join(ElementTree.parse(figure).getroot().itertext())
        require(
            "n=30 per condition" in content
            and ("MOCK" in content if mock else "REAL HOTPOTQA" in content),
            "Figure scope/provider missing",
        )
    discordant = [
        {
            "question_id": qid,
            "C2_EM": indexed[qid, "C2"]["metrics"]["em"],
            "C3_EM": indexed[qid, "C3"]["metrics"]["em"],
        }
        for qid in manifest["task_ids"]
        if indexed[qid, "C2"]["metrics"]["em"] != indexed[qid, "C3"]["metrics"]["em"]
    ]
    require(
        load(diagnostic / "discordant-C2-C3.json")["cases"] == discordant,
        "Discordant case mismatch",
    )

    journal_count = 0
    for r in records:
        journal = Path(
            cumulative["metadata"]["journal_roots"][f"{r['question_id']}:{r['condition']}"]
        )
        calls = [load(p) for p in journal.glob("*.json")]
        require(
            len(calls) == r["calls"] and len({c["agent_id"] for c in calls}) == r["calls"],
            "Call inventory mismatch",
        )
        require(
            all(not c["error"] and c["response"] for c in calls),
            "Unsuccessful call in cumulative grid",
        )
        for key in ["input_tokens", "output_tokens", "model_calls"]:
            require(
                sum(c["response"]["usage"][key] for c in calls) == r["usage"][key], "Usage mismatch"
            )
        journal_count += len(calls)
    require(journal_count == 510, "Not 510 successful calls")
    new_calls = [
        load(p)
        for p in (target / "call-journal").rglob("*.json")
        if not p.name.startswith("reused_")
    ]
    require(len(new_calls) == 206, "New call count not 206")
    history = [load(p) for p in (target / "journal-history").glob("*.json")]
    for call in new_calls:
        require(call in history, "Canonical call lacks identical append-only final snapshot")
    require(
        len(list((target / "progress").glob("*.json"))) == 61, "Append-only progress incomplete"
    )
    native_count = 0
    if not mock:
        observations = (
            list((pilot.CAMPAIGN / "pilot/http-observations").glob("*.json"))
            + list((main.CAMPAIGN / "additional/http-observations").glob("*.json"))
            + [
                p
                for p in (target / "http-observations").glob("*.json")
                if not p.name.startswith(old_run.id)
            ]
        )
        require(
            len(observations) == 510 and len({p.name for p in observations}) == 510,
            "Native response inventory not 510 distinct calls",
        )
        for path in observations:
            obs = load(path)
            require(
                obs["done"] is True
                and obs["finish_reason"] == "stop"
                and obs["thinking_chars"] == 0
                and obs["input_tokens"] <= 4096
                and obs["generated_tokens"] <= 4096,
                "Native completion guard failure",
            )
        native_count = len(observations)
    preservation = audit_preservation.compare(
        load(REPO / "reports/hotpot-recovery-preservation-before.json")
    )
    require(preservation["passed"], "Original assets changed")
    return {
        "passed": True,
        "provider": "mock" if mock else "real",
        "checked_at": datetime.now(UTC).isoformat(),
        "scope": "30 questions x C0-C4; one repetition",
        "cases": 150,
        "successful_calls": 510,
        "reservations": 511,
        "new_reservations": 206,
        "retained_pre_dispatch_failures": 1,
        "reused_successful_cases": 89,
        "restored_workers": 2,
        "native_observations": native_count,
        "runtime_databases": 3,
        "figures": 6,
        "primary_inference_questions": 24,
        "historical_preservation": preservation,
        "analysis_sha256": file_sha256(analysis_dir / "analysis.json"),
        "audit_source_sha256": file_sha256(Path(__file__)),
        "mock_caveat": "Historical real prefix reused; new calls are Mock, not performance"
        if mock
        else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(mock=args.mock)
    audit_preservation.write_new(args.output, report)
    print(json.dumps(report, ensure_ascii=False))
