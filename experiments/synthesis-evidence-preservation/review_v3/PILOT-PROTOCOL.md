# Pilot Human Review Protocol — candidate v0.1.0

2026-10-05。**PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED / 0 HUMAN LABELS / NOT FINAL-FROZEN**。pilotはannotation guidelineのcalibrationであり、新しいLLM experimentでも本研究の性能結果でもない。今回case選定、reviewer割当、packet・票の生成、判定を行わない。

## 事前に人間が固定するもの

Codebook candidateの版とdocument hashes、selection rule、pilot資料の出自／ライセンス、2名の独立reviewerと既読履歴、第三adjudicator利用方針、packet限定開示・lock方式、ambiguity logの責任者を固定する。担当者は実装・実験作成者以外。AIをreviewerとして数えない。新モデル生成を資料作成の条件にしない。

## Sample selection rule（未実行）

<!-- rule: PILOT-SELECT-001 -->
原則、Study 1のmain候補30問の**外**からHotpotQA distractor dev 4〜6問程度をregistry calibration用に選ぶ。Study 2 main24・smoke IDsもexplicit exclusion manifestへ入れ、重複がないことを検証する。旧2校正caseも今回の新pilotへ流用しない。main30/28の選択は別の未決定human preflightである。

question type等のraw metadataによる事前strata、安定したquestion ID順位／seed付きdeterministic方法等を人間がpilot開始前に固定し、pool hash・ID mapping・selection methodを保存する。model performance、answer correctness、desired failure pattern、Study 1/2のscoreを見てcaseを選ばない。今回は実ID・seed・選択caseを指定しない。取得済み資料がなければ別途人間が共有方法を決める（今回downloadなし）。

外部HotpotQAはquestion/reference/goldによるR1/R2校正用で、Worker/Synthesizer traceがない場合にそれを捏造しない。stage校正には出自を記録したarchival recordsまたは人工vignettesを使い、新LLM callを行わない。archival recordsはmain対象と独立で、選定をdesired model failureへ合わせない。人工vignetteは本研究実結果ではない。pilot IDをmain independent IAA sampleへ戻さない。

## 必須edge-case coverage

<!-- rule: PILOT-COVERAGE-001 -->
`calibration.EDGE_CASES`の全12項目：correct、partial、distorted、absent、unclear、alternative_path、identity_alias、unknown_transition、separate_publication_record、supplementary_evidence_route、upstream_failure_cascade、complete_path_unsupported_answer。bridge非記載、comparison、外部premiseが必要なinvalid path、path内requiredness、partial vs distorted、retained vs partial_lossも人工境界例で扱う。資料の有無と2名が実際に扱ったcoverageは別であり、教材が存在するだけではcoverage達成としない。

## Workflow

<!-- rule: PILOT-ORDER-001 -->
```text
Codebook candidate v0.x + human pilot authorization
→ pilot packet freeze (candidate/rules/source/packet hashes)
→ R1 independent raw-only → both R1 locks
→ R2 independent gold alignment → both R2 locks
→ pilot registry adjudication → pilot registry freeze (before outputs)
→ S1 lock → S2 lock → S3 lock → S4 lock → S5 lock, independently
→ both complete independent ballots lock
→ pre-adjudication pilot agreement / disagreement inspection
→ human adjudication → ambiguity log → codebook revision
→ next independent pilot batch if needed
→ stability review → Codebook v1.0 freeze candidate → human sign-off
→ separate main preflight / main registry / main review
```

registryのみのbatchとstage vignette batchは区別し、それぞれ該当phaseを完了する。人工stage資料のreference pathは教材仕様であってmain Registryではない。stage pilotのoutput開示にもpilot専用registry freezeを要求する。ただしpilotは候補v0.xで実行し、main用codebook freezeを先に要求しない（循環を避ける）。toolingのreview_mode=pilotとexplicit human authorizationを用い、candidate pilotをmain開始の代替にしない。

相手の票は各batch両者の独立lock後まで見ない。final answerはS5まで、条件名・aggregate/F1/EMは非開示。allocation-blinded where feasibleであり、構造・gold既知による推測は残る。pilot合議で基準を改訂したら、その版のまま次の独立batchを行い、改訂前後をpoolして同一基準のIAAとしない。

## Pilotで確認する項目

raw agreement、disagreement/confusion matrix、カテゴリ頻度、unclear rate、missing、applicability不一致、alternative-path validity／requiredness不一致、partial–distorted、retained–partial_loss、complete-path–downstream support境界を確認する。自由R1候補はmatching前に単純kappaを出さない。固定候補への独立判定とstage判定は別。kappaは参考で、rare category・Pe=1のundefinedを隠さない。pilotの少数例を本研究のfailure割合やlineage効果として解釈しない。

## Stop criterionとfreeze候補

<!-- rule: PILOT-STOP-001 -->
最低条件は（1）critical edge cases全coverage、（2）最後の独立batchでnew guideline rules=0、（3）主要不一致がそのbatch-frozen Codebookで解決可能、（4）未解決ambiguityがlogへ記録され、freezeを妨げるblockerがないこと。unclearのまま残す境界も明示的な規則で扱えるなら許容し、その件数を隠さない。固定件数を終えただけ／高kappaになるまでtuningしただけでは終了しない。

`calibration_stop_candidate()`のtyped PilotBatch入力は上記を機械確認するのみ。旧dict入力によるcoverage/new-rule summaryはpreliminary checkでありfreeze authorizationではない。人間のsigned PilotClearance、candidate version/hashとの一致、本番版とrevision履歴、codebook v1.0採用sign-offを別に必要とする。コードが自動freeze・review開始をしない。

## Revision / amendment

<!-- rule: PILOT-REVISION-001 -->
old codebook/document hash・版を保持し、change ID、reason、affected fields/rule IDs、affected pilot units、影響と再判定方針、timestamp、新版をchange logへ記録する。rule IDを別意味へsilent再利用しない。最終安定batch後にsemantic ruleを変えた場合は再pilotが必要。内容不変のv0.x→v1.0 promotionもsigned clearanceに元candidate hashを残す。main開始後はADJ-AMEND-001のSTOP/amendment/all-affected-case手順。

Pilot終了・freeze可能性をこの候補文書だけで記録しない。人間のpilot完了票・independent locks・ambiguity log・clearance・sign-offが存在するまで状態は未開始のまま。
