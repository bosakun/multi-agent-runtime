$ErrorActionPreference = 'Stop'
$null = Get-Command uv -ErrorAction Stop
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $repository
try {
    & uv run python -X utf8 experiments/epistemic-diversity/host.py inspect
    if ($LASTEXITCODE -ne 0) { throw 'Ollama inspection failed; inspect the saved report.' }
} finally {
    Pop-Location
}
