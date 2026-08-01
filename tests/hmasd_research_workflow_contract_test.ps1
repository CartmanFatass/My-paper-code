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
    'INDEPENDENT_RESEARCH_EXPLORER.md',
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
$proRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_PRO.md')
$workflowAudit = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-workflow-change-audit/SKILL.md')
$workflowCollaboration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md')
$workflowCollaborationNormalized = $workflowCollaboration -replace '\s+', ' '
$workflowCollaborationUi = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/agents/openai.yaml')
$independentResearchRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$independentReviewRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md')
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
$agentifyTransportScript = Get-Content -Raw -LiteralPath $agentifyTransportScriptPath
$agentifyTransportContract = Get-Content -Raw -LiteralPath $agentifyTransportContractPath
$agentifyTransportContractNormalized = $agentifyTransportContract -replace '\s+', ' '
$independentReviewQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/20_PRO_OPEN_QUESTION.md')
$independentDirectionQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/21_DIRECTION_SCIENTIFIC_AUDIT.md')
$directionReviewBuilder = Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py'
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
    @($operationsRole, 'review_transport_backend_selection=exactly_one_backend_before_submission'),
    @($operationsRole, 'review_browser_contract_scope=transport_backend_browser_only'),
    @($operationsRole, 'review_transport_agentify_formal_stable_key=hmasd-formal-pro'),
    @($operationsRole, 'review_transport_agentify_explorer_validation_stable_key=hmasd-explorer-validation-pro'),
    @($operationsRole, 'review_transport_agentify_monitor=forbidden'),
    @($independentReviewRole, 'review_transport_agentify_stable_key=hmasd-independent-research-pro'),
    @($independentReviewRole, 'review_transport_agentify_monitor=forbidden'),
    @($independentReviewSkill, '$hmasd-agentify-pro-transport'),
    @($agentifyTransportSkill, 'transport_backend'),
    @($agentifyTransportSkill, 'transport_owner'),
    @($agentifyTransportSkill, 'assignment_identity'),
    @($agentifyTransportSkill, 'prompt_sha256'),
    @($agentifyTransportSkill, 'timeout_ms'),
    @($agentifyTransportContractNormalized, 'agentify_required_commit=917c5328695b4546e8c7e548878b00a07f45af91'),
    @($agentifyTransportContractNormalized, 'runtime-only'),
    @($agentifyTransportContractNormalized, 'TRANSPORT_BACKEND.json'),
    @($agentifyTransportContractNormalized, 'sourceDirty'),
    @($agentifyTransportContractNormalized, 'Retiring the browser monitor or its sentinel is a separate workflow change'),
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
foreach ($required in @(
    'independent_research_canonical_scientific_authority=none',
    'independent_research_explorer_write_scope=local_research_except_pro_reviews',
    'independent_research_review_operator_transport_authority=exclusive_for_user_authorized_independent_research_review',
    'independent_research_review_operator_write_scope=local_research/pro_reviews_plus_registered_cross_task_handoff_helper',
    'independent_research_review_operator_formal_workflow_authority=none',
    '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md',
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
    'review_scope=explicit_user_authorized_methodology_or_ordered_independent_research_direction_batch',
    'formal_workflow_authority=none',
    'scientific_authority=none',
    'git_authority=none',
    'browser_authority=one_separate_registered_external_pro_conversation',
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
    'registered direction-input builder',
    '22_DIRECTION_INPUT.md',
    'copy one completed exact packet to `temp/handoffs/`')) {
    if (-not $independentReviewRole.Contains($required)) {
        throw "Independent Research Review Operator write boundary missing: $required"
    }
}
foreach ($required in @(
    'registered Independent Research Pro Review Operator',
    'local_research/pro_reviews/',
    'INDEPENDENT_RESEARCH_METHODOLOGY_AUDIT',
    'INDEPENDENT_RESEARCH_DIRECTION_AUDIT',
    'one browser-only `hmasd-pro-response-monitor`',
    'complete response verbatim',
    '60_METHODOLOGY_PACKET.md',
    '60_DIRECTION_PACKET.md',
    'build_direction_review_input.py build',
    'build_direction_review_input.py batch-plan',
    'build_direction_review_input.py batch-next',
    '--batch-manifest',
    'instruction authorizes that immutable list',
    'At most one batch item',
    '90_TERMINAL_BLOCKER.json',
    'it never treats local research paths as a',
    'Independent Research Explorer',
    'Workflow Design Manager')) {
    if (-not $independentReviewSkill.Contains($required)) {
        throw "Independent research Pro-review Skill missing: $required"
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
    'review_mode=INDEPENDENT_RESEARCH_DIRECTION_AUDIT',
    'review_scope=one_exact_advisory_candidate_only',
    'portfolio_ranking=forbidden',
    'global_winner_selection=forbidden',
    'DIRECTION_DISPOSITION',
    'MECHANISM_CAUSAL_PATH',
    'RL_MARL_DRIVER',
    'IDENTIFICATION_AND_CONTROLS',
    'SOURCE_TO_MECHANISM_BOUNDARY',
    'INTERFACE_DEPENDENCIES',
    'VALIDATION_CONTRACT',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET')) {
    if (-not $independentDirectionQuestion.Contains($required)) {
        throw "Independent research direction question missing: $required"
    }
}
if (-not (Test-Path -LiteralPath $directionReviewBuilder -PathType Leaf)) {
    throw 'Independent research direction packet builder is missing'
}
$directionBuilderResult = & 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' $directionReviewBuilder self-test
if ($LASTEXITCODE -ne 0 -or $directionBuilderResult -notcontains 'HMASD_DIRECTION_REVIEW_PACKAGER_SELF_TEST_OK') {
    throw "Independent direction packet builder self-test failed: $directionBuilderResult"
}
if ($directionBuilderResult -notcontains 'HMASD_DIRECTION_REVIEW_BATCH_SELF_TEST_OK') {
    throw "Independent direction batch self-test failed: $directionBuilderResult"
}
foreach ($required in @(
    'role=independent_research_explorer',
    'model=gpt-5.6-sol',
    'reasoning_effort=ultra',
    'canonical_scientific_authority=none',
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
    'independent_pro_direction_packet_intake=exact_verified_handoff_only',
    'independent_pro_direction_packet_effect=advisory_revision_only',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET',
    'one user-authorized ordered batch',
    'select or reorder the',
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
    'immutable manifest controls audit order',
    'select the next audit',
    'Never infer a',
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
    'review_assignment_acceptance=server_visible_main_body_or_verified_attachment_identity',
    'review_assignment_identity_sources=main_body_exact_fence|verified_attachment_payload',
    'review_assignment_attachment_validator=.agents/skills/hmasd-review-round/scripts/verify_assignment_attachment_identity.py',
    'review_assignment_attachment_filename_authority=none',
    'review_assignment_attachment_unreadable=IDENTITY_UNREADABLE',
    'review_assignment_observation_fields=client_send_consumed|main_body_fence_visible|attachment_identity_verified|assistant_generation_started|natural_completion_verified',
    'review_client_send_effect=uncommitted_until_assignment_identity_verified',
    'review_unpersisted_assignment_recovery=once_same_conversation_exact_assignment_replay',
    'review_unpersisted_assignment_recovery_eligible=reload_then_exact_url_reopen_both_show_zero_matching_fence',
    'review_unpersisted_assignment_recovery_prior_server_visible_count=zero',
    'review_unpersisted_assignment_recovery_client_send_limit=2_assignment_sends_total',
    'review_unpersisted_assignment_recovery_scientific_iteration_cost=zero',
    'review_post_error_persistence_recheck=once_observe_only_after_unpersisted_assignment_terminal',
    'review_post_error_persistence_recheck_send_authority=none',
    'review_post_error_persistence_recheck_observations=exact_url_history_plus_registered_conversation_search',
    'review_post_error_persistence_recheck_success=exactly_one_full_fence',
    'review_post_error_persistence_recheck_zero=REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT',
    'review_post_error_persistence_recheck_uncertain=REVIEW_TRANSPORT_BLOCKED',
    'review_post_error_persistence_recheck_monitor_before_fence=forbidden',
    'review_post_error_persistence_recheck_scientific_iteration_cost=zero',
    'review_user_authorized_assignment_send=once_after_closed_unpersisted_assignment',
    'review_user_authorized_assignment_send_authority=direct_user_only',
    'review_user_authorized_assignment_send_package=reuse_exact_existing_package',
    'review_user_authorized_assignment_send_presend=exact_url_plus_registered_search_both_zero',
    'review_user_authorized_assignment_send_count=one',
    'review_user_authorized_assignment_send_postsend=one_snapshot_no_reload',
    'review_user_authorized_assignment_send_automatic_recovery=forbidden',
    'review_user_authorized_assignment_send_zero=REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED',
    'review_user_authorized_assignment_send_uncertain=REVIEW_TRANSPORT_BLOCKED',
    'review_user_authorized_assignment_send_monitor_before_fence=forbidden',
    'review_user_authorized_assignment_send_scientific_iteration_cost=zero',
    'review_user_authorized_assignment_resend=once_after_closed_user_authorized_send',
    'review_user_authorized_assignment_resend_authority=direct_user_only',
    'review_user_authorized_assignment_resend_package=reuse_exact_existing_package',
    'review_user_authorized_assignment_resend_presend=exact_url_plus_registered_search_both_zero',
    'review_user_authorized_assignment_resend_count=one',
    'review_user_authorized_assignment_resend_postsend=one_snapshot_no_reload',
    'review_user_authorized_assignment_resend_automatic_recovery=forbidden',
    'review_user_authorized_assignment_resend_zero=REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_RESEND_UNPERSISTED',
    'review_user_authorized_assignment_resend_uncertain=REVIEW_TRANSPORT_BLOCKED',
    'review_user_authorized_assignment_resend_monitor_before_fence=forbidden',
    'review_user_authorized_assignment_resend_terminal_callback=one_local_ops_return',
    'review_user_authorized_assignment_resend_pending_callback=forbidden',
    'review_user_authorized_assignment_resend_scientific_iteration_cost=zero',
    'review_response_retry=once_same_conversation_after_terminal_attempt',
    'review_response_retry_eligible=format_nonconforming_or_no_response_after_exhausted_recovery',
    'review_response_retry_requires_server_visible_original_fence=true',
    'review_response_retry_unproven_persistence=forbidden',
    'review_response_retry_submission_limit=2_total',
    'review_response_retry_scientific_iteration_cost=zero',
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
    'cross_task_target_settings=locked_role_session_model_thinking',
    'passes the locked target session, model and thinking',
    'review_monitor_assignment=one_mechanical_receipt_per_sentinel',
    'review_monitor_watch_call_limit_seconds=45',
    'review_monitor_total_response_deadline=none',
    'review_monitor_watch_expiry=PENDING',
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
    'INDEPENDENT_RESEARCH_DIRECTION_AUDIT',
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
foreach ($required in @(
    'callable_agent_type=hmasd-pro-response-monitor',
    'observation_mode=registered_transport_owner_brokered_jsonl_sentinel',
    'browser_authority=none',
    'progress_notifications=forbidden',
    '--assignment-receipt <absolute-receipt-json>',
    'not the Pro response deadline',
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
