[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Stable workflow surfaces only. Scientific assignments and result labels are
# deliberately not hard-coded here because CURRENT_WORK is the active line.
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @(
    'hmasd-agile-research-development',
    'hmasd-collaborative-workflow-design',
    'hmasd-review-round',
    'hmasd-workflow-change-audit') | Sort-Object
if (Compare-Object $expectedSkills $skills) {
    throw "Unexpected active Skill set: $($skills -join ',')"
}

$roles = @(Get-ChildItem (Join-Path $repo '.agents/roles') -File -Filter '*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedRoles = @(
    'CODE_SCOUT.md',
    'EXPERIMENT_OPERATOR.md',
    'EXTERNAL_REVIEW_OPERATOR.md',
    'EXTERNAL_PRO.md',
    'IMPLEMENTER.md',
    'PROJECT_MANAGER.md',
    'PRO_RESPONSE_MONITOR.md',
    'REVIEWER.md',
    'VERIFIER.md',
    'WORKFLOW_MANAGER.md',
    'WORKFLOW_COST_REVIEWER.md') | Sort-Object
if (Compare-Object $expectedRoles $roles) {
    throw "Unexpected active role set: $($roles -join ',')"
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')
$context = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/AGENT_CONTEXT.md')
$plan = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/IMPLEMENTATION_PLAN.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$pmRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PROJECT_MANAGER.md')
$workflowManagerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_MANAGER.md')
$implementerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/IMPLEMENTER.md')
$reviewerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/REVIEWER.md')
$costReviewerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_COST_REVIEWER.md')
$reviewOperatorRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md')
$proRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_PRO.md')
$monitorRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PRO_RESPONSE_MONITOR.md')
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$complexity = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/EVIDENCE_COMPLEXITY_POLICY.md')
$workflowAudit = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-workflow-change-audit/SKILL.md')
$workflowCollaboration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md')
$workflowCollaborationNormalized = $workflowCollaboration -replace '\s+', ' '
$workflowCollaborationUi = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/agents/openai.yaml')
$handoff = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/RESTART_HANDOFF.md')

foreach ($required in @(
    'document_kind=role_router',
    'all_workspace_agents_auto_load_this_file=true',
    'project_history_in_router=forbidden',
    'dedicated Workflow Manager task',
    'Project Manager task',
    'registered native child',
    'docs/project/CURRENT_WORK.md` is PM-only code attention and runtime state',
    'workflow_manager_workflow_design_authority=exclusive',
    'workflow_manager_workflow_runtime_authority=none',
    'workflow_manager_current_work_authority=none',
    'workflow_manager_git_authority=direct_for_workflow_design_surfaces',
    'workflow_manager_external_review_runtime_authority=none',
    'workflow_manager_experiment_runtime_authority=none',
    'project_manager_code_authority=exclusive',
    'project_manager_runtime_authority=exclusive',
    'project_manager_current_work_authority=exclusive',
    'project_manager_scientific_authority=none',
    'project_manager_git_authority=direct_for_code_runtime_evidence_and_state',
    'project_manager_remote_repository_authority=permanent_user_grant',
    'project_manager_authorized_remote_repository=https://github.com/CartmanFatass/My-paper-code.git',
    'project_manager_external_review_dispatch_and_result_routing=exclusive',
    'project_manager_experiment_dispatch_and_result_routing=exclusive',
    'external_review_operator_transport_authority=exclusive',
    'External Review Operator task',
    'external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary',
    'hmasd-pro-response-monitor',
    'hmasd-collaborative-workflow-design',
    'workflow_change_skill=hmasd-workflow-change-audit',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
    'per_file_hash_handoff=forbidden',
    'isolated_worktree_identity=workspace_ticket_only',
    'handoff_document_write_trigger=explicit_user_request_only',
    'scripts/hmasd_workspace_ticket.py',
    'scripts/hmasd_pro_response_sentinel.py',
    'cross_task_routing=fixed_session_id_plus_fixed_model_effort',
    'cross_task_silent_model_effort_override=forbidden',
    'each send passes model and effort explicitly',
    'same_file_concurrent_writes=forbidden')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}

foreach ($required in @(
    'active_assignment_id=',
    'next_boundary=',
    'autonomous_research_grant=',
    'iterations_remaining=',
    'conclusion_bearing_iterations_consumed=',
    'intermediate_authorization_prompts=forbidden',
    'git_integration_status=',
    'experiment_operator_fallback=forbidden',
    'iteration_report_requirement=required_before_successor',
    'workflow_manager_task=',
    'workflow_manager_fixed_model=gpt-5.6-sol',
    'workflow_manager_fixed_effort=high',
    'external_review_operator_task=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'external_review_operator_fixed_model=gpt-5.6-luna',
    'external_review_operator_fixed_effort=high',
    'project_manager_fixed_model=gpt-5.6-sol',
    'project_manager_fixed_effort=max',
    'cross_task_send_requires_explicit_model_effort=true',
    'cross_task_routing=fixed_session_id_plus_fixed_model_effort',
    'cross_task_silent_model_effort_override=forbidden',
    'code_science_alignment_position=after_pm_implementation_acceptance',
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
    'Project Manager directly stages, commits and pushes accepted code, runtime',
    'Manager separately stages only accepted workflow-design control-plane paths',
    'Native children never run Git',
    'fixed native child',
    'not a persistent task')) {
    if (-not $context.Contains($required)) { throw "Agent context missing: $required" }
}
foreach ($required in @(
    'role_kind=sole_persistent_code_and_runtime_authority_task',
    'project_code_authority=exclusive',
    'project_runtime_authority=exclusive',
    'workflow_design_authority=none',
    'scientific_authority=none',
    'technical_acceptance_authority=exclusive',
    'current_work_owner=exclusive',
    'external_review_dispatch_and_result_routing=exclusive',
    'experiment_orchestration=registered_native_child',
    'workflow_manager_target_session=019f9d2f-e0ea-7411-9fd7-386f45f76909',
    'workflow_manager_target_effort=high',
    'external_review_operator_target_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'external_review_operator_target_effort=high',
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'CODE_SCIENCE_INDEX.md',
    'pre-implementation review',
    'PM receives one terminal')) {
    if (-not $pmRole.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'role=workflow_manager',
    'role_kind=dedicated_persistent_workflow_design_authority_task',
    'session=019f9d2f-e0ea-7411-9fd7-386f45f76909',
    'model=gpt-5.6-sol',
    'reasoning_effort=high',
    'workflow_design_authority=exclusive',
    'workflow_design_acceptance_authority=exclusive',
    'workflow_runtime_authority=none',
    'current_work_authority=none',
    'external_review_runtime_authority=none',
    'experiment_runtime_authority=none',
    'scientific_authority=none',
    'code_authority=none',
    'code_acceptance_authority=none',
    'project_manager_return_session=019f9d04-8b21-7512-acc7-ffe02d262c82',
    'project_manager_return_model=gpt-5.6-sol',
    'project_manager_return_effort=max',
    'workflow_collaboration_skill=hmasd-collaborative-workflow-design',
    'workflow_collaboration_scope=all_mutating_workflow_design',
    'workflow_zero_question_path=fully_specified_mutations',
    'workflow_decision_question_condition=changes_named_plan_field',
    'workflow_plan_confirmation=required_before_mutation',
    'workflow_read_only_plan_confirmation=not_required',
    'workflow_material_plan_drift=reconfirmation_required',
    'workflow_collaboration_runtime_authority=none',
    'routine_preimplementation_code_science_review=forbidden',
    'code_science_alignment_audit=once_after_pm_implementation_acceptance',
    'code_science_alignment_compute_budget=zero',
    'CODE_SCIENCE_INDEX.md',
    'hmasd-workflow-cost-reviewer')) {
    if (-not $workflowManagerRole.Contains($required)) { throw "Workflow Manager role missing: $required" }
}
if ($workflowManagerRole.Contains('current_work_owner=exclusive') -or
    $workflowManagerRole.Contains('external_review_dispatch_and_result_routing=exclusive') -or
    $workflowManagerRole.Contains('experiment_dispatch_and_result_routing=exclusive')) {
    throw 'Workflow Manager retains runtime ownership'
}
foreach ($required in @(
    'evidence_complexity_policy=docs/project/EVIDENCE_COMPLEXITY_POLICY.md',
    'NON_EXECUTABLE_EVIDENCE_DESIGN',
    'O(H*K_search)',
    'O(N*k_neighbor)')) {
    if (-not $pmRole.Contains($required)) { throw "Project Manager role missing complexity rule: $required" }
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
    'parent=workflow_manager',
    'model=gpt-5.6-sol',
    'reasoning_effort=xhigh',
    'fork_turns=none_required',
    'workflow_acceptance_authority=none',
    'COST_AUDIT_ACCEPT',
    'COST_AUDIT_REJECT')) {
    if (-not $costReviewerRole.Contains($required)) { throw "Cost Reviewer role missing: $required" }
}
foreach ($required in @(
    'role=external_review_operator',
    'transport_authority=exclusive_for_assigned_external_pro_round',
    'scientific_authority=none',
    'git_authority=none',
    'answer_now_activation=forbidden',
    'completion_notification=required_once',
    'Project Manager',
    'project_manager_return_session=019f9d04-8b21-7512-acc7-ffe02d262c82',
    'project_manager_return_model=gpt-5.6-sol',
    'project_manager_return_effort=max',
    'cross_task_send_requires_explicit_target_model_effort=true')) {
    if (-not $reviewOperatorRole.Contains($required)) {
        throw "External Review Operator role missing: $required"
    }
}
if (-not $pmRole.Contains('handoff_document_write_trigger=explicit_user_request_only')) {
    throw 'Project Manager role permits automatic handoff writing'
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
    'Project Manager integrates the exact accepted',
    'no relay or completion receipt exists',
    'External Pro owns',
    'Project Manager routes the one existing comparison-only',
    'commit-bound critical-point index',
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
    'Workflow Manager workflow-design procedure',
    'Workflow Manager alone accepts',
    'Workflow Manager never reads or edits them',
    'task-local impact matrix',
    'exactly one existing role charter',
    'Every profile is registered',
    'registered `hmasd-workflow-cost-reviewer` with `fork_turns=none`',
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
    'present a revised complete plan')) {
    if (-not $workflowCollaborationNormalized.Contains($required)) { throw "Workflow collaboration Skill missing: $required" }
}
if (-not $workflowCollaborationUi.Contains('allow_implicit_invocation: false')) {
    throw 'Workflow collaboration Skill permits implicit invocation'
}

