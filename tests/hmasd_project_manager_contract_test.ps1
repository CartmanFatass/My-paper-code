[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$profiles = @{
    'HMASDCodeScout' = @('hmasd-code-scout.toml', 'hmasd-code-scout', 'gpt-5.6-luna', 'medium', 'read-only')
    'HMASDImplementer' = @('hmasd-implementer.toml', 'hmasd-implementer', 'gpt-5.6-sol', 'high', 'workspace-write')
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
$workflow = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$operator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md')
$reviewOperator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md')
$reviewOperatorNormalized = $reviewOperator -replace '\s+', ' '
foreach ($required in @(
    'workflow_design_manager_persistent_task=one',
    'workflow_design_manager_workflow_design_authority=exclusive',
    'workflow_design_manager_workflow_runtime_authority=none',
    'workflow_design_manager_current_work_authority=none',
    'workflow_design_manager_git_authority=direct_for_workflow_design_surfaces',
    'workflow_design_manager_remote_repository_authority=permanent_user_grant',
    'workflow_design_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_code_authority=exclusive',
    'project_manager_runtime_authority=exclusive',
    'project_manager_current_work_authority=exclusive',
    'project_manager_git_authority=direct_for_code_runtime_evidence_and_state',
    'project_manager_remote_repository_authority=permanent_user_grant',
    'project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_external_review_dispatch_and_result_routing=exclusive',
    'project_manager_experiment_dispatch_and_result_routing=exclusive',
    'hmasd_python_interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    'cross_task_routing=probe_confirmed_session_plus_conversation_local_cache',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_model_thinking_override=omitted',
    'external_review_operator_transport_authority=exclusive')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($required in @(
    'role_kind=sole_persistent_code_and_runtime_authority_task',
    'workflow_design_authority=none',
    'current_work_owner=exclusive',
    'git_execution=direct_for_code_runtime_evidence_and_state',
    'external_review_dispatch_and_result_routing=exclusive',
    'experiment_orchestration=registered_native_child',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=probe_confirmed_live_role_session',
    'cross_task_route_cache=conversation_local_only',
    'cross_task_model_thinking_override=omitted',
    'CODE_SCIENCE_INDEX.md',
    'scripts/hmasd_workspace_ticket.py',
    'CURRENT_WORK.md',
    'PM receives one terminal')) {
    if (-not $pm.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($retired in @(
    'project_manager_round_metrics_skill=',
    'PM complete-workflow metrics:')) {
    if ($agents.Contains($retired)) { throw "AGENTS retains PM metrics workflow binding: $retired" }
}
foreach ($retired in @(
    'pm_round_metrics_skill=',
    'pm_round_metrics_sample=',
    'pm_round_metrics_ledger=',
    '$hmasd-pm-round-metrics',
    'CONFIGURATION_CHANGED',
    'logs/pm-model-performance/ledger.jsonl')) {
    if ($pm.Contains($retired)) { throw "Project Manager role retains metrics workflow binding: $retired" }
}
foreach ($required in @(
    'role=workflow_design_manager',
    'role_kind=dedicated_persistent_workflow_design_authority_task',
    'workflow_design_authority=exclusive',
    'workflow_runtime_authority=none',
    'current_work_authority=none',
    'external_review_runtime_authority=none',
    'experiment_runtime_authority=none',
    'code_acceptance_authority=none',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=probe_confirmed_live_role_session',
    'cross_task_route_cache=conversation_local_only',
    'cross_task_model_thinking_override=omitted',
    'code_science_alignment_audit=once_after_pm_implementation_acceptance',
    'routine_preimplementation_code_science_review=forbidden',
    'CODE_SCIENCE_INDEX.md')) {
    if (-not $workflow.Contains($required)) { throw "Workflow Design Manager role missing: $required" }
}
if ($workflow.Contains('current_work_owner=exclusive') -or
    $workflow.Contains('external_review_dispatch_and_result_routing=exclusive') -or
    $workflow.Contains('experiment_dispatch_and_result_routing=exclusive')) {
    throw 'Workflow Design Manager retains project-runtime authority'
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
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=probe_confirmed_live_role_session',
    'cross_task_route_cache=conversation_local_only',
    'cross_task_model_thinking_override=omitted',
    'cross-task',
    'model and thinking omitted')) {
    if (-not $reviewOperatorNormalized.Contains($required)) {
        throw "External Review Operator role missing: $required"
    }
}

foreach ($text in @($pm, $workflow, $reviewOperator)) {
    if ($text -match '(?m)^(session|model|reasoning_effort|\w+_target_session|\w+_return_session|\w+_target_model|\w+_return_model|\w+_target_effort|\w+_return_effort)=') {
        throw 'Persistent role charter retains fixed cross-task identity or model/effort'
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
