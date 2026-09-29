# Active benchmark: HotpotQA (distractor development set)

The new research entrypoint is **hotpot.py**, not the historical synthetic run.py.
The user selected HotpotQA (distractor) on 2026-09-29. Historical synthetic
benchmarks, README, freezes, code and results remain unchanged for reproduction.
They are not the active benchmark and are never pooled into this cohort.

Use [Protocol 3.0](docs/protocol-3.0-hotpotqa.md) for the current plan and caveats.
The published corpus and official evaluator replace authored canonical tasks and
canonical-claim scoring. Primary endpoint is official answer F1; answer EM,
supporting-fact and joint scores are reported separately.

From native Windows PowerShell at repository root:

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py download
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py prepare-data
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py plan
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py mock
```

These commands do not generate model answers. `download` retrieves the official
development corpus; data and generated artifacts remain under Gitignored reports/.
Existing destinations are rejected. No train/test mixing or answered-task filtering.

If the original CMU host is unavailable, explicitly use `download --mirror`.
It retrieves an identified third-party JSON mirror pinned to commit and published
SHA256, records its actual URL, and does not claim upstream byte identity without
an upstream checksum. Dataset provenance/this limitation remain in the manifest.

For a separately approved fresh real Pilot, start/keep the research Ollama server,
ensure ollama is on this child shell's PATH, then use `bind` followed by
`run --approve-real`. Native Ollama needs no OpenAI API key. Do not change Codex
authentication or use `OPENAI_API_KEY=ollama` to authenticate Codex.

Pilot: six public-length-eligible questions, C0/C2/C3, 18 runs/54 calls, hard budget60.
C0 measures full-evidence single-agent capability; C2/C3 retain role/access factors.
No automatic Main, retries, output repair, resume, or retrospective reselection.
