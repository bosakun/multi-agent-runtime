# Current experiment: HotpotQA 30 questions, C0-C4

User explicitly selected 30 questions x five conditions on 2026-09-29.
This supersedes the Pilot-only scope in ACTIVE_BENCHMARK.md without changing its
frozen source. Read [Protocol 3.1](docs/protocol-3.1-hotpotqa-main.md).

The complete planned experiment is 150 unique cases / 510 native model calls.
Protocol 3.0's completed Pilot supplies 18 cases / 54 calls; it is not rerun.
`hotpot_full.py` completes the remaining 132 cases / 456 calls under a separate
closed ledger, freeze and campaign. No automatic retry/resume or overwrite.

Main inference uses 24 new questions. All30 summaries are cumulative exploratory
results. This is a public-length-selected dev subset, not the full official
HotpotQA benchmark or a leaderboard/contamination-free test.

Historical synthetic results remain intact and separate. No commit/push is implied.
