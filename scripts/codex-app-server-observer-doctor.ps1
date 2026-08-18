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
$arguments = @(
    "-m", "tools.codex_supervisor",
    "--repo-root", $RepoRoot
)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += "doctor"
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "doctor exited with code $LASTEXITCODE" }
