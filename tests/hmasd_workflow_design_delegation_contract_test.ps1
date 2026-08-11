[CmdletBinding()]
param(
    [string]$CatalogTestPath
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Read-RepoFile([string]$Path) {
    Get-Content -Raw -LiteralPath (Join-Path $repo $Path)
}

$config = Read-RepoFile '.codex/config.toml'
$manager = Read-RepoFile '.agents/roles/WORKFLOW_DESIGN_MANAGER.md'
$managerProfile = Read-RepoFile '.codex/agents/hmasd-workflow-design-manager.toml'
$skill = Read-RepoFile '.agents/skills/hmasd-workflow-change-audit/SKILL.md'
$harness = Read-RepoFile '.agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py'
$refreshScript = Read-RepoFile '.codex/refresh-model-catalog-v2-workaround.ps1'
$workflowMap = Read-RepoFile 'docs/project/WORKFLOW_MAP.md'
$router = Read-RepoFile 'AGENTS.md'
$sessionContract = Read-RepoFile 'docs/project/SESSION_WORKSPACE_CONTRACT.md'
$collaborationSkill = Read-RepoFile '.agents/skills/hmasd-collaborative-workflow-design/SKILL.md'
$defectQueue = Read-RepoFile 'docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md'
$reverseValidation = Read-RepoFile 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
$reverseExplorerRole = Read-RepoFile '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md'
$reverseWriterRole = Read-RepoFile '.agents/roles/RESEARCH_ARTIFACT_WRITER.md'
$normalizedManager = ($manager -replace '\s+', ' ').ToLowerInvariant()
$normalizedRouter = ($router -replace '\s+', ' ').ToLowerInvariant()
$normalizedSessionContract = ($sessionContract -replace '\s+', ' ').ToLowerInvariant()
$normalizedCollaborationSkill = ($collaborationSkill -replace '\s+', ' ').ToLowerInvariant()
$normalizedReverseContract = (($reverseValidation + $reverseExplorerRole + $reverseWriterRole + $workflowMap + $defectQueue) -replace '\s+', ' ').ToLowerInvariant()

$canonicalCatalogPath = 'C:\Projects\HMASD\runtime\model-catalog-v2-workaround.json'
$catalogMatch = [regex]::Match(
    $config, '(?m)^model_catalog_json\s*=\s*"([^"]+)"\s*$')
if (-not $catalogMatch.Success) { throw 'Missing model_catalog_json setting' }
$configuredCatalogPath = $catalogMatch.Groups[1].Value -replace '\\\\', '\'
if ($configuredCatalogPath -cne $canonicalCatalogPath) {
    throw "model_catalog_json must be exactly the canonical HMASD path: $canonicalCatalogPath"
}
$normalizedConfig = ($config -replace '\\\\', '\').ToLowerInvariant()
if ($normalizedConfig.Contains('c:\project\hmasd')) {
    throw 'model_catalog_json retains the external C:\project\HMASD checkout'
}

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
    'workflow_audit_skill=hmasd-workflow-change-audit',
    'workflow_harness=.agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py',
    'workflow_defect_repair_authority=autonomous_within_accepted_stable_contract')) {
    if (-not $manager.Contains($required)) { throw "WDM charter missing: $required" }
}

foreach ($required in @(
    'workflow_assignment_writing_skill=hmasd-writing-agent-assignments',
    'exact changed paths plus focused verification as completion evidence',
    'Expand to a named Skill or reference only when its action trigger fires')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM writing-agent routing contract missing: $required" }
}

foreach ($required in @(
    'workflow_change_request_route=root->wdm',
    'cross_task_transport=return_to_root',
    'workflow_subagent_parallelism=parallel_first_with_dependency_order',
    'tracked_writer_workspace=root_managed_worktree_required',
    'tracked_writer_exemptions=read_only|ignored_only|temporary_only',
    'mandatory_ticket_identity=forbidden_for_subagent_authority',
    'one writable l1 assignment',
    'one root-managed worktree',
    'distinct concurrent wdm/cpm l1 assignments',
    'integration/convergence uses a distinct worktree',
    'independent candidate/release lifecycle means a new l1')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant())) { throw "Router execution policy missing: $required" }
}

foreach ($required in @(
    'scope-key',
    '(role, scope_key)',
    'unique per root tree',
    'multiple active wdms',
    'disjoint frozen scopes')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant())) { throw "Router scope-key contract missing: $required" }
}
if (-not [regex]::IsMatch($router, '(?i)fork_turns\s*=\s*["'']?1["'']?')) {
    throw 'Root-to-WDM fork_turns=1 background context is missing'
}
if ($managerProfile -match '(?im)^fork_turns\s*=') {
    throw 'fork_turns must remain caller context rather than a WDM TOML field'
}

