# 失敗が続いた理由と、今回直した範囲

2026-09-29 JST。研究結果の解析ではなく、実行基盤と診断方法の改善記録。

## 結論

同じ原因で失敗し続けたのではない。時間制限、backendの生成上限の
互換性、生成打ち切りという別々の問題を順に踏んでいる。
さらに、失敗した応答の記録不足と、実際より軽い診断入力によって、
原因を絞り込んで改善を確認するサイクルが不十分だった。

**Multi-Agent設計の失敗、C3の劣位、2048→4096で解決、のいずれも証明されていない。**

| 実行 | 確認できる直接の停止理由 | まだ分からないこと |
| --- | --- | --- |
| Protocol 2.1 | 90秒の期限超過、1 run / 3 calls | モデル処理・待ち行列・マシン負荷の寄与 |
| Protocol 2.2 | C3 Synthesizerが約300.01秒で期限超過、4 runs / 16 calls | 短いC3入力がC2より遅くなった理由 |
| Protocol 2.3 | 5 run目 C3 worker_0 が約431.35秒で `provider_output_truncated`、5 runs / 19 calls | thinkingと最終JSONのどちらに生成量を使ったか、繰り返しの有無 |
| token-budget-v1診断 | 6 calls全成功だが、生成量は422〜472 token | 失敗した入力を2048または4096で処理できるか |

Protocol 2.3のエラーはadapterが `finish_reason=length` を検出したときに発生する。
600秒の期限超過ではないため、timeoutだけ増やしても、この停止理由は解消しない。
過去の失敗応答は残っていない。後からその内容や実測token数を復元してはならない。

Protocol 2.2までの `max_completion_tokens` とOllamaの互換性問題は、
2.3では明示的な `max_tokens=2048` に修正済みである。
この生成上限を「thinkingを使い切った後に別枠で2048 tokenの最終JSONを出せる」
という意味にはできない。default-thinkingとこの上限の組合せが足りない可能性はあるが、
失敗応答がない以上、thinkingが原因だったと断定できない。

根拠は [2.3失敗記録](qwen3-14b-protocol23-operational-failure.md) と
[6-call診断の実測結果](token-budget-diagnostic-results.md) を参照。
ローカルの `~/.ollama/logs/server.log` も確認したが、最終記録は9月28日23:11 JSTで、
翌日の当該失敗を説明するサーバログはそこにはなかった。

## 検証側の問題

前回の診断で成功したことは、元の問題が直った証拠ではなかった。
入力の構造比較を `recovery_audit.py` で再現できるようにした。

| 入力 | 報告対象field数 | 推論ルール | 選択ルール | 前提の出現数 |
| --- | ---: | ---: | ---: | ---: |
| 実際に失敗したworker | 6 | 4 | 2 | 14 |
| diag-direct | 2 | 0 | 0 | 0 |
| diag-partial | 3 | 1 | 0 | 3 |
| diag-artifacts | 3 | 1 | 1 | 4 |

これらは構造の違いであり、token数の推計や失敗原因の因果証明ではない。
artifact診断の入力文字数は失敗workerと近くても、扱うルール構造は異なる。
単に文字数を合わせるだけでも不十分である。

## 今回の実装

完了済み診断も独立したsealを持つため、元の `operational_diagnostics/` を
編集せず、新しい `operational_recovery/` に以下を追加した。

- 保存済みcall journalから、**実際にAgentへ渡した入力だけ**を読み込む。
  GlobalStateやgoldから再構成しない。prompt/schema/configも元のまま読み込む。
  CIでも検査できるよう、そのpublic requestだけをprovenance付きfixtureとして保持し、
  request SHA256をテストで固定した。保存済み応答やgoldは含めない。
- 凍結済みproviderをそのまま使い、HTTP応答の観測を例外発生より前に行う。
  `length` でも、報告されたusage、finish reason、取得できた最終回答JSONのprefixを保持する。
- 独立したreasoning/reasoning_contentは文字数のみ。inline thinkingや不明な
  top-level field、通常のprose、HTTPエラー本文、refusal本文は保存しない。
  不完全なJSONを補完しない。機密性を優先し、疑わしい回答は全体をwithholdする。
- タイムアウト・cancel・schema failureとlength terminationを分ける。
  応答がなければusageは不明のままで、0 tokenとは記録しない。
- 単発実行・fresh directory・過去campaign保護。retry/resume/上書きはしない。
  実HTTP transportは拒否する。この回帰用executorは**fake HTTP専用**である。

fake応答中の途中JSONはテスト用に作ったもの。
**5 run目の失われた出力を復元したものではない。**
観測hookはまだ研究runnerへ組み込んでいない。Protocol 2.3のsource・freezeを
後から変えないためであり、既存の実行コマンドを再実行してはいけない。

この記録方式は明示的な最終回答channelを前提とする、合成非PIIデータ専用の診断。
任意のbackendや機密文書に対する万能なPII除去機構ではない。
保守的な文字列検査で、正当な最終回答もwithholdされることがある。

## 再現コマンド（実モデル呼び出しなし）

```bash
uv run python experiments/epistemic-diversity/recovery_audit.py
uv run pytest -q experiments/epistemic-diversity/tests/test_operational_recovery.py
```

監査はread-onlyで、readinessは `not_demonstrated` と出す。
fakeテスト成功を実モデルの完走保証へ昇格させない。

## 次の実モデル実行に必要なこと

追加の合成ミニ問題を成功させるのではなく、失敗した入力と、上限に近かった
入力を対象にした**別枠のengineering reproduction**が必要である。
同じ入力・prompt・schemaで生成上限だけを変えるなら、その変更とcall budgetを
先に承認・記録し、研究cohortとは分離する。旧runの修復や成績更新には使わない。

4096で足りるとはまだ言えない。生成量を増やすと600秒に達するリスクも増える。
thinking無効化・temperature変更・model変更も研究条件の変更なので、黙って行わない。
まず取得したfinish reason、実測usage、最終回答prefixで、何に制約されているかを
確認する。失敗が再現しなかった場合も「修正成功」ではなく「再現せず」と報告する。

今回の到達点は **診断と失敗保存処理の改善**。
**Qwen3による12/12 pilot完走は未達・未再検証**。新しいreal callは0。

## 最終検証

- Runtime + research tests: **244 passed / 3 skipped**（新規19件を含む）。
- Formatter、lint、Runtimeと実験・診断コードのstrict type check: pass。
- Protocol 2.3 freezeと既存6-call診断seal: 両方有効。
- 保存対象2,805ファイルについて、rootごとのpath/content SHA256集合を比較し一致。
  `runs/` 全体、benchmark、freeze、prompts、configs、app/、研究src/、旧診断を含む。
- 機械可読な保持証跡: `results/operational-recovery-validation.json`。
