# Protocol 2.4 Qwen3 pilot stopped on an invalid evidence reference

Recorded 2026-09-29 JST. This is an operational boundary failure. Do not include
this incomplete cohort in performance comparisons or analyze C2 versus C3.

## Outcome

- Model: `qwen3:14b`; local Ollama 0.34.4.
- Protocol 2.4; benchmark 2.0.0; C2/C3; six fixed pilot tasks; seed 20260928;
  one repetition; temperature 0; default model thinking; max_tokens 4096;
  timeout 1200 seconds; worker/model concurrency 1/1; no tools or retries.
- Four task-condition runs were started; 15 Pilot calls were made. Including the
  three diagnostic calls, the shared budget consumed 18 of 60 calls.
- The first three task-condition runs succeeded. The fourth,
  `v2-diagnosis-medium / C3`, ended partial after worker_1 failed. It made three
  calls; its synthesizer was not dispatched. The remaining eight runs were not
  attempted.
- Run error: `unknown_evidence_reference`. The AgentExecutor rejected a returned
  evidence ID that was not present in worker_1's authorized context. The model
  response was syntactically valid JSON, but referenced the literal ID `none`.
  The context contained three actual evidence IDs and did not contain `none`.
  This was an invalid model citation caught by the runtime's information boundary,
  not evidence leakage or token truncation.
- Context leakage, result leakage and gold leakage in the four completed run
  records are all zero. The failed run remains partial and is not a successful
  paired result.

The runtime correctly failed closed instead of accepting an unsupported citation.
No retry, output repair, task substitution, analysis or performance figure was
generated. Do not edit Protocol 2.4's frozen prompts, schema, evaluation or
failure record after seeing this output.

## Preserved artifacts

The local campaign directory is Git-ignored to avoid publishing live run files;
its contents remain on the machine and were not deleted or overwritten:

- `runs/qwen3-14b-protocol24/binding.json`
- `runs/qwen3-14b-protocol24/pilot/results.json`
- `runs/qwen3-14b-protocol24/pilot/traces/d17bdc7183334daeaf732e01c9eb8041.json`
- `runs/qwen3-14b-protocol24/pilot/call-journal/`
- `runs/qwen3-14b-protocol24/pilot/http-observations/`

The offending worker response and available generation metadata are in the trace
and corresponding HTTP observation. Hidden reasoning text was never written into
the record. This committed incident summary records the error and provenance;
the full local trace remains available for authorized follow-up.

## What this establishes

The generation allowance correction passed its representative diagnostic and
allowed the earlier worker request to complete with 2430 generated tokens. It
did not prevent the separate failure mode seen here: a worker can return a
schema-valid structure containing an invalid evidence reference. The runtime
boundary detected it during the real multi-agent run. No conclusion about
relative C2/C3 task performance follows from this stopped pilot.

Any next Pilot must use a new prospectively reviewed protocol and a new binding
and campaign. A follow-up should examine whether the structured output contract
can constrain evidence IDs to the current AgentContext before publication, while
preserving fail-closed validation. The observed invalid output must remain an
operational failure; it cannot be repaired retroactively into a result.
