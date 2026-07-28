[CmdletBinding()]
param([switch]$WorkflowDesignOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Stable workflow surfaces only. Scientific assignments and result labels are
# deliberately not hard-coded here because CURRENT_WORK is the active line.
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$requiredSkills = @(
    'hmasd-agile-research-development',
    'hmasd-collaborative-workflow-design',
    'hmasd-cross-task-routing',
    'hmasd-review-round',
    'hmasd-workflow-change-audit') | Sort-Object
foreach ($required in $requiredSkills) {
    if ($required -notin $skills) { throw "Missing routed workflow Skill: $required" }
}

$roles = @(Get-ChildItem (Join-Path $repo '.agents/roles') -File -Filter '*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedRoles = @(
    'CODE_SCOUT.md',
    'EXPERIMENT_OPERATOR.md',
    'EXTERNAL_PRO.md',
    'IMPLEMENTER.md',
    'CODE_PROJECT_MANAGER.md',
    'RESEARCH_OPERATIONS_MANAGER.md',
    'PRO_RESPONSE_MONITOR.md',
    'REVIEWER.md',
    'VERIFIER.md',
    'WORKFLOW_DESIGN_MANAGER.md',
    'WORKFLOW_COST_REVIEWER.md') | Sort-Object
if (Compare-Object $expectedRoles $roles) {
    throw "Unexpected active role set: $($roles -join ',')"
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$codePmRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$operationsRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md')
$workflowDesignManagerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$proRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_PRO.md')
$workflowAudit = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-workflow-change-audit/SKILL.md')
$workflowCollaboration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md')
$workflowCollaborationNormalized = $workflowCollaboration -replace '\s+', ' '
$workflowCollaborationUi = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/agents/openai.yaml')
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$assertionNormalized = $assertion -replace '\s+', ' '
$handoff = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/RESTART_HANDOFF.md')

if (-not $WorkflowDesignOnly) {
    $current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')
    $context = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/AGENT_CONTEXT.md')
    $plan = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/IMPLEMENTATION_PLAN.md')
}
foreach ($required in @(
    'document_kind=role_router',
    'all_workspace_agents_auto_load_this_file=true',
    'project_history_in_router=forbidden',
    'role_specific_procedure_in_router=forbidden',
    'dedicated Workflow Design Manager task',
    'Code Project Manager task',
    'Research Operations Manager task',
    'registered native child',
    'docs/project/CURRENT_WORK.md` is Research Operations Manager operational state; Code Project Manager may read it on demand',
    'workflow_design_manager_workflow_design_authority=exclusive',
    'workflow_design_manager_workflow_runtime_authority=none',
    'workflow_design_manager_current_work_authority=none',
    'workflow_design_manager_git_authority=direct_for_workflow_design_surfaces',
    'workflow_design_manager_external_review_runtime_authority=none',
    'workflow_design_manager_experiment_runtime_authority=none',
    'code_project_manager_code_authority=exclusive',
    'code_project_manager_technical_acceptance_authority=exclusive',
    'code_project_manager_runtime_authority=none',
    'code_project_manager_current_work_read=bounded_read_only_on_demand',
    'code_project_manager_current_work_write_authority=none',
    'research_operations_manager_runtime_authority=exclusive',
    'research_operations_manager_current_work_authority=exclusive',
    'research_operations_manager_external_review_transport_authority=exclusive',
    'research_operations_manager_experiment_dispatch_and_result_routing=exclusive',
    'external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary',
    'hmasd-pro-response-monitor',
    'hmasd-collaborative-workflow-design',
    'workflow_change_skill=hmasd-workflow-change-audit',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'hmasd_python_interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
    'per_file_hash_handoff=forbidden',
    'isolated_worktree_identity=workspace_ticket_only',
    'hmasd_worktree_root=C:/worktrees/HMASD',
    'project_write_scope=current_checkout_plus_verified_ticket_worktree',
    'external_workspace_access=read_only',
    'raw_external_worktree_creation=forbidden',
    'drive_or_path_alias_creation=forbidden',
    'handoff_document_write_trigger=explicit_user_request_only',
    'scripts/hmasd_workspace_ticket.py',
    'scripts/hmasd_workspace_boundary_guard.py',
    'scripts/hmasd_pro_response_sentinel.py',
    'cross_task_routing=fixed_role_sessions_plus_live_settings_canonicalization',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_model_thinking_preservation=pre_send_probe_plus_pretool_canonicalization',
    'cross_task_route_guard=pretool_live_settings_canonicalization',
    'workflow_design_manager_session=019f9d2f-e0ea-7411-9fd7-386f45f76909',
    'code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'research_operations_manager_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'same_file_concurrent_writes=forbidden')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($surface in @($agents, $codePmRole, $workflowDesignManagerRole, $operationsRole)) {
    if ($surface.Contains('pre_send_read_only_probe_explicit_echo')) {
        throw 'Persistent-role routing retains the unguarded explicit-echo contract'
    }
}

if ((Get-Content -LiteralPath (Join-Path $repo 'AGENTS.md')).Count -gt 150) {
    throw 'AGENTS role router has accumulated role-specific context'
}

foreach ($required in @(
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
    'research_operations_manager_portfolio_reorder_or_compression=forbidden',
    'valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue',
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'scheduled_action_presence=CONTINUE_only',
    'operational_recovery_authority=within_existing_user_authorized_scientific_boundary',
    'operational_recovery_reauthorization=not_required_per_attempt',
    'operational_recovery_scientific_iteration_cost=zero',
    'review_fence_stage_commit=full_40_hex_only',
    'review_fence_prefix_correction=once_same_conversation_before_assistant_response',
    'review_fence_correction_question_resubmission=forbidden',
    'review_fence_monitor_concurrency=one_live',
    'review_assignment_acceptance=server_visible_exact_fence_only',
    'review_client_send_effect=uncommitted_until_server_visible',
    'review_unpersisted_assignment_recovery=once_same_conversation_exact_assignment_replay',
    'review_unpersisted_assignment_recovery_eligible=reload_then_exact_url_reopen_both_show_zero_matching_fence',
    'review_unpersisted_assignment_recovery_prior_server_visible_count=zero',
    'review_unpersisted_assignment_recovery_client_send_limit=2_assignment_sends_total',
    'review_unpersisted_assignment_recovery_scientific_iteration_cost=zero',
    'review_response_retry=once_same_conversation_after_terminal_attempt',
    'review_response_retry_eligible=format_nonconforming_or_no_response_after_exhausted_recovery',
    'review_response_retry_requires_server_visible_original_fence=true',
    'review_response_retry_unproven_persistence=forbidden',
    'review_response_retry_submission_limit=2_total',
    'review_response_retry_scientific_iteration_cost=zero',
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only')) {
    if (-not $operationsRole.Contains($required)) { throw "Research Operations Manager role missing: $required" }
}
foreach ($required in @(
    'active_grant_valid_result_adjudication=result_plus_portfolio_delta_required',
    'scientific_portfolio=multiple_live_or_parked_directions_when_supported',
    'portfolio_adjudication_authority=exclusive',
    'scheduled_resource_consuming_action_count=one',
    'scheduled_action_scientific_uniqueness=false',
    'unselected_direction_retention=live_or_parked_with_reactivation_conditions',
    'missing_scheduled_action_with_remaining_balance_and_possible_candidate_response=focused_clarification_required',
    'active_grant_closure_condition=no_in_scope_executable_candidate_after_full_portfolio_consideration',
    'valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue',
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'scheduled_action_presence=CONTINUE_only',
    'valid_result_required_inputs=archived_evidence|grant_boundary|result_class|remaining_balance|current_portfolio|algorithm_principles_section_3')) {
    if (-not $proRole.Contains($required)) { throw "External Pro role missing: $required" }
}
if ($operationsRole.Contains('portfolio_adjudication_authority=research_operations_manager')) {
    throw 'Research Operations Manager claims scientific portfolio adjudication'
}
foreach ($required in @(
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue',
    'scheduled_action_presence=CONTINUE_only',
    'missing_scheduled_action_clarification=remaining_balance_and_possible_candidate_only',
    'operational_recovery=automatic_within_unchanged_authorized_boundary',
    'operational_recovery_scientific_iteration_cost=zero',
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing: $required" }
}
if ($agile.Contains('External Review Operator') -or
    -not (($agile -replace '\s+', ' ').Contains('returns its exact commit and index to Research Operations Manager'))) {
    throw 'Agile Skill retains a stale or ambiguous review route'
}
foreach ($surface in @($codePmRole, $agile)) {
    foreach ($required in @(
        'scripts/hmasd_workspace_ticket.py provision',
        'C:/worktrees/HMASD',
        'Raw external `git worktree`')) {
        if (-not $surface.Contains($required)) {
            throw "Worktree provisioning contract missing: $required"
        }
    }
}
if ($assertionNormalized.Contains('Research Operations Manager executes the smallest repair') -or
    -not $assertionNormalized.Contains('sends one exact correction assignment to Code Project Manager') -or
    -not $assertionNormalized.Contains('After `CODE_ACCEPTED`')) {
    throw 'Assertion audit assigns code repair to Research Operations Manager'
}
if (-not $handoff.Contains('Code Project Manager inspects only the G35 diff') -or
    -not $handoff.Contains('and updates the code-science index') -or
    -not $handoff.Contains('docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md') -or
    -not $handoff.Contains('stages exactly the three G35 code/index paths') -or
    -not $handoff.Contains('returns `CODE_ACCEPTED`') -or
    -not $handoff.Contains('Research Operations Manager dispatches exactly one fresh') -or
    $handoff.Contains('Research Operations Manager updates the G35 prelaunch note, code-science index')) {
    throw 'Restart handoff violates code/operations ownership'
}
if ($workflowDesignManagerRole.Contains('Project-Manager workflow-design assignment')) {
    throw 'Workflow Design Manager retains the retired requester identity'
}

if ($WorkflowDesignOnly) {
    Write-Output 'HMASD_RESEARCH_WORKFLOW_DESIGN_CONTRACT_OK'
    return
}

$implementerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/IMPLEMENTER.md')
$reviewerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/REVIEWER.md')
$costReviewerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_COST_REVIEWER.md')
$operationsRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md')
$monitorRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PRO_RESPONSE_MONITOR.md')
$complexity = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/EVIDENCE_COMPLEXITY_POLICY.md')

foreach ($required in @(
    'active_assignment_id=',
    'next_boundary=',
    'autonomous_research_grant=',
    'iterations_remaining=',
    'conclusion_bearing_iterations_consumed=',
    'git_integration_status=',
    'experiment_operator_fallback=forbidden',
    'iteration_report_requirement=required_before_successor',
    'workflow_design_manager_task=',
    'code_science_alignment_position=after_code_project_manager_implementation_acceptance',
    'code_science_alignment_index=commit_bound_CODE_SCIENCE_INDEX_required',
    'routine_preimplementation_code_science_review=forbidden',
    'active_assignment_id=NO_ACTIVE_CODE_ASSIGNMENT_G33_ABANDONED',
    'g33_status=ABANDONED_BY_USER_AFTER_DISCUSSION',
    'g33_active_code_authority=none',
    'uav_user_scope=transient_demand_coverage_plus_charging_roster_change_plus_temporary_detach_failure_robustness',
    'uav_physical_fleet_boundary=fixed_slots_distinct_from_dynamic_service_roster',
    'workflow_hash_validation=disabled')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing: $required" }
}

foreach ($required in @(
    'search_complexity_ceiling=O(H*K_search)',
    'candidate_trajectory_count_ceiling=16',
    'future_simulated_transitions_per_controller_episode<=16*H',
    'nested_rollout_replanning=forbidden',
    'nonformal_wall_clock_cap_minutes=20',
    'formal_iteration_wall_clock_cap_hours=8',
    'scalable_algorithm_target=O(N*k_neighbor)_or_O(N*logN)',
    'fixed_small_exact_simulator_O(N^2)=allowed_as_reference_only')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing complexity boundary: $required" }
}

foreach ($required in @(
    'handoff_document_write_policy=user_explicit_only',
    'automatic_handoff_document_write=forbidden')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing: $required" }
}

$remainingMatch = [regex]::Match($current, '(?m)^iterations_remaining=(\d+)\s*$')
$consumedMatch = [regex]::Match($current, '(?m)^conclusion_bearing_iterations_consumed=(\d+)\s*$')
if (-not $remainingMatch.Success -or -not $consumedMatch.Success) {
    throw 'CURRENT_WORK iteration accounting is not a nonnegative integer contract'
}
if ($current.Contains('autonomous_research_grant=ACTIVE_') -and
    [int]$remainingMatch.Groups[1].Value -le 0) {
    throw 'An active autonomous grant has no remaining conclusion-bearing iterations'
}

foreach ($required in @(
    'backend=cpu',
    'torch_threads=1',
    'docs/research/designs/',
    'Generic Superpowers execution')) {
    if (-not $plan.Contains($required)) { throw "Implementation plan missing: $required" }
}

foreach ($required in @(
    'Manager separately stages only accepted workflow-design control-plane paths',
    'Native children never run Git',
    'fixed native child',
    'not a persistent task')) {
    if (-not $context.Contains($required)) { throw "Agent context missing: $required" }
}
foreach ($required in @(
    'role=code_project_manager',
    'role_kind=persistent_code_and_technical_acceptance_task',
    'code_authority=exclusive',
    'runtime_authority=none',
    'workflow_design_authority=none',
    'scientific_authority=none',
    'technical_acceptance_authority=exclusive',
    'current_work_read=bounded_read_only_on_demand',
    'current_work_write_authority=none',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_model_thinking_preservation=pre_send_probe_plus_pretool_canonicalization',
    'cross_task_route_guard=pretool_live_settings_canonicalization',
    'CODE_SCIENCE_INDEX.md',
    'CODE_ACCEPTED')) {
    if (-not $codePmRole.Contains($required)) { throw "Code Project Manager role missing: $required" }
}
foreach ($required in @(
    'role=workflow_design_manager',
    'role_kind=dedicated_persistent_workflow_design_authority_task',
    'workflow_design_authority=exclusive',
    'workflow_design_acceptance_authority=exclusive',
    'workflow_runtime_authority=none',
    'current_work_authority=none',
    'external_review_runtime_authority=none',
    'experiment_runtime_authority=none',
    'scientific_authority=none',
    'code_authority=none',
    'code_acceptance_authority=none',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=exact_fixed_requester_role_session',
    'cross_task_route_cache=forbidden',
    'cross_task_model_thinking_preservation=pre_send_probe_plus_pretool_canonicalization',
    'cross_task_route_guard=pretool_live_settings_canonicalization',
    'never an automatic acceptance gate',
    'workflow_collaboration_skill=hmasd-collaborative-workflow-design',
    'workflow_collaboration_scope=all_mutating_workflow_design',
    'workflow_zero_question_path=fully_specified_mutations',
    'workflow_decision_question_condition=changes_named_plan_field',
    'workflow_plan_confirmation=required_before_mutation',
    'workflow_read_only_plan_confirmation=not_required',
    'workflow_material_plan_drift=reconfirmation_required',
    'workflow_collaboration_runtime_authority=none',
    'routine_preimplementation_code_science_review=forbidden',
    'code_science_alignment_audit=once_after_code_project_manager_implementation_acceptance',
    'code_science_alignment_compute_budget=zero',
    'CODE_SCIENCE_INDEX.md',
    'hmasd-workflow-cost-reviewer')) {
    if (-not $workflowDesignManagerRole.Contains($required)) { throw "Workflow Design Manager role missing: $required" }
}
if ($workflowDesignManagerRole.Contains('current_work_owner=exclusive') -or
    $workflowDesignManagerRole.Contains('external_review_dispatch_and_result_routing=exclusive') -or
    $workflowDesignManagerRole.Contains('experiment_dispatch_and_result_routing=exclusive')) {
    throw 'Workflow Design Manager retains runtime ownership'
}
foreach ($required in @(
    'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
    'NON_EXECUTABLE_EVIDENCE_DESIGN',
    'O(H*K_search)',
    'O(N*k_neighbor)')) {
    if (-not $codePmRole.Contains($required)) { throw "Code Project Manager role missing complexity rule: $required" }
}
foreach ($roleText in @($implementerRole, $reviewerRole)) {
    foreach ($required in @(
        'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
        'NON_EXECUTABLE_EVIDENCE_DESIGN')) {
        if (-not $roleText.Contains($required)) { throw "Native code role missing complexity rule: $required" }
    }
}
foreach ($required in @(
    'callable_agent_type=hmasd-workflow-cost-reviewer',
    'parent=workflow_design_manager',
    'model=gpt-5.6-sol',
    'reasoning_effort=xhigh',
    'fork_turns=none_required',
    'workflow_acceptance_authority=none',
    'COST_AUDIT_ACCEPT',
    'COST_AUDIT_REJECT')) {
    if (-not $costReviewerRole.Contains($required)) { throw "Cost Reviewer role missing: $required" }
}
foreach ($required in @(
    'role=research_operations_manager',
    'external_review_transport_authority=exclusive',
    'runtime_authority=exclusive',
    'current_work_authority=exclusive',
    'scientific_authority=none',
    'code_acceptance_authority=none',
    'Research Operations Manager may request a workflow-design change directly',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_model_thinking_preservation=pre_send_probe_plus_pretool_canonicalization',
    'cross_task_route_guard=pretool_live_settings_canonicalization')) {
    if (-not $operationsRole.Contains($required)) {
        throw "Research Operations Manager role missing: $required"
    }
}
if (-not $operationsRole.Contains('handoff_document_write_trigger=explicit_user_request_only')) {
    throw 'Research Operations Manager role permits automatic handoff writing'
}
foreach ($required in @(
    'write_trigger=explicit_user_request_only',
    'automatic_create_or_update=forbidden')) {
    if (-not $handoff.Contains($required)) { throw "Handoff contract missing: $required" }
}
if (-not $workflowAudit.Contains('written only on explicit user request')) {
    throw 'Workflow audit Skill permits automatic handoff writing'
}
foreach ($required in @(
    'superpowers_execution=disabled',
    'workflow_hash_validation=disabled',
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only',
    'CODE_SCIENCE_ALIGNMENT_AUDIT')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing: $required" }
}
foreach ($required in @(
    'search_complexity_ceiling=O(H*K_search)',
    'nested_rollout_replanning=forbidden',
    'NON_EXECUTABLE_EVIDENCE_DESIGN',
    'O(N*k_neighbor)')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing complexity rule: $required" }
}
foreach ($required in @(
    'Workflow Design Manager workflow-design procedure',
    'Workflow Design Manager alone accepts',
    'Workflow Design Manager never reads or edits them',
    'task-local impact matrix',
    'exactly one existing role charter',
    'Every profile is registered',
    'Only when the user explicitly requests a workflow cost audit',
    'fresh-task profile smoke',
    'check_hmasd_agent_harness.py')) {
    if (-not $workflowAudit.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}
foreach ($required in @(
    'runtime_authority=none',
    'zero-question path',
    'changes at least one named plan field',
    'one question at a time',
    'Requirements understanding',
    'Exact paths',
    'Perform no mutation',
    'confirms the complete plan in natural language',
    'Complete a read-only inspection',
    'workflow cost audit explicitly requested by the user',
    'present a revised complete plan')) {
    if (-not $workflowCollaborationNormalized.Contains($required)) { throw "Workflow collaboration Skill missing: $required" }
}
if (-not $workflowCollaborationUi.Contains('allow_implicit_invocation: false')) {
    throw 'Workflow collaboration Skill permits implicit invocation'
}
if ($workflowAudit.Contains('If and only if the change adds or expands a workflow step')) {
    throw 'Workflow cost audit remains an automatic acceptance gate'
}

foreach ($required in @(
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'FORMAL_RESULT_SCIENTIFIC_DISPOSITION',
    'code_science_audit_mode=contract_diff_only',
    'code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY',
    'code_science_audit_new_algorithm_or_evidence_search=forbidden')) {
    if (-not $proRole.Contains($required)) { throw "External Pro role missing: $required" }
}
foreach ($required in @(
    'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
    'O(H*K_search)',
    '16*H',
    'O(N*k_neighbor)')) {
    if (-not $proRole.Contains($required)) { throw "External Pro role missing complexity boundary: $required" }
}
foreach ($required in @(
    'scientific_acceptance_owner=external_pro',
    'code_acceptance_owner=code_project_manager',
    'runtime_owner=research_operations_manager',
    'workflow_design_owner=workflow_design_manager',
    'positive control is valid only when',
    'IMPLEMENTATION_ALIGNMENT_CLARIFICATION',
    'first-match branch reproduction',
    'code_science_audit_mode=contract_diff_only',
    'code_science_audit_position=after_code_project_manager_implementation_acceptance',
    'routine_preimplementation_code_science_review=forbidden',
    'code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY',
    'CODE_SCIENCE_INDEX.md',
    'claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded',
    'new_algorithm_design_during_code_audit=forbidden',
    'new_evidence_search_during_code_audit=forbidden',
    'there is no review of the review')) {
    if (-not $assertion.Contains($required)) { throw "Assertion audit missing: $required" }
}
foreach ($required in @(
    'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
    'NON_EXECUTABLE_EVIDENCE_DESIGN',
    'O(H*K_search)',
    'O(N*logN)')) {
    if (-not $assertion.Contains($required)) { throw "Assertion audit missing complexity gate: $required" }
}
foreach ($required in @(
    'search_complexity_ceiling=O(H*K_search)',
    'future_simulated_transitions_per_controller_episode<=16*H',
    'nested_rollout_replanning=forbidden',
    'dense_pairwise_deployment_claim=forbidden',
    'fixed_small_exact_simulator_O(N^2)=allowed_as_reference_only',
    'override_authority=user_only_for_one_named_boundary')) {
    if (-not $complexity.Contains($required)) { throw "Complexity policy missing: $required" }
}
foreach ($required in @(
    'callable_agent_type=hmasd-pro-response-monitor',
    'observation_mode=research_operations_manager_brokered_jsonl_sentinel',
    'browser_authority=none',
    'progress_notifications=forbidden',
    'answer_now_activated=false')) {
    if (-not $monitorRole.Contains($required)) { throw "Monitor role missing: $required" }
}

if (Test-Path -LiteralPath (Join-Path $repo 'docs/project/EXTERNAL_REVIEW_PIPELINE.md')) {
    throw 'Stale multi-review pipeline remains on the active line'
}

foreach ($text in @($agents, $current, $context, $plan, $agile, $codePmRole, $operationsRole, $workflowDesignManagerRole, $proRole, $assertion)) {
    if ($text -match '(?m)^\w+_sha256=' -or $text.Contains('path_hash_source_status')) {
        throw 'Active workflow retains a hash handoff'
    }
    if ($text.Contains('superpowers_execution=enabled')) {
        throw 'Active workflow enables generic Superpowers execution'
    }
}

$reportReadme = Join-Path $repo 'docs/report/README.md'
if (-not (Test-Path -LiteralPath $reportReadme -PathType Leaf)) {
    throw 'Iteration-report README is missing'
}
$readme = Get-Content -Raw -Encoding UTF8 -LiteralPath $reportReadme
foreach ($required in @(
    'iteration_report_language=zh-CN',
    'separate_approval=not_required',
    'additional_review=false')) {
    if (-not $readme.Contains($required)) { throw "Iteration-report contract missing: $required" }
}

$consumed = [int]$consumedMatch.Groups[1].Value
for ($iteration = 1; $iteration -le $consumed; $iteration++) {
    $path = Join-Path $repo "docs/report/ITERATION_$iteration.md"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing Chinese iteration report: ITERATION_$iteration.md"
    }
    $report = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    if (-not [regex]::IsMatch($report, '[\p{IsCJKUnifiedIdeographs}]')) {
        throw "ITERATION_$iteration.md is not a Chinese report"
    }
}

foreach ($retired in @(
    'ha_ctse_process/temporal_duty_g1.py',
    'ha_ctse_process/ehc_g1.py',
    'scripts/run_access_positive_ehc_g1.py',
    'tests/ha_ctse_process_temporal_duty_g1_test.py',
    'tests/ha_ctse_process_ehc_g1_test.py',
    'tests/run_access_positive_ehc_g1_test.py',
    'ha_ctse_process/cross_lifecycle_handoff_g2.py',
    'ha_ctse_process/ehc_handoff_g2.py',
    'scripts/run_cross_lifecycle_handoff_g2.py',
    'tests/ha_ctse_process_cross_lifecycle_handoff_g2_test.py',
    'tests/ha_ctse_process_ehc_handoff_g2_test.py',
    'tests/run_cross_lifecycle_handoff_g2_test.py',
    'ha_ctse_process/useful_effect_roster_g3.py',
    'scripts/run_useful_effect_roster_g3.py',
    'tests/ha_ctse_process_useful_effect_roster_g3_test.py',
    'tests/run_useful_effect_roster_g3_test.py')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Closed executable remains on the active line: $retired"
    }
}

Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
