# STOPPED — Protocol 2.4 campaign is consumed

The user authorized operational improvements through Pilot completion on 2026-09-29.
The representative diagnostic passed, but the Protocol 2.4 pilot stopped after
4 runs / 15 Pilot calls when C3 worker_1 returned evidence ID `none`, which was
outside its authorized context. The runtime rejected it as `unknown_evidence_reference`.
See [the incident report](docs/qwen3-14b-protocol24-operational-failure.md).
No analysis or performance comparison was made. The remaining eight runs were
not executed. The binding and campaign are consumed; do not rerun or resume them.

The following commands document the historical recovery procedure only. A new
protocol and campaign must be frozen after reviewing this failure.

New entry points (do not repeat a consumed phase):

```bash
uv run python experiments/epistemic-diversity/recovery_live.py verify
# Three-call diagnostic was launched separately; do not launch it again.
# Only after its recorded gate passes and before the new Pilot starts:
uv run python experiments/epistemic-diversity/pilot24.py prepare
uv run python experiments/epistemic-diversity/pilot24.py verify
uv run python experiments/epistemic-diversity/pilot24.py run --approve-real
```

New settings: qwen3:14b / local_ollama, max_tokens 4096, deadline 1200 seconds,
temperature 0, thinking default, worker/model concurrency 1/1. These apply to
both C2/C3; benchmark/tasks/prompts/roles/metrics are unchanged. All source changes
are additive extensions: historical run.py and both existing seals still verify.
New prospective campaign: `runs/qwen3-14b-protocol24`; consumed paths are refused.
See [Protocol 2.4 amendment](docs/protocol-2.4-amendment.md).

## Historical: STOPPED — protocol 2.3 campaign must not be rerun

The authorized Qwen3 pilot stopped after **5 runs / 19 calls**, on
`v2-constraints-medium / C3 / worker_0` with `provider_output_truncated`.
The 600s deadline was not reached. See the
[failure investigation](docs/qwen3-14b-protocol23-operational-failure.md).
No performance analysis, figures, retries or resumes are authorized. The binding
and consumed campaign remain immutable. A new prospective protocol/approval is
required before any additional real generation. The metadata observer is not
enabled in the frozen runner and does not establish model reliability.

The independent [token-budget diagnostic](docs/token-budget-diagnostic-results.md)
was separately authorized and completed: 6 calls, both ceilings 3/3 successful.
It did not reproduce truncation or establish a sufficient benchmark token budget.
Its campaign is consumed and must not be rerun. No new research Pilot is ready
or authorized; do not adapt the historical commands below to change its settings.

Everything below records the **historical pre-launch instructions**. Do not
repeat its real command, regenerate its binding, or reuse its campaign.

## Historical: ready for real pilot — protocol 2.3

Comparative real-model results pending. The preserved qwen3:14b protocol-2.1
attempt failed operationally; see docs/qwen3-14b-operational-failure.md.
Protocol 2.2 also stopped operationally after four runs / 16 calls; see
docs/qwen3-14b-protocol22-operational-failure.md. No protocol-2.3 real generation
has been executed during this implementation.

Content: benchmark 2.0.0 / protocol 2.3, 30 tasks / ten families. Fixed pilot: six tasks, C2/C3,
one repetition, seed 20260928, **48 calls** / 12 runs. Default ceiling **60**.
Exact selection/reasons: [real-pilot-plan.md](docs/real-pilot-plan.md).
No automatic retries, judge calls, regeneration ablations or main execution.
Current seal: `freezes/benchmark-2.0.0-protocol-2.3.json`. The superseded protocol-2/2.1/2.2
seal is archival, not the current executable freeze. Candidate-order correction
is documented in [the amendment](docs/protocol-2.1-amendment.md).

## Local Ollama recovery (requires authorization to run)

The local profile pins worker/model concurrency 1, timeout **600s**, temperature 0
and semantic maximum output 2048, sent explicitly as **`max_tokens=2048`**.
Thinking stays at the backend/model default. No fallback or retry is performed.
Binding requires a new campaign root that does not yet exist. Do not reuse
`runs/qwen3-14b`, `runs/qwen3-14b-protocol22`, their children or either binding.
Example setup/binding below
performs no model generation; launch is a separate explicitly authorized step.

```bash
export MODEL_BASE_URL="http://127.0.0.1:11434/v1/"
export OPENAI_API_KEY="ollama"
export MODEL_NAME="qwen3:14b"
export MAX_MODEL_CALLS=60
uv run python experiments/epistemic-diversity/run.py verify-freeze
uv run python experiments/epistemic-diversity/run.py bind-model \
  --model qwen3:14b --execution-profile local_ollama \
  --campaign experiments/epistemic-diversity/runs/qwen3-14b-protocol23 \
  --output experiments/epistemic-diversity/runs/qwen3-14b-protocol23/binding.json
```

