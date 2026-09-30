"""Read-only integration checks against the locally retained historical evidence."""

import copy
from pathlib import Path

import pytest
from synthesis_study.io import STUDY, read
from synthesis_study.prepare import validate_manifest
from synthesis_study.source import Sources
from synthesis_study.tokenizer import LocalTokenizer


@pytest.fixture(scope="module")
def source():
    return Sources()


def test_preserved_typed_artifacts_and_complete_source(source):
    assert len(source.ids) == 30
    assert len(source.calls) == 90
    assert source.verify_preservation()["passed"]
    for qid in source.ids:
        excerpt, ids = source.excerpt(qid)
        assert len(ids) == len(set(ids))
        assert all(f"[{sid}]" in excerpt for sid in ids)


def test_local_tokenizer_matches_every_historical_native_count(source):
    model_root = Path.home() / ".ollama/models"
    if not model_root.exists():
        pytest.skip("Installed local GGUF tokenizer is required")
    result = source.verify_tokenizer(LocalTokenizer(model_root))
    assert result["exact_matches"] == 120
    assert result["max_absolute_difference"] == 0


def test_prepared_grid_and_mutation_rejection():
    path = STUDY / "data/replay-inputs/manifest.json"
    if not path.exists():
        pytest.skip("Run gold-blind prepare first")
    manifest = read(path)
    validate_manifest(manifest)
    assert len(manifest["calls"]) == 81
    assert manifest["maximum_prompt_tokens"] <= 4096
    altered = copy.deepcopy(manifest)
    altered["calls"][0]["worker_payload_hashes"][0] = "tampered"
    with pytest.raises(ValueError, match="worker payload hash"):
        validate_manifest(altered)
    altered = copy.deepcopy(manifest)
    altered["calls"].reverse()
    with pytest.raises(ValueError, match="order"):
        validate_manifest(altered)
