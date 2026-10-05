# Observable Evidence Lineage — Codebook candidate v0.1.0

2026-10-05。**候補・未freeze・pilot未実施・human labels 0**。人間の採用・pilot後にv1.0 freeze候補を作る。これは判定規則であり、本研究caseの判定結果ではない。[Pilot](PILOT-PROTOCOL.md)・[Adjudication](ADJUDICATION-RULES.md)・[v3設計](../docs/human-review-stage-analysis-plan-v3.md)と併用する。

## 観測対象と判断の順序

<!-- rule: GEN-OBS-001 -->
hidden reasoning、internal understanding、internal evidence use、causal reliance、root causeは判定しない。対象は保存されたobservable recordsのみ。

```text
Reference evidence → actual Worker input → Worker public expression
→ observable publication transition → actual Synthesizer input
→ final-output evidential relation
```

引用ID一致だけではsemantic correctnessとせず、payload一致だけではsemantic retentionとしない。正答だけではevidenceを内部利用したとしない。独立票をlockするまで相手の票・将来stage・総合scoreを見ない。S0はregistry/reference integrity時、S1以降はprogressive disclosureで判定する。

## 共通のsemantic rules

各factについてregistryのentity / relation / value・attribute / polarity / 必要なtime・scope qualifiersを確認し、該当recordの文字列位置を引用する。対象外factや別Workerの記述を混ぜない。

| Stable rule ID | 判定規則 |
| --- | --- |
| GEN-SEM-001 | semantic equivalence：必要なentity、relation、value、polarity、qualifierが同じならparaphraseでもcorrect候補。逐語一致を要求しない |
| GEN-PART-001 | partial：必要な意味要素の一部は正しいが、path-conditional factを十分に表す要素が欠ける。明確な矛盾があるときはdistortedを優先 |
| GEN-DIST-001 | distorted：対象factに対応する主張があるが、entity、value、relation direction、polarity、temporal qualifier等の重要部分がreferenceと矛盾する。否定・relation reversalも含む |
| GEN-ABS-001 | absent：読める対象recordにfactを支持するsemantic contentがない。citation IDのみ、対象と無関係な話題、特定不能な代名詞だけではcorrectにしない |
| GEN-UNC-001 | unclear：observable materialはあるが、複数の合理的な読みでlabelが分かれる。単に判断が難しいという理由だけで付けず、競合する読みと不足する識別情報を記録する |
| GEN-MISS-001 | missing：required record自体が欠損／読めない。semantic推測で埋めず、record_availability=missing/unreadable、state=nullを原則とする。S1の記録欠損にunclearを表示する場合もavailabilityをmissingにし、集計上missingとして区別する |
| GEN-ALIAS-001 | entity alias：raw/registry内の明示的同定、または一意な局所coreferenceだけ許可。姓の一致や外部常識だけで同一entityとしない。曖昧ならunclear |
| GEN-NORM-001 | 数値・日付：単位・precision・timezone・calendar・期間が同じ場合だけ正規化を許可（例：1,000=1000、明示された同一暦のISO日付）。年だけを完全日付と同一視せず、単位や日月順が不明ならunclear |
| GEN-ADD-001 | unsupported addition：対象fact自体を変える未支持の追加qualifierはcorrectにしない。明確な矛盾はdistorted、支持も否定もできない重要な追加はunclear。独立した無関係claimは別に記録し、正しい対象factのlabelを自動降格しない |
| GEN-HEDGE-001 | uncertainty：referenceが断定しているのに「XかY」「かもしれない」と候補を残す表現はcorrectではない。確定部分のみならpartial、どの主張も一意に復元できなければunclear。reference自体の留保・否定を取り除くとdistorted候補 |
| GEN-NA-001 | NAは構造的非適用のみ。低confidence、空出力、誤答、欠損record、難しい判断をNAにしない。applicabilityと理由を別記し、missingとunclearを区別する |

contradictory assertionsが同一recordに共存するときは、そのfactについてdistortedを優先し、両箇所を記録する。明示的な撤回・訂正があり唯一の最終主張を識別できる場合は、その訂正後主張を判定し旧主張のpointerも残す。単なる文脈不足で矛盾を作らない。

## S0 — Reference Evidence Presence

