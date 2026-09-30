# レビュー資料準備とoffline検証

2026-09-30時点の実測記録です。実モデルによる新しい生成は0回です。

- 旧30問のC1/C2/C3を読み取り、C3の120 agent journalと公開artifactを照合しました。スキーマ検証後のWorker出力と合成入力の内容不一致は0件です。数値の型正規化を含むため、raw JSON bytesの同一性を主張する結果ではありません。
- ローカルGGUFの語彙・merges・chat templateから作ったtokenizerは、保存済み120呼び出しのnative input countと全件一致しました。
- 3問×3条件のsmokeと既存24問×3条件の本比較について、81件の入力をモデル生成なしで作成しました。最大入力は3554tokenで、4096上限内です。B/Cの補足・全prompt token差は計画の許容範囲内です。
- 旧30問のpublicレビュー資料、評価用資料、2名分の空の判定票を準備しました。意味的な正しさと失敗原因は未判定です。
- 最初のMockは6予約・5件のterminal記録でwinerror 32により停止しました。記録は`runs/mock-review-preparation/`に保持しています。共有違反の所有processは特定していません。
- 一時linkのcleanupエラーが、公開済み結果や元の例外を無効にしないよう保存処理を修正しました。新しい保存先`runs/mock-review-preparation-v2/`でMock81件と集計・scorer export経路が完了しました。81予約、81 journal、81 observation、162 DB eventを照合しています。Mockのスコアはモデル性能ではありません。v2のcompletion-auditにあるpassed_model_comparisonはMock経路の合格を表す旧ラベルです。誤解を避けるため、現行コードではpassed_pipelineと実モデル比較の合格を分離し、最終検証はv3へ保存します。既存v2記録は上書きしません。
- 参照元424ファイルの保存監査は変更0件です。既存成果物は削除・上書きしていません。

source freeze・backend binding・実生成・独立人手レビューは未完了です。担当者は未定のため、[引き継ぎ資料](../REVIEW-HANDOFF.md)を先に用意しています。
