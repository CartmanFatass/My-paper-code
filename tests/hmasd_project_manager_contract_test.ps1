[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$profiles = @{
    'HMASDCodeScout' = @('hmasd-code-scout.toml', 'hmasd-code-scout', 'gpt-5.6-luna', 'medium', 'read-only')
    'HMASDImplementer' = @('hmasd-implementer.toml', 'hmasd-implementer', 'gpt-5.6-sol', 'high', 'workspace-write')
    'HMASDVerifier' = @('hmasd-verifier.toml', 'hmasd-verifier', 'gpt-5.6-luna', 'high', 'workspace-write')
    'HMASDReviewer' = @('hmasd-reviewer.toml', 'hmasd-reviewer', 'gpt-5.6-sol', 'xhigh', 'read-only')
    'HMASDExperimentOperator' = @('hmasd-experiment-operator.toml', 'hmasd-experiment-operator', 'gpt-5.6-luna', 'low', 'workspace-write')
}
foreach ($entry in $profiles.GetEnumerator()) {
    if (-not $config.Contains("[agents.`"$($entry.Key)`"]")) {
        throw "Missing native agent registry entry: $($entry.Key)"
    }
    $spec = $entry.Value
    $path = Join-Path $repo ".codex/agents/$($spec[0])"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing profile: $path" }
    $text = Get-Content -Raw -LiteralPath $path
    foreach ($required in @(
        "name = `"$($spec[1])`"",
        "model = `"$($spec[2])`"",
        "model_reasoning_effort = `"$($spec[3])`"",
        "sandbox_mode = `"$($spec[4])`"")) {
        if (-not $text.Contains($required)) { throw "$($spec[0]) missing: $required" }
    }
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')
$pm = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PROJECT_MANAGER.md')
foreach ($required in @(
    '# HMASD Controller Contract',
    'The Controller may push only `Claude`',
    'Fetching and merging `origin/aggressive` into')) {
    if (-not $agents.Contains($required)) {
        throw "Claude Controller boundary missing: $required"
    }
}
foreach ($required in @(
    'autonomous_research_grant=REVOKED_BY_USER',
    'agent_assets=all_retained_active_routing_controller_registry_only',
    'the aggressive Project Manager, autonomous grant and experiment')) {
    if (-not $current.Contains($required)) {
        throw "Imported Project Manager inactive state missing: $required"
    }
}
foreach ($required in @(
    'role_kind=sole_persistent_project_task',
    'git_execution=direct',
    'external_review_transport=direct',
    'experiment_orchestration=registered_native_child',
    'Continue automatically within an active user grant')) {
    if (-not $pm.Contains($required)) { throw "Project Manager role missing: $required" }
}

Write-Output 'HMASD_PROJECT_MANAGER_ASSET_CONTRACT_OK active=false'
