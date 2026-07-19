[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-experiment/SKILL.md'
$protocolPath = Join-Path $repo '.agents/skills/hmasd-experiment/references/experiment-protocol.md'
$registryPath = Join-Path $repo '.agents/skills/hmasd-experiment/references/monitor-task.json'
$obsoleteWatcher = Join-Path $repo '.agents/skills/hmasd-experiment/scripts/wait_runner_status.ps1'

$skill = Get-Content -LiteralPath $skillPath -Raw
$protocol = Get-Content -LiteralPath $protocolPath -Raw
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

foreach ($required in @(
    'inside the persistent HMASD experiment-monitor session',
    'monitor session creates and owns its heartbeat',
    'session-roles.json.roles.experiment_monitor.thread_id',
    'session-roles.json.roles.controller.thread_id',
    'returned `hostId`',
    'ID or model setting from the assignment',
    'controller never creates, updates, pauses, or deletes',
    'interval is never shorter than 10',
    'Delete and verify deletion of the heartbeat only',
    'same `handoff_id`',
    'Never use sleep')) {
    if (-not $skill.Contains($required)) {
        throw "Experiment Skill is missing: $required"
    }
}

foreach ($required in @(
    'Read the status file exactly once',
    '`MONITOR_PROGRESS`',
    '`FINALIZATION_PENDING`',
    'Use the slowest active arm',
    'Relax to a longer interval only after ETA crosses',
    'end with `MONITOR_RUNNING`',
    'keep this session''s heartbeat `ACTIVE`',
    'resolve the controller''s live route immediately',
    'delete this heartbeat with `automation_update`',
    'same `handoff_id`')) {
    if (-not $protocol.Contains($required)) {
        throw "Experiment protocol is missing: $required"
    }
}

if ($registry.schema_version -ne 7 -or
    $registry.session_role_registry -ne '.agents/skills/hmasd-task-router/references/session-roles.json' -or
    $registry.automation.kind -ne 'heartbeat' -or
    $registry.automation.name_template -ne 'hmasd-experiment-<run-id>' -or
    $registry.automation.owner -ne 'registered_monitor_session' -or
    $registry.automation.initial_cadence_minutes -ne 15 -or
    $registry.automation.minimum_cadence_minutes -ne 10 -or
    $registry.automation.target -ne 'self' -or
    $registry.automation.terminal_action -ne 'delete_after_confirmed_controller_delivery' -or
    $registry.cadence_policy.fallback_minutes -ne 15 -or
    $registry.cadence_policy.minimum_progress_fraction -ne 0.05 -or
    $registry.cadence_policy.relax_hysteresis_multiplier -ne 1.25 -or
    $registry.cadence_policy.eta_buckets.Count -ne 3 -or
    $registry.cadence_policy.eta_buckets[2].interval_minutes -ne 10 -or
    $registry.automation_ownership.create_retarget_and_delete -ne 'registered_monitor_session' -or
    $registry.automation_ownership.controller_role -ne 'communication_only' -or
    $registry.progress_policy.display -ne 'monitor_task_each_tick' -or
    $registry.progress_policy.controller_relay -ne 'terminal_or_actionable_error_only') {
    throw 'Monitor registry does not bind one progress heartbeat to the registered monitor task'
}
if (@($registry.cadence_policy.eta_buckets | Where-Object {
    $_.interval_minutes -lt $registry.automation.minimum_cadence_minutes
}).Count -ne 0) {
    throw 'Monitor ETA cadence violates the 10-minute minimum'
}
foreach ($forbidden in @('monitor_route', 'controller_return_route', 'routing_skill', 'route_policy', 'model', 'thinking')) {
    if ($null -ne $registry.PSObject.Properties[$forbidden]) {
        throw "Monitor registry duplicates router-owned session data: $forbidden"
    }
}

if (Test-Path -LiteralPath $obsoleteWatcher) {
    throw 'Obsolete single-turn watcher remains on the active path'
}

Write-Output 'HMASD_MONITOR_HEARTBEAT_CONTRACT_OK'
