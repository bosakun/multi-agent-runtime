# 段階別レビュー設計の追加と旧kitへの影響監査

2026-10-02。最新main `213906dd6d30ab29ba0a66ecc78c3dfee1044d24`と作業ブランチHEAD `8dbb5a9525087d82d96142e136e67547ad09fb5b`は内容が一致していました。これは設計・依存関係の監査で、kit生成・人手判定・新しいモデル実験ではありません。

## 1. 採った方式と理由

旧[REVIEW.md](../REVIEW.md)はStudy 2 [v1 freeze](../freezes/v1.json)の`code_hashes`に含まれます。prepared kitの両slotは同書を`criteria.md`へコピーし、各`packet-manifest.json`でhash固定しています。同書や旧schema相当の定義、コピー、blank formを変更すると、封印仕様・準備済み配布資料の同一性を壊します。

そのため、旧仕様を変更する`REVIEW-V2.md`への置換ではなく、別の[human-review-stage-analysis-plan.md](human-review-stage-analysis-plan.md)を新規追加しました。旧REVIEW/PLAN/OPERATIONS、freeze、prepared kit、generator、空票、過去campaignは保持します。新文書は結果観測後の内容分析設計の追加で、過去の生成仕様・事前評価を再封印したものではありません。

新設計はまだ人間による採用revisionの確定・kit実装・判定を済ませていません。現行要約・outlineへのリンクと位置づけの更新だけを行います。新kitが必要でも、旧kitをin-place migrationしません。

## 2. 実際の依存関係

| 資産 | 依存／保存方式 | 今回変更したか |
| --- | --- | --- |
| `freezes/v1.json` | code_hashes 102件、source_hashes 424件、replay input manifest・Mock結果／監査・開始validationのhash参照、81回上限 | 変更しない。code/source 526件は調査時hash一致 |
| `REVIEW.md`、`PLAN.md`、`OPERATIONS.md`、`study.json` | v1 code_hashesに含まれる研究仕様・計画snapshot | 変更しない。新設計・実施状態は別文書 |
| `src/synthesis_study/audit.py` | frozen source。旧30問C3を主対象、C1/C2匿名参照、Worker available IDs・公開response・実合成context・finalを含むMD資料、private評価、blank-source CSVを生成 | 実行・変更しない |
| `src/synthesis_study/analysis.py` | frozen source。実main72件のpublic JSON、private arm/gold/metrics、blank-final CSV、完了監査を生成 | 実行・変更しない |
| `tools/prepare_review_kits.py` | v1 code_hashesには含まれないが、frozen runnerのverify_seal・IO関数、source audit、実比較completion、public packet、REVIEWのコピーに依存 | 不封印だからといって改変しない。旧kit再現の出自として保持 |
| prepared kitの`criteria.md` | 両slotともREVIEWの同じhash `7ac3d9456f2f82ad9f67c575b91c840d309525d7050bff9fa8f2136a78f79b26` | 変更しない |
| `public/*`、`forms/*`、`START-HERE.md`、`view-order.json` | slotごと102件のpublic資料＋102空JSON票＋3制御ファイル＝207件をpacket manifestでhash固定 | 変更しない。両slotの207件ずつを調査時照合、欠損・不一致なし |
| `packet-manifest.json` | 上記ファイルhash、102件、gold/条件mapping/総合score非同梱、担当者未割当を記録 | 変更しない。manifest自体のhashはpreparation auditへ記録 |
| `preparation-audit.json` | slot path・manifest SHA、元104資料保全、担当者0・完了0 | 変更しない。人手レビュー完了の証拠ではない |
| Study 1の3.0/3.1/3.2 Protocol・freeze・failure/recovery記録 | 条件・公式評価・質問・sourceの固定と承認済み復旧の出自。Study 2のsource hashesから過去資料を参照 | 変更・再封印・旧campaign再開をしない |

manifest参照を含むv1 freezeは読み取り確認しましたが、本監査は全過去ProtocolをWindowsで再実行可能にする検査ではありません。旧path/改行/journal制約は[回帰範囲の記録](regression-scope.md)のまま保持します。

## 3. 旧仕様・旧票は何を評価できるか

[REVIEW.md](../REVIEW.md)自体は既にfact単位、局所可用性、引用適合性、抽出・公開、受け渡し、合成、複数原因ラベル、独立2名と不一致処理を扱っています。全面否定せず、概念を明示的schema・適用性・導出規則へ展開するのが今回の変更です。

確認した旧票の実装は次のとおりです。

- `audit.py`のblank-source CSV：fact_id、source_sentence_ids、citation_supported、worker_extraction、transfer、synthesis、final_supported、cause_labels、rationale等。必要fact本文、Worker別stage、stage 0/3の専用field、列挙値・導出ルールは独立fieldとしてありません。
- `analysis.py`のblank-final CSV：case_code、reviewer_id、final_supported、rationale、confidence、reviewed_at。最終内容の支持評価が中心で、factごとの段階判定を直接記録する列はありません。
- `prepare_review_kits.py`の`blank()`：source/final共通の空`facts`配列と`fact_entry_fields`一覧があり、necessary_fact、local_availability、worker_extraction、公開・入力箇所、transfer、synthesis等を記録可能です。ただし一覧は記入案内であり、六stage列挙値を強制する独立JSON Schema／validatorではありません。
- source票の`target_reference`が主対象C3を示し、匿名C1/C2を参照できます。両slotは同じ校正2問を先頭、残り28問と新72回答をslot別の固定閲覧順にしています。

