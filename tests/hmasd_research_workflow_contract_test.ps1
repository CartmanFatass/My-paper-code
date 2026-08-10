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
    'hmasd-explorer-project-validation',
    'hmasd-agentify-transport',
    'hmasd-independent-research-exploration',
    'hmasd-independent-research-pro-review',
    'hmasd-workflow-change-audit') | Sort-Object
foreach ($required in $requiredSkills) {
    if ($required -notin $skills) { throw "Missing routed workflow Skill: $required" }
}

$roles = @(Get-ChildItem (Join-Path $repo '.agents/roles') -File -Filter '*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedRoles = @(
    'AGENTIFY_TRANSPORT_OPERATOR.md',
    'CPM_MECHANICAL_OPERATOR.md',
    'CODE_SCOUT.md',
    'EXPERIMENT_OPERATOR.md',
    'EXTERNAL_PRO.md',
    'IMPLEMENTER.md',
    'CODE_PROJECT_MANAGER.md',
    'INDEPENDENT_RESEARCH_EXPLORER.md',
    'RESEARCH_CRITIC.md',
    'RESEARCH_INNOVATOR.md',
    'RESEARCH_PRINCIPLES_ANALYST.md',
    'RESEARCH_SCOUT.md',
    'REVIEWER.md',
    'VERIFIER.md',
    'WORKFLOW_AUDITOR.md',
    'WORKFLOW_DESIGN_MANAGER.md',
    'WORKFLOW_IMPLEMENTER.md',
    'WORKFLOW_REVIEWER.md',
    'EXPLORER_MECHANICAL_OPERATOR.md') | Sort-Object
if (Compare-Object $expectedRoles $roles) {
    throw "Unexpected active role set: $($roles -join ',')"
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$agileNormalized = $agile -replace '\s+', ' '
$codePmRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$codePmRoleNormalized = $codePmRole -replace '\s+', ' '
$codexConfig = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$workflowDesignManagerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$workflowDesignManagerRoleNormalized = $workflowDesignManagerRole -replace '\s+', ' '
$proRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/EXTERNAL_PRO.md')
$proRoleNormalized = $proRole -replace '\s+', ' '
$workflowAudit = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-workflow-change-audit/SKILL.md')
$workflowAuditNormalized = $workflowAudit -replace '\s+', ' '
$workflowCollaboration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md')
$workflowCollaborationNormalized = $workflowCollaboration -replace '\s+', ' '
$workflowCollaborationUi = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-collaborative-workflow-design/agents/openai.yaml')
$workflowMapPath = Join-Path $repo 'docs/project/WORKFLOW_MAP.md'
if (-not (Test-Path -LiteralPath $workflowMapPath -PathType Leaf)) {
    throw 'Workflow Map pointer target is missing'
}
$workflowMap = Get-Content -Raw -LiteralPath $workflowMapPath
$workflowMapNormalized = $workflowMap -replace '\s+', ' '
$sessionWorkspaceContract = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SESSION_WORKSPACE_CONTRACT.md')
$sessionWorkspaceContractNormalized = $sessionWorkspaceContract -replace '\s+', ' '
$independentResearchRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$researchScoutRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_SCOUT.md')
$researchCriticRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_CRITIC.md')
$researchInnovatorRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_INNOVATOR.md')
$researchPrinciplesRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md')
$independentResearchSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/SKILL.md')
$explorerValidationSkillPath = Join-Path $repo '.agents/skills/hmasd-explorer-project-validation/SKILL.md'
$explorerValidationSkill = Get-Content -Raw -LiteralPath $explorerValidationSkillPath
$explorerValidationSkillNormalized = $explorerValidationSkill -replace '\s+', ' '
$retiredExplorerValidationScriptPath = Join-Path $repo '.agents/skills/hmasd-explorer-project-validation/scripts/explorer_project_packet.py'
$retiredExplorerValidationTestPath = Join-Path $repo 'tests/hmasd_explorer_project_validation_packet_test.py'
$explorerValidationContractPath = Join-Path $repo 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
$explorerValidationContract = Get-Content -Raw -LiteralPath $explorerValidationContractPath
$explorerValidationContractNormalized = $explorerValidationContract -replace '\s+', ' '
$agentifyTransportProfilePath = Join-Path $repo '.codex/agents/hmasd-agentify-transport.toml'
if (-not (Test-Path -LiteralPath $agentifyTransportProfilePath -PathType Leaf)) {
    throw 'Registered Agentify transport child profile is missing'
}
$agentifyTransportProfile = Get-Content -Raw -LiteralPath $agentifyTransportProfilePath
$explorerMechanicalProfilePath = Join-Path $repo '.codex/agents/hmasd-explorer-mechanical.toml'
$explorerMechanicalRolePath = Join-Path $repo '.agents/roles/EXPLORER_MECHANICAL_OPERATOR.md'
$explorerMechanicalSkillPath = Join-Path $repo '.agents/skills/hmasd-explorer-mechanical/SKILL.md'
foreach ($requiredPath in @($explorerMechanicalProfilePath, $explorerMechanicalRolePath, $explorerMechanicalSkillPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Explorer Mechanical surface is missing: $requiredPath"
    }
}
$explorerMechanicalProfile = Get-Content -Raw -LiteralPath $explorerMechanicalProfilePath
$explorerMechanicalRole = Get-Content -Raw -LiteralPath $explorerMechanicalRolePath
$explorerMechanicalSkill = Get-Content -Raw -LiteralPath $explorerMechanicalSkillPath
$algorithmPrinciples = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/ALGORITHM_PRINCIPLES.md')
$algorithmPrinciplesNormalized = $algorithmPrinciples -replace '\s+', ' '
$publicHandoffContractPath = Join-Path $repo 'docs/project/handoffs/README.md'
$publicHandoffContract = Get-Content -Raw -LiteralPath $publicHandoffContractPath
$publicHandoffContractNormalized = $publicHandoffContract -replace '\s+', ' '
$independentResearchMyLib = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/mylib.md')
$parallelResearch = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md')
$openInspiration = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/open-algorithm-inspiration.md')
$researchMethodology = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/references/research-methodology.md')
$independentReviewSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$independentReviewQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/20_PRO_OPEN_QUESTION.md')
$independentConstructiveQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/21_DIRECTION_CONSTRUCTIVE_REVIEW.md')
$independentAdversarialQuestion = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/references/21_DIRECTION_ADVERSARIAL_REVIEW.md')
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$assertionNormalized = $assertion -replace '\s+', ' '
$handoffPath = Join-Path $repo 'docs/project/RESTART_HANDOFF.md'
$handoff = if (Test-Path -LiteralPath $handoffPath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $handoffPath
} else {
    $null
}

$directionBindingTerms = @(
    'direction-specific Explorer answer',
    'selected direction identity',
    'smallest set of canonical',
    'parent, child or cross-direction',
    'preloading or merging the whole portfolio',
    'candidate and exact current proposition',
    'source/evidence revision boundary',
    'explicit exclusion of sibling-direction generalization',
    'one requested action and its direct consumer',
    'completion evidence',
    'CPM''s reverse result begins with its conclusion',
    'mirrors that same primary direction or explicitly named direction set',
    'Codex-native message fallback carries the same binding',
    'preserves the original handoff/artifact',
    'asks exactly one concrete semantic clarification',
    'duplicate decision records')

if (-not (Test-Path -LiteralPath $explorerValidationSkillPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $explorerValidationContractPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $publicHandoffContractPath -PathType Leaf)) {
    throw 'Explorer semantic handoff Skill/contract coupling is missing'
}
if ((Test-Path -LiteralPath $retiredExplorerValidationScriptPath) -or
    (Test-Path -LiteralPath $retiredExplorerValidationTestPath)) {
    throw 'Retired Explorer packet admission script/test remains'
}
$independentResearchSkillNormalized = $independentResearchSkill -replace '\s+', ' '
$independentReviewSkillNormalized = $independentReviewSkill -replace '\s+', ' '
$independentResearchRoleNormalized = $independentResearchRole -replace '\s+', ' '
$agentifyTransportProfileNormalized = $agentifyTransportProfile -replace '\s+', ' '
$agentifyTransportSkillPath = Join-Path $repo '.agents/skills/hmasd-agentify-transport/SKILL.md'
if (-not (Test-Path -LiteralPath $agentifyTransportSkillPath -PathType Leaf)) {
    throw 'Agentify transport Skill is missing'
}
$agentifyTransportSkill = Get-Content -Raw -LiteralPath $agentifyTransportSkillPath
$agentifyTransportSkillNormalized = $agentifyTransportSkill -replace '\s+', ' '

# Requester roles/Skills own conversation meaning; transport realizes that brief
# and keeps only operational page/tab judgment.
foreach ($entry in @(
    @($agileNormalized, 'CPM owns the per-question conversation intent.'),
    @($agileNormalized, 'clean start versus one exact continuation URL'),
    @($agileNormalized, 'permitted concurrency versus required independence'),
    @($agileNormalized, 'public remote URL'),
    @($codePmRoleNormalized, 'CPM preserves conversation meaning and performs mechanical intake.'),
    @($independentReviewSkillNormalized, 'one self-contained natural-language context brief that states for each question'),
    @($independentReviewSkillNormalized, 'Explorer alone decides whether prior memory helps or contaminates the requested judgment'),
    @($agentifyTransportSkillNormalized, 'Follow those requested relationships; do not infer scientific direction, review independence, contamination risk, future reuse or grouping'),
    @($agentifyTransportSkillNormalized, 'Requester-authorized independent conversations may perform these steps concurrently on separate owned tabs'),
    @($agentifyTransportSkillNormalized, 'write result rows in the original `question_paths` order'),
    @($agentifyTransportSkillNormalized, 'Never close the default tab, a pre-existing/unowned tab, or a tab with an active answer.'),
    @($agentifyTransportSkillNormalized, 'never guess or silently substitute another conversation')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Conversation authority/capability contract missing: $($entry[1])"
    }
}
foreach ($retired in @(
    'Choose session continuity from the task itself',
    'Start a clean conversation for an independent review; reuse the matching conversation'
)) {
    if ($agentifyTransportSkillNormalized.Contains($retired)) {
        throw "Transport retains requester-owned conversation choice: $retired"
    }
}
foreach ($required in @(
    'temp/handoffs/explorer_to_code_manager/',
    'temp/handoffs/code_manager_to_explorer/',
    'requires no Git operation',
    'semantic writing aids, not required field names',
    'bounded safe read-only reconnaissance',
    'not a packet validator, dispatcher, queue engine or state machine',
    'Known concerns are context for judgment, not mandatory headings or an expected verdict',
    'CPM may process independent direction-local candidates concurrently')) {
    if (-not $explorerValidationSkillNormalized.Contains($required)) {
        throw "Explorer semantic handoff Skill missing: $required"
    }
}
foreach ($entry in @(
    @($codePmRole, 'explorer_toy_assignment_intake=semantic_treatment_brief_or_explicit_pro_frozen_review'),
    @($codePmRole, 'explorer_public_handoff_intake=semantic_judgment_after_bounded_read_only_reconnaissance'),
    @($independentResearchRole, 'public_handoff_outbound=temp/handoffs/explorer_to_code_manager/'),
    @($independentResearchRole, 'public_handoff_git_authority=none'),
    @($independentResearchRole, 'project_validation_instruction_authority=authorize_cpm_named_treatment_execution'),
    @($independentResearchRole, 'project_validation_read_authority=project_wide_read_only_as_needed'),
    @($independentResearchRole, 'project_validation_semantic_acceptance_owner=external_pro'),
    @($independentResearchRole, 'project_validation_acceptance_review_request_and_intake=exclusive_for_explorer_origin'),
    @($independentResearchRole, 'project_validation_acceptance_review_mode=CODE_SCIENCE_ALIGNMENT_AUDIT'),
    @($independentResearchRole, 'project_validation_acceptance_review_timing=after_cpm_technical_acceptance_push_and_remote_locator_return_when_named_pro_trigger'),
    @($independentResearchRole, 'project_validation_alignment_packet_effect=authoritative_scientific_semantic_acceptance'),
    @($codePmRole, 'explorer_treatment_substitution_authority=none'),
    @($codePmRole, 'explorer_task_instruction_intake=execute_named_treatment_without_extra_confirmation'),
    @($codePmRole, 'explorer_result_semantic_acceptance_owner=external_pro'),
    @($codePmRole, 'explorer_acceptance_review_request_authority=none'),
    @($codePmRole, 'explorer_result_remote_evidence=exact_pushed_commit_and_public_github_locators'),
    @($codePmRole, 'explorer_acceptance_review_route=explorer_to_agentify_after_cpm_technical_acceptance'),
    @($independentResearchRole, 'project_toy_compute_authority=none'),
    @($proRole, 'semantically sufficient public candidate brief'),
    @($proRoleNormalized, 'Code Project Manager archives the answer exactly and returns a conclusion-first, evidence-second brief through its outbound temporary handoff'),
    @($proRole, 'EXPLORER_TOY_DESIGN_ASSERTION_AUDIT'),
    @($proRole, 'EXPLORER_TOY_RESULT_SCIENTIFIC_DISPOSITION'),
    @($proRole, 'TOY_CONTRACT_FROZEN|ADVISORY_REFINEMENT_REQUIRED|PARK_CANDIDATE'),
    @($explorerValidationContract, 'current_work_mutation=forbidden'),
    @($explorerValidationContractNormalized, 'order is work organization rather than queue state'),
    @($explorerValidationContractNormalized, 'Missing formatting or a prior mechanical BLOCKED receipt is not candidate evidence'),
    @($explorerValidationContractNormalized, 'Explorer gives one clear instruction naming implementation, instance binding'),
    @($explorerValidationContractNormalized, 'without separate code or experiment permission fields'),
    @($explorerValidationContractNormalized, 'does not reject a handoff because of formatting or a missing object'),
    @($explorerValidationContractNormalized, 'instead of creating a `BLOCKED` state'),
    @($explorerValidationContractNormalized, 'External Pro uses the GitHub connection to inspect the exact pushed revision'),
    @($explorerValidationContractNormalized, 'Explorer never substitutes its own acceptance'),
    @($explorerValidationContractNormalized, 'Ordinary B iteration may continue as advisory research without automatic Pro review'),
    @($proRole, 'cannot consume a formal iteration, update the CDC portfolio'),
    @($explorerValidationSkillNormalized, 'does not update the CDC portfolio'),
    @($explorerValidationSkill, 'current_work_mutation=forbidden'),
    @($explorerValidationContract, 'consumes no formal iteration'),
    @($explorerValidationContractNormalized, 'Candidate evidence, run roots, artifacts and results remain candidate-specific'),
    @($publicHandoffContractNormalized, 'A missing schema, `document_kind`, validator receipt, hash, byte count or fingerprint is never a blocker'),
    @($publicHandoffContractNormalized, 'begins with its natural-language conclusion and then appends the necessary exact evidence')) ) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Explorer project-validation role/contract coupling missing: $($entry[1])"
    }
}

