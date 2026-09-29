# Prospective Protocol 3.0 — published HotpotQA distractor benchmark

User selected HotpotQA (distractor) on 2026-09-29. This replaces the active
synthetic benchmark, not its historical artifacts. No real generation is implied
by dataset import, Mock success or a source binding. Explicit real launch is gated.

## Published task and official endpoints

Source: https://hotpotqa.github.io/ and https://github.com/hotpotqa/hotpot.
Dataset: `hotpot_dev_distractor_v1.json`, official dev distractor, ten paragraphs
per question. Dataset CC BY-SA4.0; attribution and adaptation notice included.
Import exact question, title, sentence text/order, answer, and supporting_facts.
When the original CMU server is unavailable, `download --mirror` explicitly uses
namlh2004/hotpotqa HF commit7e54db4656209750ff487f6fdf8e39a66dba136b,
JSON SHA256e3da074df24e8369009918aa5cdbdd254dadcde4c63f7569d36afd6f2268caa8.
Record actual mirror URL and provenance; no automatic mirror fallback or claim
of byte identity to the unavailable upstream original. This does not change scoring.
Never convert to authored subject=value tasks, add synthetic inference rules,
or require our old canonical complete-success predicate.

Primary C3−C2 endpoint: official normalized answer token F1. Secondary answer EM,
supporting-fact EM/F1 and joint EM/F1. The byte-identical official evaluator is
pinned to upstream commit3635853403a8735609ee997664e1528f4480762a and SHA256
d35fc91a6db21d791dbdda11daf3856e9359f5701d54e3eefba20d88fecc02c0.
Only its ujson import is redirected to stdlib json in memory. No scoring changes,
LLM judge, flexible answer repair, or historical canonical-claim penalties.
Adapter tests verify normalization, yes/no handling, supporting-fact sets and joint scores.

## Prospective sampling and controls

Pilot six questions, selected before any generation. Public context must be
structurally valid, have ten distinct document titles, and serialize to at most
12000 AgentContext characters. Rank eligible IDs by SHA256("20260928:"+QA-ID),
take first six. Eligibility uses only question/context, never answer, support,
type, level or model success. Persist IDs, exclusion counts, source URL, raw hash,
public/gold hashes and official scorer identity. No truncating long documents.
This is a length-limited local dev Pilot, NOT official full-dev/test or leaderboard.
12000 chars is a public size proxy, not a tokenizer guarantee; real prompt usage
above4096 fails the native context guard, never silently drops an item.

C0: neutral single agent/full context, one call. C2: three diverse-role workers/
full context plus artifact-only neutral synthesizer, four calls. C3: three neutral
workers/disjoint document-preserving partitions plus same synthesizer, four calls.
One repetition, identical questions and public sentence IDs across conditions,
seed20260928, deterministic shuffled condition order. 18 runs/54 calls, hard60.
C1/C4 and Main are not launched. C2/C3 jointly vary role and access, not isolated
factorial main effects. C0 versus either multi-agent condition has different call budget.

Document assignment is seeded, greedily balanced by public sentence-text length;
all sentences in a document remain together. No gold relevance, importance or
supporting-fact oracle routing. Synthesizer sees only released worker artifacts;
final citation IDs are mapped back to original [title, zero-based sentence_index]
without looking at gold. Original recursive unknown-ID rejection and context-scoped
enum/maxItems citation constraints remain. No fictitious canaries inserted into
the corpus. Audit actual input projection and sentence-ID access independently
of accuracy; inferred correct answers are not themselves label leakage.

Qwen3:14b same manifest digest as previous Windows work, Ollama native /api/chat,
think:false, temperature0, num_predict4096, num_ctx8192, timeout1200,
worker/model concurrency1, no tools/retry/repair/resume. Answers are short spans/
yes/no; workers can return empty candidate answers when their evidence is insufficient.
Mock never reads gold and deliberately does not infer answers; Mock scores are
plumbing verification only and cannot be reported as model performance.

## Gates, analysis and limitations

Separate public/gold types/files. Conditions/provider receive PublicQuestion only.
Require checksummed dataset inventory, pinned evaluator, current-source 54-call
Mock, new source freeze, host preflight/version/digest binding, fresh SQLite budget
and new campaign directory. Fail-stop on runtime/transport/schema or access faults;
wrong answers alone are scored, not repaired or grounds for reselection.

Only complete 18-run/54-call cohorts permit official condition summaries, per-run
prediction export and review. Report paired differences on six QA IDs; exact
sign-flip p is exploratory, not evidence of equivalence. Tasks share Wikipedia
documents/entities and are not guaranteed independent. No population claims.
Public dev data may occur in model training; document-only instructions cannot
prove absence of memorized knowledge. No contamination-free claim or blind-test
score. HotpotQA measures multi-hop QA, not the old ten authored task families.
