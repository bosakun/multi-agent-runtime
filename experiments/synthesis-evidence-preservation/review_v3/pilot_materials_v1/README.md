# Pilot Materials Preparation v1

PILOT MATERIALS FREEZE CANDIDATE / NOT FINAL-FROZEN.
PILOT HUMAN REVIEW NOT STARTED / MAIN HUMAN REVIEW NOT STARTED.
REAL HUMAN LABELS = 0 / REAL TRANSLATION ASSETS FROZEN = 0.

このnamespaceは資料の機械的projectionとID-only selection専用。意味判定、翻訳、Registry生成、review開始を行わない。基準はaudited base main snapshot `f03dd0ccf869b902da4285ffae904164f8799513`。

## 保存場所・アクセス分離

準備済みの実問題・gold・翻訳worklist・人工教材・author-only解答は、Git管理外の `../local/pilot-materials-v1/prepared-20261006-002/` にある。公開manifestはID・hash・状態のみ。Datasetの公開・再配布許可はここでは判断していない。`001`はlint修正前の作業版として上書きせず保存しており、pilotには使用しない。

- `pilot_a/R1/`: 匿名case、question、完全なraw context（title/sentence ID/text）。gold・モデル出力・scoreを含まない。
- `pilot_a/R2/`: 同じraw contextとbenchmark gold。両Reviewerの実R1 lock後にのみ開示する将来source bundle。今回Reviewer-specific packetやfake lockは作成しない。
- 各 `*.translation-worklist.json`: English original/hash/pointerとstage限定contextのみ。実日本語訳は未作成。R1の翻訳へR2/gold/future-stage情報を利用してはならない。
- `pilot_b/reviewer_materials/S1.source.json` ～ `S5.source.json`: 完全人工の英日教材16件。前段lock後に次段を開示するためのsourceであり、認可済みpacketではない。final outputはS5だけ。
- `author_only/`: real ID対応、除外、選定記録、eligible IDs、Pilot B解答キー。**Reviewerへ共有しない**。
- `templates/`: 空のbatch/ambiguity/revision/profile/authorization/clearance template。実人物・判定・sign-offは未登録。

S1からstage calibrationを行う際は、人工teaching premisesを人間が確認・採用してから使う。PATH練習は原文から道筋の妥当性・path内requirednessを説明する練習であり、real Registryではない。日本語は人工教材のauthoringであり、人間による翻訳検証・freezeが完了したとの意味ではない。

[日本語Reviewer Guide](../REVIEWER-GUIDE-JA.md)、[Codebook](../CODEBOOK.md)、[Pilot Protocol](../PILOT-PROTOCOL.md)を併用する。Pilot Aの実問題をguideの例へ転用していない。

## 再現と安全境界

`prepare.py prepare --output <新規ignored-local-directory> --catalogue <author-only artificial catalogue.json>` は既存local snapshotだけを使い、SHA256を照合する。download/LLM/翻訳APIはない。出力先の上書きを拒否する。saltは `human-review-pilot-v1:`、QA IDのSHA256 hex ascending順の6件。内容・gold・model performanceはrankへ渡さない。完全main30を除外するため30/28選択とは独立。

準備sourceの保存と、両Reviewer向けの独立・段階別開示は別工程。folder分離はOS sandboxではない。人間のcoordinatorはR2/gold/author keyを未開示stageに混ぜず、必要な権限で別exportすること。生成済みraw/private資料をGitへ追加しない。

`snapshot` / `verify --baseline <before.json>` は保存対象のbyte SHA256を照合する。旧freeze/hashを更新しない。

## Pilot開始までに必要な人間の決定

Reviewer2名・関係性/事前曝露、第三adjudicator有無、資料共有の許可、Pilot A日本語訳の作成方法/検証/同一版hash、Pilot B人工教材の確認、stage開示方法、packet freeze、pilot authorizationが未確定。過去に基準形成へ使った未記録caseがあれば、開始前に除外をamendmentして新版で再選定する（現candidateをsilent overwriteしない）。

その後に独立pilot → ballots lock → ambiguity/adjudication → versioned Codebook修正 → stop criterion確認 → human sign-off。main30/28・IAA対象・Codebook v1.0 freezeは未決定。本prepare完了はpilot/main開始の許可ではない。
