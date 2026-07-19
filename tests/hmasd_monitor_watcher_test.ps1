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
    'registered heartbeat automation',
    'Verify that the automation is `ACTIVE`')) {
    if (-not $skill.Contains($required)) {
        throw "Experiment Skill is missing: $required"
    }
}

foreach ($required in @(
    '`runner_status.txt` exactly once',
    '`MONITOR_PROGRESS`',
    'ETA-based heartbeat cadence',
    'Relax to a longer interval only when ETA exceeds',
    'monitor task exclusively owns ETA',
    'ends with `MONITOR_RUNNING`',
    'automation to `PAUSED`',
    'is confirmed does it resolve',
    'live background waiter.')) {
    if (-not $protocol.Contains($required)) {
        throw "Experiment protocol is missing: $required"
    }
}

if ($registry.schema_version -ne 3 -or
    $registry.automation.id -ne 'hmasd-r35-single-thread-monitor' -or
    $registry.automation.kind -ne 'heartbeat' -or
    $registry.automation.initial_cadence_minutes -ne 15 -or
    $registry.automation.target_thread_id -ne $registry.monitor_route.thread_id -or
    $registry.cadence_policy.fallback_minutes -ne 15 -or
    $registry.cadence_policy.minimum_progress_fraction -ne 0.05 -or
    $registry.cadence_policy.relax_hysteresis_multiplier -ne 1.25 -or
    $registry.cadence_policy.eta_buckets.Count -ne 4 -or
    $registry.cadence_policy.eta_buckets[3].interval_minutes -ne 5 -or
    $registry.automation_ownership.initial_binding -ne 'active_controller' -or
    $registry.automation_ownership.runtime_cadence_and_terminal_pause -ne 'registered_monitor_task' -or
    $registry.progress_policy.display -ne 'monitor_task_each_tick' -or
    $registry.progress_policy.controller_relay -ne 'terminal_or_actionable_error_only') {
    throw 'Monitor registry does not bind one progress heartbeat to the registered monitor task'
}

if (Test-Path -LiteralPath $obsoleteWatcher) {
    throw 'Obsolete single-turn watcher remains on the active path'
}

Write-Output 'HMASD_MONITOR_HEARTBEAT_CONTRACT_OK'
