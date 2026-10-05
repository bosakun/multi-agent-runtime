# Pilot前の透明性metadata / Human main sign-off

2026-10-06。未採用候補。PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED / REAL TRANSLATION ASSETS = 0 / HUMAN LABELS = 0 / NOT FINAL-FROZEN。

これは人物登録、実clearance、translation asset、pilot判定の記録ではない。小さなschema追加のみで、annotation platform・rendererは作らない。

現候補はCodebook v0.3.0、schema/builder 3.3.0。未freezeのv0.2.0候補へ透明性・sign-off要件を追加するpre-pilot revisionであり、pilot中の実判定を変更した記録ではない。影響する実pilot units・旧annotation・再判定は0。旧候補の歴史的Git資料・準備監査を上書きしない。

## 既存機能を維持するもの

CodebookRevisionの旧/新版・hash・理由・affected rules/units、versioned append-only票、PilotBatchの両独立lock、critical coverage、final new-rule count、ambiguity/blocker確認、PilotClearanceの人間署名、progressive disclosure、mainのSTOP/amendmentは再実装しない。既存の機械testsで確認する。R1訳の情報境界、原文基準、同一固定訳、途中変更禁止も維持する。

## 今回補強する記録

- `ReviewerProfile`: pseudonymous reviewer_id、relationship_to_author（none / family / academic_advisor / friend_or_peer / collaborator / other、未開示はundisclosed）、involvement_in_implementation、involvement_in_experiment_design、prior_result_exposure、prior_case_exposure、disclosure_notes。複数関係を許可するがnone/undisclosedと混ぜない。独立性はannotationの手順であり人的無関係ではない。
- `TranslationAsset`: 作成方法・作成者またはsystem・確認者・確認方法・可能なsystem/model/version metadataを追加。既存の版・frozen hashを使い、作成者とReviewerの別人要件は追加しない。古いassetをそのまま再freezeする移行は行わない（実assetは0）。
- `CodebookRevision`: semantic change時に旧票の保存先/hash、全影響unit再判定または新independent batch、実再判定範囲を必須化。変更理由の正当性や再判定実施の事実は人間が点検する。
- `AdjudicatorContext`: 仮名ID、prior_result_exposure、prior_case_exposure、disclosure_notes、allocation_blinded_where_feasible。協議資料の最小限定は運用規則であり、今回新しい協議packet builderは作らない。

これらはauthor-only記録。実名は不要で、raw/local/private資料や実関係性をGitへ追加しない。公開時の本人同意・Methodsでの開示範囲は人間が決める。コードによる自己申告の検証は、人物の実在・翻訳の忠実性・情報漏洩がなかったことを保証しない。

## Pilotからmainへ進む人間の10確認

1. critical edge casesを2名が実際に扱った。
2. final pilot batchのnew guideline rule数が0。
3. unresolved ambiguitiesが記録済み。
4. freeze blockerが残っていない。
5. 採用するCodebook final candidate version/definition hashを確認。
6. translation policy version/hashを確認。
7. Reviewer構成・関与・既知情報を確認。
8. adjudication policyと結果既知の限界を確認。
9. main scopeの30または28、選択理由とcase IDsを確認。
10. main IAA対象IDsとdescriptive-only対象を確認。

`MainReviewSignoff`はversion、10項目の人間による確認、採用Codebook version/hash、translation/adjudication policy version/hash、ReviewerProfile、AdjudicatorContext、Study 1 Scope、署名者・日時を持つ。30/28も対象IDsも既定値を持たず、人間が指定する。Study 2 main24×A/B/Cとsmoke exclusionは既存の別scope/manifestを維持する。

将来のcoordinatorは`main_review_signoffs`へ独立versionで保存し、PilotClearance.main_signoffに同じ内容を結び付ける。実mainのcodebook freeze gateはこの署名、workflow/pilotのReviewer ID、採用policy/codebook hashesの一致を要求する。pilot完了票だけでは不足。機械的schema一致は人間による実確認の代用ではない。main registry R1を含む作業開始前のpreflight採用・承認は人間が行い、toolingが自動開始しない。

Codebook本体のfinal freeze、各翻訳assetの固定、registry freeze、codebook promotionのrevision記録、main packets/source hashes、IAA/metrics/analysis設定のfreezeは別の既存手順として必要。candidate状態のmain_signoffを実署名として発行しない。

## 保存・使い方（将来のみ）

`schema` / `validate`にreviewer-profile、adjudicator-context、main-signoffを追加する。`ReviewStore`のreviewer_profiles / adjudicator_contexts / main_review_signoffsと既存codebook_revisions / pilot_clearances / translation_assetsへexclusive append-only保存できる。過去のrecordを上書きしない。今回実recordは作らず、人工fixturesだけで検証する。

## 機械検証（研究結果ではない）

v3人工fixture testsは123 passed、Ruff合格、diff whitespace check合格。既存の107件を保持し、関係性、翻訳provenance/hash、全影響unit再判定、human確認と署名hash、30/28の明示入力、結果既知の記録、append-only保存を追加確認した。root regressionは今回未実行。

作業直前の1,480既存ファイルをSHA256照合し、今回のcurrent docs/tooling/testsの17件だけ変更、欠損0。既存freeze・旧kit/空票・historical Protocol・Study 1/2結果・failure/recovery・旧manifest・過去の準備監査は不変。直前の未commit修正と既存未追跡mock資料も保持し、今回stage/commitはしていない。