The key here is a local compatibility placeholder, not a cloud credential.
If the new binding already exists, inspect it; **do not regenerate it**.
The bind command intentionally refuses an existing root or output.
After explicit approval, the exact launch command is:

```bash
uv run python experiments/epistemic-diversity/run.py run \
  --provider real --model qwen3:14b --execution-profile local_ollama \
  --phase pilot --timeout 600 --temperature 0 --max-output-tokens 2048 \
  --seed 20260928 --repetitions 1 \
  --binding experiments/epistemic-diversity/runs/qwen3-14b-protocol23/binding.json \
  --campaign experiments/epistemic-diversity/runs/qwen3-14b-protocol23
```

A reused root, stale seal/binding, different bound root or prior artifacts
block execution. **The real launch command has not been executed.**
Software tests prove the serialized field; real backend enforcement is not yet
observed. Truncation or timeout still triggers the unchanged fail-stop policy.
The generic commands below apply to the standard profile at non-Ollama endpoints.

## Required environment

- Python 3.12+ and the root locked development dependencies (`uv sync --group dev`).
- `OPENAI_API_KEY`: valid credential for the authorized compatible endpoint;
  supply securely in the environment, never in a command argument or checked-in file.
- `MODEL_NAME`: an explicitly chosen compatible model ID. It must support JSON-schema
  Chat Completions, temperature 0 and a 2048 completion-token limit. No model name is
  guessed here; transport/schema rejection stops the pilot instead of changing settings.
- `MODEL_BASE_URL`: optional; default `https://api.openai.com/v1/`. HTTPS required
  except explicit localhost. Do not include query keys, userinfo or fragments.
- `MAX_MODEL_CALLS`: optional, default 60. The complete 48-call pilot must fit the
  remaining campaign budget. API costs are independent of Codex/Plus usage.

## Exact commands (repository root)

After securely exporting the credential and setting `MODEL_NAME`:

```bash
uv sync --group dev
uv run python experiments/epistemic-diversity/run.py verify-freeze
uv run python experiments/epistemic-diversity/run.py plan --phase pilot
uv run python experiments/epistemic-diversity/run.py bind-model \
  --model "$MODEL_NAME" \
  --output experiments/epistemic-diversity/runs/real-v2p23/binding.json
uv run python experiments/epistemic-diversity/run.py run \
  --provider real --model "$MODEL_NAME" --phase pilot \
  --binding experiments/epistemic-diversity/runs/real-v2p23/binding.json \
  --campaign experiments/epistemic-diversity/runs/real-v2p23
```

Only after all 12 runs succeed, 48 calls are accounted for, errors are empty and
context/result/gold leaks are zero, analysis/figures may be run. For the local
campaign, use its own `results/qwen3-14b-protocol23-pilot` and
`figures/qwen3-14b-protocol23-pilot` destinations, never older output paths.
Generic standard-profile analysis examples:

```bash
uv run python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/real-v2p23/pilot/results.json \
  --output experiments/epistemic-diversity/results/real-v2p23-pilot
uv run python experiments/epistemic-diversity/run.py figures \
  experiments/epistemic-diversity/results/real-v2p23-pilot/analysis.json \
  --output experiments/epistemic-diversity/figures/real-v2p23-pilot
```

Inspect the binding before launch. It records actual model ID, endpoint, settings,
selection, backend token-limit strategy and content seal without a secret.
Changing settings/endpoint/seed after
binding or changing source/benchmark/protocol after content freeze is rejected.
The branch may still have uncommitted work; the result records actual parent commit
AND dirty state/file hashes. Commit the reviewed files before a public paid cohort
if desired; committing unchanged bytes does not invalidate the content seal.

## Expected outputs (not a promise of correct answers)

At most 12 executed records / 48 attempted calls; possible fewer on operational
failure. Each record includes benchmark and metrics versions, git commit/source
hash, condition/task, role/partition maps, settings, output, metrics and errors.
`pilot/runtime.sqlite`, `pilot/call-journal/`, `pilot/traces/`, `pilot/results.json`
and `pilot/pilot-human-review.md` preserve the run. Each real call journal also
records `backend_request.token_limit_fields` from the actual HTTP body before
transport; for local execution it must be exactly `{"max_tokens": 2048}`.
Thinking override fields must be absent. Analysis writes compact records,
CSV, statistics, incomplete/planned-but-unexecuted cells and a human review report.
Cost is null without verified pricing; failed transport usage may be unknown.

Incorrect answers remain in the data and do not stop the pilot. A transport,
schema, runtime or boundary violation stops after its case is saved; concurrent
workers already dispatched still count. Do not delete those records or choose
replacement tasks. Existing phases/bindings are never overwritten. A failed pilot
needs an explicit documented recovery/new freeze and remaining budget review.

**STOP after human review.** Paid main/full are disabled in this iteration.
All-condition expansion requires a separately authorized plan/budget; passing
pilot plumbing checks is not evidence that either condition is superior.
