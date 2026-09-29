# Native Windows / NVIDIA / Ollama host preparation

対象は Windows 10/11・native PowerShell 5.1+・NVIDIA・native Ollama・Python 3.12+。
WSL、Docker、管理者権限を標準経路にしない。このガイドは **host preparationのみ**。
Protocol 2.1–2.4 の campaign は consumed のまま保持し、retry/resume は行わない。
本変更では実モデル生成も研究実験も実行していない。

## 境界と準備

```text
Scientific condition (C2/C3; unchanged)
        ↓
Execution profile (local_ollama; unchanged)
        ↓
Host environment (macOS Apple Silicon | Windows NVIDIA)
```

`host.py` / `host_support/` は freeze 対象外の追加層。既存の
`operational_diagnostics.budget_experiment.preflight` を読み取り専用で再利用し、
その応答から model metadata を取得する。既存 `app/` / scientific source は未変更。
host CLI に研究実行のサブコマンドは存在しない。

新規Windows checkoutではLFを維持する（既存checkoutの未commit変更は捨てない）：

```powershell
git -c core.autocrlf=false clone --branch research/epistemic-diversity https://github.com/bosakun/multi-agent-runtime.git
cd multi-agent-runtime
git status
git log -1 --oneline
uv sync --frozen --group dev
. .\scripts\windows\env-research.ps1
```

Windows supportを含むcommitをcheckoutし、`scripts/windows/preflight.ps1` と
`experiments/epistemic-diversity/host.py` が存在することを確認する。
別OSの `.venv` は移さず、Windowsで `uv sync` する。
Pythonは `-X utf8` で起動する。`.gitattributes` はLF保持用であり、
既存ファイルをrenormalizeしない。freezeが一致しないcheckoutで実験しない。
スクリプト実行が組織ポリシーに拒否されたら管理者へ確認し、勝手にpolicyを緩めない。

環境スクリプトは `OPENAI_API_KEY=ollama`、ローカルendpoint、`qwen3:14b`、
`PYTHONUTF8=1` を設定する。既存 `MAX_MODEL_CALLS` は保持し、未指定なら60。
明示変更には `-MaxModelCalls 60` を使えるが、budget設定は実行許可ではない。
timeout/token limit/temperature/thinking/contexts/retryを設定・変更しない。

## Step 1 — GPU

```powershell
nvidia-smi
```

GPU名、VRAM、driverを確認。fingerprintは `nvidia-smi -q -x` で複数GPUを列挙する。
CUDA欄は **driver-supported CUDA** であり、インストール済みCUDA runtimeとは扱わない。
後者は安全に観測できない場合 `null`。GPUが12GBでも14Bモデルの完全offloadを仮定しない。

## Step 2 — Ollama CLI / installed model

```powershell
ollama --version
ollama list
```

