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
$routeTable = Read-RepoFile 'docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md'
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

function Get-SessionField([string]$Name) {
    $pattern = '(?m)^' + [regex]::Escape($Name) + '=(.+)$'
    $match = [regex]::Match($sessionContract, $pattern)
    if (-not $match.Success) { throw "Session keyed contract field missing: $Name" }
    $match.Groups[1].Value.Trim()
}

function Get-KeyedRouteField([string]$Text, [string]$Name) {
    $pattern = '(?m)^' + [regex]::Escape($Name) + '=(.+)$'
    $match = [regex]::Match($Text, $pattern)
    if (-not $match.Success) { throw "Route-table keyed field missing: $Name" }
    $match.Groups[1].Value.Trim()
}

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
    @('.agents/roles/WORKFLOW_AUDITOR.md', '.codex/agents/hmasd-workflow-auditor.toml', 'hmasd-workflow-auditor', '[agents."HMASDWorkflowAuditor"]', 'gpt-5.6-terra', 'medium', 'read-only', 'WORKFLOW_IMPACT_PACKET'),
    @('.agents/roles/WORKFLOW_IMPLEMENTER.md', '.codex/agents/hmasd-workflow-implementer.toml', 'hmasd-workflow-implementer', '[agents."HMASDWorkflowImplementer"]', 'gpt-5.6-terra', 'medium', 'workspace-write', 'WORKFLOW_CHANGE_PACKET'),
    @('.agents/roles/WORKFLOW_REVIEWER.md', '.codex/agents/hmasd-workflow-reviewer.toml', 'hmasd-workflow-reviewer', '[agents."HMASDWorkflowReviewer"]', 'gpt-5.6-terra', 'high', 'read-only', 'WORKFLOW_REVIEW_PACKET'))

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
    'workflow_defect_repair_authority=Root_compiled_explicit_user_authorization_boundary')) {
    if (-not $manager.Contains($required)) { throw "WDM charter missing: $required" }
}

foreach ($required in @(
    'workflow_assignment_writing_skill=hmasd-writing-agent-assignments',
    'exact changed paths plus focused verification as completion evidence',
    'Expand to a named Skill or reference only when its action trigger fires')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM writing-agent routing contract missing: $required" }
}

# Plain-language is a small universal pointer in the router; the writing Skill
# and Session Contract carry the detailed meaning.  Keep this source-level
# check structural meaning rather than requiring one exact sentence or heading.
$plainLanguageSurfaces = @($skill, $sessionContract)
$normalizedPlainLanguageSurfaces = (($skill + "`n" + $sessionContract) -replace '\s+', ' ').ToLowerInvariant()
if (-not ($plainLanguageSurfaces -join ' ').ToLowerInvariant().Contains('plain-language') -and
    -not ($plainLanguageSurfaces -join ' ').ToLowerInvariant().Contains('plain language')) {
    throw 'Plain-language-first contract is missing from the detailed sources'
}
foreach ($detailGroup in @(
    'concrete objects|concrete files, objects or decisions',
    'their relationship|how they relate|causal relationship',
    'responsible owner|owner of the relevant action|next responsible actor',
    'consequence|what breaks',
    'paths, fields, abbreviations, commands, statuses, or evidence|fields, paths, abbreviations, commands, statuses or evidence|paths, commands, statuses and evidence|exact fields or other mechanical anchors')) {
    $detailLowers = @($detailGroup.Split('|') | ForEach-Object { $_.ToLowerInvariant() })
    if (-not ($detailLowers | Where-Object { $normalizedPlainLanguageSurfaces.Contains($_) })) {
        throw "Detailed plain-language contract missing: $detailGroup"
    }
    # The router may state the small universal semantic rule (objects,
    # relationship, owner and next action). Only detailed technical-tail
    # wording must remain in the Skill/Session sources.
    if ($detailGroup.StartsWith('paths, fields,') -and
        ($detailLowers | Where-Object { $router.ToLowerInvariant().Contains($_) })) {
        throw "Router duplicates detailed plain-language wording: $detailGroup"
    }
}
if (-not ($router.ToLowerInvariant().Contains('plain-language') -or
          $router.ToLowerInvariant().Contains('plain language') -or
          $router.ToLowerInvariant().Contains('ordinary-language'))) {
    throw 'Router lacks the universal plain-language pointer'
}
if (-not $router.ToLowerInvariant().Contains('hmasd-writing-agent-assignments') -or
    -not $router.ToLowerInvariant().Contains('session_workspace_contract')) {
    throw 'Router plain-language pointer does not name both detailed sources'
}

