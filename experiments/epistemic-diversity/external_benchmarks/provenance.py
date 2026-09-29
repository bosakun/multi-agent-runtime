"""Checksummed downloads/bundles, append-only source seals, no credential changes."""

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

from bounded_pilot.seals import sources as historical_sources
from epistemic.paths import REPO, ROOT, digest
from operational_diagnostics.budget_experiment import exclusive
from operational_recovery.pilot24 import read_signed, signed

from external_benchmarks.dataset import SEED, private_gold, select

SCORER_COMMIT = "3635853403a8735609ee997664e1528f4480762a"
SCORER_SHA256 = "d35fc91a6db21d791dbdda11daf3856e9359f5701d54e3eefba20d88fecc02c0"
DATA_URL = "https://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
MIRROR_URL = "https://huggingface.co/datasets/namlh2004/hotpotqa/resolve/7e54db4656209750ff487f6fdf8e39a66dba136b/hotpot_dev_distractor_v1.json"
MIRROR_SHA256 = "e3da074df24e8369009918aa5cdbdd254dadcde4c63f7569d36afd6f2268caa8"
DATA = REPO / "reports/hotpotqa-data"
BUNDLE = DATA / "prepared"


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sources() -> dict[str, str]:
    files = historical_sources()
    paths = list((ROOT / "external_benchmarks").glob("*.py")) + [
        ROOT / "external_benchmarks/vendor/hotpot_evaluate_v1.py",
        ROOT / "external_benchmarks/vendor/LICENSE.txt",
        ROOT / "external_benchmarks/vendor/NOTICE.md",
        ROOT / "hotpot.py",
        ROOT / "ACTIVE_BENCHMARK.md",
        ROOT / "docs/protocol-3.0-hotpotqa.md",
        ROOT / "tests/test_hotpot.py",
        ROOT / "freezes/benchmark-2.0.0-protocol-2.7.json",
    ]
    files.update({p.relative_to(REPO).as_posix(): file_sha256(p) for p in paths})
    return files


def download(*, mirror: bool = False) -> Path:
    raw = DATA / "hotpot_dev_distractor_v1.json"
    if raw.exists():
        raise ValueError("Dataset path exists; no overwrite or silent refresh")
    DATA.mkdir(parents=True, exist_ok=True)
    url = MIRROR_URL if mirror else DATA_URL
    request = urllib.request.Request(url, headers={"User-Agent": "research-hotpot-import/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read(128 * 1024 * 1024 + 1)
    if len(payload) > 128 * 1024 * 1024:
        raise ValueError("Dataset exceeds safety size bound")
    if mirror and hashlib.sha256(payload).hexdigest() != MIRROR_SHA256:
        raise ValueError("Pinned mirror checksum mismatch")
    rows = json.loads(payload)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Not an official list-format dataset")
    # Downloaded corpus is a generated artifact, not authored source.
    with raw.open("xb") as stream:
        stream.write(payload)
    exclusive(
        DATA / "download.json",
        signed(
            {
                "url": url,
                "original_source": DATA_URL,
                "mirror": mirror,
                "raw_sha256": file_sha256(raw),
                "bytes": len(payload),
                "rows": len(rows),
                "dataset_license": "CC BY-SA 4.0",
                "source": "https://hotpotqa.github.io/",
            }
        ),
    )
    return raw


def verify_download() -> Path:
    """Add a verified receipt without changing an earlier download or receipt."""
    raw = DATA / "hotpot_dev_distractor_v1.json"
    receipt = DATA / "download.json"
    recorded = json.loads(receipt.read_text(encoding="utf-8"))
    actual = file_sha256(raw)
    if recorded.get("url") != MIRROR_URL or recorded.get("mirror") is not True:
        raise ValueError("Only the explicitly pinned mirror can be re-attested")
    if actual != MIRROR_SHA256 or recorded.get("bytes") != raw.stat().st_size:
        raise ValueError("Pinned mirror checksum/size mismatch")
    rows = json.loads(raw.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) != recorded.get("rows"):
        raise ValueError("Downloaded corpus row count mismatch")
    target = DATA / "download-verification.json"
    exclusive(
        target,
        signed(
            {
                "url": MIRROR_URL,
                "mirror": True,
                "original_source": DATA_URL,
                "raw_sha256": actual,
                "bytes": raw.stat().st_size,
                "rows": len(rows),
                "earlier_receipt_sha256": file_sha256(receipt),
                "note": "Earlier receipt retained; raw and receipt hashes use distinct keys",
                "dataset_license": "CC BY-SA 4.0",
            }
        ),
    )
    return target


def prepare(raw: Path, bundle: Path = BUNDLE) -> Path:
    if bundle.exists():
        raise ValueError("Prepared bundle exists; no overwrite or reselection")
    rows: list[dict[str, Any]] = json.loads(raw.read_text(encoding="utf-8"))
    provenance = (
        read_signed(
            DATA / "download-verification.json"
            if (DATA / "download-verification.json").exists()
            else DATA / "download.json"
        )
        if raw.resolve() == (DATA / "hotpot_dev_distractor_v1.json").resolve()
        else None
    )
    if provenance and provenance["raw_sha256"] != file_sha256(raw):
        raise ValueError("Downloaded corpus changed before preparation")
    questions, selection = select(rows)
    original = {row["_id"]: row for row in rows}
    gold = [private_gold(original[q.id], q) for q in questions]
    bundle.mkdir(parents=True, exist_ok=False)
    for question, annotation in zip(questions, gold, strict=True):
        exclusive(bundle / "public" / f"{question.id}.json", question.model_dump(mode="json"))
        exclusive(bundle / "gold" / f"{annotation.id}.json", annotation.model_dump(mode="json"))
    files = {p.relative_to(bundle).as_posix(): file_sha256(p) for p in bundle.rglob("*.json")}
    exclusive(
        bundle / "manifest.json",
        signed(
            {
                "benchmark": "HotpotQA",
                "setting": "distractor",
                "split": "dev",
                "source_url": provenance["url"]
                if provenance
                else "provided local file (unverified origin)",
                "original_source": DATA_URL,
                "download_provenance": provenance,
                "raw_sha256": file_sha256(raw),
                "selection_seed": SEED,
                "selection": selection,
                "selection_rule": "public context <=12000 chars; hash(seed:QA-ID), first six",
                "task_ids": [q.id for q in questions],
                "files": files,
                "scorer_commit": SCORER_COMMIT,
                "scorer_sha256": SCORER_SHA256,
                "license": "CC BY-SA 4.0; source text unchanged, public/gold projection added",
            }
        ),
    )
    return bundle / "manifest.json"


def verify_bundle(bundle: Path = BUNDLE) -> dict[str, Any]:
    manifest = read_signed(bundle / "manifest.json")
    if manifest["scorer_sha256"] != SCORER_SHA256 or manifest["selection_seed"] != SEED:
        raise ValueError("Dataset/scorer selection controls drift")
    actual = {
        p.relative_to(bundle).as_posix(): file_sha256(p)
        for p in bundle.rglob("*.json")
        if p.relative_to(bundle).as_posix() != "manifest.json"
    }
    if actual != manifest["files"]:
        raise ValueError("Prepared public/gold content inventory drift")
    if digest({k: v for k, v in manifest.items() if k != "sha256"}) != manifest["sha256"]:
        raise ValueError("Dataset manifest signature mismatch")
    return manifest
