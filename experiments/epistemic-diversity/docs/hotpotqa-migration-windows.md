# HotpotQA移行・Windows検証記録

2026-09-29。対象branch `research/epistemic-diversity`、HEAD
`95441daee16dc51821b07cd67bc28773f7185664`。ユーザー指定はHotpotQA（distractor）。

## 実装と完了した検証

新しい入口は `experiments/epistemic-diversity/hotpot.py`。
[実行案内](../ACTIVE_BENCHMARK.md)と[事前計画](protocol-3.0-hotpotqa.md)を参照。
旧 `run.py`、自作ベンチマーク、旧freeze・研究結果は履歴再現用として残し、混ぜない。

- 公開質問・原文文書と、非公開の正解・支持証拠を別モデル／別ファイルに分離。
  モデル入力には質問・許可された原文・公開worker成果物のみを渡す。
- 文書の分割は公開文書長と固定seedによる。正解・支持証拠に基づく配布はしない。
- 採点は固定commit・SHA256の公式スクリプト。回答EM/F1、支持証拠、joint指標を分離。
  旧自作タスクの完全成功判定は使わない。
- C0単独／全文、C2多様役割3worker／全文、C3中立3worker／分割文書。
  後者2条件の統合者はworker成果物だけを読む。
- 移行用16テストは合格。公式採点、正解非混入、分割、54回の偽HTTP実行、
  出力切断・不正引用での停止、ハッシュ・予算・source/backend改変検出を検証。
- 新規コードのRuff lint／整形検査とmypy（8 source files）は合格。
- 既存testsと2.5／2.6／2.7／HotpotQAテストの回帰検証は196合格・2skip。
  skipはPostgreSQLの接続URL未指定と、非配布のimplementation-local保存baseline。
  live API E2Eは明示除外した。テストのHTTP backendは偽物で、Ollamaを呼ばない。
- 実データを使ったMockは18ケース・54呼び出しすべて成功、監査違反0、
  `operational_integrity=true`。Mockは推論しないため、採点値0はモデル能力の結果ではない。
- 旧2.5／2.6／2.7のbindingと歴史的freezeを検証済み。
  保存監査では移行前972ファイルの変更・削除0。stage／commit／pushもしていない。

検証成果物（Gitignored）：

- `reports/hotpotqa-data/prepared/manifest.json`：データ・選定・公開／正解ファイルのハッシュ。
- `reports/hotpotqa-mock/results.json`：18ケース・54回のMock結果。
- `reports/hotpotqa-mock-analysis/`：公式形式の予測3条件と、Mock専用の集計。
- `reports/hotpot-migration-preservation-after.json`：972ファイルの保存確認。

## データの出所と制限

公式案内：https://hotpotqa.github.io/ 、評価コード：https://github.com/hotpotqa/hotpot 。
CMUの元配布サーバーに接続できなかったため、明示的な `download --mirror` で
HF `namlh2004/hotpotqa` commit `7e54db4656209750ff487f6fdf8e39a66dba136b` を利用。
取得済みJSONは61,065,698 bytes、7,405問、公開ミラーSHA256
`e3da074df24e8369009918aa5cdbdd254dadcde4c63f7569d36afd6f2268caa8` と一致。
元配布ファイルとのbyte一致は元サーバー未確認のため主張しない。
データはCC BY-SA 4.0、評価コードはApache-2.0。原文は変更せず射影を追加した。

初回ダウンロード記録に、データハッシュと記録ハッシュを同じキーに格納する不具合が
あった。コードでは `raw_sha256` と `sha256` を分離して修正。
初回 `download.json` と元データは上書きせず、`verify-download` で
公開ミラーハッシュ・サイズ・件数を再検証した追加記録
`download-verification.json` を保存し、準備処理はこの記録を参照した。

選定は全文AgentContextが12,000文字以下、文書タイトル重複なし等の公開条件のみ。
7,405問のうち構造条件で60問、文書長で3,152問を除外し、適格4,193問から
固定seed `20260928` とQA-IDハッシュ順位の先頭6問を選んだ。正解やモデル成功率では選ばない。
これは短い文書に限定したdevの小規模Pilotであり、全体benchmark／公式leaderboard成績ではない。
12,000文字はtoken数の保証ではなく、実入力が上限を超えれば停止する。

C2/C3は役割と文書アクセスを同時に変えるため、それぞれの単独効果は識別できない。
C0との比較は呼び出し予算も異なる。公開devの学習データ混入も否定できない。
6問の差・推測統計は探索的なものに限る。

## まだ実行していないこと／次の手順

この移行ではHotpotQAの実モデル生成、実研究freeze／binding、実Pilotを開始していない。
既存Ollama server、Qwen3、CodexのChatGPT認証は変更していない。

実Pilotを開始する際は、専用研究serverを確認してから、リポジトリrootのPowerShellで：

```powershell
$env:PYTHONUTF8 = '1'
$env:MAX_MODEL_CALLS = '60'
$env:PATH = 'C:\Users\USER\multi-agent-runtime\.venv\Scripts;C:\Users\USER\AppData\Local\Programs\Ollama;' + $env:PATH
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py bind
if ($LASTEXITCODE -ne 0) { throw 'HotpotQA binding failed' }
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py verify
if ($LASTEXITCODE -ne 0) { throw 'HotpotQA verification failed' }
# 以下だけが実モデル生成を始める。実Pilot開始を了承した場合に実行。
.\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/hotpot.py run --approve-real
```

`bind` はcurrent-source Mock・データ・host/version/model digestを確認する。
`run` は6問×C0/C2/C3の18ケース、予定54回、hard limit60、serial実行。
retry／repair／resume／自動Mainはない。既存campaignは上書きしない。
実行後、全18ケースが正常に完了した場合のみ `hotpot.py analyze` で公式集計を作る。
実生成・GPU挙動・実モデルの能力差はこの移行のMockからは確認できない。
Native OllamaにAPI keyは不要。`OPENAI_API_KEY=ollama` をCodex認証に使わない。
