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
    'hmasd-agentify-pro-transport',
    'hmasd-collaborative-workflow-design',
    'hmasd-cross-task-routing',
    'hmasd-explorer-project-validation',
    'hmasd-independent-research-exploration',
    'hmasd-independent-research-pro-review',
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
    'INDEPENDENT_RESEARCH_EXPLORER.md',
    'INDEPENDENT_RESEARCH_DIRECTION_REVIEW_OPERATOR.md',
    'INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md',
    'RESEARCH_CRITIC.md',
    'RESEARCH_INNOVATOR.md',
    'RESEARCH_PRINCIPLES_ANALYST.md',
    'RESEARCH_SCOUT.md',
    'REVIEWER.md',
    'VERIFIER.md',
    'WORKFLOW_AUDITOR.md',
    'WORKFLOW_DESIGN_MANAGER.md',
    'WORKFLOW_COST_REVIEWER.md',
    'WORKFLOW_IMPLEMENTER.md',
    'WORKFLOW_REVIEWER.md') | Sort-Object
if (Compare-Object $expectedRoles $roles) {
    throw "Unexpected active role set: $($roles -join ',')"
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$codePmRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$operationsRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md')
$workflowDesignManagerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$workflowDesignManagerRoleNormalized = $workflowDesignManagerRole -replace '\s+', ' '
$proRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_PRO.md')
$workflowAudit = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-workflow-change-audit/SKILL.md')
$workflowCollaboration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md')
$workflowCollaborationNormalized = $workflowCollaboration -replace '\s+', ' '
$workflowCollaborationUi = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/agents/openai.yaml')
$crossTaskRouting = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-cross-task-routing/SKILL.md')
$crossTaskRoutingNormalized = $crossTaskRouting -replace '\s+', ' '
$independentResearchRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$independentReviewRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md')
$independentDirectionReviewRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_DIRECTION_REVIEW_OPERATOR.md')
$independentDirectionReviewProfile = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/agents/hmasd-independent-research-review-operator.toml')
$researchScoutRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_SCOUT.md')
$researchCriticRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_CRITIC.md')
$researchInnovatorRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_INNOVATOR.md')
$researchPrinciplesRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md')
$independentResearchSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/SKILL.md')
$explorerValidationSkillPath = Join-Path $repo '.agents/skills/hmasd-explorer-project-validation/SKILL.md'
$explorerValidationSkill = Get-Content -Raw -LiteralPath $explorerValidationSkillPath
$explorerValidationScriptPath = Join-Path $repo '.agents/skills/hmasd-explorer-project-validation/scripts/explorer_project_packet.py'
$explorerValidationContractPath = Join-Path $repo 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
$explorerValidationContract = Get-Content -Raw -LiteralPath $explorerValidationContractPath
$explorerValidationContractNormalized = $explorerValidationContract -replace '\s+', ' '
$independentResearchMyLib = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/mylib.md')
$parallelResearch = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md')
$openInspiration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/open-algorithm-inspiration.md')
$researchMethodology = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/research-methodology.md')
$independentReviewSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$agentifyTransportSkillPath = Join-Path $repo '.agents/skills/hmasd-agentify-pro-transport/SKILL.md'
$agentifyTransportScriptPath = Join-Path $repo '.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py'
$agentifyTransportContractPath = Join-Path $repo 'docs/project/AGENTIFY_PRO_TRANSPORT.md'
$agentifyTransportSkill = Get-Content -Raw -LiteralPath $agentifyTransportSkillPath
$agentifyTransportSkillNormalized = $agentifyTransportSkill -replace '\s+', ' '
$agentifyTransportScript = Get-Content -Raw -LiteralPath $agentifyTransportScriptPath
$agentifyTransportContract = Get-Content -Raw -LiteralPath $agentifyTransportContractPath
$agentifyTransportContractNormalized = $agentifyTransportContract -replace '\s+', ' '
$independentReviewQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/20_PRO_OPEN_QUESTION.md')
$independentConstructiveQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/21_DIRECTION_CONSTRUCTIVE_REVIEW.md')
$independentAdversarialQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/21_DIRECTION_ADVERSARIAL_REVIEW.md')
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$assertionNormalized = $assertion -replace '\s+', ' '
$handoff = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/RESTART_HANDOFF.md')

if (-not (Test-Path -LiteralPath $explorerValidationSkillPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $explorerValidationScriptPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $explorerValidationContractPath -PathType Leaf)) {
    throw 'Explorer project-validation Skill/script/contract coupling is missing'
}
foreach ($required in @(
    'EXPLORER_PROJECT_CANDIDATE_PACKET',
    'EXPLORER_ADVISORY_REFINEMENT_PACKET',
    'Ops-centered lane',
    'dedicated Operations-owned Pro conversation',
    'formal Pro transport',
    'Independent Research Review Operator',
    'one candidate is selected for each Pro package',
    'EXPLORER_TOY_DESIGN_ASSERTION_AUDIT',
    'EXPLORER_TOY_RESULT_SCIENTIFIC_DISPOSITION',
    'AWAITING_TOY_COMPUTE_GRANT')) {
    if (-not $explorerValidationSkill.Contains($required)) {
        throw "Explorer project-validation Skill missing: $required"
    }
}
foreach ($entry in @(
    @($operationsRole, 'explorer_toy_validation_skill=hmasd-explorer-project-validation'),
    @($operationsRole, 'explorer_toy_pro_conversation=dedicated_ops_owned_runtime_registration'),
    @($operationsRole, 'explorer_toy_candidate_per_package=one'),
    @($operationsRole, 'explorer_toy_pregrant_stop=AWAITING_TOY_COMPUTE_GRANT'),
    @($operationsRole, 'formal=false'),
    @($operationsRole, 'current_work_mutation=forbidden'),
    @($operationsRole, 'exactly one candidate per Pro turn'),
    @($independentResearchRole, 'EXPLORER_PROJECT_CANDIDATE_PACKET'),
    @($independentResearchRole, 'project_toy_compute_authority=none'),
    @($proRole, 'EXPLORER_TOY_DESIGN_ASSERTION_AUDIT'),
    @($proRole, 'EXPLORER_TOY_RESULT_SCIENTIFIC_DISPOSITION'),
    @($proRole, 'TOY_CONTRACT_FROZEN|ADVISORY_REFINEMENT_REQUIRED|PARK_CANDIDATE'),
    @($explorerValidationContract, 'authority={scientific_authority:none,code_authority:none,compute_authority:none,project_state_effect:none}'),
    @($explorerValidationContract, 'dedicated Ops-owned Pro conversation'),
    @($explorerValidationContract, 'current_work_mutation=forbidden'),
    @($explorerValidationContract, 'exactly one candidate in each Pro'),
    @($explorerValidationContract, 'Explorer packet or candidate-artifact nonconformance'),
    @($explorerValidationContract, 'packet-validator or workflow-routing defect'),
    @($operationsRole, 'do not consume a formal iteration, update the CDC portfolio'),
    @($proRole, 'cannot consume a formal iteration, update the CDC portfolio'),
    @($explorerValidationSkill, 'do not update the CDC portfolio'),
    @($explorerValidationSkill, 'current_work_mutation=forbidden'),
    @($explorerValidationSkill, 'CAND-VAP-FOLR-CORE|CAND-VSP-02|CAND-VSP-05'),
    @($explorerValidationContract, 'consume no formal iteration'),
    @($explorerValidationContractNormalized, 'Candidate evidence, run roots, artifacts and results must remain candidate-specific')) ) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Explorer project-validation role/contract coupling missing: $($entry[1])"
    }
}
foreach ($required in @(
    'document_kind=explorer_project_candidate_packet_v1',
    'EXPLORER_TOY_DESIGN_ASSERTION_AUDIT',
    'nonformal_toy',
    'local_research',
    'pro_reviews',
    'symlink/reparse',
    'EXPLORER_PROJECT_PACKET_OK',
    'build',
    'check')) {
    if (-not (Get-Content -Raw -LiteralPath $explorerValidationScriptPath).Contains($required)) {
        throw "Explorer project packet script missing: $required"
    }
}

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
    'Independent Research Pro Review Operator task',
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
    'research_operations_manager_formal_external_review_transport_authority=exclusive',
    'research_operations_manager_experiment_dispatch_and_result_routing=exclusive',
    'external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary',
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
    'workflow_gate_form=budget_grant_or_scope_decision_only',
    'per_action_confirmation_inside_active_grant=forbidden',
    'reversible_internal_action_user_gate=forbidden',
    'internal_role_handoff_within_active_grant=no_user_authority_required',
    'scripts/hmasd_workspace_ticket.py',
    'scripts/hmasd_workspace_boundary_guard.py',
    'cross_task_routing=locked_role_session_model_thinking',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'workflow_design_manager_session=019fb73d-5635-7b63-b165-6c5129bc0217',
    'code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'research_operations_manager_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'independent_research_explorer_session=019fb398-0a76-7bd0-9400-c5ea4eefa5de',
    'independent_research_review_operator_session=019fb311-6137-7781-9708-3df24da34a4b',
    'same_file_concurrent_writes=forbidden')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($entry in @(
    @($agents, '.agents/skills/hmasd-agentify-pro-transport/SKILL.md'),
    @($operationsRole, 'review_transport_agentify_formal_stable_key=hmasd-formal-pro'),
    @($operationsRole, 'review_transport_agentify_explorer_validation_stable_key=hmasd-explorer-validation-pro'),
    @($operationsRole, 'review_transport_generation_active_send=forbidden'),
    @($operationsRole, 'review_transport_recovery_rule=.agents/skills/hmasd-agentify-pro-transport/SKILL.md#minimal-recovery'),
    @($workflowDesignManagerRole, 'agentify_transport_real_review_send=forbidden'),
    @($independentReviewRole, 'review_transport_agentify_stable_key=hmasd-independent-research-pro'),
    @($independentReviewSkill, '$hmasd-agentify-pro-transport'),
    @($agentifyTransportSkill, 'transport_backend'),
    @($agentifyTransportSkill, 'transport_owner'),
    @($agentifyTransportSkill, 'assignment_identity'),
    @($agentifyTransportSkill, 'timeout_ms'),
    @($agentifyTransportSkillNormalized, 'Active generation or a readable complete response always suppresses another'),
    @($agentifyTransportSkillNormalized, 'client submission limit is three per assignment'),
    @($agentifyTransportSkillNormalized, 'existing immutable request records'),
    @($agentifyTransportSkillNormalized, 'adds no hash, ledger or validator gate'),
    @($agentifyTransportSkillNormalized, 'Ordinary recovery never launches a synthetic smoke'),
    @($agentifyTransportSkillNormalized, 'duplicate submission of the same operation'),
    @($agentifyTransportContractNormalized, 'agentify_required_commit=read_AGENTIFY_REQUIRED_COMMIT_from_wrapper'),
    @($agentifyTransportContractNormalized, 'runtime-only'),
    @($agentifyTransportContractNormalized, 'TRANSPORT_BACKEND.json'),
    @($agentifyTransportContractNormalized, 'sourceDirty'),
    @($agentifyTransportScript, 'transport_owner'),
    @($agentifyTransportScript, 'backend_selection_path'),
    @($agentifyTransportScript, 'AGENTIFY_REQUIRED_COMMIT'),
    @($agentifyTransportScript, 'sendCount'),
    @($agentifyTransportScript, 'snapshot_stability_too_short')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Agentify route/contract coupling missing: $($entry[1])"
    }
}
foreach ($staleGate in @('resend requires a new user instruction', 'Only no recorded user message permits')) {
    if ($agentifyTransportSkill.Contains($staleGate)) {
        throw "Agentify transport retains a per-resend user gate: $staleGate"
    }
}
if ($agentifyTransportScript.Contains('"prompt_sha256"')) {
    throw 'Agentify wrapper must not use prompt_sha256 as a request or recovery gate'
}
foreach ($required in @(
    'independent_research_canonical_scientific_authority=none',
    'independent_research_explorer_write_scope=local_research_except_pro_reviews',
    'independent_research_review_operator_transport_authority=exclusive_for_user_authorized_independent_methodology_review',
    'independent_research_review_operator_write_scope=local_research/pro_reviews_plus_registered_cross_task_handoff_helper',
    'independent_research_review_operator_formal_workflow_authority=none',
    'independent_research_direction_review_operator=hmasd-independent-research-review-operator',
    'independent_research_direction_review_operator_parent=independent_research_explorer',
    'independent_research_direction_review_operator_authority=one_exact_direction_review_assignment',
    'independent_research_direction_review_operator_write_scope=exact_assigned_local_research/pro_reviews_item_root',
    '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md',
    '.agents/roles/INDEPENDENT_RESEARCH_DIRECTION_REVIEW_OPERATOR.md',
    '.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md',
    'hmasd-independent-research-exploration',
    'hmasd-independent-research-pro-review')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing research route: $required" }
}
foreach ($required in @(
    'role=independent_research_review_operator',
    'role_kind=user_owned_persistent_independent_pro_transport_task',
    'model=gpt-5.6-luna',
    'reasoning_effort=medium',
    'review_scope=explicit_user_authorized_methodology_audit_only',
    'formal_workflow_authority=none',
    'scientific_authority=none',
    'git_authority=none',
    'write_scope=local_research/pro_reviews_only',
    'formal_review_conversation_access=forbidden',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_target_settings=locked_role_session_model_thinking',
    'cross_task_route_cache=forbidden')) {
    if (-not $independentReviewRole.Contains($required)) {
        throw "Independent Research Review Operator role missing: $required"
    }
}
foreach ($required in @(
    'exact methodology item root',
    'Direction review is forbidden in this persistent task',
    'One user instruction authorizes one methodology turn')) {
    if (-not $independentReviewRole.Contains($required)) {
        throw "Independent Research Review Operator write boundary missing: $required"
    }
}
foreach ($required in @(
    'role=independent_research_direction_review_operator',
    'callable_agent_type=hmasd-independent-research-review-operator',
    'role_kind=registered_nonpersistent_native_child',
    'parent=independent_research_explorer',
    'model=gpt-5.6-luna',
    'reasoning_effort=medium',
    'authority=one_exact_direction_review_assignment',
    'review_transport_stable_key=hmasd-independent-research-pro',
    'review_transport_concurrency=one_active_child_per_binding',
    'client_send_limit=1',
    'assignment_identity=IR_DIRECTION_REVIEW:<exact identity>',
    'cross_session_send=forbidden_native_final_return_only',
    'terminal_statuses=COMPLETE|BLOCKED',
    'tool working directory to the exact assigned item',
    'sibling item path is forbidden',
    'THIRD_PARTY_GEMINI_ADVISORY')) {
    if (-not $independentDirectionReviewRole.Contains($required)) {
        throw "Independent direction-review child role missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-independent-research-review-operator"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "medium"',
    '.agents/roles/INDEPENDENT_RESEARCH_DIRECTION_REVIEW_OPERATOR.md',
    'assignment identity must start with IR_DIRECTION_REVIEW:',
    'working directory to the exact assigned item root',
    'never address a sibling review item',
    'Never call a cross-task messaging tool')) {
    if (-not $independentDirectionReviewProfile.Contains($required)) {
        throw "Independent direction-review child profile missing: $required"
    }
}
foreach ($required in @(
    'Use only the persistent',
    'methodology audit',
    'native direction-review child does not load this Skill',
    'complete response verbatim',
    '60_METHODOLOGY_PACKET.md',
    'Submit exactly once',
    'Never enter a direction review',
    'Workflow Design Manager')) {
    if (-not $independentReviewSkill.Contains($required)) {
        throw "Independent research Pro-review Skill missing: $required"
    }
}
foreach ($forbidden in @(
    'PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW',
    'PRO_ADVERSARIAL_SCIENTIFIC_REVIEW',
    '60_DIRECTION_PACKET.md')) {
    if ($independentReviewSkill.Contains($forbidden)) {
        throw "Persistent methodology Skill contains direction-child procedure: $forbidden"
    }
}
foreach ($required in @(
    'review_mode=INDEPENDENT_RESEARCH_METHODOLOGY_AUDIT',
    'SCIENTIFIC_OBJECTS',
    'MEMBERSHIP_NONSTATIONARITY',
    'VARIABLE_SKILL_DURATION',
    'MODULE_ADMISSION',
    'CONJECTURE_AND_COLLABORATION',
    'METHODOLOGY_PRINCIPLES_PACKET')) {
    if (-not $independentReviewQuestion.Contains($required)) {
        throw "Independent research methodology question missing: $required"
    }
}
foreach ($required in @(
    'review_mode=PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW',
    'review_scope=one_exact_advisory_candidate_only',
    'portfolio_ranking=forbidden',
    'FORMAL_OBJECT_AND_ASSUMPTIONS',
    'ESTIMAND_AND_IDENTIFICATION',
    'SIMPLE_NULL_OR_EQUIVALENCE',
    'IDENTIFYING_TOY',
    'CONSTRUCTIVE_CORRECTIONS_AND_INSPIRATION',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET')) {
    if (-not $independentConstructiveQuestion.Contains($required)) {
        throw "Independent constructive review question missing: $required"
    }
}
foreach ($required in @(
    'review_mode=PRO_ADVERSARIAL_SCIENTIFIC_REVIEW',
    'constructive_correction_disposition_required=true',
    'not a closure-only check',
    'CONFOUNDS_AND_LEAKAGE',
    'CAPACITY_AND_OPTIMIZER_EXPOSURE',
    'PARTNER_COADAPTATION_AND_GAME_EFFECTS',
    'DIRECTION_DISPOSITION',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET')) {
    if (-not $independentAdversarialQuestion.Contains($required)) {
        throw "Independent adversarial review question missing: $required"
    }
}
foreach ($retired in @(
    '.agents/skills/hmasd-independent-research-pro-review/references/21_DIRECTION_SCIENTIFIC_AUDIT.md',
    '.agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Retired persistent direction-review surface remains: $retired"
    }
}
foreach ($required in @(
    'role=independent_research_explorer',
    'model=gpt-5.6-sol',
    'reasoning_effort=ultra',
    'canonical_scientific_authority=none',
    'research_state_change_authority=direct_user_in_explorer_task_only',
    'wdm_ops_scientific_command_effect=none',
    'external_pro_packet_effect=advisory_input_under_user_authorized_workflow',
    'write_scope=local_research_except_pro_reviews',
    'current_work_read=forbidden',
    'local_research_single_writer=true',
    'local_research_write_tool=apply_patch_only',
    'local_research_shell_mutation=forbidden',
    'logical_assignment_count=derived_from_exact_work_roster',
    'runtime_concurrency=available_native_capacity',
    'phase_barrier=required',
    'completion_order_priority=forbidden',
    'research_modes=evidence_review|algorithm_inspiration_campaign|candidate_validation',
    'automatic_campaign_progression=allowed_until_convergence_within_authorized_boundary',
    'unbounded_source_expansion=forbidden',
    'methodology_reference=research-methodology.md_required_for_candidate_validation',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_target_settings=locked_role_session_model_thinking',
    'cross_task_route_cache=forbidden',
    'independent_pro_direction_packet_intake=exact_native_child_final_only',
    'independent_pro_direction_packet_effect=advisory_revision_only',
    'independent_pro_direction_transport_child=hmasd-independent-research-review-operator',
    'independent_pro_direction_transport_concurrency=one_active_child_per_binding',
    'independent_pro_constructive_adversarial_barrier=required',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET',
    'returns one native final',
    'Only that new version may support a',
    'research architect, portfolio integrator and only',
    'SOURCE_ABSORPTION_BRIEF',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'new_mechanism',
    'subdirection_split',
    'cross_direction_inspiration',
    'PARTIAL_CAMPAIGN_RESOURCE_BOUND')) {
    if (-not $independentResearchRole.Contains($required)) {
        throw "Independent Research Explorer role missing: $required"
    }
}
foreach ($required in @(
    'A session is an address, not authority.',
    'Only a direct user instruction in the Independent Research Explorer task may change',
    'research_state_effect=none',
    'control-plane reload notice or mechanical receipt',
    'mechanical nonconformance',
    'verbatim External Pro advisory gap',
    'Direction review is a native-child final to Explorer',
    'ROUTE_AUTHORITY_MISMATCH')) {
    if (-not $crossTaskRoutingNormalized.Contains($required)) {
        throw "Cross-task routing research-authority boundary missing: $required"
    }
}
if ($crossTaskRoutingNormalized.Contains('user-requested read-only factual query')) {
    throw 'Cross-task routing improperly grants WDM an Explorer factual-query route'
}
$operationsRoleNormalized = $operationsRole -replace '\s+', ' '
foreach ($forbidden in @(
    'Request one `EXPLORER_ADVISORY_REFINEMENT_PACKET`',
    'Supply the bounded gap and allowed source boundary')) {
    if ($operationsRoleNormalized.Contains($forbidden)) {
        throw "Operations role improperly grants research-driving authority: $forbidden"
    }
}
foreach ($required in @(
    'The cross-task routing Skill is the single source for WDM-to-Explorer output.',
    'The cross-task routing Skill is the single source for Operations-to-Explorer output.',
    'The cross-task routing Skill is the single source for non-authoritative inputs',
    'Explorer may make autonomous transitions inside that exact authorization.',
    'Operations neither requests refinement nor defines its source boundary.')) {
    $allAuthoritySurfaces = "$workflowDesignManagerRoleNormalized $operationsRoleNormalized $($independentResearchRole -replace '\s+', ' ')"
    if (-not $allAuthoritySurfaces.Contains($required)) {
        throw "Independent-research role boundary missing: $required"
    }
}
foreach ($pair in @(
    @{ Text=$researchScoutRole; Required=@(
        'callable_agent_type=hmasd-research-scout',
        'model=gpt-5.6-sol',
        'reasoning_effort=high',
        'write_authority=none',
        'child_authority=none',
        'research_modes=evidence_review|algorithm_inspiration_campaign',
        'SOURCE_RESULT_PACKET',
        'json_content_layer_required=true',
        'pdf_verification_on_fidelity_boundary=true') },
    @{ Text=$researchInnovatorRole; Required=@(
        'callable_agent_type=hmasd-research-innovator',
        'model=gpt-5.6-sol',
        'reasoning_effort=max',
        'write_authority=none',
        'child_authority=none',
        'research_modes=algorithm_inspiration_campaign|candidate_validation',
        'inspiration_purposes=adapt|combine|develop|refine|split|challenge_dependency',
        'initial_favored_direction_visibility=withheld',
        'methodology_reference=required_for_candidate_validation_only',
        'conclusion_forcing=forbidden',
        'ALGORITHM_INSPIRATION_PACKET') },
    @{ Text=$researchCriticRole; Required=@(
        'callable_agent_type=hmasd-research-critic',
        'model=gpt-5.6-sol',
        'reasoning_effort=max',
        'write_authority=none',
        'child_authority=none',
        'research_modes=evidence_review|algorithm_inspiration_campaign|candidate_validation',
        'principles_analysis_precedes_campaign_criticism=true',
        'formal_proof_requirement=forbidden_for_algorithm_inspiration_campaign',
        'portfolio_selection_authority=none',
        'RL_PRINCIPLE_ANALYSIS_PACKET') },
    @{ Text=$researchPrinciplesRole; Required=@(
        'callable_agent_type=hmasd-research-principles-analyst',
        'model=gpt-5.6-sol',
        'reasoning_effort=max',
        'write_authority=none',
        'child_authority=none',
        'review_nature=constructive_not_adversarial',
        'RL_PRINCIPLE_ANALYSIS_PACKET',
        'exploration and exploitation drivers',
        'posterior-collapse risk') })) {
    foreach ($required in $pair.Required) {
        if (-not $pair.Text.Contains($required)) {
            throw "Independent research child role missing: $required"
        }
    }
}
foreach ($authority in @(
    'C:/Projects/Inst-sci/AGENTS.md',
    'C:/Projects/Inst-sci/papers/AGENTS.md',
    'llm-index/INSTRUCTIONS.md')) {
    if (-not $researchScoutRole.Contains($authority) -or
        -not $researchInnovatorRole.Contains($authority) -or
        -not $researchCriticRole.Contains($authority)) {
        throw "Independent research child authority load missing: $authority"
    }
}
foreach ($required in @(
    'docs/project/ALGORITHM_PRINCIPLES.md sections 1 and 3',
    'metadata/integrity.json',
    'structured JSON is the formal LLM content layer',
    'PDF is required for original verification, formula/figure/table semantics, or missing JSON',
    'legacy Markdown is excluded',
    'SOURCE_RESULT_PACKET',
    'ALGORITHM_INSPIRATION_PACKET',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'CRITIC_ASSESSMENT_PACKET',
    'evidence review',
    'algorithm inspiration campaign',
    'candidate validation',
    'NEXT_CYCLE_OPPORTUNITY_MAP',
    'delete|retain|add',
    '`--output` is forbidden in this route',
    'new_mechanism',
    'transfer',
    'combination',
    'important_correction',
    'subdirection_split',
    'cross_direction_inspiration',
    'available native capacity',
    'PARTIAL_CAMPAIGN_RESOURCE_BOUND',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET',
    'not an automatic campaign phase',
    'hmasd-independent-research-review-operator',
    'no persistent Operator handoff',
    'Explorer, not the child or completion order',
    'local_research')) {
    if (-not $independentResearchSkill.Contains($required)) {
        throw "Independent research Skill missing: $required"
    }
}
foreach ($required in @(
    'llm-index/catalog.v2.jsonl',
    'metadata/v2/papers.v2.jsonl',
    'metadata/v2/schema.v2.json',
    'quality-report.v2.json',
    'quality.grade',
    'quality.warnings',
    'provenance.field_evidence',
    'abstract_only',
    'Empty arrays and `unspecified` remain unknown')) {
    if (-not $independentResearchSkill.Contains($required) -and
        -not $independentResearchMyLib.Contains($required)) {
        throw "Independent research Metadata v2 contract missing: $required"
    }
}
foreach ($required in @(
    'logical_assignment_count=derived_from_exact_work_roster',
    'runtime_concurrency=available_native_capacity',
    'merge_barrier=required',
    'completion_order_priority=forbidden',
    'single_writer=independent_research_explorer',
    'automatic_campaign_progression=allowed_until_convergence',
    'first_innovation_roster_independence_shielding=required',
    'later_cycle_collaboration_brief=required',
    'SOURCE_RESULT_PACKET',
    'SOURCE_ABSORPTION_BRIEF',
    'ALGORITHM_INSPIRATION_PACKET',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'Constructive principles review',
    'Adversarial review',
    'Next-cycle opportunity map',
    'Resource exhaustion is partial',
    'automatic_formal_workflow_promotion=forbidden')) {
    if (-not $parallelResearch.Contains($required)) {
        throw "Parallel research workflow missing: $required"
    }
}
foreach ($required in @(
    'campaign_unit=one_broad_research_direction',
    'source_first=true',
    'fixed_first_wave_count=forbidden',
    'source_result',
    'transferable_primitive',
    'adaptation_hypothesis',
    'algorithm_candidate',
    'information-theoretic',
    'posterior collapse',
    'NEXT_CYCLE_OPPORTUNITY_MAP',
    'new_mechanism',
    'transfer',
    'combination',
    'important_correction',
    'subdirection_split',
    'cross_direction_inspiration')) {
    if (-not $openInspiration.Contains($required)) {
        throw "Open algorithm inspiration workflow missing: $required"
    }
}
foreach ($required in @(
    'MRM-01_OBJECT_BEFORE_MECHANISM',
    'MRM-02_DECOMPOSE_MEMBERSHIP_NONSTATIONARITY',
    'MRM-03_EXPLICIT_IDENTITY_AND_OWNERSHIP',
    'MRM-04_SEMI_MARKOV_CLOCK_DISCIPLINE',
    'MRM-05_STRATEGIC_POLICY_DEPENDENCE',
    'MRM-06_ESTIMAND_FIRST',
    'MRM-07_STRONGEST_SIMPLE_NULL',
    'MRM-08_FAIL_CLOSED_MODULE_ADMISSION',
    'MRM-09_COUNTEREXAMPLE_BEFORE_ESCALATION',
    'MRM-10_IDENTIFYING_TOYS_AND_CONTROLS',
    'MRM-11_INDEPENDENCE_WITH_PROVENANCE',
    'MRM-12_PROPAGATE_CORRECTIONS_WITHOUT_FORCING_CONVERGENCE',
    'MRM-13_BOUND_EVIDENCE_AND_DEPLOYMENT_COMPLEXITY',
    'MRM-14_INTERPRET_THE_SMALLEST_PROPOSITION',
    'provenance.cross_pollination_edges',
    'scope.partner_policy_population',
    '`stop_condition`',
    'mechanical_schema_validity_is_not_scientific_truth=true')) {
    if (-not $researchMethodology.Contains($required)) {
        throw "Independent research methodology missing: $required"
    }
}
foreach ($forbidden in @(
    'additional_wave_user_confirmation=required_per_wave',
    'automatic_additional_wave=forbidden',
    'user_confirmation_fingerprint')) {
    foreach ($surface in @(
        $independentResearchRole,
        $independentResearchSkill,
        $parallelResearch,
        $researchMethodology)) {
        if ($surface.Contains($forbidden)) {
            throw "Independent research retains stale per-wave control: $forbidden"
        }
    }
}
foreach ($forbidden in @(
    'scientific_innovation',
    'SCOUT_EVIDENCE_PACKET',
    'research_scout_parallel_limit',
    'research_innovator_parallel_limit',
    'research_critic_parallel_limit',
    'max_cohorts',
    'unique_winner')) {
    foreach ($surface in @(
        $independentResearchRole,
        $researchScoutRole,
        $researchInnovatorRole,
        $researchCriticRole,
        $researchPrinciplesRole,
        $independentResearchSkill,
        $parallelResearch,
        $openInspiration)) {
        if ($surface.Contains($forbidden)) {
            throw "Independent research retains stale closed-proof control: $forbidden"
        }
    }
}
foreach ($surface in @(
    $independentResearchRole,
    $researchScoutRole,
    $researchInnovatorRole,
    $researchCriticRole,
    $researchPrinciplesRole,
    $independentResearchSkill,
    $parallelResearch,
    $openInspiration)) {
    if ($surface -match '\bRESEARCH_DIRECTION_PACKET\b') {
        throw 'Independent research retains stale closed-proof RESEARCH_DIRECTION_PACKET'
    }
}
foreach ($forbidden in @(
    'Assume for purposes of this task that a complete affirmative proof exists',
    'Spend at least 8 hours',
    'up to 64 concurrent agents',
    'Return only when a complete affirmative proof has been found')) {
    foreach ($surface in @(
        $independentResearchRole,
        $researchInnovatorRole,
        $independentResearchSkill,
        $parallelResearch)) {
        if ($surface.Contains($forbidden)) {
            throw "Independent research imported conclusion-forcing CDC text: $forbidden"
        }
    }
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
    'workflow_gate_law=AGENTS.md#universal-project-constraints',
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
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only')) {
    if (-not $operationsRole.Contains($required)) { throw "Research Operations Manager role missing: $required" }
}
foreach ($forbidden in @(
    'review_assignment_acceptance=server_visible_exact_fence_only',
    'review_client_send_effect=uncommitted_until_server_visible')) {
    if ($operationsRole.Contains($forbidden)) {
        throw "Research Operations Manager retains stale attachment-blind transport: $forbidden"
    }
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
$complexity = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/EVIDENCE_COMPLEXITY_POLICY.md')

function ConvertTo-UniqueKeyMap([string]$Body, [string]$Scope) {
    $map = @{}
    foreach ($line in ($Body -split "`r?`n")) {
        if ($line -eq '') { continue }
        if ($line -notmatch '^([A-Za-z][A-Za-z0-9_]*)=(.*)$') { throw "$Scope has a non-key line: $line" }
        if ($map.ContainsKey($Matches[1])) { throw "$Scope repeats key: $($Matches[1])" }
        $map.Add($Matches[1], $Matches[2])
    }
    return $map
}
$lineCount = @($current -split "`r?`n").Count
if ($lineCount -gt 500) { throw "CURRENT_WORK exceeds 500 lines: $lineCount" }
$headerMatch = [regex]::Match($current, '(?ms)\A# HMASD Current Work Portfolio\r?\n\r?\n```text\r?\n(?<body>.*?)^```\r?$')
if (-not $headerMatch.Success) { throw 'CURRENT_WORK portfolio header fence is missing' }
$header = ConvertTo-UniqueKeyMap $headerMatch.Groups['body'].Value 'CURRENT_WORK header'
$parsedKeyCount = $header.Count
foreach ($key in @('document_kind', 'state_owner', 'state_updated', 'workstream_ids', 'independent_research_pointer_ids', 'legacy_snapshot')) {
    if (-not $header.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($header[$key])) { throw "CURRENT_WORK header missing: $key" }
}
if ($header['document_kind'] -ne 'current_work_portfolio' -or $header['state_owner'] -ne 'research_operations_manager') {
    throw 'CURRENT_WORK header identity is invalid'
}
$legacyPath = Join-Path $repo $header['legacy_snapshot']
if (-not (Test-Path -LiteralPath $legacyPath -PathType Leaf)) { throw 'CURRENT_WORK legacy snapshot is missing' }
$workstreamIds = @($header['workstream_ids'].Split('|') | Where-Object { $_ })
$workstreamMatches = [regex]::Matches($current, '(?ms)^## Workstream: (?<name>[a-z0-9_]+)\r?\n\r?\n```text\r?\n(?<body>.*?)^```\r?$')
if ($workstreamMatches.Count -ne $workstreamIds.Count) { throw 'CURRENT_WORK roster and workstream block counts differ' }
$workstreams = @{}
foreach ($match in $workstreamMatches) {
    $name = $match.Groups['name'].Value
    if ($workstreams.ContainsKey($name)) { throw "CURRENT_WORK repeats workstream: $name" }
    $record = ConvertTo-UniqueKeyMap $match.Groups['body'].Value "CURRENT_WORK workstream $name"
    foreach ($key in @('workstream_id', 'owner_role', 'status', 'active_assignment_id', 'next_boundary', 'environment', 'grant_or_authority_reference', 'current_evidence_pointer')) {
        if (-not $record.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($record[$key])) { throw "CURRENT_WORK workstream $name missing: $key" }
    }
    if ($record['workstream_id'] -ne $name -or $record['owner_role'] -ne 'research_operations_manager') { throw "CURRENT_WORK workstream identity mismatch: $name" }
    $workstreams[$name] = $record
    $parsedKeyCount += $record.Count
}
foreach ($name in $workstreamIds) {
    if (-not $workstreams.ContainsKey($name)) { throw "CURRENT_WORK roster has no block: $name" }
}
if ([regex]::Matches($current, '(?m)^active_assignment_id=').Count -ne $workstreamIds.Count -or
    [regex]::Matches($current, '(?m)^next_boundary=').Count -ne $workstreamIds.Count) {
    throw 'CURRENT_WORK current assignment keys are not unique within the roster'
}
$formal = $workstreams['formal_toy_research']
foreach ($key in @('grant_iterations_authorized', 'grant_iterations_remaining', 'conclusion_bearing_iterations_consumed_total')) {
    if (-not $formal.ContainsKey($key) -or $formal[$key] -notmatch '^\d+$') { throw "CURRENT_WORK formal grant is invalid: $key" }
}
if ([int]$formal['grant_iterations_remaining'] -gt [int]$formal['grant_iterations_authorized']) {
    throw 'CURRENT_WORK formal grant remaining exceeds authorization'
}
$pointerMatches = [regex]::Matches($current, '(?ms)^## Independent research pointer: (?<name>[a-z0-9_]+)\r?\n\r?\n```text\r?\n(?<body>.*?)^```\r?$')
$pointerIds = @($header['independent_research_pointer_ids'].Split('|') | Where-Object { $_ })
if ($pointerMatches.Count -ne $pointerIds.Count) { throw 'CURRENT_WORK pointer roster and block counts differ' }
foreach ($match in $pointerMatches) {
    $record = ConvertTo-UniqueKeyMap $match.Groups['body'].Value "CURRENT_WORK pointer $($match.Groups['name'].Value)"
    if ($record['pointer_id'] -ne $match.Groups['name'].Value -or $record['project_state_replication'] -ne 'forbidden') {
        throw 'CURRENT_WORK independent research pointer duplicates owned state'
    }
    $parsedKeyCount += $record.Count
}
$allKeyLineCount = [regex]::Matches($current, '(?m)^[A-Za-z][A-Za-z0-9_]*=.*$').Count
if ($allKeyLineCount -ne $parsedKeyCount) {
    throw 'CURRENT_WORK contains key-bearing state outside a registered current record'
}
if ($current -match '(?im)^## .*mechanically recorded|authoritative .*override') {
    throw 'CURRENT_WORK contains appended historical state'
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
    'cross_task_target_settings=locked_role_session_model_thinking',
    'passes the locked target session, model and thinking',
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
    'independent_research_scientific_command_authority=none',
    'independent_research_contract_encoding=direct_user_confirmed_text_only',
    'independent_research_cross_task_output=control_plane_reload_or_mechanical_receipt_only',
    'code_authority=none',
    'code_acceptance_authority=none',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=exact_fixed_requester_role_session',
    'cross_task_target_settings=locked_role_session_model_thinking',
    'cross_task_route_cache=forbidden',
    'resolves the requester''s locked session, model and thinking',
    'never an automatic acceptance gate',
    'workflow_collaboration_skill=hmasd-collaborative-workflow-design',
    'workflow_collaboration_scope=all_mutating_workflow_design',
    'workflow_zero_question_path=fully_specified_mutations',
    'workflow_decision_question_condition=changes_named_plan_field',
    'workflow_plan_confirmation=required_before_mutation',
    'workflow_read_only_plan_confirmation=not_required',
    'workflow_material_plan_drift=reconfirmation_required',
    'workflow_collaboration_runtime_authority=none',
    'workflow_design_mechanical_guarantee_scope=irreversible_external_actions_only', 'workflow_design_retry_recoverable_failure_mechanism=forbidden', 'workflow_design_single_mechanism_line_budget=100', 'workflow_design_single_mechanism_terminal_state_budget=3', 'workflow_design_new_mechanism_requires_named_deletion=true', 'workflow_design_net_line_growth_default=negative_or_zero', 'workflow_design_incident_to_mechanism_promotion_threshold=2_recurrences', 'workflow_design_single_incident_response=root_cause_fix_plus_note_only', 'workflow_design_rule_single_source=one_defining_file_others_point', 'workflow_design_role_file_rule_duplication=forbidden', 'workflow_design_sha256_whitelist=archived_response_integrity_only', 'workflow_design_recovery_path_line_share=must_not_exceed_normal_path',
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
    'current_work_structure=dynamic_workstream_portfolio',
    'current_work_key_uniqueness=within_each_workstream',
    'current_work_history_storage=git_named_evidence_reports_ledgers_and_legacy_snapshot',
    'current_work_independent_explorer=pointer_only_no_state_replication',
    'scientific_authority=none',
    'independent_research_scientific_command_authority=none',
    'independent_research_cross_task_output=mechanical_nonconformance_or_verbatim_pro_gap_only',
    'code_acceptance_authority=none',
    'Research Operations Manager may request a workflow-design change directly',
    'cross_task_routing_skill=hmasd-cross-task-routing',
    'cross_task_target_identity=fixed_router_role_session',
    'cross_task_target_settings=locked_role_session_model_thinking',
    'passes the locked target session, model and thinking',
    'review_transport_operational_error=automatic_safe_recovery',
    'review_transport_blocked=only_after_safe_recovery_exhausted_and_irreversible_risk_remains',
    'review_transport_misclassification_correction=append_only')) {
    if (-not $operationsRole.Contains($required)) {
        throw "Research Operations Manager role missing: $required"
    }
}
if (-not $operationsRole.Contains('handoff_document_write_trigger=explicit_user_request_only')) {
    throw 'Research Operations Manager role permits automatic handoff writing'
}
if (-not $operationsRole.Contains('handoff_document_absence_blocks_progress=false')) {
    throw 'Optional handoff document is incorrectly treated as a progress gate'
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
    'INDEPENDENT_RESEARCH_METHODOLOGY_AUDIT',
    'PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW',
    'PRO_ADVERSARIAL_SCIENTIFIC_REVIEW',
    'independent_research_constructive_adversarial_barrier=explorer_new_advisory_version_required',
    'Other candidate records, the full portfolio',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET',
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

$consumed = [int]$formal['conclusion_bearing_iterations_consumed_total']
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
