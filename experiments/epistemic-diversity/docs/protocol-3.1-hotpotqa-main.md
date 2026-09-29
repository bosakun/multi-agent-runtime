# Protocol 3.1: HotpotQA 30-question, five-condition completion

2026-09-29, prospective before additional real calls. User explicitly selected
"30問×5条件まで進める": 150 cases / 510 total native Qwen3 calls, including
the already completed Protocol 3.0 Pilot's 18 cases / 54 calls. Do not regenerate
these 18 cases. Preserve their source, freeze, binding, ledger and results.

## Cohort and fixed execution

Use exactly the same downloaded dev distractor corpus, scorer, public length /
structure eligibility, SHA256(seed:QA-ID) ranking, seed20260928, prompts, schemas,
document partitioning, model digest, native wire controls and access enforcement.
Take the first 30 eligible IDs, not 30 outcome-selected tasks. The first six must
match the existing Pilot exactly, including public/gold file hashes. Original
sentences are neither truncated nor simplified; selection uses no private label.

Complete C1/C4 for the six Pilot questions (12 cases / 48 calls), and execute all
five conditions on the next 24 questions (120 cases / 408 calls). This fresh
additional campaign has 132 cases / exactly 456 planned calls, hard limit456.
Combined with the Pilot ledger54, the real HotpotQA ceiling is510, not516 or an
unbounded recovery allowance. Errors consume reservations; no retry/refund/resume.
Require the complete integral Pilot, zero access faults, matching source/data,
all-condition current-source Mock, new source freeze and host/backend binding.
The new campaign does not share a writable runtime/ledger with the Pilot.

C0: single neutral worker / full raw context, one call.
C1: three neutral workers / full context plus artifact-only neutral synthesis.
C2: three diverse-role workers / full context plus the same synthesis.
C3: three neutral workers / disjoint documents plus the same synthesis.
C4: the C2 roles / C3 documents plus the same synthesis. Each multi-agent case
uses four serial calls. Role assignment is identical across C2/C4 per question.
The former Pilot's C0/C2/C3 condition order is preserved; new question blocks
shuffle all five conditions deterministically. Six completion blocks shuffle
only C1/C4. Later execution of C1/C4 on Pilot questions is a phase confound.

Qwen3:14b digest bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8,
Ollama0.34.4 observed at Pilot, think:false, temperature0, context8192,
num_predict4096, input guard4096, timeout1200, concurrency1, no tools/repair.
Host/model/backend drift blocks launch. Fail-stop on runtime/schema/transport or
access failure; wrong answers are scored and never cause task replacement.

## Analysis fixed before the new 24-question experiment

Official answer token F1, EM, supporting-fact and joint metrics replace all old
authored canonical metrics. Primary P1 is C3 minus C2 answer F1 on the 24 *new*
questions, with per-QA paired differences, mean, 5000 task bootstrap draws,
20,000 seeded sign flips and conditional 95% interval. Use seed20260928.
Secondary P2 C2-C1, P3 C3-C1, P4 C4-C3, P5 C3-C0 use the same endpoint; report
Holm correction across those four secondary p values. Other endpoints and the
interaction (C4-C3)-(C2-C1) are descriptive. No endpoint promotion after results.
Temperature0 / one repetition is not a stochastic robustness experiment.

Report all 30-question five-condition official summaries separately as a
cumulative exploratory cohort. Do not label the 30-question combined analysis
as entirely prospective: six answers were already generated before this plan,
and some conditions on those six were executed in a later phase. Primary and
secondary inference use only the 24 new complete five-condition blocks.

Artifact review, citations/gold-support recall, citation uniqueness, redundancy,
overlap, unauthorized input IDs, token totals, model-call latency and raw sentence
exposures are descriptive. Reporting diagnostics were added after Pilot launch,
but before this new experiment. Citations matching gold support do not validate
the surrounding statement; disjoint access mechanically forces raw-ID uniqueness.
Unknown pricing stays null, and model-call latency is not end-to-end runtime.
Export official prediction JSON, per-case CSV, visible saved-output review,
observed discordant C2/C3 cases and labeled SVG figures. Review generation is not
independent human validation. Preserve source/data/result input hashes.

## Scope and completion evidence

Completion requires exactly 150 distinct QA/condition cases and 510 journaled
real calls across the two immutable phases, all expected cells, official scorer
recomputation, ledger/journal/results agreement, no access violations, unchanged
freeze/binding, saved GPU residency observation, tests and historical preservation
audit, condition summaries, comparisons, plots and final limitations report.
Any failure leaves the planned grid incomplete and cannot be called "all done".

30 publicly length-limited dev questions are not the 7405-question full official
benchmark, a leaderboard score or an independently sampled population. They may
share Wikipedia entities and appear in model training. No contamination-free or
causal cognitive-independence claim. Per-call controls do not equalize total input
or compute, especially C0 versus multi-agent conditions. Existing synthetic
cohorts are never pooled into this HotpotQA experiment. No other model, ablation,
repetition, benchmark download, commit or push is included in this authorization.

## Native Windows entrypoint

New entrypoint: `experiments/epistemic-diversity/hotpot_full.py`.
Prepared data: `reports/hotpotqa-data/prepared-thirty`. Additional Mock:
`reports/hotpotqa-main-mock`. Real additional campaign:
`experiments/epistemic-diversity/runs/hotpotqa-protocol31-qwen3-14b-windows`.
Old `hotpot.py` remains the immutable Pilot entrypoint.

```powershell
$env:PYTHONUTF8 = '1'
$env:MAX_MODEL_CALLS = '456'
# Add installed Ollama and .venv/Scripts to this child shell's PATH.
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py prepare-data
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py plan
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py mock
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py bind
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py verify
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py run --approve-real
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot_full.py analyze
```

Every command must succeed before the next. Existing data, Mock, freeze, campaign
and analysis destinations are refused; these commands are not a rerun recipe.
The real launch was explicitly requested for this user-selected completion scope.
Codex keeps ChatGPT authentication; native Ollama does not require an API key.
