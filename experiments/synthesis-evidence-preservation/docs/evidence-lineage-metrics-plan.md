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
| Downstream Evidential Support | S5b=fully_supported | 受信したpathの支持と最終回答を判定できるquestion–arm units | fully+partially_supported。partial/none received pathも判定対象とし、complete path subsetの値を別記。S5a=not_assertedのbridgeだけでunsupportedにしない |
| Fact End-to-End Survival | 同一factについてdocumented complete Worker access→correct public expression→Artifact retention→Artifact route S4 correctの連続lineageが少なくとも1つ存在 | S0=completeのunique path-conditional factsで、必要なrecordsが判定可能 | 本metricは**Artifact経由でSynthesizer入力まで**。alias transitionはS3成功ではなく構造的にbypass。補足原文だけの復元はこのsuccessでなくAny-Route Availability。final短答への逐語記載は要求しない |
| Path End-to-End Survival | 少なくとも1つの妥当なpathで全required factsの上記連続lineageが存在するquestions | 少なくとも1つの妥当なfrozen pathを持ち、path success/failureを判定可能なquestions | AND within path、OR across paths。各factの連続lineageは同じWorkerに由来している必要があるが、異なるfactsは異なるWorkers由来でもよい |

最後のPath metricはprimary候補。補足原文を含む**Any-Route Received-Path Availability**も別に報告する計画で、全path-required factsがS4にそろうかを判定する。Artifact lineageとraw-evidence routeの復元を混同しない。path availabilityとS5b fully_supportedの共同成立は補助指標候補であり、モデルがそのpathを使ったという主張ではない。

Artifact-route metricは固定Worker/Artifactが共有されるA/B/Cで同じ情報を繰り返し数えない。arm別に変わり得る比較対象は実際のS4のroute availabilityとS5のoutput supportである。共有upstream stageの差を、Synthesizer入力介入の効果として検定しない。

pathごとのrequired factsは条件付きであり、alternative paths全体の和集合を必須にはしない。factの重複IDはquestion内で一度だけ数える。primary path集計に加えてgold-anchored / raw-discovered alternativeの別、bridge / answer claim等のfact type別を記述的に示す候補。未確定path・support setはcoverageを示し、都合よくprimaryへ取り込まない。

## Question-level aggregation / uncertainty

fact-level metricは各question内で分子/分母を計算し、分母>0のquestionの平均を**question-level macro**として報告する。question内でfactの多いケースが重くなるpooled microはsecondary descriptiveに留める。binary path survivalはquestion比率として集計する。対象question数、除外question数、question別coverageを併記する。

Study 2ではS0〜S3の共有レコードはquestionごとに一度だけ保持する。S4/S5をA/B/C別に持たせ、同じ24問のpaired differencesをquestion-levelで構成する。shared recordsを72独立観測として扱わない。Study 1とStudy 2の同じquestionも独立sampleとしてpoolしない。

CIが必要ならquestion-clustered bootstrapを第一候補とする。questionを復元抽出し、そのquestionに属する全facts、paths、Workers、共有stages、A/B/Cを一緒に保持する。候補設定はpercentile 95%、10,000 draws、seed=20261002で、**人間が開始前に採否・実装・ゼロ分母draw処理を固定**する。今回は実行しない。IAAの不確実性を出す場合もfact単位を独立再標本化しない。

N≈30/24、1モデル1反復、rare failures、question間のentity/document共有、registry設計への依存が限界。question-clusteringだけで全質問間依存が解消するとはしない。mixed-effects modelはsecondary/exploratory候補に留め、主結論を小標本のモデル推定へ依存させない。多指標・arm比較は記述的探索として整理し、primary metricとsensitivityを事前区別する。今回新しい有意性主張は作らない。
