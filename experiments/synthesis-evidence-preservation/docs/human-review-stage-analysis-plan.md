# fact単位の段階別独立人手分析計画

設計revision：`human-stage-review-v2-draft`、2026-10-02。状態：**設計のみ・人間の開始判断待ち**。新kit・判定票・評価実装はまだ作成していません。独立人手レビューは0/2名です。

本計画は[研究目的・RQ2](../../../docs/research-question-and-contributions.md)へ直接答えるための探索的内容分析の仕様です。freeze済み[REVIEW.md](../REVIEW.md)を変更せず、分析項目を別文書で拡張します。旧kitのまま新schemaで判定済みとしません。[依存・影響監査](review-stage-amendment-and-kit-impact.md)と併せて人間が採用revisionを決めます。過去の生成条件、主評価、scorer、結果は変更しません。

## 1. 分析対象と単位

元30問のC3を主対象とし、C1/C2は匿名参照を維持します。Study 2は既存24問×A/B/Cの72最終回答を対象とします。smoke9件は本判定集計に追加せず、同じ質問・同じ固定Workerを独立観測として数えません。元の校正用2問を維持し、残り28問と新72回答を本判定にします。

基本キーは`question_key / fact_id / target_case_code / reviewer_id`です。Worker別のstage 1〜3は`worker_code`を追加します。同じ24問のfactと固定Workerの判定は一度のsource判定へリンクし、A/B/Cで抽出失敗の件数を三重に増やしません。Stage 4/5は実際の各合成入力・回答について判定します。

factは人物・日付・関係・制約等の検証可能な命題です。単にsentence ID一つをfactとしません。複数文にまたがる関係は支持集合を記録し、atomic factと、複数factを組み合わせた関係・回答経路を分けます。gold支持文を唯一・完全な必要fact一覧とせず、別表現・代替支持経路を許します。

### fact registryと必要性

校正後、本判定の出力を読む前に、2名が質問・raw evidenceだけから候補fact／支持経路を整理し、対応づけた`fact-registry`のrevisionを固定する方針です。この準備の合意は本判定のstage判断の合意ではありません。実装作成者・AIが正解に都合のよいfactを選ぶ方法は採りません。

registryには`fact_id`、`fact_text`、`fact_type`（atomic/relation）、`support_sets`（代替sentence集合）、`answer_path_ids`、`required_for_path`（yes/no/unclear）、`reference_basis`（raw_only/gold_aided）、必要性の根拠を持たせます。ある経路に必要でも別経路では不要なfactを全回答の必須と扱わず、同じ最小支持経路の中で欠落を評価します。候補の必要性を合意できなければ`unclear`で保持し、確定factだけの集計と不確定候補を分けます。

最初はraw-onlyで行い、goldは条件・総合scoreと切り離して管理します。人間が後段にgold照合を採用する場合は、独立票の固定後に別registry revision・別の補助判定を追加し、元票を変更しません。rawにない評価上の候補factはstage 0=noになり得ます。gold由来factとraw-only factを同じreference basisとして混ぜません。fact粒度・支持経路・goldの提示時点は開始前の人間の判断事項です。

## 2. 情報フローと観測可能性

```text
Raw evidence
  → S0：評価対象原文に必要factが存在
  → S1：特定Workerの実入力に支持証拠が存在
  → S2：保存されたWorker公開出力でfactを正しく抽出・表現
  → S3：公開Artifactにfactを保持
  → S4：実際のSynthesizer入力にfactが存在
  → S5：受信factと最終回答の利用・整合を観測
  → Final answer
```

これは観測記録の分析経路で、モデル内部の思考過程ではありません。S2とS3は概念上区別しますが、同じ公開payloadしかない場合には独立した過程として識別できません。保存されたWorker応答の公開JSONと公開Artifactの前後を別に確認できるときだけpublication固有の変化を評価します。内部で「理解していたが書かなかった」とは推測しません。

## 3. 記録schema（設計仕様、未実装）

列挙値は下表のとおりとし、自由な同義ラベルへ置き換えません。未判定は`null`＋`review_status=not_reviewed`で、`no`や`unclear`とは別です。`unclear`は資料を読んだ上で判定不能、`not_applicable`は構造上評価対象外で、必ず理由を残します。

