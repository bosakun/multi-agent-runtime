# Current Related Work / positioning

2026-10-02。研究の主題はRole Diversity、**actual Information Access Diversity**、Observable Evidence Lineageの組合せである。Runtimeはexperimental treatment integrityを担保・監査する基盤と位置づける。旧[focused survey](../docs/related-work.md)は当時の調査記録として保持する。

以下は添付Deep Research Report Aを起点に一次資料のタイトル・abstract・必要な本文を照合した現行整理であり、systematic reviewや全論文の全文再現ではない。「無」はその論文全体に一切存在しないとの断定ではなく、ここで確認した主設定で独立操作として扱われていないことを示す。「Role」はprompt/persona/機能役割、「actual access」は異なる外部資料・memory・contextの実際の割当を指す。実装レベルのrestrictionとsecurity certificationを混同しない。Report Aの内部citation tokenは転記しない。

## A. Role / Persona Diversity

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [CAMEL](https://proceedings.neurips.cc/paper_files/paper/2023/hash/a3621ee907def47c1b952ade25c67698-Abstract-Conference.html) (NeurIPS 2023) | role-playing / task prompting。Roleあり、外部evidence accessの直交操作が主題ではない | promptと対話役割。自然言語の協調会話 | 同:役割に基づく協調。異:同じQA evidenceのaccess条件・lineage比較が主題ではない |
| [ChatEval](https://arxiv.org/abs/2308.07201) | evaluator personaとdebate。多様roleと同一roleのablationがある。actual source partitionは主操作でない | persona prompts、debate/評価メッセージ | 同:role diversityの比較。異:LLM評価が中心で、Worker evidence割当と固定Synthesizer QAの比較ではない |
| [MetaGPT](https://arxiv.org/abs/2308.00352) | specialist rolesとSOPを組み合わせる。roleと工程・入力が結びつく | SOP/structured intermediate artifactsによるsoftware pipeline | 同:構造化public artifacts。異:役割と工程を結合し、本研究のneutral/diverse×full/partitioned格子とは異なる |
| [ChatDev](https://aclanthology.org/2024.acl-long.810/) (ACL 2024) | software専門role・chat chain。工程ごとのcontextであり独立access factorのQA比較でない | pipeline routing / 自然言語chat | 同:専門roleと協調。異:software開発・工程依存、固定QA evidenceのrole/access比較ではない |
| [CHOIR](https://aclanthology.org/2026.acl-long.2175/) (ACL 2026) | demographic persona perturbationsとcollective decoding。Role/personaあり、raw evidence分割は主操作でない | persona-conditioned generationと集約 | 同:同じモデルに異なるpersona。異:知識文書の実割当・Artifact lineageの診断ではない |
| [Tree-of-Debate](https://aclanthology.org/2025.acl-long.1422/) (ACL 2025) | scientific-paper comparison。paper-derived personaとpaper-specific情報を組み合わせる | debate tree、動的な主張・反論の通信 | 同:roleと異なる資料に基づく協調。異:roleとpaper情報が結合、固定構造の2×2 access比較ではない |

Role/persona操作自体を本研究の新規性としない。MetaGPT等では機能role、工程、入力が結びつくため、roleのラベルだけで本研究と同じ処置とは言わない。

## B. Model Diversity

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [ReConcile](https://aclanthology.org/2024.acl-long.381/) (ACL 2024) | 異なるLLMsとconfidence-weighted consensus。Role/personaは主操作でなく、actual evidence accessの独立操作もない | model選択、multi-round debate、回答・confidenceを集約。access enforcementは主題でない | 同:複数agentの回答統合。異:model diversityが処置で、本研究は同一Qwen3モデルに固定 |

## C. Reasoning / Sampling Diversity

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [DMAD](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3de667dab3b3d812583abc0a786139a0-Abstract-Conference.html) (ICLR 2025) | reasoning-method diversityを促すdebate。Role/personaより方法の差が主題、actual evidence accessの分割は主処置でない | 方法指定・debate messages。access enforcementは主題でない | 同:multi-agent diversityの区別。異:reasoning strategy diversityであって本研究のactual document accessではない |
| [Should we be going MAD?](https://proceedings.mlr.press/v235/smit24a.html) (ICML 2024) | debateとself-consistency等、sampling/aggregation・計算量を比較。Role条件は設定依存、actual source分割は主処置でない | debate rounds / vote・sampling集約。独立access enforcement比較でない | 同:collaborationの評価とcompute比較。異:同じreference factのaccess/lineageが主題ではない |

reasoning instruction、sampling、model weights、external information accessを一つの「多様性」へまとめない。

## D. Distributed / Asymmetric Information

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [iAgents](https://arxiv.org/abs/2406.14928v2) | private user information下のtask協調。actual asymmetric informationあり | agent-specific memory / retrieval、InfoNavによる能動的情報交換 | 同:agent間で知っている外部情報が異なる。異:private情報を探索・交換し、固定one-pass Artifact-only QA比較ではない |
| [Chain-of-Agents](https://proceedings.neurips.cc/paper_files/paper/2024/hash/ee71a4b14ec26710b39ee6be113d7750-Abstract-Conference.html) (NeurIPS 2024) | long contextをsegmentへ分けるWorker群とmanager。actual accessあり、worker/manager機能roleあり | context chunk割当、serial communication units→manager | 同:文書分割とpublic messageの統合。異:sequential relay / long-context主眼、neutral/diverse role×access直交格子でない |
| [HiddenBench](https://arxiv.org/abs/2505.11556v4) | shared/unique情報を持つhidden-profile tasks。information surfacingとcollective reasoningを分析 | distributed contexts、discussion / prompting interventions | 同:分散情報が表出・統合される問題。異:本研究の固定HotpotQA Worker→Artifact→Synthesizer lineageとは設定・介入が違う |
| [SILO-BENCH](https://aclanthology.org/2026.acl-long.1354/) (ACL 2026) | role-free distributed coordination。role-based priorsとcoordinationのconfoundingを明示 | silo別private inputs、情報共有・coordination | 同:Role priorとactual distributed informationを区別。異:role-free benchmarkが主題、本研究は既存QAの同一モデル・協調構造にrole/access格子を置く |
| [MARCH](https://aclanthology.org/2026.acl-long.1828/) (ACL 2026) | Solver/Proposer/Checkerとmulti-agent RL。CheckerにはSolverのoriginal outputを与えない等、roleとaccessがcoupled | asymmetric contexts、atomic claims / verification messages | 同:実際のinput access restriction。異:roleとaccessを結合した学習・役割構造で、固定same-model inference条件の直交比較でない |
| [InfoDelphi](https://arxiv.org/abs/2607.01661v1) (2026 preprint) | forecastingでpublic/disjoint private evidence、関連情報の集約 | agent別evidence bundles、relevance routing・反復confidence consensus | 同:actual private evidenceの割当。異:forecasting / Delphi反復であり、本研究の一回Worker→Synthesizerと異なる |

distributed information自体、またRoleとInformationのconfoundingへの注意は既知である。特にSILO-BENCHを無視して「本研究が初めてRoleとInformationを区別した」としない。

## E. Communication / Representation / Propagation

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [Chain-of-Agents](https://proceedings.neurips.cc/paper_files/paper/2024/hash/ee71a4b14ec26710b39ee6be113d7750-Abstract-Conference.html) | 分割contextとserial relay | communication unitで次Workerへ渡しmanager統合 | 同:中間表現による情報受渡し。異:relay構造、role/accessを固定構造内で比較する問いとは異なる |
| [PACT](https://arxiv.org/html/2606.05304v1) (2026 preprint) | action-state communicationのcompact representation。specialist pipelineとsplit-evidence QAを含む | structured action-state messages / 通信投影 | 同:split evidenceとstructured public communication。異:本文付録のHotpotQA割当は各agentへ1 gold-support paragraph＋4 distractors。本研究はgold非依存の公開文書配置で、固定Workerの引用原文復元対照も目的が違う |
| [Information Propagation Topologies](https://aclanthology.org/2025.emnlp-main.623/) (EMNLP 2025) | interaction graphと正誤情報のpropagation。Role/accessの直交処置でなく、外部source partitionの有無は本照合範囲で未確認 | graph routing / message propagation。外部文書ACLの評価とは区別 | 同:情報フローの分析。異:通信topologyが処置で、reference factの段階別意味保持と同じ設計ではない |
| [Why Do Multi-Agent LLM Systems Fail? / MAST](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html) (NeurIPS 2025) | MAS tracesのfailure taxonomy、人手annotation。Role/actual accessは対象framework依存で、単一の独立処置ではない | framework別trace / communication、failure分類・human agreement。共通ACL機構の提案でない | 同:観測traceを用いる失敗分析。異:本研究はreference-side fact/path registryと段階別状態・イベントの区別に焦点を限定する |

information-flow / MAS failure analysisを初めて提案したとはしない。MASTの旧arXiv版と採録版で対象数が異なるため、版を混ぜた件数比較も避ける。

## F. Runtime / Access Enforcement

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [Authorization-First Retrieval](https://aclanthology.org/volumes/2026.trustnlp-main/) (TrustNLP 2026; volume内同名論文) | role-scoped authorizationをretrieval前に適用。security roleはpersona diversityとは異なる | authorization-first context construction / least privilege | 同:モデルへの入力前にaccessを制限。異:security retrievalが主題、本研究はexperimental treatment integrityと保存記録の照合に用いる |
| [GuardAgent](https://proceedings.mlr.press/v267/xiang25a.html) (ICML 2025) | guard機能roleあり、persona diversity比較でない。actual external evidenceの分割は主操作でない | generated guardrail actions / 実行制御 | 同:prompt complianceだけでない実行側制約。異:action guardrailsであり、本研究のWorker knowledge allowlistそのものとは異なる |
| [HiddenBench](https://arxiv.org/abs/2505.11556v4) / [SILO-BENCH](https://aclanthology.org/2026.acl-long.1354/) / CoA | context-level agent別情報割当 | benchmark/pipeline側でinputを分ける | 同:actual input isolation。異:本研究はintended visibility→serialized inputs→Artifact→serialized Synthesizer inputをまとめて記録・監査する位置づけ |

Runtime access control、context partitionを新mechanismと主張しない。allowlist/ACL/typed Artifactは、処置が実input/routing levelで成立したことを確認する基盤である。trusted Python host、モデルの事前学習知識、意味的confidentiality、OS sandboxには別の限界がある。

## G. Evidence / Claim-level Diagnosis

| Study / primary source | 操作・Role / actual access | Enforcement / communication | 同じ点・異なる点 |
| --- | --- | --- | --- |
| [RAGChecker](https://papers.nips.cc/paper_files/paper/2024/hash/27245589131d17368cccdfa990cbf16e-Abstract-Datasets_and_Benchmarks_Track.html) (NeurIPS 2024) | claim-level retrieval/generation diagnosis。MAS Role/agent別accessは処置でない | retrieved chunks、claims、pipeline metrics。診断でありACL enforcement提案でない | 同:stageを分けて診断。異:RAG pipelineの診断で、MAS role/access比較とfixed-Worker lineageではない |
| [AIS](https://aclanthology.org/2023.cl-4.2/) (Computational Linguistics 2023) | identified sourcesからgenerated statementsを支持できるか。Role/agent別access操作はない | human attribution判定。通信・access enforcementは非該当 | 同:外部証拠による出力支持。異:internal useは測らず、Workerからのlineageを直接定義していない |
| [ALCE](https://aclanthology.org/2023.emnlp-main.398/) (EMNLP 2023) | answer/citation correctness・completeness。Role/agent別access比較はない | source-backed generation/evaluation。MAS通信・ACL enforcementは主題でない | 同:引用と回答の支持の区別。異:引用品質そのものは意味的伝達・内部利用の証明ではない |
| [FActScore](https://aclanthology.org/2023.emnlp-main.741/) (EMNLP 2023) | generated textをatomic factsへ分けて支持評価。Role/agent別access操作はない | output-side factsとretrieved evidence。MAS通信・ACL enforcementは非該当 | 同:fact-level支持の分解。異:本研究のregistryはoutput開示前のreference側から作る |
| [HotpotQA](https://aclanthology.org/D18-1259/) (EMNLP 2018) | multi-hop questions、supporting facts。原benchmarkはRole/agent別partitionを処置としない | gold answer/support annotations。MAS通信・enforcementはbenchmark外 | 同:同じbenchmarkと公式評価。異:gold sentence IDはfactや唯一のreasoning pathではない |
| [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) | entity/activity/derivation。LLM Role/actual access処置は非該当 | provenance relationshipsを記録。MAS通信・ACL enforcementは規格の目的でない | 同:証拠と中間記録のlineage。異:semantic correctness、truth、内部因果を保証する規格ではない |

[Compositional Questions Do Not Necessitate Multi-hop Reasoning](https://aclanthology.org/P19-1416/)はHotpotQAのreference経路とshortcut/alternative経路を区別する動機となる。[ERASER](https://aclanthology.org/2020.acl-main.408/)もrationale評価の参考になるが、公開説明のplausibilityを内部faithfulnessへ読み替えない。

## 本研究の差分候補と境界

今回確認した主要文献の範囲では、**same LLM / same collaboration structureでRoleとactual Information Accessを別factorとして配置し、同じreference evidenceをobservable stagesに沿って追跡する組合せ**の明示的な直交比較を確認できなかった。ただし非網羅的な照合であり、「初」「世界初」「unprecedented」は主張しない。

Study 1のC1〜C4はneutral/diverse × full/partitionedの2×2配置を持つが、主比較C3−C2は二要因同時変更である。新たなfactorial analysisは[post-hoc plan](exploratory-role-access-factorial-analysis-plan.md)に留まり、主効果・interactionの新結果はない。C0は同じcollaboration structureではないため格子外のbaselineとする。

Study 2の実証範囲は、固定Workerで引用原文追加がtoken-length-matched neutral controlより平均Answer F1を改善する所見が得られなかったこと。Evidence Lineageの独立人手分析は**planned contribution**であってcompleted resultではない。[Objective / RQs / contributions](../../../docs/research-question-and-contributions.md)と[v3 methodology](../../synthesis-evidence-preservation/docs/human-review-stage-analysis-plan-v3.md)へ接続する。

### 引用監査上の注意

Report AのiAgentsに付されたarXiv `2402.11444`は[自動運転車の受容に関する別論文](https://arxiv.org/abs/2402.11444)であり、[2406.14928v2](https://arxiv.org/abs/2406.14928v2)を用いた。AISは上記CL一次資料で同定した。Authorization-First Retrievalは個別ページ取得が不調だったためofficial venue volumeでタイトル・abstractを照合した。全文・コード・安全性の完全な再検証を済ませたという意味ではない。投稿前に使用版・bibliographic metadata・本文の詳細比較を再確認する。
