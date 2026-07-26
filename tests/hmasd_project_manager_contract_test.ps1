[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$profiles = @{
    'HMASDCodeScout' = @('hmasd-code-scout.toml', 'hmasd-code-scout', 'gpt-5.6-luna', 'medium', 'read-only')
    'HMASDImplementer' = @('hmasd-implementer.toml', 'hmasd-implementer', 'gpt-5.6-terra', 'high', 'workspace-write')
    'HMASDVerifier' = @('hmasd-verifier.toml', 'hmasd-verifier', 'gpt-5.6-luna', 'high', 'workspace-write')
    'HMASDReviewer' = @('hmasd-reviewer.toml', 'hmasd-reviewer', 'gpt-5.6-luna', 'max', 'read-only')
    'HMASDWorkflowCostReviewer' = @('hmasd-workflow-cost-reviewer.toml', 'hmasd-workflow-cost-reviewer', 'gpt-5.6-sol', 'xhigh', 'read-only')
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
$pm = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PROJECT_MANAGER.md')
$operator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md')
$reviewOperator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md')
foreach ($required in @(
    'project_manager_project_authority=exclusive',
    'project_manager_git_authority=direct',
    'project_manager_remote_repository_authority=permanent_user_grant',
    'project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_external_review_transport=question_dispatch_and_result_intake_only',
    'external_review_operator_transport_authority=exclusive')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($required in @(
    'role_kind=sole_persistent_project_authority_task',
    'git_execution=direct',
    'external_review_transport=question_dispatch_and_result_intake_only',
    'external_review_operator=dedicated_persistent_task',
    'experiment_orchestration=registered_native_child',
    'hmasd-workflow-change-audit',
    'scripts/hmasd_workspace_ticket.py',
    'Spawn only registered native child profiles',
    'Continue automatically within an active user grant')) {
    if (-not $pm.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'role=external_review_operator',
    'scientific_authority=none',
    'git_authority=none',
    'completion_notification=required_once',
    'cross-task',
    'target model and effort explicitly passed')) {
    if (-not $reviewOperator.Contains($required)) {
        throw "External Review Operator role missing: $required"
    }
}

$ticket = Join-Path $repo 'scripts/hmasd_workspace_ticket.py'
if (-not (Test-Path -LiteralPath $ticket -PathType Leaf)) {
    throw 'Workspace-ticket harness is missing'
}
foreach ($required in @(
    'callable_agent_type=hmasd-experiment-operator',
    'role_kind=registered_nonpersistent_native_child',
    'ad hoc/default agent')) {
    if (-not $operator.Contains($required)) { throw "Experiment Operator role missing: $required" }
}

Write-Output 'HMASD_PROJECT_MANAGER_CONTRACT_OK'