$plainExample = 'Root combined the frozen edits to `AGENTS.md` and `docs/project/SESSION_WORKSPACE_CONTRACT.md`. The two files must describe the same plain-language rule; WDM owns resolving any disagreement, and Root cannot accept the combined change until that conflict is resolved. This is the union-semantics check.'
foreach ($cue in @('AGENTS.md', 'SESSION_WORKSPACE_CONTRACT.md', 'two files', 'WDM', 'conflict', 'cannot accept')) {
    if (-not $plainExample.ToLowerInvariant().Contains($cue.ToLowerInvariant())) {
        throw "Positive plain-language example lacks structural cue: $cue"
    }
}
$ambiguousExample = 'Union semantics are complete; run integration.'
foreach ($missingCue in @('AGENTS.md', 'SESSION_WORKSPACE_CONTRACT.md', 'two files', 'WDM', 'conflict')) {
    if ($ambiguousExample.ToLowerInvariant().Contains($missingCue.ToLowerInvariant())) {
        throw "Ambiguous shorthand unexpectedly names structural cue: $missingCue"
    }
}
$plainTail = 'Paths/artifacts: `AGENTS.md` and `docs/project/SESSION_WORKSPACE_CONTRACT.md`; action/status: changed and ready; command/evidence: focused checks observed; WDM is next owner and no unresolved uncertainty remains.'
$twoLayerExample = $plainExample + "`n`n" + $plainTail
foreach ($tailCueGroup in @(
    'paths|artifacts|scope',
    'action|status|changed',
    'command|evidence|observed',
    'WDM|Root|next|unresolved|uncertain')) {
    if (-not ($tailCueGroup.Split('|') | Where-Object { $plainTail.ToLowerInvariant().Contains($_.ToLowerInvariant()) })) {
        throw "Positive factual tail lacks task-relevant cue: $tailCueGroup"
    }
}
$narrativeOnly = 'Root combined the two files because they must describe one rule. WDM resolves any disagreement, and Root waits when the conflict is unresolved.'
$fieldsOnly = 'status=TERMINAL; paths=`AGENTS.md`; command=integration; evidence=pending; owner=WDM.'
if ($narrativeOnly.Contains('status=') -or $narrativeOnly.Contains('paths=')) {
    throw 'Narrative-only negative unexpectedly has a fields-style factual tail'
}
if (-not $fieldsOnly.Contains('status=') -or -not $fieldsOnly.Contains('paths=') -or
    -not $fieldsOnly.Contains('evidence=')) {
    throw 'Fields-only negative lacks its deliberately mechanical tail'
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
    'root_managed_worktree_union_convergence=separate_worktree_for_multi_candidate_union_only',
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
    'Direction Action Map semantic-delta installation',
    'It never sends a full map',
    'Root alone accepts the complete Direction Action Map')) {
    $reverseSurface = (($reverseExplorerRole + $sessionContract) -replace '\s+', ' ')
    if (-not $reverseSurface.Contains($required)) {
        throw "Reverse-intake ownership transition missing: $required"
    }
}
if (-not $defectQueue.Contains(
        'reverse_intake_queue_role=evidence_log_only_not_dispatcher_or_scheduler')) {
    throw 'Workflow defect queue role missing: reverse_intake_queue_role=evidence_log_only_not_dispatcher_or_scheduler'
}

