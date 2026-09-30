"""One-shot fixed-request replay with durable reservations and append-only events."""

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from external_benchmarks.models import FinalAnswer
from native_pilot.provider import parse_native

from synthesis_study.io import REPO, STUDY, Budget, digest, exclusive, file_hash, read, snapshot

ENDPOINT = "http://127.0.0.1:11434"


def now() -> str:
    return datetime.now(UTC).isoformat()


def citations(value: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_ids" and isinstance(child, list):
                ids.update(child)
            else:
                ids.update(citations(child))
    elif isinstance(value, list):
        for child in value:
            ids.update(citations(child))
    return ids


def source_preserved(manifest: dict[str, Any]) -> dict[str, Any]:
    changed = [
        p for p, expected in manifest["source_hashes"].items() if file_hash(REPO / p) != expected
    ]
    return {
        "passed": not changed,
        "checked_files": len(manifest["source_hashes"]),
        "changed": changed,
    }


def code_hashes() -> dict[str, str]:
    paths = [
        STUDY / "run.py",
        STUDY / "study.json",
        STUDY / "PLAN.md",
        STUDY / "REVIEW.md",
        STUDY / "OPERATIONS.md",
        STUDY / "requirements-research.txt",
        STUDY / "assets/length-control.txt",
    ]
    paths.extend(sorted((STUDY / "src").rglob("*.py")))
    paths.extend(sorted((STUDY / "tests").rglob("*.py")))
    paths.extend(sorted((STUDY / "scripts").glob("*.ps1")))
    paths.extend(sorted((REPO / "app").rglob("*.py")))
    for directory in [
        "external_benchmarks",
        "native_pilot",
        "bounded_pilot",
        "prospective_pilot",
        "hotpot_reporting",
        "src/epistemic",
    ]:
        paths.extend(sorted((REPO / "experiments/epistemic-diversity" / directory).rglob("*.py")))
    paths.extend([REPO / "pyproject.toml", REPO / "uv.lock"])
    # Include the exact repository modules reused for schemas/scoring/provider serialization.
    import sys

    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename and filename.endswith(".py"):
            path = Path(filename).resolve()
            if path.is_relative_to(REPO) and ".venv" not in path.parts:
                paths.append(path)
    return {p.relative_to(REPO).as_posix(): file_hash(p) for p in sorted(set(paths))}


def freeze(mock_campaign: Path) -> dict[str, Any]:
    manifest_path = STUDY / "data/replay-inputs/manifest.json"
    manifest = read(manifest_path)
    from synthesis_study.prepare import validate_manifest

    validate_manifest(manifest)
    result = read(mock_campaign / "results.json")
    if (
        result["provider"] != "mock"
        or result["status"] != "completed"
        or len(result["records"]) != 81
        or result["reservations"] != 81
    ):
        raise ValueError("Require complete 81-cell Mock")
    if (
        result["input_manifest_sha256"] != file_hash(manifest_path)
        or not source_preserved(manifest)["passed"]
    ):
        raise ValueError("Mock/source mismatch")
    audit_path = STUDY / "reports" / mock_campaign.name / "completion-audit.json"
    audit = read(audit_path)
    if audit.get("provider") != "mock" or not audit.get("passed_pipeline"):
        raise ValueError("Require independently analyzed Mock pipeline")
    validation_path = STUDY / "data/prelaunch-validation.json"
    validation = read(validation_path)
    if not validation["passed"] or validation["code_hashes"] != code_hashes():
        raise ValueError("Require passed validation of current implementation")
    seal = {
        "created_at": now(),
        "input_manifest_sha256": file_hash(manifest_path),
        "code_hashes": code_hashes(),
        "mock_campaign": mock_campaign.relative_to(REPO).as_posix(),
        "mock_results_sha256": file_hash(mock_campaign / "results.json"),
        "mock_audit_path": audit_path.relative_to(REPO).as_posix(),
        "mock_audit_sha256": file_hash(audit_path),
        "validation_sha256": file_hash(validation_path),
        "source_hashes": manifest["source_hashes"],
        "call_limit": 81,
    }
    exclusive(STUDY / "freezes/v1.json", seal)
    return seal


def verify_seal() -> dict[str, Any]:
    seal = read(STUDY / "freezes/v1.json")
    for relative, expected in {**seal["code_hashes"], **seal["source_hashes"]}.items():
        if file_hash(REPO / relative) != expected:
            raise ValueError("Frozen source changed: " + relative)
    if file_hash(STUDY / "data/replay-inputs/manifest.json") != seal["input_manifest_sha256"]:
        raise ValueError("Frozen inputs changed")
    if file_hash(REPO / seal["mock_campaign"] / "results.json") != seal["mock_results_sha256"]:
        raise ValueError("Mock evidence changed")
    if file_hash(REPO / seal["mock_audit_path"]) != seal["mock_audit_sha256"]:
        raise ValueError("Mock audit changed")
    if file_hash(STUDY / "data/prelaunch-validation.json") != seal["validation_sha256"]:
        raise ValueError("Validation evidence changed")
    return seal


def fingerprint(client: httpx.Client, spec: dict[str, Any]) -> dict[str, Any]:
    version = client.get("/api/version").raise_for_status().json()
    tags = client.get("/api/tags").raise_for_status().json()
    models = [m for m in tags["models"] if m["name"] == spec["generation"]["model"]]
    if (
        version["version"] != spec["generation"]["ollama_version"]
        or len(models) != 1
        or models[0]["digest"] != spec["generation"]["model_digest"]
    ):
        raise ValueError("Ollama/model identity drift")
    show = (
        client.post("/api/show", json={"model": spec["generation"]["model"]})
        .raise_for_status()
        .json()
    )
    from synthesis_study.tokenizer import TEMPLATE_DIGEST

    if hashlib.sha256(show["template"].encode()).hexdigest() != TEMPLATE_DIGEST:
        raise ValueError("Backend template drift")
    return {
        "checked_at": now(),
        "endpoint": ENDPOINT,
        "version": version,
        "model": models[0],
        "template_sha256": TEMPLATE_DIGEST,
        "details": show["details"],
        "residency": client.get("/api/ps").raise_for_status().json(),
    }


def bind() -> dict[str, Any]:
    verify_seal()
    spec = read(STUDY / "study.json")
    with httpx.Client(
        base_url=ENDPOINT, timeout=15, trust_env=False, follow_redirects=False
    ) as client:
        backend = fingerprint(client, spec)
    import platform
    import subprocess

    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    result = {
        "freeze_sha256": file_hash(STUDY / "freezes/v1.json"),
        "backend": backend,
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "python": platform.python_version(),
            "gpu": gpu,
        },
        "hard_call_limit": 81,
    }
    # Verify actual local weight bytes once; API/manifest identity alone does not
    # prove that the multi-GB blob has not been modified on disk.
    model_root = Path.home() / ".ollama/models"
    local_manifest = read(model_root / "manifests/registry.ollama.ai/library/qwen3/14b")
    layer = next(
        item
        for item in local_manifest["layers"]
        if item["mediaType"] == "application/vnd.ollama.image.model"
    )
    model_blob = model_root / "blobs" / layer["digest"].replace(":", "-")
    measured = file_hash(model_blob)
    if layer["digest"] != "sha256:" + measured or model_blob.stat().st_size != layer["size"]:
        raise ValueError("Local model weight bytes differ from declared identity")
    result["model_blob_verified_sha256"] = measured
    exclusive(STUDY / "data/binding.json", result)
    return result


