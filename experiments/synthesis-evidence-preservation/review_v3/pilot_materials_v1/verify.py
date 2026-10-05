"""Integrity/projection checks only, not semantic review or real IAA/metrics."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3.pilot_materials_v1.prepare import (  # noqa: E402
    EXPECTED_RAW,
    MARKER,
    REPO,
    raw_material,
    select_ids,
    worklist,
)
from review_v3.storage import digest, exclusive, file_hash, read  # noqa: E402

REQUIRED_COVERAGE = {
    "correct",
    "partial",
    "distorted",
    "absent",
    "unclear",
    "valid_alternative_path",
    "invalid_external_premise_path",
    "path_conditional_requiredness",
    "identity_alias",
    "retained",
    "partial_loss",
    "publication_distorted",
    "lost",
    "unknown_transition",
    "separate_publication_record",
    "artifact_route",
    "supplementary_evidence_route",
    "both_routes",
    "upstream_absence_cascade",
    "bridge_fact_not_asserted",
    "final_fact_reflected",
    "final_fact_contradicted",
    "complete_path_fully_supported",
    "complete_path_unsupported_answer",
    "partially_supported_answer",
}


def validate_b_sources(sources, keys):
    key_ids = {c["vignette_id"] for c in keys}
    coverage = {tag for c in keys for tag in c["coverage"]}
    assert REQUIRED_COVERAGE <= coverage
    for phase, cases in sources.items():
        assert {c["vignette_id"] for c in cases} == key_ids
        for case in cases:
            assert case["marker"] == MARKER
            assert ("final_output" in case) == (phase == "S5")
            assert ("actual_synthesizer_input" in case) == (phase in {"S4", "S5"})
            assert "author_key" not in case and "intended_label" not in json.dumps(case)
            assert case["question"]["en"] and case["question"]["ja"]
    return len(key_ids)


def verify(root):
    root = Path(root)
    manifest = read(root / "pilot_materials_manifest.json")
    for path, expected in manifest["file_hashes"].items():
        assert file_hash(root / path) == expected, path
    raw_path = REPO / "reports/hotpotqa-data/hotpot_dev_distractor_v1.json"
    assert file_hash(raw_path) == EXPECTED_RAW
    rows = read(raw_path)
    exclusions = read(root / "author_only/exclusions.json")
    selected, eligible = select_ids([r["_id"] for r in rows], exclusions["excluded_ids"])
    assert selected == manifest["pilot_a"]["selected_ids"]
    assert digest(eligible) == manifest["pilot_a"]["eligible_ids_hash"]
    assert exclusions["groups"]["old_kit_calibration"]
    for group in exclusions["groups"].values():
        assert not set(selected) & set(group)
    by_id = {r["_id"]: r for r in rows}
    aliases = read(root / "author_only/case_alias_mapping.json")
    for alias, qid in aliases.items():
        r1 = read(root / f"pilot_a/R1/{alias}.source.json")
        r2 = read(root / f"pilot_a/R2/{alias}.source.json")
        # Compare complete whitelisted raw projections, without interpreting prose.
        assert r1 == raw_material(by_id[qid], alias)
        assert set(r1) == {"case_alias", "question", "reference_sentences"}
        assert set(r2) == set(r1) | {"benchmark_alignment"}
        assert {k: r2[k] for k in r1} == r1
        assert r2["benchmark_alignment"] == {
            "gold_answer": by_id[qid]["answer"],
            "gold_supporting_facts": by_id[qid]["supporting_facts"],
        }
        for phase, material in [("R1", r1), ("R2", r2)]:
            assert read(root / f"pilot_a/{phase}/{alias}.translation-worklist.json") == worklist(
                material, phase
            )
    sources = {
        p: read(root / f"pilot_b/reviewer_materials/{p}.source.json")
        for p in ("S1", "S2", "S3", "S4", "S5")
    }
    count = validate_b_sources(sources, read(root / "author_only/pilot_b_answer_key.json"))
    assert not manifest["final_frozen"] and manifest["human_labels"] == 0
    assert manifest["reviewer_specific_packets_generated"] == 0
    return dict(
        passed=True,
        selected_n=len(selected),
        eligible_n=len(eligible),
        excluded_n=len(exclusions["excluded_ids"]),
        vignette_n=count,
        file_hashes_checked=len(manifest["file_hashes"]),
        manifest_sha256=file_hash(root / "pilot_materials_manifest.json"),
        real_semantic_annotations_generated=0,
        real_translations_generated=0,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = verify(args.root)
    exclusive(args.output, result)
    print(json.dumps(result, indent=2))