$scientificOnlyNormalized = $explorerValidationContract -replace '\s+', ' '
foreach ($required in @(
    'mechanically verified packet',
    'does not recompute schema, readability, receipts, activity counts, locators',
    'scientifically ambiguous',
    'supported proposition',
    'strongest alternative explanation',
    'information gain',
    'next discriminator',
    'A/B/C or named-Pro action',
    'one canonical scientific decision record',
    'existing `local_research/` ownership',
    'Portfolio, index, README and continuity',
    'pointer, navigation',
    'mandatory packet schema or validator admission gate',
    'ordinary B',
    'named Pro triggers')) {
    if (-not $scientificOnlyNormalized.Contains($required)) {
        throw "Explorer scientific-only intake definition missing: $required"
    }
}
$scientificOnlyPointer = 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
foreach ($surface in @(
    $independentResearchRole,
    $explorerValidationSkill,
    $independentResearchSkill,
    $parallelResearch,
    $publicHandoffContract)) {
    if (-not $surface.Contains($scientificOnlyPointer)) {
        throw 'Explorer scientific-only intake surface does not point to the single definition'
    }
}
foreach ($required in @(
    'project_validation_intake_boundary=scientific_only_after_cpm_technical_acceptance',
    'project_validation_packet_dependency=cpm_technical_acceptance_and_mechanically_verified_packet',
    'project_validation_technical_recompute=forbidden_unless_scientifically_ambiguous',
    'project_validation_technical_facts_not_recomputed=schema|readability|receipts|activity_counts|locators|retry|technical_consistency',
    'canonical_scientific_decision_record=one_per_candidate_under_existing_local_research_ownership',
    'portfolio_index_readme_continuity_role=pointer_navigation_barrier_only')) {
    if (-not $independentResearchRole.Contains($required)) {
        throw "Explorer role scientific-only key missing: $required"
    }
}
foreach ($entry in @(
    @($independentResearchRole, 'runtime_authority=none'),
    @($independentResearchRole, 'agentify_transport_child=hmasd-agentify-transport'),
    @($independentResearchRole, 'agentify_transport_parent=independent_research_explorer'),
    @($independentResearchRole, 'agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT'),
    @($independentResearchRole, 'agentify_transport_assignment_fields=batch_path|results_path'),
    @($independentResearchRole, 'agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT'),
    @($independentResearchRole, 'agentify_transport_result_fields=status|results_path|error'),
    @($independentResearchRole, 'agentify_transport_terminal_status=COMPLETE|ERROR'),
    @($independentResearchRole, 'agentify_transport_wait_visibility=silent_until_terminal_native_final'),
    @($independentResearchRole, 'root_explorer_state_retention=direction_pointer|dependency|compact_returned_conclusion|sole_canonical_intake_and_decision|cpm_readiness'),
    @($independentResearchRole, 'independent_pro_review_result_path_guard=.agents/skills/hmasd-agentify-transport/scripts/hmasd_agentify_result_path_guard.py'),
    @($independentResearchRole, 'independent_pro_review_result_guard_timing=after_terminal_before_read'),
    @($independentResearchRole, 'independent_pro_review_result_guard_failure=reject_actual_error_no_fallback'),
    @($independentResearchRole, 'independent_pro_review_transport_execution=registered_agentify_transport_child'),
    @($independentReviewSkillNormalized, 'provider|context_path|question_paths'),
    @($independentResearchSkillNormalized, 'registered `hmasd-agentify-transport` child'),
    @($independentReviewSkillNormalized, 'fork_turns=none'),
    @($independentReviewSkillNormalized, 'AGENTIFY_REVIEW_BATCH_ASSIGNMENT'),
    @($independentReviewSkillNormalized, 'batch_path|results_path'),
    @($independentReviewSkillNormalized, 'silent while live'),
    @($independentReviewSkillNormalized, 'exactly once through its native final response'),
    @($independentReviewSkillNormalized, 'status|results_path|error'),
    @($independentReviewSkillNormalized, 'terminal status `COMPLETE|ERROR`'),
    @($independentReviewSkillNormalized, 'no polling, progress handling or parent-task result relay'),
    @($independentReviewSkillNormalized, 'hmasd_agentify_result_path_guard.py'),
    @($independentReviewSkillNormalized, 'returned terminal anchor'),
    @($independentReviewSkillNormalized, 'do not infer a fallback path'),
    @($independentReviewSkillNormalized, 'registered `hmasd-agentify-transport` child'),
    @($independentReviewSkillNormalized, 'AGENTIFY_REVIEW_BATCH_ASSIGNMENT'),
    @($independentReviewSkillNormalized, 'batch_path|results_path'),
    @($independentReviewSkillNormalized, 'silent while live'),
    @($independentReviewSkillNormalized, 'exactly once through its native final response'),
    @($independentReviewSkillNormalized, 'status|results_path|error'),
    @($independentReviewSkillNormalized, 'terminal status `COMPLETE|ERROR`'),
    @($independentReviewSkillNormalized, 'no polling, progress handling or parent-task result relay'),
    @($agentifyTransportProfileNormalized, 'name = "hmasd-agentify-transport"'),
    @($agentifyTransportProfileNormalized, 'model = "gpt-5.6-luna"'),
    @($agentifyTransportProfileNormalized, 'model_reasoning_effort = "medium"')) ) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Explorer Agentify silent-child contract missing: $($entry[1])"
    }
}