def validate_response(data: dict[str, Any], planned: dict[str, Any]) -> dict[str, Any]:
    response = parse_native(data)
    output = FinalAnswer.model_validate(response.output).model_dump(mode="json")
    if not citations(output).issubset(set(planned["allowed_ids"])):
        raise ValueError("Output cites unauthorized evidence")
    for values in [output["evidence_ids"], output["uncertainty"]["evidence_ids"]]:
        if len(values) > len(planned["allowed_ids"]):
            raise ValueError("Citation cardinality exceeded")
    if response.usage.input_tokens != planned["prompt_tokens"]:
        raise ValueError("Native prompt count differs from verified tokenizer")
    return output


def mock_response(planned: dict[str, Any]) -> dict[str, Any]:
    output = {
        "answer": "",
        "evidence_ids": [],
        "uncertainty": {
            "confidence": 0,
            "assumptions": [],
            "evidence_ids": [],
            "unknowns": ["Mock plumbing only"],
        },
    }
    return {
        "done": True,
        "done_reason": "stop",
        "message": {"content": json.dumps(output), "thinking": ""},
        "prompt_eval_count": planned["prompt_tokens"],
        "eval_count": 30,
        "total_duration": 0,
        "eval_duration": 0,
        "load_duration": 0,
    }


def replay(*, mock: bool, campaign: Path | None = None) -> Path:
    manifest_path = STUDY / "data/replay-inputs/manifest.json"
    manifest = read(manifest_path)
    from synthesis_study.prepare import validate_manifest

    validate_manifest(manifest)
    if manifest["failures"] or not source_preserved(manifest)["passed"]:
        raise ValueError("Inputs/source fail preflight")
    if not mock:
        verify_seal()
        binding = read(STUDY / "data/binding.json")
        if binding["freeze_sha256"] != file_hash(STUDY / "freezes/v1.json"):
            raise ValueError("Binding/seal mismatch")
        # A second real campaign is not an automatic retry or resume.
        if any((p / "real-authorization.json").exists() for p in (STUDY / "runs").glob("*")):
            raise ValueError("A real campaign already exists; new protocol required")
    root = campaign or STUDY / "runs" / (("mock-" if mock else "real-") + uuid.uuid4().hex)
    root.mkdir(parents=True, exist_ok=False)
    budget = Budget(root / "budget.sqlite", 81)
    records: list[dict[str, Any]] = []
    status, failure = "running", None
    db_path = root / "replay.sqlite"
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute(
            "CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, payload TEXT)"
        )
    if not mock:
        exclusive(
            root / "real-authorization.json",
            {
                "goal": "Complete the evidence-preservation research",
                "planned_calls": 81,
                "new_worker_calls": 0,
                "freeze_sha256": file_hash(STUDY / "freezes/v1.json"),
            },
        )
    client = httpx.Client(
        base_url=ENDPOINT,
        timeout=manifest["spec"]["generation"]["timeout_seconds"],
        trust_env=False,
        follow_redirects=False,
    )
    try:
        if not mock:
            fingerprint(client, manifest["spec"])
        for planned in manifest["calls"]:
            if digest(planned["body"]) != planned["body_sha256"]:
                raise ValueError("Prepared request mutated")
            number = budget.reserve(planned["phase"], planned["qid"], planned["arm"])
            record: dict[str, Any] = {
                "number": number,
                "phase": planned["phase"],
                "qid": planned["qid"],
                "arm": planned["arm"],
                "agent": "synthesizer",
                "started_at": now(),
                "body_sha256": planned["body_sha256"],
                "request": planned["body"],
                "status": "reserved",
                "provider": "mock" if mock else "real",
            }
            snapshot(root / "journal-history", record)
            with closing(sqlite3.connect(db_path)) as db, db:
                db.execute(
                    "INSERT INTO events (type,payload) VALUES (?,?)",
                    (
                        "reserved",
                        json.dumps(
                            {k: record[k] for k in ["number", "phase", "qid", "arm", "body_sha256"]}
                        ),
                    ),
                )
            start = time.perf_counter()
            try:
                data = (
                    mock_response(planned)
                    if mock
                    else client.post("/api/chat", json=planned["body"]).raise_for_status().json()
                )
                message = data.get("message", {})
                exclusive(
                    root / "native-observations" / f"{number:04}.json",
                    {
                        "done": data.get("done"),
                        "finish_reason": data.get("done_reason"),
                        "input_tokens": data.get("prompt_eval_count"),
                        "output_tokens": data.get("eval_count"),
                        "thinking_chars": len(message.get("thinking") or ""),
                        "final_content_sha256": hashlib.sha256(
                            (message.get("content") or "").encode()
                        ).hexdigest(),
                        "total_duration_ns": data.get("total_duration"),
                        "eval_duration_ns": data.get("eval_duration"),
                        "load_duration_ns": data.get("load_duration"),
                        "hidden_reasoning_stored": False,
                    },
                )
                record["output"] = validate_response(data, planned)
                record["final_content"] = message["content"]
                record.update(
                    status="succeeded",
                    input_tokens=data["prompt_eval_count"],
                    output_tokens=data["eval_count"],
                )
                if not mock:
                    record["residency"] = client.get("/api/ps").raise_for_status().json()
            except Exception as exc:
                record.update(
                    status="failed",
                    error={
                        "type": type(exc).__name__,
                        "code": getattr(exc, "code", None),
                        "errno": getattr(exc, "errno", None),
                        "winerror": getattr(exc, "winerror", None),
                    },
                )
                failure = {
                    "number": number,
                    "phase": planned["phase"],
                    "qid": planned["qid"],
                    "arm": planned["arm"],
                    "error": record["error"],
                }
            record.update(ended_at=now(), latency_seconds=time.perf_counter() - start)
            exclusive(root / "call-journal" / f"{number:04}.json", record)
            snapshot(root / "journal-history", record)
            records.append(record)
            with closing(sqlite3.connect(db_path)) as db, db:
                db.execute(
                    "INSERT INTO events (type,payload) VALUES (?,?)",
                    (record["status"], json.dumps({"number": number, "status": record["status"]})),
                )
            snapshot(
                root / "progress",
                {
                    "reservations": budget.used,
                    "successful": sum(r["status"] == "succeeded" for r in records),
                    "last": {
                        "phase": planned["phase"],
                        "qid": planned["qid"],
                        "arm": planned["arm"],
                    },
                },
            )
            print(
                json.dumps(
                    {
                        "campaign": root.name,
                        "completed": len(records),
                        "planned": 81,
                        "phase": planned["phase"],
                        "qid": planned["qid"],
                        "arm": planned["arm"],
                        "status": record["status"],
                    }
                ),
                flush=True,
            )
            if failure:
                raise ValueError("Campaign failed; no retry/resume")
            # Native B/C token matching is checked as soon as a question block is complete.
            siblings = {
                r["arm"]: r
                for r in records
                if r["phase"] == planned["phase"] and r["qid"] == planned["qid"]
            }
            if {"B", "C"}.issubset(siblings) and abs(
                siblings["B"]["input_tokens"] - siblings["C"]["input_tokens"]
            ) > max(1, siblings["B"]["input_tokens"] * 0.05):
                raise ValueError("Native length control gate failed")
            if number == 9:
                exclusive(
                    root / "smoke-gate.json",
                    {
                        "passed": all(r["status"] == "succeeded" for r in records),
                        "calls": 9,
                        "criterion": "technical_only_no_gold_scoring",
                    },
                )
        status = "completed"
    except Exception as exc:
        status = "failed"
        failure = failure or {
            "type": type(exc).__name__,
            "errno": getattr(exc, "errno", None),
            "winerror": getattr(exc, "winerror", None),
        }
    finally:
        client.close()
        exclusive(
            root / "results.json",
            {
                "provider": "mock" if mock else "real",
                "status": status,
                "reservations": budget.used,
                "new_worker_calls": 0,
                "input_manifest_sha256": file_hash(manifest_path),
                "failure": failure,
                "source_preservation": source_preserved(manifest),
                "records": records,
            },
        )
    if status != "completed":
        raise ValueError(f"Campaign {root.name} failed; original records retained")
    return root
