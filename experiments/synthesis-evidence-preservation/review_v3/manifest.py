"""Implementation candidate only; checklist decisions remain explicitly unresolved."""

from pathlib import Path

from review_v3 import BUILDER_VERSION, PROTOCOL_VERSION, RULE_VERSION, SCHEMA_VERSION, STATUS
from review_v3.codebook import candidate_definition
from review_v3.storage import file_hash

UNRESOLVED = [
    "two independent human reviewers unassigned",
    "Study 1 30/28 scope and IAA/descriptive case IDs unresolved",
    "registry/stage reviewer relationship and prior exposure unresolved",
    "external calibration cases not selected; human calibration not performed",
    "R1/R2 independent ballots and adjudicated registry absent",
    "registry, codebook, applicability and rules require human freeze",
    "bootstrap draws/seed/CI/zero-denominator policy unresolved",
    "source/packet inclusion, normalization and privacy sharing approval unresolved",
    "primary metrics, sensitivity and analysis software require human sign-off",
    "no human labels; no adjudication",
    "pilot selection/reviewers/third-adjudicator policy and packet freeze unresolved",
    "pilot not performed; stability and ambiguity inspection absent",
    "codebook candidate requires pilot revisions and v1.0 human sign-off",
]


def freeze_candidate():
    root = Path(__file__).parent
    return {
        "status": STATUS,
        "candidate": "HUMAN REVIEW V3 FREEZE CANDIDATE",
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "builder_version": BUILDER_VERSION,
        "analysis_rule_version": RULE_VERSION,
        "codebook_version": None,
        "codebook_candidate": candidate_definition().model_dump(mode="json"),
        "pilot_batches_completed": 0,
        "pilot_clearance": None,
        "reviewers": [None, None],
        "scope": None,
        "bootstrap_config": None,
        "human_labels": 0,
        "adjudication_records": 0,
        "unresolved_checklist_items": UNRESOLVED,
        "tooling_hashes": {
            p.relative_to(root).as_posix(): file_hash(p) for p in sorted(root.rglob("*.py"))
        },
        "protocol_document_hashes": {
            name: file_hash(root.parent / "docs" / name)
            for name in (
                "human-review-stage-analysis-plan-v3.md",
                "evidence-lineage-metrics-plan.md",
                "human-review-preflight-freeze-checklist.md",
                "review-stage-amendment-and-kit-impact.md",
            )
        },
        "source_hashes": {},
        "packet_hashes": {},
        "human_signoff": None,
        "final_frozen": False,
    }
