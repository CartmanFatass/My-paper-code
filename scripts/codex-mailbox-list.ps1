[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [string]$CodexBinary,
    [string]$RuntimeHome,
    [string]$Target
)

$ErrorActionPreference = "Stop"
$arguments = @("-m", "tools.codex_supervisor", "--repo-root", $RepoRoot)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @("mailbox", "list")
if ($Target) { $arguments += @("--target", $Target) }
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "mailbox list exited with code $LASTEXITCODE" }