| Stage / field | 値 | 判定基準・担当 |
| --- | --- | --- |
| S0 `raw_evidence_contains_required_fact` | yes / no / unclear | 人間：当該問の評価対象raw本文が、そのfactまたは支持経路を含むか。本文箇所と支持sentence IDを示す。正解文字列だけの一致ではyesにしない |
| S1 `worker_had_access_to_required_evidence` | yes / no / unclear | Worker別。支持集合と、保存requestのknowledge／policy／partitionを機械照合する。少なくとも一つの十分な支持集合が実入力に揃えばyes。一部だけならno＋available/missing IDs。記録不足・矛盾ならunclear。閲覧・注意・理解まで意味しない |
| S2 `worker_extracted_fact_correctly` | yes / partial / no / unclear / not_applicable | 人間：保存された公開responseのcandidate_answer/findings/uncertaintyがfactを意味的に正しく表現するか。正しい引用IDだけではyesにしない。誤表現と欠落は補助fieldで区別する |
| S3 `public_artifact_retained_fact` | yes / partial / no / distorted / unclear / not_applicable | 人間：実際の公開Artifactのpayloadに正しいfactが保持されたか。誤った人物・日付・関係はdistorted。Worker応答との前後変化は別途確認し、単なる上流誤りの継承をpublication固有損失としない |
| S4 `synthesizer_received_fact` | yes / no / unclear / not_applicable | 人間：送信された実合成入力に正しい完全なfactがあるか。partial/distortedのみならno＋入力の意味状態を別記。機械的payload一致は別field。Study 2ではArtifactとsupplementary原文の経路を分ける |
| S5 `synthesizer_used_fact_correctly` | yes / partial / no / contradicted / unclear / not_applicable | 人間：受信したfactと観測できる最終回答・引用・明示された関係の整合。内部で何を用いたかは推定しない。正答だけではyesにしない。短い回答に中間factの明記がないだけではnoにしない |

S2の`no`には`worker_expression_state=absent/distorted`を添えます。`yes/partial/unclear/not_applicable`にも対応する意味状態と理由を残します。S4には`input_fact_state=correct/partial/distorted/absent/unclear/not_applicable`と`received_via=artifact/supplementary_material/both/neither/unclear`を併記します。Bの原文で受信factが回復しても、Worker公開の欠落を修正済みに書き換えません。

S5の`yes`は「記録上、受信factと整合する適切な利用を確認できる」の操作的判定で、因果的な内部利用を証明しません。適切な回答が複数経路で得られ、どのfactを使ったか見えなければ`unclear`にします。`no`は、必要性・十分な受信・求められた出力との不整合から不使用を判定できる場合、`contradicted`は正しい受信factと最終出力が明示的に矛盾する場合に限ります。正しいfactを受信していないなら、そのfactを「使わなかった」失敗とはせず原則`not_applicable`です。

### provenanceと機械項目

各記録に以下を添付します。値の事前計算・新フォーム生成は今回実行しません。

| 記録群 | field / 内容 |
| --- | --- |
| 識別・revision | study/source study、question_key、case_code、target_reference、worker_code、fact_id、registry_revision、schema_revision、criteria_revision、reviewer_id、reviewed_at、calibration、本判定phase、reference_basis |
| supporting evidence | support_sets、factの原文箇所、実Worker input ID集合、available/missing IDs、入力hash、policy/partition参照、scope判定理由 |
| 出力・公開・受信 | public response／Artifact／実合成request／finalの相対path・SHA256・JSON pointer／箇所。匿名資料からの対応を保持する |
| 機械照合 | `transmission_payload_match=match/mismatch/unclear/not_applicable`、比較対象・型正規化revision、Artifact ID/version/producer/recipient、順序、実送信入力の出自 |
| 意味判定 | 六stageの値、expression/input state、citation_supported（yes/no/unclear）、received_via、根拠箇所、短いrationale、confidence（high/medium/low）、applicability_reason |
| 識別限界 | `extraction_publication_separability=separate_records/shared_record/unclear`、unavailable_record、alternative_path、ambiguous_first_stage等 |
| 派生ラベル | observed_failure_labels、first_failure_stage、first_failure_status、secondary_failures、rule_revision、対応するstageと根拠。人手票の後に別の派生層へ保存 |

機械照合のmatchは通信上の同一性であり、S2〜S5のyesを自動補完しません。S1も「人間が定義した支持集合に対する記録上の可用性」で、必要性そのものを機械判定したわけではありません。

## 4. Failure Stageの導出ルール

ラベルは因果的な原因の確定ではなく、観測された障害／情報可用性のパターンです。排他的な一ラベルに潰さず、`observed_failure_labels`をmulti-labelで保持します。`multiple_failures`はsummary flagで、元ラベルを置換しません。

