# Observable Evidence Lineage — Human Review design v3

2026-10-02。**将来の人手レビュー用の設計案。未実施・未freeze・未実装**。実験仕様を変更する文書ではない。旧[段階別計画](human-review-stage-analysis-plan.md)、[REVIEW](../REVIEW.md)、freeze v1、prepared kit、空票は履歴として保持する。新しい実行・統計結果・人手判定は含まない。

## 1. 目的と観測範囲

RQ2は、reference factsが実際のWorker入力、Workerの公開表現、publication transition、実際のSynthesizer入力、最終出力の証拠支持に沿ってどう保持・変形・欠落するかを問う。内部抽出、理解、hidden reasoning、証拠を「使った／無視した」、root causeは判定しない。引用IDの一致は意味的な表現の正しさではなく、payload一致も原文の意味の保持を証明しない。

```text
Frozen reference registry
  → S0 reference presence
  → S1 actual Worker input
  → S2 public expression
  → S3 independent publication transition, if observable
  → S4 actual Synthesizer input (Artifact / supplementary evidence)
  → S5a final fact relation + S5b received-path support
```

主対象候補はStudy 1の既存30問C3とStudy 2の既存24問×A/B/C（72出力）。同一questionのS0〜S3は共有レコードを参照し、A/B/Cで三重計上しない。smokeは校正・動作確認の記録として別扱いで、本比較へ混ぜない。旧仕様は2問校正＋28問独立判定だった。v3は対象30問外で校正する方向を提案するが、30問／28問の本判定範囲は開始前に人間が固定する。既に校正で見たケースがあれば、そのreviewerの独立本判定・IAAから除き、記述的な別層として残す。結果に基づく対象除外はしない。

## 2. Fact Registry: system output開示前のtwo-pass

実装・実験作成者以外の2名が担当する。registry担当とstage担当を同じ2名にするか分けるかは開始前に決め、既知情報・過去のケース閲覧を申告する。

### R1 — Raw-only discovery

2名へquestion、complete raw/reference evidence、title/sentence IDsだけを開示する。gold answer、gold supporting facts、全system/Worker出力、Artifact、Synthesizer入力・最終回答、条件名、aggregate scoresを開示しない。各自がcandidate facts、support sets、reasoning pathsを作る。R1独立票・時刻・版・source hashをimmutable保存してから比較する。原文にない補助前提は明示し、raw evidence中の事実として登録しない。

### R2 — Benchmark alignment

R1保存後に初めてgold answerとHotpotQA gold supporting factsを開示する。system outputsは引き続き非開示。gold-intended pathとR1候補を対応づけ、gold-anchored pathとraw-discovered alternative valid pathの両方を保持する。gold sentence IDをfactと同一視せず、goldにない経路を自動的に誤りとしない。代替経路には、原文に支持されquestionへ答えられるかの根拠を残す。

自由生成したR1項目には共通の項目宇宙がないため、そのままkappaを計算しない。候補対応づけ・集合一致を別に記録する。統合候補一覧を固定した後、各reviewerがfactの支持、support setの十分性、pathの妥当性、path内の必要性を独立に判定し、その票を保存してからadjudicateする。R1で後から相手の候補を見た影響を区別して記録する。

最終registryは**全system output開示前にfreeze**する。goldに沿う経路だけへの絞り込みや、モデル出力に合うfactの後付け選択はしない。freeze後に新しい代替経路候補が見つかった場合、primary registryを静かに書き換えない。amendmentと別versionのsensitivity analysis候補として記録する。

### Registry objects / schema（仕様のみ）

| Object | 必須fieldと意味 |
| --- | --- |
| Question | `question_id`, question text/reference source hash, `registry_version` |
| Sentence | question-scoped sentence ID、title、sentence index、text/hash。sentenceは支持箇所であってfactではない |
| Fact | `fact_id`, `fact_text`, `fact_type`（atomic_fact / relation_step / answer_claim）, `reference_basis`（raw_discovery / gold_anchor / both）、review根拠 |
| Support set | `support_set_id`, `fact_id`, `evidence_sentence_ids`, `support_set_sufficient`（yes / no / unclear）。複数sentenceが共同で支持する場合を表す |
| Reasoning path | `path_id`, `path_basis`（gold_anchored / raw_discovered_alternative）、fact参照・関係・target answer、妥当性判定。人間が構成するreference pathでありモデル内部推論の復元ではない |
| Path–fact membership | `question_id`, `path_id`, `fact_id`, `required_within_path`（yes / no / unclear）、候補support-set参照 |
| Judgment / provenance | `registry_reviewer`, `registry_version`, R1/R2 pass、独立票／adjudicatedの別、根拠箇所、timestamp、source hashes |

