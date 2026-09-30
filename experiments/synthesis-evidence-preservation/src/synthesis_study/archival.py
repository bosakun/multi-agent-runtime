"""Explain unavailable archival tests without modifying archival files or verifiers."""

import hashlib

from synthesis_study.io import REPO, read


def archival_exceptions():
    from epistemic.freeze import FREEZE_PATH, frozen_files

    old = read(FREEZE_PATH)["files"]
    actual = {p.replace("\\", "/"): h for p, h in frozen_files().items()}
    if actual != old:
        raise ValueError("Archival scientific content differs, not merely Windows path keys")
    baseline = read(REPO / "experiments/epistemic-diversity/results/protocol23-preservation.json")
    line_endings = []
    for group in ["benchmark20", "prompts", "configs", "historical_freezes"]:
        for relative, expected in baseline["before"][group]["files"].items():
            raw = (REPO / relative).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != expected:
                    raise ValueError(
                        "Historical preservation failure is not only CRLF: " + relative
                    )
                line_endings.append(relative)
    prefix = "experiments/epistemic-diversity/tests/"
    nodes = [
        prefix + "test_budget_experiment.py::" + name
        for name in [
            "test_six_serial_calls_and_only_limit_changes",
            "test_other_failures_stop_without_retry",
            "test_budget_refused_before_preflight_or_generation",
            "test_prepare_refuses_overwrite_and_historical_descendants",
            "test_rehashed_binding_settings_rejected",
            "test_preflight_failure_retains_unexecuted_cells_and_zero_calls",
            "test_stale_seal_rejected_without_campaign_mutation",
        ]
    ]
    nodes += [
        prefix + "test_pilot24.py::" + name
        for name in [
            "test_mock_pipeline_full_grid",
            "test_full_fake_http_grid_integrity_and_no_reuse",
            "test_failure_retained_no_second_case_or_retry",
            "test_stale_source_and_old_protocol_binding_rejected",
        ]
    ]
    nodes += [
        prefix + "test_protocol23.py::test_preservation_manifest[" + group + "]"
        for group in ["benchmark20", "prompts", "configs", "historical_freezes"]
    ]
    nodes += [
        prefix + "test_protocol23.py::test_scientific_sources_match_protocol22_seal",
        prefix
        + "test_token_budget_plan.py::"
        + "test_new_budget_does_not_relax_current_pilot_or_reuse_campaign",
    ]
    missing = REPO / (
        "experiments/epistemic-diversity/runs/qwen3-14b-protocol23/pilot/call-journal/"
        "0017_e14b05fe11754953a75d6010dc002060_worker_0.json"
    )
    if not missing.exists():
        nodes += [
            prefix + "test_recovery_live.py::" + name
            for name in [
                "test_diagnostic_baseline_length_then_gate_and_no_reuse",
                "test_candidate_length_stops_and_never_approves_pilot",
            ]
        ]
    return {
        "old_protocol23_not_runnable_on_this_checkout": True,
        "normalized_path_scientific_hashes_match": True,
        "raw_preservation_differences_only_crlf": line_endings,
        "missing_old_journal": missing.relative_to(REPO).as_posix()
        if not missing.exists()
        else None,
        "deselected_archival_nodes": nodes,
        "original_full_suite_passed": False,
        "historical_source_not_modified": True,
    }
