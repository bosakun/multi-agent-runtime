# Research log

## 2026-09-28 JST — protocol 2.1 pre-real correction and final validation

- Final review discovered that all canonical correct decision candidates were
  authored first. This distributional hint escaped literal-gold/solvability
  checks. Recorded protocol-2.1-amendment.md before the corrected named runs.
- Preserved the prior seal, mock records and exact source archive; verified all
  139 archived files against that seal. No prior result was deleted or relabeled.
- Public inference/candidate order now uses a task/seed-derived shuffle without
  gold access, identical across conditions. Fixed seed gives first/second counts
  16/14 full, 4/2 pilot. Did not select new tasks or reroll seeds to balance them.
- Static audit now reports these counts; tests check common order, reproducibility,
  no canonical-input mutation and variation across seeds. Scientific hypotheses,
  benchmark truth, roles, access, endpoints and paid selection remain unchanged.
- Created and verified current seal before execution:
  06e2b3ebac936e8cee2e8f506a74d46664342c9a2d1da2d5c698262a909dd041.
- Ran a fresh mock-v2p21-validation pilot (12 runs / 48 calls). After confirming
  runtime/schema/boundary checks, ran full (150 runs / 510 calls). All passed;
  final quality remained identical across conditions, as expected of this mock.
  This is not evidence of no real-model effect. No incomplete cells or boundary hits.
- Regenerated seven labeled figures, statistics and human-review reports under
  separate mock-v2p21 paths. No C2/C3 discordant success pair appeared in the mock.
- Formatter, lint, both typing checks pass; final suite 145 passed / 3 optional
  external checks skipped. Existing runtime and v1 benchmark hashes unchanged.
- No real credentials available, no real pilot/main, no remote push, no paper
  conclusion. Content/software ready; explicit model binding and credentials remain.

## 2026-09-28 JST — benchmark hardening / pilot-2 (before any real model)

- Preserved existing dirty worktree on research/epistemic-diversity. No branch
  replacement, destructive git command, remote push or app/ change.
- Recorded v2-design-amendment.md before the expanded benchmark implementation.
  RQ/H1–H5/C0–C4 unchanged; paid pilot limited to central C2/C3 to fit 48/60 calls
  while covering six different families. All-five-condition main is disabled.
- Authored 30 distinct configurations in ten structural families. Removed
  answer-bearing wording during pre-freeze prompt review; separated observation
  and validation canonical keys; corrected seven declared dependency depths to
  measured active inference depth. These are annotation/audit fixes, not selections
  based on a favorable condition score. No v1 result was overwritten.
- Static audit checks 180 seeded assignments, source importance/count balance,
  decision concentration, shortcuts, duplicates and gold isolation. No failing
  audit flags remain. Shared easy-control structures are disclosed, not concealed.
- Added valid fact/evidence/required-insight diversity, collective coverage gains,
  fixed-output provenance marginal support loss and explicit-unknown scoring.
  Observed worker coverage no longer disappears when synthesis fails. This metrics
  change is versioned 2.0.0; old v1 records are retained unchanged.
- Corrected statistical units to family-level paired means for v2, retaining task
  diagnostics and refusing mixed cohorts. No independent-pair binary p-value is
  emitted for multiple related cases in a family. No role-effect conclusion drawn.
- Added immutable content sealing and actual model/endpoint pre-call binding.
  Real pilot requires a complete 48-call remaining budget, stops on operational/
  boundary failure, retains semantic errors, journals every reserved call and
  writes an evaluator-side human report. Model secrets never enter saved metadata.
- All 77 research tests pass, including fake HTTP (not real model) provider-path
  tests. Existing offline runtime: 67 passed / 3 optional external checks skipped.
- Sealed benchmark/protocol/source before named v2 execution. Hash:
  66653c194ab214816d03d823c07a0ecaf3e58fb40d4eb478ffb5ed651f163121.
- Named v2 mock pilot: 12 runs / 48 calls; inspected successful runtime/schema and
  zero boundary counts. Then named full: 150 runs / 510 calls. All final mock tasks
  passed, no incomplete full blocks. Full and pilot are separate analyses.
- Generated human-readable reports and seven mock-labeled SVGs. No credentials
  available; no paid pilot or main and no paper conclusion. Real-model results pending.
- Verified old v1 results via their saved analysis digest and old benchmark/app
  files via stored hashes. Freeze remains unchanged after analysis/documented status.

The previous "no amendments" entry below describes v1 only. The explicit v2
amendment above supersedes its execution scope without retroactively changing it.

## 2026-09-27 — repository inspection and pre-execution plan

- Clean main at a63b676; created local research/epistemic-diversity branch.
- Reviewed Runtime architecture, domain schemas, ContextBuilder, AgentExecutor,
  DAG orchestration, message routing, SQL repository, HTTP provider and tests.
- Reuse these boundaries by importing app; do not import experiment code from app.
- Real-provider environment credentials absent. No real API calls authorized by
  configuration or possible from the available environment.
- Fixed docs/research-plan.md before benchmark generation, implementation or runs.
- Existing model adapter and policies appear sufficient; no Runtime change planned.

## 2026-09-28 JST — implementation, validation and offline execution

- Implemented the fixed five-condition protocol using existing ContextBuilder,
  AgentExecutor, Orchestrator, SQLRepository and provider interface. No app/ edits.
- Chose JSON condition files instead of YAML to avoid an extra dependency.
  SVG generation uses the standard library rather than installing a plotting stack.
  These are serialization/presentation choices, not hypothesis or metric changes.
- Authored six templates × four variants, producing 24 public/gold task pairs.
  No LLM generated the benchmark. Public candidate rules list alternatives, not
  the hidden true assignment. Oracle routing and correlated premises are limitations.
- Added SQLite call reservations (including transport failures), seeded assignments,
  actual-context/raw-structured-response audit and per-run trace persistence.
- First research-test pass found five test-fixture errors (missing required
  WorkflowState.nodes); fixed the fixtures, not Runtime behavior. Final 26 tests pass.
- Ran named mock pilot: 2 tasks, five conditions, one repetition, 10 runs, 34 calls.
  Checked complete records, successful runtime statuses and zero boundary/gold hits
  before proceeding. Semantic task quality was not an exclusion criterion.
- Ran named mock full: 24 tasks, five conditions, two repetitions, 240 runs,
  816 calls. Combined mock ledger consumed 850/1000 explicitly permitted offline
  calls. No paid calls, no ablations, no judge. Test fixtures are not study results.
- Full phase has zero incomplete blocks and no failures. All conditions have equal
  final coverage/success; only expected structural overlap and resource differences
  appear. No directional C2/C3 final failure case exists. Reported exactly as such.
- Generated task-level descriptions, paired bootstrap/sign-flip analysis, Holm
  corrections, exact McNemar, CSV, compact records and five clearly labeled mock SVGs.
- Reviewed primary sources for ReConcile, iAgents, Diversity of Thought, DMAD and
  AgentPanel; references and scope distinctions are in related-work.md.
- Existing offline Runtime suite: 67 passed, three optional service tests skipped.
  Runtime regression does not claim a new live PostgreSQL or provider validation.
- Wrote methodology, limitations, findings, Japanese summary, protocol abstract and
  paper outline. No real paper-results section was fabricated. Root README only
  gains a small independent research link. Branch remains local; no push.

## Protocol amendments

None to task selection, hypotheses, primary metrics, contrasts or statistical
methods after execution. Mock full includes pilot IDs by design and is analyzed
separately. Execution machine timestamps use UTC (2026-09-27); this log's dates use
JST (2026-09-28). Future scientific design changes must be a new dated amendment.
