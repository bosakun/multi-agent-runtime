# 研究相談用概要：情報境界と証拠保持を扱う同一モデルMulti-Agent研究

2026-09-30。相談用の約2ページ相当の概要です。モデル比較2件は完了していますが、独立人手検証済みの完成研究・投稿論文ではありません。研究全体の入口は[現在地](research-status-ja.md)、主張の範囲は[根拠対応表](research-claims-evidence-map.md)を参照してください。

## 問題意識と実装

出発点は「同じLLMに同じ資料を渡し、役名だけを変えれば、有用な多様性が生まれるのか」という疑問です。役割の違いと、アクセスできる外部情報の違いを区別し、さらに情報を分けた後に必要な事実が統合されるかを調べています。人間の会議は着想の比喩で、モデルの信条・人格・事前学習知識を隔離した研究ではありません。

実装したIsolated Agent Runtimeは、Agentごとの入力・文書・memory・Tool権限をallowlistとACLで制御し、スキーマ検証されたArtifactだけを公開・受け渡しします。DAGの実行、予算・timeout、永続状態、events/snapshots、引用scope検証を備えます。信頼されたPython host内の入力・権限境界であり、OS process sandboxや意味的正しさの保証ではありません。汎用Runtimeと研究アプリケーションは分離しています。Mockは経路・境界・保存の検証で、LLMの推論性能を測る結果ではありません。

## 研究質問とStudy 1

RQ1：同じモデルで、役割と文書アクセスの組合せを変えると回答性能はどう変わるか。RQ2：Workerから公開Artifactを経て最終回答へ至る過程で、必要な事実は保持・利用されているか。

Study 1はRole Diversity vs. Epistemic Diversityです。HotpotQA distractor devから公開長さ・構造と固定seedのID順位で30問を選び、Qwen3:14b Q4_K_M、temperature 0、think=false、単一反復で5条件を実行しました。C0は単一中立Agent・全文、C1は中立3 Worker・全文、C2は多様役割3 Worker・全文、C3は中立3 Worker・文書分割、C4は多様役割3 Worker・文書分割です。C1〜C4の共通SynthesizerはWorkerの公開出力だけを読みます。

150 unique cells・510 successful native generationsを完了しました。予約は511件で、Windows journal保存の送信前失敗1件を含みます。承認済み最小復旧で正常出力を再利用し、原失敗・partial記録を残しています。アクセス監査違反は0でしたが、一般的な安全性の証明ではありません。

先行Pilot 6問を除いた事前指定fresh24で、主比較C3−C2の平均Answer F1差は−0.15643、条件付きbootstrap 95%区間[−0.29848, −0.03985]、sign-flip p=0.03010でした。24問中18問は同点、6問はC3が低い結果です。全30問の累積探索的Answer F1はC2=0.758、C3=0.599でした。C2とC3はroleとaccessの両方が変わるため、情報分割だけの因果効果やEpistemic Diversity一般の劣位は主張しません。

## 機構仮説とStudy 2

全30問C3のWorker群のgold支持文引用recallは0.8472、final support recallは0.5917でした。保存出力のEM不一致3件の予備的確認には、Workerが必要な事実を公開したのに合成が使わない例と、Workerが原文中の必要な事実を抽出できない例がありました。引用IDの一致は意味理解を保証せず、この3件から全体の原因割合は推定できません。

Study 2は、この仮説のうち単純な「引用元原文を戻せば改善する」を調べるSynthesis Evidence Preservationです。保存済みC3 Worker出力・順序を固定し、Synthesizer入力だけを変えました。AはWorker outputのみ、Bは同じoutput＋引用原文、Cは同じoutput＋token長を近づけた固定中立文です。原文選択にgoldやレビューラベルは使いません。共通instructionを新たに揃え、Aも生成し直しました。

3問smokeの9件と、本比較既存24問の72件、計81/81 native responsesを完了しました。新規Worker生成は0です。smokeは主集計に入れていません。本比較のAnswer F1はA=0.5666、B=0.5805、C=0.5805でした。B−Aは+0.0139（探索的95%区間[−0.1111,+0.1250]）、B−Cは0（同[−0.1250,+0.1250]）です。B−Cは1問改善・22問同点・1問悪化で、平均が同じでも全回答が同一ではありません。

この標本では引用原文追加に固有の平均回答改善は支持されませんでした。ただし効果ゼロの証明でも、情報損失一般の否定でもありません。引用されなかった文は戻していません。B/Cの実入力長差は最大1.893%で、総computeを揃えた比較ではありません。

## 現在の限界と未完了事項

長さ選択された小標本、単一モデル・一反復、公開devの学習汚染不明、質問間依存、role・partition・promptへの依存があります。Study 2の24問は既に観測済みで、未観測標本による確認実験ではありません。他モデル、追加反復、全dev 7405問、総計算量統制は未実施です。抽出・公開・合成の失敗機構と、元保存エラーの具体的なlock原因も未確定です。

独立人手レビューは0/2名です。元30問のC3を主対象とする匿名参照資料と、新72回答、2名分の空の判定票は準備済みです。計画は実験作成者以外の2名、旧Pilot 2問で基準校正、残り28問と新72回答の独立判定、一致率・ラベル分布、不一致協議を別version保存する方式です。資料構造から条件を推測でき、完全blindではありません。AIの照合は人手レビューに数えません。

実装・計画・結果要約はGit管理されていますが、raw・DB・詳細ログ・判定票はローカル限定です。ライセンス・共有範囲を整理した第三者再解析パッケージは未整備で、GitHubだけで完全再現できるとは言えません。

## 教員に相談したいこと

1. この限定比較と透明な失敗・非支持結果の報告は、研究会発表として成立するか。主な研究貢献をどこに置くべきか。
2. 査読付き論文へ発展可能か。必要な独立検証・新規性・標本設計は何か。
3. Study 1とStudy 2を一論文にまとめるか、探索的報告と確認研究を分けるか。
4. 独立人手レビューの判定単位、校正、匿名化、一致率・不一致処理は妥当か。機構分類に必要な証拠は何か。
5. 次の確認実験は、未観測標本、role固定のアクセス比較、資源統制、別モデル、反復のどれを優先すべきか。必要標本数・予算はどう決めるか。
6. IPSJ等では、マルチエージェント／協調AI、自然言語処理・QA、ソフトウェア／実行基盤のどの領域・研究会と議論するのが適切か。現行の募集・投稿区分を確認して判断したい。

これらは相談事項であり、採択可能性や適切な会場を確定したものではありません。本整理では追加モデル実験や機能実装を行いません。

## 主要根拠

[Study 1完了報告](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)／[3.1事前計画](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)／[3.2復旧計画](../experiments/epistemic-diversity/docs/protocol-3.2-hotpotqa-recovery.md)／[Study 2計画](../experiments/synthesis-evidence-preservation/PLAN.md)・[結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)／[レビュー基準](../experiments/synthesis-evidence-preservation/REVIEW.md)／[一論文化の構成案](../experiments/epistemic-diversity/paper/current-outline.md)。
