# 研究の現在地

初回確認日：2026-09-30。当時のaudited base snapshotはmain `130ff0c54ddd77129bd9645d56ca33de505481ec`、研究branch `6d27edc4535f22d195b229da7010f982563eaf80`で内容は一致していました。本書は保存済み資料の整理であり、新しい実験・統計・人手判定ではありません。2026-10-02の照合snapshotは[統合監査](deep-research-integration-audit.md)へ分離します。

2026-10-02更新：[研究目的・RQ・貢献](research-question-and-contributions.md)を説明の基準とし、Role Diversity、actual Information Access Diversity、Observable Evidence Lineageを主題にします。Runtimeはtreatment integrityの基盤です。Study 1→仮説→探索的Study 2→独立人手lineage分析を一つの研究ストーリーとする基本案です。[現行Related Work](../experiments/epistemic-diversity/paper/current-related-work.md)と[統合監査](deep-research-integration-audit.md)を追加しました。過去の事前計画・結果は変更していません。

## 全体の要約

2026-10-05追記：空の[v3 tooling](../experiments/synthesis-evidence-preservation/review_v3/README.md)は実装候補となり、[Codebook](../experiments/synthesis-evidence-preservation/review_v3/CODEBOOK.md)・[pilot protocol](../experiments/synthesis-evidence-preservation/review_v3/PILOT-PROTOCOL.md)・[adjudication rules](../experiments/synthesis-evidence-preservation/review_v3/ADJUDICATION-RULES.md)を具体化しました。pilot/mainレビューとも未開始、human labelsは0、final freeze未完了です。以下の結果・研究解釈は変更していません。

この研究は、同じLLMに異なる役割を与えることと、参照できる外部情報を実際に分けることが、最終回答にどう関係するかを調べています。情報境界をコードで強制するRuntime上で、Study 1ではHotpotQAの固定30問・5条件を実行し、事前指定の24問ではC3（中立役割・分割情報）がC2（多様役割・全文情報）より低いAnswer F1となりました。そこから公開表現・情報保持・回答の支持に関する仮説が生じ、Study 2では保存済みWorker出力を固定して引用原文を追加しました。しかし、中立文による入力量対照と比べた平均回答改善は観測されませんでした。二つのモデル比較は完了していますが、独立人手レビュー、機構の因果的特定、再現性・一般化の確認は未完了です。

## Runtimeと研究の関係

Runtimeは実験対象の条件を実装・監査する基盤です。`ContextBuilder`が許可された入力・文書・Artifact・memoryだけを選び、切り離されたContextをAgentへ渡します。通信はスキーマ検証された公開Artifactを介します。これはプロンプト上の「見ないで」ではなく、入力の境界です。ただし、学習済み知識、意味的な漏洩、推論の正しさまで保証しません。

`app/`は汎用Runtime、`experiments/`は研究アプリケーションです。Study 2は保存記録を再利用する別runnerで、旧Runtimeの実行をそのまま再開したものではありません。Runtimeのソフトウェア検証、Mockの経路検証、実モデルの成績、独立人手検証は別の証拠です。[設計](architecture.md)・[情報フロー](information-flow.md)・[安全境界](security.md)を参照してください。

## Study 1：Role Diversity vs. Epistemic Diversity

RQ：同一モデルで、役割と文書アクセスの組合せを変えると回答性能・引用・資源使用はどう変わるか。ここでいうEpistemic Diversityは実行時の外部文書アクセスの違いで、信条・人格・モデル重みの違いではありません。

HotpotQA distractor devから、公開文書の長さ・構造と固定seedのID順位だけで30問を選びました。Qwen3:14b、temperature 0、think=false、単一反復です。文書単位の分割にgold支持文は使っていません。

| 条件 | Worker | 文書アクセス | 後段 |
| --- | --- | --- | --- |
| C0 | 1・中立 | 全文 | なし |
| C1 | 3・中立 | 全員が全文 | Artifactのみを読む共通Synthesizer |
| C2 | 3・多様役割 | 全員が全文 | 同上 |
| C3 | 3・中立 | 重複しない文書分割 | 同上 |
| C4 | 3・多様役割 | C3と同じ分割 | 同上 |

Protocol 3.0のPilot、3.1の本実験と停止、3.2の承認済み最小復旧を合わせ、150 unique cells・510 successful native generationsが揃いました。予約は511件で、送信前保存失敗1件を含みます。原失敗と正常出力の再利用を保持し、アクセス監査違反は0でした。

全30問は累積探索的集計です。先行Pilot 6問を除いた、Study 1時点で未観測だったfresh24を事前指定の主比較に使いました。C3−C2の平均Answer F1差は−0.15643、条件付きbootstrap 95%区間は[−0.29848, −0.03985]、seed付きsign-flip pは0.03010でした。24問中18問は同点、6問はC3が低い結果です。小標本・質問間依存を踏まえた限定的な比較であり、C2/C3はroleとaccessの両方が変わるため、情報分割だけの純粋な因果効果ではありません。[完了報告](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)に副比較・資源・復旧の詳細があります。

## Study 1から生じた仮説