`qwen3:14b` が必要。未導入ならここで停止し、別途モデル導入を判断する。
本スクリプトはpull/更新しない。インストール時にbackground serverが起動している場合がある。
Windows native動作と標準APIポートは [Ollama Windows documentation](https://docs.ollama.com/windows)
を参照。

## Step 3 — research用サーバー起動（Terminal A）

```powershell
.\scripts\windows\start-ollama-research.ps1
```

起動前にWindows process queryとIPv4/IPv6 loopbackのport 11434を検査する。
既存Ollama processまたはport使用を検出すると **existing Ollama server detected** と停止。
ユーザーがtrayメニューのQuitまたは元terminalの操作で終了し、portの所有者を確認する。
スクリプトはkill/restartしない。検査不能もfail-closed。

新しいforeground `ollama serve` は次の環境を実際に継承する：

```text
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

Terminal Aを開いたままにする。既存processへ後から環境変数を設定しても適用されない。
このhost設定は既存Runtimeのworker/model concurrency 1/1を変更するものではない。
port検査とbindの間の競合は完全には防げず、serveのbind失敗時も自動retryしない。
既存サーバーの環境値をAPIから検証できるとは主張しない。

## Step 4 — generationなしのAPI確認（Terminal B）

```powershell
. .\scripts\windows\env-research.ps1
Invoke-RestMethod http://127.0.0.1:11434/api/version
Invoke-RestMethod http://127.0.0.1:11434/v1/models
```

host preflight が許可するHTTPは GET `/api/version`, `/api/tags`, `/api/ps`, `/v1/models`
とPOST `/api/show`（model metadata）のみ。`/generate` / `/chat` / `/chat/completions` は使わない。
proxy環境変数とredirectを無効にし、http localhost/127.0.0.1:11434以外を拒否する。
endpoint/modelは `MODEL_BASE_URL` / `MODEL_NAME`（未設定なら上記default）を検査し、
Python CLIで明示した `--endpoint` / `--model` がある場合のみそれを優先する。

## Step 5 — preflight（fingerprint保存を含む）

```powershell
.\scripts\windows\preflight.ps1
```

失敗時はnonzero終了し、観測できた値とfailed checksも新しいreportへ保存する。
CPU/RAM等の取得不能はunknown/null + warning、GPU/VRAM/model/digest/API/Git不備はfail。
`qwen3:14b` のexact nameと64桁digestを検証する。
Windowsへ移したモデルが元と同じ内容か確認する場合、信頼できる既存model metadataの
**full digest** を指定する（short IDや想像した値は使わない）：

```powershell
# $expectedDigest に、確認済みの64桁SHA256を代入した場合のみ
.\scripts\windows\preflight.ps1 -ExpectedDigest $expectedDigest
```

期待digest未指定では「現在インストール済みモデルの同一性を記録」するだけで、
Mac上のモデルとの一致までは保証しない。resident modelのdigest差はfail。
CLIとAPIのモデル一覧が一致していても、freeze/bindingの代用にはならない。

## Step 6 — fingerprint保存先・再取得

Step 5が表示した `reports/windows-host/preflight-<UTC>-<UUID>.json` が保存先。
OS/build/architecture、CPU、物理RAM、全GPU、Ollama/model/residency、Python/uv/Gitを含む。
任意の追加観測も新しいファイルだけに保存する：

```powershell
uv run python -X utf8 experiments/epistemic-diversity/host.py fingerprint
```

`--output reports/windows-host/windows-first.json` の指定も可能。ただし既存pathは拒否。
campaign/freezes/benchmark内への出力は禁止。UTF-8で閉じた一時ファイルをfsync後、
no-clobber hard linkで公開する。NTFS推奨、hard link非対応FSやsharing violationは停止し、
非atomicなfallbackや上書きはしない。reportは `.gitignore` 対象で機器情報の意図しない公開を防ぐ。

## Step 7 — optional diagnosticのみ（自動実行しない）

モデルが未ロードならresidencyは `not_loaded` であり、preflightはロードしない。
人間が別途非研究diagnosticを行うと決めた場合のみ：

```powershell
ollama run qwen3:14b
```

これは実モデル生成を起こし得る。研究task/goldを入力しない。今回の作業では未実行。
context/temperature/thinking等を `/set` で変更しない。終了は `/bye`。

## Step 8 — 別terminalでGPU residency

```powershell
ollama ps
.\scripts\windows\inspect-ollama.ps1
```

API `size`, `size_vram`, `context_length` とCLI `PROCESSOR` を保存する。
CLIのGPU/CPU%はoffload表示であり、GPU compute utilizationではない。
API byte ratioをcompute%に変換しない。APIにresidencyがなくてもCLIにあれば補助情報として記録。
partial/CPU/not_loaded/unknownはwarning、model/context変更は一切しない。
model metadataの最大contextとロード中contextは別field。
[API /api/ps](https://docs.ollama.com/api/ps) と
[Ollama FAQ: GPU residency / environment](https://docs.ollama.com/faq) が基準。

## Step 9 — 非研究Runtime smoke（Mockのみ）

```powershell
uv run python -X utf8 experiments/epistemic-diversity/host.py smoke
uv run python -X utf8 -m pytest -q tests/windows
```

smokeはproviderをコードでMockに固定し、環境のreal providerを無視する。
既存investigation demoを一時SQLiteで実行し、Runtime close後にDB rename/removeを検査する。
6 mock calls、0 real generation calls。研究benchmark、campaign、budget DBは使わない。
host reportのatomic保存も同時に実行される。

## Step 10 — 停止

ここで終了。formal Pilot、Protocol 2.4 retry/resume、Protocol 3.0、Benchmark 3.0.0、
C2/C3実験、main/full、別model実験を実行しない。
preflight成功はWindows実機上での将来の実験成功やEvidence ID contractの改善を意味しない。

## 検証と残る制約

この変更はmacOS上のWindows mocks / fake HTTPで検証した。native Windows、PowerShell実行、
4070 Ti実機性能はまだ検証していない。driver/Ollamaバージョン・digestの差、12GB VRAM、
KV cache、partial offload、GPU power state、thermals、Windows Defenderやindexerによる
file sharing lockに注意。最新tagを同じモデル内容と仮定しない。
watcher/editorをcampaignのJSON/SQLiteに開いたままにしない。非ローカル共有driveやFAT系FSは非推奨。
Qwenのschema-validな未知Evidence IDを受理する処理は追加していない。

詳細なコード監査・保全結果は [Windows compatibility audit](windows-compatibility-audit.md)。
