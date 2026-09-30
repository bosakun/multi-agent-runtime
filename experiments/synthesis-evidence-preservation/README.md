# Synthesis Evidence Preservation

Workerの公開出力からSynthesizerの最終回答まで、必要な事実がどう保持されるかを調べる独立した研究です。

前の研究は、HotpotQA distractor devの30問×C0〜C4・150ケース・510正常生成の比較として完了しました。C3が低かった原因の特定、独立人手検証、他モデルへの一般化は、その比較から生まれた次の問いです。研究全体の問いが残っていることと、一つの実験が完了していることは両立します。

今回の問いは、保存済みC3 Worker出力に、Worker自身が引用した原文を添えると最終回答が改善するか、です。Workerを固定した3条件比較を中心にします。

| 条件 | Synthesizer入力 |
| --- | --- |
| A | 保存済みWorker出力 |
| B | 同じWorker出力＋引用元原文 |
| C | 同じWorker出力＋Bと同程度のtoken量の中立文 |

## 最初に読む資料

- [Windows実比較の結果](docs/qwen3-14b-windows-outcome.md)：81件の実生成と集計、未完了の人手レビューを区別した報告。

- [独立レビューの引き継ぎ](REVIEW-HANDOFF.md)：担当者未定のまま準備した資料と、担当者が決まった後の手順。

- [研究計画](PLAN.md)：仮説、入力の作り方、3問の動作確認と既存24問の比較、分析・完了条件。
- [レビュー基準](REVIEW.md)：原文・公開出力・最終回答の内容検証と、独立人手レビューの手順。
- [運用・検証計画](OPERATIONS.md)：source保全、Mock、token計測、保存エラーの観測、実生成の開始条件。
- [機械可読の計画仕様](study.json)：質問ID、予定81呼び出し、設定、参照元のhash。実行済みmanifestやfreezeではありません。

固定Worker比較のrunner、レビュー資料、tokenizer検証、source freeze、81件の実比較と集計は完了しました。独立人手レビューは0/2名で未実施です。Answer F1はAが0.5666、BとCが0.5805で、引用原文追加に固有の平均回答改善を支持する所見は得られませんでした。旧研究のfrozen runnerとcampaignは読み取り専用で参照しています。

計画作成時に、元の完了監査と累積結果の150ケース・510正常生成、参照3ファイルのSHA256、C3の30問分・120 agent journalの存在、24問IDとpublic/gold資料の存在を確認しました。3問×3条件＋24問×3条件＝81回、動作確認と本比較の重複は2問です。これはsourceと計画の整合確認で、新しい実験結果ではありません。

## 研究資産の置き方

```text
experiments/synthesis-evidence-preservation/
  README.md / PLAN.md / REVIEW.md / OPERATIONS.md
  study.json                 計画仕様
  assets/length-control.txt  入力量対照の固定原文
  src/・tests/               固定入力replayと検証
  freezes/                  実装・入力確認後のsealを保存
  data/                     replay入力・private評価資料（Git管理外）
  runs/                     新規campaign・台帳・DB・journal（Git管理外）
  reports/                  監査・レビュー・集計（Git管理外）
```

実データを旧フォルダから移動する必要はありません。`study.json`に指定した保存記録を読み、新しい成果物だけをこの研究の保存先に作ります。rawデータ・DB・詳細ログの公開範囲は、要約と分けて決めます。

## 前の研究との接続

- [前の研究の完了報告](../epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)
- [前の30問と24問の事前計画](../epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)
- [Windows保存エラーの記録](../epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol31-operational-failure.md)

旧研究の`STATUS.md`には過去のPilot停止時点の記述が残っています。現在の完了状態は上記のProtocol 3.2完了報告とその監査を参照します。
