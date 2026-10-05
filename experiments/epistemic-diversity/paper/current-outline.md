# 一論文化する場合の構成案

2026-10-02更新。仮題：**Role and Information Access Diversity: Observable Evidence Lineage in a Same-Model Multi-Agent QA System**。既存結果の数値は変更せず、研究目的と未実施のlineage分析を整理した構成案です。

Motivation→Role / actual Information Access→Runtime as treatment integrity→Study 1→観測と仮説→探索的Study 2→引用原文固有の平均改善は支持されず→Evidence Lineage Human Review→将来のfailure patterns / 仮説生成→確認実験の相談、というストーリーを基本案にします。一論文化が最善かは未確定です。Study 2は観測済み標本での探索的追加実験で、機構を決着させる確認実験ではありません。[研究目的・RQ・貢献候補](../../../docs/research-question-and-contributions.md)に合わせます。[旧outline](outline.md)と[旧abstract](abstract.md)は保持し、新旧の件数・指標を混ぜません。

## 1. Introduction

- 問題意識：役割の違い、外部情報アクセスの違い、公開後の情報保持を区別する。
- 研究の射程：同じモデルの小さなQAシステム。人間の信条や認知的独立性を操作したとはしない。
- RQ1はroleとactual external information accessの条件差と回答性能の関係、RQ2はreference factsのobservable lineageと最終出力の証拠支持を扱う。
- 候補貢献：role / accessを区別する実験枠組み、その条件を実装・監査する基盤、限定比較から仮説・固定Worker介入・段階別分析へ接続する研究。Runtime単体の新規性を主主張にしない。新規性・投稿水準は未確定。

## 2. Related Work

- [現行Related Work](current-related-work.md)のA〜G: Role/Persona、Model、Reasoning/Sampling、Distributed Information、Communication、Access Enforcement、Evidence/Claim Diagnosisで整理する。
- SILO-BENCHのrole-prior confounding、HiddenBenchのsurfacing、MARCHのcoupled role/access、PACTのsplit evidence、RAGCheckerのclaim diagnosisを比較する。[旧focused survey](../docs/related-work.md)は当時の記録として保持する。
- 既存研究がすべて共有情報しか扱わないという主張や、既存手法より優れるという主張はしない。

## 3. Isolated Agent Runtime / Information Boundary

- Runtimeはexperimental treatment integrityの基盤とする。intended visibility→actual serialized Worker input→public Artifact→actual serialized Synthesizer inputを照合し、access-control自体の新規mechanismを主張しない。
- ContextBuilderのallowlist、ACL、detached context、typed Artifact、引用scope検証。
- Worker→Artifact→Synthesizerの一枚の情報フロー図。情報の公開は意図したdeclassification。
- 汎用`app/`と研究runnerの関係。Study 2の専用replay/event DBと旧Runtime DBを区別。
- trusted Python hostの限界、事前知識を隔離できないこと、schema妥当性と意味的正しさの違い。

## 4. Study 1: Role vs. Epistemic Diversity

- RQとC0〜C4。C1〜C4のrole×access構造と、主比較C3−C2が二要因同時変更であることを明示。
- HotpotQA distractor dev、公開長さ・構造による適格性、固定ID順位、文書単位の分割、gold非依存の配布。
- 先行6問Pilotと当時未観測24問。全30問の探索的集計とfresh24推論を分ける。
- Qwen3:14b Q4_K_M、digest、Ollama、Windows/NVIDIA、temperature 0、think=false、単一反復。seedはsampling決定性の保証ではない。
- Protocol 3.0→3.1停止→3.2復旧の変更表。89正常ケース・2 Workerの再利用、510正常生成／511予約、元失敗保存。
- 公式scorerのpin、Answer F1主評価、副評価・Holm family、bootstrap/sign-flip仕様。旧自作タスクの指標とは混ぜない。

## 5. Study 1 Results

