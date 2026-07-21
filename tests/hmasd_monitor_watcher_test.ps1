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
$normalizedProtocol = $protocol -replace '\s+', ' '
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

foreach ($required in @(
    'inside the persistent HMASD experiment-monitor session',
    '$hmasd-dispatch-task',
    '$hmasd-experiment',
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
    'Inspect the authoritative status',
    'smallest useful registered progress',
    '`MONITOR_PROGRESS`',
    'interval is never shorter than 10 minutes',
    'Prefer the slowest active arm and recent progress',
    'Completed training counters with a nonterminal runner state',
    'keep this session''s heartbeat `ACTIVE`',
    'resolve the controller''s live route immediately',
    'delete this heartbeat with `automation_update`',
    'same `handoff_id`')) {
    if (-not $normalizedProtocol.Contains($required)) {
        throw "Experiment protocol is missing: $required"
    }
}

if ($registry.schema_version -ne 8 -or
    $registry.session_role_registry -ne '.agents/skills/hmasd-dispatch-task/references/session-roles.json' -or
    $registry.automation.kind -ne 'heartbeat' -or
    $registry.automation.name_template -ne 'hmasd-experiment-<run-id>' -or
    $registry.automation.owner -ne 'registered_monitor_session' -or
    $registry.automation.initial_cadence_minutes -ne 15 -or
    $registry.automation.minimum_cadence_minutes -ne 10 -or
    $registry.automation.target -ne 'self' -or
    $registry.automation.terminal_action -ne 'delete_after_confirmed_controller_delivery' -or
    $registry.cadence_policy.fallback_minutes -ne 15 -or
    $registry.cadence_policy.minimum_progress_fraction -ne 0.05 -or
    $registry.cadence_policy.decision -ne 'model_estimates_eta_and_expected_information_gain_from_registered_evidence' -or
    $registry.cadence_policy.guidance -ne 'increase_frequency_near_expected_completion_and_reduce_it_when_little_can_change' -or
    $registry.automation_ownership.create_retarget_and_delete -ne 'registered_monitor_session' -or
    $registry.automation_ownership.controller_role -ne 'communication_only' -or
    $registry.progress_policy.display -ne 'monitor_task_each_tick' -or
    $registry.progress_policy.controller_relay -ne 'terminal_or_actionable_error_only') {
    throw 'Monitor registry does not bind one progress heartbeat to the registered monitor task'
}
foreach ($forbidden in @('monitor_route', 'controller_return_route', 'routing_skill', 'route_policy', 'model', 'thinking')) {
    if ($null -ne $registry.PSObject.Properties[$forbidden]) {
        throw "Monitor registry duplicates dispatcher-owned session data: $forbidden"
    }
}

if (Test-Path -LiteralPath $obsoleteWatcher) {
    throw 'Obsolete single-turn watcher remains on the active path'
}

Write-Output 'HMASD_MONITOR_HEARTBEAT_CONTRACT_OK'