flat exportでも上記の`question_id / path_id / path_basis / fact_id / fact_text / fact_type / required_within_path / support_set_id / evidence_sentence_ids / support_set_sufficient / reference_basis / registry_reviewer / registry_version`を保持する。別オブジェクトのID参照を失わない。

`required_fact`は**path-conditional required fact**である。path内のrequired factsはAND、同じfactの十分なalternative support setsはOR、妥当なalternative pathsはOR。全経路のfactの和集合を「すべて必要」とはしない。support set / pathがunclearならprimaryの確定経路へ昇格させず、件数とcoverageを報告する。

## 3. Stage labelsとapplicability

各記録はquestion / path / fact / Worker / arm / route / source record IDを持つ。`observed_stage_state`、`applicability`（applicable / not_applicable / unclear）、`applicability_reason`、根拠となる文字列・ID・レコード位置を別fieldにする。`NA`は非適用の表示値でありsemantic categoryではない。未入力のmissing/nullを`unclear`へ変換しない。

| Stage | 定義・state | 判定主体・制限 |
| --- | --- | --- |
| S0 Reference Evidence Presence | fact/support setのreference evidence中の存在。`complete / partial / absent / unclear` | ID/text/hashの機械確認＋registryの意味判定。reference integrity checkが中心 |
| S1 Documented Worker Accessibility | **actual serialized Worker input**に十分な登録support setがあるか。`complete / partial / none / unclear` | 原則machine-deterministic。intended visibility/partition manifestと実入力を別に照合。実入力欠落はnoneではなくunclear |
| S2 Worker Public Expression Fidelity | 保存public outputがfactを表現するか。`correct / partial / distorted / absent / unclear / NA` | 人間の意味判定。正しい引用IDだけでcorrectにしない。「Extraction」と呼ばない |
| S3 Publication-Transition Retention | 独立したbefore/after publicationで意味が保持されたか。`retained / partial_loss / distorted / lost / unclear / NA` | 下記transition識別が前提。公開前内部状態を推定しない |
| S4 Synthesizer-Input Evidence State | actual serialized Synthesizer input内のfactの状態。`correct / partial / distorted / absent / unclear / NA` | 意味判定と機械照合を分離。Artifact経由と補足原文経由を区別 |
| S5a Final Output Fact Relation | `reflected / contradicted / not_asserted / unclear / NA` | 最終出力にfactが表現される関係。bridge factがshort answerに書かれないだけではfailureにしない |
| S5b Downstream Evidential Support | `final_answer_supported_by_received_path`: `fully_supported / partially_supported / unsupported / unclear / NA` | **受け取った入力に存在するregistry path**で最終回答を支持できるか。question/arm/pathを単位に評価。gold正答率と別物 |

S1はWorkerごとの入力について判定する。1つのsupport setが複数Workerに分散しているだけなら、そのWorkerのcomplete accessとはしない。system-level union coverageは別の記述値とする。パラメトリック知識で正しい表現が出たことは、access violationや情報漏洩の証拠ではない。

### S3: transitionの識別を先に行う

`publication_transition_type = separate_records / identity_alias / unknown`を記録する。`identity_alias`なら`S3=NA`、理由`no_separate_transition`とし、publication成功0/1へ変換しない。単なる同じ文字列やmetadataの追加では独立した意味変換の証拠にならない。

現在の`app/orchestration/orchestrator.py`は`record.result.output`をArtifact.payloadへ設定する。Study 2のsource validationもtyped normalization後のWorker outputとArtifact.payloadを照合する。このためidentity aliasの可能性を明示する。ただし各対象レコードの実際のlineageを確認して分類し、コードだけで全ケースの判定結果を作らない。

Artifact自体の`artifact_fact_state`（correct / partial / distorted / absent / unclear）は別に記録できる。S3がNAでもS4の入力照合は可能であり、NAをpublication成功と見なす必要はない。独立before/afterがない場合、内部抽出とpublication lossを区別できない。

### S4 / S5: 機械照合と支持の区別

S4には`machine_payload_match = match / mismatch / unclear / NA`、expected/actualの正規化規則・hash・位置を別に記録する。`received_via = artifact / supplementary_evidence / both / neither / unclear`とroute別semantic stateも保存する。Bで補足原文にfactがあることはWorker expressionの修復ではなく、別routeでのavailabilityである。Cの中立文がfactを含むと仮定しない。

