# READY FOR REAL PILOT — software/content ready; credentials and model binding required

Real-model results pending. No real-provider credentials were available during
preparation. No paid experiment or main experiment has been executed.

Content: benchmark 2.0.0 / protocol 2.1, 30 tasks / ten families. Fixed pilot: six tasks, C2/C3,
one repetition, seed 20260928, **48 calls** / 12 runs. Default ceiling **60**.
Exact selection/reasons: [real-pilot-plan.md](docs/real-pilot-plan.md).
No automatic retries, judge calls, regeneration ablations or main execution.
Current seal: `freezes/benchmark-2.0.0-protocol-2.1.json`. The superseded protocol-2
seal is archival, not the current executable freeze. Candidate-order correction
is documented in [the amendment](docs/protocol-2.1-amendment.md).

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