foreach ($required in @(
    'WDM owns workflow semantic design, modification and acceptance',
    'workflow_scope_key',
    'multiple active WDMs',
    'disjoint frozen scopes')) {
    if (-not $normalizedManager.Contains($required.ToLowerInvariant())) { throw "WDM execution policy missing: $required" }
}
if (-not $skill.Contains('Never use a hash, digest, byte count or fingerprint')) {
    throw 'Workflow audit Skill missing hash prohibition'
}
foreach ($required in @(
    'workflow_slice_result=wdm_accepts_exact_slice_then_returns_candidate_ready_packet',
    'workflow_candidate_integration=Root_records_and_integrates_candidate_set_after_all_children_finish',
    'workflow_union_convergence=conditional_on_workflow_multi_candidate_convergence_trigger',
    'workflow_change_risk_tiers=high|bounded_contract|low_causal_repair',
    'workflow_route_table_policy=clear_route_loads_defining_source_direct_consumers_focused_tests|missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor',
    'workflow_singleton_package=one_writable_WDM_L1_exact_final_frozen_bytes_reviewed_together',
    'workflow_singleton_acceptance=one_advisory_Reviewer_then_same_WDM_package_acceptance_before_Root_integration',
    'workflow_multi_candidate_convergence_trigger=two_or_more_independently_reviewed_WDM_candidates|actual_union_differs_from_every_reviewed_package',
    'workflow_causal_check_timing=when_all_consumed_bytes_are_frozen_before_package_acceptance',
    'workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report',
    'workflow_reviewer_authority=advice_only_no_acceptance')) {
    $name, $expected = $required.Split('=', 2)
    if ((Get-SessionField $name) -cne $expected) {
        throw "Scoped WDM/convergence contract missing: $required"
    }
}

foreach ($required in @(
    'control_plane_document_routes=docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md',
    'workflow_change_risk_tiers=high|bounded_contract|low_causal_repair',
    'workflow_route_table_policy=clear_route_loads_defining_source_direct_consumers_focused_tests|missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor',
    'workflow_singleton_package=one_writable_WDM_L1_exact_final_frozen_bytes_reviewed_together',
    'workflow_singleton_acceptance=one_advisory_Reviewer_then_same_WDM_package_acceptance_before_Root_integration',
    'workflow_multi_candidate_convergence_trigger=two_or_more_independently_reviewed_WDM_candidates|actual_union_differs_from_every_reviewed_package',
    'workflow_causal_check_timing=when_all_consumed_bytes_are_frozen_before_package_acceptance',
    'workflow_auditor_skip_evidence=concrete_WDM_rationale|focused_causal_evidence_on_all_frozen_consumed_bytes',
    'workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report')) {
    $name, $expected = $required.Split('=', 2)
    if ((Get-SessionField $name) -cne $expected) {
        throw "Canonical WDM efficiency contract missing: $required"
    }
}
if ((Get-SessionField 'workflow_auditor_policy') -cne
    'high_requires_Auditor|bounded_contract_clear_route_may_skip_with_WDM_rationale|low_causal_repair_may_skip_with_WDM_rationale|missing_ambiguous_conflicting_or_authority_crossing_route_requires_Auditor') {
    throw 'Canonical Auditor risk/route policy is stale'
}