全30問のC3では、Worker群のgold支持文引用recallが0.8472、final support recallが0.5917でした。引用集合の差は意味内容の欠落率ではありません。保存出力の不一致3件の予備的確認には、Workerの公開表現に必要な事実が欠落・混同する例と、公開された事実とfinalの主張が整合しない例があります。歴史的記録の「抽出／不使用」という説明を内部過程の証拠とは扱いません。これは独立人手評価でも、全30問の原因割合でもありません。

次の仮説は「原文→Worker公開Artifact→Synthesizer→最終回答の過程で、必要な事実の欠落・変形や出力支持の不足が性能差に関係する可能性」です。スキーマ正規化後の受け渡し照合は不一致0件で、Runtime転送時の文字列欠損が確認されたわけではありません。[事例記録](articles/multi-agent-runtime-hotpotqa-windows-ja.md)と[Study 2計画](../experiments/synthesis-evidence-preservation/PLAN.md)を区別して読みます。

## Study 2：Synthesis Evidence Preservation

RQ：既存C3 Worker出力を固定したまま、Worker自身が引用した原文をSynthesizerへ追加すると、入力量対照より回答が改善するか。

| 条件 | 入力 | 本比較24問のAnswer F1 |
| --- | --- | ---: |
| A | 固定Worker outputのみ | 0.5666 |
| B | 同じoutput＋引用元原文 | 0.5805 |
| C | 同じoutput＋token長を近づけた固定中立文 | 0.5805 |

同じQwen3設定でsmoke 3問×3条件の9件と、本比較24問×3条件の72件、計81/81 native responsesを完了しました。新規Worker生成は0件です。引用原文は公開引用IDから機械的に選び、goldや人手ラベルでは選んでいません。3条件に共通の新instructionを使い、Aも新たに生成しています。

B−Aは+0.0139（探索的bootstrap 95%区間[−0.1111, +0.1250]）、B−Cは0（同[−0.1250, +0.1250]）でした。B−Cで1問改善・22問同点・1問悪化なので、全回答が同じという意味ではありません。この24問は既にStudy 1で観測済みであり、Study 2のfresh確認標本ではありません。smokeは主集計に入れず、重複2問も独立標本数へ加えていません。[結果報告](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)を参照してください。

## 現時点で言えること・言えないこと

言えることは、指定範囲のモデル比較と機械的監査が完了したこと、Study 1の選択標本でC3優位が見られなかったこと、Study 2で「引用原文を戻すことに固有の平均回答改善」が今回支持されなかったことです。

言えないことは、Epistemic Diversity一般がRole Diversityより劣ること、情報分割が低下の原因であること、information-loss mechanismが証明または否定されたことです。Bで戻るのは引用済みの文だけで、未引用情報の欠落は修復しません。B/Cの入力量差は実測最大1.893%ですが、生成量・処理時間等を含む総computeは同一ではありません。BのSupport F1上昇も、support recall上昇や主評価改善とは同義ではありません。

## 未完了事項と人間に相談する論点

- 独立人手レビュー0/2名。元30問と新72回答の匿名資料・空の票は準備済みですが、意味的判定と不一致処理は未実施です。
- [Evidence Lineageレビューv3](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md)は設計のみ・未freezeです。two-pass registryを出力開示前に固定し、reference presence・actual access・public expression・独立publication・actual Synthesizer input・final evidential supportを分けます。question macro集計、[metrics](../experiments/synthesis-evidence-preservation/docs/evidence-lineage-metrics-plan.md)、[開始前checklist](../experiments/synthesis-evidence-preservation/docs/human-review-preflight-freeze-checklist.md)を設計しました。旧kitは保持し、新対応kitは未生成です。レビューと不一致処理終了前に次の確認実験は開始せず、終了後も新計画・人間の承認が必要です。
- 他モデル、追加反復、未観測標本の確認実験、全dev 7405問、総計算量を揃えた比較は未実施です。公開devの学習汚染も否定できません。
- 観測可能な公開表現・保持・出力支持のどこで障害が見られるか、その頻度と因果機構は未確定です。identity aliasでは独立publicationの損失を識別できません。元Windows保存エラーの具体的なlock所有者も未確定です。
- 教員とは、研究会発表としての貢献、一論文化か分離か、レビュー設計、確認実験の優先順位、関連研究の補強と公開可能な証拠範囲を相談します。追加生成は本整理の対象外です。

## 根拠と読み方

主要根拠は[Study 1の3.1計画](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)、[3.2復旧計画](../experiments/epistemic-diversity/docs/protocol-3.2-hotpotqa-recovery.md)、上記の両結果報告、[Study 2のfreeze](../experiments/synthesis-evidence-preservation/freezes/v1.json)、[レビュー基準](../experiments/synthesis-evidence-preservation/REVIEW.md)・[引き継ぎ](../experiments/synthesis-evidence-preservation/REVIEW-HANDOFF.md)です。

現在の主張は[主張と根拠の対応](research-claims-evidence-map.md)、古い「pending/current」の扱いは[文書監査](research-document-consistency-audit.md)、相談用要約は[教員向けbrief](professor-review-brief-ja.md)にまとめました。raw・DB・詳細ログ・判定票はGit管理外です。結果報告内のローカルリンクはGitHubだけでは読めず、第三者による完全な再解析が可能な公開パッケージはまだありません。機械的な「独立監査」は別コード経路の照合であり、独立人手レビューではありません。
