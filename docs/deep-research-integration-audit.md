# Deep Research integration audit

2026-10-02。documentation / research designのみの整合性監査。外部recommendationをrepositoryのhistorical factより優先するものではない。新しい実験、人手判定、統計計算、kit実装はしていない。

## 入力・監査snapshot

Report A `Multi-agent-既存研究.md`（846行、SHA256 `172b8486ac1c1f5da2a2fc55f8b25fb75a444a8185481d58adc63a70d142269f`）とReport B `deep-research-方法論整理.md`（1,832行、SHA256 `d277f3fe0aa15abaa7f906ce05c92d3dbc276bad9a59bc2489c06c9d17861666`）を全文参照した。レポート自体・個人のローカルpath・private資料をGitへ追加しない。レポートの引用は一次資料で同定し、非公開の内部citation tokenを流用しない。

Git fetch後のmainの**audited base snapshot**は`432a5ec85e78be31508ce250df6396ad7105041e`。編集開始前の研究branch snapshot `8c9ea24fb0df6809077491206fb3637fa67f36ca`とtree contentsは一致した。branch移動・history書換はしていない。このSHAは監査時点の識別子で、永続的なlatest/main HEADの研究事実ではない。

research-level要約、Study 1 Protocol 3.0/3.1/3.2・final Windows outcome・保存失敗/復旧記録・旧related work・current paper drafts、Study 2 README/PLAN/REVIEW/HANDOFF/OPERATIONS/freeze/final outcome、段階別案と依存監査、旧kit builder・空票・manifestsを照合した。実入力・Artifact照合のコードも確認した。[旧依存監査](../experiments/synthesis-evidence-preservation/docs/review-stage-amendment-and-kit-impact.md)は当時の記録として残す。

## 統合判定

| Deep Research recommendation | Current repository state | 判定 | Proposed change | Historical/freeze impact | Reason |
| --- | --- | --- | --- | --- | --- |
| A: Role / actual Information Access / observable lineageが主題 | framing v1はRole/Epistemicと「抽出・利用」を使う | needs revision | [framing v2](research-question-and-contributions.md)で3主題と観測範囲を明示 | 現行解説のみ。Protocol条件名は保持 | epistemicを人格・モデル多様性と混同させない |
| A: Runtimeはtreatment integrity | v1もRuntime単体新規性を主張しないが実入力lineageを十分明示しない | compatible + clarification | intended / actual Worker input / Artifact / actual Synthesizer inputの監査を明示 | core・実行仕様は不変 | access-control自体の新規mechanismとしない |
| A: RQ1はsame-model / structureのfactor比較 | C1〜C4は2×2、主比較C3−C2はRole/Access同時変更、C0は別構造 | compatible | RQ1は保持、C0除外と[exploratory plan](../experiments/epistemic-diversity/paper/exploratory-role-access-factorial-analysis-plan.md)を追加 | 3.1主比較・副比較・descriptive interactionは不変 | controlled配置と因果識別の達成を区別 |
| A: 各構成要素は既知、組合せが差分候補 | 旧surveyはfocused / 当時の範囲 | needs revision | [current Related Work](../experiments/epistemic-diversity/paper/current-related-work.md)をA〜G分類で追加 | 旧surveyを保持 | SILOのconfounding指摘等を含めfirst主張を避ける |
| A: Contributionsを候補・実証済み・計画へ分離 | v1はStudy 2から「性能差を十分説明できず」という強い接続 | needs revision | C1比較枠組み、C2treatment integrity、C3実観測＋planned lineageを分離 | 過去結果値は不変 | B−C=0はStudy 1原因の識別でない |
| B: RQ2はObservable Evidence Lineage | v2 human planは抽出／最終利用という語を残す | needs revision | S2 public expression、S5 fact relation/supportへ改訂 | [v3別文書](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md)。旧v2は短いsuperseded注記のみ | internal cognitionを観測しない |
| B: R1 raw-only / R2 gold alignment / pre-output registry freeze | 旧REVIEWとv2には共通two-pass frozen registryなし、gold開示方法は未確定 | needs revision | 2名R1独立票→R2alignment独立票→adjudication→registry freeze | frozen REVIEW/kitを改変しない | outcome-aware fact選択を避け、alternative pathsを残す |
| B: sentence/fact/support set/pathを分離 | 旧票はfact自由記述、support sentence列 | needs revision | object/ID schema、path-conditional requiredness、OR–AND規則 | schema仕様のみ。validator/form未実装 | gold sentence ID≠fact、全経路和集合≠必要facts |
| B: actual inputのS1、identity aliasのS3=NA | allowlist/auditあり、Worker公開outputをArtifact.payloadへそのまま設定・型正規化照合 | needs revision | actual inputによる機械state、transition provenanceの分類、S3 alias除外 | 保存record/codeは読み取りのみ | 独立publication transitionのない成功・損失率を作らない |
| B: S4 routes / S5a+b | old kitのtransfer/synthesis項目が混合 | needs revision | machine matchと意味stateを分離、Artifact/補足原文route、出力支持を定義 | 新kitなし、旧票へ代入しない | Bのraw routeをWorker保持と数えない、bridge非記載を失敗としない |
| B: stateとevent、cascade非二重計上 | v2も一部prerequisiteを設けるがmultiple_failures/first手入力の候補が残る | needs revision | scoped prerequisite付きderived events、first_observable_failure_stageをanalysis層で導出 | code・票・導出実行なし | observable first≠root cause、absence伝播≠独立failure |
| B: progressive disclosure / allocation blinding | prepared source packetはraw→Worker→Synthesizer→finalを一度に開示 | needs revision | future stage packetsとlocksを設計 | old kitを削除・上書きしない | old kitはv3の完全なblindレビューには使えない |
| B: external calibration＋edge cases＋stability | old REVIEW/kitはpilot2問先頭、28問本判定 | needs revision | 対象外4〜6問候補とvignettes、最後のbatchで新ruleなし | future amendment。旧2＋28仕様は履歴 | 固定2問だけで境界を校正したとはしない |
| B: IAA primary raw/kappa/marginals/n、pre-adjudication | v2 raw primary/kappa補助、独立票保存方針あり | needs revision | nominal unweighted kappaをprimary併記、applicabilityとmissing分離、derived-label agreement | 計画のみ。IAA値なし | prevalence・rare category・未定義を隠さない |
| B: question macro / clustered uncertainty | v2はfact独立不可とするがmacro/CI未固定 | needs revision | [metrics](../experiments/synthesis-evidence-preservation/docs/evidence-lineage-metrics-plan.md)で主要単位・coverage・strict/sensitivityを定義 | 新集計・CIなし | fact数・shared S0〜S3の擬似反復を避ける |
| B: preflight freeze checklist | v1は生成実験と旧review資料をseal済み、v3分析は未採用 | needs revision | [新checklist](../experiments/synthesis-evidence-preservation/docs/human-review-preflight-freeze-checklist.md)を全未完了で追加 | v1 freeze/hashを更新しない | design作成≠analysis freeze≠review開始 |
| 現executionをレポートの仮定へ合わせる | Study 1/2は既に実行済み、失敗/recovery保存あり | not applicable / rejected | factual resultとhistorical failuresを保持 | 一切再生成・再封印しない | repository一次記録を優先 |

