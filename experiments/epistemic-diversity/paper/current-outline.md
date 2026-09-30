# 一論文化する場合の構成案

2026-09-30。仮題：**Information Boundaries and Evidence Preservation in a Same-Model Multi-Agent QA System**。

Study 1とStudy 2を一論文にすることが最善かは未確定です。共通の情報境界を軸に「比較→仮説→限定的介入」を説明できる一方、Study 2は観測済み標本の探索的追試で、Study 1の機構を決着させる確認実験ではありません。研究会報告と後続論文の分離も教員と相談します。[旧outline](outline.md)と[旧abstract](abstract.md)は実行前の歴史的記録として保持し、新旧の件数・指標を混ぜません。

## 1. Introduction

- 問題意識：役割の違い、外部情報アクセスの違い、公開後の情報保持を区別する。
- 研究の射程：同じモデルの小さなQAシステム。人間の信条や認知的独立性を操作したとはしない。
- 候補貢献：監査可能な情報境界、完了した限定比較、固定Workerによる入力介入と支持されなかった説明の報告。新規性・投稿水準は未確定。

## 2. Related Work

- モデル異質性、役割・推論方法の多様性、情報非対称、マルチホップQA、証拠付き合成を分ける。
- [保存済み関連研究調査](../docs/related-work.md)は出発点で、網羅的レビューではない。投稿前に一次論文を再確認する。
- 既存研究がすべて共有情報しか扱わないという主張や、既存手法より優れるという主張はしない。

## 3. Isolated Agent Runtime / Information Boundary

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
- EM不一致3件の保存出力確認：届いた事実の不使用とWorker抽出失敗の両方。結果に基づく事例選択で、頻度推定や独立レビューに使わない。
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

## 9. Discussion

- 境界遵守、必要事実の抽出、公開、統合は異なる達成事項。
- 単純な引用原文復元の説明は今回支持されなかったが、未引用情報・文書分割・統合負担は残る。
- 中立文の注意分散もあり得るため、B−Cを万能なmechanism検定とはしない。
- Study 1からStudy 2への接続は仮説生成と探索的介入で、因果機構の確定ではない。

## 10. Limitations

- 長さ選択された30/24問、公開dev・汚染不明、単一モデル・一反復、質問依存、弱いrole操作、partition依存。
- role/accessの同時変更、総資源の非同一、Study 2の既観測標本・smoke重複、完全blindでないレビュー資料。
- 独立人手レビュー0/2、内容の妥当性と失敗原因未確定。
- 保存復旧と不明なlock原因。Git管理外資料、完全な第三者再解析パッケージ未整備。
- 回帰検証は398 passed / 4 skipped / 25 archival deselectedのgateであり、repository全体無条件greenではない。

## 11. Future Work

人間と合意すべき計画として、独立2名のレビュー、未観測標本での確認、role固定のアクセス比較、資源統制、別モデル・追加反復、公開パッケージを挙げる。全dev実行を当然の次段階とはせず、研究目的・予算・必要精度から優先順位を決める。本outlineは実行承認ではない。

## 12. Conclusion

この設定・選択標本で観測した比較結果と、原文追加固有の平均回答改善が支持されなかった範囲だけを述べる。Epistemic Diversity一般の優劣、information-loss mechanismの証明、LLM一般への外挿はしない。

## 付録・投稿前の判断

- Protocolの時系列、freeze/scorer/モデルのhash、復旧の出自、全比較、各失敗の記録。
- 独立レビューの基準・校正2問・独立28問・新72回答・協議別version。実判定は未実施。
- 公開可能な再解析資料とローカル限定資料を区別し、倫理・ライセンス・共有範囲を相談する。
- 一論文化なら「未確定機構を含む探索的研究」を中核にする。分離ならStudy 1の限定比較報告とStudy 2の介入報告それぞれの独自貢献を検討する。
- 根拠：[研究の現在地](../../../docs/research-status-ja.md)、[主張対応表](../../../docs/research-claims-evidence-map.md)、[両研究の結果報告への入口](../../synthesis-evidence-preservation/README.md)。
