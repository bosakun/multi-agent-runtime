# Human Review v3 — preflight / freeze checklist

2026-10-02。**全項目は未完了の設計checklist**。この文書の作成はreviewのfreeze・開始・承認を意味しない。人間の研究責任者と2名のindependent reviewersが、[v3 protocol](human-review-stage-analysis-plan-v3.md)と[metrics](evidence-lineage-metrics-plan.md)の採用版を確認する。旧freeze/kitは変更せず、新しいversioned manifestを将来作る。

## Scope / registry

- [ ] **Human Review開始前に人間が**Study 1 C3の本判定・IAA対象を以下のどちらか一つに固定する。現時点では未選択。
  - [ ] 全30問。
  - [ ] 旧calibration 2問を除いた28問。
- [ ] 選択理由、旧2問を既に閲覧した人、discussion/calibration実施の有無と参加者、reviewerごとの既知ケース、IAA対象に含める妥当性、除外ケースをdescriptive-onlyとして残すかを記録する。**calibrationやdiscussionで基準形成に使ったcaseは、そのreviewerのindependent IAA sampleへ無条件に戻さない**。本判定対象数と、2名とも独立性を満たすIAA対象case IDsを区別して固定する。
- [ ] Study 2 main24問×A/B/Cを維持し、smokeは本比較から除外する。既読ケースの扱いも開始前に記録する。
- [ ] reviewer2名（実装・実験作成者以外）、registryとstage担当の関係、過去の閲覧・利益相反を記録する。AIを人員に数えない。
- [ ] R1 raw-only discoveryの資料、gold非開示、独立immutable票の保存を確認する。
- [ ] R2 gold answer/supporting facts開示時点とsystem output非開示を固定する。
- [ ] sentence / fact / support set / pathのschema、path-conditional requiredness、alternative path validity / OR–AND規則を固定する。
- [ ] R1/R2独立票を保持し、reference basis・adjudication根拠を含むregistryを**system output開示前**にfreezeする。
- [ ] freeze後の新しいpath候補はamendment/sensitivity versionへ分離する規則を固定する。

## Labels / derivation / packets

- [ ] S0〜S5a/b、applicability、identity_aliasのS3=NA、unknown transition、S4 routeとmachine_payload_matchを固定する。
- [ ] observed stateとfailure eventを分離し、upstream prerequisites、重複eventの統合、cascade非二重計上を定める。
- [ ] first_observable_failure_stageは規則で導出し、不明な先行stageがある場合のundeterminedを定める。root causeと呼ばない。
- [ ] old kitがv3対応でないことを確認し、future packetの入力一覧・匿名linkage・アクセス権を固定する。旧kit・空票を上書きしない。
- [ ] progressive disclosure S1→lock→S2→lock→S3→S4→S5、final answer開示時点、条件名・scoresの非開示を定める。
- [ ] allocation-blinded where feasibleの限界（gold既知、入力構造からの条件推測）を記録する。
- [ ] source hashes、software/code commit・依存版・normalization規則、packet hashes、registry/codebook/rulesのhashesを保存する。実行commitと設計snapshotを区別する。

## Calibration / production / agreement

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

- [ ] 新版protocol・registry・codebook・packet/analysis manifestの採用者、版、日付、hashを記録する。old manifestのhashを更新しない。
- [ ] raw/local/private dataの公開可否・ライセンス・reviewerへの共有方式を人間が判断する。Gitへ自動追加しない。
- [ ] 実票とadjudicationが存在する前にreview結果を記述しない。review終了前の新確認実験を開始しない。

本checklistを満たすための将来のkit作成・人手判定・analysis実装は、今回のdocumentation作業には含まれない。
