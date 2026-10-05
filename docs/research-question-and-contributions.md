# 研究目的・Research Questions・Contributions

設計revision：`research-framing-v2`、2026-10-02。v1の用語・分析設計を改訂する現行文書です。
今回のaudited base snapshotはmain `432a5ec85e78be31508ce250df6396ad7105041e`。作業ブランチの比較snapshot `8c9ea24fb0df6809077491206fb3637fa67f36ca`とファイル内容が一致していました。これらは監査時点の識別子であり、永続的な「最新HEAD」表記ではありません。

本書は、実施済みStudy 1/2と今後の内容分析を一貫して説明するための研究目的・用語・主張範囲の基準です。過去の事前計画や主評価を変更する文書でも、事後に事前登録を主張する文書でもありません。以降の現行要約・論文構成はこの定義に合わせます。新しい実験の実行承認は含みません。

## Research Objective

LLMマルチエージェントシステムにおいて、役割の多様性と実際の外部情報アクセスの多様性が、協調的な回答性能にどのように関係するかを調べる。さらに、同じreference evidenceに基づくfactsが、実Worker入力、Workerの公開表現、Artifact publication、実Synthesizer入力、最終出力のevidential supportに沿ってどのように保持・変形・欠落するかを、観測可能な保存記録に限定して分析する。

主題はRole Diversity、actual Information Access Diversity、およびObservable Evidence Lineageです。従来のEpistemic Diversityという条件名は実行時の外部文書アクセス差を意味し、モデル重み・事前学習知識・人格・信条の違いではありません。Runtimeは**experimental treatment integrity / auditable experimental infrastructure**です。intended visibility、actual serialized Worker input、public Artifact、actual serialized Synthesizer inputを保存・照合し、条件がprompt complianceだけでなく実input/routing levelで成立することを監査します。Runtime単体の新規access-control mechanismを主貢献にしません。

## RQ1：役割・情報アクセスと回答性能

**同一LLMを用いたマルチエージェントシステムにおいて、役割の多様性と外部情報アクセスの多様性の違いは、最終的な回答性能にどのように関係するか。**

Study 1のC1〜C4はsame LLM / same collaboration structureのneutral/diverse role × full/partitioned access格子です。C0はsingle-agent baselineで格子外です。C2はrole-diverse＋full access、C3はneutral role＋partitioned accessであり、主比較C3−C2は二要因を同時に変えます。roleとaccessの主効果をこの対比だけで識別したとはしません。事後に主比較を変更せず、副比較の補正・資源差・標本制約を保持します。[Exploratory factorial plan](../experiments/epistemic-diversity/paper/exploratory-role-access-factorial-analysis-plan.md)は計画のみです。

固定30問・5条件・単一モデル／反復の結果は限定的な観測です。Study 1時点の未観測fresh24におけるC3−C2 Answer F1差−0.15643は、その条件・選択標本での差として報告します。全30問は累積探索的集計です。

## RQ2：Observable Evidence Lineage

**必要なreference factsは、Workerへの実際の情報アクセス、Workerの公開表現、Artifact publication、実際のSynthesizer input、最終出力のevidential supportという観測可能な各段階で、どの程度保持・変形・欠落しているか。**

annotation単位はpath-conditional fact、support set、pathです。sentenceとfactを同一視しません。原文の存在、実入力、公開表現、独立publication transitionの保持、実合成入力、最終出力の支持を分けます。引用IDの正しさを意味的な公開表現の正しさと同一視せず、payload一致を意味的保持の証明とも扱いません。inferential statisticsの主要単位はquestionであり、fact数を独立sample数としません。

Workerの内部思考やLLMのhidden chain-of-thoughtは観測しません。現在の設計では「internally extracted / understood / used / ignored / relied on」を評価labelにしません。独立publication transitionのないidentity aliasはS3=NAです。最終短答にbridge factが書かれないだけではfailureにせず、受信したpathによる支持と出力の整合関係を判定します。識別不能は`undetermined`／`unclear`を残します。

