param([string]$ExpectedDigest = '', [string]$OutputPath = '')
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows is required.' }
$null = Get-Command uv -ErrorAction Stop
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$arguments = @('run', 'python', '-X', 'utf8', 'experiments/epistemic-diversity/host.py', 'preflight')
if ($ExpectedDigest) { $arguments += @('--expected-digest', $ExpectedDigest) }
if ($OutputPath) { $arguments += @('--output', $OutputPath) }
Push-Location $repository
try {
    & uv @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; read the saved host report. Do not start a research run.' }
} finally {
    Pop-Location
}