foreach ($required in @(
    'reverse_intake_payload=small_self_contained_semantic_delta',
    'reverse_intake_transport=assignment_specific_temporary_patch',
    'reverse_intake_writer=hmasd-research-artifact-writer',
    'reverse_intake_explorer_acceptance=full_read_semantic_accept_or_reject',
    'reverse_intake_root_action=exact_path_and_git_revision_check_then_exact_copy_install',
    'WDM owns this owner/transport/order/path interface',
    'does not own artifact integrity, map meaning or Explorer acceptance',
    'defect queue is evidence history only')) {
    if (-not $normalizedReverseContract.Contains($required.ToLowerInvariant())) {
        throw "Workflow reverse-intake boundary missing: $required"
    }
}

foreach ($required in @(
    'WDM owns workflow semantic design, modification and acceptance',
    'workflow_scope_key',
    'multiple active WDMs',
    'disjoint frozen scopes')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM execution policy missing: $required" }
}
if (-not $skill.Contains('workflow_hash_validation=forbidden')) {
    throw 'Workflow audit Skill missing hash prohibition'
}
foreach ($required in @(
    'accepts only its slice',
    'candidate-ready evidence',
    'root records/integrates candidates',
    'fresh convergence',
    'integrated union',
    'union acceptance',
    'workflow reviewer',
    'advisory',
    'cannot accept')) {
    $controlPlane = ($normalizedManager + ' ' + $normalizedRouter + ' ' + $normalizedSessionContract + ' ' + $normalizedCollaborationSkill)
    if (-not $controlPlane.Contains($required.ToLowerInvariant())) {
        throw "Scoped WDM/convergence contract missing: $required"
    }
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
    'Prefer positive capability text')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}