RQ2の意味的分析は独立人手レビュー未実施です。Study 2はこの問いを動機とした探索的追加実験であり、RQ2全体や因果機構を解決したものではありません。[v3レビュー設計](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md)は未freezeのplanned analysisです。空の[versioned tooling](../experiments/synthesis-evidence-preservation/review_v3/README.md)は実装候補となり、2026-10-05には[Codebook候補](../experiments/synthesis-evidence-preservation/review_v3/CODEBOOK.md)とpilot・adjudication規則を具体化しました。pilot/mainレビューは未開始で、方法論の検証や人手結果を意味しません。

## Contributions：現在の貢献候補と証拠の境界

| 候補 | 現在の内容 | 達成・未達成の境界 |
| --- | --- | --- |
| Contribution 1：controlled comparisonの枠組み | same-model / same collaboration structureでRoleとactual Information Accessを別experimental factorとして配置 | Study 1 C1〜C4は実行済み。ただし主比較は二要因変更で、新factorial解析は未実施。今回確認した主要文献の範囲では、この配置と同一evidenceのobservable lineageを組み合わせた明示的直交比較を確認できなかった。世界初とはしない |
| Contribution 2：experimental treatment integrity | allowlist / ACL / detached context / typed Artifactと保存された実入力・公開記録で条件を担保・監査 | 実装とアクセス監査の証拠がある。access-control自体の新mechanism、完全sandbox、意味的confidentialityを主張しない |
| Contribution 3：exploratory follow-upとplanned lineage analysis | Study 1の観測→仮説→fixed-Worker Study 2を接続し、reference evidence→documented access→public expression→publication transition→actual Synthesizer input→downstream evidential supportを追跡する分析設計 | **実証済み:** 固定Worker条件では引用原文追加がtoken-length-matched neutral controlより平均Answer F1を改善する所見は得られなかった。**planned contribution:** two-pass registryと独立人手lineage分析。原因特定・bottleneckの証明でも、完了済み人手結果でもない |

Study 2の既存24問のAnswer F1はA=0.5666、B=0.5805、C=0.5805、B−A=+0.0139、B−C=0です。引用原文追加固有の平均回答改善が今回支持されなかったという観測に留めます。「単純なraw-evidence restorationだけでは十分でない可能性」はDiscussionの仮説であり、Study 1のgapの原因を説明した／否定したという結論ではありません。効果ゼロや情報損失一般の否定でもなく、未引用文は復元していません。既観測標本・一反復・総compute非同一の探索的追加実験です。

## 研究ストーリーと次段階の境界

```text
役割の違いと外部情報アクセスの違いを区別する
  → Runtimeで比較条件を実装・監査
  → Study 1：C2/C3等の比較と限定的な性能差の観測
  → 仮説：必要情報の公開表現・保持・最終出力の支持に課題がある可能性
  → Study 2：固定Worker＋引用原文／中立文対照
  → 引用原文追加固有の平均改善は今回支持されず
  → Observable Evidence Lineage独立人手分析（未実施）
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
- Role/persona研究、distributed information、context partition、Runtime access control、Role/Informationの区別、MAS stage-wise error analysis、HotpotQA evidence splitを初めて提案した。
- 保存されたpublic outputからモデルの内部的な証拠利用や因果的root causeを特定した。

## 根拠

[Study 1事前計画3.1](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)・[復旧計画3.2](../experiments/epistemic-diversity/docs/protocol-3.2-hotpotqa-recovery.md)・[最終結果](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)、[Study 2 PLAN](../experiments/synthesis-evidence-preservation/PLAN.md)・[結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)、[Runtimeの情報フロー](information-flow.md)・[安全境界](security.md)、[主張と根拠](research-claims-evidence-map.md)。旧仕様の保全と新レビューの差分は[依存監査](../experiments/synthesis-evidence-preservation/docs/review-stage-amendment-and-kit-impact.md)に記録します。

現行[Related Work](../experiments/epistemic-diversity/paper/current-related-work.md)と[Deep Research統合監査](deep-research-integration-audit.md)が位置づけ・citation照合の根拠です。旧revisionの本文はGit履歴に保持し、freeze済み研究仕様・旧kitを改変しません。
