[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')]
    [string]$ThreadId,
    [string]$StateDb = (Join-Path $env:USERPROFILE '.codex\state_5.sqlite')
)

$ErrorActionPreference = 'Stop'
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
    hostId = 'local'
    threadId = [string]$row.id
    model = [string]$row.model
    thinking = [string]$row.reasoning_effort
} | ConvertTo-Json -Compress
