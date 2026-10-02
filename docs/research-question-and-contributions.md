# 研究目的・Research Questions・Contributions

設計revision：`research-framing-v1`、2026-10-02。
確認した最新mainは`213906dd6d30ab29ba0a66ecc78c3dfee1044d24`、作業ブランチHEADは`8dbb5a9525087d82d96142e136e67547ad09fb5b`で、ファイル内容は一致していました。

本書は、実施済みStudy 1/2と今後の内容分析を一貫して説明するための研究目的・用語・主張範囲の基準です。過去の事前計画や主評価を変更する文書でも、事後に事前登録を主張する文書でもありません。以降の現行要約・論文構成はこの定義に合わせます。新しい実験の実行承認は含みません。

## Research Objective

LLMマルチエージェントシステムにおいて、エージェントに与える役割の多様性と、アクセス可能な外部情報の多様性が、協調的な回答生成にどのように関係するかを調べる。さらに、情報を分割した条件において、回答に必要な情報が、原文参照、Workerの公開出力での抽出・表現、公開Artifactへの保持、Synthesizerへの伝達、最終回答での利用という過程でどのように保持・欠落・変形・不使用されるかを、保存済みの入力・公開出力に基づき分析する。

主題はRole Diversity、実際の外部情報アクセス差としてのEpistemic Diversity、および情報フローの分析です。Runtimeは、条件をプロンプト指示だけに依存せず実装・監査する実験基盤であり、Runtime単体の新規性を主貢献には置きません。Epistemic Diversityはモデル重み・事前学習知識・人格・信条の違いを意味しません。

## RQ1：役割・情報アクセスと回答性能

**同一LLMを用いたマルチエージェントシステムにおいて、役割の多様性と外部情報アクセスの多様性の違いは、最終的な回答性能にどのように関係するか。**

Study 1のC0〜C4はこの問いに対する比較枠組みです。C2はrole-diverse＋full access、C3はneutral role＋partitioned accessであり、主比較C3−C2は二要因を同時に変えます。roleとaccessの主効果をこの対比だけで識別したとはしません。C1/C3等の同role比較を含む設計が存在しても、事後に主比較を変更せず、副比較の補正・資源差・標本制約を保持します。

固定30問・5条件・単一モデル／反復の結果は限定的な観測です。Study 1時点の未観測fresh24におけるC3−C2 Answer F1差−0.15643は、その条件・選択標本での差として報告します。全30問は累積探索的集計です。

## RQ2：観測可能な情報フロー

**情報アクセスを分割したマルチエージェントシステムにおいて、回答に必要な情報は、原文参照、Workerによる抽出・表現、公開Artifactへの保持、Synthesizerへの伝達、最終回答での利用という各段階でどのように保持・欠落・変形・不使用されるか。**

判定単位は原則として必要factです。原文にあること、実入力に含まれること、意味的に正しい表現、公開payloadへの保持、実合成入力への到達、最終出力との整合を分けます。引用IDの正しさを意味的抽出の正しさと同一視せず、payload一致を意味的保持の証明とも扱いません。

Workerの内部思考やLLMのhidden chain-of-thoughtは観測しません。「抽出」は保存された公開出力で正しく表現されたか、「利用」は入力と最終出力から評価できる支持・整合の範囲を指します。別々の前後記録がなく抽出と公開の失敗を区別できない場合や、短い回答から利用経路を特定できない場合は`undetermined`／`unclear`を残します。

RQ2の意味的分析は独立人手レビュー未実施です。Study 2はこの問いを動機とした探索的追加実験であり、RQ2全体や因果機構を解決したものではありません。[段階別計画](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan.md)を参照してください。

## Contributions：現在の貢献候補と証拠の境界

| 候補 | 現在の内容 | 達成・未達成の境界 |
| --- | --- | --- |
| Contribution 1：実験枠組み | Role Diversityと実際の外部情報アクセス差としてのEpistemic Diversityを区別し、同一モデルの条件格子として比較する枠組み | Study 1を実行済み。C2/C3から単一要因の因果効果は識別していない。既存研究に対する新規性・網羅性は別途検討が必要 |
| Contribution 2：条件の実装・監査 | allowlist、ACL、detached context、typed Artifact等により、Agentごとのアクセスと公開経路を実装・監査可能にした実験基盤 | 実装・アクセス監査の証拠はある。完全sandboxや意味的confidentialityの保証、Runtime自体の新規性を主張しない |
| Contribution 3：観測から探索的介入・段階別分析への接続 | Study 1の観測から情報保持・統合の仮説を立て、固定WorkerのStudy 2を実施した。単純な引用原文復元で今回の性能差を十分説明する支持は得られず、段階別分析を次の分析課題として定義した | Study 2のモデル比較は完了。原因特定・information bottleneckの証明ではない。独立人手の段階別分析結果はまだ存在せず、達成済み貢献として数えない |

Study 2の既存24問のAnswer F1はA=0.5666、B=0.5805、C=0.5805、B−A=+0.0139、B−C=0です。「単純に引用原文を戻せば改善する」「情報圧縮による情報量減少がStudy 1の主原因だった」という説明は今回支持されませんでした。ただし効果ゼロや情報損失一般の否定ではなく、未引用文は復元していません。既観測標本・一反復・総compute非同一の探索的介入です。

## 研究ストーリーと次段階の境界

```text
役割の違いと外部情報アクセスの違いを区別する
  → Runtimeで比較条件を実装・監査
  → Study 1：C2/C3等の比較と限定的な性能差の観測
  → 仮説：必要情報の抽出・公開・保持・利用に課題がある可能性
  → Study 2：固定Worker＋引用原文／中立文対照
  → 引用原文追加固有の平均改善は今回支持されず
  → 段階別独立人手分析（未実施）
  → failure pattern → specific hypothesis → 確認実験の提案・事前計画
```

現時点では一つの研究ストーリーとして扱う方向を基本案とします。投稿形態・一論文化の最終判断や採択可能性は未確定です。独立人手レビューと不一致処理が終了し、残る不確実性を明示するまで、次の確認実験は開始しません。その後も人間の判断、新たな事前計画・予算・承認が必要で、自動実行へ進みません。

## Non-claims

- Epistemic Diversity一般がRole Diversityより劣る。
- 情報分割がC3性能低下の原因である。
- C2/C3でroleとaccessの因果主効果を分離した。
- Study 2がinformation-loss mechanismを証明または否定した。
- raw evidenceは一般に無意味、または今回の平均差0が同等性を証明した。
- Runtimeが完全なconfidentiality、process sandbox、意味的真実性を保証する。
- 24/30問の結果をHotpotQA全体やLLM一般へ一般化できる。
- 人間の集団知・認知多様性と同じ現象、または内部思考を測定した。
- 段階別レビューを設計したこと自体が独立人手検証の完了である。

## 根拠

[Study 1事前計画3.1](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)・[復旧計画3.2](../experiments/epistemic-diversity/docs/protocol-3.2-hotpotqa-recovery.md)・[最終結果](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)、[Study 2 PLAN](../experiments/synthesis-evidence-preservation/PLAN.md)・[結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)、[Runtimeの情報フロー](information-flow.md)・[安全境界](security.md)、[主張と根拠](research-claims-evidence-map.md)。旧仕様の保全と新レビューの差分は[依存監査](../experiments/synthesis-evidence-preservation/docs/review-stage-amendment-and-kit-impact.md)に記録します。
