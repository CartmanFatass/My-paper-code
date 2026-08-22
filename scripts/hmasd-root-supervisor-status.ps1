param(
    [string] $RepoRoot = (Get-Location).Path,
    [string] $RuntimeHome = (Join-Path (Get-Location).Path 'runtime/hmasd-root-supervisor'),
    [string] $PythonPath = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
)
$ErrorActionPreference = 'Stop'
$identityPath = Join-Path $RuntimeHome 'supervisor-process.json'
$running = $false; $record = $null
if (Test-Path $identityPath) {
    $record = Get-Content -Raw $identityPath | ConvertFrom-Json
    $running = [bool](Get-Process -Id ([int]$record.pid) -ErrorAction SilentlyContinue)
}
$doctor = $null
try {
    $doctorText = & $PythonPath -m tools.codex_supervisor --repo-root $RepoRoot --runtime-home $RuntimeHome doctor 2>$null
    if ($doctorText) { $doctor = ($doctorText -join "`n") | ConvertFrom-Json }
} catch { $doctor = [ordered]@{ unavailable = $true } }
$payload = [ordered]@{ schema = 'HMASD_SUPERVISOR_STATUS_V1'; running = $running; automatic_wake = $false; process = $record; doctor = $doctor }
$payload | ConvertTo-Json -Depth 5
