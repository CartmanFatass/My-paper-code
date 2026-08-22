param(
    [string] $RepoRoot = (Get-Location).Path,
    [string] $RuntimeHome = (Join-Path (Get-Location).Path 'runtime/hmasd-root-supervisor')
)
$ErrorActionPreference = 'Stop'
$identityPath = Join-Path $RuntimeHome 'supervisor-process.json'
if (Test-Path $identityPath) {
    $record = Get-Content -Raw $identityPath | ConvertFrom-Json
    $process = Get-Process -Id ([int]$record.pid) -ErrorAction SilentlyContinue
    if ($process) { Stop-Process -Id $process.Id -Force }
    Remove-Item -LiteralPath $identityPath -Force
}
Write-Output 'HMASD_SUPERVISOR_STOPPED_V1'