<!-- rule: S0-PRESENCE-001 -->
登録support setsはOR。少なくとも1つの十分なsupport setがreference evidenceに存在すればcomplete。関連する部分はあるがfact全体の支持に不足ならpartial。読めるcomplete evidence中に支持materialがないならabsent。wordingやreference mappingの解釈が曖昧ならunclear。source自体の欠損はmissing。gold supporting sentenceというだけでcompleteにしない。support-setごとの根拠と十分性を残す。

## S1 — Documented Worker Accessibility

<!-- rule: S1-ACCESS-001 -->
actual serialized Worker inputを基準に、登録済みで十分性yesのsupport setsとsentence ID/text/hashを照合する。1つのcomplete setが当該Worker内にあればcomplete、一部だけならpartial、十分なsetのmaterialが全くないことを確認できればnone。input欠損／mapping不能はunclear（欠損metadataも併記）。intended partitionとactual inputを別欄に保存する。複数Workersのunionを1 Workerのcompleteにしない。十分性unclearのsetしかない場合もcompleteへ昇格しない。

## S2 — Worker Public Expression Fidelity

<!-- rule: S2-CORRECT-001 -->
correct：保存public outputがregistered factの必要な意味要素を十分表現。paraphrase可、citationは独立した根拠項目であり正しさの代用でない。

<!-- rule: S2-PARTIAL-001 -->
partial：核となる一部は正しいがpath上必要な意味要素が欠ける。referenceとの明確な矛盾があればpartialではなくdistorted。

<!-- rule: S2-DISTORT-001 -->
distorted：対象factに対応する記述があり、重要なentity / relation / value / polarity / temporal qualifierを誤る。内部の理解や抽出を判定したとはしない。

<!-- rule: S2-ABSENT-001 -->
absent：対象factの意味内容がない。正しいcitation IDだけでもabsent。空のpublic outputが実際に保存されていればabsentであり、record自体の欠損とは別。

<!-- rule: S2-UNCLEAR-001 -->
unclear：読みが曖昧でcorrect / partial / distorted / absentを一意に選べない。NAは構造的非適用のみ（GEN-NA-001）。

## S3 — Publication-Transition Retention

<!-- rule: S3-ALIAS-001 -->
最初にprovenanceでseparate_records / identity_alias / unknownを記録する。identity_aliasはS3=NA、applicability=not_applicable、reason=no_separate_transition。publication success=1にもfailure=0にも変換しない。文字列一致だけではaliasと断定しない。

<!-- rule: S3-UNKNOWN-001 -->
unknownは独立transitionの有無が識別不能。publication-specific lineageはnon-identifiable。S3=unclear、applicability=unclear、reason=transition_not_identifiableを使用できるが、成功／失敗へ補完しない。Artifact自体のsemantic stateは別に判定可能。

<!-- rule: S3-RETENTION-001 -->
separate_recordsかつS2=correctというobservable beforeがある場合：afterも同じfactを十分保持→retained、一部の意味要素だけ消失→partial_loss、重要な意味が矛盾・変化→distorted、完全消失→lost。before/afterは読めるが意味比較が一意でない→unclear。record欠損→missing。

<!-- rule: S3-GATE-001 -->
S2がcorrectでない場合は「correct factがpublicationで失われた」というfailureを導出しない。この候補ではretention比較をNA / no_correct_before_factとし、afterのartifact_fact_stateは独立記録する。S2がunclear/missingの場合はNAで消さずretentionもunclear/missingを残す。publication failureの既存prerequisite（separate_records AND S2=correct）を維持する。
この条件付きNAはidentity_aliasのstructural bypassではない。separate_recordsのE2EでS3を成功補完・skipせず、既存のNA/evaluability coverageへ残す。上流の確定failure eventと、全連続lineageの判定可能性は別に記録する。

## S4 — Synthesizer-Input Evidence State

<!-- rule: S4-ROUTE-001 -->
対象はactual serialized Synthesizer input。correct / partial / distorted / absent / unclear / NAの意味境界はS2と同じ。overall、artifact_state、supplementary_stateを別に記録し、received_via=artifact / supplementary_evidence / both / neither / unclearを残す。supplementary evidenceでcorrectでもWorker/Artifact survivalへ遡及帰属しない。

