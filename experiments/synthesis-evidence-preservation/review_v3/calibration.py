"""Future external cases and local synthetic vignettes live outside main scope."""

from typing import Literal

from review_v3.schema import Record

EDGE_CASES = (
    "correct",
    "partial",
    "distorted",
    "absent",
    "unclear",
    "alternative_path",
    "identity_alias",
    "unknown_transition",
    "separate_publication_record",
    "supplementary_evidence_route",
    "upstream_failure_cascade",
    "complete_path_unsupported_answer",
)


class CalibrationCase(Record):
    case_id: str
    namespace: Literal["external_hotpotqa", "synthetic_vignette"]
    source_hashes: dict[str, str]
    edge_cases: list[str]
    synthetic: bool


def calibration_stop_candidate(batches, covered_edge_cases):
    # A mechanical checklist indication, NOT automatic codebook sign-off.
    return bool(
        batches
        and batches[-1]["new_guideline_rules"] == 0
        and set(EDGE_CASES) <= set(covered_edge_cases)
    )
