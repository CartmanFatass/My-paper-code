[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$legacyProfilePath = Join-Path $repo '.omp/legacy/codex/agents/hmasd-experiment-operator.toml'
$legacyRolePath = Join-Path $repo '.omp/legacy/roles/EXPERIMENT_OPERATOR.md'
$monitorSkillPath = Join-Path $repo '.omp/skills/hmasd-experiment-monitor/SKILL.md'
$registryPath = Join-Path $repo '.omp/skills/hmasd-dispatch-task/references/session-roles.json'
foreach ($path in @($legacyProfilePath, $legacyRolePath, $monitorSkillPath, $registryPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Experiment workflow asset is missing: $path"
    }
}

$legacyProfile = Get-Content -Raw -LiteralPath $legacyProfilePath
$legacyRole = Get-Content -Raw -LiteralPath $legacyRolePath
foreach ($required in @('name = "hmasd-experiment-operator"',
    'model = "gpt-5.6-luna"','Monitoring is silent',
    'Do not repair, restart, resume, extend, or retry')) {
    if (-not $legacyProfile.Contains($required)) { throw "Legacy operator profile lost: $required" }
}
foreach ($required in @('callable_agent_type=hmasd-experiment-operator',
    'terminal_notification_count=exactly_one','train -> evaluate -> analyze')) {
    if (-not $legacyRole.Contains($required)) { throw "Legacy operator charter lost: $required" }
}

$monitor = Get-Content -Raw -LiteralPath $monitorSkillPath
$roles = Get-Content -Raw -LiteralPath $registryPath | ConvertFrom-Json
$resolverPath = Join-Path $repo '.omp/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1'
if (-not (Test-Path -LiteralPath $resolverPath -PathType Leaf) -or
    -not $monitor.Contains('`.omp/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1 -Role controller`')) {
    throw 'Active experiment Monitor terminal resolver path is broken'
}
foreach ($required in @('registered `experiment_monitor` session',
    'gpt-5.3-codex-spark','Do not modify repository files',
    'EXPERIMENT_MONITOR')) {
    if ($required -eq 'gpt-5.3-codex-spark') {
        $dispatcher = Get-Content -Raw -LiteralPath (
            Join-Path $repo '.omp/skills/hmasd-dispatch-task/SKILL.md')
        if (-not $dispatcher.Contains($required)) { throw "Active Monitor route missing: $required" }
    } elseif (-not $monitor.Contains($required)) {
        throw "Active Monitor contract missing: $required"
    }
}
if ($roles.roles.experiment_monitor.kind -ne 'persistent_codex_experiment_monitor' -or
    $roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.role_skill -ne '.omp/skills/hmasd-experiment-monitor/SKILL.md' -or
    $roles.asset_root.legacy_active) {
    throw 'Active experiment Monitor route or legacy isolation changed'
}

Write-Output 'HMASD_EXPERIMENT_MONITOR_ASSET_CONTRACT_OK legacy_retained=true active=persistent_rebuild_required'