foreach ($required in $directionBindingTerms) {
    if (-not $explorerValidationContractNormalized.Contains($required)) {
        throw "Direction-local Explorer/CPM binding missing from stable contract: $required"
    }
}
$directionBindingPointer = 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
foreach ($surface in @(
    $independentResearchRole,
    $explorerValidationSkill,
    $independentResearchSkill,
    $parallelResearch,
    $publicHandoffContract)) {
    if (-not $surface.Contains($directionBindingPointer)) {
        throw 'Direction-local context surface does not point to the stable contract'
    }
}

$explorerTransportSurfaces = @(
    $independentResearchRole,
    $independentResearchSkill,
    $independentReviewSkill,
    $explorerValidationSkill,
    $explorerValidationContract)
foreach ($stale in @(
    'return_task_id',
    'dedicated Agentify task',
    'dedicated transport task',
    'cross-task return',
    'AGENTIFY_REVIEW_BATCH_REQUEST')) {
    foreach ($surface in $explorerTransportSurfaces) {
        if ($surface.Contains($stale)) {
            throw "Retired Explorer Agentify transport wording remains: $stale"
        }
    }
}

# Keep this workflow-level test focused on positive ownership and isolation
# facts rather than a packet schema.
$explorerMechanicalIntegrated = ($null -ne $explorerMechanicalProfile) -and
    ($null -ne $explorerMechanicalRole) -and
    ($null -ne $explorerMechanicalSkill) -and
    $agents.Contains('hmasd-explorer-mechanical') -and
    $independentResearchRole.Contains('hmasd-explorer-mechanical') -and
    $independentResearchSkill.Contains('hmasd-explorer-mechanical') -and
    $parallelResearch.Contains('hmasd-explorer-mechanical') -and
    $explorerValidationContract.Contains('hmasd-explorer-mechanical')
if (-not $explorerMechanicalIntegrated) {
    throw 'Explorer Mechanical integration is incomplete'
}
foreach ($required in @(
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'sandbox_mode = "read-only"',
    'approval_policy = "never"')) {
    if (-not $explorerMechanicalProfile.Contains($required)) {
        throw "Explorer Mechanical profile integration missing: $required"
    }
}
foreach ($required in @(
    'explorer_mechanical_task=literal_fact_organization_only',
    'explorer_mechanical_write_authority=none',
    'explorer_mechanical_scientific_authority=none',
    'explorer_mechanical_barrier=none',
    'research_state_effect=none')) {
    $surfaces = @(
        $independentResearchRole,
        $independentResearchSkill,
        $parallelResearch,
        $sessionWorkspaceContract,
        $workflowMap,
        $explorerValidationContract)
    if (-not (($surfaces -join " ").ToLowerInvariant().Contains($required.ToLowerInvariant()))) {
        throw "Explorer Mechanical integration fact missing: $required"
    }
}
foreach ($required in @(
    'role=explorer_mechanical_operator',
    'parent=independent_research_explorer',
    'write_authority=none',
    'scientific_authority=none')) {
    if (-not (($explorerMechanicalRole -replace '\s+', ' ').Contains($required))) {
        throw "Explorer Mechanical Role integration missing: $required"
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
    'workflow_design_owner=workflow_design_manager',
    'workflow_design_charter=WORKFLOW_DESIGN_MANAGER.md',
    'docs/project/CURRENT_WORK.md',
    'docs/project/WORKFLOW_MAP.md',
    'workflow_design_manager_workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_design_manager_workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_design_manager_workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_design_manager_git_authority=exclusive_for_workflow_control_plane_surfaces',
    'persistent_session_workflow_design_authority=none',
    'persistent_session_workflow_acceptance_authority=none',
    'persistent_session_workflow_git_authority=none',
    'workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace',
    'workflow_child_parent=workflow_design_manager',
    'workflow_child_acceptance_authority=none',
    'session_workspace_contract=docs/project/SESSION_WORKSPACE_CONTRACT.md',
    'workflow_design_manager_workflow_runtime_authority=none',
    'workflow_design_manager_current_work_authority=public_index_and_own_workflow_control_plane_records_only',
    'workflow_design_manager_git_authority=exclusive_for_workflow_control_plane_surfaces',
    'workflow_design_manager_external_review_runtime_authority=none',
    'workflow_design_manager_experiment_runtime_authority=none',
    'code_project_manager_code_authority=exclusive',
    'code_project_manager_technical_acceptance_authority=exclusive',
    'code_project_manager_runtime_authority=exclusive',
    'code_project_manager_current_work_authority=exclusive',
    'code_project_manager_formal_external_review_request_and_intake_authority=exclusive',
    'code_project_manager_experiment_dispatch_and_result_routing=exclusive',
    'external_pro_scientific_authority=exclusive_within_user_goal_and_review_boundary',
    'hmasd-collaborative-workflow-design',
    'workflow_change_skill=hmasd-workflow-change-audit',
    'project_write_scope=current_checkout_plus_verified_ticket_worktree',
    'external_workspace_access=read_only',
    'cross_task_transport=codex_native_send_message_to_thread',
    'same_file_concurrent_writes=forbidden',
    '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($retired in @(
    'cross_task_routing=',
    'cross_task_routing_skill=',
    'workflow_design_manager_session=',
    'code_project_manager_session=',
    'independent_research_explorer_session=')) {
    if ($agents.Contains($retired)) { throw "AGENTS retains retired fixed routing: $retired" }
}
foreach ($required in @(
    '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md',
    'hmasd-independent-research-exploration',
    'hmasd-independent-research-pro-review')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing routed pointer: $required" }
}
foreach ($required in @(
    'owns both independent-research direction reviews and methodology',
    'Copy each named successful raw response',
    'Workflow Design Manager',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET')) {
    if (-not $independentReviewSkill.Contains($required)) {
        throw "Independent research Pro-review Skill missing: $required"
    }
}
foreach ($required in @(
    'invoked only by the persistent `INDEPENDENT_RESEARCH_EXPLORER`',
    'there is no separate persistent review-operator session',
    'local_research/pro_reviews/<review-id>/',
    'PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW',
    'PRO_ADVERSARIAL_SCIENTIFIC_REVIEW',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET',
    'Copy each named successful raw response')) {
    if (-not $independentReviewSkill.Contains($required)) {
        throw "Independent research Pro-review Skill missing direct Explorer contract: $required"
    }
}
foreach ($forbidden in @('60_DIRECTION_PACKET.md')) {
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
    '.agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py',
    '.agents/roles/INDEPENDENT_RESEARCH_DIRECTION_REVIEW_OPERATOR.md',
    '.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md',
    '.agents/roles/PROJECT_OPERATIONS_OPERATOR.md',
    '.codex/agents/hmasd-independent-research-review-operator.toml',
    '.codex/agents/hmasd-project-operations-operator.toml')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Retired persistent direction-review surface remains: $retired"
    }
}
foreach ($staleRegistration in @(
    'HMASDIndependentResearchReviewOperator',
    'hmasd-independent-research-review-operator.toml',
    'HMASDProjectOperationsOperator',
    'hmasd-project-operations-operator.toml')) {
    if ($codexConfig.Contains($staleRegistration)) {
        throw "Retired direction-review profile remains registered: $staleRegistration"
    }
}
foreach ($required in @(
    'role=independent_research_explorer',
    'model=gpt-5.6-sol',
    'reasoning_effort=ultra',
    'canonical_scientific_authority=none',
    'research_state_change_authority=direct_user_in_explorer_task_only',
    'wdm_cpm_scientific_command_effect=none',
    'external_pro_packet_effect=advisory_input_under_user_authorized_workflow',
    'write_scope=local_research_including_explorer_owned_pro_reviews|temp/handoffs/explorer_to_code_manager/',
    'public_handoff_outbound=temp/handoffs/explorer_to_code_manager/',
    'public_handoff_inbound_read=temp/handoffs/code_manager_to_explorer/',
    'public_handoff_git_authority=none',
    'public_handoff_admission=semantic_judgment_no_mandatory_schema',
    'project_validation_instruction_authority=authorize_cpm_named_treatment_execution',
    'current_work_read=read_only_as_needed_for_project_validation',
    'local_research_single_writer=true',
    'local_research_write_tool=apply_patch_only',
    'local_research_shell_mutation=forbidden',
    'logical_assignment_count=derived_from_exact_work_roster',
    'runtime_concurrency=three_unit_cpm_capacity_pool',
    'resource_consuming_experiment_action=capacity_controlled_per_direction',
    'active_experiment_roster_owner=independent_research_explorer_scientific_view',
    'runtime_capacity_admission_owner=code_project_manager',
    'independent_ready_treatment_dispatch=parallel_first_within_capacity',
    'read_only_science_lane_capacity=independent_of_cpm_pool_by_default',
    'science_barrier_condition=exact_question_depends_on_unreturned_cpm_result_only',
    'cpm_dispatch_constraints=exact_scientific_or_dependency_predecessor|capacity_or_admission|formal_or_observed_resource_conflict|same_mutable_path_or_object_conflict',
    'persistent_explorer_progress=event_driven_or_user_resumed',
    'global_serial_fallback=forbidden_without_named_dependency_or_resource_evidence',
    'per_direction_result_bearing_default=one_active',
    'same_direction_parallelism=exact_frozen_joint_roster_only',
    'experiment_pool_exclusive_runtime=B_HEAVY_OR_C',
    'capacity_wait_effect=pending_runtime_capacity_only_not_blocked',
    'read_only_scientific_analysis_parallelism=available_native_capacity',
    'canonical_phase_barrier=required_for_algorithm_inspiration_campaign_only',
    'adaptive_question_dispatch=bounded_registered_child_consultation',
    'adaptive_question_barrier=none_for_singleton|exact_local_roster_only_when_joint',
    'adaptive_question_result_effect=consultation_only',
    'completion_order_priority=forbidden',
    'research_modes=evidence_review|algorithm_inspiration_campaign|candidate_validation',
    'automatic_campaign_progression=allowed_until_convergence_within_authorized_boundary',
    'per_review_user_authorization=not_required_inside_active_grant',
    'wdm_campaign_approval=none',
    'unbounded_source_expansion=forbidden',
    'methodology_reference=research-methodology.md_required_for_C_or_named_science_review_trigger',
    'research_child_dispatch=registered_child_type|fork_turns=none|self_contained_natural_language_assignment',
    'research_child_assignment_context=research_purpose|exact_question|named_sources_and_prerequisite_packets|protected_assumptions_and_independence|exclusions|permitted_local_judgment|completion_meaning',
    'cross_task_transport=codex_native_send_message_to_thread',
    'cross_task_target=current_thread_id_from_user_or_native_task_context',
    'cross_task_model_and_thinking_overrides=omit',
    'independent_pro_direction_packet_effect=advisory_revision_only',
    'independent_pro_review_assignment_prefixes=IR_DIRECTION_REVIEW:|IR_METHODOLOGY_REVIEW:',
    'independent_pro_review_item_root=local_research/pro_reviews/<review-id>/',
    'independent_pro_review_request_and_intake_authority=exclusive_for_explorer_direction_and_methodology_reviews',
    'independent_pro_review_terminal_intake=exact_archived_response_fifo',
    'independent_pro_direction_packet=INDEPENDENT_RESEARCH_DIRECTION_PACKET',
    'independent_pro_direction_shared_page_registry=forbidden',
    'independent_pro_constructive_adversarial_barrier=required',
    'INDEPENDENT_RESEARCH_DIRECTION_PACKET',
    'Only that new version may support a',
    'research architect, portfolio integrator and only')) {
    if (-not $independentResearchRole.Contains($required)) {
        throw "Independent Research Explorer role missing: $required"
    }
}
$independentResearchProcedure = "$independentResearchSkill $parallelResearch $independentResearchMyLib $openInspiration $researchMethodology"
$independentResearchProcedureNormalized = $independentResearchProcedure -replace '\s+', ' '
foreach ($required in @(
    'SOURCE_ABSORPTION_BRIEF',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'new_mechanism',
    'subdirection_split',
    'cross_direction_inspiration')) {
    if (-not $independentResearchProcedure.Contains($required)) {
        throw "Independent Research Explorer procedure missing: $required"
    }
}

