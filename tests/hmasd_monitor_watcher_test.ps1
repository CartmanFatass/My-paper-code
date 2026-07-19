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
    'inside the persistent HMASD experiment-monitor task',
    'pause and verify the heartbeat',
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
    'automation to `PAUSED`',
    'resolve the controller''s live route immediately',
    'send exactly one payload')) {
    if (-not $protocol.Contains($required)) {
        throw "Experiment protocol is missing: $required"
    }
}

if ($registry.schema_version -ne 5 -or
    $registry.automation.id -ne 'hmasd-r35-single-thread-monitor' -or
    $registry.automation.kind -ne 'heartbeat' -or
    $registry.automation.initial_cadence_minutes -ne 15 -or
    $registry.automation.target_thread_id -ne $registry.monitor_route.thread_id -or
    $registry.cadence_policy.fallback_minutes -ne 15 -or
    $registry.cadence_policy.minimum_progress_fraction -ne 0.05 -or
    $registry.cadence_policy.relax_hysteresis_multiplier -ne 1.25 -or
    $registry.cadence_policy.eta_buckets.Count -ne 4 -or
    $registry.cadence_policy.eta_buckets[3].interval_minutes -ne 5 -or
    $registry.automation_ownership.assignment_activation_cadence_and_terminal_pause -ne 'registered_monitor_task' -or
    $registry.automation_ownership.controller_role -ne 'communication_only' -or
    $registry.controller_return_route.route_policy -ne 'resolve_live_immediately_before_each_send' -or
    $registry.progress_policy.display -ne 'monitor_task_each_tick' -or
    $registry.progress_policy.controller_relay -ne 'terminal_or_actionable_error_only') {
    throw 'Monitor registry does not bind one progress heartbeat to the registered monitor task'
}
foreach ($route in @($registry.monitor_route, $registry.controller_return_route)) {
    if ($null -ne $route.PSObject.Properties['model'] -or
        $null -ne $route.PSObject.Properties['thinking']) {
        throw 'Monitor registry must not mirror task model or thinking'
    }
}

if (Test-Path -LiteralPath $obsoleteWatcher) {
    throw 'Obsolete single-turn watcher remains on the active path'
}

Write-Output 'HMASD_MONITOR_HEARTBEAT_CONTRACT_OK'