if ((Get-KeyedRouteField $routeTable 'control_plane_document_routes') -cne
    'docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md') {
    throw 'Route table self-pointer is stale'
}
if ((Get-KeyedRouteField $routeTable 'control_plane_document_routes_not') -cne
    'task_state|history|hash|receipt|queue|admission|acceptance') {
    throw 'Route table stores forbidden state-bearing data'
}
$routeRows = @($routeTable -split "`r?`n" | Where-Object { $_.Trim().StartsWith('|') })
if ($routeRows.Count -lt 8) { throw "Route table must retain header, separator and its required routes: $($routeRows.Count)" }
$headerCells = @($routeRows[0].Trim('|').Split('|') | ForEach-Object { $_.Trim() })
if (($headerCells -join '|') -cne 'Trigger|Defining source|Direct consumers|Focused tests|Auditor escalation') {
    throw 'Route table columns drifted'
}
$triggers = @()
foreach ($row in $routeRows[2..7]) {
    $cells = @($row.Trim('|').Split('|') | ForEach-Object { $_.Trim() })
    if ($cells.Count -ne 5 -or ($cells | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -gt 0) {
        throw "Route table row is empty or malformed: $row"
    }
    $triggers += $cells[0]
    foreach ($cell in $cells[1..3]) {
        foreach ($match in [regex]::Matches($cell, '`([^`]+)`')) {
            $value = $match.Groups[1].Value
            if ($value -match '^https?://') { continue }
            if (-not (Test-Path -LiteralPath (Join-Path $repo $value) -PathType Leaf)) {
                throw "Route table path is missing: $value"
            }
        }
    }
}
if (@($triggers | Select-Object -Unique).Count -ne 6) { throw 'Route table triggers must be unique' }
if ($routeTable -match '(?m)^(?:assignment|history|hash|receipt|queue|admission|acceptance)(?:_|[a-z])*\s*=') {
    throw 'Route table contains a state-bearing keyed assignment'
}

foreach ($required in @(
    'root_advisory_portfolio_science_authority=',
    'independent_research_explorer_scope_key_forms=direction:<id>',
    'code_project_manager_scope_key_forms=direction:<id>|shared:<component>',
    'root_cross_owner_relay_authority=exclusive',
    'root_final_git_integration_authority=accepted_paths_only')) {
    if (-not $normalizedRouter.Contains($required.ToLowerInvariant())) {
        throw "Direction-scoped topology router invariant missing: $required"
    }
}
foreach ($required in @(
    'Mechanism budgets constrain only irreversible/high-cost actions',
    'focused contract evidence and qualitative maintainability',
    'one-line runtime checklist')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing bounded-efficiency rule: $required" }
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
$normalizedAuditSkill = ($skill -replace '\s+', ' ').ToLowerInvariant()
foreach ($required in @(
    'parent task model -> hmasd-writing-agent-assignments Skill -> self-contained',
    'assignment -> child judgment/result',
    'not a state machine, queue or admission gate')) {
    if (-not $normalizedWorkflowMap.Contains($required.ToLowerInvariant())) { throw "Workflow Map assignment dependency missing: $required" }
}

foreach ($required in @(
    'Mechanism budgets constrain only irreversible/high-cost actions',
    'If a failure means only “try again,” use the smallest direct',
    'One incident does not create a permanent rule',
    'Never use a hash, digest, byte count or fingerprint')) {
    if (-not $skill.Contains($required)) { throw "Workflow audit Skill missing: $required" }
}

foreach ($required in @(
    'workflow_validation_layers=slice_local|integration_cross_slice|runtime_fresh_smoke_after_root_integration_reload',
    'workflow_writer_full_suite=forbidden',
    'workflow_progress_event_names=DISPATCHED|WRITES_COMPLETE|TESTS_COMPLETE|REVIEW_READY|TERMINAL',
    'workflow_progress_event_semantics=status_observations_only|not_scheduler|not_queue|not_ledger|not_background_callback|not_retry_state|not_admission|not_acceptance_token',
    'workflow_integrated_review=exactly_one_advisory_Reviewer_after_TESTS_COMPLETE_and_REVIEW_READY',
    'workflow_root_l1_start_guidance=useful_owned_work_and_useful_action_or_matching_leaf_capacity',
    'workflow_windows_basetemp=short_absolute_assignment_specific_under_root_controlled_parent',
    'workflow_validation_failure_classes=environment_setup|product_assertion',
    'workflow_root_runtime_smoke=Root_only_after_integration_and_canonical_reload')) {
    $name, $expected = $required.Split('=', 2)
    if ((Get-SessionField $name) -cne $expected) { throw "Workflow keyed contract missing: $required" }
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

if (-not $normalizedWorkflowMap.Contains('independent frozen slices are parallel-first')) {
    throw 'Workflow Map stable parallel-first orientation is missing'
}
foreach ($required in @(
    'dispatch read-only auditor/scout concurrently with already-freezable implementation slices',
    'run exact disjoint implementers parallel-first',
    'serialize only actual information dependencies or same-file writers',
    'every mutation is carried out by a registered workflow implementer l2 on its exact assigned paths; wdm never writes')) {
    if (-not $normalizedAuditSkill.Contains($required)) {
        throw "Workflow audit Skill execution policy missing: $required"
    }
}

foreach ($required in @(
    'workflow_l1_parallelism=disjoint_frozen_workflow_scopes_only',
    'managed_worktree_allocation=one_writable_l1_assignment_one_root_managed_worktree',
    'l2_worktree_lifecycle=forbidden',
    'root_managed_worktree_authority=root_only',
    'workflow_max_threads_semantics=20_agent_tree_ceiling_only_not_runtime_authorization',
    'workflow_runtime_pool=forbidden')) {
    $name, $expected = $required.Split('=', 2)
    if ((Get-SessionField $name) -cne $expected) { throw "Parallel-first execution policy missing: $required" }
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

$normalizedMaintainabilityContract = (($manager + "`n" + $skill) -replace '\s+', ' ').ToLowerInvariant()
foreach ($required in @(
    'mechanism budgets constrain only irreversible/high-cost actions',
    'focused contract evidence and qualitative maintainability',
    'one-line runtime checklist')) {
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