| label | 導出に必要な観測／条件 |
| --- | --- |
| `not_in_evidence` | S0=no。rawの範囲とreference basisを示す。局所資料の外に存在する可能性は否定しない |
| `not_accessible_under_partition` | S0=yesかつ特定WorkerのS1=no。局所の可用性制約で、Worker errorやquestion失敗とは同義でない |
| `worker_extraction_failure` | S0=yes、当該WorkerのS1=yes、S2=no＋expression_state=absent。partialで必要部分が欠落する場合も、欠けた述語を根拠として明記して付与できる |
| `worker_extraction_distortion` | S0=yes、S1=yes、S2=no＋expression_state=distorted、またはpartial中に必要内容の誤表現が確認できる |
| `publication_loss` | 別の保存公開responseで正しい完全なfact（S2=yes）があり、公開Artifactで欠落／必要部分喪失（S3=no/partial）。前後箇所と別記録が必要 |
| `publication_distortion` | S2=yesの正しい公開responseから、別記録のArtifactで誤変形（S3=distorted）が確認できる。上流の誤表現をそのまま公開しただけでは付けない |
| `transmission_mismatch` | S3=yesの公開factが、対応する実受信Artifactで欠落・変形し、factに関連するpayload mismatchを機械確認。無関係fieldの差だけでは付けない。Bの補足で回復した場合も経路別に保持 |
| `synthesis_nonuse` | 正しい完全なfactのS4=yes、S5=noで、必要な出力・支持経路に対する不使用を記録から示せる。短い正答や引用省略だけでは付けない |
| `synthesis_distortion` | S4=yes、S5=contradicted、またはpartialに必要な関係の誤利用が明示される。別の必要fact不足による誤答をこのfactの歪曲と自動分類しない |
| `no_failure_observed` | 当該factと適用可能な経路の判定が揃い、障害ラベルがなく、必要な出力との整合が確認できる。未判定・不明を成功に置換しない。内部利用まで保証しない |
| `multiple_failures` | 同じ分析単位に独立に根拠づけられた障害ラベルが2種類以上。別Workerの異なる経路のラベルを一つの連鎖に混ぜない |
| `undetermined` | 記録不足、必要性不明、矛盾、分離不能、適用可能stageのunclear等。障害が一部判明していても未確定部分と併記できる |

### 最初の障害と後段の障害

`first_failure_stage`の候補は`evidence/access/worker_extraction/publication/transmission/synthesis`です。`first_failure_status=identified/no_failure_observed/undetermined`を別に持ち、最初のstageを識別できない場合はstageをnull、候補stageを併記します。最初の「観測された」障害であって最初の因果原因ではありません。

S0→S1→S2→S3→S4→S5の順に、適用可能な前段が判断済みの場合だけ最初の障害を確定します。前段unclearのまま後段だけ障害が分かる場合、後段ラベルは残しますがfirstはundeterminedです。後段の`secondary_failures`はそれぞれ固有の前提と根拠が満たされたものだけです。上流でfactが無いから下流もnoという伝播だけで、合成失敗を追加しません。

S2/S3が同じ記録なら、factが公開表現にないことは記録できても「正しく抽出した後のpublication_loss」は識別できません。欠落の観測ラベルと`ambiguous_first_stage=[worker_extraction,publication]`を保持し、内部抽出が成功していたとはしません。

Worker別の`worker_path`と、全Worker・全受信経路を考慮した`fact_pipeline`を分けます。あるWorkerにアクセスがなくても、別Workerの正しいfactが到達すれば全体のaccess failureにはしません。全体の失敗は、同じ支持経路のどの必要factが未到達かを示して評価します。全factが各Worker一人に揃うことを常に要求せず、分割による統合課題をWorkerの怠慢に読み替えません。

### 仕様上の検証ケース（実測結果ではない）

- 正しいIDを引用するが人物関係を誤る：citation scopeが正しくてもS2=yesにはならない。
- Worker公開表現とArtifactにfactがなく、両者が同じ記録：publication固有の損失は判定不能。下流S5の不使用を自動追加しない。
- Artifactは正しいが対応する実入力で欠落し、fact関連mismatchがある：transmissionの候補。機械matchなのにS3=yes/S4=noなら判定・参照範囲の矛盾として再確認する。
- ArtifactにはないがB補足で正しいfactを受信：公開経路の欠落と補足経路の受信を別記し、合成の分析は実際の受信を基準にする。
- 必要factが正しく実入力にあり最終出力が明示的に反する：synthesis_distortionの候補。原因全体は確定しない。
- 短い正答に中間factが書かれていない：それだけではnonuseにしない。経路不明ならS5=unclear。

