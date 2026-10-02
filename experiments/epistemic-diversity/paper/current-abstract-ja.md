# 現在の研究に基づく要旨案

2026-10-02更新。Study 1とStudy 2を一論文化する場合の案であり、投稿方針・独立人手検証済みの完成論文を意味しません。[旧abstract](abstract.md)は実行前の歴史的文書として保持します。

同じLLMに異なる役割を与えることと、参照可能な外部情報を実際に分けることは異なる操作である。本研究はRole Diversity、actual Information Access Diversity、Observable Evidence Lineageを扱う。Isolated Agent Runtimeをinput/routing条件の担保・監査基盤として用い、Qwen3:14bによる二つの比較を行った。Study 1ではHotpotQA distractor devから公開文書の長さ・構造に基づき固定した30問をC0〜C4の5条件で単一反復実行し、150 unique cells・510正常native生成を完了した。先行Pilotを除く事前指定24問で、C3（中立役割・文書分割）−C2（多様役割・全文アクセス）の平均Answer F1差は−0.1564であった。ただし、この対比はroleとaccessを同時に変えるため、情報分割だけの因果効果ではない。引用統計と予備的な保存出力確認から、公開表現・情報保持・出力支持に関する仮説が生じた。Study 2では既存C3 Worker出力を固定し、outputのみ、引用元原文追加、token長を近づけた中立文追加を比較した。smoke 9件と既存24問の本比較72件を完了し、Answer F1は順に0.5666、0.5805、0.5805となった。原文追加とoutputのみの平均差は+0.0139だが、中立文対照との差は0であり、この標本では原文追加固有の平均回答改善は支持されなかった。これは情報損失一般の否定や機構の確定ではない。今後、出力開示前のtwo-pass reference registryと独立人手による段階別Evidence Lineage分析を計画しているが未実施である。小規模な長さ選択標本、単一モデル・単一反復、非同一の総compute、観測済み標本による探索的追加実験、独立人手レビュー未実施という限界があり、HotpotQA全体やLLM一般への外挿は行わない。

根拠：[Study 1結果](../docs/qwen3-14b-hotpotqa-protocol32-windows-outcome.md)、[Study 2計画](../../synthesis-evidence-preservation/PLAN.md)・[結果](../../synthesis-evidence-preservation/docs/qwen3-14b-windows-outcome.md)、[主張と根拠](../../../docs/research-claims-evidence-map.md)。
