# 日本語話者向けHuman Review — 固定訳の併記方針

2026-10-05。設計候補。**翻訳資料未作成／pilot・main未開始／human labels 0／未final-freeze**。
これは英語→日本語の翻訳を実施した記録ではない。toolingに翻訳生成機能はない。

## 提示・観測の原則

reviewerは日本語話者2名を前提とし、question、raw/reference evidence、保存されたWorker公開出力、Artifact、actual Synthesizer入力、final output等の英語資料に、事前に固定した日本語訳を併記する。日本語訳を主に参照して判定できるようにし、必要時に英語原文を確認できる状態を維持する。sentence/evidence IDsとrecord構造を変えず、翻訳を実モデル入力や元Artifactへ書き戻さない。

翻訳は**表示用の追加情報変換**であり、S0〜S5のモデル実行lineageに新しいfailure stageを自動追加しない。原文と訳の対応、訳版、英語／日本語のUTF-8 SHA256、資料全体のcanonical hash、作成方式、人間の確認者、固定日時を保存する。意味の正しさはhash一致だけでは保証されない。

英語原文を**semantic source of record**とする。metadataは`semantic_reference_language = en`と`reviewer_primary_display_language = ja`に分離し、日本語訳を意味上のreferenceと呼ばない。

## Freeze・同一性・blind

- pilot/mainの各開始前に、それぞれの使用資料の翻訳版とhashを人間が固定する。同じcase/unitについて2名には同じ固定訳を提示する。translation assetはreviewer別に作らない。
- 全保存済み英語資料をauthor-only資産として固定しても、gold訳はR2、final訳はS5まで非開示。翻訳リスト全体をreviewerへ渡さず、当該stageの原文と訳だけをexportする。条件名・scores・private source pathsも非開示を維持する。
- **翻訳準備にもstageの情報境界を適用する。** R1の翻訳・確認に使えるのはquestionとraw/reference evidenceのみ。Gold answer/supporting facts、Worker output、Artifact、Synthesizer input、final answer等のfuture-stage情報を使って代名詞・entity・関係等の曖昧さを解消しない。R1原文の曖昧さは訳でも保持する。全stage資産を同じbundleに保存できることは、翻訳時の情報混用の許可ではない。準備時の閲覧範囲・確認手順を記録し、人間が点検する（hashやpacketの非開示検証だけでは翻訳準備中の情報混用は検出できない）。
- R1/R2のfact/path記述、rationale等の**人間の新規annotationは原則日本語で記入**する。英語の既存sourceは英日ペアで参照する。人間のregistryをAIで翻訳・補完しない。英語で新規作成したregistryの訳が必要なら、stage開始前に別のversioned人間確認・共有freezeを計画し、現builderの未対応欄を訳済みと扱わない。
- review途中に都合よく訳を修正しない。修正が必要なら停止、translation amendment、新版・理由・影響unit定義、両者への同じ修正版提示、影響判定の全再判定、旧訳／元票保存とする。pilotの版変更も新batchへ分離する。
- 同一の原文文字列でも文脈が異なる場合があるため、原文hashだけでなくdisplay locationとsource pointerを対応づける。固有名詞・IDの原表記保持は可能だが、訳に新しいfactや曖昧さの解消を勝手に足さない。
- reviewerごと／caseごと／開示stageごとにその場のLLM翻訳を行わない。準備手段を採用するかは別途人間が決め、方法・モデル利用の有無・確認手順を記録する。今回LLM翻訳も人間翻訳も行わない。

## 判定・ambiguity

英語原文が意味上の参照基準であり、日本語訳は判定を助ける固定表示である。否定、比較方向、数値・日付、entity alias、留保等に訳の曖昧さ／不一致があり判定へ影響する場合、`translation_issue`、`translation_unit_pointers`、`translation_visible_pairs_hash`、rationaleへ記録する。確定できないsemantic stateはunclearを残し、既存ambiguity logにも対応箇所・両言語の読み・影響field・blockerを記録できる。

原文を照合して判断できる場合も訳の問題を消さず記録する。翻訳起因の誤読をWorker/Synthesizerのdistortionと自動分類しない。解決できない場合は協議規則／amendmentへ進み、reviewerだけで訳を書き換えない。

## Tooling契約・限界

翻訳作成・確認の追跡には`translation_method`（human_manual / machine_translation / llm_assisted_translation / other）、`translation_prepared_by_or_system`、`translation_verified_by`、`verification_method`を記録する。使用system/model/version/settings等は可能な範囲で`translation_system_metadata`へ保存し、不明は不明と記録する。既存version/frozen hashと合わせてhash対象とする。作成者・確認者・Reviewerが必ず別人であることは要求せず、実際の構成と確認方法を説明する。実翻訳は今回作成しない。

`TranslationAsset`はquestion/review mode/version単位の固定資産。`TranslationPair`は英語原文、日本語訳、両text hash、author source pointers、display pointersを持つ。`Workflow.bind_translations()`は独立lock前に資産hash/versionを一度だけ結び付ける。`build_packet()`は実reviewでは固定資産を必須とし、欠訳・hash不一致・case/mode/version不一致を拒否する。

packetの`materials`は原文のまま保持し、`bilingual_display.pairs`へ当該stageの英日ペアを併記する。`material_pointer`は原文位置を示す。coordinatorはこの対を並列表示して提供する。manifestにはvisible pair hash、author linkageには全資産hashを保存する。旧kitは変更しない。JSON schemaは実在する人間の確認、翻訳の意味忠実性、filesystemアクセス制御を保証しない。

## Methodology / 論文記載

現時点の記載：**「Human Reviewでは、英語原文と事前に固定した日本語訳を併記し、日本語話者のreviewerが主に日本語訳を参照して判定する予定である。」**

実施後に実記録で確認できた場合の記載候補：**「Human Reviewでは、英語原文と事前に固定した日本語訳を併記し、日本語話者のReviewerが主に日本語訳を参照して判定した。」**

実施後は翻訳準備・確認方法、同一訳の共有、版/hash、開示順序、翻訳ambiguityと修正の有無、原文確認の扱い、翻訳を介するlimitationsも報告する。今の文書を過去形の実施主張にしない。

## Candidate revision

2026-10-06のpilot前補強でCodebook候補はv0.3.0、metadata schema/builderは3.3.0へ進める。翻訳作成/確認、Reviewer関係性、pilot修正記録、main human sign-offの透明性を補強した。実翻訳・実annotationへの影響は0。以下はv0.2.0準備時の改訂記録として保持する。

Codebook candidateをv0.1.0から**v0.2.0**へ進める。理由は日本語話者・固定訳併記の方針追加。影響は表示、translation ambiguity、pilot資料freeze、preflight、methodology記載。実pilot/main casesは未存在で、実票への変更／再判定は0。旧候補・準備監査はcommit `7888d84`とGit履歴に保持し、historical/frozen資料を更新しない。v0.2.0も未採用・未final-freeze。
