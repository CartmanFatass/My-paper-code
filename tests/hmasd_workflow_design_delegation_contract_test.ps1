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

$profiles = @(
    @('.agents/roles/WORKFLOW_AUDITOR.md', '.codex/agents/hmasd-workflow-auditor.toml', 'hmasd-workflow-auditor', '[agents."HMASDWorkflowAuditor"]', 'gpt-5.6-luna', 'high', 'read-only', 'WORKFLOW_IMPACT_PACKET'),
    @('.agents/roles/WORKFLOW_IMPLEMENTER.md', '.codex/agents/hmasd-workflow-implementer.toml', 'hmasd-workflow-implementer', '[agents."HMASDWorkflowImplementer"]', 'gpt-5.6-luna', 'xhigh', 'workspace-write', 'WORKFLOW_CHANGE_PACKET'),
    @('.agents/roles/WORKFLOW_REVIEWER.md', '.codex/agents/hmasd-workflow-reviewer.toml', 'hmasd-workflow-reviewer', '[agents."HMASDWorkflowReviewer"]', 'gpt-5.6-luna', 'max', 'read-only', 'WORKFLOW_REVIEW_PACKET'))

foreach ($entry in $profiles) {
    $role = Read-RepoFile $entry[0]
    $profile = Read-RepoFile $entry[1]
    foreach ($required in @(
        "name = `"$($entry[2])`"", "model = `"$($entry[4])`"",
        "model_reasoning_effort = `"$($entry[5])`"", "sandbox_mode = `"$($entry[6])`"",
        $entry[0], $entry[7])) {
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
    'Automatic continuous execution', 'Minimal-control discipline',
    'workflow_hash_validation=forbidden',
    'workflow_input_precedence=direct_user_instruction|wdm_charter_and_design_principles|accepted_stable_workflow_contract|other_session_report',
    'workflow_incident_log=docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md',
    'simple_operation_active_engineering_budget_minutes=20',
    'simple_operation_failed_probe_budget=2',
    'workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match',
    'Role and Skill capability standard',
    'necessary observations', 'permitted actions',
    'exact resolved ticket', 'git rev-parse --show-toplevel')) {
    if (-not $manager.Contains($required)) { throw "WDM charter missing: $required" }
}

foreach ($required in @(
    'workflow_child_parent=workflow_design_manager',
    'workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace',
    'workflow_child_acceptance_authority=none',
    'workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match',
    'For six or more paths', 'workflow_nonoverlapping_families=one_implementer_per_family',
    'do not impose a fixed', 'two-Implementer ceiling',
    'simple_operation_active_engineering_budget_minutes=20',
    'simple_operation_failed_probe_budget=2',
    'simple_operation_paths=one_normal_plus_one_simple_fallback',
    'simple_operation_success=user_visible_requested_result',
    'passive_external_generation_wait_excluded_from_engineering_budget=true',
    'one Workflow Reviewer by default', 'parallel reviewers only for genuinely',
    'Their advice cannot create a second pass.',
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
    'workflow_delegation_economics=cheaper_registered_children_by_default',
    'workflow_direct_edit_boundary=indivisible_semantic_junctions|integration_conflict_repair|final_acceptance_git_reload|no_child_action_needed',
    'workflow_known_local_work=direct_single_implementer',
    'workflow_missing_interface_facts=workflow_auditor_before_freeze',
    'workflow_nonoverlapping_families=one_implementer_per_family',
    'workflow_simple_mechanical_edit=single_implementer_without_scout_or_per_edit_reviewer',
    'workflow_delegation_shape=adaptive_composition_not_fixed_state_machine',
    'workflow_context_model=compact_task_model_plus_docs/project/WORKFLOW_MAP.md',
    'workflow_context_loading=compact_child_conclusions_and_final_diff',
    'workflow_context_expansion=concrete_interface_or_authority_dependency_only',
    'workflow_successor_continuity=fresh_wdm_task_after_coherent_batch',
    'workflow_successor_brief=short_reload_receipt_without_task_creation_registry_or_approval_state',
    'workflow_map_owner=workflow_design_manager',
    'workflow_map_maintenance=stable_role_interface_dependency_or_context_boundary_change_same_commit')) {
    if (-not $skill.Contains($required)) { throw "Workflow delegation/context contract missing: $required" }
}
$obsoleteDispatchRule = @('Do not', 'create', 'a', 'child', 'when', 'dispatch/packet', 'review', 'costs', 'more', 'than', 'the') -join ' '
if ($skill.Contains($obsoleteDispatchRule)) {
    throw 'Workflow audit Skill retains the obsolete dispatch-cost discouragement'
}

foreach ($required in @(
    'owner_role=workflow_design_manager',
    'Owner roles and stable outputs',
    'Dependency direction',
    'Minimum context loading',
    'Event-triggered maintenance',
    'no timer',
    'no freshness checker',
    'no registry')) {
    if (-not (($workflowMap -replace '\s+', ' ').ToLowerInvariant()).Contains($required.ToLowerInvariant())) {
        throw "Workflow Map contract missing: $required"
    }
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

Write-Output 'HMASD_WORKFLOW_DESIGN_DELEGATION_CONTRACT_OK'
