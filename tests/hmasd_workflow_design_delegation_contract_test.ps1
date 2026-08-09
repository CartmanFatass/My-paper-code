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
$codePmRole = Read-RepoFile '.agents/roles/CODE_PROJECT_MANAGER.md'
$agileSkill = Read-RepoFile '.agents/skills/hmasd-agile-research-development/SKILL.md'
$sessionContract = Read-RepoFile 'docs/project/SESSION_WORKSPACE_CONTRACT.md'
$collaborationSkill = Read-RepoFile '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md'
$defectQueue = Read-RepoFile 'docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md'
$normalizedManager = ($manager -replace '\s+', ' ').ToLowerInvariant()
$normalizedRouter = ($router -replace '\s+', ' ').ToLowerInvariant()
$normalizedSessionContract = ($sessionContract -replace '\s+', ' ').ToLowerInvariant()
$normalizedCollaborationSkill = ($collaborationSkill -replace '\s+', ' ').ToLowerInvariant()
$normalizedCodePmRole = ($codePmRole -replace '\s+', ' ').ToLowerInvariant()
$normalizedAgileSkill = ($agileSkill -replace '\s+', ' ').ToLowerInvariant()

$profiles = @(
    @('.agents/roles/WORKFLOW_AUDITOR.md', '.codex/agents/hmasd-workflow-auditor.toml', 'hmasd-workflow-auditor', '[agents."HMASDWorkflowAuditor"]', 'gpt-5.6-luna', 'high', 'read-only', 'WORKFLOW_IMPACT_PACKET'),
    @('.agents/roles/WORKFLOW_IMPLEMENTER.md', '.codex/agents/hmasd-workflow-implementer.toml', 'hmasd-workflow-implementer', '[agents."HMASDWorkflowImplementer"]', 'gpt-5.6-luna', 'xhigh', 'danger-full-access', 'WORKFLOW_CHANGE_PACKET'),
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
        'role_kind=registered_nonpersistent_native_child',
        'assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace',
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
    'workflow_git_authority=exclusive_for_workflow_control_plane_surfaces',
    'current_work_authority=public_index_and_own_workflow_control_plane_records_only',
    'workflow_input_precedence=direct_user_instruction|wdm_charter_and_design_principles|accepted_stable_workflow_contract|other_session_report',
    'workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md',
    'workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match',
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
    'workflow_change_execution=subagent_workflow_by_default',
    'workflow_subagent_parallelism=parallel_first_with_dependency_order',
    'wdm_direct_modification=only_when_user_explicitly_instructs_WDM_to_modify_directly',
    'ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order',
    'generic workflow change request remains on the default subagent route',
    'pure wdm design or authority decisions without file mutation remain wdm-local',
    'delegate-vs-local routing does not use task size, complexity, local feasibility, context cost, path count or benefit estimates')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant())) { throw "Router execution policy missing: $required" }
}

foreach ($required in @(
    "wdm's exclusive workflow modification authority is exercised through the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order",
    'a direct user instruction explicitly naming wdm direct modification is the only exception',
    'pure design or authority decisions without file mutation remain wdm-local')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM execution policy missing: $required" }
}
if (-not $skill.Contains('workflow_hash_validation=forbidden')) {
    throw 'Workflow audit Skill missing hash prohibition'
}
foreach ($required in @('simple_operation_active_engineering_budget_minutes=20','simple_operation_failed_probe_budget=2')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing simple-operation budget: $required" }
}
foreach ($required in @('resolved ticket worktree path','git rev-parse --show-toplevel')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing ticket identity check: $required" }
}

foreach ($required in @(
    'Designing or dispatching a child or cross-session interface',
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
    'workflow_successor_rotation=integrated_batch_completion',
    'workflow_successor_brief=current_commit|accepted_stable_change|real_unfinished_item|next_user_goal|next_map_or_interface',
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
    'the log is evidence', 'resolved ticket worktree path',
    'observation, action, judgment, recovery and completion capabilities',
    'Prefer positive capability text',
    '`git rev-parse --show-toplevel`')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}

