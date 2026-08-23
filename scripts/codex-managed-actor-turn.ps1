[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [Parameter(Mandatory = $true)]
    [string]$Operator,
    [Parameter(Mandatory = $true)]
    [string]$BindingId,
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$SemanticState,
    [string]$CodexBinary,
    [string]$RuntimeHome,
    [int]$TimeoutSeconds = 1800
)

$ErrorActionPreference = "Stop"
$request = [ordered]@{ semantic_state = $SemanticState; binding_id = $BindingId; text = $Text }
& (Join-Path $PSScriptRoot 'hmasd-supervisor-request.ps1') -Command 'MANAGED_TURN' -ArgumentsJson ($request | ConvertTo-Json -Compress) -Operator $Operator -RuntimeHome $RuntimeHome -PythonExecutable $PythonExecutable -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "managed turn host request exited with code $LASTEXITCODE" }
