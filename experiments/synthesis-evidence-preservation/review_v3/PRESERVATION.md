# v3 tooling実装の保全監査

2026-10-02。**実装・人工テストの監査**であり、Human Reviewや実研究の追加解析ではありません。

## Audited base snapshot

remote mainの取得済みsnapshotは`d998ed6b76714f56a9a5c3d0728a0c649cdca5f0`（PR #11 merge）。
作業branchは`research/epistemic-diversity`、local HEAD snapshotは
`a9280fd9312d814fbae3aa3cf99d7bb4f33a10b9`。この二つのtree内容は一致していました。
SHAは監査時のbase記録であり、永続的な「latest HEAD」という研究事実ではありません。

## 保全対象と結果

- 作業前に既存1,439ファイルのbyte SHA256を記録し、作業後に全件照合：**変更0、欠落0**。
  全597 tracked files、v1 sealの依存、旧review kit・blank forms・manifest等を含む指定対象です。
- `freezes/v1.json`のcode/source hash参照は、新suite内の読み取り専用testで原hashに一致しました。
- 旧prepared kit 2 slotは、preparation auditのmanifest hash、各manifestに列挙された
  207ファイル×2のhashと一致しました。旧criteria / REVIEW / 旧空票もそのままです。
- Protocol 3.1 / 3.2、PLAN / REVIEW / OPERATIONS、旧audit / analysis / builder、過去の結果・
  failure / recovery文書、Runtime coreを編集していません。historical hashを更新していません。
- 既存未追跡のprotocol25/26/27 Windows mock directoriesを削除・上書き・stageしていません。
  これらは上記1,439件のhash対象外であり、全ローカルfilesystemの完全backupとは主張しません。
- 新規追加は`review_v3/`だけ。既存non-frozen文書にも変更なし。stage / commit / pushなし。

baseline自体は`local/preservation-before.json`という**Git ignored local metadata**です。
raw/private資料をGitへ追加していません。旧prepared kitをv3 kitへ変換・再生成していません。
現在の公開監査要約は[implementation-audit.json](implementation-audit.json)を参照してください。

## 機械的確認

新namespace専用suite：**72 passed / 0 failed / 0 skipped**、0.68秒。
既存Ruffのcheckも合格しました。root全体の回帰suite合格を意味しません。
synthetic unit testsはregistry/OR–AND、順序とprogressive locks、schema/blank fields、
failure gating/重複除去、complete-path分母、alias/unknown E2E、coverage、共有stages、
question macro、bootstrap blocks、IAA、source projection、hash保存を確認しました。

packet、registry、label、adjudication等のテスト入力は全て明示的にinvented fixtureです。
生成先はpytest temporary directoryで、実review資料として保存・公開していません。
保全testだけは実既存資産のhashを読み、意味内容の判定・採点・再解析はしません。

候補manifestの`candidate` commandは今回のコードhashを返せますが、実source/packetの
hashは空です。real v3 packet、担当者、registry freeze、codebook freeze、human labels、
adjudication、実lineage metric / IAA / CIは存在しません。
状態は**DESIGN IMPLEMENTED / HUMAN REVIEW NOT STARTED / 0 HUMAN LABELS / NOT FINAL-FROZEN**です。
コード25ファイル・仕様4文書のhashと未決事項10項目を含む候補を
`local/freeze-candidate.json`へGit ignored metadataとして保存しました。human sign-offはnullです。
