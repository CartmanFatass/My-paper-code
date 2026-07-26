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
    'workflow_manager_workflow_design_authority=exclusive',
    'workflow_manager_workflow_runtime_authority=none',
    'workflow_manager_current_work_authority=none',
    'workflow_manager_git_authority=direct_for_workflow_design_surfaces',
    'workflow_manager_remote_repository_authority=permanent_user_grant',
    'workflow_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_code_authority=exclusive',
    'project_manager_runtime_authority=exclusive',
    'project_manager_current_work_authority=exclusive',
    'project_manager_git_authority=direct_for_code_runtime_evidence_and_state',
    'project_manager_remote_repository_authority=permanent_user_grant',
    'project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_external_review_dispatch_and_result_routing=exclusive',
    'project_manager_experiment_dispatch_and_result_routing=exclusive',
    'cross_task_routing=fixed_session_id_plus_fixed_model_effort',
    'cross_task_silent_model_effort_override=forbidden',
    'external_review_operator_transport_authority=exclusive')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($required in @(
    'role_kind=sole_persistent_code_and_runtime_authority_task',
    'session=019f9d04-8b21-7512-acc7-ffe02d262c82',
    'model=gpt-5.6-sol',
    'reasoning_effort=max',
    'workflow_design_authority=none',
    'current_work_owner=exclusive',
    'git_execution=direct_for_code_runtime_evidence_and_state',
    'external_review_dispatch_and_result_routing=exclusive',
    'experiment_orchestration=registered_native_child',
    'workflow_manager_target_session=019f9d2f-e0ea-7411-9fd7-386f45f76909',
    'workflow_manager_target_model=gpt-5.6-sol',
    'workflow_manager_target_effort=high',
    'external_review_operator_target_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'external_review_operator_target_model=gpt-5.6-luna',
    'external_review_operator_target_effort=high',
    'cross_task_silent_override=forbidden',
    'CODE_SCIENCE_INDEX.md',
    'scripts/hmasd_workspace_ticket.py',
    'CURRENT_WORK.md',
    'PM receives one terminal')) {
    if (-not $pm.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'role=workflow_manager',
    'role_kind=dedicated_persistent_workflow_design_authority_task',
    'session=019f9d2f-e0ea-7411-9fd7-386f45f76909',
    'model=gpt-5.6-sol',
    'reasoning_effort=high',
    'workflow_design_authority=exclusive',
    'workflow_runtime_authority=none',
    'current_work_authority=none',
    'external_review_runtime_authority=none',
    'experiment_runtime_authority=none',
    'code_acceptance_authority=none',
    'project_manager_return_session=019f9d04-8b21-7512-acc7-ffe02d262c82',
    'project_manager_return_model=gpt-5.6-sol',
    'project_manager_return_effort=max',
    'cross_task_silent_override=forbidden',
    'code_science_alignment_audit=once_after_pm_implementation_acceptance',
    'routine_preimplementation_code_science_review=forbidden',
    'CODE_SCIENCE_INDEX.md')) {
    if (-not $workflow.Contains($required)) { throw "Workflow Manager role missing: $required" }
}
if ($workflow.Contains('current_work_owner=exclusive') -or
    $workflow.Contains('external_review_dispatch_and_result_routing=exclusive') -or
    $workflow.Contains('experiment_dispatch_and_result_routing=exclusive')) {
    throw 'Workflow Manager retains project-runtime authority'
}
if ($pm.Contains('current_work_access=forbidden_by_default') -or
    $pm.Contains('experiment_orchestration=none')) {
    throw 'Project Manager is denied its runtime attention boundary'
}
foreach ($required in @(
    'role=external_review_operator',
    'scientific_authority=none',
    'git_authority=none',
    'completion_notification=required_once',
    'project_manager_return_session=019f9d04-8b21-7512-acc7-ffe02d262c82',
    'project_manager_return_model=gpt-5.6-sol',
    'project_manager_return_effort=max',
    'cross_task_silent_override=forbidden',
    'cross-task',
    'cross_task_send_requires_explicit_target_model_effort=true')) {
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