S5は、出力の主張とreceived pathの支持関係を記録する。正答でも実入力から支持経路を確認できなければ、正答率とsupport判定を混同しない。支持経路があっても実際にモデルがそれを参照したとは主張しない。S5bは必要な橋渡し関係が入力にそろうかを含め、最終短答にbridgeを逐語記載することは要求しない。

## 4. Observed stateとderived failure event

reviewerはstageのstateと根拠を独立に記録する。failure taxonomyはfreeze済み規則を用いるanalysis layerで導出する設計であり、`first_observable_failure_stage`はreviewer手入力禁止。規則は以下を基本案として、校正後・本番前に固定する。

| Event label | Upstream prerequisite / 導出条件 |
| --- | --- |
| `reference_evidence_absent` | S0=absent。source欠損で判別不能ならundetermined |
| `access_partial` / `access_absent` | reference supportがcompleteで、当該WorkerのS1=partial / none |
| `expression_absent_after_complete_access` | S0とS1がcompleteで、S2=absent |
| `expression_distorted_after_complete_access` | 同上でS2=distorted。内部理解の失敗とは呼ばない |
| `publication_partial_loss / publication_loss / publication_distortion` | separate_recordsかつS2=correctというbeforeがあり、afterに対応するpartial_loss / lost / distorted。identity_aliasでは導出しない |
| `transmission_record_mismatch` | 規定のArtifact routingのexpectedとactualが不一致で、そのfactを含む部分に関連する。無関係なmetadata差は別のrecord diagnostic |
| `transmission_partial_loss / transmission_distortion` | published factがcorrectという前提があり、Artifact routeのactual inputでpartial / distorted。上流absentの伝播を新しい転送失敗としない |
| `answer_unsupported_despite_complete_received_path` | S4に少なくとも1つの妥当な完全pathがあり、S5b=unsupported |
| `final_output_contradicts_received_fact` | S4 fact=correctで、S5a=contradicted。因果的な「無視」とは呼ばない |
| `undetermined` | prerequisite不明、独立transitionなしの帰属不能、または必要な記録不足。明確な他eventを消さず不確実性として保持 |

partial expression等はstage state・metricに残す。absentやdistortedへ強制変換しない。部分的アクセスだけをC3回答誤りの原因と扱わない。`downstream_nonuse`、`multiple_failures`というcategoryは使わない。

イベントレコードには`event_id / stage / labels / fact-path-worker-arm-route scope / prerequisite references / supporting record locations / rule_version`を持たせる。record mismatchと同一箇所のsemantic lossは同じeventの複数labelとして保持し、二件へ数えない。上流S2=absentがそのままS4=absentになった場合、S4はobserved absenceだが独立したtransmission eventではない。別Workerや別pathの事象もscopeなしで混ぜない。

`failure_count`と`has_multiple_distinct_observable_failures`は重複除去したdistinct eventから導出する。最初の障害はstage順の**first observable failure**でありroot causeではない。先行する適用stageが不明で最初を特定できない場合は`undetermined`とし、後段で確認できたeventを別に残す。identity aliasのS3は非適用としてスキップするが成功とは数えない。`no_failure_observed`は全適用stageを評価できた範囲でのsummaryであり、内部失敗がないことの証明ではない。

## 5. Reviewer workflow / calibration / progressive disclosure

1. 実装・実験作成者以外の2名を確保し、role、経験、利益相反、既読ケースを記録する。AIは人数に数えず、Codexは空票を埋めない。
2. **Registry calibration:** 対象30問外のHotpotQA 4〜6問程度を候補とする。選定条件と公開範囲を事前固定する。今回その選定・取得・判定は行わない。
3. **Stage calibration:** bridge、comparison、partial、distorted、absent、alternative path、identity_alias、unclearを含むedge-case vignetteを使う。架空例なら実データ・実験結果と明確に区別する。
4. 固定2問のみで終了しない。最後のbatchで新guideline ruleが発生せず、必須edge caseを扱えたことを終了条件候補とする。安定するまで追加batchと改訂履歴を保存する。高いkappaを達成するまで調整する方式にはしない。
5. registry R1/R2独立票→adjudication→registry freeze。codebook v1.0、derivation rules、分析・packet仕様を本判定前にfreezeする。
6. 本判定は独立に、S1→lock→S2→lock→S3→lock→S4→lock→S5のprogressive disclosureで行う。S0はregistry/reference integrityの段階で固定する。S1でWorker outputを、S2でArtifact/Synthesizer outputを先に見せない。final answerはS5まで非開示。
7. 条件名、aggregate results、Answer F1/EMを非開示にする。**allocation-blinded where feasible**であって完全blindではない。入力構造から条件を推測でき、R2を担当したreviewerはgoldを既知である。これをlimitationsに記載する。
8. 各stageの独立lock済み票はimmutable保存する。訂正が必要なら追加versionと理由を残す。全独立票保存後にdisagreement resolutionを行い、adjudicated labelsは別versionとする。解決不能はunclear / undeterminedを残す。
9. 本判定開始後に重大変更が必要ならstop→amendment→new version→影響ケース**すべて**再判定→旧票保存。都合のよいケースだけ再判定しない。

