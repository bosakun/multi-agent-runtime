# Recovery v2: prospective engineering diagnostic and Pilot gate

Authorized on 2026-09-29 by the user's request to improve problems and reach pilot
completion. No historical run is retried, resumed, overwritten or pooled.

First execute **three diagnostic calls**, separately from scientific results:

1. Exact saved Protocol 2.3 failed worker request (journal 0017), max_tokens 2048.
2. Same request, max_tokens 4096. Verify wire bodies match except max_tokens.
3. Exact saved near-limit synthesizer request (journal 0008, previously 2033
   generated tokens), max_tokens 4096.

All use qwen3:14b, loopback Ollama, temperature 0, default thinking, no tools,
no retries, model concurrency 1, **1200-second deadline**. This new deadline is
common to all diagnostic cells, not an amendment to historical campaigns.
Record reported usage, finish reason and guarded final-answer prefix before
provider rejection. Never store hidden reasoning. Input/schema/prompt are copied
only from saved authorized agent requests, not global state or hidden gold.

The first cell's length termination is expected diagnostic evidence and permits
the second cell; any other operational failure stops. Both 4096 cells must be
schema-valid, report stop and generation usage within the requested limit before
a new Pilot can be prepared. No claim that this proves general reliability.
Even if the 2048 cell also succeeds, use 4096 for the new cohort as a prospective
headroom policy, not a claim of causally established superiority.

If the gate passes, freeze **pilot-2.4** separately: max_tokens 4096, deadline
1200 seconds, unchanged benchmark 2.0.0, all six tasks, C2/C3, seed 20260928,
one repetition, default thinking, temperature 0, serial workers/models, same
roles/prompts/context policies/metrics/order and strict fail-stop. Both worker
and synthesizer in both conditions get the same budget. This changes a generation
control; do not describe it as scientifically identical to 2.3 or pool cohorts.

Budget: shared durable counter, MAX_MODEL_CALLS default/hard ceiling 60;
3 diagnostic + 48 Pilot = **51 planned calls**. No full/main, additional
repetition, different model or unconstrained recovery loop. If the Pilot fails,
retain it and diagnose; any further cohort needs a new prospective budget/plan,
not an unrecorded continuation of this one.

Diagnostic campaign: runs/qwen3-14b-recovery-v2.
Prospective pilot campaign: runs/qwen3-14b-protocol24.
Old freeze/source files remain valid; extensions live in operational_recovery.
Seal diagnostic inputs/source before dispatch; seal the new pilot source and
settings after the diagnostic gate, before any of its 48 calls.
