# Pilot materials preparation outcome

Audited base main snapshot: `f03dd0ccf869b902da4285ffae904164f8799513` (includes the required merge). New work branch: `prep/human-review-pilot-materials`. This SHA is a historical preparation base, not a permanently latest HEAD statement.

## Pilot A

Local source: `reports/hotpotqa-data/hotpot_dev_distractor_v1.json`, 7,405 questions; SHA256 `e3da074df24e8369009918aa5cdbdd254dadcde4c63f7569d36afd6f2268caa8`, matching the saved provenance/verification receipt. No network dataset download or replacement.

Unique exclusions: 30; eligible IDs: 7,375. Main30, Study2 main24/smoke, historical Pilot6, old review calibration2 and old-kit calibration aliases are explicitly represented as overlapping groups in the local exclusion manifest. Old-kit aliases were matched using the frozen audit's ID-and-seed algorithm, not question content. No additional real codebook case is documented; human disclosure of unrecorded prior cases remains a preflight blocker.

Salt: `human-review-pilot-v1:`. Rank: `SHA256(UTF8(salt + QA_ID))`, ascending hex. Eligible list canonical SHA256: `ca1335df414948d8afc68486ba5e300b0ebe1e79358023866b8eabc01414338f`. Exclusion list canonical SHA256: `4f13113f974bb7328bc2b28fc1b4238587283b698d94790d1551618af40dd47c`. Canonicalization is sorted unique IDs, compact JSON, UTF8. File byte hashes are separate and recorded in the manifest.

Selected order:

1. `5adddb415542992200553b61`
2. `5a74c2bd5542996c70cfadda`
3. `5ab431d855429942dd415ed2`
4. `5a865cac55429960ec39b675`
5. `5a7ed2c655429930675135e5`
6. `5ae5064e5542993aec5ec113`

Content, gold, model results and failure patterns did not enter selection. The selected rows were projected only after selection. No real facts/support sets/paths/requiredness judgments were generated.

## Saved material and candidate

Ignored local root: `review_v3/local/pilot-materials-v1/prepared-20261006-002/`. See [README](README.md) for R1/R2, separate translation worklists, S1–S5 synthetic sources, author-only answer key and six empty log/profile/authorization/clearance templates. Version `001` is an untouched working candidate from before lint/guard changes; use `002`, not `001`.

Pilot B: 16 wholly artificial bilingual vignettes. Authored coverage includes semantic boundaries, alternative/external-premise paths, path-conditional requiredness, every publication state, artifact/supplementary/both routes, cascade, bridge omission, reflected/contradicted final fact and complete/partial/unsupported support. Coverage here describes authored teaching intentions, **not validated human calibration outcomes**. Answer keys have intended labels, Codebook rule IDs, explanations and neighboring-label counterexamples; they are not in reviewer sources.

Local full manifest byte SHA256: `9bdb9714d8cce6d40e89d92d759551c5c2b2ad222f2f954fe9d4d1b8cb91e0c8`.
[Public metadata manifest](pilot_materials_manifest.json) records all 40 material byte hashes, selected IDs/ranks, codebook/protocol/policy hashes and unresolved items. It intentionally omits raw/gold/source/key content and the full local codebook definition; its byte hash is therefore different from the local full manifest.

Artificial authoring catalogue (ignored local): `review_v3/local/pilot-materials-v1-authoring/catalogue.json`; byte SHA256 `c2d03f11cd8aaa04d60697399a4708e62dbb98dcd7caef4b144f9958099ebf73`. Preserve/backup local private preparation assets separately; a public checkout alone does not contain them. Publication permission has not been assumed.

## Mechanical verification and preservation

- Human Review v3 suite: **143 passed** (existing 128 plus 15 new mechanical/synthetic tests).
- New code Ruff: passed.
- Final local integrity report: `review_v3/local/pilot-materials-v1-integrity-final.json`; all 40 material hashes matched, selection reproduced, exclusion groups checked, R1/R2 whitelist and stage-limited worklists checked, no author keys in Pilot B sources, final output absent before S5.
- Pre/post preservation: **5,909 files**, missing 0, changed 0. Baseline/report: `review_v3/local/pilot-materials-v1-preservation-before.json` and `...-after.json`. Baseline byte SHA256: `082cc29308d5e03bfb7d22046b4ece05dab988e253053f1d0695bc69e5cbed4f`. Includes tracked historical protocols/results/freeze and local old kits/forms/manifests/campaign/source assets. No old hash was replaced.
- Existing tracked files were not edited. Existing untracked mock result directories were left alone. Real/private preparation source and synthetic author-only keys remain Git-ignored.

## State and human prerequisites

CODEBOOK CANDIDATE / PILOT MATERIALS PREPARED / PILOT MATERIALS FREEZE CANDIDATE.
PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED.
REAL HUMAN LABELS = 0 / REAL TRANSLATION ASSETS FROZEN = 0 / NOT FINAL-FROZEN.

Before human pilot: verify source-sharing permission; check unrecorded prior case exposure; assign real reviewers and record disclosures; settle optional third adjudicator; prepare/verify/fix identical Pilot A Japanese translations from stage-limited English sources; human-check Pilot B bilingual material/teaching premises; approve separate-stage disclosure and packet hashes; complete human pilot authorization. Main30/28, IAA inclusion and Codebook v1.0 remain undecided.

No human review, semantic annotation of real cases, real registry/path discovery, adjudication, IAA, lineage analysis, real translation, LLM/Ollama experiment, Study1/2 rerun or final freeze was performed. No commit/push/PR was requested in this preparation task.
