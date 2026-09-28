# Pre-execution amendment: benchmark 2.0.0 / pilot protocol 2

2026-09-28 JST. Written before v2 benchmark generation or model execution.
The research question, H1–H5 and C0–C4 interventions are unchanged. Existing v1
benchmark files and mock results are historical artifacts and must not be deleted
or relabeled. No real-model conclusions will be written in this phase.

## Changes authorized by the benchmark-hardening request

- Author 30 cases in ten structural families, three difficulty tiers per family.
  Facts no longer change in correlated triples. Cases have manually specified
  conclusions and required insights, public alternative rules and private support
  annotations. Reuse typed schemas with backward-compatible fields, not app changes.
- Inspect solvability, instruction-only/single-document shortcuts, duplicates,
  relevance/importance balance and diverse structural signatures before freezing.
  Use lightweight lexical similarity as a flag, not a measure of reasoning quality.
- Add evidence/fact/required-insight uniqueness and overlap separately; collective
  coverage gain; fixed-final-output leave-one-worker-out provenance support loss.
  The last is explicitly NOT an LLM regeneration ablation or causal attribution.
- Correct the old failure convention: observed worker evidence recovery is not
  erased merely because later synthesis fails. Failed final quality remains zero;
  completeness and failure accounting are separate. Version the metrics.
- Pilot six preselected families/difficulties, C2 and C3 only, one repetition:
  6 × (3 workers + 1 synthesizer) × 2 = 48 calls, default ceiling 60.
  All five conditions would require 102 calls, incompatible with that ceiling.
  C0/C1/C4 stay implemented and are checked in full mock validation. This pilot
  cannot answer P2–P5 and is a feasibility check, not the main experiment.
- Real main/full execution is disabled in this iteration. No automatic escalation
  from pilot. A model/endpoint binding and verified content freeze must precede
  paid calls. No credentials are currently present; no model name will be guessed.
- Use family-level paired resampling as primary for v2 (average repetitions,
  then tasks within family); show task-level differences descriptively. With only
  six pilot families, uncertainty/power remain limited. Keep v1 analysis intact
  for saved v1 records; never combine versions/providers/models in one analysis.
- Freeze benchmark, task selection, prompts, metrics/source, protocol and hashes
  after audit fixes, BEFORE the named v2 mock pilot/full and any real pilot.
  Later fixes require an explicit amendment and a new freeze, not an overwrite.

## Proposed pilot selection (metadata only, before outcomes)

v2-synthesis-easy; v2-diagnosis-medium; v2-constraints-medium;
v2-contradiction-hard; v2-missing-easy; v2-causal-hard.
Six distinct families; two easy, two medium and two hard; one repetition;
seed 20260928. Selection is not changed based on mock or real task scores.
