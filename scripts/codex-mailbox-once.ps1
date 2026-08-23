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
    [Parameter(Mandatory = $true)]
    [string]$TargetActorContextId,
    [string]$CodexBinary,
    [string]$RuntimeHome,
    [int]$TimeoutSeconds = 1800
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot) -or [string]::IsNullOrWhiteSpace($SemanticState)) {
    throw 'RepoRoot and SemanticState compatibility values are required; they never select request authority'
}
# SemanticState is launch-time only and is intentionally absent from this request.
$request = [ordered]@{ target_actor_context_id = $TargetActorContextId }
& (Join-Path $PSScriptRoot 'hmasd-supervisor-request.ps1') -Command 'MAILBOX_DELIVER_ONCE' -ArgumentsJson ($request | ConvertTo-Json -Compress) -Operator $Operator -RuntimeHome $RuntimeHome -PythonExecutable $PythonExecutable -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "mailbox delivery host request exited with code $LASTEXITCODE" }
