# 研究主張と根拠の対応

2026-09-30。保存済み計画・結果・監査とコードを照合した表です。新しい統計分析や意味的判定は行っていません。

2026-10-02更新：[研究目的・RQ・貢献](research-question-and-contributions.md)を説明の基準にしました。Runtimeはexperimental treatment integrityの基盤で、access-control単体の新規性を主張しません。[Evidence Lineage v3](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md)はRQ2への設計であり、分析結果の証拠ではありません。[Related Work](../experiments/epistemic-diversity/paper/current-related-work.md)と[統合監査](deep-research-integration-audit.md)で差分候補と旧freeze／kitの保全を整理します。

statusの意味：`established`は指定された実装・実行・機械照合の範囲で確認、`descriptive`は当該標本の観測・集計、`hypothesis`は未確定の説明、`limitation`は未実施事項・設計上の制約です。`established`も普遍的な安全性や認知機構を意味しません。

## 主張対応表

| claim | evidence | source file | status | allowed wording | wording to avoid |
| --- | --- | --- | --- | --- | --- |
| RuntimeがAgentごとの情報境界をコードで強制する | 入力・knowledge allowlist、Artifact policy∩ACL、memory namespace、JSON round-trip；隔離テスト | [context.py](../app/policies/context.py)、[router.py](../app/orchestration/router.py)、[test_isolation.py](../tests/security/test_isolation.py)、[security.md](security.md) | established | trusted host内で、Agentへ渡す情報・公開経路をコードで制限する | 完全sandbox、学習済み知識の隔離、意味的漏洩の完全防止 |
| HotpotQA 30×5が完了した | 150 unique cells、510正常native生成、511予約、原送信前失敗1件を保持；完了監査passed | [Study 1結果](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)；ローカルL1 | established | 固定した長さ選択dev30問×5条件の実行・集計が完了した | HotpotQA全体完了、511正常生成、失敗なし、研究全体完了 |
| access audit violationは0だった | C0〜C4の全30問集計audit_violations=0；原文射影・引用scopeの照合 | [Study 1結果](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)、[report.py](../experiments/epistemic-diversity/hotpot_reporting/report.py)；L3 | established | 対象の実入力・引用の機械的アクセス監査で違反0 | あらゆる情報漏洩なし、思考や引用文の真実性を保証 |
| fresh24のC3−C2 Answer F1差は負 | P1平均−0.1564303752；18同点・6低下；条件付きCI95[−0.29848,−0.03985]、p=0.03010 | [3.1計画](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)、[Study 1結果](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)；L2 | descriptive | 事前指定の選択24問・当該モデルではC3が低かった | Epistemic Diversity一般が劣る、母集団で確実、p値が機構を証明 |
| C2 vs C3は単一要因比較ではない | C2=多様役割＋全文、C3=中立役割＋分割；総inputも不同 | [3.1計画](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md) | limitation | roleとaccessの同時変更を含む比較である | 情報分割だけの純粋な因果効果、他は完全同一 |
| C3のWorker citation recallとfinal support recallに差があった | 全30問のWorker引用union∩goldのrecall平均0.847222、final sp_recall平均0.591667 | [Study 1結果](../experiments/epistemic-diversity/docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)、[引用集計実装](../experiments/epistemic-diversity/hotpot_reporting/report.py)；L3 | descriptive | 引用集合と最終支持文集合のrecallに差がある | 必要な意味内容の25.6%が転送中に消失、Workerは全て理解した |
| 3件のcase reviewには公開表現と最終出力の双方に問題を示唆する例がある | 旧記録は「抽出／合成失敗」と記述するが、観測は公開事実の欠落・混同、公開事実とfinalの不整合 | [保存済み事例記録](articles/multi-agent-runtime-hotpotqa-windows-ja.md)；L4 | descriptive | 保存出力の予備的3件確認に公開表現と最終出力の問題がある | 内部抽出失敗や証拠不使用を確認、独立人手レビュー済み、全30問の原因割合 |
| 正規化後の受け渡し不一致は0 | 30問C3の120 agent journalとArtifact入力を照合；数値型正規化あり | [Study 2結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)；L7 | established | スキーマ正規化後の公開payload受け渡しに不一致なし | raw bytesが完全一致、要約の意味的欠落なし |
| Study 2の実モデル比較が完了した | smoke9＋main72＝81予約／81正常応答、Worker新規0、main72セル、full research=false | [Study 2結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)、[freeze](../experiments/synthesis-evidence-preservation/freezes/v1.json)；L5 | established | 固定Worker・3条件のモデル比較は完了、人手レビューは未完了 | 27独立問、81問、研究全体完了 |
| Study 2のB−Aは+0.0139 | 24問平均+0.0138889；2改善/21同点/1悪化；探索的CI95[−0.1111,+0.1250] | [Study 2計画](../experiments/synthesis-evidence-preservation/PLAN.md)、[結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)；L6 | descriptive | 既観測24問でB−Aの平均は+0.0139だった | 引用原文で確実に改善、有意な一般的効果 |
| Study 2のB−Cは0 | 24問平均0；1改善/22同点/1悪化；探索的CI95[−0.1250,+0.1250] | [Study 2結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)；L6 | descriptive | この標本でB−Cの平均差は0だった | 全回答同一、同等性証明、効果ゼロ確定 |
| raw evidence追加固有の平均改善は今回支持されなかった | A=0.566577、B=C=0.580466；計画した中立文対照との差なし | [Study 2結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)；L6 | descriptive | 今回の条件・標本・主評価では支持する所見が得られなかった | 原文は常に無益、情報損失仮説を否定、mechanismを証明 |
| information-loss mechanismは未確定 | 引用IDと意味的表現は別；未引用文はBに戻らない；独立人手lineage判定なし | [PLAN](../experiments/synthesis-evidence-preservation/PLAN.md)、[v3設計](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md) | hypothesis | 公開表現・保持・出力支持の不足が関係する可能性を検討している | C3低下の原因は圧縮と断定、媒介効果を識別、内部的ignoredを確認 |
| Observable Evidence Lineageの人手分析はplanned contribution | two-pass registry、S0〜S5a/b、prerequisite付きevents、独立workflowを設計、新kitも判定も未実施 | [v3設計](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md) | limitation | RQ2へ答える観測記録の内容分析を計画した | 情報損失stageを特定した、publication loss率を測定済み |
| independent human reviewは未完了 | 担当者0/2、完了0/2、匿名資料・空票のみ準備済み | [REVIEW-HANDOFF](../experiments/synthesis-evidence-preservation/REVIEW-HANDOFF.md)；L8 | limitation | 機械照合は済み、独立人手内容検証は未実施 | AIレビューを独立人手2名として数える、意味的妥当性検証済み |
| 入力長対照は総compute対照ではない | B/C native input差最大1.893%；output・latencyは異なる | [Study 2結果](../experiments/synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)；L6 | limitation | 許容5%以内で入力長を近づけた対照 | 計算量を完全に揃えた因果実験 |
| 他モデル・未観測標本等への一般化は未検証 | 単一モデル・一反復、30問選択、Study 2は既観測24問；他モデル・全devなし | 両結果報告、[PLAN後続課題](../experiments/synthesis-evidence-preservation/PLAN.md) | limitation | 次の確認研究が必要である | HotpotQA全体、LLM一般、人間集団の多様性へ外挿 |
| same-model / same structureのRole × Access配置は実行済み | C1〜C4のneutral/diverse × full/partitioned配置。C0は格子外 | [3.1計画](../experiments/epistemic-diversity/docs/protocol-3.1-hotpotqa-main.md)、[exploratory plan](../experiments/epistemic-diversity/paper/exploratory-role-access-factorial-analysis-plan.md) | established | 別factorとして配置した既存条件がある。新factorial解析は未実施 | C2/C3からRole/Access因果効果を分離、post-hoc解析を事前主評価へ変更 |
| 位置づけの差分は組合せの候補 | Role、actual distributed input、context isolation、MAS/claim diagnosisには先行例がある | [現行Related Work](../experiments/epistemic-diversity/paper/current-related-work.md) | hypothesis | 今回確認した主要文献の範囲では比較格子＋同一evidence lineageの明示的直交比較を確認できなかった | 世界初、既存MASは全て共通知識、網羅的novelty証明 |
| identity aliasは独立publication成功ではない | Worker outputをArtifact.payloadへ設定、typed normalization後の一致を検証 | [orchestrator.py](../app/orchestration/orchestrator.py)、[source.py](../experiments/synthesis-evidence-preservation/src/synthesis_study/source.py)、[v3設計](../experiments/synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md) | limitation | transition provenanceを確認してaliasならS3=NA。独立変換の意味保持率は識別しない | payload一致だから全factがpublicationで意味的に保持、publication成功100% |

