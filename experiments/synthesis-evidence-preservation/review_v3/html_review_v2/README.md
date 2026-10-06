# Guided Review UI v2

This version adds a guided, local-only presentation and input layer on top of the v3 canonical JSON and ballot models. JSON remains the source of truth. The UI preserves source text and fixed Japanese translations, shows Japanese first, and opens English originals on request. Labels keep their existing canonical values; Japanese explanations are display text only.

The builder accepts one phase-limited prepared Pilot A source, one canonical v3 packet, or the existing Pilot B synthetic source array. Every output bundle has an `index.html`, `review.html`, and `overview.html`. A bundle contains data for its declared phase only. `review.html` carries several cases only when they belong to the same source file and same phase. No answer key is read by this renderer. Pilot B material keeps its synthetic marker.

## Guided work

The overview explains R1, R2, registry freeze, and S1–S5 in plain Japanese. The index shows phase purpose, case aliases, position, progress, and a start button. Each case presents its question, reference facts, and observed information in separate columns on desktop and stacked cards on narrow screens. At the top it states the purpose, permitted material, comparison, question to answer, and material not to use at that stage.

English originals are inside `<details>` and remain in the same phase file. The rendered page reminds reviewers that English is the semantic source of record. Stage labels show a plain Japanese description and the unchanged canonical code.

R1/R2 expose the existing Registry fields through ordinary form controls. S1–S5 expose the existing v3 form labels, reason/ambiguity note, and optional evidence sentence IDs. `unclear` requires a note. The export uses the v3 Registry wrapper or the existing `{stage, annotation}` form array and can be checked with `validate_ballot.py`. No new semantic ballot schema is introduced.

## Browser storage and privacy

The page autosaves drafts in browser `localStorage`, namespaced by the phase source hash. This stores annotations and pseudonymous Reviewer ID only in that browser profile; it does not send data anywhere. Use **このcaseの下書きを消す** for the current case. On a shared computer, also clear the browser's file-page/site storage after exporting. If the browser blocks localStorage for `file:` URLs, the page stays usable for the open tab and offers JSON export; save the ballot before closing. The exported JSON is a separate file and should be transferred into the authorized reviewer-specific private location.

No server, network dependency, external font, account, or database is used. HTML contains phase-scoped materials required to move among that phase's cases. The coordinator-only `render-manifest.json` contains hashes and source pointers; do not distribute it to Reviewers.

## Prepare artificial previews

Only synthetic examples and the already-prepared Pilot B artificial vignettes are used:

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_review_v2/examples.py experiments/synthesis-evidence-preservation/review_v3/local/guided-review-v2-preview-001
```

Open `artificial-registry-tutorial/R1/index.html` for the invented registry demo, or `pilot-b-synthetic-training/S1/index.html` through `S5/index.html` for the 16 synthetic training vignettes. Each stage has its own source and output folder. These are preparation previews, not review authorization.

## Build authorized local material

Use only the authorized single-phase JSON source and, when required, its already frozen translation asset. Pick a fresh destination under `review_v3/local/`:

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_review_v2/renderer.py --source <stage-limited.json> --phase S1 --destination experiments/synthesis-evidence-preservation/review_v3/local/<new-batch>/S1
```

For Pilot A or a canonical packet, add `--translations <frozen-TranslationAsset.json>`. Open the destination's `index.html`; the same phase's `review.html` provides next/previous case navigation and ballot export. Validate an exported stage ballot with:

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_review_v2/validate_ballot.py --ballot <exported.ballot.json> --phase S1
```

Verify a bundle against its recorded source, translation, renderer, and HTML hashes with:

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_review_v2/audit.py experiments/synthesis-evidence-preservation/review_v3/local/<new-batch>/S1
```

The renderer refuses overwrite and confines repository outputs to the ignored `review_v3/local/` namespace. It does not lock ballots, authorize disclosure, or start a review.

## Status

### Fact-centred stage screens (v2.1)

S1–S4 and S5a show one fixed fact alongside the actual same-stage prose,
then one Japanese question and canonical-label choices. Previous/next moves
between existing annotation units; it does not create new facts or paths.
Internal IDs are confined to coordinator JSON and a details panel. A sentence
picker records evidence pointers without requiring typed sentence IDs.

S5b remains a separate, existing path-level support judgment: the predetermined
fact combination and received evidence are displayed without asking the reviewer
to construct a path. It must not be replaced with per-fact correctness alone.
S1 still uses the registered supporting material and actual-input record, not
external knowledge. S3 identity alias remains structural NA.

The preparation tasks R1/R2 are deliberately separate: they require humans to
construct the reference facts before stage review. The renderer never does this.

PILOT MATERIALS PREPARED / PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED / REAL HUMAN LABELS = 0 / NOT FINAL-FROZEN. No real translation, human annotation, adjudication, or experiment was conducted for v2.