- 表1：150セル・510正常native生成・送信前失敗1予約・アクセス監査違反0。
- 表2：全30問とfresh24のC0〜C4公式指標。主比較は−0.15643、条件付き95%区間[−0.29848, −0.03985]、p=0.03010。
- 主比較24問の18同点・6低下。P2〜P5は補正後p>0.05で、効果ゼロの証明ではない。
- token・latency・引用・復旧感度を記述的に報告。p値でrole/access交絡や標本制約は解消しない。

## 6. Error Analysis and Mechanism Hypothesis

- 全30問C3のWorker citation recall 0.8472とfinal support recall 0.5917。集合指標で、意味的欠落率ではない。
- EM不一致3件の予備的保存出力確認：Worker公開表現の欠落・混同と公開事実/finalの不整合。旧記録の抽出・不使用という語を内部思考の証拠にしない。outcome-selectedで頻度推定・独立レビューではない。
- 30問のスキーマ正規化後の受け渡し不一致0。転送破損と意味的な選択・変形を区別。
- 独立人手レビューは未実施。原因ラベルの結果・一致率欄は「未実施」とし、推測で埋めない。

## 7. Study 2: Synthesis Evidence Preservation

- RQ/H1/H2、固定C3 Worker、共通の新instruction、引用集合・順序・最終schemaの固定。
- A=outputのみ、B=引用元原文追加、C=token長を近づけた固定中立文。Bの文選択にgold・レビューラベルを使わない。
- smoke 3問×3=9、本比較既存24問×3=72。重複2問とsmoke除外、新規Worker生成0を明示。
- 独立freeze・台帳・保存先、事前tokenizer測定と実native countの照合。
- B−Aを主評価、B−Cを計画した対照、C−Aを記述的比較。既観測標本に条件づけた探索的bootstrapである。

## 8. Study 2 Results

- 表3：81/81正常応答、main 72セル、保存監査・scorer再照合。
- 表4：Answer F1 A=0.5666、B=C=0.5805。B−A=+0.0139、95%区間[−0.1111,+0.1250]；B−C=0、同[−0.1250,+0.1250]。
- B−Aは2改善/21同点/1悪化、B−Cは1/22/1。平均同値を回答同一や統計的同等性とはしない。
- B/C全prompt長差最大1.893%。outputとlatencyを併記し、総compute一致を主張しない。
- Support F1のB上昇とSupport recallのB低下を併記。主評価改善に言い換えない。
- 新Aと歴史的C3はinstruction変更を含むため、純粋な再現性試験として扱わない。

## 9. Observable Evidence Lineage Human Analysis（RQ2：計画・未実施）

- Reviewerは日本語話者2名を前提とする。[固定訳方針](../../synthesis-evidence-preservation/review_v3/BILINGUAL-REVIEW-POLICY.md)に従い、英語原文と事前固定日本語訳を併記し、日本語訳を主に参照して判定する予定である。methodologyでは同一訳の共有・対応表・版/hash・翻訳確認方法・開示順・ambiguityを記録する。実施後に実記録で確認できた場合のみ「判定した」と記述する。翻訳を介する不確実性もlimitationsへ加える。
- [v3計画](../../synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md): two-pass registryを出力開示前にfreeze。sentence/fact/support set/path、alternative paths、path-conditional requirednessを明示する。RQ2の本文分析であって付録だけに置かない。
- S0 reference presence→S1 actual Worker accessibility→S2 public expression→S3独立publication（aliasはNA）→S4 actual Synthesizer input / routes→S5a final relation＋S5b evidential support。引用ID・payload一致と意味stateを分け、内部extract/use/ignoreを推定しない。
- 2名によるindependent annotation（初回判定中は相談せず相手のlabelを見ない）、著者との関係性・利益相反の別記録、対象外registry校正とedge cases、progressive disclosureとlocks、allocation blindingの限界、pre-adjudication IAA、adjudication別versionを説明する。著者から人的に独立しているとは仮定しない。stateとderived failure eventを分け、first observable failureをroot causeと呼ばない。
- [Metrics](../../synthesis-evidence-preservation/docs/evidence-lineage-metrics-plan.md): question macro、coverage、strict/partial sensitivity、Path End-to-End Survival、question-clustered uncertainty、共有S0〜S3の非三重計上を計画する。
- 既存freeze・旧kitは保持し、新kitはまだ生成しない。人手レビュー結果、障害件数・割合、一致率は存在せず、本節は分析計画のみ。完了後に保存済み実判定を根拠として構成を再検討する。

