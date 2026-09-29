# Protocol 2.3 validation

Validation uses the installed locked development environment. No Ollama generation
or external model request is performed. Fake HTTP fixtures use `httpx.MockTransport`.
Live-service tests remain opt-in and are not evidence of backend enforcement.

Commands from the repository root:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
MYPYPATH=experiments/epistemic-diversity/src uv run mypy --strict \
  experiments/epistemic-diversity/src experiments/epistemic-diversity/run.py
uv run pytest -q tests
uv run pytest -q experiments/epistemic-diversity/tests
uv run python experiments/epistemic-diversity/run.py verify-freeze
```

An already installed environment may use `.venv/bin/ruff`, `.venv/bin/mypy`,
`.venv/bin/pytest` and `.venv/bin/python` without invoking dependency resolution.
Never run opt-in live tests for this amendment validation.

To reproduce the offline local regression, choose a new nonexistent campaign:

```bash
uv run python experiments/epistemic-diversity/run.py run \
  --provider mock --execution-profile local_ollama --timeout 600 --phase pilot \
  --campaign experiments/epistemic-diversity/runs/my-protocol23-mock
uv run pytest -q experiments/epistemic-diversity/tests/test_protocol23.py \
  -k mock_scientific_outputs_match_archived_protocol22
```

## Guarantees exercised

- Standard deadline 90s and original HTTP limit key; local deadline 600s,
  worker/model concurrency 1/1, `max_tokens=2048`, no thinking overrides.
- Both keys together, missing/wrong key or wrong limit are rejected before HTTP
  transport; the inspected wire fields are retained even for rejected attempts.
- Old freezes, mismatched bindings, old campaign roots/children, existing phase
  outputs and reused local roots are refused before dispatch.
- The full fake local pilot exercises 12 runs / 48 calls without network access.
- Current local Mock outputs, all worker payloads, assignments, condition order,
  quality/diversity/leakage metrics and calls match archived protocol-2.2 Mock
  records. Wall time is not required to match and cannot show an LLM effect.
- Historical campaigns, archives, benchmark, prompts and configs are checked
  against pre-edit raw-byte SHA256 maps in `results/protocol23-preservation.json`.
  Scientific sources additionally match the protocol-2.2 content seal.

## Execution record

Runtime: **68 passed / 3 skipped** (optional external PostgreSQL/live-server
checks). Research: **122 passed**. Combined: **190 passed / 3 skipped**.
Formatter checks all 143 Python files; lint and strict typing pass (44 runtime
and 18 research source files). New freeze verification passes:

`fb661f49dd4b98276ae1594ded53b3aca53ac92b91d01e6b9d26a5913872e361`

Before edits, the then-valid protocol-2.2 source ran a separate 12-run / 48-call
offline local baseline in a fresh temporary directory. After the new freeze,
`runs/mock-v2p23-local/pilot/results.json` completed 12 runs / 48 Mock calls.
Every corresponding final output, worker payload, assignment, status, condition
order, non-resource quality/diversity/leakage metric and call count matches.
The automated regression also compares the retained published 2.2 Mock records,
so it is reproducible without that temporary baseline. Results are summarized
in `results/protocol23-mock-regression.json`. All literal boundary/gold hits are
zero. These two named baseline/current validations consume 96 **offline** calls;
test-fixture invocations are separate, not real experiments.

Preservation verified: protocol 2.1 campaign **14 files**, protocol 2.2 campaign
**30 files**, benchmark 2.0.0 **63 files**, prompts **7 files**, configs **5 files**,
existing freeze/archive artifacts **4 files**. All retain their pre-edit hashes.
The three protected directory aggregate SHA256 values are:

- 2.1: `2bc076f8ba086ba000c7e60188d536f13380e1a95985117710cb2cecb196bfa0`
- 2.2: `f67564b84a0c85cc2d181840167e322005b7b70562aa8b6cb94c1044bde94677`
- Benchmark: `f4284f7f5b5e33f771e0b3549bb786bf3efa4984cc82aaacd280dc1b807b4ded`

Aggregate = SHA256 of sorted-key JSON mapping repository-relative path to its
raw-byte SHA256. This is distinct from the runtime's text-content seal digest.
The preservation manifest records each individual file hash and after-checks.

New local binding was generated without provider contact and verified against the
new freeze. Digest:
`dfb01ea587f9b782e2779b2df88d935f0c73c3991a28f27b3341e31d108fecb7`.
The fresh real campaign contains **only binding.json**, no phase or budget database.
No real generation, server probe, recovery, resume, main/full or figure generation
was performed. No real-model performance conclusion belongs in this report.

## Changed and new files

Only `app/llm/openai_provider.py` changes in runtime source: generic explicit limit
field selection, with the default and all prompt/response behavior preserved.
`tests/integration/test_provider.py` checks default preservation and body equality
apart from the selected key.

Within `experiments/epistemic-diversity/`:

- `src/epistemic/models.py`: 600s local invariant, derived field strategy, wire audit data.
- `src/epistemic/provider.py`: pre-transport body checks and journal checkpoint.
- `src/epistemic/runner.py`: explicit adapter configuration, hook, metadata, old-path guard.
- `src/epistemic/cli.py`: local default deadline 600s.
- `src/epistemic/freeze.py`: protocol 2.3 seal/binding controls and historical-path refusal.
- `tests/test_protocol22.py`: retained serial/boundary guards updated for current profile,
  plus fake local truncation/fail-stop verification.
- `tests/test_protocol23.py`: preservation, compatibility, old-seal/binding/path rejection,
  fixed scientific sources and archived Mock equivalence.
- `docs/protocol-2.3-amendment.md`: prospective correction and unchanged-factor declaration.
- `docs/qwen3-14b-protocol22-operational-failure.md`: separate factual failure record.
- `docs/experiment-freeze.md`, `docs/real-pilot-plan.md`, `docs/methodology.md`,
  `docs/limitations.md`: current operational settings and cohort separation.
- `docs/experiment-log.md`, `docs/protocol-2.3-validation.md`: implementation/validation log.
- `README.md`, `READY_FOR_REAL_PILOT.md`, `STATUS.md`: current readiness and exact commands.
- `freezes/benchmark-2.0.0-protocol-2.3.json`: new immutable content seal.
- `results/protocol23-preservation.json`, `results/protocol23-mock-regression.json`:
  integrity and offline equivalence evidence, not research findings.
- `runs/qwen3-14b-protocol23/binding.json`: new local-only pre-execution binding
  (gitignored); no real results. `runs/mock-v2p23-local/` contains the fresh
  gitignored offline validation outputs.

Existing source outside these files, old freezes, old campaigns and scientific
definitions are not rewritten. Existing untracked `.DS_Store` files remain untouched.
