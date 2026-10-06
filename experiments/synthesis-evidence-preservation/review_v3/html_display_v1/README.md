# Static HTML display v1

Canonical JSONから再生成するread-only表示。`static-html-display-v1.0.0`。
PILOT MATERIALS PREPARED / PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED / REAL HUMAN LABELS = 0 / NOT FINAL-FROZEN。

## 入力と表示

`renderer.py`は**一つのphaseのJSONだけ**を読み、匿名case/vignetteごとにHTMLを生成する。questionを上部card、referenceを文書/sentenceごとのcard、sentence IDsをbadgeで表示する。日本語を先に、英語原文を直下に併記する。文字列はescapeして保持し、要約・言い換え・翻訳・意味判定は行わない。外部font/CDN、通信、JavaScript、判定入力UIはない。既存のballot templateを別途使う。

対応入力は、既存builderのstage限定`packet.json`、準備済みPilot A R1/R2 source bundle、準備済みPilot B S1〜S5 source array。原文・訳のhash/pointerを照合する。Pilot Aとcanonical packetには、既存schemaの固定`TranslationAsset`が必要。packetの`bilingual_display`は供給assetからの正規projectionと一致する必要がある。実Pilot Aの訳はまだ存在しないため、今回実Pilot AのHTMLは生成していない。

Pilot Bの`en`/`ja`は人工教材JSONからそのまま表示する。入力はReviewer sourceだけであり、author catalogue/answer keyは使用しない。teaching facts/pathは既存の人工教材定義であって、実Fact Registryや人間の判定結果ではない。人工訳のhashは保存するが、人間の検証・translation freezeが完了したとは扱わない。

## Phaseと公開

- R1: question/raw referenceのみ。Gold・Worker・Artifact・Synth・Finalを含むfieldがあれば拒否する。注意書きにGold等の名称は出るが、その内容は含まない。
- R2: 同じrawとgold alignment。両ReviewerのR1 lock後にだけ人間が別bundleを開示する。Worker/Synth/Finalを含まない。
- S1→S5: 元JSONが許可したstageだけ。S1にWorker public expression等があれば拒否する。各stageを別directoryに出力し、indexも同じstageのcaseだけをリンクする。
- 解答キー・unknown private fieldsはHTMLへ入れず、入力検証で拒否する。future情報をCSSやJavaScriptで隠す仕組みはない。

RendererはWorkflowを進めず、人間のlock/認可を発行しない。準備用HTMLの生成はpilot開始を意味しない。coordinatorはstage lock後にそのstageの`index.html`とcase HTMLだけを別のReviewer用folderへ共有する。全phaseの親directory、canonical private JSON、author keys、`render-manifest.json`をReviewerへ渡さない。manifestはsource path/author pointersを含むcoordinator専用。HTMLにはそれらを埋め込まない。

Shared material HTMLには判定票・`form`・R2の`own_locked_R1_registry`を表示しない。R2の各人のlocked R1は、既存手順で各人だけへ別資料として提示する。両者には共通のcase aliasと固定訳で生成した同一HTMLを共有する。各人の票やprivate source metadataの違いを共通HTMLへ混ぜない。Stage用の共通frozen Registryはそのまま表示する。

## 実行・開き方

repository rootから、同じphaseのsourceと新しいignored-local出力先を指定する。出力の上書きを拒否する。

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_display_v1/renderer.py --source <stage-limited.json> --phase S1 --destination experiments/synthesis-evidence-preservation/review_v3/local/html-display-v1/<new-batch>/S1
```

Pilot Aまたはcanonical packetでは `--translations <existing-frozen-TranslationAsset.json>` を追加する。新しい翻訳は生成されない。実dataset/raw/gold/translation/HTMLはGit管理外の`review_v3/local/`へ保存し、入力JSONと既存preparation manifestを変更しない。

Reviewerは許可されたfolderの**index.htmlをダブルクリック**し、caseを選ぶ。Edge等のbrowserで日本語・原文・IDsを読め、印刷も可能。serverやJSONの手編集は不要。両者には同じHTML bytes/hashを渡す。

## Determinism / audit

HTMLはUTF8、固定CSS、固定field順/ID、元array順で作成し、timestamp・random IDを含まない。表示を変更する際はrenderer versionを更新する。manifestはJSON byte/canonical hash、翻訳版/hash、renderer版とPython/CSS・使用helperのsource hash、phase、case/vignette ID、各HTML/index byte hash、原文/訳text hashとpointerを保存する。同じsourceと固定rendererから同一HTML bytesを再生成できる。

Pilot Bのtranslation fingerprintは表示されたEnglish/Japanese text-hashの順序付き列のcanonical SHA256。canonical packet/Pilot Aは既存assetのfrozen hashをそのまま記録する。hash一致は意味の忠実性や人間承認の証明ではない。既存JSON/freeze/selection hashを更新しない。

`render-manifest.schema.json`は新しい表示manifestのschemaで、canonical ballot/registry schemaは変更していない。

生成後のbyte/hash/pointer照合はread-only auditで行える（意味判定・研究統計は行わない）。

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_display_v1/audit.py <generated-phase-directory>
```

## Preview

`examples.py`は完全人工のA形式R1/R2およびB形式S1〜S5を新しいlocal folderに生成する。fixtureの翻訳metadataにあるTEST ONLY表記は機械確認用で、実Reviewer・訳確認者・sign-offではない。

```powershell
.\.venv\Scripts\python.exe -X utf8 experiments/synthesis-evidence-preservation/review_v3/html_display_v1/examples.py experiments/synthesis-evidence-preservation/review_v3/local/html-display-v1/synthetic-preview-001
```

今回の人工example: `../local/html-display-v1/synthetic-preview-002/R1/index.html`（ほかR2・S1〜S5も個別）。準備済み16 vignettesの表示: `../local/html-display-v1/pilot-b-preparation-002/S1/index.html` ～ `S5/index.html`。いずれも開始認可前のPREPARATION DISPLAY。`001`は開発時の表示candidateとして保持し、最新rendererの確認には`002`を使用する。
