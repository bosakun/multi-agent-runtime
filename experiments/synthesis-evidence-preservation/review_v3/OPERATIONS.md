# v3 tooling operations — human sign-off前の実装候補

```text
DESIGN IMPLEMENTED / HUMAN REVIEW NOT STARTED / 0 HUMAN LABELS / NOT FINAL-FROZEN
CODEBOOK CANDIDATE PREPARED / PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED
```

This tooling does not perform semantic review. It stores and validates human judgments.
Human reviewers remain required. No Human Review has been conducted yet.

## 人間が先に決めること

[既存preflight checklist](../docs/human-review-preflight-freeze-checklist.md)の選択をコード完成で
承認済みとしないでください。2名の担当者・独立性・既読ケース、registry/stage担当関係、
30/28の本判定scope、IAA対象とdescriptive-only IDs、校正とcodebook、source sharing、
metric採用版・分母・analysis rules、bootstrapの採否と設定を人間が決定します。
Study 2 main24×3、smoke exclusionを維持します。toolingがcaseを選ぶことはありません。

`Scope`入力には必ず`included_case_ids`, `iaa_eligible_case_ids`,
`descriptive_only_case_ids`, `decision_reason`, `prior_exposure_by_reviewer`を指定します。
後者の既知caseを無条件にindependent IAAへ戻す入力は拒否します。人間による妥当性判断・記録は別途必要です。

## 順序

2026-10-05からの候補（現revision v0.3.0）：まず[CODEBOOK](CODEBOOK.md)、[PILOT-PROTOCOL](PILOT-PROTOCOL.md)、
[ADJUDICATION-RULES](ADJUDICATION-RULES.md)を人間が採用し、main対象外でpilotを行います。
以下の従来main手順の前に、candidate版→pilot packet freeze→2名独立票lock→不一致確認→
協議→ambiguity log→必要なrevision / next batch→signed PilotClearance→main用codebook freezeを置きます。
今回pilotは実施していません。30/28 scopeは未決定で、新pilotをmain IAAへ戻しません。

```text
preflight decision
→ registry calibration / R1 (independent raw-only)
→ both immutable R1 locks
→ R2 (independent gold alignment; preserve R1 alternative candidates)
→ both immutable R2 locks
→ human adjudication / registry freeze
→ stage calibration / human codebook freeze
→ independent S1→lock→S2→lock→S3→lock→S4→lock→S5
→ pre-adjudication IAA
→ human adjudication (separate version)
→ final human labels
→ lineage analysis under human-frozen plan
```

R1/R2は自由候補への単純kappaではなく、candidate alignment後の独立判定も別記録します。
registry自由候補を機械が意味的に対応づける機能はありません。
calibrationは本対象外HotpotQA候補とedge-case vignettesを将来登録します。
`Workflow(review_mode="pilot")`に候補版とhuman authorizationを明示し、pilot用registryを
output開示前にfreezeします。pilotはcandidate版で校正するためmain codebook freezeを要求しません。
main workflowへsilent promotionはできません。registry-only calibrationとstage vignetteを分け、
外部QAにモデルtraceがない場合は新LLM生成ではなく人工stage教材等を別に使います。
最後のbatchに新ruleがないことは終了**候補**であり自動sign-offではありません。
本判定後の重大改訂はstop→amendment→new version→影響case全再判定、旧票保持です。

## 今実行してよい機械的確認

repo rootから既存venvで実行できます。新しいdependency installは不要です。

```powershell
.\.venv\Scripts\python.exe -B -X utf8 -m pytest -q -p no:cacheprovider experiments/synthesis-evidence-preservation/review_v3/tests
.\.venv\Scripts\python.exe -B -m ruff check --no-cache experiments/synthesis-evidence-preservation/review_v3
.\.venv\Scripts\python.exe -B -X utf8 experiments/synthesis-evidence-preservation/review_v3/run.py candidate
.\.venv\Scripts\python.exe -B -X utf8 experiments/synthesis-evidence-preservation/review_v3/run.py schema registry
.\.venv\Scripts\python.exe -B -X utf8 experiments/synthesis-evidence-preservation/review_v3/run.py codebook-candidate
```

`candidate`はstdoutへ候補を表示するだけです。FINAL FROZEN / READY / STARTEDへ変更しません。
schemasはPydantic JSON Schemaです。`validate KIND INPUT.json`はfield/参照の機械的確認のみ。
semantic correctness、reviewer資格、独立性や方法論の妥当性は保証しません。
保存テストは既存freeze/kitの**hashのみ**を読みます。ローカル非配布資産がないcheckoutでは
その保全テストだけ理由付きskipとなり、純粋なsynthetic suiteは動作します。

## 将来のcoordinator操作（今回は実行しない）

