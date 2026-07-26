[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$configPath = Join-Path $repo '.codex/config.toml'
$profilePath = Join-Path $repo '.codex/agents/hmasd-experiment-operator.toml'
$rolePath = Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md'
$config = Get-Content -Raw -LiteralPath $configPath
$profile = Get-Content -Raw -LiteralPath $profilePath
$role = Get-Content -Raw -LiteralPath $rolePath
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')

if (-not $config.Contains('[agents."HMASDExperimentOperator"]') -or
    -not $config.Contains('config_file = "./agents/hmasd-experiment-operator.toml"')) {
    throw 'Experiment operator is not registered as a fixed native child'
}
foreach ($required in @(
    'name = "hmasd-experiment-operator"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'sandbox_mode = "workspace-write"',
    'approval_policy = "never"',
    'active Project Manager',
    'exactly one already-authorized run',
    'Monitoring is silent',
    'Do not emit commentary, progress updates, ETA messages',
    'exactly once, through your final response',
    'only at COMPLETE or ERROR',
    'Do not detach with',
    'do not repeatedly open its',
    'progress file',
    'Do not repair, restart, resume, extend, or retry',
    'Do not spawn',
    'agents.')) {
    if (-not $profile.Contains($required)) { throw "Operator profile missing: $required" }
}
foreach ($required in @(
    'callable_agent_type=hmasd-experiment-operator',
    'parent=project_manager',
    'model=gpt-5.6-luna',
    'reasoning_effort=low',
    'progress_notifications=forbidden',
    'terminal_notification_count=exactly_one',
    'terminal_values=COMPLETE|ERROR',
    'cross_session_send=forbidden_native_final_return_only',
    'Project Manager supplies',
    'restart policy, whose default is `forbidden`',
    'train -> evaluate -> analyze',
    'No progress, ETA, phase, heartbeat')) {
    if (-not $role.Contains($required)) { throw "Operator role missing: $required" }
}
if ($profile.Contains('active Workflow Design Manager') -or $role.Contains('parent=workflow_design_manager')) {
    throw 'Experiment runtime is still assigned to Workflow Design Manager'
}
foreach ($required in @(
    'native_child_authority=exact_assignment_only',
    'registered native child',
    '.agents/roles/EXPERIMENT_OPERATOR.md',
    'No role reads every routed document')) {
    if (-not $agents.Contains($required)) { throw "AGENTS operator contract missing: $required" }
}
foreach ($required in @(
    'hmasd-experiment-operator',
    '`gpt-5.6-luna` with `low` reasoning',
    'returns exactly one `COMPLETE` or',
    'No Controller, persistent project Monitor, dispatcher')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK operator state missing: $required" }
}

$catalogMatch = [regex]::Match($config, '(?m)^model_catalog_json\s*=\s*"([^"]+)"\s*$')
if (-not $catalogMatch.Success) { throw 'Missing model_catalog_json setting' }
$catalogPath = $catalogMatch.Groups[1].Value -replace '\\\\', '\'
if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
    throw "Configured model catalog is unavailable: $catalogPath"
}
$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
$luna = @($catalog.models | Where-Object { $_.slug -eq 'gpt-5.6-luna' })
if ($luna.Count -ne 1) { throw 'Configured catalog does not expose exactly one gpt-5.6-luna model' }
$efforts = @($luna[0].supported_reasoning_levels | ForEach-Object { $_.effort })
if ($efforts -notcontains 'low') { throw 'Configured gpt-5.6-luna model does not support low effort' }

foreach ($retired in @(
    '.agents/roles/CONTROLLER.md',
    '.agents/roles/EXPERIMENT_MONITOR.md',
    '.agents/skills/hmasd-dispatch-task/SKILL.md',
    '.agents/skills/hmasd-experiment-monitor/SKILL.md')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Retired execution surface remains: $retired"
    }
}

Write-Output 'HMASD_EXPERIMENT_OPERATOR_CONTRACT_OK'
