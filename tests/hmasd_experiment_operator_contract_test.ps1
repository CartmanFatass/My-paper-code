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
    'model=gpt-5.6-luna',
    'reasoning_effort=low',
    'progress_notifications=forbidden',
    'terminal_notification_count=exactly_one',
    'terminal_values=COMPLETE|ERROR',
    'restart policy, whose default is `forbidden`',
    'train -> evaluate -> analyze',
    'No progress, ETA, phase, heartbeat')) {
    if (-not $role.Contains($required)) { throw "Operator role missing: $required" }
}
foreach ($required in @(
    '# HMASD Controller Contract',
    'The Controller may push only `Claude`',
    'Fetching and merging `origin/aggressive` into')) {
    if (-not $agents.Contains($required)) {
        throw "Claude Controller boundary missing: $required"
    }
}
foreach ($required in @(
    'operator topology are not activated here',
    'autonomous_research_grant=REVOKED_BY_USER',
    'experiment_monitor_status=unassigned',
    'agent_assets=all_retained_active_routing_controller_registry_only')) {
    if (-not $current.Contains($required)) {
        throw "Imported operator inactive state missing: $required"
    }
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

foreach ($retained in @(
    '.agents/skills/hmasd-dispatch-task/SKILL.md',
    '.agents/skills/hmasd-experiment-monitor/SKILL.md',
    '.omp/agents/hmasd-code-scout.md',
    '.omp/agents/hmasd-implementer.md',
    '.omp/agents/hmasd-reviewer.md',
    '.omp/agents/hmasd-verifier.md')) {
    if (-not (Test-Path -LiteralPath (Join-Path $repo $retained) -PathType Leaf)) {
        throw "Retained OMP agent asset is missing: $retained"
    }
}

Write-Output 'HMASD_EXPERIMENT_OPERATOR_ASSET_CONTRACT_OK active=false'
