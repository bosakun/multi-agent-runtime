# Validation record

## Current: protocol 2.1 / benchmark 2.0.0 — 2026-09-28 JST

The pre-real candidate-order correction is described in protocol-2.1-amendment.md.
New freeze (sealed before named runs):
`06e2b3ebac936e8cee2e8f506a74d46664342c9a2d1da2d5c698262a909dd041`.
The old seal and all old named records remain intact. All 139 prior sealed files
were checked against protocol-2-source.tar.gz. Old v1 and protocol-2 record digests
match their saved analysis inputs; 85 v1 benchmark/app files match original hashes.

Final validation: **145 passed / 3 skipped** (78 research, 67 runtime passed).
132 Python files pass formatter check; lint passes; strict runtime typing passes
44 files and research typing passes 18 files. Freeze verification and git diff
whitespace checks pass. No new dependencies, app/ edits, real calls or push.
The skipped tests require optional live PostgreSQL/provider services.

Current named cohort: pilot 12 runs / 48 mock calls, then full 150 runs / 510
mock calls. All 162 runs completed, all final task checks passed, no literal
context/result/gold leak was detected, and no planned cell is missing. The seven
regenerated SVGs and human reports are pipeline validation, not empirical LLM
results. Statistics use six pilot family units and ten full family units.

Commands executed for the current cohort (after freeze and verification):

```bash
.venv/bin/python experiments/epistemic-diversity/run.py run \
  --provider mock --phase pilot \
  --campaign experiments/epistemic-diversity/runs/mock-v2p21-validation --max-model-calls 600
.venv/bin/python experiments/epistemic-diversity/run.py run \
  --provider mock --phase full \
  --campaign experiments/epistemic-diversity/runs/mock-v2p21-validation --max-model-calls 600
.venv/bin/python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/mock-v2p21-validation/pilot/results.json \
  --output experiments/epistemic-diversity/results/mock-v2p21-pilot
.venv/bin/python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/mock-v2p21-validation/full/results.json \
  --output experiments/epistemic-diversity/results/mock-v2p21-full
.venv/bin/python experiments/epistemic-diversity/run.py figures \
  experiments/epistemic-diversity/results/mock-v2p21-full/analysis.json \
  --output experiments/epistemic-diversity/figures/mock-v2p21-full
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
MYPYPATH=experiments/epistemic-diversity/src .venv/bin/mypy --strict \
  experiments/epistemic-diversity/src experiments/epistemic-diversity/run.py
.venv/bin/pytest -q tests experiments/epistemic-diversity/tests
.venv/bin/python experiments/epistemic-diversity/run.py verify-freeze
git diff --check
```

The following sections are historical. Do not rerun their freeze commands over
existing files, or mistake their source seal for current executable source.

## V2 benchmark hardening — 2026-09-28 JST

After the expanded design, formatter/lint and both typing checks passed. Combined
suite: **144 passed / 3 skipped**, comprising 77 research tests and 67 runtime
tests; optional live PostgreSQL/API tests skipped. No app/ modifications or new
dependencies. Prior v1 public/gold files and app sources match hashes retained in
the v1 manifest; old v1 records match their prior analysis input digest.

Pre-execution static audit: 30 cases, ten families, ten per difficulty; 180 seeded
assignments; no reported errors. Minimum decision support 4–7 documents; count
stratum imbalance ≤1, importance range ≤3, decision-support concentration ≤2/3.
28 coarse graph signatures, with two deliberately disclosed easy-control pairs.
No lexical duplicate flag at the predeclared 0.65 trigram-Jaccard threshold.
These checks do not prove semantic independence or empirical difficulty.

Sealed content hash:
`66653c194ab214816d03d823c07a0ecaf3e58fb40d4eb478ffb5ed651f163121`.
Freeze verification ran before and after named v2 execution. Fake-HTTP fixtures
test the actual compatible provider adapter, fixed generation parameters, full
48-call pilot path, 429 stop with three in-flight worker reservations, rejection
of a 47-call pilot budget, version recording and human-readable reports.

Named runs (not test fixtures): v2 pilot 12 runs / 48 mock calls, then full 150
runs / 510 mock calls. No incomplete full blocks; all final tasks passed; zero
context/result/gold hits. Statistics use ten family units for 30 full tasks.
No actual paid endpoint was called; no real main experiment. Cost stays null.
Reports are under results/mock-v2-pilot and results/mock-v2-full; seven SVGs under
figures/mock-v2-full. These numbers validate plumbing, not scientific hypotheses.

