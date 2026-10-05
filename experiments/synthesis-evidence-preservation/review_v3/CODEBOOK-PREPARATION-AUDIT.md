# Codebook / pilot準備の保全・機械検証

2026-10-05。**design/documentation/tooling候補の監査**。人間のpilot、意味判定、実IAA、実lineage解析の結果ではない。

## Audited base snapshot

Git fetchで確認したmain snapshotは`cb1bb510b3a1ebbf4595ea5a810d8ec35740ba5c`（PR #12 merge）。
編集前のlocal snapshot `f16c0c1ddab27baf1bdd1833a7b1b9dff8bdedd2`とtree内容は一致した。
branch切替・commit・pushは今回行っていない。SHAは作業基点の歴史的識別子でlatest mainの永続表記ではない。

## 保全

編集前後で1,470既存ファイルのbyte SHA256を照合した（全628 tracked files＋以前の保全対象のunion）。
変更は今回のcurrent文書／v3 toolingの17ファイルのみ、残る1,453件は不変、欠損0。
新規のCodebook、pilot/adjudication文書、人工例、metadata utility/tests、本監査はbaseline対象外の追加。

旧v1 freeze、REVIEW / PLAN / OPERATIONS、historical Protocol、Study 1/2 results、failure/recovery、
旧builder/audit/analysis、prepared kits、blank forms、packet manifests、preparation auditは不変。
v3 suite内のhash-only testでもv1参照526件と旧2 slot各207件・manifest hashを照合した。
旧hashの更新、過去資料の削除、空票記入、旧kit再生成はしていない。

既存未追跡protocol25/26/27 Windows mock directoriesは保持し、stageしない。
raw/private/local資料のGit追加はない。本監査は全filesystem backupではない。
旧[PRESERVATION.md](PRESERVATION.md)とimplementation-audit.jsonは以前の実装snapshotとして変更しない。

## 機械的確認

- v3全suite：**100 passed**（既存72件を含む）。追加28件も人工のmetadata/label fixturesのみ。
- Ruff：全チェック合格。`git diff --check`：空白エラーなし。
- 新規・変更Markdownのローカルリンク78件に欠落なし。
- root suite：live APIを除外し、Mock provider / SQLite / UTF-8環境で**139 passed、2 skipped**。
  skipはPostgreSQL外部integrationと、このcheckoutにない旧Windows保全baseline。
- root初回は137 passed、2 failed、2 skipped。CLI inspect子プロセスの文字コード不一致で
  UnicodeDecodeErrorとstdout=Noneが発生した。PYTHONUTF8=1を親子へ伝える再実行で上記合格。
  root/coreや旧testを修正して失敗記録を消したわけではない。

テストはpytest temporary filesを利用し、synthetic packet・票・協議recordを教材／研究資料として
保存しない。Codebookの自然言語判定基準が人間に妥当であることをunit testsで証明していない。

## 候補と残る決定

Codebook候補はv0.1.0、schema/builderは3.1.0、既存analysis rule版は変更なし。
`run.py codebook-candidate`はdesign metadata/rule IDs/document hashesを表示し、
`candidate`は未決事項を含むfreeze候補を表示できる。実source/packet hashesは空、human sign-offはnull。

**DESIGN IMPLEMENTED / CODEBOOK CANDIDATE PREPARED / PILOT HUMAN REVIEW NOT STARTED /
MAIN HUMAN REVIEW NOT STARTED / 0 HUMAN LABELS / NOT FINAL-FROZEN**。

人間が決める事項は2名と既読履歴、第三adjudicator方針、pilot raw pool・選定方法・資料共有、
候補版採用、pilot packet freeze、独立票／協議／ambiguity確認、v1.0 sign-off、main30/28 scope、
IAA対象・descriptive-only、metricsとbootstrap採否・設定。今回これらを実行・決定していない。
LLM/Ollama、モデルdownload、real pilot case選定、real registry / labels / adjudication、
実研究の統計・factorial解析、real kit/票生成、Human Review開始は行っていない。
