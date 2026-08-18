[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [string]$CodexBinary,
    [string]$RuntimeHome
)

$ErrorActionPreference = "Stop"
$baseTemp = Join-Path $RepoRoot ".tmp_app_server_observer"
$arguments = @(
    "-m", "pytest",
    "tests/codex_supervisor",
    "-q",
    "--basetemp=$baseTemp"
)
Push-Location $RepoRoot
try {
    & $PythonExecutable @arguments
    if ($LASTEXITCODE -ne 0) { throw "observer tests exited with code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
