# Protocol 2.1 amendment — candidate-order confound

2026-09-28 JST, after protocol-2 mock validation but BEFORE any real-model call.
No real result has been observed. Benchmark meaning/version (2.0.0), gold, task
selection, roles/access manipulations, metrics and seeds are unchanged.

## Defect and correction

Final pre-real review found a positional shortcut in authoring: the first public
decision candidate was the correct one for every task. Static solvability and
literal-gold audits did not detect this distributional hint. Perfect deterministic
mock scores neither revealed nor justified ignoring it. Correcting this is a
confound reduction independent of which experimental condition performs better.

The Context construction now deep-copies public instructions and shuffles both
inference rules and decision candidates with
`Random(SHA256([task_id, seed, "public-criteria-order"]))` (the project's canonical
JSON digest). It does not inspect gold. The same task/seed yields the same public
order for C0–C4 and every worker/synthesizer, so this does not change role or access
factors. The public-rule mock already uses fixed-point evaluation, so rule order
does not change its meaning or support validity.

With the already selected seed 20260928, correct-candidate positions are 16 first
and 14 second across 30 tasks; pilot is 4 first and 2 second across six tasks.
This is randomized, not perfectly balanced. Neither task selection nor seed was
changed to tune those counts. Future repetitions keep their preplanned seeds.
Difficulty/position effects remain limitations; no claim of zero bias is made.

## Preservation and new freeze

The old seal `freezes/benchmark-2.0.0.json` and named
`runs/mock-v2-validation` / `results/mock-v2-*` artifacts are retained unchanged.
`freezes/protocol-2-source.tar.gz` preserves the exact files needed to verify and
reproduce that old seal in a separate extraction directory. Current source must
not be falsely presented as matching the old seal.

The new immutable seal is `freezes/benchmark-2.0.0-protocol-2.1.json` and protocol
version `pilot-2.1`. Named validation will use separate `mock-v2p21-*` paths.
The new seal must precede those named runs and all real calls. No paid main is
enabled and no prior record is deleted or relabeled. The paper remains pending.