## 5. Reviewer workflow

1. 人間が採用schema／基準、fact粒度、対象・参照条件、共有範囲を決め、実装・実験作成者以外の2名を割り当てる。AIはreviewerに数えない。
2. 新kitを作る場合は別の未使用保存先、別manifest・schema/criteria/registry revisionにする。旧kit・空票・criteria・manifestを編集しない。コード変更やkit生成は別途必要性・承認・保全を確認してから行う。
3. 元Pilotの最初の2問で校正し、規則・例・曖昧な場合の扱いを合意してcriteria revisionを固定する。校正票は残し、本判定の一致率から除く。新72回答用の基準もこの段階で固定する。
4. raw-only fact registryの準備・対応づけを行う。条件・score・本判定出力を見てfact選定を最適化しない。goldを後に出す場合の分離方式も固定する。
5. 残り28問と新72回答を別々に判定する。本判定中は相談せず、互いの票・集計score・条件対応表を見ない。sourceの匿名参照、slot別閲覧順を維持し、必要なsource linkageは匿名question_keyで示す。
6. 規則改訂が必要なら一旦止め、revisionと影響範囲を記録する。旧票を上書きせず、同じ新revisionで双方が該当単位を独立再判定する。異なるrevisionの票を一組のagreementへ混ぜない。
7. 個票を保存・hash固定後、必要に応じ別層でfailure labelを導出し、一致率を集計する。人間が導出の根拠・適用性を確認する。AIは空票・判定内容を補完しない。
8. 独立票保存後にdisagreement resolutionを行う。adjudicated結果は別versionで、元の独立票・ラベル・根拠を保存する。解消しない項目はunclear/undeterminedにする。adjudicated agreementを独立一致率に使わない。

条件名・総合score・private mappingは可能な範囲で隠します。資料量、role instruction、文書分割、B補足、同質問の繰返しから推測可能なので完全blindとはしません。評価担当は対応表をローカル管理し、外部共有は人間が宛先・範囲を決めてから行います。空欄は未実施で、Codexは埋めません。

## 6. Agreementと分析の計画

主報告はstageごとのraw agreement＝同一カテゴリになった対応単位数／両者の判定がある対応単位数です。accuracyとは呼ばず、各stage・Worker scope・study/source/finalを区別します。判定数、欠測、unclear、not_applicable、カテゴリ分布と混同行列を併記します。null未判定は分母から外し件数を明記します。unclearやnot_applicableの一致だけで高くなることを避け、全カテゴリの集計と、双方が判定可能な実質カテゴリであるsubsetの集計を別に示します。後者の除外率も必須です。

同一factの対応づけがない自由記述票をそのままagreementへ使いません。registry上で不一致の必要性・支持経路は別項目として報告します。stageごとの分母は異なり得ます。fact数が多い質問を過大に重みづけしないよう、質問別の記述値も併記する方針です。固定Workerの重複と同一質問内の依存を明示し、fact数を独立標本数にしません。

Cohen's kappaは補助指標として検討します。共通revision・共通カテゴリの対応票について、原則unweightedの名義尺度として扱います。sparse/偏ったカテゴリでは不安定で、期待一致が1なら未定義です。n・カテゴリ分布・raw agreementを常に併記し、機械的閾値でレビュー品質を合否判定しません。採用・未定義時の扱いは本判定前に人間が固定します。multi-labelはラベルごとの有無の一致とラベル分布を主とし、kappaを出す場合もラベル別・補助に限定します。

failure stageの件数・割合、条件別差、一致率、kappaの実値はまだありません。分析実装・計算も今回しません。将来のstage頻度は対象・適用性・欠測・必要fact定義に条件づけた記述で、C3低下の因果寄与率ではありません。

## 7. 開始判断と確認実験の順序

人間が決める事項は、2名の独立性と担当、schema／criteria／registry revision、必要性・代替経路・gold提示方法、S2/S3の分離可能性、S5の観測的基準、校正と独立対象、匿名化とデータ共有、agreement/kappa方針です。採用済み旧計画を遡及変更せず、新設計の採用・未実施を別記します。

```text
独立人手レビュー＋不一致処理
  → 判断可能なfailure patternと残るundetermined
  → specific hypothesis
  → 確認実験の提案
  → 人間の判断・新事前計画・予算・承認
```

未使用HotpotQA、別モデル、複数反復、role固定access比較、access固定role比較、資源統制、Artifact表現介入は候補だけです。今回優先順位を確定せず、人手レビュー終了前に確認実験を開始しません。review終了後も自動で生成・download・campaign作成に移行しません。