# Adaptive scientific delegation is a bounded consultation capability layered
# inside the existing Explorer grant; it is not a campaign phase or a new
# portfolio-gate mode.
$adaptiveRoleNormalized = $independentResearchRole -replace '\s+', ' '
$adaptiveSkillNormalized = $independentResearchSkill -replace '\s+', ' '
$adaptiveParallelNormalized = $parallelResearch -replace '\s+', ' '
foreach ($required in @(
    'one clear, bounded, decision-relevant question',
    'expected information gain exceeds dispatch and synthesis cost',
    'no code, runtime, write, technical acceptance or formal scientific acceptance',
    'If evidence is sufficient and the next step is cheap and reversible, Explorer decides directly.',
    'The child result is consultation only',
    'Explorer remains the portfolio integrator and writes exactly one canonical scientific decision',
    'First-round children see neither peer answers nor a favored answer',
    'completion order is not evidence priority',
    'disagreement is not voting',
    'no fixed panel, quorum, concurrency requirement, every-B review or automatic Pro review',
    'sole recovery is one low-cost retry with the identical question and source boundary',
    'These adaptive consultations do not alter the campaign phase barriers or the existing External Pro triggers.')) {
    if (-not $adaptiveRoleNormalized.Contains($required)) {
        throw "Explorer adaptive consultation contract missing: $required"
    }
}
foreach ($required in @(
    'Adaptive scientific question dispatch (not a fourth research mode)',
    'matching registered read-only research child',
    'information gain, next discriminator or selected A/B/C or named-Pro action',
    'one child capability is a clear match',
    'expected gain exceeds dispatch and synthesis cost',
    'When evidence is sufficient and the next step is cheap and reversible, Explorer decides directly.',
    'not a fourth research mode or an automatic pipeline',
    'A child answer is advisory input to one Explorer decision',
    'Canonical campaign rosters, ordered barriers and single-writer authority remain unchanged.',
    'best-matching registered read-only research child',
    'The root retains only the direction pointer, exact dependency, compact returned conclusion and CPM readiness')) {
    if (-not $adaptiveSkillNormalized.Contains($required)) {
        throw "Independent research adaptive Skill contract missing: $required"
    }
}
foreach ($required in @(
    'adaptive_question_roster=singleton_or_exact_joint_roster',
    'adaptive_singleton_global_barrier=none',
    'adaptive_joint_local_merge_barrier=only_when_every_named_answer_is_necessary',
    'adaptive_first_round_peer_reading=forbidden',
    'There is no fixed adaptive count, concurrency, quorum, every-B panel, automatic-Pro path or persistent mechanism.',
    'Preserve disagreements as advisory inputs; never vote or collapse them into a quorum.',
    'The Explorer remains the single writer and integrates answers into one decision.',
    'runtime_capacity_units_total=3',
    'B_TOY_LIGHT:1|B_TOY_MEDIUM:2|B_HEAVY_OR_C:3_exclusive',
    'experiment_pool_exclusivity_scope=result_bearing_runtime_only',
    'workflow_progress_during_exclusive_runtime=continues',
    'three independent light treatments, or one medium plus one light',
    'one-shot observed CPU, memory and process facts',
    'CPM-supplied GPU/paid-service claims or conflicts',
    'CPM makes no external GPU/paid-service call or inference',
    'capacity_wait_state=pending_runtime_capacity_only',
    'capacity_wait_effect=pending_runtime_capacity_only',
    'Insufficient capacity is `pending_runtime_capacity`, never a direction, task or workflow `BLOCKED` state',
    'creates no queue engine, lease, dispatcher or acceptance owner',
    'Formal or explicitly heavy runtime may prevent another result-bearing experiment from starting, but it never pauses code work',
    'read-only research, scientific intake, External Pro review or another non-runtime action',
    'Every concurrent treatment has distinct direction/treatment identity, canonical design, CPM ticket/worktree, source freeze and accepted commit, run, evidence, checkpoint and result roots, seed/RNG namespace, temporary session paths, Operator receipt, readiness/technical-acceptance record and Explorer decision',
    'By default a direction has at most one result-bearing treatment active',
    'until that predecessor is terminal and Explorer completes the direction''s scientific intake',
    'freeze one exact joint roster before any member starts',
    'Completion order is never scientific priority, voting or a cross-direction barrier',
    'B completion or parallelism alone never does',
    'normal path for two or more scientifically selected and frozen independent treatments is parallel-first',
    'same mutable-path/object conflict',
    'Attribution, generic caution, completion order, convenience and a current sole action are not dependency or resource evidence',
    'exact scientific/dependency predecessor, capacity/admission, a formal or actually observed resource conflict, or a same mutable-path/object conflict',
    'Explorer progress is event-driven or user-resumed',
    'Read-only Explorer science lanes',
    'Strict methodology is scoped to conclusion-bearing C work or a named science-review trigger, not all candidate validation.')) {
    if (-not $adaptiveParallelNormalized.Contains($required)) {
        throw "Adaptive roster contract missing: $required"
    }
}