foreach ($required in @(
    'dispatch read-only auditor/scout concurrently with already-freezable implementation slices',
    'run disjoint implementer file families concurrently',
    'serialize only actual information dependencies or same-file writers',
    'same writable path',
    'shared unfrozen semantic contract',
    'candidate-ready evidence',
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

foreach ($forbidden in @('OneDrive root', 'legacy scan', 'legacy prune', 'legacy repair', 'scan/prune/repair')) {
    foreach ($surface in @($router, $manager, $collaborationSkill, $skill, $workflowMap)) {
        if ($surface.ToLowerInvariant().Contains($forbidden.ToLowerInvariant())) {
            throw "Stale workspace/legacy control remains: $forbidden"
        }
    }
}

if (-not $normalizedWorkflowMap.Contains('dispatch read-only auditor/scout concurrently with already-freezable implementation slices') -or
    -not $normalizedWorkflowMap.Contains('run disjoint implementer file families concurrently') -or
    -not $normalizedWorkflowMap.Contains('serialize only actual information dependencies or same-file writers') -or
    -not $normalizedWorkflowMap.Contains('workflow-file changes are performed by assigned workflow implementer leaves')) {
    throw 'Workflow Map execution policy missing parallel-first stages or registered implementer route'
}

foreach ($required in @(
    'workflow_subagent_parallelism=parallel_first_with_dependency_order',
    'run disjoint implementer file families concurrently',
    'serialize only actual information dependencies or same-file writers',
    'one writable l1 assignment',
    'one root-managed worktree')) {
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
$roleForkMatch = [regex]::Match(
    $workflowImplementer, '(?m)^default_fork_turns\s*=\s*([A-Za-z0-9_-]+)')
$profileForkMatch = [regex]::Match(
    $workflowImplementerProfile, 'fork_turns\s*=\s*([A-Za-z0-9_-]+)')
if (-not $roleForkMatch.Success -or -not $profileForkMatch.Success -or
    $roleForkMatch.Groups[1].Value -ne 'none' -or
    $profileForkMatch.Groups[1].Value -ne 'none' -or
    $roleForkMatch.Groups[1].Value -ne $profileForkMatch.Groups[1].Value) {
    throw 'Workflow implementer Role/profile fork_turns are inconsistent'
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
$normalizedImplementerRoleText = ($implementerRoleText -replace '\s+', ' ').ToLowerInvariant()
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
foreach ($required in @(
    'one writable L1 assignment = one Root-managed worktree',
    'parallel implementers may share that L1 worktree',
    'same frozen base',
    'exact disjoint paths',
    'one L1 slice candidate',
    'Root commits/records only after all children complete',
    'disjoint L2 writers share one L1 worktree',
    'L2 never has its own worktree lifecycle',
    'independent candidate/release lifecycle is a new L1',
    'current checkout is allowed only for read-only, ignored-only, or temporary-only assignments',
    'mixed tracked+ignored assignment is still classified as a tracked writer',
    'Root alone provisions, records, integrates, releases or retains the managed worktree and owns the Git lifecycle',
    'children never invoke helper or Git lifecycle')) {
    if (-not $normalizedImplementerRoleText.Contains($required.ToLowerInvariant())) {
        throw "Workflow implementer Root-managed writer contract missing: $required"
    }
}

$catalogPath = $configuredCatalogPath
if (-not [string]::IsNullOrWhiteSpace($CatalogTestPath)) {
    $catalogPath = $CatalogTestPath
}
if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
    throw "Selected model catalog is unavailable: $catalogPath"
}
$catalogBytes = [System.IO.File]::ReadAllBytes($catalogPath)
if ($catalogBytes.Length -ge 3 -and
    $catalogBytes[0] -eq 0xEF -and $catalogBytes[1] -eq 0xBB -and $catalogBytes[2] -eq 0xBF) {
    throw "Selected model catalog must not start with a UTF-8 BOM: $catalogPath"
}
try {
    $catalogText = [System.Text.UTF8Encoding]::new($false, $true).GetString($catalogBytes)
} catch {
    throw "Selected model catalog is not strict UTF-8: $catalogPath"
}
$firstJsonCharacter = ($catalogText -replace '^\s+', '')
if ([string]::IsNullOrEmpty($firstJsonCharacter) -or
    ($firstJsonCharacter[0] -ne '{' -and $firstJsonCharacter[0] -ne '[')) {
    throw "Selected model catalog must begin with { or [ after whitespace: $catalogPath"
}
try {
    $catalog = $catalogText | ConvertFrom-Json
} catch {
    throw "Selected model catalog is not valid JSON: $catalogPath"
}
if (-not $catalog.models) { throw 'Selected model catalog has no models array' }
foreach ($targetSlug in @('gpt-5.6-luna', 'gpt-5.3-codex-spark')) {
    $target = @($catalog.models | Where-Object { $_.slug -eq $targetSlug })
    if ($target.Count -ne 1) {
        throw "Selected model catalog must expose exactly one $targetSlug entry"
    }
    if ($target[0].multi_agent_version -ne 'v2') {
        throw "Selected model catalog must route $targetSlug through multi_agent_version=v2"
    }
}

if ($refreshScript -notmatch '(?i)\[System\.Text\.UTF8Encoding\]::new\(\$false\)') {
    throw 'Catalog refresh script must construct UTF8Encoding(false) explicitly'
}
if ($refreshScript -notmatch '(?i)\[System\.IO\.File\]::WriteAllText\(\$OutputPath,\s*\$jsonText,\s*\[System\.Text\.UTF8Encoding\]::new\(\$false\)\)') {
    throw 'Catalog refresh script must write catalog bytes through File.WriteAllText with the no-BOM encoding'
}
if ($refreshScript -match '(?im)Set-Content.*(?:\$OutputPath|OutputPath)') {
    throw 'Catalog refresh script must not use Set-Content for the catalog output path'
}

$selectedRoutes = @()
foreach ($profilePath in Get-ChildItem -LiteralPath (Join-Path $repo '.codex/agents') -Filter '*.toml' -File) {
    $profileText = Get-Content -Raw -LiteralPath $profilePath.FullName
    $modelRoute = [regex]::Match($profileText, '(?m)^model\s*=\s*"([^"]+)"')
    $effortRoute = [regex]::Match($profileText, '(?m)^model_reasoning_effort\s*=\s*"([^"]+)"')
    if ($modelRoute.Success -and $effortRoute.Success) {
        $selectedRoutes += [pscustomobject]@{
            Model = $modelRoute.Groups[1].Value
            Effort = $effortRoute.Groups[1].Value
            Profile = $profilePath.Name
        }
    }
}
foreach ($selected in $selectedRoutes) {
    $model = @($catalog.models | Where-Object { $_.slug -eq $selected.Model })
    if ($model.Count -ne 1) {
        throw "Selected model catalog entry missing for $($selected.Profile): $($selected.Model)"
    }
    $efforts = @($model[0].supported_reasoning_levels | ForEach-Object { $_.effort })
    if ($efforts -notcontains $selected.Effort) {
        throw "Selected model catalog does not support $($selected.Model)/$($selected.Effort) from $($selected.Profile)"
    }
}

Write-Output 'HMASD_WORKFLOW_DESIGN_DELEGATION_CONTRACT_OK'