```bash
.venv/bin/python experiments/epistemic-diversity/run.py benchmark
.venv/bin/python experiments/epistemic-diversity/run.py audit
.venv/bin/python experiments/epistemic-diversity/run.py freeze
.venv/bin/python experiments/epistemic-diversity/run.py verify-freeze
.venv/bin/python experiments/epistemic-diversity/run.py run \
  --provider mock --phase pilot \
  --campaign experiments/epistemic-diversity/runs/mock-v2-validation --max-model-calls 600
.venv/bin/python experiments/epistemic-diversity/run.py run \
  --provider mock --phase full \
  --campaign experiments/epistemic-diversity/runs/mock-v2-validation --max-model-calls 600
.venv/bin/python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/mock-v2-validation/pilot/results.json \
  --output experiments/epistemic-diversity/results/mock-v2-pilot
.venv/bin/python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/mock-v2-validation/full/results.json \
  --output experiments/epistemic-diversity/results/mock-v2-full
.venv/bin/python experiments/epistemic-diversity/run.py figures \
  experiments/epistemic-diversity/results/mock-v2-full/analysis.json \
  --output experiments/epistemic-diversity/figures/mock-v2-full
```

The freeze command was executed once; repeating it intentionally refuses overwrite.
Use verify-freeze for reproduction. Existing campaign phases likewise refuse overwrite.

## Historical v1 validation

2026-09-28 JST. Local branch `research/epistemic-diversity`, parent commit
`a63b676fdcf6ddeff8a6e71b96638f8c25d53f13`. No remote push. Research sources remain
outside `app/`; the only modified pre-existing tracked file is the root README's
small Research / Experiments section.

## Commands actually executed

From the repository root, with the existing Python 3.13 virtual environment:

```bash
uv sync --group dev
uv run python experiments/epistemic-diversity/run.py plan --phase main --repetitions 2
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
MYPYPATH=experiments/epistemic-diversity/src .venv/bin/mypy --strict \
  experiments/epistemic-diversity/src experiments/epistemic-diversity/run.py
.venv/bin/pytest -q tests experiments/epistemic-diversity/tests
```

Results: 106 Python files already formatted; lint passed; runtime typing passed
for 44 files; research typing passed for 13 files. Combined tests: **93 passed,
3 skipped** (67 runtime + 26 research tests passed). The skipped checks require
live API/PostgreSQL services; they were not started for this research-only change.
The initial sandbox denied uv's default cache path; after explicit permission,
the unmodified `uv sync --group dev` and `uv run ... plan` commands succeeded.
No dependencies were added to root pyproject.toml or uv.lock.

Research tests cover configuration controls, deterministic/randomized role
assignment, balanced disjoint partitions, public/gold separation, actual runtime
contexts, detached state, supported-citation metrics, overlap, contradictions,
paired statistics, repetition aggregation, incomplete pairs, budget concurrency
and restart, actual parallel scheduling, artifact-only synthesis, rejected-output
leakage detection, failed calls, serialization, pilot gate and SVG generation.

## Named validation campaigns

```bash
.venv/bin/python experiments/epistemic-diversity/run.py benchmark
.venv/bin/python experiments/epistemic-diversity/run.py run \
  --provider mock --phase pilot \
  --campaign experiments/epistemic-diversity/runs/mock-validation --max-model-calls 1000
.venv/bin/python experiments/epistemic-diversity/run.py run \
  --provider mock --phase full --repetitions 2 \
  --campaign experiments/epistemic-diversity/runs/mock-validation --max-model-calls 1000
.venv/bin/python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/mock-validation/pilot/results.json \
  --output experiments/epistemic-diversity/results/mock-pilot
.venv/bin/python experiments/epistemic-diversity/run.py analyze \
  experiments/epistemic-diversity/runs/mock-validation/full/results.json \
  --output experiments/epistemic-diversity/results/mock-full
.venv/bin/python experiments/epistemic-diversity/run.py figures \
  experiments/epistemic-diversity/results/mock-full/analysis.json \
  --output experiments/epistemic-diversity/figures/mock-full
```

Pilot: 10/10 succeeded, 34 calls, zero boundary hits; eligibility checked before
full. Full: 240/240 succeeded, 816 calls, no incomplete blocks. Total ledger:
850/1000, entirely offline. No scientific inference is drawn from the perfect mock
scores. Real model experiments were not executed because credentials were absent.
Use a fresh campaign name to reproduce; the existing phase directories are
intentionally protected from overwrite. Tests create temporary campaigns that are
not added to the research sample.
