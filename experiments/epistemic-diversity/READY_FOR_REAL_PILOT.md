# READY FOR REAL PILOT — software/content ready; credentials and model binding required

Comparative real-model results pending. The preserved qwen3:14b protocol-2.1
attempt failed operationally; see docs/qwen3-14b-operational-failure.md.
No protocol-2.2 real run has been executed or authorized during this implementation.

Content: benchmark 2.0.0 / protocol 2.2, 30 tasks / ten families. Fixed pilot: six tasks, C2/C3,
one repetition, seed 20260928, **48 calls** / 12 runs. Default ceiling **60**.
Exact selection/reasons: [real-pilot-plan.md](docs/real-pilot-plan.md).
No automatic retries, judge calls, regeneration ablations or main execution.
Current seal: `freezes/benchmark-2.0.0-protocol-2.2.json`. The superseded protocol-2/2.1
seal is archival, not the current executable freeze. Candidate-order correction
is documented in [the amendment](docs/protocol-2.1-amendment.md).

## Local Ollama recovery (requires authorization to run)

The local profile pins worker/model concurrency 1, timeout 300s, temperature 0
and maximum output 2048. Binding requires a new campaign root that does not yet
exist. Do not reuse `runs/qwen3-14b` or its binding. Example setup/binding below
performs no model generation; launch is a separate explicitly authorized step.

```bash
export MODEL_BASE_URL="http://127.0.0.1:11434/v1/"
export OPENAI_API_KEY="ollama"
uv run python experiments/epistemic-diversity/run.py verify-freeze
uv run python experiments/epistemic-diversity/run.py bind-model \
  --model qwen3:14b --execution-profile local_ollama \
  --campaign experiments/epistemic-diversity/runs/qwen3-14b-protocol22 \
  --output experiments/epistemic-diversity/runs/qwen3-14b-protocol22/binding.json
```

The key here is a local compatibility placeholder, not a cloud credential.
After explicit approval, the exact launch command is:

```bash
uv run python experiments/epistemic-diversity/run.py run \
  --provider real --model qwen3:14b --execution-profile local_ollama \
  --phase pilot --timeout 300 --temperature 0 --max-output-tokens 2048 \
  --binding experiments/epistemic-diversity/runs/qwen3-14b-protocol22/binding.json \
  --campaign experiments/epistemic-diversity/runs/qwen3-14b-protocol22
```

An existing root, stale seal/binding, different bound root or prior artifacts
block execution. No command above has been executed for the real model here.
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
  --output experiments/epistemic-diversity/runs/real-v2/binding.json
uv run python experiments/epistemic-diversity/run.py run \
  --provider real --model "$MODEL_NAME" --phase pilot \
  --binding experiments/epistemic-diversity/runs/real-v2/binding.json \
  --campaign experiments/epistemic-diversity/runs/real-v2
uv run python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/real-v2/pilot/results.json \
  --output experiments/epistemic-diversity/results/real-v2-pilot
uv run python experiments/epistemic-diversity/run.py figures \
  experiments/epistemic-diversity/results/real-v2-pilot/analysis.json \
  --output experiments/epistemic-diversity/figures/real-v2-pilot
```

Inspect the binding before launch. It records actual model ID, endpoint, settings,
selection and content seal without a secret. Changing settings/endpoint/seed after
binding or changing source/benchmark/protocol after content freeze is rejected.
The branch may still have uncommitted work; the result records actual parent commit
AND dirty state/file hashes. Commit the reviewed files before a public paid cohort
if desired; committing unchanged bytes does not invalidate the content seal.

## Expected outputs (not a promise of correct answers)

At most 12 executed records / 48 attempted calls; possible fewer on operational
failure. Each record includes benchmark and metrics versions, git commit/source
hash, condition/task, role/partition maps, settings, output, metrics and errors.
`pilot/runtime.sqlite`, `pilot/call-journal/`, `pilot/traces/`, `pilot/results.json`
and `pilot/pilot-human-review.md` preserve the run. Analysis writes compact records,
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