## 10. Discussion

- 境界遵守、public expression、publication、actual inputへの到達、最終回答の支持は異なる観測対象。
- 単純な引用原文復元の説明は今回支持されなかったが、未引用情報・文書分割・統合負担は残る。
- 中立文の注意分散もあり得るため、B−Cを万能なmechanism検定とはしない。
- Study 1からStudy 2への接続は仮説生成と探索的介入で、因果機構の確定ではない。
- 観測は「fixed Workerで引用原文追加がneutral controlより平均Answer F1を改善する所見は得られなかった」。単純なraw-evidence restorationだけでは十分でない可能性はDiscussionの仮説に留める。将来のobservable failure patterns→specific hypothesisを検討し、人手分析だけで因果機構を確定しない。

## 11. Limitations

- 長さ選択された30/24問、公開dev・汚染不明、単一モデル・一反復、質問依存、弱いrole操作、partition依存。
- role/accessの同時変更、総資源の非同一、Study 2の既観測標本・smoke重複、完全blindでないレビュー資料。
- gold alignmentによる参照経路へのanchoring、registry依存、S3非識別、unclear/coverage、rare-label IAA、質問間依存。新2×2解析は[post-hoc plan](exploratory-role-access-factorial-analysis-plan.md)だけで新結果はない。
- 独立人手レビュー0/2、内容の妥当性と失敗原因未確定。
- 保存復旧と不明なlock原因。Git管理外資料、完全な第三者再解析パッケージ未整備。
- 回帰検証は398 passed / 4 skipped / 25 archival deselectedのgateであり、repository全体無条件greenではない。

## 12. Future Work

独立人手レビューと不一致整理→failure pattern→具体的仮説→確認実験候補→人間による計画・予算・実行承認の順序を守る。候補は未使用質問、role固定のaccess-only比較、access固定のrole-only比較、資源統制、別モデル・追加反復、Artifact表現への介入であり、実行するものはまだ決めない。全dev実行を当然の次段階とはせず、研究目的・予算・必要精度から優先順位を相談する。本outlineは実行承認ではなく、人手レビュー終了前に新実験を開始しない。

## 13. Conclusion

この設定・選択標本で観測した比較結果と、原文追加固有の平均回答改善が支持されなかった範囲だけを述べる。Epistemic Diversity一般の優劣、information-loss mechanismの証明、LLM一般への外挿はしない。

## 付録・投稿前の判断

- Protocolの時系列、freeze/scorer/モデルのhash、復旧の出自、全比較、各失敗の記録。
- 独立レビューv3 schema・two-pass registry・校正記録・scope採用版・IAA/derivation rules・協議別version。旧2校正＋28本判定仕様と区別する。実判定未実施で、RQ2本体は第9節、付録は手続き・記録仕様の補足とする。
- 公開可能な再解析資料とローカル限定資料を区別し、倫理・ライセンス・共有範囲を相談する。
- 一論文化なら「未確定機構を含む探索的研究」を中核にする。分離ならStudy 1の限定比較報告とStudy 2の介入報告それぞれの独自貢献を検討する。
- 根拠：[研究の現在地](../../../docs/research-status-ja.md)、[主張対応表](../../../docs/research-claims-evidence-map.md)、[両研究の結果報告への入口](../../synthesis-evidence-preservation/README.md)。
