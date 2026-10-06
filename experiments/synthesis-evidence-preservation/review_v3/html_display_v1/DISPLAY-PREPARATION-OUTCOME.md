# Static HTML display preparation outcome

Audited base main snapshot: `f72cfc8248fca612f42b18168050cb954968c24f`。これは作業開始時のsnapshotであり、永続的な「latest main」の指定ではない。

## Implementation / local examples

`renderer.py`（`static-html-display-v1.0.0`）はcanonical JSONのread-only表示projection。原文・固定訳を変えず、phase別allowlistでfuture/private fieldを拒否する。HTMLにはJavaScript、外部依存、author key、個人判定票を入れない。manifestはcoordinator専用でありReviewerへ共有しない。

生成物はすべてGit-ignoredの`review_v3/local/html-display-v1/`内に保存した。

- `synthetic-preview-002/`: 完全人工R1/R2およびS1〜S5例。架空の訳metadataはtest fixtureであり、人間承認ではない。
- `pilot-b-preparation-002/S1/`〜`S5/`: 既存の16人工vignettes × 5stage = 80 case HTML。同stageのみのindex、case HTML、render manifestを各folderへ生成。
- 実Pilot A: 固定日本語訳が存在しないためHTML未生成。実訳を作ったり、英語のみへ無断fallbackしたりしていない。

Reviewerには許可されたstageの`index.html`とcase HTMLだけを渡す。共通表示からR2の個人locked R1票は除外し、既存workflowに従い当該本人だけへ別資料として提示する。生成は開示認可・lock・review開始を意味しない。

## Mechanical verification

- review_v3 suite: **177 passed**（既存143 + 新規34）。Ruff format/checkもpass。
- disclosure、answer-key leakage rejection、HTML escaping、同一入力から同一bytes、manifest/HTML hash、原文・訳pointer/hash、上書き拒否をsynthetic fixturesで確認。
- Pilot B全5stageで各16件の再生成byte一致・text pointer/hash照合auditがpass。
- 人工R1およびPilot B S1をlocal browser screenshotで目視確認。質問card、日本語→英語、文書/sentence ID別表示を確認した。意味annotationはしていない。
- renderer source fingerprint: `ab8cd2907586cb09653a0d2e700a4105bd1194ee6fdcc0894cdcc63266cc8ad5`。Python/CSSと使用helperのbyte hashを含む。各生成HTMLのhashはlocal manifestに保存。

## Preservation / status

作業前snapshotとのbyte照合で既存**5,916 files: changed 0 / missing 0**。既存pilot preparationの**82 files: changed 0 / missing 0 / added 0**。Study 1/2、historical Protocol、freeze、旧kit・票・manifest、Pilot A selected 6 IDs、Pilot B canonical materialは変更していない。

PILOT MATERIALS PREPARED / PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED / REAL HUMAN LABELS = 0 / NOT FINAL-FROZEN。

実翻訳、Reviewer assignment、Human Review、semantic registry construction、adjudication、研究統計、LLM/Ollama requestは行っていない。Pilot A表示には今後、stage-limitedな実日本語訳の作成・人間確認・固定が必要。資料開示には既存のhuman authorizationとprogressive-disclosure lockが引き続き必要。