## 6. IAA計画（未計算）

nominal categorical stage itemsのprimaryはraw percent agreement、**unweighted Cohen's kappa**、marginal counts / confusion matrix、n evaluable units。applicability agreementを別に報告する。semantic agreementは両者がapplicableとした単位を対象とし、分母・applicability不一致・excluded coverageを併記する。

substantive judgmentとしてのunclearはカテゴリに含める。not_applicableはsemantic stateから分離する。missingは未判定でありunclearに変換しない。疎なカテゴリやprevalence偏り、Pe=1でkappaが未定義になる場合を明示し、raw agreementだけで妥当性を証明しない。weighted kappaは主semantic statesには使わない。Krippendorff's alphaはmissing-data sensitivity等の補助候補として、採用するなら方法・ソフトウェアを開始前に固定する。

multi-label event setsはindependent stage labelsから同じ規則で導出し、exact-set agreement、Jaccard、label-wise binary raw agreement/kappaとpositive countsを報告する計画。両者空集合のJaccardは1と定義し、非空集合subsetのcoverageも併記して空集合一致の多さを隠さない。これはderived-label agreementであり独立した原因診断の一致ではない。

IAAは必ず**pre-adjudication independent labels**から算出する。adjudicated labelsでIAAを算出しない。registry自由生成の一致、固定候補への意味判定一致、stage一致を分ける。[IAA survey](https://aclanthology.org/J08-4004/)を背景に、ここに記す選択は本研究の事前設計とする。

## 7. Metrics / statistical unit / 次段階

[Metrics plan](evidence-lineage-metrics-plan.md)で分子・分母・eligibility・coverageを定義する。primary independent unitはquestion、primary aggregationはquestion-level macro。fact、Worker、armを独立sampleとして扱わない。Study 2はquestionを再標本化する際に共有S0〜S3とA/B/Cを一緒に保持する。CIが必要ならquestion-clustered bootstrapを候補にし、draws/seedを開始前に固定する。質問間で同じ文書・entityを共有する依存も残る。

人手レビュー→observable failure pattern→specific hypothesis→人間が相談・事前計画する確認実験という順序を守る。人手分析も原因の因果的確定ではない。新モデル・未使用質問・反復・factor固定・compute統制・representation介入は提案候補に留める。

## 8. 旧kitとの関係と開始条件

旧kitはcitation support、旧worker/transfer/synthesis分類、final answer supportの判定用資料を提供する。ただし、全traceを同時に開示し、two-pass frozen registry、独立publication transitionの識別、route別S4、S5a/b、path-level分母、progressive locksを満たさない。旧kitの票はv3の判定結果へ自動変換しない。

将来の新kitにはraw-only R1 packet、gold-alignment R2 packet、frozen registry、actual Worker/Synthesizer serialized input、publication provenance、route別補足原文、stage限定packet、lock/version履歴が必要。source hashesと匿名case linkageはauthor側manifestで保持する。旧kit・schema・builderは今回変更せず、新kitも生成しない。[開始前checklist](human-review-preflight-freeze-checklist.md)と[統合監査](../../../docs/deep-research-integration-audit.md)を参照。

### 方法論上の参照

[HotpotQA](https://aclanthology.org/D18-1259/)のsupporting sentencesはregistry alignmentに利用するが唯一の推論経路とは扱わない。[Compositional Questions Do Not Necessitate Multi-hop Reasoning](https://aclanthology.org/P19-1416/)は代替・shortcut経路を区別する動機となる。[AIS](https://aclanthology.org/2023.cl-4.2/)、[ALCE](https://aclanthology.org/2023.emnlp-main.398/)、[FActScore](https://aclanthology.org/2023.emnlp-main.741/)は外部証拠による出力支持の参考であり、内部の証拠利用を観測する方法ではない。[W3C PROV-DM](https://www.w3.org/TR/prov-dm/)のentity/activity/derivationをlineage記録の参考とし、semantic truthや因果性の保証とはしない。two-pass、各label、freeze・校正終了条件は本研究用の設計であり、これらの文献がそのまま同一仕様を定めたとは主張しない。
