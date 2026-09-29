# HotpotQA 30問×5条件：本実験開始時の検証記録

2026-09-29。これは開始時のgate記録であり、実験完了や最終成績の報告ではない。
[現行実験](../ACTIVE_EXPERIMENT.md)、[事前計画](protocol-3.1-hotpotqa-main.md)を参照。

## 完了した事前検証

- Protocol 3.0の実Pilot：6問×C0/C2/C3、18ケース・54呼び出し、全件正常終了。
  公式採点と独立に、入力射影・証拠アクセス違反0件を確認。
  Pilotの回答F1はC0/C2とも0.892857、C3は0.726190。
  この6問の結果を理由に本実験の質問を選び直していない。
- 30問は同じ公開文書長・構造規則とseed/QA-IDハッシュ順位の先頭30問。
  先頭6問の公開／正解ファイルはPilotとbyte単位で一致。
- 新規Mock：既存18ケースを再実行せず、欠けた132ケース・456回を追加。
  元のMockと合わせ150ケース・510回の完全な条件格子を検証。
  `reports/hotpotqa-main-mock-analysis/` に、全30問と新規24問の公式集計、
  新規24問の比較、CSV、保存出力レビュー、6枚のSVGを生成。
- 追加8テスト：偽native HTTP、全456回／累積510回の帳簿照合、旧Pilot再実行なし、
  C2/C4の同一役割対応、C3/C4の同一分割、予算不足拒否、不正引用による停止、
  source改変拒否、公式採点再計算、出力上書き拒否、SVGのXML／ラベルを確認。
- 独立報告コードは、保存された全requestの公開原文・方針・schema・引用権限、
  native wire controls、finish_reason、thinking0、token guardを再確認する。
  補助診断はPilot開始後に追加したものとして明示し、新たな主評価にしない。
- 新規コードRuff lint／整形検査・mypy（8 source files）は合格。
- 最終回帰検証：204合格・2skip、312.84秒。live API E2Eは明示除外。
  skipはPostgreSQL接続URL未指定と、Git非配布のimplementation-local保存baseline。
  テストのモデル通信はMock／偽HTTPであり、実生成ではない。

## 実行binding・実機観測

本実験binding SHA256：
`abc37681a57b907b4db88998898aaaaadfad2f5bf4b774ab6cc53cd4917e7670`。
freezeは `freezes/hotpotqa-dev-distractor-protocol-3.1.json`。
実行場所は `runs/hotpotqa-protocol31-qwen3-14b-windows/additional/`。
実行開始は2026-09-29T12:51:23Z（日本時間21:51:23）。

既存1147ファイルの開始前snapshot／実行中保存確認は
`reports/hotpot-main-preservation-before.json`／
`reports/hotpot-main-preservation-inflight.json`。変更・削除0件。
進行中にも `hotpot_full.py verify` が同じbindingを確認した。

`reports/windows-host/inspect-20260929T125213Z-eed3a4d566c348e1b173d68bffe2cb1a.json`
では、Ollama0.34.4、固定Qwen3:14b digest、context8192、100% GPU配置、
size／size_vramとも10,321,636,883 bytesを観測。
同時のnvidia-smiではRTX4070 SUPER、11,696／12,282MiB、使用率98%、68℃、202.52W。
GPU配置の100%と演算使用率98%は別の測定値であり、相互に換算しない。

## 残る完了監査

実モデルの追加132ケース／456回が終わるまで、全実験完了とは扱わない。
既存Pilot54回と合わせ150ケース・510回の格子・帳簿・journal、全公式スコア、
実入力アクセス、native完了状態、freeze、保存監査を再検証する。
成功した完全部分ではなく、指定された全条件・全質問の証拠を要求する。
終了後は `hotpot_full.py analyze` で、新規24問の推測統計と、
累積30問の探索的集計・補助診断・図・保存出力レビューを別々に保存する。
結果の解釈は事前計画の制限に従い、独立した人間のレビューと呼ばない。
