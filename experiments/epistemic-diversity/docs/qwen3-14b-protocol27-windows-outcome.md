# Windows Qwen3 Pilot 2.7 実行結果（2026-09-29）

実行安定化は確認できた。一方、固定評価器の課題完全成功は 0/12 であり、
研究上の成功・C3 の優位・主実験への準備完了とは扱わない。

## 改善と失敗履歴

- 2.5 の worker が thinking のみで出力上限に到達したため、2.6 で
  native `/api/chat`、`think:false`、context8192 を事前固定した。
  元の失敗入力１回は正常終了（出力313 tokens）した。
- 2.6 の新 Pilot は 11 calls、２正常 runs＋１部分 run で停止。
  diagnosis-medium/C2 worker_2 の最終 JSON 生成が4096 tokensに到達した。
  thinking はゼロだった。別予算１回の再現では、`uncertainty.evidence_ids`
  に同じ許可済みIDを繰り返し追加するループを確認した。
- [Protocol 2.7](protocol-2.7-amendment.md) は、全ての引用配列に
  `maxItems=len(AgentContext.evidence_scope())` を設定し、受信時にも検証する。
  enum・再帰的未知ID拒否を維持し、切り捨て・修復・retry はしない。
  同じ失敗入力１回が正常終了（出力773 tokens）し、新 Pilot を開始した。

旧コホートを再開・修正・分析・混合していない。goldをモデル入力に追加せず、
科学課題・seed20260928・C2/C3・１反復・評価器を変更していない。
各実機試行は事前のソース/設定/入力/backend bindingと個別の永続予算に拘束した。
今回の追加実機呼び出しは2.6診断1＋2.6 Pilot11＋再現診断1＋2.7診断1＋
2.7 Pilot48＝62。各診断上限1、各新 Pilot上限48を守り、旧残予算は再利用しない。

## 完了した 2.7 の確認事実

- 2026-09-29 19:55:48–20:05:41 JST、約9分52秒。
- ６課題×C2/C3、12/12 runs が runtime `succeeded`、各４calls、合計48。
- 48/48 native応答が `stop`、thinking出力0、切り詰め0、runtime error0。
- context/result/gold leak は全12 runsで0。
- 入力61219＋出力25952＝87171 tokens。１応答の最大入力3935、最大出力1070。
- 実機診断を含む2.7の実呼び出しは49。診断結果は研究統計に含めない。
- [生結果](../runs/qwen3-14b-protocol27-windows/pilot/results.json) の SHA256:
  `841071456dacd3d69eba6d877ef8865e64c12a7603903b618207a05d25295d1e`。
- compact recordsのlegacy token-field表記は、2.7だけ `options.num_predict` と
  正しく記録した。2.6の実際のwireはnative call journalに記録されている。

## 回答品質（固定評価器、各条件６課題）

| 指標 | C2 | C3 |
|---|---:|---:|
| 課題完全成功 | 0/6 | 0/6 |
| 事実カバレッジ平均 | 1.000 | 0.619 |
| 必須推論カバレッジ平均 | 0.333 | 0.167 |
| worker証拠カバレッジ平均 | 1.000 | 0.952 |
| unsupported項目数平均 | 2.000 | 4.167 |

最終conclusionの文字列は10/12でgoldと一致したが、それだけでは課題成功に
ならない。評価器はcanonical subject/valueと支持証拠集合の完全一致、必須推論、
unknowns制約、余分なunsupported項目なし等を要求する。例えばsynthesis/C2は
全事実・必須推論を満たしたが、insights内の追加 `decision=release_batch` が
canonical集合外の項目となった。`unsupported_claims` はこの固定判定の件数で、
自然言語の虚偽の数と同一視しない。diagnosisでは原因名をconclusionに出し、
必要な対処名 `cap_retries` と不一致。C3のconstraints/contradictionは必要な
事実の出力・支持引用の要件を満たさず、causalでは不足・矛盾もある。
単なるruntime障害ではない。

比較は６課題（各family１課題）だけの探索的Pilot。C3−C2の事実カバレッジ差は
−0.381、正確符号反転検定p=0.25、Holm調整p=0.5。C3優位も同等性も結論しない。
全て2.7単独の[固定分析](../runs/qwen3-14b-protocol27-windows/analysis/analysis.json)で、
12行metrics.csv、７SVG、[人間レビュー資料](../runs/qwen3-14b-protocol27-windows/analysis/pilot-human-review.md)
を生成した。実験後に評価器・gold・回答を書き換えていない。

## Windows・GPU・保全

[Windows用ガイド](../../../docs/windows-nvidia-ollama.md) はhost preparation専用。
その禁止事項を既存ガイドの編集で解除せず、後続のユーザー許可と新しい
prospective amendmentに従って研究実行を分離した。

- Windows native / RTX4070 SUPER / driver591.86 / Ollama0.34.4 / qwen3:14b Q4_K_M。
- モデルfull digestは全bindingと一致。ロード中context8192、size=size_vram
  10321636883 bytes、CLI `100% GPU` とAPI `full_gpu` を実行中に再確認。
  offload100%は計算利用率100%を意味しない。CUDA driver表示とruntimeも区別する。
- 実行中inspect: `reports/windows-host/inspect-20260929T110609Z-ed81275042de48e1a7fd582593fd8e99.json`。
- Mock smoke再確認: 6 mock calls、実生成0、SQLite close/rename/remove確認通過。
- 回帰テスト180 passed / 2 skipped。skipはPostgreSQL接続未指定と配布されない
  旧実装ローカル保全baseline。新しい608ファイルのSHA256保全確認は別途通過。
- 新規2.7のruff・mypy通過。2.5/2.6/2.7のfreeze/binding検証も実験後通過。
- `reports/protocol27-preservation-after.json`: 開始時の既存608ファイル全て一致。
  追加ファイルのみ。stage/commit/pushなし。Codex認証やアカウント設定は未変更。

## 未確認・次の安全な手順

主実験・追加反復・別モデル・Mac/Windows差の推定・温度/thinkingの効果分離は
未実施。６課題１反復の成功した実行から一般的安定性や研究効果は保証しない。

次は人間レビュー資料で、追加insight、支持集合の過不足、原因と対処の混同を
確認する。今のPilotをチューニング対象として再実行せず、改善するならgoldを
入力に使わない一般的な出力契約・推論方針を別protocolで事前固定し、独立した
未使用課題で検証する。Main/fullは自動開始していない。
