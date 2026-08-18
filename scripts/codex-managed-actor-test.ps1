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
$baseTemp = Join-Path $RepoRoot ".tmp_managed_actor"
$arguments = @(
    "-m", "pytest",
    "tests/codex_supervisor/test_managed_cli.py",
    "tests/codex_supervisor/test_stage3_end_to_end.py",
    "tests/codex_supervisor/test_legacy_adoption.py",
    "-q",
    "--basetemp=$baseTemp"
)
Push-Location $RepoRoot
try {
    & $PythonExecutable @arguments
    if ($LASTEXITCODE -ne 0) { throw "managed actor tests exited with code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
