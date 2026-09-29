# Pilot 2.4: common generation-budget and observation amendment

Prospectively written before any 2.4 research calls, under the user's authorization
to improve operational problems and proceed to Pilot completion (2026-09-29).

Protocol 2.3 stopped on a length-terminated worker response at approximately
431 seconds, not at its 600-second deadline. Previous synthetic diagnostics were
too small to establish compatibility with the failed workload. Recovery v2 uses
the exact saved worker input and a near-limit synthesizer input as a separately
labelled engineering reproduction. A positive gate does not establish reliability
or causal attribution; negative observations and historical failures are retained.

Changes applied equally to every worker and synthesizer in C2/C3:

- max_tokens **4096**, previously 2048. This is a changed generation control,
  not a claim that semantic budgets are identical across historical protocols.
- per-agent and HTTP deadline **1200 seconds**, previously 600. Upper bound,
  not fixed waiting time. No retry, JSON repair, fallback or partial resume.
- Capture reported response usage, finish reason and guarded explicit final-answer
  JSON prefix before rejection. No hidden reasoning text is persisted.

Unchanged: qwen3:14b, local endpoint, temperature 0, model-default thinking,
no tools, worker/model concurrency 1, benchmark 2.0.0, all six Pilot task IDs,
C2/C3, seed 20260928, one repetition, assignment/ordering, prompts, schemas,
context policies, artifact visibility, metrics, statistical definitions and
operational fail-stop. Incorrect answers remain research outcomes, not failures
to be repaired. The same frozen run_case implementation performs execution,
scoring and boundary audits. No old source or seal is rewritten.

Execution is enabled only after both representative 4096-token diagnostic cells
complete with schema-valid outputs, stop finish reason and valid usage. A new
freeze and binding seal the extension, base source, inputs and diagnostic gate.
Backend version/model digest must match the diagnostic. The binding is only for
runs/qwen3-14b-protocol24; its entry point is pilot24.py, not historical run.py.

Budget is shared with recovery-v2: 3 diagnostic + 48 Pilot calls, ceiling 60.
Record shared total separately from the expected 48 Pilot calls. The entire
12-run grid is required; no task substitution or exclusion. Stop at an operational
failure, retain it, and do not splice a subsequent cohort into this one.

Only after 12 succeeded records, 48 Pilot calls, zero errors and zero context/
result/gold leaks: analyze, generate figures and inspect human review in new
Protocol 2.4-specific output directories. This is a six-task, one-repetition
pilot, not evidence of general superiority of either condition. Historical
protocols and diagnostic cells must not be pooled in performance comparisons.

This preparation does not authorize main/full, new models or extra repetitions.
If it fails, another cohort requires an explicit prospective plan/budget within
the user's recovery scope; the consumed binding is never reused.
