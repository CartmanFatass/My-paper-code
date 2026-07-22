[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$agentPath = Join-Path $repo '.omp/agents/hmasd-experiment-monitor.md'
$protocolPath = Join-Path $repo '.omp/agents/references/hmasd-experiment-monitor-protocol.md'
$schemaPath = Join-Path $repo '.omp/agents/references/hmasd-monitor-manifest.schema.json'
foreach ($path in @($agentPath, $protocolPath, $schemaPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing Monitor contract: $path" }
}
$agent = Get-Content -LiteralPath $agentPath -Raw
$protocol = Get-Content -LiteralPath $protocolPath -Raw
$schema = Get-Content -LiteralPath $schemaPath -Raw | ConvertFrom-Json
foreach ($required in @(
    'name: hmasd-experiment-monitor',
    'model: openai-codex/gpt-5.6-luna',
    'thinking-level: medium',
    'spawns: []',
    'monitor-<run-id>',
    'authoritative status',
    'bounded',
    'idempotency',
    'never launch',
    'never restart',
    'never repair',
    'never extend',
    'never scientifically interpret')) {
    if (($agent + "`n" + $protocol) -notmatch [regex]::Escape($required)) { throw "Monitor contract missing: $required" }
}
foreach ($forbidden in @('session-roles.json', 'resolve_task_route.ps1', 'automation_update', 'controller_return_route')) {
    if (($agent + "`n" + $protocol).Contains($forbidden)) { throw "Persistent Monitor mechanism remains: $forbidden" }
}
if ($schema.'$schema' -ne 'https://json-schema.org/draft/2020-12/schema' -or $schema.type -ne 'object') {
    throw 'Monitor manifest must be JSON Schema draft 2020-12 object'
}
$requiredProperties = @('schema_version', 'run_id', 'hub_process_name', 'run_root', 'status_path', 'progress_sources', 'deadline', 'monitor_task_name', 'terminal_idempotency_key_fields')
foreach ($name in $requiredProperties) {
    if ($schema.required -notcontains $name -or $null -eq $schema.properties.PSObject.Properties[$name]) {
        throw "Monitor manifest schema missing required property: $name"
    }
}
if ($schema.properties.monitor_task_name.pattern -ne '^monitor-.+$') { throw 'Monitor task name pattern mismatch' }
if (@($schema.properties.terminal_idempotency_key_fields.const) -join ',' -ne 'run_id,terminal_state,status_updated_at') {
    throw 'Monitor idempotency fields mismatch'
}
Write-Output 'HMASD_MONITOR_TASK_CONTRACT_OK'
