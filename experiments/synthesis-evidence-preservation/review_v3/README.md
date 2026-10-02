# Observable Evidence Lineage Human Review v3 tooling

```text
DESIGN IMPLEMENTED
HUMAN REVIEW NOT STARTED
0 HUMAN LABELS
NOT FINAL-FROZEN
```

This tooling does not perform semantic review.
It stores and validates human judgments.
Human reviewers remain required.
No Human Review has been conducted yet.

このnamespaceは[Human Review v3](../docs/human-review-stage-analysis-plan-v3.md)、
[metrics plan](../docs/evidence-lineage-metrics-plan.md)、
[preflight checklist](../docs/human-review-preflight-freeze-checklist.md)の実装候補です。
コード・人工テストの完成は方法論の検証、review開始、担当者決定、final freezeを意味しません。
`STATUS`は今回のimplementation snapshotです。将来の実施状況は実際の独立票・lock・
sign-off・adjudication記録に分けて保存し、このsnapshotで実施件数を代用しません。

## 実装の構成

| ファイル | 役割 |
| --- | --- |
| `schema.py` | PydanticによるQuestion / Sentence / Fact / SupportSet / Path / Membership / Provenance、S0–S5a/b、scope、adjudicationのstrict schema |
| `logic.py` | support sets OR、required facts AND、valid paths OR。不明・missing・非識別を失敗へ補完しない |
| `workflow.py` | R1→R2→adjudication→registry freeze、codebook gate、reviewer別progressive locks |
| `storage.py` | SHA256、canonical JSON、exclusive append-only保存、保全照合、旧namespaceへの出力禁止 |
| `ballots.py` | 入力票の機械的検証、匿名IDの別copyへの対応づけ。意味欄を埋めない |
| `provenance.py` | 保存済みrequestのread-only projection。intended partitionとactual inputを分離 |
| `packets.py` | R1/R2/S1/S2/S3/S4/S5のstage限定packet・全意味欄が空のform・hash manifest |
| `assembly.py` | 人間票を共有S0–S3とarm別S4/S5へ機械的にgroupする。未入力はNoneのまま |
| `failures.py` | prerequisite付きevent導出、first observable failure、distinct event重複除去 |
| `metrics.py` | 8指標、coverage、strict / sensitivity、question macro / secondary micro |
| `bootstrap.py` | 必須設定付きquestion-block bootstrap。既定seed/draws/CI policyなし |
| `agreement.py` | 独立票からraw agreement、unweighted kappa、marginals、matrix、multi-label一致、IAA scope限定 |
| `adjudication.py` | 両者の独立lock後に別versionの人間協議結果を保存 |
| `calibration.py` | 本判定外external cases / synthetic vignettesの登録schemaと終了候補条件 |
| `manifest.py`, `run.py` | freeze candidate、schema出力、入力検証、明示的lock/transition/packet CLI |
| `tests/` | invented fixturesのみの機械的テスト＋既存seal/kitのhash-only確認 |

新依存はありません。既存環境のPython / Pydantic 2 / pytest / Ruffを使用します。
旧`src/synthesis_study/audit.py`・`analysis.py`・旧builderをimport/実行しません。
Runtime core、旧freeze、Protocol、既存結果・空票・kitは変更しません。

## データと判断の境界

R1はquestion / raw sentencesのみ。R2は**両者のR1 lock後**にgoldを開示し、
そのreviewer自身のimmutable R1候補を参照します。他者の独立票はpacketに入りません。
system outputはhuman-adjudicated registry freeze前に非開示です。
新pathは`post_freeze_candidate`領域へ保存し、primary registryを変更しません。

S2は**Worker Public Expression Fidelity**であり、内部理解や内部抽出の判定ではありません。
S3の独立publication有無と、Artifact自体の`artifact_fact_state`を分離します。
S4はoverall / Artifact / supplementaryの意味欄とmachine payload一致を分離します。
S5a/bは出力のfact関係・受信pathによる支持であり、モデル内部の証拠利用は主張しません。
bridgeの`not_asserted`からfailureを自動生成しません。

