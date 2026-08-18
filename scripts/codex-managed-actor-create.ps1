[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [Parameter(Mandatory = $true)]
    [string]$Operator,
    [Parameter(Mandatory = $true)]
    [string]$ActorContextId,
    [Parameter(Mandatory = $true)]
    [string]$SemanticState,
    [string]$CodexBinary,
    [string]$RuntimeHome
)

$ErrorActionPreference = "Stop"
$arguments = @("-m", "tools.codex_supervisor", "--repo-root", $RepoRoot)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @("managed", "--operator", $Operator, "create", "--actor-context-id", $ActorContextId, "--semantic-state", $SemanticState, "--confirm-global-memory-disabled")
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "managed create exited with code $LASTEXITCODE" }
