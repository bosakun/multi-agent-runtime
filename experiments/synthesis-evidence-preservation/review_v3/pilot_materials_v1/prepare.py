"""Local-only, result-blind preparation. Never downloads, translates or annotates QA."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review_v3 import BUILDER_VERSION, PROTOCOL_VERSION, SCHEMA_VERSION  # noqa: E402
from review_v3.codebook import candidate_definition, definition_hash  # noqa: E402
from review_v3.storage import digest, exclusive, file_hash, now, read  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
V3 = Path(__file__).resolve().parents[1]
VERSION = "pilot-materials-v1.0.0"
SALT = "human-review-pilot-v1:"
EXPECTED_RAW = "e3da074df24e8369009918aa5cdbdd254dadcde4c63f7569d36afd6f2268caa8"
MARKER = "SYNTHETIC CALIBRATION MATERIAL / NOT STUDY DATA / NOT MODEL OUTPUT"


def select_ids(ids, excluded, count=6):
    """Only IDs enter ranking: no type, question text, gold, scores or lengths."""
    if any(not isinstance(qid, str) or not qid for qid in ids) or len(ids) != len(set(ids)):
        raise ValueError("Unique text QA IDs required")
    eligible = sorted(set(ids) - set(excluded))
    ranked = sorted(eligible, key=lambda q: (hashlib.sha256((SALT + q).encode()).hexdigest(), q))
    if len(ranked) < count:
        raise ValueError("Insufficient eligible raw IDs")
    return ranked[:count], eligible


def raw_material(row, alias):
    """Whitelisted raw projection; no facts/support sets/paths/judgments constructed."""
    sentences = []
    for doc, (title, texts) in enumerate(row["context"]):
        for index, text in enumerate(texts):
            sentences.append(
                dict(
                    sentence_id=f"{alias}-d{doc:02d}-s{index:03d}",
                    title=title,
                    sentence_index=index,
                    sentence_text=text,
                )
            )
    return dict(case_alias=alias, question=row["question"], reference_sentences=sentences)


def worklist(material, phase):
    """Stage-local English prose only; intentionally no Japanese text field."""
    allowed = (
        "R1 question and complete raw/reference evidence only; no gold or future-stage information"
        if phase == "R1"
        else "R2 question/raw evidence and benchmark gold only; no Worker or final output or scores"
    )
    rows = []

    def add(pointer, text):
        rows.append(
            dict(
                case_alias=material["case_alias"],
                material_pointer=pointer,
                english_original=text,
                english_hash=hashlib.sha256(text.encode()).hexdigest(),
                allowed_translation_context=allowed,
            )
        )

    add("/question", material["question"])
    for i, sentence in enumerate(material["reference_sentences"]):
        add(f"/reference_sentences/{i}/title", sentence["title"])
        add(f"/reference_sentences/{i}/sentence_text", sentence["sentence_text"])
    if phase == "R2":
        add("/benchmark_alignment/gold_answer", material["benchmark_alignment"]["gold_answer"])
        for i, fact in enumerate(material["benchmark_alignment"]["gold_supporting_facts"]):
            add(f"/benchmark_alignment/gold_supporting_facts/{i}/0", fact[0])
    return rows


def exclusion_manifest():
    """Read only selection IDs and calibration flags; never consume scores/results."""
    dataset_manifest = REPO / "reports/hotpotqa-data/prepared-thirty/manifest.json"
    replay_manifest = (
        REPO / "experiments/synthesis-evidence-preservation/data/replay-inputs/manifest.json"
    )
    study1 = read(dataset_manifest)
    study2 = read(replay_manifest)["spec"]
    groups = {
        "study1_main30": study1["task_ids"],
        "study2_main24": study2["main_question_ids"],
        "study2_smoke": study2["smoke_question_ids"],
        "historical_model_pilot6": study1["pilot_task_ids"],
        "historical_review_calibration2": study1["pilot_task_ids"][:2],
        "other_documented_real_codebook_cases": [],
    }
    if len(groups["study1_main30"]) != 30 or len(groups["study2_main24"]) != 24:
        raise ValueError("Historical scopes do not match 30/24")
    kit_root = REPO / "experiments/synthesis-evidence-preservation/reports/review-kits"
    mappings = {}
    source_hashes = {
        str(dataset_manifest.relative_to(REPO)): file_hash(dataset_manifest),
        str(replay_manifest.relative_to(REPO)): file_hash(replay_manifest),
    }
    # Old forms contain no real human labels. Calibration case-code mapping is in
    # their public material. Read the QA ID only, not Worker/final text or scores.
    for form in sorted(kit_root.glob("*/reviewer_*/forms/*.json")):
        value = read(form)
        if value.get("calibration"):
            public = form.parent.parent / "public" / (form.stem + ".md")
            if not public.is_file():
                raise ValueError("Calibration mapping missing; do not silently omit old case")
            # Frozen audit.py defines case aliases by ID + seed, not content.
            matches = [
                q
                for q in groups["study1_main30"]
                if "source-" + digest({"id": q, "seed": 20260930})[:12] == form.stem
            ]
            if len(matches) != 1:
                raise ValueError("Cannot map historical calibration to QA ID")
            qid = matches[0]
            mappings[form.stem] = qid
            source_hashes[str(form.relative_to(REPO))] = file_hash(form)
            source_hashes[str(public.relative_to(REPO))] = file_hash(public)
    groups["old_kit_calibration"] = sorted(set(mappings.values()))
    excluded = sorted({q for ids in groups.values() for q in ids})
    return dict(
        groups=groups,
        excluded_ids=excluded,
        exclusion_ids_hash=digest(excluded),
        source_hashes=source_hashes,
        scope="main30 fully excluded; independent of unresolved main30/28 decision",
        other_case_basis=(
            "Current codebook examples are wholly synthetic; "
            "no additional real QA IDs documented"
        ),
        human_prior_exposure_check_pending=True,
    )


def pilot_b_projection(case, phase):
    """Preparation source, NOT an authorized reviewer-specific packet/ballot."""
    if phase not in {"S1", "S2", "S3", "S4", "S5"} or case.get("marker") != MARKER:
        raise ValueError("Known stage and explicitly artificial material required")
    base = dict(
        marker=MARKER,
        vignette_id=case["vignette_id"],
        phase=phase,
        question=case["question"],
        reference=case["reference"],
        teaching_reference=case["teaching_reference"],
        actual_worker_input_sentence_ids=case["actual_worker_input_sentence_ids"],
        exercise_prompt_ja="この段階の観測資料だけで該当するCodebook欄を判定してください。",
    )
    if phase != "S1":
        base["worker_public_expression"] = case["worker_public_expression"]
    if phase in ("S3", "S4", "S5"):
        base["publication_transition_type"] = case["publication_transition_type"]
        base["published_artifact"] = case["published_artifact"]
    if phase in ("S4", "S5"):
        base["actual_synthesizer_input"] = case["actual_synthesizer_input"]
    if phase == "S5":
        base["final_output"] = case["final_output"]
    return base


def templates():
    return {
        "pilot-batch-log": dict(
            batch_id=None,
            namespace=None,
            codebook_version=None,
            codebook_definition_hash=None,
            protocol_hash=None,
            packet_hashes={},
            case_ids=[],
            independent_ballot_locks={},
            independent_locks_at=None,
            inspected_at=None,
            adjudication_log_hash=None,
            ambiguity_log_hash=None,
            covered_edge_cases=[],
            new_guideline_rules=None,
            major_disagreements_resolvable=None,
            unresolved_ambiguities_documented=None,
            unresolved_blocker_ids=[],
        ),
        "pilot-ambiguity-log": dict(
            entries=[],
            entry_fields=[
                "ambiguity_id",
                "batch_id",
                "unit_id",
                "codebook_version",
                "affected_fields",
                "competing_labels",
                "rule_ids",
                "evidence_pointer",
                "issue",
                "disposition",
                "resolution",
                "blocks_freeze",
                "timestamp",
            ],
        ),
        "pilot-codebook-revision-log": dict(
            entries=[],
            entry_fields=[
                "old_version",
                "new_version",
                "old_definition_hash",
                "new_definition_hash",
                "reason",
                "affected_rule_ids",
                "affected_pilot_units",
                "old_annotation_hashes",
                "reannotation_strategy",
                "reannotated_pilot_units",
                "new_independent_batch_id",
            ],
        ),
        "reviewer-profile": dict(
            reviewer_id=None,
            relationship_to_author=[],
            involvement_in_implementation=None,
            involvement_in_experiment_design=None,
            prior_result_exposure=None,
            prior_case_exposure=[],
            disclosure_notes=None,
        ),
        "pilot-human-authorization": dict(
            authorization_id=None,
            version=None,
            reviewer_ids=[],
            signed_by=None,
            signed_at=None,
            codebook_version=None,
            codebook_definition_hash=None,
            material_manifest_hash=None,
            translation_asset_hashes={},
            third_adjudicator_used=None,
            source_sharing_approved=None,
            stage_disclosure_method=None,
        ),
        "pilot-clearance-checklist": dict(
            critical_edge_cases_actually_reviewed=None,
            final_batch_new_rules_zero=None,
            unresolved_ambiguities_recorded=None,
            no_freeze_blockers=None,
            final_codebook_version_hash_checked=None,
            translation_policy_version_hash_checked=None,
            reviewer_composition_checked=None,
            adjudication_policy_checked=None,
            main_scope_checked=None,
            main_iaa_scope_checked=None,
            human_signoff=None,
            signed_at=None,
        ),
    }


def prepare(destination, catalogue):
    raw = REPO / "reports/hotpotqa-data/hotpot_dev_distractor_v1.json"
    if not raw.is_file():
        raise ValueError(
            "PILOT A SELECTION BLOCKED: eligible raw HotpotQA source unavailable locally"
        )
    if file_hash(raw) != EXPECTED_RAW:
        raise ValueError("Raw dataset snapshot differs; no download/replacement permitted")
    rows = read(raw)
    if len(rows) != 7405:
        raise ValueError("Expected complete local distractor dev snapshot")
    exclusions = exclusion_manifest()
    selected, eligible = select_ids([row["_id"] for row in rows], exclusions["excluded_ids"])
    by_id = {row["_id"]: row for row in rows}
    definition = candidate_definition()
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    cases = read(catalogue)
    if len(cases) < 12 or len({c["vignette_id"] for c in cases}) != len(cases):
        raise ValueError("Unique artificial vignette catalogue required")
    for case in cases:
        if case["marker"] != MARKER:
            raise ValueError("Synthetic marker required")
        for entry in case["author_key"]["judgments"]:
            if not set(entry["rule_ids"]) <= {r.rule_id for r in definition.rules}:
                raise ValueError("Answer key references unknown Codebook rule")
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Fresh versioned destination required; no overwrite")
    hashes = {}

    def save(path, value):
        hashes[path] = exclusive(destination / path, value)

    save("author_only/exclusions.json", exclusions)
    selection = dict(
        algorithm="SHA256(UTF8(selection_salt + QA_ID)), hex ascending; ID tie-break",
        selection_salt=SALT,
        eligible_pool_count=len(eligible),
        eligible_ids_hash=digest(eligible),
        eligible_ids_canonicalization=(
            "UTF8 compact JSON, lexicographically sorted unique QA ID list"
        ),
        exclusion_count=len(exclusions["excluded_ids"]),
        exclusion_ids_hash=exclusions["exclusion_ids_hash"],
        selected_ids=selected,
        selected_ordering=selected,
        selected_ranks={q: hashlib.sha256((SALT + q).encode()).hexdigest() for q in selected},
        dataset_sha256=EXPECTED_RAW,
        source_commit=source_commit,
        implementation_version=VERSION,
        implementation_sha256=file_hash(__file__),
        selection_timestamp=now(),
        selection_inputs="QA IDs only; no score/content/gold stratification",
    )
    save("author_only/eligible_ids.json", eligible)
    save("author_only/selection.json", selection)
    aliases = {}
    for i, qid in enumerate(selected, 1):
        alias = f"PA-{i:02d}"
        aliases[alias] = qid
        r1 = raw_material(by_id[qid], alias)
        r2 = {
            **r1,
            "benchmark_alignment": dict(
                gold_answer=by_id[qid]["answer"],
                gold_supporting_facts=by_id[qid]["supporting_facts"],
            ),
        }
        for phase, material in (("R1", r1), ("R2", r2)):
            save(f"pilot_a/{phase}/{alias}.source.json", material)
            save(f"pilot_a/{phase}/{alias}.translation-worklist.json", worklist(material, phase))
    save("author_only/case_alias_mapping.json", aliases)
    for phase in ("S1", "S2", "S3", "S4", "S5"):
        save(
            f"pilot_b/reviewer_materials/{phase}.source.json",
            [pilot_b_projection(case, phase) for case in cases],
        )
    save(
        "author_only/pilot_b_answer_key.json",
        [
            dict(
                marker=MARKER,
                vignette_id=c["vignette_id"],
                **c["author_key"],
            )
            for c in cases
        ],
    )
    for name, value in templates().items():
        save(f"templates/{name}.template.json", dict(template_only=True, **value))
    guide = V3 / "REVIEWER-GUIDE-JA.md"
    # Guide is read by path/hash, not copied and silently treated as adopted.
    manifest = dict(
        preparation_version=VERSION,
        source_main_commit=source_commit,
        status="PILOT MATERIALS FREEZE CANDIDATE",
        final_frozen=False,
        protocol_version=PROTOCOL_VERSION,
        schema_version=SCHEMA_VERSION,
        builder_version=BUILDER_VERSION,
        selection_implementation_version=VERSION,
        selection_implementation_sha256=file_hash(__file__),
        codebook_candidate=definition.model_dump(mode="json"),
        codebook_candidate_hash=definition_hash(definition),
        pilot_protocol_hash=file_hash(V3 / "PILOT-PROTOCOL.md"),
        adjudication_rules_hash=file_hash(V3 / "ADJUDICATION-RULES.md"),
        bilingual_policy_hash=file_hash(V3 / "BILINGUAL-REVIEW-POLICY.md"),
        reviewer_guide_hash=file_hash(guide),
        pilot_a=selection,
        exclusion_manifest_hash=hashes["author_only/exclusions.json"],
        pilot_b_vignette_ids=[c["vignette_id"] for c in cases],
        pilot_b_authored_coverage=sorted({x for c in cases for x in c["author_key"]["coverage"]}),
        file_hashes=hashes,
        unresolved=[
            "Pilot A Japanese translations not prepared/verified/frozen",
            "Pilot B bilingual authoring requires human verification, not semantic validation",
            "reviewers unassigned; human authorization absent; access/share permissions unresolved",
            "Pilot B teaching reference requires human adoption before stage pilot",
            "public/source license and publication approval unresolved",
            "pilot packet freeze/independent ballots/calibration/clearance absent",
            "main30/28, IAA inclusion and v1.0 freeze unresolved",
        ],
        human_labels=0,
        pilot_human_review="NOT STARTED",
        main_human_review="NOT STARTED",
        real_translation_assets_frozen=0,
        reviewer_specific_packets_generated=0,
    )
    exclusive(destination / "pilot_materials_manifest.json", manifest)
    return manifest


def preservation_paths():
    tracked = subprocess.check_output(["git", "ls-files"], cwd=REPO, text=True).splitlines()
    paths = set(tracked) | set(read(V3 / "local/preservation-before.json"))
    for folder in (
        "experiments/epistemic-diversity/runs",
        "experiments/synthesis-evidence-preservation/runs",
        "experiments/synthesis-evidence-preservation/reports",
        "experiments/synthesis-evidence-preservation/data",
        "reports/hotpotqa-data",
    ):
        paths.update(
            p.relative_to(REPO).as_posix()
            for p in (REPO / folder).rglob("*")
            if p.is_file()
            and p.suffix not in {".pyc", ".db", ".sqlite", ".sqlite-wal", ".sqlite-shm"}
        )
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["snapshot", "verify", "prepare"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--catalogue")
    args = parser.parse_args()
    if args.command == "snapshot":
        values = {p: file_hash(REPO / p) for p in preservation_paths()}
        exclusive(args.output, values)
        result = dict(files=len(values), baseline_sha256=file_hash(args.output))
    elif args.command == "verify":
        baseline = read(args.baseline)
        missing = [p for p in baseline if not (REPO / p).is_file()]
        changed = [p for p, h in baseline.items() if p not in missing and file_hash(REPO / p) != h]
        result = dict(
            files=len(baseline),
            missing=missing,
            changed=changed,
            passed=not missing and not changed,
        )
        exclusive(args.output, result)
    else:
        result = prepare(args.output, args.catalogue)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
