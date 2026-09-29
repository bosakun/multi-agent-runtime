param([int]$MaxModelCalls = 0)
$ErrorActionPreference = 'Stop'
if ($MaxModelCalls -lt 0) { throw 'MaxModelCalls must be positive, or 0 to retain the existing/default budget.' }
$env:OPENAI_API_KEY = 'ollama'
$env:MODEL_BASE_URL = 'http://127.0.0.1:11434/v1/'
$env:MODEL_NAME = 'qwen3:14b'
$env:PYTHONUTF8 = '1'
if ($MaxModelCalls -gt 0) {
    $env:MAX_MODEL_CALLS = [string]$MaxModelCalls
} elseif (-not $env:MAX_MODEL_CALLS) {
    $env:MAX_MODEL_CALLS = '60'
}
if ($env:MAX_MODEL_CALLS -notmatch '^[1-9][0-9]*$') { throw 'MAX_MODEL_CALLS must be a positive integer.' }
Write-Host 'Local environment configured. No research command has been executed.'
Write-Host 'This does not configure any already-running Ollama server.'
