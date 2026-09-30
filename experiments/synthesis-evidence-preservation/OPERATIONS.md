# 実装・保存・検証の手順

## 参照元と新しい保存先

`study.json`が指定する元のanalysis/cumulative-resultsとsource auditを読み取り専用で開きます。累積metadataの`journal_roots`から質問ごとのC3を解決し、各agentのjournalをJSON内の`agent_id`と`run_id`で確認します。ファイル名を`synthesizer.json`と仮定しません。各agentの成功journalが一件でなければ停止します。

metadataにある絶対pathが移行先で存在しない場合は、元repo rootを新repo rootに置換して相対suffixを解決します。repo外へ抜けるpathは拒否し、結果が一意に確定しない場合は手動でsource対応表を作り、生成前にhashとともにfreezeします。

新しい成果物は、この研究内に保存します。

- `data/replay-inputs/manifest.json`内の`source_hashes`：元ファイル・public問題・private評価の参照とhash。private本文は入力側に露出しない。
- `data/replay-inputs/`：81件の入力、条件、引用集合、token数。goldなし。
- `reports/source-audit/`、`reports/review/`：30問監査とレビュー資料。
- `freezes/`：計画仕様、コード、全入力と条件順、tokenizer資産のseal。既存pathは再利用しない。
- `data/binding.json`：backend・host確認とseal対応。
- `runs/<new-campaign-id>/`：budget.sqlite、replay.sqlite、call journal、native observations、progress、terminal結果。replay.sqliteは新研究専用のイベント記録で、旧Runtimeの実行DBではない。
- `reports/<campaign-id>/`：公式予測JSON、cases.csv、分析JSON、summary.md、入力token差/品質差/失敗ラベルの図、完了・保存監査。

raw資料・DB・ログは新フォルダの`.gitignore`で除外します。計画・コード・tests・freezeはGit管理対象です。freezeには機器の識別情報やAPI key、gold本文を含めずhashで参照します。

## 次の実装順序

1. sourceを解決し、150ケース・510正常生成・元監査hashとの整合、30問のC3の120 agent journal、24問IDを確認する。sourceファイルの保存baselineを取る。
2. public-onlyローダー、固定Worker replay、引用原文抽出、中立文matcher、入力検査とtoken計測を実装する。最終出力は元の公式scorerへexportできる形にする。
3. 旧30問の監査資料を生成する。独立レビューの担当者・資料は実生成処理から分離する。
4. offline/fake HTTP testsと81件Mockを行う。全81入力の最終manifestとsealを作る。source/model/host driftを拒否するbindingを新規作成する。
5. 実生成の開始判断がされたらsmoke9件を実行する。技術gateに合格した同じfreezeでmain72件へ進む。
6. 完了監査、公式scorer再計算、source保存監査、結果報告を行う。人手レビューの完了状態を別記する。

CLIは`prepare`（生成0）、`audit`（生成0）、`mock`（実生成0）、`freeze`、`bind`、`verify`、`run`、`analyze`に分離します。`run`だけがモデル生成を行い、source/goldを使った入力作成や条件変更を内部で行いません。完了したMockも実モデルの研究結果とは扱いません。

## 必要な検証シナリオ

| 検証 | 合格条件 |
| --- | --- |
| 元研究の参照 | 指定hash・質問ID・正常status・公開artifactが一致。private資料をモデルContextへ入れない |
| 3条件の固定 | Worker payload・順序・共通指示・Schema・引用権限が同一。差は補足文字列のみ |
| 原文抽出 | 重複除去・field順が再現可能。unknown/out-of-scope IDは停止。gold fieldを混ぜた入力は拒否 |
| 中立文・tokenizer | 固定asset由来、B/Cの補足と全promptが許容差内。tokenizer/template未確認・上限超過は生成前に停止 |
| source不足 | ファイルなし、hash変更、重複journal、payload不一致は停止。自動代替・問題除外なし |
| 予算 | 81以内、smoke9以内、Worker0。送信前に予約、失敗も消費。82件目・再起動resume・refundを拒否 |
| native応答 | done/stop、Schema、引用範囲、thinkingなし、input/output上限、token対照を検査。不正・timeoutはfail-stop |
| 保存 | append-only checkpointとsingle-write terminal。既存ファイルを上書きせず、部分失敗を残す |
| Mock | 全81件のroute、9/72の段階境界、集計72セル、ledger/journal/export整合を検証。モデル性能の結果としない |
| 評価 | 既存公式scorerで再計算。誤答は保持し、smokeをmain統計へ加えない |
| Windows | DB close後のhandle解放、no-clobber保存、共有lock時の失敗記録が動く |

testsは新研究の仕様を対象に追加します。旧campaignやfreezeをテスト用に改変せず、Runtime本体との接続に必要な回帰テストはlive APIを使わず実施します。

## 保存エラーの観測

元事件の具体的なlock所有者とOS subcodeは記録不足のため未確定です。append-only方式の確認はできますが、過去の所有者を遡って証明できたとは扱いません。

新runnerは保存のphase、UTC時刻、process/thread ID、errno、winerror、repo相対path、操作（create/write/fsync/publish/close）を安全な診断記録に残します。payload本文・hidden reasoning・機器の秘密・認証情報を例外記録へ入れません。問題のファイルへの書き込みが失敗した場合も、別のexclusiveな診断pathへ記録を試み、失敗すればstderrへ上記情報だけを出して停止します。

共有lockの再現テストは診断用temp dirで行い、既存campaignを対象にしません。自然再発時は対象pathに絞った[Process Monitor](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)でprocessとfile operationを照合します。ツールの導入・OS権限が必要なら研究生成とは別の運用作業として扱います。lockしたprocessを自動killしたり、Defenderを無効にしたりしません。

診断用に再現できたエラーと元事件の同一原因を混同せず、元の原因は再発時の証拠がない限り未確定のまま報告します。

canonicalファイルのexclusive公開が成功した後、自分の一時hard linkの削除だけが共有lockで失敗した場合は、診断を記録し、一時linkを残します。公開済みのcanonical結果を失敗扱いにしません。公開自体の失敗は停止条件のままです。元の例外をcleanupの例外で上書きせず、既存成果物の削除や自動再送は行いません。