1. author-only source bundleを新しいignored `review_v3/local/`以下へ用意する。
   `PrivateSource`のstrict schemaを使い、actual Worker request・public output・Artifact・actual
   Synthesizer context・final outputを明示的に対応づける。`provenance.py`は旧saved requestから
   projected inputsを機械的に作るutilityであり、factやpath、stage判断を作らない。
   native Study 2はuser messageのserialized JSON context、Study 1はrequest.contextを読む。
   actual IDsだけでなくreference sentenceのtitle/index/text/hashも照合する。
   equal output/payloadだけで全caseをidentity_aliasへ自動分類しない。
2. scope JSONとquestionごとのWorkflow JSONを用意する。reviewer IDsは人間の明示入力で
   あり、toolingは割り当てない。開始stateはR1_OPEN。R1では空registry＋raw materialのみ。
3. `packet --source ... --workflow ... --registry ... --scope ... --phase R1
   --reviewer ... --destination ... --private-linkage ... --case-alias ...`でそのstageだけexport。
   destinationとprivate linkageはfresh path、linkageはexportの外側。
   匿名case aliasは各phase・両reviewer・全armsで同じ対応を維持し、arm aliasもS4/S5で維持する。
   reviewerへexportだけを渡し、coordinator sourceやcondition mappingは渡さない。
4. 人間がformのregistry欄を独立に記入する。`RegistryJudgment`にはreviewer/pass/version/
   independent status/rationale/timestamp/source hashesを人間が記録する。
   `lock --workflow ... --reviewer ... --phase R1 --ballot registry-ballot.json
   --version ... --store ... --unit ... --output new-workflow.json`でimmutable raw票とhash lockを保存。
   旧JSONへ書き戻さず、更新workflowも新versionのpathへ保存する。
   保存fileは`AREA/UNIT/PHASE-VERSION.json`なのでR1/R2、S1–S5の同じversion名も衝突しない。
5. 両者lock後に`advance --workflow ... --target R1_LOCKED --output ...`、
   続いてR2_OPENへadvanceする。R2 packetのregistry引数は**そのreviewer自身のlocked R1票**。
   hash照合により他者の候補との取り違えを拒否する。匿名票なら同じcase aliasを指定する。
   R2 formは空のまま、own locked R1候補を参照資料として別に保持する。
6. R2独立lock→R2_LOCKED→ADJUDICATION。独立raw票は上書きしない。
   coordinatorの`reconcile_registry_ids()`は別copyへIDだけを正規化する。
   fact/path対応づけやalternative validity、adjudicationは人間が行う。
   human-adjudicated registryに対し`advance ... --target REGISTRY_FROZEN --registry ...
   --human-signoff ... --frozen-registry-output fresh-registry.json --output fresh-workflow.json`。
   registry hash/時刻/sign-offを保存する。primary registryのsilent mutationは拒否する。
7. Stage calibration後、`freeze-codebook --workflow ... --codebook ... --version ...
   --human-signoff ... --calibration-completed --pilot-clearance ... --output ...`で採用版を記録。
   mainでは`CodebookDefinition`の>=1 freeze_candidateと、typed `PilotClearance`を必須にします。
   最終pilotとdocument hashes / rule IDsが変わった場合は再pilotが必要です。内容不変のpromotionも
   `CodebookRevision`履歴へ残し、候補文書のhashと採用manifest versionを分離します。
   freeze済みcodebookは上書きしない。analysis rules/software/source hashesも別manifestに固定する。
8. stage formの`annotation`を人間が記入する。worker/arm/unitは匿名linkageの対応を保つ。
   S0 reference presenceはregistry/reference integrity時に別のS0票へ記録する。
   S3 identity_aliasなら人間がS3=NA / not_applicable / no_separate_transitionを記録し、
   Artifact factの意味状態は別fieldに記録する。unknownは非識別でありmissingとは別。
   S4はoverallとroute別state、machine match、expected/actual pointersを区別する。
   `lock ... --phase S1 --ballot stage-ballot.json ...`は`[{stage, annotation}, ...]`を検証・保存。
   同reviewerの前stage lockがあるまで次stageはexportできない。
   S4/S5の全arm packetに対する当該stage票は一つの独立ballotにまとめてlockする。
9. `ReviewStore`はregistry raw2領域、stage labels2領域、pre-adjudication agreement、
   adjudication log、final labels、post-freeze candidate、workflow、packetsを別保存する。
   各票の訂正は別versionと理由を保持する。本判定規則改訂は新workflow/amendmentで扱う。
10. `scoped_stage_agreement(..., scope)`で人間が固定したIAA IDsへ限定し、
    `stage_agreement()`でapplicabilityとsemantic一致を別に集計。
    同unit/同codebook/別reviewerを確認する。`multilabel()`は同じ規則で導出した独立票由来setのみ。
    IAAはadjudicated labelsから計算しない。未定義kappa・missing・coverageを隠さない。
