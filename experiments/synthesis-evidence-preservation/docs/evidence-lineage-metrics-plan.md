# Evidence Lineage metrics / aggregation plan

2026-10-02。v3 Human Reviewの**計画のみ**。値、CI、p値は生成していない。本判定前にregistry・codebook・本書の採用版をfreezeする。[Stage definitions](human-review-stage-analysis-plan-v3.md)に従う。

## 共通の分母規則

`potentially eligible`はregistryとtransition/route仕様から定まる候補数。`evaluable`は適用性と必要なupstream条件・対象stateを確定できる数。各metricで**evaluable / potentially eligible coverage**、unclear、missing、NA、non-identifiableの件数を併記する。unknown transitionは非識別でありpublication失敗としない。identity aliasはPublication Survivalのpotentially eligibleにも入れず、除外数を別記する。

下表のdenominatorはevaluable eligible units。unclear/missingはprimaryの分母から外すが、不確実性を消さない。分母0はNAであり0点ではない。適用stageを全て観測できた場合にだけend-to-endのsuccess/failureを判定する。既知の失敗があり未評価stageもある場合のpathは、failureが確定しているか／classificationがundeterminedかを分けて記録する。

strict primaryはcomplete/correct/retained/fully_supportedのみ。sensitivityは該当stageのpartialも含める。partialへ0.5などの重みを付けない。distortedはpartialへ入れない。unclearのbest/worst boundsを追加するならfreezeで規則を決め、primaryと区別する。

## Metrics

| Metric | Numerator (strict) | Denominator / eligibility | Sensitivity・適用上の注意 |
| --- | --- | --- | --- |
| Access Coverage | S1=completeのfact–Worker units | S0=completeで実入力に対してS1を確定できるregistry fact–Worker units | partialも含む値を別掲。union of Workersは別記述値で、個別Workerのcomplete accessと混ぜない |
| Worker Public-Expression Survival | S2=correct | S0/S1=completeのfact–Worker unitsでS2 evaluable | correct+partial。S1 partial/noneでの表現は別層。access completeのWorkerとexpression correctの別Workerをつなげない |
| Publication Survival | S3=retained | separate_recordsかつS2=correctで独立before/after transitionを判定可能なunits | retained+partial_loss。identity_aliasは成功・失敗とも分母外。unknownはnon-identifiable coverageへ |
| Artifact Transmission Survival | Artifact route S4=correct | artifact_fact_state=correctで、規定Artifact routeと実入力を照合できるunits | correct+partial。上流で失われたfactはtransmission failure分母にしない。record-level payload matchは別diagnostic |
| Any-Route Synthesizer Availability | 少なくとも1routeでS4=correct | S0=completeのunique registry factsで実Synthesizer入力がevaluable | correct+partial。artifact / supplementary / bothを別掲。Bで補足原文が届くことをWorker survivalとしない |
| Downstream Evidential Support | final answerがS4で利用可能だった少なくとも1本のcomplete valid frozen registered pathによってfully_supported | **S4で少なくとも1本のcomplete valid frozen registered pathが利用可能なquestion–arm**のうち、最終回答の支持を判定可能なunits | 同じeligible subset内のfully+partially_supportedはsensitivity。partial/none received pathはprimary分母外。all-evaluable support rate等はsecondary descriptiveとして別記。S5a=not_assertedのbridgeだけでunsupportedにしない |
| Fact End-to-End Survival | 同一factについて下記transition別規則を満たすArtifact-route連続lineageが少なくとも1つ存在 | S0=completeのunique path-conditional factsで、必要なrecordsとtransition別lineageを判定可能 | **Artifact経由でSynthesizer入力まで**。identity_aliasはS3=NA / structural bypass、unknownは当該lineageをnon-identifiableとする。補足原文だけの復元はAny-Route Availabilityへ。final短答への逐語記載は要求しない |
| Path End-to-End Survival | 少なくとも1つの妥当なfrozen pathで全required factsが下記transition別E2E規則を満たすquestions | 少なくとも1つの妥当なfrozen pathを持ち、path success/failureを判定可能なquestions | AND within path、OR across paths。各required factに同じE2E規則を適用。各factの連続lineageは同じWorker由来であり、異なるfactsは異なるWorkers由来でもよい。non-identifiableとcoverageを別記 |

### Downstream Evidential Supportのprimary eligibility

eligibleは、S4の実入力に**少なくとも1本のcomplete valid frozen registered path**が利用可能なquestion–armである。completeは、そのpath内の全required factsと必要な関係がS4でcorrectとして確認できることを指す。Artifact／supplementary evidence／両方という許可された受信routeは区別して記録するが、primary eligibilityは実際に受信した完全pathで判定する。

