import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from synthesis_study.analysis import components, paired
from synthesis_study.io import Budget, digest, exclusive
from synthesis_study.prepare import SupplementaryInput
from synthesis_study.runner import mock_response, validate_response
from synthesis_study.source import citations
from synthesis_study.tokenizer import LocalTokenizer

from app.core.errors import RuntimeFault


def planned(ids=None):
    return {"prompt_tokens": 100, "allowed_ids": ids or ["hp_example"]}


def test_exclusive_preserves_existing_bytes(tmp_path):
    target = tmp_path / "result.json"
    exclusive(target, {"first": True})
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        exclusive(target, {"second": True})
    assert target.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_budget_cannot_refund_resume_or_exceed(tmp_path):
    path = tmp_path / "budget.sqlite"
    budget = Budget(path, 2)
    assert budget.reserve("main", "a", "A") == 1
    assert budget.reserve("main", "a", "B") == 2
    with pytest.raises(ValueError):
        budget.reserve("main", "a", "C")
    with pytest.raises(ValueError):
        Budget(path, 81)
    assert budget.used == 2
    # Closed connections permit native Windows rename, including after exceptions.
    renamed = path.with_name("closed.sqlite")
    path.rename(renamed)
    renamed.unlink()


def test_smoke_budget_stops_at_nine(tmp_path):
    budget = Budget(tmp_path / "budget.sqlite")
    for i in range(9):
        budget.reserve("smoke", str(i), "A")
    with pytest.raises(ValueError):
        budget.reserve("smoke", "extra", "A")
    assert budget.reserve("main", "main", "A") == 10


def test_supplement_schema_rejects_private_or_unknown_fields():
    assert SupplementaryInput(supplementary_material="").model_dump() == {
        "supplementary_material": ""
    }
    with pytest.raises(ValidationError):
        SupplementaryInput(supplementary_material="", gold_answer="secret")
    with pytest.raises(ValidationError):
        SupplementaryInput(supplementary_material=3)


def test_citation_order_and_deduplication():
    payload = {
        "findings": [{"evidence_ids": ["b", "a"]}, {"evidence_ids": ["b", "c"]}],
        "uncertainty": {"evidence_ids": ["d", "a"]},
    }
    assert citations(payload) == ["b", "a", "c", "d"]


def test_valid_mock_response_is_schema_checked():
    assert validate_response(mock_response(planned()), planned())["answer"] == ""


@pytest.mark.parametrize("mutation", ["unknown_id", "thinking", "input_count", "length", "tool"])
def test_invalid_response_stops(mutation):
    data = mock_response(planned())
    if mutation == "unknown_id":
        output = json.loads(data["message"]["content"])
        output["evidence_ids"] = ["not_allowed"]
        data["message"]["content"] = json.dumps(output)
    elif mutation == "thinking":
        data["message"]["thinking"] = "not stored"
    elif mutation == "input_count":
        data["prompt_eval_count"] = 101
    elif mutation == "length":
        data["done_reason"] = "length"
    else:
        data["message"]["tool_calls"] = [{"name": "forbidden"}]
    with pytest.raises((ValueError, RuntimeFault)):
        validate_response(data, planned())


def test_paired_analysis_and_cluster_degenerate_case():
    result = paired([0.25, 0.25])
    assert result["mean_difference"] == 0.25
    assert result["ci95"] == [0.25, 0.25]
    assert paired([0.1, -0.1], [[0, 1]])["ci95"] is None


def test_title_components_are_transitive():
    questions = {
        "a": {"sentences": [{"title": "x"}]},
        "b": {"sentences": [{"title": "x"}, {"title": "y"}]},
        "c": {"sentences": [{"title": "y"}]},
        "d": {"sentences": [{"title": "z"}]},
    }
    assert components(["a", "b", "c", "d"], questions) == [[0, 1, 2], [3]]


def test_renderer_checks_backend_contract():
    body = {
        "think": False,
        "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
    }
    rendered = LocalTokenizer.render(body)
    assert "u /no_think<|im_end|>" in rendered
    assert rendered.endswith("<think>\n\n</think>\n\n")
    body["think"] = True
    with pytest.raises(ValueError):
        LocalTokenizer.render(body)


def test_hashes_track_content_not_dictionary_order():
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})
    assert digest({"a": 1}) != digest({"a": 2})


def test_temporary_cleanup_lock_does_not_invalidate_publication(tmp_path, monkeypatch, capsys):
    original = Path.unlink

    def locked_unlink(path, *args, **kwargs):
        if path.suffix == ".tmp":
            error = PermissionError(13, "simulated sharing violation")
            error.winerror = 32
            raise error
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", locked_unlink)
    target = tmp_path / "published.json"
    exclusive(target, {"complete": True})
    assert json.loads(target.read_text()) == {"complete": True}
    assert "cleanup_own_temporary_link" in capsys.readouterr().err
    with pytest.raises(FileExistsError):
        exclusive(target, {"complete": False})
    assert json.loads(target.read_text()) == {"complete": True}
