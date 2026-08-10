[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Read-RepoFile([string]$Path) {
    Get-Content -Raw -LiteralPath (Join-Path $repo $Path)
}

$config = Read-RepoFile '.codex/config.toml'
$manager = Read-RepoFile '.agents/roles/WORKFLOW_DESIGN_MANAGER.md'
$skill = Read-RepoFile '.agents/skills/hmasd-workflow-change-audit/SKILL.md'
$harness = Read-RepoFile '.agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py'
$workflowMap = Read-RepoFile 'docs/project/WORKFLOW_MAP.md'
$router = Read-RepoFile 'AGENTS.md'
$sessionContract = Read-RepoFile 'docs/project/SESSION_WORKSPACE_CONTRACT.md'
$collaborationSkill = Read-RepoFile '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md'
$defectQueue = Read-RepoFile 'docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md'
$normalizedManager = ($manager -replace '\s+', ' ').ToLowerInvariant()
$normalizedRouter = ($router -replace '\s+', ' ').ToLowerInvariant()
$normalizedSessionContract = ($sessionContract -replace '\s+', ' ').ToLowerInvariant()
$normalizedCollaborationSkill = ($collaborationSkill -replace '\s+', ' ').ToLowerInvariant()

$profiles = @(
    @('.agents/roles/WORKFLOW_AUDITOR.md', '.codex/agents/hmasd-workflow-auditor.toml', 'hmasd-workflow-auditor', '[agents."HMASDWorkflowAuditor"]', 'gpt-5.6-luna', 'high', 'read-only', 'WORKFLOW_IMPACT_PACKET'),
    @('.agents/roles/WORKFLOW_IMPLEMENTER.md', '.codex/agents/hmasd-workflow-implementer.toml', 'hmasd-workflow-implementer', '[agents."HMASDWorkflowImplementer"]', 'gpt-5.6-luna', 'xhigh', 'workspace-write', 'WORKFLOW_CHANGE_PACKET'),
    @('.agents/roles/WORKFLOW_REVIEWER.md', '.codex/agents/hmasd-workflow-reviewer.toml', 'hmasd-workflow-reviewer', '[agents."HMASDWorkflowReviewer"]', 'gpt-5.6-luna', 'max', 'read-only', 'WORKFLOW_REVIEW_PACKET'))

foreach ($entry in $profiles) {
    $role = Read-RepoFile $entry[0]
    $profile = Read-RepoFile $entry[1]
    foreach ($required in @(
        "name = `"$($entry[2])`"", "model = `"$($entry[4])`"",
        "model_reasoning_effort = `"$($entry[5])`"", "sandbox_mode = `"$($entry[6])`"", 'approval_policy = "never"',
        $entry[0])) {
        if (-not $profile.Contains($required)) { throw "$($entry[2]) profile missing: $required" }
    }
    foreach ($required in @(
        "callable_agent_type=$($entry[2])", 'parent=workflow_design_manager',
        'role_kind=registered_task_scoped_level2_leaf',
        'assignment_identity=workflow_assignment_id|owned_paths',
        'acceptance_authority=none', 'child_authority=none', 'current_work_read=forbidden')) {
        if (-not $role.Contains($required)) { throw "$($entry[2]) role missing: $required" }
    }
    if ($role -match '(?m)^parent_session_id=') {
        throw "$($entry[2]) retains a fixed historical session identity"
    }
    if (-not $config.Contains($entry[3]) -or
        -not $config.Contains("config_file = `"./agents/$($entry[2]).toml`"")) {
        throw "$($entry[2]) registration missing"
    }
}

foreach ($required in @(
    'workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_modification_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_acceptance_authority=exclusive_for_all_workflow_control_plane_surfaces',
    'workflow_git_authority=none',
    'current_work_authority=public_index_and_own_workflow_control_plane_records_only',
    'workflow_input_precedence=direct_user_instruction|wdm_charter_and_design_principles|accepted_stable_workflow_contract|root_handoff',
    'workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md',
    'Role and Skill capability standard',
    'necessary observations', 'permitted actions')) {
    if (-not $manager.Contains($required)) { throw "WDM charter missing: $required" }
}

foreach ($required in @(
    'workflow_assignment_writing_skill=hmasd-writing-agent-assignments',
    'owned outcome, necessary observations, permitted actions, role-local judgment, bounded recovery and completion evidence',
    'does not load code maps or code-context guides by default')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM writing-agent routing contract missing: $required" }
}

foreach ($required in @(
    'workflow_change_request_route=root->wdm',
    'cross_task_transport=return_to_root',
    'workflow_subagent_parallelism=parallel_first_with_dependency_order')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant())) { throw "Router execution policy missing: $required" }
}

foreach ($required in @(
    'ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order',
    'pure design or authority decisions without file mutation remain wdm-local')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM execution policy missing: $required" }
}
if (-not $skill.Contains('workflow_hash_validation=forbidden')) {
    throw 'Workflow audit Skill missing hash prohibition'
}
foreach ($required in @('simple_operation_active_engineering_budget_minutes=20','simple_operation_failed_probe_budget=2')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing simple-operation budget: $required" }
}

foreach ($required in @(
    'designing an assignment/interface',
    'hmasd-writing-agent-assignments')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant())) { throw "Router writing-agent routing contract missing: $required" }
}

foreach ($required in @(
    'assignment_writing_skill=hmasd-writing-agent-assignments',
    'required sub-skill',
    'design a reusable child or cross-session interface',
    'compile each concrete file-backed assignment')) {
    if (-not $normalizedCollaborationSkill.Contains($required.ToLowerInvariant())) { throw "Collaborative Skill writing-agent contract missing: $required" }
}

foreach ($required in @(
    'child_assignment_brief=temp/sessions/<parent_role>/assignments/<assignment_id>.md',
    'child_assignment_format=self_contained_natural_language_not_schema_admission',
    'child_forked_context=background_only',
    'workflow_root_reload=fresh_root_task_canonical_reload',
    'workflow_root_reload_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface',
    'workflow_thread_registry=forbidden')) {
    if (-not $normalizedSessionContract.Contains($required.ToLowerInvariant())) { throw "Session assignment-writing contract missing: $required" }
}

$normalizedWorkflowMap = ($workflowMap -replace '\s+', ' ').ToLowerInvariant()
foreach ($required in @(
    'parent task model -> hmasd-writing-agent-assignments Skill -> self-contained',
    'assignment -> child judgment/result',
    'not a state machine, queue or admission gate')) {
    if (-not $normalizedWorkflowMap.Contains($required.ToLowerInvariant())) { throw "Workflow Map assignment dependency missing: $required" }
}

foreach ($required in @(
    'workflow_mechanical_invariant_scope=irreversible_and_high_cost_actions_only',
    'workflow_retryable_failure_mechanism=forbidden_use_one_line_runtime_checklist',
    'workflow_rule_single_source=one_defining_file_others_point',
    'workflow_single_mechanism_terminal_state_budget=3',
    'workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch',
    'workflow_legacy_mechanism_policy=no_expansion_preserve_contract_when_touched',
    'workflow_incident_to_permanent_rule_threshold=2_independent_recurrences',
    'workflow_hash_validation=forbidden',
    'the log is evidence', 'exact assignment-owned path set',
    'observation, action, judgment, recovery and completion capabilities',
    'Prefer positive capability text',
    'no external workspace identity precondition')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}

foreach ($required in @(
    'ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order',
    'dispatch read-only auditor/scout concurrently with already-freezable implementation slices',
    'run disjoint implementer file families concurrently',
    'serialize only actual information dependencies or same-file writers',
    'integrated reviewer follows the complete integrated batch',
    'every workflow-file mutation remains on the registered l2 subagent route',
    'focused checks, review and root reload boundary below',
    'parallel reviewers are limited to genuinely independent review questions',
    'mechanism and simple-operation budgets constrain new gates, recovery branches and probe work; they never decide delegate-vs-local routing',
    'task size, complexity, local feasibility, context cost, path count and benefit estimates never alter it')) {
    if (-not (($skill -replace '\s+', ' ').ToLowerInvariant()).Contains($required.ToLowerInvariant())) { throw "Workflow delegation/context contract missing: $required" }
}
$obsoleteDispatchRule = @('Do not', 'create', 'a', 'child', 'when', 'dispatch/packet', 'review', 'costs', 'more', 'than', 'the') -join ' '
if ($skill.Contains($obsoleteDispatchRule)) {
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
    if (-not (($workflowMap -replace '\s+', ' ').ToLowerInvariant()).Contains($required.ToLowerInvariant())) {
        throw "Workflow Map contract missing: $required"
    }
}

foreach ($retiredRoutingPhrase in @(
    'After confirmation, WDM may use',
    'when implementers were used',
    'Delegation is judgment-guided',
    'bounded slices may use registered children',
    'no mandatory pipeline',
    'cost-aware delegation path',
    'local feasibility threshold',
    'task size threshold',
    'complexity threshold')) {
    foreach ($surface in @($router, $manager, $collaborationSkill, $skill, $workflowMap)) {
        if ($surface.ToLowerInvariant().Contains($retiredRoutingPhrase.ToLowerInvariant())) {
            throw "Stale optional or threshold routing remains: $retiredRoutingPhrase"
        }
    }
}

if (-not $normalizedWorkflowMap.Contains('ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order') -or
    -not $normalizedWorkflowMap.Contains('dispatch read-only auditor/scout concurrently with already-freezable implementation slices') -or
    -not $normalizedWorkflowMap.Contains('workflow-file changes are performed by assigned workflow implementer leaves')) {
    throw 'Workflow Map execution policy missing parallel-first stages or registered implementer route'
}

foreach ($required in @(
    'workflow_subagent_parallelism=parallel_first_with_dependency_order',
    'ordinary workflow stages are mandatory and parallel-first with dependency order',
    'integrated reviewer follows the complete integrated batch')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant()) -and
        -not $normalizedWorkflowMap.Contains($required.ToLowerInvariant())) {
        throw "Parallel-first execution policy missing: $required"
    }
}

foreach ($retiredSerialPhrase in @(
    'ordinary workflow changes use the registered auditor/scout -> implementer -> reviewer sequence',
    'ordinary workflow changes use the registered auditor/scout -> implementer -> reviewer workflow',
    'ordinary workflow changes use the registered auditor/scout -> implementer -> reviewer')) {
    foreach ($surface in @($router, $manager, $collaborationSkill, $skill, $workflowMap)) {
        if ($surface.ToLowerInvariant().Contains($retiredSerialPhrase.ToLowerInvariant())) {
            throw "Serial workflow wording remains: $retiredSerialPhrase"
        }
    }
}

foreach ($forbidden in @(
    'agentify_transport_assignment_fields=',
    'agentify_transport_result_fields=',
    'cpm_mechanical_result_fields=',
    'explorer_mechanical_result_fields=')) {
    if ($router.Contains($forbidden)) { throw "Router duplicates delegated child schema: $forbidden" }
}

foreach ($required in @(
    'CPM_MECHANICAL_TASK_ASSIGNMENT',
    'CPM_MECHANICAL_TASK_RESULT',
    'cpm_mechanical_assignment_locators=spec_path|result_path',
    'cpm_mechanical_result_locator=result_path',
    'AGENTIFY_REVIEW_BATCH_ASSIGNMENT',
    'agentify_transport_result_locator=results_path')) {
    if (-not (($sessionContract -replace '\s+', ' ').Contains($required))) {
        throw "Session workspace mechanical contract missing: $required"
    }
}

foreach ($required in @(
    'EXPLORER_MECHANICAL_OVERLOAD',
    'TICKET_MODEL_OUTPUT_TRUNCATION',
    'NONBLOCKING',
    'CLOSED')) {
    if (-not $defectQueue.Contains($required)) { throw "Workflow incident log entry missing: $required" }
}

$normalizedMaintainabilityContract = (($manager + "`n" + $skill) -replace '\s+', ' ')
foreach ($required in @(
    'interface quality', 'coherent responsibility', 'dependency direction',
    'state ownership', 'decoupling', 'complexity isolation', 'change locality',
    'focused contract evidence')) {
    if (-not $normalizedMaintainabilityContract.Contains($required)) {
        throw "Qualitative maintainability contract missing: $required"
    }
}

foreach ($retired in @(
    (@('single', 'mechanism', 'line', 'budget') -join '_'),
    (@('wdm', 'core', 'control', 'plane', 'line', 'budget') -join '_'),
    (@('workflow', 'net', 'line', 'growth', 'default') -join '_'),
    (@('net', 'active', 'line', 'growth', 'default') -join '_'),
    (@('workflow', 'recovery', 'path', 'line', 'share') -join '_'),
    (@('CONTROL', 'PLANE', 'LINE', 'BUDGET') -join '_'),
    (@('CONTROL', 'PLANE', 'BUDGET', 'PATHS') -join '_'),
    ((@('control', 'plane') -join '-') + ' ' + (@('line', 'budget', 'exceeded') -join ' ')),
    (@('net', 'active-line', 'change') -join ' '),
    (@('at', 'most', 'five', 'lines') -join ' '))) {
    if ($manager.Contains($retired) -or $skill.Contains($retired) -or
        $harness.Contains($retired)) {
        throw "Retired numeric workflow gate remains: $retired"
    }
}

foreach ($forbidden in @(
    'parent=assigning_persistent_session',
    'assignment_identity=session_owner_role|session_owner_id|owned_paths|session_workspace',
    'workflow_child_parent=assigning_persistent_session',
    'exclusive_for_shared_control_plane_surfaces')) {
    if ($manager.Contains($forbidden) -or $skill.Contains($forbidden)) {
        throw "Retired distributed workflow authority remains: $forbidden"
    }
}

$legacyVerifier = Read-RepoFile '.agents/roles/VERIFIER.md'
$legacyReviewer = Read-RepoFile '.agents/roles/REVIEWER.md'
if (-not $legacyVerifier.Contains('parent=code_project_manager') -or
    -not $legacyReviewer.Contains('parent=code_project_manager')) {
    throw 'Code-side verifier/reviewer ownership drifted'
}
if (-not $config.Contains('max_depth = 2')) { throw 'Two-level depth is not configured' }

$workflowAuditor = Read-RepoFile '.agents/roles/WORKFLOW_AUDITOR.md'
if (-not (($workflowAuditor -replace '\s+', ' ').ToLowerInvariant().Contains(
        'bounded repository-wide text search'))) {
    throw 'Workflow auditor lacks bounded coupled-path discovery'
}
$workflowImplementer = Read-RepoFile '.agents/roles/WORKFLOW_IMPLEMENTER.md'
$workflowImplementerProfile = Read-RepoFile '.codex/agents/hmasd-workflow-implementer.toml'
if ($workflowImplementerProfile.Contains('resolved_ticket_worktree_path') -or
    $workflowImplementerProfile.Contains('scripts/hmasd_workspace_ticket.py')) {
    throw 'Workflow implementer retains retired ticket identity'
}
if (-not $workflowImplementer.Contains('reversible')) {
    throw 'Workflow implementer lacks local reversible judgment'
}

# Registered workflow children receive semantic task models rather than packet
# shaped completion gates.  Keep this contract source-level and heading-agnostic.
$workflowChildSpecs = @(
    @{ Role = '.agents/roles/WORKFLOW_AUDITOR.md'; Profile = '.codex/agents/hmasd-workflow-auditor.toml'; Tail = 'WORKFLOW_IMPACT_PACKET'; Recovery = 'alternate read-only observation' },
    @{ Role = '.agents/roles/WORKFLOW_IMPLEMENTER.md'; Profile = '.codex/agents/hmasd-workflow-implementer.toml'; Tail = 'WORKFLOW_CHANGE_PACKET'; Recovery = 'reversible correction/re-run' },
    @{ Role = '.agents/roles/WORKFLOW_REVIEWER.md'; Profile = '.codex/agents/hmasd-workflow-reviewer.toml'; Tail = 'WORKFLOW_REVIEW_PACKET'; Recovery = 'bounded re-read' })

foreach ($child in $workflowChildSpecs) {
    $childRole = Read-RepoFile $child.Role
    $childProfile = Read-RepoFile $child.Profile
    $normalizedChildRole = ($childRole -replace '\s+', ' ').ToLowerInvariant()
    $normalizedChildProfile = ($childProfile -replace '\s+', ' ').ToLowerInvariant()
    foreach ($required in @(
        'self-contained natural-language task model',
        'workflow_assignment_id', 'owned_paths', 'wdm_session_workspace',
        'factual authority and scope anchors', 'never define task meaning',
        'concise natural-language conclusion', 'owned outcome',
        'complete or unresolved', 'direct consequence', 'residual uncertainty',
        'compact factual', $child.Tail, 'never substitutes for the conclusion',
        $child.Recovery)) {
        if (-not $normalizedChildRole.Contains($required.ToLowerInvariant())) {
            throw "$($child.Role) semantic contract missing: $required"
        }
    }
    if ($childRole -match '(?i)return\s+(?:one\s+)?(?:the\s+)?(?:exactly\s+one\s+)?(?:`)?WORKFLOW_[A-Z_]+_PACKET(?:`)?\b' -or
        $childRole -match '(?i)return\s+the\s+packet\s+only') {
        throw "$($child.Role) still permits packet-only completion"
    }
    foreach ($required in @(
        'fork_turns=none', '.agents/roles/', 'Workflow Design Manager',
        'self-contained natural-language task model', 'authority')) {
        if (-not $normalizedChildProfile.Contains($required.ToLowerInvariant())) {
            throw "$($child.Profile) thin profile contract missing: $required"
        }
    }
    foreach ($forbidden in @('Return exactly one', 'return exactly one', 'For impact_map,', 'A finding is actionable only when')) {
        if ($normalizedChildProfile.Contains($forbidden.ToLowerInvariant())) {
            throw "$($child.Profile) retains duplicated packet/review procedure: $forbidden"
        }
    }
}

$implementerRoleText = Read-RepoFile '.agents/roles/WORKFLOW_IMPLEMENTER.md'
$normalizedImplementerRoleText = ($implementerRoleText -replace '\s+', ' ')
if (-not $normalizedImplementerRoleText.Contains('agent_tree_level=2') -or
    -not $normalizedImplementerRoleText.Contains('spawn_authority=none') -or
    -not $normalizedImplementerRoleText.Contains('return')) {
    throw 'Workflow implementer lacks the L2 leaf boundary'
}
foreach ($forbidden in @('Git mutation', 'stage, commit, push', 'route cross-task messages')) {
    if (-not $implementerRoleText.Contains($forbidden)) {
        throw "Workflow implementer boundary missing: $forbidden"
    }
}

Write-Output 'HMASD_WORKFLOW_DESIGN_DELEGATION_CONTRACT_OK'
