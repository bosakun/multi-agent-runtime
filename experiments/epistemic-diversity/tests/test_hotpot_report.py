"""Independent offline report checks; no server requests."""

import json
import sys
from pathlib import Path
from xml.etree import ElementTree

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hotpot_reporting.report import bar_svg, citations, create, diversity
from test_hotpot import bound  # noqa: F401 - expose the existing offline fixture


def test_recursive_citations_and_mechanical_overlap_are_not_semantic_validity():
    assert citations(
        {"findings": [{"evidence_ids": ["a", "b"]}], "uncertainty": {"evidence_ids": ["a"]}}
    ) == {"a", "b"}
    values = diversity([{"a", "b"}, {"a"}, {"c"}], {"a", "c"}, single=False)
    assert values["worker_citation_redundancy"] == pytest.approx(0.25)
    assert values["worker_gold_support_recall"] == 1
    assert values["worker_unique_citation_fraction"] == pytest.approx(2 / 3)
    assert diversity([set()], {"a"}, single=True)["worker_citation_jaccard"] is None


def test_svg_is_well_formed_labeled_and_escapes_titles():
    svg = bar_svg("A < B & C", {"C0": 0, "C3": 0}, "MOCK - NOT LLM RESULTS; n=6")
    root = ElementTree.fromstring(svg)
    text = " ".join(root.itertext())
    assert "A < B & C" in text and "MOCK - NOT LLM RESULTS" in text


async def test_saved_mock_report_recomputes_official_metrics_and_refuses_overwrite(
    bound,  # noqa: F811 - pytest fixture imported above
    tmp_path,
):
    from external_benchmarks import runner

    input_path = runner.MOCK / "results.json"
    report_path = create(input_path, bound, tmp_path / "report")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert len(report["records"]) == 18 and report["label"].startswith("MOCK")
    assert all(value["cost_usd"] is None for value in report["records"])
    assert len(list(report_path.parent.glob("*.svg"))) == 6
    with pytest.raises(ValueError, match="overwrite"):
        create(input_path, bound, tmp_path / "report")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    data["records"][0]["metrics"]["f1"] = 1
    changed = input_path.parent / "changed-results.json"
    changed.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="recomputation"):
        create(changed, bound, tmp_path / "bad-report")