successは、final answerが**そのS4で利用可能だった完全pathの少なくとも1本**によってfully_supportedであること。未受信pathやgold正答との一致だけでsuccessにしない。S4 eligibilityを満たすがS5bがunclear/missingの場合は、共通規則に従いevaluable分母から除外し、eligible件数に対するcoverageを必ず併記する。

必要証拠が届かずcomplete pathがないケースはprimary分母へ入れず、access / expression / publication / transmissionの観測状態・適用可能なfailure rulesで別に扱う。all-evaluable casesのsupport rateとpartial-path casesはsecondary descriptiveとしてのみ残せる。primaryの分母や感度分析へ混ぜない。

`answer_unsupported_despite_complete_received_path`は同じS4 eligibilityに加えS5b=unsupportedの場合だけ導出する。partially_supportedはstrict primaryのsuccessではないが、このunsupported eventへ自動変換しない。証拠が届かなかったことだけでdownstream failureを導出しない。

### Artifact-lineage E2Eのtransition別規則

Fact / Path End-to-End Survivalは既存の**Artifact-lineage E2E**として、S0=completeの対象に以下を適用する。

| publication_transition_type | strict E2Eに必要な連続lineage | S3 / evaluability |
| --- | --- | --- |
| separate_records | S1 complete → S2 correct → S3 retained → Artifact-route S4 correct | 独立S3 transitionを評価する |
| identity_alias | S1 complete → S2 correct → Artifact-route S4 correct | S3=NA / no_separate_transition。structurally not applicableとしてskipし、**publication success=1にもfailure=0にも変換しない** |
| unknown | publicationを経由するstage-specific lineageはnon-identifiable | 当該lineageを成功にも失敗にも割り当てず、coverageとnon-identifiable件数を別記する |

Path End-to-End Survivalでも**各required fact**に同じ規則を適用する。別の識別可能なlineage／valid pathでsuccessを確認できる場合はその根拠を用い、unknownな候補を成功・失敗へ補完しない。未確定の代替候補によりsuccess/failureを確定できなければnon-identifiableとして保持する。evaluable / potentially eligible coverageを必ず併記する。

unknownでもS4自体を判定できる場合、publication attributionを要求しない既存のAny-Route Availability / Received-Path Availabilityは別に評価できる。ただし、それをArtifact-lineage E2E successへ読み替えない。identity_aliasを含む識別可能なE2Eと、独立publicationだけを対象とするPublication Survivalの分母を混同しない。

最後のPath metricはprimary候補。補足原文を含む**Any-Route Received-Path Availability**も別に報告する計画で、全path-required factsがS4にそろうかを判定する。Artifact lineageとraw-evidence routeの復元を混同しない。path availabilityとS5b fully_supportedの共同成立は補助指標候補であり、モデルがそのpathを使ったという主張ではない。

Artifact-route metricは固定Worker/Artifactが共有されるA/B/Cで同じ情報を繰り返し数えない。arm別に変わり得る比較対象は実際のS4のroute availabilityとS5のoutput supportである。共有upstream stageの差を、Synthesizer入力介入の効果として検定しない。

pathごとのrequired factsは条件付きであり、alternative paths全体の和集合を必須にはしない。factの重複IDはquestion内で一度だけ数える。primary path集計に加えてgold-anchored / raw-discovered alternativeの別、bridge / answer claim等のfact type別を記述的に示す候補。未確定path・support setはcoverageを示し、都合よくprimaryへ取り込まない。

## Question-level aggregation / uncertainty

fact-level metricは各question内で分子/分母を計算し、分母>0のquestionの平均を**question-level macro**として報告する。question内でfactの多いケースが重くなるpooled microはsecondary descriptiveに留める。binary path survivalはquestion比率として集計する。対象question数、除外question数、question別coverageを併記する。

Study 2ではS0〜S3の共有レコードはquestionごとに一度だけ保持する。S4/S5をA/B/C別に持たせ、同じ24問のpaired differencesをquestion-levelで構成する。shared recordsを72独立観測として扱わない。Study 1とStudy 2の同じquestionも独立sampleとしてpoolしない。

CIが必要ならquestion-clustered bootstrapを第一候補とする。questionを復元抽出し、そのquestionに属する全facts、paths、Workers、共有stages、A/B/Cを一緒に保持する。候補設定はpercentile 95%、10,000 draws、seed=20261002で、**人間が開始前に採否・実装・ゼロ分母draw処理を固定**する。今回は実行しない。IAAの不確実性を出す場合もfact単位を独立再標本化しない。

N≈30/24、1モデル1反復、rare failures、question間のentity/document共有、registry設計への依存が限界。question-clusteringだけで全質問間依存が解消するとはしない。mixed-effects modelはsecondary/exploratory候補に留め、主結論を小標本のモデル推定へ依存させない。多指標・arm比較は記述的探索として整理し、primary metricとsensitivityを事前区別する。今回新しい有意性主張は作らない。
