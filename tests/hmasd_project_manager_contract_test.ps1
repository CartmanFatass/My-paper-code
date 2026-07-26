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
$pro = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_PRO.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
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
    'formal_compute_authority=user_only',
    'hmasd_python_interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    'cross_task_routing=fixed_role_sessions_plus_pre_send_live_settings_probe',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_model_thinking_preservation=pre_send_read_only_probe_explicit_echo',
    'workflow_design_manager_session=019f9d2f-e0ea-7411-9fd7-386f45f76909',
    'project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'external_review_operator_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
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
    'formal_compute_authority=user_only',
    'active_unattended_grant_valid_iteration_limit=9',
    'active_unattended_grant_permission_prompts=forbidden',
    'valid_result_external_pro_adjudication=result_plus_portfolio_delta_required',
    'scientific_portfolio=multiple_live_or_parked_directions_when_supported',
    'portfolio_adjudication_authority=external_pro',
    'scheduled_resource_consuming_action_count=one',
    'scheduled_action_scientific_uniqueness=false',
    'unselected_direction_retention=live_or_parked_with_reactivation_conditions',
    'missing_scheduled_action_with_remaining_balance_and_possible_candidate=focused_external_pro_clarification',
    'scheduled_action_execution=exact_designated_only',
    'project_manager_portfolio_reorder_or_compression=forbidden',
    'out_of_scope_proposal_action=require_in_scope_alternative',
    'portfolio_closure_condition=no_in_scope_executable_candidate_after_full_portfolio_consideration',
    'grant_balance_exhaustion_action=terminal_completion',
    'valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue',
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'scheduled_action_presence=CONTINUE_only',
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only',
    'operational_recovery_authority=within_existing_user_authorized_scientific_boundary',
    'operational_recovery_reauthorization=not_required_per_attempt',
    'operational_recovery_fixed_attempt_limit=none',
    'operational_recovery_scientific_iteration_cost=zero',
    'operational_recovery_scientific_disposition=none',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_route_cache=forbidden',
    'cross_task_model_thinking_preservation=pre_send_read_only_probe_explicit_echo',
    'CODE_SCIENCE_INDEX.md',
    'scripts/hmasd_workspace_ticket.py',
    'CURRENT_WORK.md')) {
    if (-not $pm.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'active_grant_valid_result_adjudication=result_plus_portfolio_delta_required',
    'scientific_portfolio=multiple_live_or_parked_directions_when_supported',
    'portfolio_adjudication_authority=exclusive',
    'scheduled_resource_consuming_action_count=one',
    'scheduled_action_scientific_uniqueness=false',
    'unselected_direction_retention=live_or_parked_with_reactivation_conditions',
    'missing_scheduled_action_with_remaining_balance_and_possible_candidate_response=focused_clarification_required',
    'active_grant_out_of_scope_proposal=require_in_scope_alternative',
    'active_grant_closure_condition=no_in_scope_executable_candidate_after_full_portfolio_consideration',
    'valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue',
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'scheduled_action_presence=CONTINUE_only',
    'valid_result_required_inputs=archived_evidence|grant_boundary|result_class|remaining_balance|current_portfolio|algorithm_principles_section_3',
    'active_grant_user_permission_request=forbidden')) {
    if (-not $pro.Contains($required)) { throw "External Pro unattended grant contract missing: $required" }
}
if ($pm.Contains('portfolio_adjudication_authority=project_manager')) {
    throw 'Project Manager role claims scientific portfolio adjudication'
}
foreach ($required in @(
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue',
    'scheduled_action_presence=CONTINUE_only',
    'missing_scheduled_action_clarification=remaining_balance_and_possible_candidate_only',
    'operational_recovery=automatic_within_unchanged_authorized_boundary',
    'operational_recovery_scientific_iteration_cost=zero',
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only')) {
    if (-not $agile.Contains($required)) { throw "Agile unattended grant contract missing: $required" }
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
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_route_cache=forbidden',
    'cross_task_model_thinking_preservation=pre_send_read_only_probe_explicit_echo',
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
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_route_cache=forbidden',
    'cross_task_model_thinking_preservation=pre_send_read_only_probe_explicit_echo',
    'cross-task',
    'live model and thinking as visible tool parameters')) {
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
