# Research log

## 2026-09-29 JST — Protocol 2.4 pilot stopped on boundary validation

- Executed 4 runs / 15 Pilot calls (18 total including the 3-call diagnostic).
  First 3 runs succeeded. Fourth, v2-diagnosis-medium / C3, stopped partial at
  worker_1 with `unknown_evidence_reference`; its structured output cited `none`,
  not present in that worker's authorized context. Runtime fail-closed behavior
  is correct. This is invalid citation handling, not context leakage.
- Leakage checks in all 4 records: zero. Eight remaining runs unexecuted; campaign
  consumed with no retry/resume/task replacement. No performance analysis/figures.
- Full local results, calls and traces remain in Git-ignored runs/. The concise
  incident/provenance summary is docs/qwen3-14b-protocol24-operational-failure.md.
- 2.4 diagnosis improves one observed generation-limit failure but does not make
  the multi-agent pilot robust to unsupported model citations. Any further attempt
  requires a new predeclared protocol/binding/campaign.

## 2026-09-29 JST — representative diagnostic passed; new Pilot launched

- User authorized improving operational problems through Pilot completion.
  Predeclared recovery-v2: 3 real diagnostic + 48 Pilot calls, shared ceiling 60.
- Exact failed worker input reproduced length termination with max_tokens 2048;
  measured 2048 generated tokens, nonzero reasoning characters, zero final-content
  characters. Same input at 4096 produced schema-valid JSON in 2430 generated
  tokens. Near-limit synthesizer also passed. No hidden reasoning persisted.
- Source/input binding preceded diagnostic generation. Protocol 2.4 freeze and
  new binding preceded its separate real Pilot launch. Both conditions share
  4096 tokens / 1200s; all scientific factors other than generation budget stay
  fixed. This is a changed cohort, never pooled with failed historical attempts.
- Mock 2.4 validation: 12 succeeded runs / 48 calls, zero errors/leaks. Full
  pre-launch suite: 252 passed / 3 skipped; formatter/lint/strict types pass.
- All 2,805 historical protected files retain hashes. Old source and both old
  seals remain unchanged/valid. Pilot completion/results are still pending.

## 2026-09-29 JST — repeated-failure audit and offline recovery improvements

- Separated deadline failures (2.1/2.2), the corrected Ollama limit-field mismatch,
  and the observed length termination (2.3). The latter is not a 600-second timeout.
  No failed answer or reasoning/token allocation was reconstructed.
- The prior six-call diagnostic consumed only 422–472 generated tokens. Compared
  structural load against the failed request: 4 inference rules / 2 decision rules /
  14 premises versus at most 1 / 1 / 4. Small-fixture success cannot establish a fix.
- Added unsealed operational_recovery tooling, outside both archived source sets:
  exact public request fixture with provenance/hash, read-only workload audit,
  pre-rejection final-answer-prefix/usage capture and fake-only single-attempt executor.
  Hidden reasoning/prose/error bodies withheld; truncation and schema errors stay failures.
- Added 19 offline/fake HTTP tests covering unchanged requests, partial/complete JSON
  with length, timeout/cancel, usage unknowns, schema rejection, privacy guards,
  real-transport rejection, old paths and overwrite refusal. No new real call,
  retry, scientific protocol, condition analysis or push.
- Details and remaining limits: docs/operational-recovery.md. Scientific pilot
  reliability is still unestablished, not promoted from fake-test success.

## 2026-09-29 JST — authorized six-call real diagnostic completed

- User explicitly authorized implementation through real execution. Implemented
  independent token_budget.py with immutable synthetic plan, seal and new binding.
  Did not modify app/, scientific src/, benchmark, prompts or old campaigns.
- Fake HTTP validation and full suite passed: 225 tests / 3 external-service skips;
  formatter/lint/strict types pass. Then sealed source/plan before real generation.
- Executed exactly six serial calls in the fixed order, Thinking default,
  temperature 0, 600s deadlines, max_tokens 2048/4096. All six schema-valid / stop,
  no errors; 3116 input + 2640 generated = 5756 reported tokens, about 3m52s.
- Both ceilings completed all three small fixtures, with identical reported
  counts/lengths per pair. Failed-Pilot truncation was not reproduced; the
  predeclared criterion for proposing 4096 was not met. No reliability claim.
- Thinking lengths were measured without persisting text; reasoning-token split
  remained unknown. Recorded all journals, backend metadata and consumed budget.
- Both seals verify and all 228 protected hashes match. No added calls, retry,
  resume, new research protocol, Pilot, main/full, performance analysis or push.
  Detailed actual outcomes: docs/token-budget-diagnostic-results.md.

## 2026-09-29 JST — approved diagnostic planning, no implementation or execution

- Fixed an independent synthetic-input diagnostic proposal: three contexts,
  two total generation ceilings 2048/4096, one repetition, six calls maximum.
- Kept Thinking default, temperature 0, serial dispatch, no tools/retries and
  600s per-call deadlines. Seeded the predetermined pair order with 20260928.
