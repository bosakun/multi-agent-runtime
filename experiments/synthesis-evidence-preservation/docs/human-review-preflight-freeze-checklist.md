# Human Review v3 — preflight / freeze checklist

2026-10-02。**全項目は未完了の設計checklist**。この文書の作成はreviewのfreeze・開始・承認を意味しない。人間の研究責任者と独立判定を行う2名のreviewersが、[v3 protocol](human-review-stage-analysis-plan-v3.md)と[metrics](evidence-lineage-metrics-plan.md)の採用版を確認する。旧freeze/kitは変更せず、新しいversioned manifestを将来作る。

## Scope / registry

- [ ] **Human Review開始前に人間が**Study 1 C3の本判定・IAA対象を以下のどちらか一つに固定する。現時点では未選択。
  - [ ] 全30問。
  - [ ] 旧calibration 2問を除いた28問。
- [ ] 選択理由、旧2問を既に閲覧した人、discussion/calibration実施の有無と参加者、reviewerごとの既知ケース、IAA対象に含める妥当性、除外ケースをdescriptive-onlyとして残すかを記録する。**calibrationやdiscussionで基準形成に使ったcaseは、そのreviewerのindependent IAA sampleへ無条件に戻さない**。本判定対象数と、2名とも独立性を満たすIAA対象case IDsを区別して固定する。
- [ ] Study 2 main24問×A/B/Cを維持し、smokeは本比較から除外する。既読ケースの扱いも開始前に記録する。
- [ ] reviewer2名（実装・実験作成者以外）、registryとstage担当の関係、過去の閲覧・利益相反を記録する。AIを人員に数えない。
- [ ] independent annotation（初回判定中は相談せず相手のlabelを見ない、adjudication前に各自の票をlock）を確認する。著者との人的関係とは分離し、family / academic advisor / friend等の関係・関与・既読履歴・利益相反への対応をauthor-onlyで記録する。関係なし／未開示を混同せず、個人情報をGitへ追加しない。
- [ ] R1 raw-only discoveryの資料、gold非開示、独立immutable票の保存を確認する。
- [ ] R2 gold answer/supporting facts開示時点とsystem output非開示を固定する。
- [ ] sentence / fact / support set / pathのschema、path-conditional requiredness、alternative path validity / OR–AND規則を固定する。
- [ ] R1/R2独立票を保持し、reference basis・adjudication根拠を含むregistryを**system output開示前**にfreezeする。
- [ ] freeze後の新しいpath候補はamendment/sensitivity versionへ分離する規則を固定する。

## Labels / derivation / packets

- [ ] 日本語話者2名を前提に、[英語原文＋固定日本語訳](../review_v3/BILINGUAL-REVIEW-POLICY.md)の同一表示、対応表、text/asset hashes、作成・人間確認方法をpilot/main開始前に固定する。原文・訳ともgold/finalの開示順を守る。
- [ ] semantic reference language=English、reviewer primary display language=Japaneseを分離する。R1訳の準備・確認にquestion/raw evidence以外のfuture-stage情報を使わない手順と閲覧範囲を確認し、[日本語Reviewerガイド](../review_v3/REVIEWER-GUIDE-JA.md)を共有する。
- [ ] translation ambiguityの記録、unclearの扱い、途中修正時の停止／amendment／新版／両者への同一修正版／全影響判定再実施／旧訳と票の保持を固定する。その場のreviewer別・case別LLM翻訳はしない。
- [ ] S0〜S5a/b、applicability、identity_aliasのS3=NA、unknown transition、S4 routeとmachine_payload_matchを固定する。
- [ ] observed stateとfailure eventを分離し、upstream prerequisites、重複eventの統合、cascade非二重計上を定める。
- [ ] first_observable_failure_stageは規則で導出し、不明な先行stageがある場合のundeterminedを定める。root causeと呼ばない。
- [ ] old kitがv3対応でないことを確認し、future packetの入力一覧・匿名linkage・アクセス権を固定する。旧kit・空票を上書きしない。
- [ ] progressive disclosure S1→lock→S2→lock→S3→S4→S5、final answer開示時点、条件名・scoresの非開示を定める。
- [ ] allocation-blinded where feasibleの限界（gold既知、入力構造からの条件推測）を記録する。
- [ ] source hashes、software/code commit・依存版・normalization規則、packet hashes、registry/codebook/rulesのhashesを保存する。実行commitと設計snapshotを区別する。

## Calibration / production / agreement