foreach ($required in @(
    'ordinary workflow changes use the registered auditor/scout, implementer and integrated reviewer stages with parallel-first scheduling and dependency order',
    'dispatch read-only auditor/scout concurrently with already-freezable implementation slices',
    'run disjoint implementer file families concurrently',
    'serialize only actual information dependencies or same-file writers',
    'integrated reviewer follows the complete integrated batch',
    'generic workflow-change requests remain on the subagent route',
    'normal wdm checks and acceptance mechanics',
    "do not invent a reviewer requirement beyond the user's rule",
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
    'WDM may use',
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
    -not $normalizedWorkflowMap.Contains('generic workflow-change requests follow the default subagent route')) {
    throw 'Workflow Map execution policy missing parallel-first stages or direct-request default'
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

foreach ($required in @(
    'cpm_mechanical_child=hmasd-cpm-mechanical',
    'cpm_mechanical_parent=code_project_manager',
    'explorer_mechanical_child=hmasd-explorer-mechanical',
    'explorer_mechanical_parent=independent_research_explorer')) {
    if (-not $router.Contains($required)) { throw "Router mechanical child pointer missing: $required" }
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
if (-not $config.Contains('max_depth = 1')) { throw 'Workflow children may spawn descendants' }

$workflowAuditor = Read-RepoFile '.agents/roles/WORKFLOW_AUDITOR.md'
if (-not (($workflowAuditor -replace '\s+', ' ').ToLowerInvariant().Contains(
        'bounded repository-wide text search'))) {
    throw 'Workflow auditor lacks bounded coupled-path discovery'
}
$workflowImplementer = Read-RepoFile '.agents/roles/WORKFLOW_IMPLEMENTER.md'
$workflowImplementerProfile = Read-RepoFile '.codex/agents/hmasd-workflow-implementer.toml'
if (-not $workflowImplementerProfile.Contains('resolved_ticket_worktree_path')) {
    throw 'Workflow implementer assignment lacks the exact ticket worktree'
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
if (-not $normalizedImplementerRoleText.Contains('exactly `git rev-parse --show-toplevel`') -or
    -not $normalizedImplementerRoleText.Contains('sole permitted Git observation')) {
    throw 'Workflow implementer lacks the exact read-only Git identity exception'
}
foreach ($forbidden in @('Git mutation', 'stage, commit, push', 'route cross-task messages')) {
    if (-not $implementerRoleText.Contains($forbidden)) {
        throw "Workflow implementer boundary missing: $forbidden"
    }
}

$schedulerRolePath = '.agents/roles/RESEARCH_SCHEDULER.md'
$schedulerSkillPath = '.agents/skills/hmasd-research-scheduler/SKILL.md'
$schedulerRole = Read-RepoFile $schedulerRolePath
$schedulerSkill = Read-RepoFile $schedulerSkillPath
$schedulerText = (($schedulerRole + "`n" + $schedulerSkill) -replace '\s+', ' ').ToLowerInvariant()
foreach ($required in @(
    'user_owned_persistent_desktop_task',
    'registered_child=false',
    'profile_path=none',
    'task_lifecycle_and_resource_conflict_routing_only',
    'same-level ephemeral owner tasks',
    'create_thread', 'environment=local', 'threadid', 'hostid',
    'wait_threads', 'read_thread', 'canonical locator',
    'at most eight', 'active_assignments.md',
    'exact_desktop_lifecycle_and_routing_identity',
    'single_create_thread_return',
    'self-contained natural-language assignment',
    'exact cooperative write ownership',
    'known exact handles only', 'never blindly retry')) {
    if (-not $schedulerText.Contains($required.ToLowerInvariant())) {
        throw "Research Scheduler contract missing: $required"
    }
}
foreach ($forbidden in @(
    'research-scheduler.toml',
    'fixed unit pool')) {
    if ($config.Contains($forbidden)) { throw "Scheduler profile/config drifted: $forbidden" }
}
foreach ($required in @(
    'science_authority=none', 'code_authority=none',
    'technical_acceptance_authority=none', 'git_authority=none',
    'runtime_execution_authority=none', 'semantic_relay_authority=none',
    'sibling_preload_authority=none')) {
    if (-not $schedulerRole.Contains($required)) { throw "Scheduler boundary missing: $required" }
}
foreach ($surface in @($router, $sessionContract, $workflowMap)) {
    if (-not $surface.Contains('.agents/skills/hmasd-research-scheduler/SKILL.md')) {
        throw 'Scheduler procedure/resource pointer missing'
    }
    foreach ($commandLevel in @('create_thread', 'wait_threads', 'read_thread')) {
        if ($surface -match "(?<![A-Za-z0-9_])$([regex]::Escape($commandLevel))(?![A-Za-z0-9_])") {
            throw "Scheduler command-level procedure duplicated outside Skill: $commandLevel"
        }
    }
}

# Scheduler handles own lifecycle/routing only.  Assignment paths are
# cooperative ownership policy; generic and ticket guards remain defense in
# depth, while CPM owns the ticket and serialized shared-mainline boundaries.
foreach ($required in @(
    'research_scheduler_desktop_handle=threadId|hostId',
    'research_scheduler_desktop_handle_purpose=exact_desktop_lifecycle_and_routing_identity',
    'research_scheduler_desktop_handle_scope=exact_lifecycle_and_routing_only',
    'research_scheduler_assignment_write_ownership=cooperative_exact_paths',
    'cpm_treatment_write_ownership=one_registered_ticket_worktree|exact_ticket_paths|direct_native_result',
    'cpm_integration_write_ownership=sole_serialized_shared_mainline_writer|exact_accepted_commits',
    'shared_mainline_concurrent_writers=forbidden')) {
    if (-not $router.Contains($required)) { throw "Native ownership router contract missing: $required" }
}
foreach ($required in @(
    'research_scheduler_desktop_handle=threadid|hostid',
    'research_scheduler_desktop_handle_purpose=exact_desktop_lifecycle_and_routing_identity',
    'research_scheduler_desktop_handle_scope=exact_lifecycle_and_routing_only',
    'owner_assignment_write_ownership=cooperative_exact_paths',
    'owner_assignment_write_enforcement=generic_and_ticket_guards_defense_in_depth',
    'owner_mode_treatment_write_scope=one_registered_ticket_worktree|exact_ticket_paths',
    'owner_mode_treatment_result=direct_native_result',
    'owner_mode_treatment_mainline_write=forbidden',
    'owner_mode_integration_write_scope=shared_mainline|exact_accepted_commits',
    'owner_mode_integration_concurrency=sole_serialized_writer',
    'shared_mainline_concurrent_writers=forbidden',
    'the scheduler''s exact native `{threadid, hostid}` handle is lifecycle/routing identity only',
    'treatment cpm owns one registered ticket worktree and the exact ticket paths',
    'returns its conclusion and result directly through the native owner handle',
    'integration cpm alone writes the shared mainline',
    'no shared-mainline writers run concurrently')) {
    if (-not $normalizedCodePmRole.Contains($required)) { throw "CPM native ownership contract missing: $required" }
}
foreach ($required in @(
    'for `owner_mode=treatment`, the self-contained owner assignment names one registered ticket worktree and the exact ticket paths cpm owns',
    'returns its conclusion and result directly through the native owner handle',
    'exact assignment paths are cooperative ownership policy, not authorization',
    'generic filesystem and ticket guards remain defense-in-depth',
    'cpm is the sole serialized writer of the shared mainline',
    'no shared mainline writers run concurrently')) {
    if (-not $normalizedAgileSkill.Contains($required)) { throw "Agile native ownership contract missing: $required" }
}
foreach ($required in @(
    'exact native `{threadid, hostid}` handle is lifecycle/routing identity only, not write authorization',
    'assignments carry cooperative exact write ownership',
    'treatment cpm owns one registered ticket worktree and exact ticket paths and returns a direct native result',
    'integration cpm alone serializes writes to the shared mainline for exact accepted commits',
    'no shared-mainline concurrent writers')) {
    if (-not $normalizedWorkflowMap.Contains($required)) { throw "Workflow Map native ownership contract missing: $required" }
}
foreach ($surface in @($codePmRole, $agileSkill, $router, $workflowMap)) {
    foreach ($stale in @(
        'owner_mode_treatment_write_scopes=exactly_two|',
        'owner_mode_treatment_reverse_handoff_root=',
        'owner_mode_treatment_reverse_handoff_locator=',
        'owner_mode_treatment_main_checkout_mutation=apply_patch_only_reverse_handoff_no_git',
        'assignment and scheduler binding enumerate exactly two physical write scopes',
        'scheduler binding as authorization',
        'file identity handshake',
        'temporary identity handshake',
        'session binding')) {
        if ($surface.ToLowerInvariant().Contains($stale.ToLowerInvariant())) {
            throw "Retired Scheduler binding/treatment handoff authorization remains: $stale"
        }
    }
}

Write-Output 'HMASD_WORKFLOW_DESIGN_DELEGATION_CONTRACT_OK'
