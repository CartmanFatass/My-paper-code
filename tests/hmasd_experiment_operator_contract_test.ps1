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
$manager = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$roleNormalized = $role -replace '\s+', ' '
$managerNormalized = $manager -replace '\s+', ' '

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
    'active Code Project Manager',
    'already-authorized scientific boundary',
    'Treat a complete, internally consistent assignment',
    'as delegated compute authority',
    'Do not request or require a separate per-run user authorization reference',
    'Monitoring is silent',
    'Do not emit commentary, progress updates, ETA messages',
    'exactly once, through your final response',
    'only at COMPLETE or ERROR',
    'Do not detach with',
    'do not repeatedly open its',
    'progress file',
    'fresh|retry|resume|restart execution mode',
    'do not choose a recovery action',
    'zero scientific iterations',
    'no scientific disposition',
    'not scientific abandonment',
    'Do not spawn',
    'agents.')) {
    if (-not $profile.Contains($required)) { throw "Operator profile missing: $required" }
}
foreach ($required in @(
    'callable_agent_type=hmasd-experiment-operator',
    'parent=code_project_manager',
    'model=gpt-5.6-luna',
    'reasoning_effort=low',
    'compute_authority=derived_from_valid_code_project_manager_assignment',
    'per_run_user_authorization_reference=not_required',
    'grant_admission_owner=code_project_manager',
    'progress_notifications=forbidden',
    'terminal_notification_count=exactly_one',
    'terminal_values=COMPLETE|ERROR',
    'cross_session_send=forbidden_native_final_return_only',
    'Code Project Manager supplies',
    'execution mode from `fresh|retry|resume|restart`',
    'unchanged authorized-boundary binding',
    'A changed source commit requires `fresh`',
    'new run identity',
    'new independent run root',
    'changed source commit + prior run root',
    'never reads a prior failed root',
    'selects among scientific outcomes',
    'costs zero scientific iterations',
    'no scientific disposition or abandonment',
    'train -> evaluate -> analyze',
    'No progress, ETA, phase, heartbeat')) {
    if (-not $roleNormalized.Contains($required)) { throw "Operator role missing: $required" }
}
if ($profile.Contains('active Workflow Design Manager') -or $role.Contains('parent=workflow_design_manager')) {
    throw 'Experiment runtime is still assigned to Workflow Design Manager'
}
foreach ($required in @(
    'native_child_authority=exact_assignment_only',
    'experiment_operator_compute_authority=derived_from_valid_code_project_manager_assignment',
    'experiment_operator_per_run_user_authorization=not_required_inside_active_grant',
    'operational_recovery_scientific_iteration_cost=zero',
    'operational_recovery_owner=code_project_manager',
    'registered native child',
    '.agents/roles/EXPERIMENT_OPERATOR.md',
    'No role reads every routed document')) {
    if (-not $agents.Contains($required)) { throw "AGENTS operator contract missing: $required" }
}
foreach ($required in @(
    'A complete exact assignment delegates compute authority to the child automatically',
    'CPM checks the active grant and remaining balance before dispatch',
    'neither CPM nor the child asks for per-run authorization')) {
    if (-not $managerNormalized.Contains($required)) { throw "CPM experiment delegation contract missing: $required" }
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
