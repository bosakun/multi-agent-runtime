# HotpotQA Protocol 3.1：Windows journal保存異常

2026-09-29。実験は2026-09-29T13:12:12Zにfail-stopした。
全実験完了ではない。元campaign・freeze・binding・ledger・結果は変更せず保持する。

## 確認した事実

- Pilotは18ケース・54予約／54 native応答、すべて正常終了。
- 本実験追加分は72ケースを実行。71正常・1partial、251予約／250 native応答。
  合計では89正常・1partial・60未着手、305予約／304 native応答。
- 異常ケース：QA `5adc0c2b55429947ff1738db`、条件C1、
  run `cddc69d9e35c4232911e3b306a5585fc`。
- worker_0のjournalは `error=PermissionError`、応答なし、latency3.7921ms。
  native wire auditのbounded contract／maxItems40は設定済みだが、
  このworkerのnative応答観測ファイルは存在しない。
- worker_1／worker_2は正常。各prompt3462tokens／output168tokens、
  finish_reason=stop、thinking0、両方ともcandidate_answer=no。
  synthesizerは実行されていない。final predictionは空、公式スコアは0として残った。
- 原文入力射影・private inputs・out-of-scope IDsの記録上の違反は0。
  モデルの不正引用や出力切断を示す記録はない。
- 問題のjournal pathは212文字で、現在の属性はArchive。恒常的な長すぎるpathや
  ReadOnly属性を示す証拠はない。

## 原因の判断と不確実性

固定された `epistemic.paths.write_json` は `.json.tmp` を書いて既存journalに
replaceする。native HTTPの送信前hookでこのcheckpointを複数回行う。
bounded wire auditが設定済み、3.8msでのPermissionError、応答・観測なし、
他workerの正常応答という証拠から、送信直前のjournal保存／replace異常と判断する。
ローカルモデルが問題を解けなかったことを原因とする証拠ではない。
詳細な例外文／OS subcodeは安全なjournalに保存していないため、具体的に何が
ファイルをロックしたか、Windows共有違反だったかは確定できない。

## 保存・テスト

停止後も `hotpot_full.py verify` は同じbindingを確認した：
`abc37681a57b907b4db88998898aaaaadfad2f5bf4b774ab6cc53cd4917e7670`。
`reports/hotpot-main-preservation-after-failure.json` は既存1147ファイル変更・削除0。
Git tracked/cached diffも空。stage／commit／pushをしていない。
最終回帰テストは210合格・2skip、294.73秒。live API E2Eは除外。
skipはPostgreSQL URLと非配布implementation-local baseline。
独立完了監査はMock150ケースで合格したが、この不完全な実cohortには適用できない。

## 完了に必要な追加判断

元のhard reservation ceiling510／no retry・resumeは引き続き有効。
勝手に原campaignを再開したり、失敗したreservationを払い戻したりしない。

最小復旧案：既存89正常ケースと、失敗C1内のworker_1／worker_2正常出力を
改変せず再利用し、欠けたworker_0とsynthesizerの2生成、および60未着手ケースの
204生成を、新しい事前計画・source freeze・campaignで実行する。
journalは既存ファイルreplaceを避けたappend-only版を別実装し、Mockで検証する。
これなら追加206予約。合計予約は511、正常native応答は計510が予定値となる。
送信前IO異常の1予約は失敗履歴として保持・計上し、隠さない。
元計画の予約上限を1増やすため、実生成再開前にユーザーの判断が必要。
既存成果物・正常モデル出力・質問集合・役割／アクセス・native controls・
公式評価を変更しない。復旧例を別の統計的反復として水増ししない。
