$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows is required.' }
$null = Get-Command uv -ErrorAction Stop
$null = Get-Command ollama -ErrorAction Stop
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $repository
try {
    & uv run python -X utf8 experiments/epistemic-diversity/host.py startup-check
    if ($LASTEXITCODE -ne 0) {
        throw 'Startup refused. Quit existing Ollama via the tray/original terminal yourself and check port 11434. No process was killed.'
    }
    $env:OLLAMA_HOST = '127.0.0.1:11434'
    $env:OLLAMA_NUM_PARALLEL = '1'
    $env:OLLAMA_MAX_LOADED_MODELS = '1'
    Write-Host 'Starting foreground server with parallel=1, max_loaded_models=1. Keep this terminal open.'
    Write-Host 'No context, token limit, thinking, temperature or research configuration is changed.'
    & ollama serve
    if ($LASTEXITCODE -ne 0) { throw "Ollama exited with code $LASTEXITCODE; no restart attempted." }
} finally {
    Pop-Location
}