旧kitでは引用と内容の関係、抽出・合成の予備分類、finalの原文支持、正規化後の受け渡しを検討できます。しかし六stageを分けた一致率やfirst/secondary failureを、旧自由記述から欠測なく自動復元できるとはしません。旧判定が将来存在しても、足りないstageをAIで補完せず、新revisionの独立判定と区別します。

## 4. 新RQ2への不足と新kitに必要な入力

| 分析項目 | 旧kitにあるもの／限界 | 新kitを作るなら追加・明示するもの |
| --- | --- | --- |
| 必要factと原文 | public原文・質問、自由なfact記入。共通registryなし | 匿名question_key、支持経路・代替support set、必要性とbasis、fact registry revision。goldは別管理 |
| S1アクセス | source packetにavailable sentence IDs。final packetには元Worker partitionを独立掲載しない | fact支持集合に対するWorker別available/missing IDs、元request／policy／partition参照・hash。新72件から元C3を指す匿名source linkage |
| S2抽出とS3公開 | source packetのWorker公開responseと、合成context内のArtifact。区別の判定field・出自が曖昧 | 公開response／Artifactそれぞれのpointer・hash・意味判定、前後記録の有無、分離不能field。hidden reasoningは追加しない |
| S4受信 | actual synthesis contextは掲載。typed matchはsource audit側で、blind配布しない評価情報も含む | 評価情報を除いた通信照合だけの機械項目と出自、Artifact経路と補足原文経路の分離、受信factの意味状態 |
| S5利用 | final outputと引用はあるが、入力factの利用可能性・適用性を分離していない | 必要な回答関係、別支持経路、短い回答で判断不能な場合の規則、観測的利用の限界 |
| ラベルと一致率 | generic cause_labelsとrationale、校正・独立票はある | 六stage enum、null/unclear/not_applicableの区別、Worker path／fact pipeline、first_failure_status、secondary labels、rule revision、共通単位と分母 |
| provenance／版管理 | packet-manifestとsource audit hash | 新schema/criteria/registry/generator/source-linkage hashと旧kit識別子、機械項目と人間項目の別保存、独立票・adjudicated票の別version |

新72件のpublic JSONは`case_code/question/public_sentences/synthesis_input/output`を持ちます。WorkerのArtifact自体は合成入力から読めますが、元Workerの実入力・公開response・partitionを前後別記録として追跡する情報は独立に補足する必要があります。同じWorker判定をA/B/Cそれぞれ新観測として数えません。

追加するのは保存済み公開・許可範囲の記録とその対応であり、新生成・入力修復ではありません。private gold、条件mapping、score、監査ラベルを配布用public資料へ混入させません。旧source auditの全JSONをそのままblind reviewerへ渡す方法は採りません。

## 5. 移行方針・生成コードの扱い

新schemaを採用するなら、別名のkitとmanifestを作り、旧criteria/票/public packetは変更しません。実装前に以下を人間が判断します。

1. 新段階別仕様を採用するか、そのrevisionと旧レビューとの関係。
2. 2名の担当者・独立性、fact registry準備、校正、匿名化、gold提示時点。
3. 機械的provenanceの追加が可能か、S2/S3を分離できない資料の扱い。
4. 新kitの保存先、共有範囲、ライセンスとprivate情報の分離。
5. agreement／kappa・欠測・適用性・不一致処理の基準。

将来コードが必要なら、frozen `audit.py`／`analysis.py`を書き換えるのではなく、読み取り専用sourceを使う別のversioned kit builderを検討します。既存`prepare_review_kits.py`は出自を残し、新builderを別名・別revisionにする方針です。新builderは条件・集計scoreを見せず、stage fieldは空で生成し、人間が原型をコピーした別票へ記入します。prepared原型を直接埋めてmanifestと不一致にしません。

これは設計提案であり、今回はgenerator変更、JSON Schema実装、新kit・新判定票生成、配布、レビューの記入を実行していません。raw/local/private資料をGitへ追加していません。次のモデル実験も、独立レビュー・不一致処理→failure pattern→specific hypothesis→新しい確認計画と承認、の後に判断します。

## 6. 文書編集後の読み取り専用検証

- 編集前snapshotの1,430ファイルをSHA256で再照合し、変更は予定した現行文書6件（root README、研究現在地、教員相談概要、主張対応表、current-outline、Study 2 README）のみで、欠損はありませんでした。別途、新規の設計文書3件を追加しました。
- v1のcode 102件・source 424件、計526件は封印hashとすべて一致しました。freezeそのもの、生成コード、historical protocol／failure記録、旧空票は編集前snapshotから変わっていません。
- prepared kitは両slotとも207件すべてmanifestのhashと一致し、manifest自体もpreparation auditのhashと一致しました。criteria・public資料・空フォームを変更していません。
- 新規・更新文書9件のローカルリンク124件の参照先が存在し、`git diff --check`で空白エラーはありませんでした。既存の未追跡mock出力もそのまま保持しています。

これは文書と保存資産の保全確認であり、新しい研究統計・意味的評価・Runtimeテストではありません。新たなテストや実験の実行結果として報告しません。