- Authored JSON inputs/plan outside sealed source and benchmark; no failed-task
  replay or gold data. Artifact inputs are clearly labeled authored fixtures.
- Specified metadata-before-rejection logging, separate diagnostic truncation
  outcomes, fail-stop for other operational faults, unknown usage and incomplete
  cells, and descriptive-only decision criteria. Neither budget is proven reliable.
- No new source change, model call, Protocol 2.4, seal, binding or campaign.
  Implementation and real launch remain separate approval gates.
- Offline validation: 212 passed / 3 existing skips, formatter/lint/strict types
  pass, current freeze valid and all 228 protected hashes unchanged. No real calls.

## 2026-09-29 JST — protocol 2.3 failure diagnosis, no new generation

- Inspected saved five records / 19 journals: first four records succeeded, then
  v2-constraints-medium / C3 partial. Worker_0 failed once with output truncation
  after 431.35s; the other workers succeeded and synthesis was not dispatched.
- Distinguished length termination from deadline expiry. The failed HTTP envelope
  and token usage are unavailable, so thinking exhaustion is a hypothesis, not
  a recovered fact. Two successful calls used 2033/2025 of 2048 generated tokens.
- Consulted versioned official Ollama implementation and the Qwen3-14B model card;
  documented shared generation-budget/default-thinking and greedy-decoding risks.
  Neither temperature nor thinking nor any other generation setting was changed.
- Added unsealed offline diagnostics and a prospective metadata-only HTTP hook,
  tested using fake HTTP; it does not save hidden reasoning or change requests.
  It is not integrated into frozen execution without a future reviewed amendment.
- Preserved old and current campaign artifacts, scientific sources, bindings,
  seals and benchmark. No Protocol 2.4, performance analysis, figures or real
  generation is part of this improvement. Validation details are recorded in
  docs/protocol23-diagnostic-validation.md.

## 2026-09-29 JST — protocol 2.3 operational compatibility amendment

- Inspected the retained protocol-2.2 pilot: four runs / 16 calls, three successes,
  then v2-diagnosis-medium / C3 partial. Workers succeeded; synthesizer exceeded
  its 300s deadline. Journal recorded cancellation without a response. No
  performance comparison or plots followed the failed operational gate.
- Recorded separate failure documentation and protocol-2.3-amendment.md before
  implementation or any new generation. Preserved all old campaign/freeze bytes.
- Exactly two local corrections: deadline 600s and explicit `max_tokens=2048`.
  Generic runtime adapter defaults to the old parameter; the research profile
  chooses the compatibility field. Wire checks journal actual key/value before
  transport and reject mismatches rather than fallback. Thinking is unchanged.
- Scientific code, benchmark public/gold files, prompts and configs remain fixed;
  seed, six tasks, C2/C3, assignment/order, metrics and stopping rules are unchanged.
- Prepared new seal/binding/fresh campaign requirements. Neither partial resume
  nor a real execution is performed. Old cohorts are never pooled with 2.3.
- Mock and fake HTTP validation only; finalized commands, counts, preservation
  checks and regression equivalence are recorded in protocol-2.3-validation.md.

## 2026-09-28 — protocol 2.2 local Ollama operational recovery

- Inspected preserved runs/qwen3-14b only with read-only checks: 1 C2 run on
  v2-synthesis-easy, 3 calls, ~90.04s, 2 agent_timeout and 2 CancelledError journal
  entries. Recorded as operational failure; no paired research outcome claimed.
- Recorded protocol-2.2-amendment.md before named runs. Benchmark version/data,
  selected tasks, conditions, temperature/output tokens, prompts and seeds fixed.
- Added local-only worker scheduling and provider dispatch concurrency 1, timeout
  300s. Independent workers have no sibling context access or dependency edges;
  both C2 and C3 share scheduling. Latency/load effects remain disclosed.
- New local binding requires a nonexistent campaign root. Launch checks current
  freeze, bound root, profile/endpoint/settings and absence of prior artifacts.
  Prior seal/binding/failed campaign are preserved; no automatic resume.
- Tests initially exposed an async test-double mismatch with the synchronous
  MockProvider responder contract. Replaced the test double; Runtime unchanged.
- Final suite: 161 passed / 3 optional external-service checks skipped.
  Formatter/lint and both strict typing checks pass. Fake HTTP adapter tests
  verify the serial 48-call path at 300s, without accessing any real endpoint.
- New content seal created before named mock runs:
  64123f9c62f55a6c26dff30a582472fffbc8b02ede9a42a3c607fd8896a12154.
- Ran standard and local mock pilots separately, 12 runs / 48 calls each.
  Paired final outputs, assignments, quality and boundary metrics match. All
  succeeded. No inference about qwen3:14b quality follows from mock behavior.
- Compared all 77 saved file hashes: failed campaign (14 files) and benchmark-v2
  (63 files) unchanged byte-for-byte. No new real-model execution or binding.

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
