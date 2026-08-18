[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [Parameter(Mandatory = $true)]
    [string]$Operator,
    [Parameter(Mandatory = $true)]
    [string]$SemanticState,
    [string]$CodexBinary,
    [string]$RuntimeHome,
    [double]$DurationSeconds
)

$ErrorActionPreference = "Stop"
$arguments = @("-m", "tools.codex_supervisor", "--repo-root", $RepoRoot)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @("scheduler", "serve", "--operator", $Operator, "--semantic-state", $SemanticState)
if ($PSBoundParameters.ContainsKey("DurationSeconds")) { $arguments += @("--duration-seconds", "$DurationSeconds") }
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "mailbox serve exited with code $LASTEXITCODE" }