Reviewerはstage stateだけを記録します。failure / first stage / countは票のfieldではなく
analysisの出力です。同じtransitionのmismatchとdistortionは一つのeventの複数labelです。
上流absenceのcascadeは新しいtransmission eventになりません。
`derive_question()`はA/B/Cで共有された上流eventも一度だけ数えます。
前段の観測が不明ならfirst observable failureは`undetermined`です。
これは原因の特定ではなく、採用した規則で観測可能な障害の分類です。

## Metric上の重要な仕様

- Downstream Evidential Supportのprimaryは、S4に**complete valid frozen registered pathが
  少なくとも1本存在するquestion–arm**のみ。successはその受信pathの少なくとも1本で
  final answerがfully supported。partial/none-pathはprimary分母にもsensitivityにも混ぜません。
- S5bはpath別。別の受信valid pathがfully supportedなら、他pathでunsupportedだったことだけで
  question–arm全体のunsupported eventを導出しません。
- Fact E2Eは同じWorkerのS1→S2→Artifact-route S4を接続します。separate_recordsはS3 retainedも必須。
  identity_aliasはS3をstructural NAとしてskipし、publication success/failureを補完しません。
  unknownはArtifact-lineage E2Eがnon-identifiable。Any-Route Availabilityとは別です。
- Path E2Eはrequired facts AND、alternative valid paths OR。factの和集合を全て必須にしません。
- Publication Survivalではidentity aliasをpotentially eligibleにも入れず、NA除外数を別記します。
- strictはcomplete/correct/retained/fully_supportedのみ。sensitivityは該当stageのpartialも含みます。
  survivalの上流eligibilityは維持し、partial=0.5などの重みを作りません。
- 各指標はpotentially eligible / evaluable / success / unclear / missing / NA /
  non-identifiable / ineligibleとcoverageを返します。ゼロ分母はNoneで0点ではありません。
- primaryはquestion-level macro。pooled microはsecondary descriptive。
  Study 2の共有S0–S3は一度だけ保持し、arm間のupstream差を検定しません。
  同じquestionをStudy 1/2から独立標本としてpoolしません。
  実票の集計にはScope入力を必須とし、descriptive-only casesはprimary macroから分離します。
- bootstrapはwhole question blockを復元抽出し、Workers / facts / paths / shared stages / all armsを保持します。
  draws、seed、percentile CI水準、zero-denominator draw処理を必須設定にし、実票では人間のfinalizationが必要です。
- IAAはpre-adjudication独立票のみ。applicabilityとsemantic agreementを分け、missingはunclearに変えません。
  `Pe=1`等の未定義kappaをNone＋理由で返します。empty/empty Jaccardは1で非空subsetも併記します。

## 保存とblinding

author-only source bundleとreviewer exportは分離します。旧kitの全traceをそのままコピーしません。
packetは**一回に許可された一stageだけ**を生成します。S1→lock→S2→lock→S3→lock→S4→lock→S5。
S4/S5の各arm packetは匿名aliasを使い、全armの当該stage票をまとめてからlockします。
final answerはS5のみ。条件対応、scores、aggregate outcomes、original IDsとprivate source pathsは
author側linkageへ置きます。reference registryのtarget answerはモデルのfinal outputとは別です。

`allocation-blinded where feasible`であり完全blindではありません。gold既知、本文・入力構造からの
推測は残ります。coordinator storeや将来stageのsource bundleをreviewerへ共有しないでください。
CLIの順序gateはOS認証・暗号化・sandboxではありません。別export・filesystem ACLの運用が必要です。
匿名化したregistry projectionのhashと、元のfrozen registryのorigin hashも分離して保存します。
非開示stageやgoldの個別source hashesもauthor linkage側に残し、reviewer manifestには
そのstageで実際に開示したmaterialsのhashを記録します。

repo内の生成物は`local/`, `packets/`, `exports/`, `sessions/`のみ許可し、Git ignoreします。
別のローカル保管先も指定可能ですが、人間が権限・共有先を管理します。自動Git追加はありません。
旧namespaceへの出力は拒否し、既存出力への再生成・上書きも拒否します。

開始前の手順は[OPERATIONS](OPERATIONS.md)、保全結果は[PRESERVATION](PRESERVATION.md)を参照してください。
実kit、fact registry、human labels、reviewer assignment、final freezeは今回作成していません。