## 採用しない／留保するもの

- Report AのiAgentsのarXiv `2402.11444`は別分野の論文なので採用しない。正しい一次資料[2406.14928v2](https://arxiv.org/abs/2406.14928v2)を使用する。AISは[CL 2023の論文](https://aclanthology.org/2023.cl-4.2/)で同定した。Authorization-First Retrievalは個別ページ取得が不調で、[公式volume](https://aclanthology.org/volumes/2026.trustnlp-main/)の掲載タイトル・abstractを照合した範囲に留める。
- 強い「初」の断定、C2/C3からのaccess因果効果、内部extract/use/nonuse、Study 2でStudy 1の原因を説明／否定したという表現は採らない。レポートから採用する差分候補も非網羅的な文献照合の範囲に限定する。
- 旧仕様の抽出／利用enum、multiple_failures category、identity aliasをpublication成功とする扱いを新designへ移植しない。historical文書の語を遡及改変するのではない。
- 既存2校正＋28本判定を既に実施したとは扱わない。v3の対象数・外部校正採用・担当者・packet方式は人間が開始前に決める。旧prepared formsを新schemaへ自動変換しない。
- レポートの推奨を採用しただけで査読妥当性・venue適合性・採択可能性を確定しない。mixed-effects等やalphaは補助候補、bootstrap設定は未承認候補であり今回は一切計算しない。

## Freeze / kitへの具体的影響

v1はcode_hashes 102件＋source_hashes 424件＝526件を参照する。REVIEW/PLAN/OPERATIONS/study.json、frozen audit/analysis/source/runnerなどを含む。旧builderはseal対象外でもkitの出自として保持する。両reviewer slotはpublic資料102＋空forms102＋制御3＝207件をmanifestで固定し、preparation auditがmanifest自体のhashを参照する。blank CSV、全空formsを含めて変更しない。

旧kitは引用適合、旧worker/transfer/synthesis分類、final supportのための資料を提供する。新RQ2にはpre-output registry、actual Worker inputとprovenanceの対応、独立publication判別、route別S4、S5a/b、progressive locks、path/denominator schemaが不足する。将来の新kitは別builder/保存先/version/manifestとして作る必要があるが、今回は設計だけである。

## 現行文書の更新範囲

framing、現在地、教員brief、claims map、current abstracts/outline、root/Study 2 READMEの現行説明を最小限整合させる。旧stage案は短いsuperseded注記のみ。旧依存監査と文書監査の「最新HEAD」表現は**当時のaudited snapshot**へ直し、当時の監査結果・本文は保持する。current Related Work、v3設計、metrics/checklist、factorial planは新規文書として追加する。historical abstracts/outlines、Protocol/freezes/campaigns/outcomes/failuresは変更しない。

検証は文書リンク・diff・保存資産hashの読み取り照合に限定する。テスト、モデル生成、review実施、factorial解析、研究統計再計算、stageのケース判定は対象外。

## 文書編集後の保全確認

- 編集前に取得した1,433ファイルのSHA256 snapshotを再照合し、変更は予定した現行文書12件だけで、欠損はなかった。新規文書は6件。既存未追跡mock出力3ディレクトリは保持した。
- v1のcode 102件・source 424件、計526件はsealのhashと全て一致。freeze本体、historical protocols/outcomes/failures、core、builder、旧CSV空票は編集前から不変だった。
- prepared kitの両slotは207件ずつ全てmanifest hashと一致し、manifest自体のhashもpreparation auditと一致。public packet、criteria、空formsを変更していない。
- 新規・変更18文書のローカルリンク181件に欠落なし。`git diff --check`で空白エラーなし。これは文書・資産の保全確認であり、新しい研究分析・テスト結果ではない。

人間の未決定事項は独立2名の確保、scope/校正ケース、registry/adjudication担当、path妥当性・applicability基準、codebook/metricの採用版、bootstrap採否・設定、source/packet共有・ライセンス、versioned freezeと新kitの実装承認。v3は未freezeでありreview開始を承認していない。
