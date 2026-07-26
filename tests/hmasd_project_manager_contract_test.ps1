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
$workflow = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_MANAGER.md')
$operator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md')
$reviewOperator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md')
foreach ($required in @(
    'workflow_manager_persistent_task=one',
    'workflow_manager_workflow_authority=exclusive',
    'workflow_manager_git_authority=direct_for_workflow_review_and_state',
    'workflow_manager_remote_repository_authority=permanent_user_grant',
    'workflow_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_code_authority=exclusive',
    'project_manager_git_authority=direct_for_code_and_engineering_evidence',
    'project_manager_remote_repository_authority=permanent_user_grant',
    'project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_external_review_authority=post_implementation_code_index_and_repair_only',
    'external_review_operator_transport_authority=exclusive')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($required in @(
    'role_kind=sole_persistent_code_authority_task',
    'workflow_authority=none',
    'git_execution=direct_for_code_and_engineering_evidence',
    'external_review_authority=post_implementation_code_index_and_repair_only',
    'experiment_orchestration=none',
    'current_work_access=forbidden_by_default',
    'CODE_SCIENCE_INDEX.md',
    'scripts/hmasd_workspace_ticket.py',
    'Never spawn the experiment operator',
    'Workflow Manager owns continuation')) {
    if (-not $pm.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'role=workflow_manager',
    'role_kind=sole_persistent_workflow_authority_task',
    'model=gpt-5.6-sol',
    'reasoning_effort=high',
    'workflow_authority=exclusive',
    'workflow_acceptance_authority=exclusive',
    'code_acceptance_authority=none',
    'current_work_owner=exclusive',
    'code_science_alignment_audit=once_after_pm_implementation_acceptance',
    'routine_preimplementation_code_science_review=forbidden',
    'CODE_SCIENCE_INDEX.md')) {
    if (-not $workflow.Contains($required)) { throw "Workflow Manager role missing: $required" }
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