- [ ] [Codebook candidate](../review_v3/CODEBOOK.md)の版・stable Rule IDs・document hashes・semantic equivalence / partial / distorted / absent / unclear / missingの境界を人間が採用する。
- [ ] alternative valid pathのpre-output候補化、登録premises、外部factual premise禁止、logical composition、path-conditional requiredness、post-freeze候補分離の規則を固定する。
- [ ] [Adjudication Rules](../review_v3/ADJUDICATION-RULES.md)の優先順位、evidence pointer、独立票保存、未解決unclear、第三adjudicator利用方針を開始前に固定する。
- [ ] [Pilot Protocol](../review_v3/PILOT-PROTOCOL.md)のmain30問外selection rule、Study 2 main/smoke exclusion、result-aware selection禁止、資料出自・共有方式、batch packet freezeを固定する。今回実case・reviewerは未選定。
- [ ] pilotを2名が独立に完了し、両票lock後のdisagreement inspection / adjudication / ambiguity logを保存する。教材の存在をpilot完了と数えない。
- [ ] adopted candidate版のcritical edge-case coverage、final batch new-rule count=0、主要不一致の既存ruleによる解決可能性、未解決ambiguityの明記・blockerなしを人間が確認する。高kappaを終了条件にしない。
- [ ] old candidate版・change reason・affected fields/units・再判定影響を保持し、signed PilotClearanceとCodebook v1.0 human sign-offを新versionへ保存する。コードのstop候補から自動freezeしない。
- [ ] 対象外HotpotQA 4〜6問程度のregistry calibration選定基準とstage edge-case vignettesを固定する。
- [ ] 最終batchで新guideline ruleなし＋必須境界のcoverageという終了条件、未達時の追加batch・改訂記録を定める。
- [ ] 本判定前にcodebook v1.0をfreezeする。開始後の重大改訂はstop / amendment / new version / affected cases全再判定 / 旧票保存とする。
- [ ] independent labelsとstage locksを保存し、その後のみadjudicationする。adjudicated versionを別保存する。
- [ ] missing / unclear / not_applicableの区別、未解決判断、訂正履歴の扱いを固定する。
- [ ] IAA: raw agreement、unweighted Cohen's kappa、marginals/confusion matrix、n evaluable、applicability agreementを定める。
- [ ] registry自由候補のalignment方法、multi-label exact set / Jaccard / binary agreement、空集合、rare labels、未定義kappaを定める。
- [ ] IAAはpre-adjudication independent labelsのみ。alpha等を採る場合は補助手法・missing規則を固定する。

## Metrics / statistical plan

- [ ] primary Path End-to-End Survival等の採否、Artifact routeとAny-Routeの別、全metricの分子・分母・eligibility・evaluabilityを固定する。
- [ ] Downstream Evidential Supportのprimary eligibilityはS4にcomplete valid frozen registered pathが少なくとも1本あるquestion–arm、successはその受信pathによるfully_supportedとする。partial/none-path casesの記述値はsecondaryへ分離し、unsupported eventの前提も照合する。
- [ ] Fact / Path E2Eはseparate_recordsでS1→S2→S3→S4、identity_aliasでS3=NA / structural bypassとしてS1→S2→S4を要求する。unknownはpublication経由lineageをnon-identifiableとし、成功・失敗へ割り当てずcoverageを併記する。
- [ ] unclear / NA / missing / non-identifiable、evaluable/potentially eligible coverage、zero denominator処理を固定する。
- [ ] strict correct-only primaryとcorrect+partial sensitivity、alternative path感度の扱いを固定する。partialに恣意的重みを付けない。
- [ ] questionを主要単位としquestion-level macroをprimaryとする。Study 2 shared S0〜S3を三重計上しない。
- [ ] CIが必要か、question-clustered bootstrapのdraws/seed/CI方式、zero-denominator draws、paired arms、multiplicityを固定する。候補10,000 draws / seed 20261002は未承認設定である。
- [ ] fixed selected sample・rare failure・質問間依存・1モデル1反復のlimitationsを固定する。

## Sign-off / gate

- [ ] [透明性metadata](../review_v3/TRANSPARENCY-AND-SIGNOFF.md)のReviewerProfile、翻訳作成・確認metadata、AdjudicatorContextをauthor-onlyで保存する。実人物・実訳は今回未登録。
- [ ] pilot revisionは旧/新版・hash・理由・affected rule IDs/units・旧票保存hash・再判定範囲を残し、semantic change時に全影響unitを同じ新版で再判定するか新independent batchへ分離する。caseごとの都合のよい変更をしない。
- [ ] critical edge coverageの実施、final new-rule=0、ambiguity記録、blockerなし、final Codebook版/hash、translation policy版/hash、Reviewer構成、adjudication policy、main30/28 scope、IAA対象の10項目を人間が確認し、versioned MainReviewSignoffとPilotClearanceへ保存する。機械test成功を承認の代用にしない。

- [ ] 新版protocol・registry・codebook・packet/analysis manifestの採用者、版、日付、hashを記録する。old manifestのhashを更新しない。
- [ ] raw/local/private dataの公開可否・ライセンス・reviewerへの共有方式を人間が判断する。Gitへ自動追加しない。
- [ ] 実票とadjudicationが存在する前にreview結果を記述しない。review終了前の新確認実験を開始しない。

本checklistを満たすための将来のkit作成・人手判定・analysis実装は、今回のdocumentation作業には含まれない。
