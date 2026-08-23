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
# References only: the host derives current snapshots from the two typed actor identities.
$request = [ordered]@{ semantic_state = $SemanticState; source_actor_context_id = $SourceActorContextId; target_actor_context_id = $TargetActorContextId; message_kind = 'ROOT_TO_PORTFOLIO_REVIEW'; subject_ref = $SubjectRef; payload_ref = $PayloadRef; priority = 20 }
& (Join-Path $PSScriptRoot 'hmasd-supervisor-request.ps1') -Command 'MAILBOX_ENQUEUE' -ArgumentsJson ($request | ConvertTo-Json -Compress) -Operator $Operator -RuntimeHome $RuntimeHome -PythonExecutable $PythonExecutable -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "mailbox enqueue host request exited with code $LASTEXITCODE" }