foreach ($stale in @(
    'heartbeat',
    'timed wake',
    'deadline stop',
    'at-most-one-new-treatment-per-turn',
    'one-new-treatment-per-heartbeat',
    'per-heartbeat')) {
    foreach ($surface in @($independentResearchRole, $independentResearchSkill, $parallelResearch,
        $codePmRole, $agile, $workflowMap, $publicHandoffContract)) {
        if (($surface -replace '\s+', ' ').ToLowerInvariant().Contains($stale.ToLowerInvariant())) {
            throw "Retired Explorer continuation wording remains: $stale"
        }
    }
}
foreach ($pair in @(
    @{ Text=$researchScoutRole; Required=@(
        'candidate_validation_scope=exact_source_terminology_metric_citation_counterevidence_or_evidence_boundary_fidelity') },
    @{ Text=$researchInnovatorRole; Required=@(
        'candidate_validation_capabilities=causal_hypothesis_construction|candidate_repair|separating_prediction|smallest_next_discriminator|outcome_pattern_decision_map|mechanism_simplification',
        'cannot recheck acceptance, start or schedule an experiment') },
    @{ Text=$researchPrinciplesRole; Required=@(
        'review_nature=constructive_not_adversarial',
        'without redoing technical acceptance or promoting a formal direction') },
    @{ Text=$researchCriticRole; Required=@(
        'criticism_modes=canonical_campaign|adaptive_bounded',
        'Only canonical campaign criticism requires that terminal',
        'Adaptive bounded criticism has no campaign-barrier effect') })) {
    foreach ($required in $pair.Required) {
        if (-not ($pair.Text -replace '\s+', ' ').Contains($required)) {
            throw "Adaptive child capability boundary missing: $required"
        }
    }
}
foreach ($required in @(
    'project_validation_technical_recompute=forbidden_unless_scientifically_ambiguous',
    'project_validation_technical_facts_not_recomputed=schema|readability|receipts|activity_counts|locators|retry|technical_consistency')) {
    if (-not $independentResearchRole.Contains($required)) {
        throw "Explorer accepted-result boundary missing: $required"
    }
}
foreach ($required in @(
    'does not recompute schema, readability, receipts, activity counts, locators',
    'necessary to one Explorer decision',
    'Several read-only questions may run in parallel',
    'one result-bearing experiment active per direction by default',
    'Independent ordinary A/B treatments from different directions may overlap',
    'exactly one CPM technical acceptance and one Explorer scientific intake',
    'ordinary B remains B and does not automatically invoke Pro',
    'consumes no formal iteration')) {
    if (-not $explorerValidationContractNormalized.Contains($required)) {
        throw "Explorer targeted-result intake boundary missing: $required"
    }
}
foreach ($required in @(
    'research_treatment_pro_trigger=direction_changing_or_material_ambiguity_or_final_alignment_or_conclusion_or_explicit_C_review_or_explicit_user_request',
    'without a Pro review on every iteration')) {
    if (-not ($independentResearchRole.Contains($required) -or $independentResearchSkillNormalized.Contains($required))) {
        throw "Existing External Pro trigger boundary missing: $required"
    }
}
foreach ($required in @(
    'not a state machine, queue or admission gate',
    'No timer, no periodic audit, no freshness checker and no registry drives')) {
    if (-not $workflowMapNormalized.Contains($required)) {
        throw "Workflow Map adaptive boundary missing: $required"
    }
}
$codePmRoleNormalized = $codePmRole -replace '\s+', ' '
foreach ($forbidden in @(
    'Request one `EXPLORER_ADVISORY_REFINEMENT_PACKET`',
    'Supply the bounded gap and allowed source boundary')) {
    if ($codePmRoleNormalized.Contains($forbidden)) {
        throw "CPM role improperly grants research-driving authority: $forbidden"
    }
}
foreach ($required in @(
    'Cross-task messages arrive through Codex-native `send_message_to_thread` with no model or thinking override',
    'Explorer may make autonomous transitions inside that exact authorization.',
    'Workflow Design Manager and Code Project Manager messages cannot initiate those transitions.')) {
    $allAuthoritySurfaces = "$workflowDesignManagerRoleNormalized $codePmRoleNormalized $($independentResearchRole -replace '\s+', ' ')"
    if (-not $allAuthoritySurfaces.Contains($required)) {
        throw "Independent-research role boundary missing: $required"
    }
}
foreach ($pair in @(
    @{ Text=$researchScoutRole; Required=@(
        'callable_agent_type=hmasd-research-scout',
        'model=gpt-5.6-sol',
        'reasoning_effort=high',
        'default_fork_turns=none',
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
        'default_fork_turns=none',
        'write_authority=none',
        'child_authority=none',
        'research_modes=algorithm_inspiration_campaign|candidate_validation',
        'inspiration_purposes=adapt|combine|develop|refine|split|challenge_dependency',
        'initial_favored_direction_visibility=withheld',
        'methodology_reference=required_for_C_or_named_science_review_trigger',
        'conclusion_forcing=forbidden',
        'ALGORITHM_INSPIRATION_PACKET') },
    @{ Text=$researchCriticRole; Required=@(
        'callable_agent_type=hmasd-research-critic',
        'model=gpt-5.6-sol',
        'reasoning_effort=max',
        'default_fork_turns=none',
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
        'default_fork_turns=none',
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
    'docs/project/ALGORITHM_PRINCIPLES.md',
    'references/mylib.md',
    'references/parallel-research-workflow.md',
    'hmasd-independent-research-pro-review',
    'hmasd-explorer-project-validation',
    'local_research',
    'Explorer route remains read-only (`--output` is forbidden)',
    'fork_turns="none"',
    'self-contained natural-language',
    'Parent conversation history is background only',
    'source and prerequisite-packet bindings',
    'allowed local judgment',
    'completion meaning',
    'not a mandatory schema, file, validator or admission gate')) {
    if (-not $independentResearchProcedureNormalized.Contains($required)) {
        throw "Independent research Skill missing: $required"
    }
}
foreach ($entry in @(
    @($independentResearchRole, 'research_treatment_levels=A_read_only_reconnaissance_or_nonintervening_probe|B_small_exploratory_real_toy_algorithm_experiment|C_conclusion_bearing_promotion_retirement_or_expensive_experiment'),
    @($independentResearchRole, 'methodology_reference=research-methodology.md_required_for_C_or_named_science_review_trigger'),
    @($independentResearchRole, 'research_treatment_pro_trigger=direction_changing_or_material_ambiguity_or_final_alignment_or_conclusion_or_explicit_C_review_or_explicit_user_request'),
    @($proRole, 'explorer_toy_review_timing=not_a_normal_B_precondition_or_per_iteration_review'),
    @($proRoleNormalized, 'A normal exploratory B iteration may proceed'),
    @($proRoleNormalized, 'real environment, policy, learner, trainer and evaluation runner calls'),
    @($proRoleNormalized, 'Ordinary B technical acceptance supplies no Pro input'),
    @($algorithmPrinciplesNormalized, 'Use the default loop `Conjecture -> minimum necessary derivation or counterexample -> real algorithm implementation -> environment experiment -> interpretation -> revision or retirement`'),
    @($algorithmPrinciplesNormalized, 'Explorer may interpret A/B observations only inside its advisory research state'),
    @($algorithmPrinciplesNormalized, 'External Pro owns scoped scientific acceptance and conclusion-bearing decisions when invoked'),
    @($algorithmPrinciplesNormalized, 'A — engineering/evidence reconnaissance or a read-only runtime probe'),
    @($algorithmPrinciplesNormalized, 'B — small exploratory toy algorithm experiment'),
    @($algorithmPrinciplesNormalized, 'C — conclusion-bearing, promotion/retirement or expensive experiment'),
    @($algorithmPrinciplesNormalized, 'fix the exact code revision, configuration, seeds and small budget cap'),
    @($algorithmPrinciplesNormalized, 'produce nonzero transitions, updates **and** evaluations'),
    @($algorithmPrinciplesNormalized, 'favorable adjusted run must not be presented as preregistered confirmation'),
    @($algorithmPrinciplesNormalized, 'judgment-guided questions, not required states'),
    @($algorithmPrinciplesNormalized, 'expense alone does not make its diagnostics conclusion-bearing'),
    @($algorithmPrinciplesNormalized, 'Before collecting or observing a run intended to support superiority'),
    @($algorithmPrinciplesNormalized, 'stop rule, budget, decision criterion'),
    @($algorithmPrinciplesNormalized, 'Do not rescue a valid conclusion-bearing C negative'),
    @($algorithmPrinciplesNormalized, 'alone, are neither an algorithm implementation nor an experiment'),
    @($explorerValidationContractNormalized, 'Ordinary B iteration may continue as advisory research without automatic Pro review'),
    @($explorerValidationContractNormalized, 'A B result shows real calls to the environment, policy, learner, trainer and evaluation runner'),
    @($explorerValidationContractNormalized, 'External Pro owns final scoped estimand, mechanism, sufficiency and result meaning when a C or other named review trigger is invoked'))) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Explorer proportional experiment surface missing: $($entry[1])"
    }
}
foreach ($entry in @(
    @($independentResearchSkillNormalized, 'it is not a prerequisite for ordinary B iteration'),
    @($independentResearchSkillNormalized, 'An in-grant direction review or bounded methodology audit is an explicit advisory trigger.'),
    @($independentResearchSkillNormalized, 'External Pro owns final scientific-semantic acceptance when invoked'))) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Explorer proportional Pro trigger missing: $($entry[1])"
    }
}
foreach ($required in @(
    'The proportional A/B/C evidence definitions live in `docs/project/ALGORITHM_PRINCIPLES.md`',
    'A is read-only engineering or runtime reconnaissance',
    'B is a small exploratory toy algorithm experiment',
    'C is conclusion-bearing, promotion/retirement or otherwise expensive work',
    'The strict methodology reference is for conclusion-bearing C work',
    'B normally means preparing a direct implementation/experiment handoff',
    'Additional fixture, census, enumerator, certificate or byte-stability work must name the unresolved result-relevant scientific question',
    'real toy environment, policy, learner, trainer and evaluation runner',
    'produce nonzero transitions, updates and evaluations',
    'Freeze the exact code revision, configuration, seeds and small budget for each concrete B run',
    'preserves every earlier result',
    'iterative pattern, not a state machine',
    'tests and truth tables alone do not qualify')) {
    if (-not $independentResearchSkillNormalized.Contains($required)) {
        throw "Independent research proportional experiment contract missing: $required"
    }
}
foreach ($required in @(
    'selected A/B/C treatment and one named action',
    'The detailed A/B/C definitions are maintained in `docs/project/ALGORITHM_PRINCIPLES.md`',
    'A is a read-only engineering/evidence reconnaissance or runtime probe',
    'one question, a named path, a non-intervention boundary and a fixed resource cap',
    'it cannot establish algorithm effect',
    'B is a small exploratory toy algorithm experiment',
    'candidate, matched comparator and an initial toy path',
    'Each concrete run fixes its exact code revision, configuration, seeds and small budget cap',
    'environment, policy, learner, trainer and evaluation runner',
    'nonzero transitions, updates and evaluations',
    'Tests, truth tables, enumerators, censuses, certificates and byte-stability checks alone are not B experiments',
    'C is conclusion-bearing, promotion/retirement or expensive work',
    'A conclusion-bearing C is the only treatment that requires the strict methodology',
    'expense alone does not give it terminal scientific meaning',
    'Missing support, unstable training, comparator equivalence and non-discrimination guide the next question',
    'A favorable adjusted run is not preregistered confirmation',
    'Ordinary B does not make a terminal support, promotion or retirement decision',
    'Introduce a sibling environment only when the scientific question independently requires it',
    'never design one backwards to make the candidate win',
    'current stage as `conjecture`, `derivation`, `algorithm implementation` or `experiment`',
    'real calls, transition, update and evaluation counts, observed result, strongest alternative explanation and next step',
    'A missing DTO, adapter, runner hook, observation or lifecycle object is an engineering implementation task for CPM',
    'Only a choice that changes the scientific question returns to Explorer',
    'Ordinary B iteration is nonformal and does not automatically initiate a Pro review',
    'direction-changing decision, material result ambiguity, final science alignment',
    'formal/conclusion-bearing C result')) {
    if (-not $explorerValidationSkillNormalized.Contains($required)) {
        throw "Explorer project-validation proportional experiment contract missing: $required"
    }
}
foreach ($entry in @(
    @($explorerValidationContractNormalized, 'Each named run fixes its exact code revision, configuration, seeds and small budget cap'),
    @($explorerValidationContractNormalized, 'nonzero transitions, updates and evaluations'),
    @($explorerValidationContractNormalized, 'every between-run adjustment with its reason'),
    @($explorerValidationContractNormalized, 'a common progression, not a required state machine'),
    @($explorerValidationContractNormalized, 'Full estimand, null/comparator, population, budget, stop-rule and decision-criterion freeze begins only for C'),
    @($explorerValidationContractNormalized, 'expense alone neither supplies terminal scientific meaning'))) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Explorer iterative B/C freeze boundary missing: $($entry[1])"
    }
}
if ($explorerValidationSkillNormalized.Contains(
        'After technical acceptance, CPM pushes the result and returns its exact commit plus public GitHub repository/path locators. Explorer may inspect project material read-only as needed, then freezes one')) {
    throw 'Explorer project-validation retains an unconditional post-technical-acceptance Pro rule'
}
foreach ($stale in @(
    'For ROM',
    'Operations-Manager-routed',
    'Operations-packaged',
    'Operations archives and routes',
    'wdm_ops_scientific_command_effect')) {
    if ($proRole.Contains($stale) -or
        $independentResearchRole.Contains($stale)) {
        throw "Retired ownership wording remains: $stale"
    }
}
$parallelResearchNormalized = $parallelResearch -replace '\s+', ' '
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
    'runtime_concurrency=three_unit_cpm_capacity_pool',
    'runtime_capacity_units_total=3',
    'active_experiment_roster_owner=independent_research_explorer_scientific_view',
    'runtime_capacity_admission_owner=code_project_manager',
    'cpm_dispatch_constraints=exact_scientific_or_dependency_predecessor|capacity_or_admission|formal_or_observed_resource_conflict|same_mutable_path_or_object_conflict',
    'read_only_science_lane_capacity=independent_of_cpm_pool_by_default',
    'science_barrier_condition=exact_question_depends_on_unreturned_cpm_result_only',
    'persistent_explorer_progress=event_driven_or_user_resumed',
    'canonical_campaign_phase_barriers=required',
    'adaptive_singleton_global_barrier=none',
    'adaptive_joint_local_merge_barrier=only_when_every_named_answer_is_necessary',
    'completion_order_priority=forbidden',
    'single_writer=independent_research_explorer',
    'automatic_campaign_progression=allowed_until_convergence',
    'first_innovation_roster_independence_shielding=required',
    'later_cycle_collaboration_brief=required',
    'research_child_default_fork_turns=none',
    'research_child_dispatch_contract=registered_agent_type|fork_turns="none"|self_contained_natural_language_assignment',
    'independent_direction_question_default=best_matching_registered_read_only_child|fork_turns="none"',
    'independent_direction_question_direct_root_exception=cheap_reversible_singleton_when_dispatch_overhead_exceeds_task',
    'cpm_accepted_result_interpretation=optional_direction_specific_read_only_child|technical_acceptance_not_repeated',
    'parent_conversation_history=background_only_not_task_authority',
    'SOURCE_RESULT_PACKET',
    'SOURCE_ABSORPTION_BRIEF',
    'ALGORITHM_INSPIRATION_PACKET',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'Constructive principles review',
    'Adversarial review',
    'Next-cycle opportunity map',
    'Resource exhaustion is partial',
    'automatic_formal_workflow_promotion=forbidden',
    'self-contained natural-language',
    'source and prerequisite-packet bindings',
    'completion meaning',
    'not a mandatory schema, assignment file, validator or admission gate')) {
    if (-not $parallelResearchNormalized.Contains($required)) {
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
foreach ($surface in @($agents, $codePmRole, $workflowDesignManagerRole, $independentResearchRole)) {
    if ($surface.Contains('pre_send_read_only_probe_explicit_echo')) {
        throw 'Persistent-role routing retains the unguarded explicit-echo contract'
    }
}

foreach ($required in @(
    'scientific_authority=none',
    'formal_compute_authority=user_only',
    '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md',
    '.agents/skills/hmasd-agentify-transport/SKILL.md',
    'CPM preserves conversation meaning and performs mechanical intake.')) {
    if (-not $codePmRoleNormalized.Contains($required)) { throw "Code Project Manager role missing: $required" }
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
    if (-not $proRoleNormalized.Contains($required)) { throw "External Pro role missing: $required" }
}
if ($codePmRole.Contains('portfolio_adjudication_authority=code_project_manager')) {
    throw 'Code Project Manager claims scientific portfolio adjudication'
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
if ($agileNormalized.Contains('External Review Operator') -or
    $agileNormalized.Contains('Project Operations Operator')) {
    throw 'Agile Skill retains a stale or ambiguous review route'
}
if (-not $agileNormalized.Contains('CODE_SCIENCE_ALIGNMENT_AUDIT') -or
    -not $agileNormalized.Contains('Agentify Transport Operator')) {
    throw 'Agile Skill does not route the code-science audit through Agentify transport'
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
if ($assertionNormalized.Contains('Research Operations Manager') -or
    $assertionNormalized.Contains('project-operations-operator') -or
    -not $assertionNormalized.Contains('opens one exact correction assignment') -or
    -not $assertionNormalized.Contains('After `CODE_ACCEPTED`')) {
    throw 'Assertion audit does not assign code repair to CPM'
}
if (-not $WorkflowDesignOnly -and
    ($plan.Contains('Research Operations Manager') -or
     $plan.Contains('project-operations-operator'))) {
    throw 'Implementation plan retains a retired transport or terminal route'
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
$complexity = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/EVIDENCE_COMPLEXITY_POLICY.md')

function Read-FencedRecord([string]$RelativePath, [string]$Scope) {
    $body = Get-Content -Raw -LiteralPath (Join-Path $repo $RelativePath)
    $match = [regex]::Match($body, '(?ms)```text\r?\n(?<body>.*?)^```\r?$')
    if (-not $match.Success) { throw "$Scope fenced record is missing" }
    $map = @{}
    foreach ($line in ($match.Groups['body'].Value -split "`r?`n")) {
        if ($line -eq '') { continue }
        if ($line -notmatch '^([A-Za-z][A-Za-z0-9_]*)=(.*)$') { throw "$Scope has a non-key line: $line" }
        if ($map.ContainsKey($Matches[1])) { throw "$Scope repeats key: $($Matches[1])" }
        $map.Add($Matches[1], $Matches[2])
    }
    return $map
}

$header = Read-FencedRecord 'docs/project/CURRENT_WORK.md' 'CURRENT_WORK index'
foreach ($key in @('document_kind', 'schema_version', 'index_owner', 'session_record_ids', 'common_record_ids', 'legacy_snapshot')) {
    if (-not $header.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($header[$key])) { throw "CURRENT_WORK index missing: $key" }
}
if ($header['document_kind'] -ne 'current_work_index' -or
    $header['index_owner'] -ne 'workflow_design_manager') {
    throw 'CURRENT_WORK index identity is invalid'
}
if (-not (Test-Path -LiteralPath (Join-Path $repo $header['legacy_snapshot']) -PathType Leaf)) {
    throw 'CURRENT_WORK legacy snapshot is missing'
}
foreach ($id in @($header['session_record_ids'].Split('|') | Where-Object { $_ })) {
    $record = Read-FencedRecord "docs/project/current-work/sessions/$id.md" "CURRENT_WORK session $id"
    if ($record['document_kind'] -ne 'current_work_session' -or $record['session_owner_role'] -ne $id) {
        throw "CURRENT_WORK session identity mismatch: $id"
    }
}
$common = @{}
foreach ($id in @($header['common_record_ids'].Split('|') | Where-Object { $_ })) {
    $record = Read-FencedRecord "docs/project/current-work/common/$id.md" "CURRENT_WORK common $id"
    if ($record['document_kind'] -ne 'current_work_common_record' -or $record['record_id'] -ne $id) {
        throw "CURRENT_WORK common identity mismatch: $id"
    }
    $common[$id] = $record
}
if ($common['workflow_control_plane']['owner_role'] -ne 'workflow_design_manager' -or
    $common['formal_toy_research']['owner_role'] -ne 'code_project_manager') {
    throw 'CURRENT_WORK partition ownership is invalid'
}
$formal = $common['formal_toy_research']
foreach ($key in @('grant_iterations_authorized', 'grant_iterations_remaining', 'conclusion_bearing_iterations_consumed_total')) {
    if (-not $formal.ContainsKey($key) -or $formal[$key] -notmatch '^\d+$') { throw "CURRENT_WORK formal grant is invalid: $key" }
}
if ([int]$formal['grant_iterations_remaining'] -gt [int]$formal['grant_iterations_authorized']) {
    throw 'CURRENT_WORK formal grant remaining exceeds authorization'
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
    'role_kind=persistent_project_coordination_code_runtime_and_acceptance_task',
    'code_authority=exclusive',
    'runtime_authority=exclusive',
    'current_work_authority=exclusive_for_project_operational_records',
    'formal_external_review_request_and_intake_authority=exclusive',
    'experiment_dispatch_and_result_routing=exclusive',
    'mechanical_result_acceptance=exclusive',
    'workflow_design_authority=none',
    'scientific_authority=none',
    'technical_acceptance_authority=exclusive',
    'experiment_child=hmasd-experiment-operator',
    'cross_task_transport=codex_native_send_message_to_thread',
    'cross_task_target=current_thread_id_from_user_or_native_task_context',
    'cross_task_model_and_thinking_overrides=omit',
    'passing no model or thinking override',
    'research_stage=EXPLORATION|FORMALIZATION',
    'code_change_shape=coherent_module_responsibility_with_focused_evidence',
    'shared_abstraction_justification=ownership_or_multiple_live_callers',
    'successor_replaces_predecessor=same_commit_delete_code_runner_direction_test',
    'coherent module responsibility, minimal public interfaces, directed dependencies, explicit state ownership, complexity isolation, change locality, preserved behavior and focused evidence',
    'Line and file statistics may be reported as optional diagnostics, but they cannot reject work, force arbitrary slicing or substitute for architecture review',
    'Extract a shared abstraction when it improves ownership or serves multiple live callers',
    'CODE_SCIENCE_INDEX.md',
    'CODE_ACCEPTED')) {
    if (-not $codePmRoleNormalized.Contains($required)) { throw "Code Project Manager role missing: $required" }
}

$retiredArchitectureGates = @(
    'small_' + 'active_line_only',
    'new_tracked_source_files_per_change<=' + '3',
    'refactor_' + 'active_line_delta<0',
    'new_mechanism_' + 'active_line_growth<=500',
    'existing_file_over_' + '1200_lines=must_not_grow',
    'active_' + 'line_delta=<added-minus-deleted>',
    'negative active-' + 'line delta',
    'at most 500 active ' + 'lines',
    'three tracked source files',
    'file already above 1200 ' + 'lines')
foreach ($surface in @($agents, $codePmRole, $agile)) {
    foreach ($retired in $retiredArchitectureGates) {
        if ($surface.Contains($retired)) {
            throw "Retired line/file acceptance gate remains: $retired"
        }
    }
}
foreach ($required in @(
    'role=workflow_design_manager',
    'role_kind=dedicated_persistent_central_workflow_design_authority_task',
    'workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_git_authority=exclusive_for_workflow_control_plane_surfaces',
    'public_workflow_session_record=docs/project/current-work/sessions/workflow_design_manager.md',
    'session_workspace=docs/session-workspaces/workflow_design_manager|temp/sessions/workflow_design_manager',
    'workflow_runtime_authority=none',
    'current_work_authority=public_index_and_own_workflow_control_plane_records_only',
    'external_review_runtime_authority=none',
    'experiment_runtime_authority=none',
    'scientific_authority=none',
    'independent_research_scientific_command_authority=none',
    'independent_research_contract_encoding=direct_user_confirmed_text_only',
    'independent_research_cross_task_output=control_plane_reload_or_mechanical_receipt_only',
    'code_authority=none',
    'code_acceptance_authority=none',
    'cross_task_transport=codex_native_send_message_to_thread',
    'cross_task_target=current_thread_id_from_user_or_native_task_context',
    'cross_task_model_and_thinking_overrides=omit',
    'not make WDM a code, runtime, scientific or per-operation approval gate',
    'workflow_collaboration_skill=hmasd-collaborative-workflow-design',
    'workflow_collaboration_scope=all_workflow_control_plane_mutations',
    'workflow_collaboration_runtime_authority=none',
    'routine_preimplementation_code_science_review=forbidden',
    'CODE_SCIENCE_INDEX.md')) {
    if (-not $workflowDesignManagerRoleNormalized.Contains($required)) { throw "Workflow Design Manager role missing: $required" }
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
    'role=code_project_manager',
    'formal_external_review_request_and_intake_authority=exclusive',
    'runtime_authority=exclusive',
    'current_work_authority=exclusive',
    'scientific_authority=none',
    'technical_acceptance_authority=exclusive',
    'formal_review_transport=agentify_file_batch_result',
    'AGENTIFY_REVIEW_BATCH_ASSIGNMENT',
    'AGENTIFY_REVIEW_BATCH_RESULT',
    'experiment_child=hmasd-experiment-operator',
    'cross_task_transport=codex_native_send_message_to_thread',
    'cross_task_target=current_thread_id_from_user_or_native_task_context',
    'cross_task_model_and_thinking_overrides=omit',
    'Workflow Design Manager')) {
    if (-not $codePmRole.Contains($required)) {
        throw "Code Project Manager role missing: $required"
    }
}
if ($null -ne $handoff) {
    foreach ($required in @(
        'write_trigger=explicit_user_request_only',
        'automatic_create_or_update=forbidden')) {
        if (-not $handoff.Contains($required)) { throw "Handoff contract missing: $required" }
    }
}
if (-not $workflowAudit.Contains('written only on explicit user request')) {
    throw 'Workflow audit Skill permits automatic handoff writing'
}
foreach ($required in @(
    'superpowers_execution=disabled',
    'workflow_hash_validation=disabled',
    'codebase_policy=architecture_first_module_boundaries',
    'code_change_shape=coherent_module_responsibility_with_focused_evidence',
    'shared_abstraction_justification=ownership_or_multiple_live_callers',
    'valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED',
    'early_termination_boundary=unrecoverable_external_technical_impossibility_only',
    'CODE_SCIENCE_ALIGNMENT_AUDIT')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing: $required" }
}
foreach ($required in @(
    'Keep public interfaces minimal, dependencies directed, and complexity isolated',
    'Evaluate each change by coherent module responsibility, minimal public interfaces, directed dependencies, explicit state ownership, complexity isolation, change locality, preserved behavior and focused evidence')) {
    if (-not $agileNormalized.Contains($required)) { throw "Agile Skill missing architecture criterion: $required" }
}
foreach ($required in @(
    'search_complexity_ceiling=O(H*K_search)',
    'nested_rollout_replanning=forbidden',
    'NON_EXECUTABLE_EVIDENCE_DESIGN',
    'O(N*k_neighbor)')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing complexity rule: $required" }
}
foreach ($required in @(
    'Workflow Design Manager is the sole workflow design, modification, acceptance',
    'This Skill grants no science, code, code acceptance, runtime or project-state authority.',
    'workflow_mechanical_invariant_scope=irreversible_and_high_cost_actions_only',
    'workflow_retryable_failure_mechanism=forbidden_use_one_line_runtime_checklist',
    'workflow_new_mechanism_requires_named_deletion=true',
    'workflow_legacy_mechanism_policy=no_expansion_preserve_contract_when_touched',
    'Maintainability is judged by interface quality, coherent responsibility, dependency direction, explicit state ownership, decoupling, complexity isolation, change locality and focused contract evidence',
    'Line and file counts may be recorded as diagnostics, but they never reject a change, force a split or define acceptance',
    'workflow_incident_to_permanent_rule_threshold=2_independent_recurrences',
    'workflow_rule_single_source=one_defining_file_others_point',
    'simple_operation_active_engineering_budget_minutes=20',
    'simple_operation_failed_probe_budget=2',
    'simple_operation_paths=one_normal_plus_one_simple_fallback',
    'simple_operation_success=user_visible_requested_result',
    'passive_external_generation_wait_excluded_from_engineering_budget=true',
    'reviews it once by default',
    'parallel reviewers only for genuinely',
    'Their advice cannot create a second pass.',
    'the log is evidence',
    'keep authority/capability in the role',
    'model/sandbox plus a role pointer in the profile',
    'Run with the registered interpreter:',
    'check_hmasd_agent_harness.py')) {
    if (-not $workflowAuditNormalized.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}
foreach ($required in @(
    'Ordinary workflow changes use the registered Auditor/Scout, Implementer and integrated Reviewer stages with parallel-first scheduling and dependency order',
    'Dispatch read-only Auditor/Scout concurrently with already-freezable implementation slices',
    'serialize only actual information dependencies or same-file writers',
    'The integrated Reviewer follows the complete integrated batch',
    'parallel reviewers are limited to genuinely independent review questions',
    'Their authority and assignment meaning remain with their Role',
    'Stable execution orientation is in',
    'generic workflow-change requests remain on the subagent route',
    'stable assignment dependency is',
    'This is context and evidence direction, not a state machine, queue or admission gate',
    'A Reviewer or Auditor reports a conflict',
    'Detailed procedures do',
    'Role-based successor continuity',
    'Successor brief storage and reload semantics live in',
    'Owner roles and stable outputs',
    'Maintenance is event-triggered only')) {
    $workflowDelegationSurface = "$workflowAuditNormalized $workflowMapNormalized $workflowDesignManagerRoleNormalized"
    if (-not (($workflowDelegationSurface -replace '\s+', ' ').Contains($required))) {
        throw "Workflow delegation/context contract missing: $required"
    }
}
$obsoleteDispatchRule = @('Do not', 'create', 'a', 'child', 'when', 'dispatch/packet', 'review', 'costs', 'more', 'than', 'the') -join ' '
if ($workflowAudit.Contains($obsoleteDispatchRule)) {
    throw 'Workflow audit Skill retains the obsolete dispatch-cost discouragement'
}
foreach ($required in @(
    'owner_role=workflow_design_manager',
    'Owner roles and stable outputs',
    'Dependency direction',
    'Context loading',
    'Event-triggered maintenance',
    'no timer',
    'no freshness checker',
    'no registry')) {
    if (-not $workflowMapNormalized.ToLowerInvariant().Contains($required.ToLowerInvariant())) {
        throw "Workflow Map contract missing: $required"
    }
}
foreach ($required in @(
    'document_kind=session_workspace_contract',
    'workflow_child_parent=workflow_design_manager',
    'docs/session-workspaces/<role_id>/',
    'temp/sessions/<role_id>/',
    'workflow_assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace',
    'workflow_successor_rotation=integrated_batch_completion',
    'workflow_successor_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface',
    'workflow_thread_registry=forbidden',
    'docs/project/current-work/common/<record-id>.md',
    'docs/project/current-work/sessions/<role_id>.md',
    'same_file_concurrent_writes=forbidden',
    'docs/project/handoffs/README.md',
    'temp/handoffs/',
    'assignment-specific direction/treatment handoff files',
    'never share a writable file',
    'does not allocate runtime capacity or establish scientific priority',
    'workspace_boundary_guard=fail_closed_for_recognized_pretooluse_cases',
    'authoritative_write_boundary=tool_os_sandbox|verified_ticket_identity|git_visible_checks',
    'workspace_ticket_retirement=registered_clean_detached_worktree_only',
    'Formats and suggested sections aid understanding but never become admission gates',
    'It is never staged, committed or pushed')) {
    if (-not $sessionWorkspaceContractNormalized.Contains($required)) { throw "Session workspace contract missing: $required" }
}
foreach ($retired in @(
    'resource_consuming_experiment_action=one_at_a_time_for_attribution',
    'Explorer names at most one resource-consuming experiment action at a time',
    'one resource-consuming experiment action active',
    'one isolated candidate at a time',
    'one-candidate-at-a-time',
    'queued_capacity_state=',
    'Insufficient capacity is `queued`',
    'global_serial_fallback=allowed',
    'global_serial_fallback=default',
    'global_serial_fallback=serial_by_default',
    'attribution requires serialization',
    'completion order determines dispatch')) {
    if ($independentResearchRole.Contains($retired) -or
        $parallelResearch.Contains($retired) -or
        $explorerValidationContract.Contains($retired) -or
        $explorerValidationSkill.Contains($retired) -or
        $sessionWorkspaceContract.Contains($retired)) {
        throw "Retired global experiment lock remains: $retired"
    }
}

$principlesSection3 = ($algorithmPrinciples -split '## 4\. Evidence Design', 2)[0]
if ($principlesSection3.Contains('Schedule one resource-consuming action at a time for attribution')) {
    throw 'Algorithm principles retain the stale global attribution lock'
}
foreach ($stale in @(
    'one resource-consuming action at a time for attribution',
    'global serial lock by default',
    'serialize independent treatments for attribution',
    'current sole action permits serialization')) {
    foreach ($surface in @(
        $independentResearchRole,
        $parallelResearch,
        $independentResearchSkill,
        $explorerValidationSkill,
        $explorerValidationContract,
        $publicHandoffContract)) {
        if (($surface -replace '\s+', ' ').ToLowerInvariant().Contains($stale.ToLowerInvariant())) {
            throw "Independent research retains weak serial fallback wording: $stale"
        }
    }
}
foreach ($required in @(
    'scripts/hmasd_workspace_ticket.py retire',
    'Retirement never uses force or discards Git-visible work',
    'fails closed for recognized mutation forms',
    'bounded syntactic preflight')) {
    if (-not $workflowAuditNormalized.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}
foreach ($required in @(
    'workflow_decision_question_condition=changes_named_plan_field',
    'workflow_plan_confirmation=required_before_mutation',
    'workflow_read_only_plan_confirmation=not_required',
    'workflow_material_plan_drift=reconfirmation_required')) {
    if (-not $workflowCollaborationNormalized.Contains($required)) { throw "Workflow collaboration Skill missing plan-first execution rule: $required" }
}
foreach ($required in @(
    'runtime_authority=none',
    'workflow_zero_question_path=fully_specified_mutations',
    'workflow_decision_question_condition=changes_named_plan_field',
    'workflow_plan_confirmation=required_before_mutation',
    'workflow_read_only_plan_confirmation=not_required',
    'workflow_material_plan_drift=reconfirmation_required',
    'zero-question path',
    'changes at least one named plan field',
    'one question at a time',
    'Requirements understanding',
    'Exact paths',
    'Perform no mutation',
    'confirms the complete plan in natural language',
    'Complete a read-only inspection',
    'workflow cost audit explicitly requested by the user',
    'present the complete revised plan')) {
    if (-not $workflowCollaborationNormalized.Contains($required)) { throw "Workflow collaboration Skill missing: $required" }
}
foreach ($required in @(
    '`AGENTS.md` owns the lazy trigger table',
    'Roles and Audit Skill own detailed routing mechanics',
    'Delegation orientation',
    'This is context and evidence direction, not a state machine, queue or admission gate',
    'stable ownership, interface, dependency, context-loading, delegation or continuity change',
    'successor-continuity contract')) {
    if (-not $workflowMapNormalized.Contains($required)) {
        throw "Workflow map missing lazy context/delegation orientation: $required"
    }
}
foreach ($required in @(
    'workflow_successor_rotation=integrated_batch_completion',
    'workflow_successor_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface',
    'workflow_thread_registry=forbidden')) {
    if (-not $sessionWorkspaceContractNormalized.Contains($required)) {
        throw "Session workspace contract missing successor boundary: $required"
    }
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
    'code_science_audit_mode=independent_scientific_assessment_then_bounded_disposition',
    'Question-authored concerns are leads, not a closure checklist or an expected answer',
    'code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY',
    'code_science_audit_new_algorithm_or_evidence_search=forbidden')) {
    if (-not $proRoleNormalized.Contains($required)) { throw "External Pro role missing: $required" }
}
foreach ($required in @(
    'explorer_project_alignment_review=CODE_SCIENCE_ALIGNMENT_AUDIT',
    'explorer_project_alignment_reviewer=external_gpt_5_6_pro',
    'explorer_project_alignment_source=github_connector_exact_pushed_revision',
    'explorer_project_alignment_acceptance_owner=external_pro',
    'explorer_project_alignment_transport_owner=independent_research_explorer',
    'use its GitHub connection to inspect the exact named pushed commit')) {
    if (-not $proRoleNormalized.Contains($required)) { throw "External Pro project-alignment boundary missing: $required" }
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
    'runtime_owner=code_project_manager',
    'workflow_design_owner=workflow_design_manager',
    'positive control is valid only when',
    'IMPLEMENTATION_ALIGNMENT_CLARIFICATION',
    'first-match branch reproduction',
    'code_science_audit_mode=independent_scientific_assessment_then_bounded_disposition',
    'code_science_audit_position=after_code_project_manager_implementation_acceptance',
    'routine_preimplementation_code_science_review=forbidden',
    'code_science_audit_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY',
    'finding sequence, closure checklist or expected answer',
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

foreach ($text in @($agents, $current, $context, $plan, $agile, $codePmRole, $workflowDesignManagerRole, $independentResearchRole, $proRole, $assertion)) {
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