foreach ($required in @(
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'FORMAL_RESULT_SCIENTIFIC_DISPOSITION',
    'code counterexample',
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
    'code_acceptance_owner=project_manager',
    'runtime_owner=project_manager',
    'workflow_design_owner=workflow_manager',
    'positive control is valid only when',
    'IMPLEMENTATION_ALIGNMENT_CLARIFICATION',
    'first-match branch reproduction',
    'code_science_audit_mode=contract_diff_only',
    'code_science_audit_position=after_pm_implementation_acceptance',
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
    'observation_mode=external_review_operator_brokered_jsonl_sentinel',
    'browser_authority=none',
    'progress_notifications=forbidden',
    'answer_now_activated=false')) {
    if (-not $monitorRole.Contains($required)) { throw "Monitor role missing: $required" }
}

if ((Get-Content -LiteralPath (Join-Path $repo 'AGENTS.md')).Count -gt 150) {
    throw 'AGENTS role router has accumulated role-specific context'
}
if (Test-Path -LiteralPath (Join-Path $repo 'docs/project/EXTERNAL_REVIEW_PIPELINE.md')) {
    throw 'Stale multi-review pipeline remains on the active line'
}

foreach ($text in @($agents, $current, $context, $plan, $agile, $pmRole, $workflowManagerRole, $reviewOperatorRole, $proRole, $assertion)) {
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