## ローカル一次資料の所在

以下はこのPC上で内容を確認したGit管理外の資料です。GitHubの公開根拠は上表の計画・結果要約・コード・freezeで、ローカルJSON、DB、raw、票が公開されたとは扱いません。再解析可能な公開パッケージの準備・共有は別途判断が必要です。

- L1：[Study 1機械的完了監査](../reports/hotpot-recovery-completion-final-audit.json)。別コード経路の照合で、人手評価ではありません。
- L2：[Study 1分析JSON](../experiments/epistemic-diversity/runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/analysis.json)。`fresh24_comparisons.P1`、全30/fresh24、復旧感度を区別。
- L3：[Study 1記述的report](../experiments/epistemic-diversity/runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/descriptive/report.json)。`summaries.C3.worker_gold_support_recall`と`sp_recall`、各条件`audit_violations`。
- L4：[EM不一致3件のID](../experiments/epistemic-diversity/runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/descriptive/discordant-C2-C3.json)と[保存出力](../experiments/epistemic-diversity/runs/hotpotqa-protocol32-qwen3-14b-windows/analysis/descriptive/saved-output-review.md)。選択された事例で、独立レビューではありません。
- L5：[Study 2完了監査](../experiments/synthesis-evidence-preservation/reports/real-fixed-workers-20260930/completion-audit.json)。`passed_model_comparison=true`、`passed_full_research=false`。
- L6：[Study 2分析JSON](../experiments/synthesis-evidence-preservation/reports/real-fixed-workers-20260930/analysis.json)。`conditions`、`comparisons.B-A/B-C`、`new_worker_calls`等。
- L7：[source照合](../experiments/synthesis-evidence-preservation/reports/source-audit/audit.json)。型正規化後の同一性と、原ファイルhashの保持は別の検査。
- L8：[レビュー準備監査](../experiments/synthesis-evidence-preservation/reports/review-kits/prepared-625d2bfc3c62491ba47d1540b0d59466/preparation-audit.json)。`assigned_reviewers=0`、`completed_reviewers=0`。空票は未実施の記録です。

## 記述上の境界

Study 1のCI・pは事前指定したfresh24の条件付き比較で、role/accessを分離した因果推定ではありません。Study 2の区間は既観測標本の探索的bootstrapで、確認的有意性や同等性の判定に使いません。予備的事例、機械照合、独立人手レビューを相互に代用しません。主張と根拠が不足する場合は、より弱い表現か未確定を残します。