<!-- rule: S4-MACHINE-001 -->
machine_payload_match（match / mismatch / unclear / NA）とsemantic stateを別に判定する。matchでも原payload自体がdistortedならsemantic correctでない。無関係metadataのmismatchをfact lossにせず、fact-related pointerを残す。routeが互いに矛盾する場合は両箇所とoverall distortedを記録し、correct routeの存在だけで矛盾を隠さない。

## S5a — Final Output Fact Relation

<!-- rule: S5A-RELATION-001 -->
reflected：出力が対象factを明示または一意に意味表現。contradicted：対象factと矛盾。not_asserted：そのfact自体を述べない。unclear：出力との関係が一意でない。NAは構造的非適用のみ。bridge factがshort answerに書かれないnot_assertedだけではfailureにしない。

## S5b — Downstream Evidential Support

<!-- rule: S5B-SUPPORT-001 -->
frozen valid pathごとに、actual S4 inputとfinal answerの支持関係を判定する。fully_supported：その受信pathがfinal answerの主要claimを十分支持。partially_supported：一部は支持するが主要claimの支持が不完全。unsupported：読める受信material/pathから主要claimを支持できない。unclear：支持関係が一意でない。NAは構造的非適用のみ。gold一致や内部利用の推定でfully_supportedにしない。bridgeを最終短答へ逐語記載させない。

<!-- rule: S5B-ELIGIBLE-001 -->
primary metricはS4に少なくとも1本のcomplete valid frozen registered pathがあるquestion–armのみ。成功はその受信完全pathの少なくとも1本でfully_supported。partial/none-pathはsecondary descriptiveのみ。S5b missing/unclearはcoverageへ。unsupported failureはcomplete-path eligibilityかつ受信完全pathsがいずれもunsupportedのときだけ。partially_supportedをunsupported eventにしない。

## Alternative valid path / path-conditional requiredness

<!-- rule: PATH-VALID-001 -->
primary valid pathの条件：system outputを見る前に候補化／adjudicateされ、registered facts/support setsがraw/reference evidenceで支持され、questionの答えを十分に支持し、未登録の外部factual premiseを要しないこと。偶然の答え文字列一致やモデル出力に都合がよい後付け採用は不可。goldと異なる経路も可。registryは全system output開示前にfreezeする。

<!-- rule: PATH-LOGIC-001 -->
equality、comparison、temporal ordering、明示的entity linking、simple compositionは、全factual operandsと必要qualifiersが登録・支持され、接続を人間が説明できる場合に限り可。一般的な論理演算と新しいworld-knowledge premiseを区別する。年だけで同一年内の前後を決める、同名entityを外部知識で同定する、数値の単位を補うことは不可。境界不明ならunclear path。

<!-- rule: PATH-STATE-001 -->
valid：上記条件をすべて満たす。invalid：少なくとも1条件を明確に満たさない（外部premise必須等）。unclear：支持十分性・linking等が確定できない。既存schemaへの保存はvalid→yes、invalid→no、unclear→unclear。新しいsemantic enumをhistorical registryへ遡及適用しない。

<!-- rule: PATH-REQUIRED-001 -->
required_within_path=yes：そのfactを除くと**そのpathだけ**ではtarget benchmark answerを十分支持できない。no：補助・冗長で除いても当該pathが十分。unclear：反実的なpath十分性が一意でない。他のvalid pathが存在しても当該pathのyesをnoへ変更しない。十分性yesの同一factのalternative support setsはOR、path内required factsはAND、valid pathsはOR。

<!-- rule: PATH-POST-001 -->
output開示後の新pathはpost_freeze_candidate_pathとして別versionに保存する候補であり、primary frozen registryに追加しない。amendment/sensitivity採用の範囲と理由は人間が別に固定する。

## 人工例の読み方

[examples/semantic-boundaries.md](examples/semantic-boundaries.md)はclear positive / boundary / counterexampleを持つ**人工の教材仕様**。本研究caseのsemantic annotation、pilot票、real registryではない。各rule IDは協議記録のguideline_ruleから参照できる。規則変更時はIDを別意味に再利用せず、新versionで履歴・影響範囲を残す。
