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
    [string]$RuntimeHome,
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$request = [ordered]@{ repo_root = $RepoRoot; semantic_state = $SemanticState; actor_context_id = $ActorContextId; confirm_global_memory_disabled = $true }
& (Join-Path $PSScriptRoot 'hmasd-supervisor-request.ps1') -Command 'MANAGED_CREATE' -ArgumentsJson ($request | ConvertTo-Json -Compress) -Operator $Operator -RuntimeHome $RuntimeHome -PythonExecutable $PythonExecutable -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "managed create host request exited with code $LASTEXITCODE" }