11. `save_adjudication()`は両者のS5 lock後のみ別領域へ保存する。
    unit/field/両者label/採用label/reason/guideline/adjudicator/time/codebookを人間が記録する。
    schema 3.1.0ではevidence_pointer / resolution_statusを追加し、実票保存では採用Rule IDも検証します。
    未解決はunclear、record欠損はnull＋missing_recordを維持します。
    `reconcile_stage_ids()`は匿名raw票を保持したまま別copyにする。
    `assemble_question()`は正規化した人間票をshared S0–S3 / arm別S4/S5にgroupするだけ。
    未提供stateを埋めず、missingとしてcoverageへ残す。
12. 人間のfinal labels・採用規則で`derive()` / `derive_question()` / `aggregate(..., scope=scope)`を呼ぶ。
    解析は明示呼出しだけで、CLIに自動解析／real-result生成commandはない。
    bootstrapは`BootstrapConfig(draws=..., seed=..., ci_type=..., confidence_level=...,
    zero_denominator_rule=..., human_finalization=...)`を人間が固定した場合だけ。
    `macro_statistic()`は復元抽出されたquestion blockのmacroを維持する。

全てのlocal出力・partial preparation failureは保存する。再実行はfresh destination/versionを
使い、旧生成物をcleanupしてやり直さない。sourceのbyte hashとcanonical payload hashは別物です。
実reviewや実統計の実行を、ここに記した利用手順だけで新たに承認済みとは扱いません。
人手分析後の次実験も人間による別計画が必要です。

## Pilot / version metadata（将来操作、今回は実行しない）

[透明性/sign-off手順](TRANSPARENCY-AND-SIGNOFF.md)も採用前に確認してください。reviewer-profile / adjudicator-context / main-signoffのschema/validateとauthor-only保存を利用可能です。実mainのfreeze-codebookにはPilotClearance.main_signoffの10項目の人間確認、scope、policy/codebook hashes、Reviewer構成が必要です。pilot完了を自動main承認にしません。

日本語話者向けの[固定訳方針](BILINGUAL-REVIEW-POLICY.md)を追加しました。pilot/main開始前に
人間がTranslationAssetを準備・確認・固定し、`bind-translations --workflow ... --translations ...
--output ...`で両reviewer共有のworkflowへ一度だけhash/versionを結び付けます。
実`packet`には`--translations ...`を指定します。未固定／欠訳／不一致は出力前に拒否します。
全翻訳assetはauthor-onlyで、reviewerへはそのstageの英日ペアだけを渡します。
registryの人間記述は原則日本語。訳を途中で変える場合はamendmentと旧資料・票保存を必要とします。
schema/builderの現候補は3.3.0ですが、旧manifestやkitは変更しません。翻訳生成commandはありません。

`codebook-candidate`は3文書のbyte SHA256とstable rule一覧のmetadataをstdoutへ表示するだけです。
実票、Fact Registry、packetを生成しません。`schema` / `validate`はcodebook、codebook-revision、
ambiguity、pilot-selection、pilot-batch、pilot-clearance、path-admission、requirednessも検証できます。
`PathAdmission`は人間が入力した前提条件の整合性検証であり、自然言語の妥当性を自動判定しません。
人間のpath採用・requiredness補助記録はpath_admission_checks / path_requiredness_checksへ
別versionとして保存可能です。Registryのyes/no/unclearを自動記入せず、R2独立票・協議根拠と対応づけます。

将来のpilot coordinatorはfresh pilot Workflowに対し`authorize-pilot-codebook --workflow ...
--codebook ... --human-authorization ... --output ...`を明示実行します。pilot許可はmain freezeではなく、
候補版・protocol hashを持つbatch限定の許可です。packet builderは既存stage限定開示を維持し、
manifestにreview_modeを保存します。source/packet freeze、third-adjudicator方針、実reviewer独立性は
human preflightとfilesystem権限で管理し、JSON gateが人間の実行事実を証明すると考えないでください。

`ReviewStore`にはcodebook_versions / codebook_revisions / pilot_batches / ambiguity_logs /
pilot_clearancesを別領域として追加しました。全てexclusive append-onlyです。旧版・元独立票を保持し、
pilot batchesのcodebook hash、2名lock hashes/time、inspection time、adjudication/ambiguity hashesを残します。
typed `calibration_stop_candidate()`は全境界coverage、最後のbatchでnew rule=0、主要不一致の解決可能性、
ambiguity文書化・blockerなしを要求します。旧dict形式はpreliminary summaryでfreezeに使えません。
人間の実pilot完了とcodebook採用のsign-offは別途必要です。
