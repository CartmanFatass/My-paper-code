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

$profiles = @(
    @('.agents/roles/WORKFLOW_AUDITOR.md', '.codex/agents/hmasd-workflow-auditor.toml', 'hmasd-workflow-auditor', '[agents."HMASDWorkflowAuditor"]', 'gpt-5.6-luna', 'high', 'read-only', 'WORKFLOW_IMPACT_PACKET'),
    @('.agents/roles/WORKFLOW_IMPLEMENTER.md', '.codex/agents/hmasd-workflow-implementer.toml', 'hmasd-workflow-implementer', '[agents."HMASDWorkflowImplementer"]', 'gpt-5.6-luna', 'high', 'workspace-write', 'WORKFLOW_CHANGE_PACKET'),
    @('.agents/roles/WORKFLOW_REVIEWER.md', '.codex/agents/hmasd-workflow-reviewer.toml', 'hmasd-workflow-reviewer', '[agents."HMASDWorkflowReviewer"]', 'gpt-5.6-sol', 'xhigh', 'read-only', 'WORKFLOW_REVIEW_PACKET'))

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
        'parent_session_id=019fb73d-5635-7b63-b165-6c5129bc0217',
        'assignment_identity=workflow_assignment_id|owned_paths|wdm_session_workspace',
        'acceptance_authority=none', 'child_authority=none', 'current_work_read=forbidden')) {
        if (-not $role.Contains($required)) { throw "$($entry[2]) role missing: $required" }
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
    'exact resolved ticket', 'git rev-parse --show-toplevel')) {
    if (-not $manager.Contains($required)) { throw "WDM charter missing: $required" }
}

foreach ($required in @(
    'workflow_child_parent=workflow_design_manager',
    'workflow_child_assignment_fields=workflow_assignment_id|owned_paths|wdm_session_workspace',
    'workflow_child_acceptance_authority=none',
    'workflow_child_edit_worktree=resolved_ticket_worktree_path|pre_edit_git_rev_parse_toplevel_exact_match',
    'For six or more paths', 'one implementer per exact nonoverlapping file family',
    'do not impose a fixed', 'two-implementer ceiling',
    'simple_operation_active_engineering_budget_minutes=20',
    'simple_operation_failed_probe_budget=2',
    'simple_operation_paths=one_normal_plus_one_simple_fallback',
    'simple_operation_success=user_visible_requested_result',
    'passive_external_generation_wait_excluded_from_engineering_budget=true',
    'request at most one advisory', 'never starts a re-review loop',
    'workflow_single_mechanism_line_budget=100',
    'workflow_single_mechanism_terminal_state_budget=3',
    'workflow_mechanism_budget_unit=one_new_or_expanded_gate_or_recovery_branch',
    'workflow_legacy_mechanism_policy=no_expansion_reduce_when_touched',
    'workflow_incident_to_permanent_rule_threshold=2_independent_recurrences',
    'workflow_hash_validation=forbidden',
    'the log is evidence', 'resolved ticket worktree path',
    '`git rev-parse --show-toplevel`')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing: $required" }
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

Write-Output 'HMASD_WORKFLOW_DESIGN_DELEGATION_CONTRACT_OK'
