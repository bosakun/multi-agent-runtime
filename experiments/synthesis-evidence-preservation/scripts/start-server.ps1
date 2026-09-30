$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows required.' }
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$ollamaExecutable = (Get-Command ollama -ErrorAction Stop).Source
Push-Location $repository
try {
    & .\.venv\Scripts\python.exe -X utf8 experiments/epistemic-diversity/host.py startup-check
    if ($LASTEXITCODE -ne 0) { throw 'Existing process/port or failed inspection. No process was killed.' }
    $env:OLLAMA_HOST = '127.0.0.1:11434'
    $env:OLLAMA_NUM_PARALLEL = '1'
    $env:OLLAMA_MAX_LOADED_MODELS = '1'
    $logRoot = Join-Path $repository ('experiments/synthesis-evidence-preservation/reports/server-' + [guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $logRoot
    $server = Start-Process -FilePath $ollamaExecutable -ArgumentList 'serve' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'stdout.txt') -RedirectStandardError (Join-Path $logRoot 'stderr.txt')
    [pscustomobject]@{ProcessId=$server.Id; LogRoot=$logRoot; Parallel=1; MaxLoadedModels=1; Host='127.0.0.1:11434'} | ConvertTo-Json
} finally { Pop-Location }
