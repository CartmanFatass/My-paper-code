[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [Parameter(Mandatory = $true)]
    [string]$Operator,
    [Parameter(Mandatory = $true)]
    [string]$TargetActorContextId,
    [Parameter(Mandatory = $true)]
    [string]$SubjectRef,
    [Parameter(Mandatory = $true)]
    [string]$PayloadRef,
    [string]$CodexBinary,
    [string]$RuntimeHome
)

$ErrorActionPreference = "Stop"
$arguments = @("-m", "tools.codex_supervisor", "--repo-root", $RepoRoot)
if ($RuntimeHome) { $arguments += @("--runtime-home", $RuntimeHome) }
if ($CodexBinary) { $arguments += @("--codex-bin", $CodexBinary) }
$arguments += @(
    "mailbox", "send-operator",
    "--operator", $Operator,
    "--target-actor-context-id", $TargetActorContextId,
    "--subject-ref", $SubjectRef,
    "--payload-ref", $PayloadRef
)
& $PythonExecutable @arguments
if ($LASTEXITCODE -ne 0) { throw "mailbox send-canary exited with code $LASTEXITCODE" }
