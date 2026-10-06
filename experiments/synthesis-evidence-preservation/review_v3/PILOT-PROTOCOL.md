# Pilot Human Review Protocol — candidate v0.3.0

2026-10-06現在。**PILOT MATERIALS PREPARED / PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED / REAL HUMAN LABELS = 0 / NOT FINAL-FROZEN**。pilotはannotation guidelineのcalibrationであり、新しいLLM experimentでも本研究の性能結果でもない。PR #17でPilot Materials Preparationが完了し、Pilot Aの6問はresult-blind / deterministicに選定済み。Reviewer assignment、real translation freeze、reviewer-specific packet authorization、人間によるpilot annotationは未実施。

## 事前に人間が固定するもの

reviewerは日本語話者2名。[固定訳方針](BILINGUAL-REVIEW-POLICY.md)に従い、pilot開始前に英語原文と対応する日本語訳の版/hashを固定し、両者へ同一の訳を提示する。gold/final訳も当該phaseまで非開示。翻訳ambiguityと訳修正の影響範囲もpilotの確認対象とする。今回翻訳生成・実訳の固定は行わない。

Codebook candidateの版とdocument hashes、selection rule、pilot資料の出自／ライセンス、独立判定を行う2名と既読履歴、第三adjudicator利用方針、packet限定開示・lock方式、ambiguity logの責任者を固定する。担当者は実装・実験作成者以外。AIをreviewerとして数えない。新モデル生成を資料作成の条件にしない。

<!-- rule: PILOT-REVIEWER-001 -->
Reviewer候補は、成人または大学生相当以上で、日本語でReviewer GuideとCodebookを理解でき、pilot calibrationを最後まで完了できる人とする。runtime実装およびStudy 1/2の実験設計に関与しておらず、初回annotationを他Reviewerへ相談せず、相手の票を見ずに行えることを確認する。AI/LLM・NLPの専門知識は必須とせず、必要なのは保存されたobservable evidenceだけを基準にCodebookに沿って判定できること。Pilot中に判定困難が明らかになった候補者はMain Reviewerに採用しない。PilotとMainのReviewer候補について、関与・既知情報・関係性は既存ReviewerProfileへ開始前に記録する。

今回の研究では、査読上不要な疑義を避けるため家族をMain Reviewer候補から除外し、Reviewerとして使用しない。これは本研究の選択であり、家族Reviewerを方法論上一般に禁止する規則ではない。具体的な候補者・関係性の登録は人間が行い、実名や個人情報を公開文書へ書かない。

独立性は初回判定中に相談せず、相手のlabelを見ず、adjudication前に各自の票を作るindependent annotationを指す。著者との人的関係の有無は別に[Adjudication Rules](ADJUDICATION-RULES.md)のauthor-only項目へ記録する。[日本語Reviewerガイド](REVIEWER-GUIDE-JA.md)を開始前に共有する。英語はsemantic source of record、日本語はprimary displayであり、R1訳の準備にもfuture-stage情報を使わない。

## Sample selection rule（Pilot A選定済み／human annotation未開始）

<!-- rule: PILOT-SELECT-001 -->
原則、Study 1のmain候補30問の**外**からHotpotQA distractor dev 4〜6問程度をregistry calibration用に選ぶ。Study 2 main24・smoke IDsもexplicit exclusion manifestへ入れ、重複がないことを検証する。旧2校正caseも今回の新pilotへ流用しない。main30/28の選択は別の未決定human preflightである。

Pilot Aでは、取得済みのHotpotQA distractor dev 7,405問から上記の既存caseを重複除外し、eligible pool 7,375問に対して事前固定した `selection_salt = "human-review-pilot-v1:"` と `rank = SHA256(UTF8(selection_salt + QA_ID))` を使用した。rankのhex ascending順の先頭6問を選定済みであり、model performance、answer correctness、desired failure pattern、Study 1/2のscoreや問題内容を選定に用いていない。salt・ranking・exclusion manifest・選定済み6 IDsは維持し、再選定・資料再生成は行わない。

Actual selected IDs、順序、pool/exclusion hashes、dataset hash、provenance、selection timestampおよびprepared material hashesのsource of recordは、[pilot_materials_v1 manifest](pilot_materials_v1/pilot_materials_manifest.json)と[preparation outcome](pilot_materials_v1/PREPARATION-OUTCOME.md)とする。この同期は現在文書の状態記述のみの更新であり、保存済みmanifestや資料、選定前のhistorical commitは書き換えない。資料準備済みはhuman pilot開始を意味せず、Reviewer assignment・固定訳・packet authorizationを人間が完了してからpilot annotationへ進む。

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
最低条件は（1）critical edge cases全coverage、（2）最後の独立batchでnew guideline rules=0、（3）主要不一致がそのbatch-frozen Codebookで解決可能、（4）未解決ambiguityがlogへ記録され、freezeを妨げるblockerがないこと。さらに、`unclear`が頻発する、ReviewerがCodebookの同じ箇所で繰り返し迷う、critical boundaryで安定した判定ができない、または新しい判定規則が継続的に必要な場合はMain Reviewへ進まず、Codebookまたはtraining materialを見直して必要なpilot calibrationを続ける。固定数値thresholdは設けず、高いagreementを証明することもstop目的にしない。人間が判定基準の実用上の安定性を確認する。unclearのまま残す境界も明示的な規則で扱えるなら許容し、その件数を隠さない。固定件数を終えただけ／高kappaになるまでtuningしただけでは終了しない。

`calibration_stop_candidate()`のtyped PilotBatch入力は上記を機械確認するのみ。旧dict入力によるcoverage/new-rule summaryはpreliminary checkでありfreeze authorizationではない。人間のsigned PilotClearance、candidate version/hashとの一致、本番版とrevision履歴、codebook v1.0採用sign-offを別に必要とする。コードが自動freeze・review開始をしない。

## Revision / amendment

pilotでは問題を発見してCodebookを修正してよいが、修正過程を完全に残す。不一致が出たcaseだけに都合のよい基準を適用することは禁止する。旧・新Codebook version/definition hash、理由、affected rule IDs、affected pilot units、旧annotationの保存先/hash、実際に再判定した範囲を`CodebookRevision`へ記録する。semantic rule変更時は**影響する全pilot unitsを同じ新版で再判定**するか、改訂を採用した**新しいindependent pilot batch**へ分離する。後者では旧unitsを新版の判定として扱わず、旧・新batchのIAAを混ぜない。

<!-- rule: PILOT-REVISION-001 -->
old codebook/document hash・版を保持し、change ID、reason、affected fields/rule IDs、affected pilot units、影響と再判定方針、timestamp、新版をchange logへ記録する。rule IDを別意味へsilent再利用しない。最終安定batch後にsemantic ruleを変えた場合は再pilotが必要。内容不変のv0.x→v1.0 promotionもsigned clearanceに元candidate hashを残す。main開始後はADJ-AMEND-001のSTOP/amendment/all-affected-case手順。

Pilot終了・freeze可能性をこの候補文書だけで記録しない。人間のpilot完了票・independent locks・ambiguity log・clearance・sign-offが存在するまで状態は未開始のまま。

PilotClearanceだけでmainへ進まない。[透明性metadataとmain sign-off](TRANSPARENCY-AND-SIGNOFF.md)の10項目を人間が確認し、versioned `MainReviewSignoff`を別保存してclearanceに結び付ける。これはpilotのテスト成功をコードが自動認定する仕組みではない。main開始後はSTOP→amendment→new version→affected cases全再判定→old labels保存を維持し、結果を見ながら柔軟に基準を変えない。
