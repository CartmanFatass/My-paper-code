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
    [Parameter(Mandatory = $true)]
    [string]$SemanticState,
    [Parameter(Mandatory = $true)]
    [string]$SourceActorContextId,
    [string]$CodexBinary,
    [string]$RuntimeHome,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot) -or [string]::IsNullOrWhiteSpace($SemanticState)) {
    throw 'RepoRoot and SemanticState compatibility values are required; they never select request authority'
}
# References only: the launch-bound host owns repo/state and derives both actor snapshots.
$request = [ordered]@{ source_actor_context_id = $SourceActorContextId; target_actor_context_id = $TargetActorContextId; message_kind = 'ROOT_TO_PORTFOLIO_REVIEW'; subject_ref = $SubjectRef; payload_ref = $PayloadRef; priority = 20 }
& (Join-Path $PSScriptRoot 'hmasd-supervisor-request.ps1') -Command 'MAILBOX_ENQUEUE' -ArgumentsJson ($request | ConvertTo-Json -Compress) -Operator $Operator -RuntimeHome $RuntimeHome -PythonExecutable $PythonExecutable -ExpectedRepoRoot $RepoRoot -ExpectedSemanticState $SemanticState -ExpectedCodexBinary $CodexBinary -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "mailbox enqueue host request exited with code $LASTEXITCODE" }
