[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('controller', 'project_manager', 'experiment_monitor', 'open_divergent_exchange')]
    [string]$Role,
    [string]$RegistryPath = (Join-Path $PSScriptRoot '..\references\session-roles.json'),
    [string]$StateDb = (Join-Path $env:USERPROFILE '.codex\state_5.sqlite')
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $RegistryPath -PathType Leaf)) {
    throw "Session role registry not found: $RegistryPath"
}
$registry = Get-Content -LiteralPath $RegistryPath -Raw | ConvertFrom-Json
$entry = $registry.roles.PSObject.Properties[$Role].Value
if ($null -eq $entry) { throw "Unregistered Codex role: $Role" }
if ($Role -ne 'controller' -and [string]$entry.registration_status -ne 'ACTIVE') {
    throw "Codex role is not ACTIVE: $Role"
}
$ThreadId = [string]$entry.thread_id
if ($ThreadId -notmatch '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') {
    throw "Registered Codex role has invalid thread ID: $Role"
}
if (-not (Test-Path -LiteralPath $StateDb -PathType Leaf)) {
    throw "Codex task database not found: $StateDb"
}
if (-not (Get-Command sqlite3 -ErrorAction SilentlyContinue)) {
    throw 'sqlite3 is required to resolve live Codex task routes'
}

$query = @"
SELECT id, model, reasoning_effort, archived
FROM threads
WHERE id = '$ThreadId';
"@
$json = & sqlite3 -json $StateDb $query
if ($LASTEXITCODE -ne 0) { throw "Unable to read live Codex task metadata for $ThreadId" }

$rows = @($json | ConvertFrom-Json)
if ($rows.Count -ne 1) { throw "Expected one live Codex task for $ThreadId, found $($rows.Count)" }
$row = $rows[0]
if ([int]$row.archived -ne 0) { throw "Codex task is archived: $ThreadId" }
if ([string]::IsNullOrWhiteSpace([string]$row.model) -or
    [string]::IsNullOrWhiteSpace([string]$row.reasoning_effort)) {
    throw "Codex task has incomplete route metadata: $ThreadId"
}

[ordered]@{
    role = $Role
    hostId = 'local'
    threadId = [string]$row.id
    model = [string]$row.model
    thinking = [string]$row.reasoning_effort
} | ConvertTo-Json -Compress
