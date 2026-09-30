# 固定Worker出力への引用原文追加：Windows実比較の結果

2026-09-30。研究IDは`synthesis-evidence-preservation-v1`です。

予定した3問のsmokeと既存24問の3条件比較は、81予約・81正常応答で完了しました。Workerは再生成していません。一方、独立人手レビューは0/2名で未実施です。モデル比較の完了と、研究全体の完了は区別します。

## 結果の要約

引用元原文を追加したBのAnswer F1は、要約のみのAより平均0.0139高くなりました。ただし、同程度の入力量を足した中立文Cとの差は0でした。質問ごとの改善と悪化もあり、平均が同じだから全回答が同じという結果ではありません。

この標本では、引用原文の追加に固有の平均回答改善を支持する所見は得られませんでした。効果がないと確定したわけではなく、区間は広く、24問・一モデル・一反復という制約が残ります。

| 条件 | Answer F1 | Answer EM | Support F1 | Joint F1 |
| --- | ---: | ---: | ---: | ---: |
| A：固定Worker出力のみ | 0.5666 | 0.3333 | 0.5899 | 0.3897 |
| B：同じ出力＋引用原文 | 0.5805 | 0.3333 | 0.6246 | 0.4006 |
| C：同じ出力＋中立文 | 0.5805 | 0.3333 | 0.5485 | 0.3821 |

| 比較 | 平均Answer F1差 | paired bootstrap 95%区間 | 改善 / 同点 / 悪化 |
| --- | ---: | --- | --- |
| B−A：主比較 | +0.0139 | [−0.1111, +0.1250] | 2 / 21 / 1 |
| B−C：計画した対照 | 0.0000 | [−0.1250, +0.1250] | 1 / 22 / 1 |
| C−A：記述的比較 | +0.0139 | [0.0000, +0.0417] | 1 / 23 / 0 |

bootstrapは計画どおり10,000回、seed20260930です。これは既に結果を観測していた24問に条件づけた探索的な区間で、確認的な有意性の主張には使いません。public文書titleの共有による連結成分は24個、すべて1問でした。そのためcluster感度確認の区間は質問単位の区間と同じです。意味的な依存がないと証明した結果ではありません。

BのSupport F1はA/Cより高い記述値でした。ただし、BのSupport recallは0.5799で、Aの0.5903、Cの0.6146より低く、Support precisionはBが0.7639、Aが0.7007、Cが0.6279でした。「必要な根拠をより多く拾えた」とは言い換えません。これは補助的な結果で、主評価の回答改善や原因の確定とは分けます。

## 何を固定し、何を追加したか

保存済みC3の同じ3 Worker出力と順序を使い、Synthesizerへの補足だけを変えました。Bの原文はWorkerが公開出力で引用したsentence IDから機械的に取り出し、gold回答・支持文・監査ラベルでは選びませんでした。Cは固定の中立文を繰り返した対照です。

3条件とも、原文追加と矛盾しない同じ共通instructionを使っています。元の最終回答をAに流用せず、新しく生成しました。新Aと歴史的C3の平均F1差は−0.000784でしたが、指示変更を含む再実行差で、純粋な再現性試験の結果とは扱いません。

モデルは同じdigestのQwen3:14b、Ollama 0.34.4です。temperature0、think=false、context8192、input/output上限各4096、concurrency1、retry/repair/resumeなしで実行しました。smoke9件を本比較72件の集計に加えていません。2問の重複も独立標本数へ加えていません。

## 計算資源とGPU実機確認

| 条件 | 平均input tokens | 平均output tokens | 平均call latency（秒） |
| --- | ---: | ---: | ---: |
| A | 1619.58 | 128.25 | 3.454 |
| B | 2150.13 | 110.50 | 3.350 |
| C | 2126.46 | 127.08 | 3.631 |

実応答のB/C input token差は最大1.893%で、事前の5%許容範囲内でした。全81件のnative input countは、ローカルtokenizerの事前計測と一致しました。最大入力は3554tokenです。tokenizer自体も保存済み120呼び出しと全件一致しています。

入力量を近づけたことは、総computeの同一性を意味しません。output量・処理時間・cache等が異なり得ます。上表はSynthesizerの本比較分だけで、過去に実行した固定Workerの計算量を新たに計上した値ではありません。

実機はRTX 4070 SUPER、driver 591.86、VRAM 12282 MiBでした。モデルblobの実バイトSHA256を確認し、全81件の`/api/ps`で対象モデルのdigest・context8192・GPU residencyを照合しました。生成中の10回のNVIDIA観測では、GPU利用率27〜100%、VRAM使用量10650〜10651 MiBでした。ホスト全体のsamplingであり、条件別computeへの直接帰属は主張しません。

## 完了した機械的検証

- 81件の予約内容、順序、入力、canonical journal、native observationと、162件のDBイベントを照合しました。独立人手レビューではなく、別の読み取り専用コード経路による再照合です。
- official予測exportを同じpinned HotpotQA scorerで再計算し、3条件の集計と一致しました。
- Schema・引用権限・native token上限・thinkingなしの検査に全81件が合格しました。hidden reasoningは保存していません。
- 元30問のC3と参照C1/C2の公開出力を照合し、スキーマ正規化後の受け渡し不一致は0件でした。Workerの要約中の意味的欠落や、合成段階での不使用を否定する検査ではありません。
- 参照元424ファイルの保存監査は変更0件で、freezeも一致しました。元campaignや既存未追跡ファイルは削除・上書きしていません。
- 開始gateは398 passed、4 skipped、25件の理由付きarchival除外でした。最初の広いsuiteの未合格と、旧Windows path/CRLF・旧journal欠落の制約は[別記](regression-scope.md)しており、全repositoryがgreenとは主張しません。

最初のMockのwinerror32記録は残しています。自分の一時linkのcleanupエラーが公開済み結果を無効にしないよう対策し、実比較は正常終了しました。過去の保存エラーの具体的なlock所有者や、今回と同じ原因だったかは未確定です。

## 残る作業と資料

実装・入力作成者以外の2名による、元30問と新72回答の内容検証・一致率集計・不一致処理が残っています。担当者は未定です。原文→Worker要約→合成入力→最終回答のどこで必要な事実が欠落・変形・不使用になったかの意味的分類は、その判定前に確定しません。

別モデル、追加反復、未観測標本、公式dev全7405問、情報分割そのものや総計算量を統制した比較は、[事前計画](../PLAN.md)にある後続研究です。本比較で検証済みとは扱いません。今回の結果だけで介入を本体へ採用したり、追加生成を自動実行したりしません。

- [機械的完了監査](../reports/real-fixed-workers-20260930/completion-audit.json)
- [DB・export・資源の再照合](../reports/real-fixed-workers-20260930/independent-execution-audit.json)
- [分析JSON](../reports/real-fixed-workers-20260930/analysis.json)、[ケースCSV](../reports/real-fixed-workers-20260930/cases.csv)
- [新72回答の匿名public資料](../reports/real-fixed-workers-20260930/review/public/)、[2名分の空の判定票](../reports/real-fixed-workers-20260930/review/blank-final-review.csv)
- [レビュー引き継ぎ](../REVIEW-HANDOFF.md)、[freeze](../freezes/v1.json)

raw資料・DB・詳細ログ・判定票はGit管理外のローカル資料です。上のreportsリンクはそれらが存在するこのPCで参照します。`study.json`のstatusや件数は計画作成時のsnapshotで、現在の実施状態はこの報告と実行監査を参照します。commit/pushや外部共有は今回行っていません。
