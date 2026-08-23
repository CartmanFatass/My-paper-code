[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)]
    [string]$PythonExecutable,
    [string]$CodexBinary,
    [string]$RuntimeHome,
    [string]$Target,
    [string]$Operator = 'mailbox-list',
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$request = [ordered]@{}
if ($Target) { $request.target_actor_context_id = $Target }
& (Join-Path $PSScriptRoot 'hmasd-supervisor-request.ps1') -Command 'MAILBOX_LIST' -ArgumentsJson ($request | ConvertTo-Json -Compress) -Operator $Operator -RuntimeHome $RuntimeHome -PythonExecutable $PythonExecutable -TimeoutSeconds $TimeoutSeconds
if ($LASTEXITCODE -ne 0) { throw "mailbox list host request exited with code $LASTEXITCODE" }
