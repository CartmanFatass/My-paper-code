[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.omp/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @('hmasd-agile-research-development','hmasd-dispatch-task',
    'hmasd-experiment-monitor','hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) {
    throw "Unexpected retained Skill asset set: $($skills -join ',')"
}
if (Test-Path (Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/SKILL.md') -PathType Leaf) {
    throw 'Disabled BrowserMCP automation Skill remains in active discovery'
}
if (-not (Test-Path (Join-Path $repo '.omp/legacy/review-round/BROWSER_PRO_EXCHANGE_DISABLED.md') -PathType Leaf)) {
    throw 'Disabled BrowserMCP automation contract is missing from legacy evidence'
}
if (-not (Test-Path (Join-Path $repo '.omp/browsermcp-direct/start_browsermcp_direct.ps1') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo 'tests/browsermcp_direct_launcher_contract_test.ps1') -PathType Leaf)) {
    throw 'Controller-direct BrowserMCP launcher or focused contract is missing'
}
$currentWork = Get-Content (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
foreach ($required in @('autonomous_research_grant=ACTIVE_TEN_ITERATION_DECOUPLED_SKILL_LIFETIME_CHAIN',
    'grant_scope=s1_to_s10_simple_scene_cpu_review_design_implementation_evidence_successor',
    'iterations_remaining=7_authorized',
    'conclusion_bearing_iterations_consumed=3_on_claude',
    'formal_compute_status=not_started_no_iteration_4_compute_selected',
    'git_integration_status=Claude_only',
    'aggressive_branch_mutation=forbidden',
    'agent_assets=active_orchestration_consolidated_under_dot_omp_legacy_nonactive',
    'orchestration_asset_root=.omp',
    'end_to_end_research_loop=PRO_REVIEW_TO_CONTROLLER_PLAN_TO_LOCAL_OMP_IMPLEMENTATION_AND_REVIEW_TO_MONITORED_RUN_TO_PRO_RESULT_REVIEW',
    'experiment_monitor_status=ARCHIVED_REBUILD_REQUIRED_BEFORE_FIRST_CONCLUSION_BEARING_RUN',
    'primary_research_axis=decoupled_individual_skill_lifetime_from_global_k',
    'k_decoupling_current_result=PASS_ALCPS_CONTROLLED_STATE_DERIVATION',
    'k_next_legal_route=RETURN_S3_EXACT_RESULT_TO_REGISTERED_PRO',
    's2_result_status=NO_IDENTIFIABLE_EXCLUSIVE_SLOW_CHANNEL',
    'external_review_transport_status=ACTIVE_LUNA_HIGH_EXCHANGE_REVIEW_AGENT',
    'external_review_operator_agent=hmasd-exchange-review',
    'external_review_response_capture=PAGE_COPY_RESPONSE_BUTTON',
    'review_scout_status=ACTIVE_LOCAL_EXPERIENCE_RECORDER',
    'browsermcp_direct_launcher=.omp/browsermcp-direct/start_browsermcp_direct.ps1',
    'browsermcp_direct_timeout_ms=120000',
    'browsermcp_direct_implicit_type_snapshot=removed',
    'browsermcp_direct_live_status=CLICK_HOVER_TYPE_IMPLICIT_SNAPSHOTS_REMOVED_S2_ARCHIVE_COMPLETE',
    'active_assignment_id=S3_ALCPS_RESULT_EXTERNAL_REVIEW',
    'next_boundary=COMMIT_PUSH_S3_RESULT_THEN_RETURN_TO_REGISTERED_PRO',
    'next_action_class=external_review_controller_direct_transport',
    'active_scientific_direction=C_ALCPS_RESULT_AWAITING_EXTERNAL_PRO',
    's2_result_review_status=ALREADY_ARCHIVED_CONTROLLER_INTAKE_ACCEPTED',
    's3_result_status=PASS_ALCPS_CONTROLLED_STATE_DERIVATION',
    's3_code_required=false',
    's3_compute_required=false',
    's3_write_rate=2_over_7',
    's3_decoder_kernel_cardinality=2')) {
    if (-not $currentWork.Contains($required)) {
        throw "Claude inactive-import boundary missing: $required"
    }
}

$reviewRound = Get-Content (Join-Path $repo '.omp/skills/hmasd-review-round/SKILL.md') -Raw
foreach ($path in @(
    '.omp/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1',
    '.omp/skills/hmasd-browser-pro-exchange/scripts/render_browser_pro_dispatch.ps1',
    '.omp/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1',
    '.omp/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1',
    '.omp/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1')) {
    if (-not $reviewRound.Contains($path)) { throw "Review workflow omits executable interface: $path" }
    if (-not (Test-Path (Join-Path $repo $path) -PathType Leaf)) { throw "Missing workflow interface: $path" }
}
if (-not (Test-Path (Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/browser_pro_dispatch.psm1') -PathType Leaf)) {
    throw 'Missing shared Browser Pro dispatch constructor'
}
$roles = Get-Content (Join-Path $repo '.omp/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
if (Compare-Object @('controller','experiment_monitor') @($roles.roles.PSObject.Properties.Name)) {
    throw 'Unexpected persistent role graph'
}
if ($roles.schema_version -ne 26 -or
    $roles.external_review_transport.transport_exploration_enabled -or
    $roles.external_review_transport.status -ne 'ACTIVE_LUNA_HIGH_EXCHANGE_REVIEW_AGENT' -or
    $roles.external_review_transport.automation_skill_enabled -or
    $roles.external_review_transport.automation_skill_archive -ne '.omp/legacy/review-round/BROWSER_PRO_EXCHANGE_DISABLED.md' -or
    $roles.external_review_transport.operator_agent -ne 'hmasd-exchange-review' -or
    $roles.external_review_transport.operator_profile -ne '.omp/agents/hmasd-exchange-review.md' -or
    $roles.external_review_transport.connection_state -ne 'REGISTERED_TAB_PREFLIGHT_REQUIRED_EVERY_ASSIGNMENT' -or
    $roles.external_review_transport.authenticated_registered_tab_prerequisite -ne 'ONE_TIME_ENVIRONMENTAL_NOT_ROUTINE_STEP' -or
    $roles.external_review_transport.routine_human_interaction_allowed -or
    $roles.external_review_transport.response_capture -ne 'page_copy_response_button' -or
    $roles.external_review_transport.keyboard_copy_allowed -or
    $roles.external_review_transport.dispatch_marker -ne 'HMASD_BP_D1' -or
    $roles.external_review_transport.dispatch_max_utf16_code_units -ne 352 -or
    $roles.external_review_transport.receipt_schema -ne 'hmasd.browser_pro_submission.v2' -or
    $roles.external_review_transport.file_upload_allowed -or
    $roles.external_review_transport.full_question_browser_type_allowed) {
    throw 'Luna-high Browser Pro transport registry changed'
}
if ($roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.last_route_check -ne 'ARCHIVED_TASK' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.role_skill -ne '.omp/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Archived experiment Monitor route changed'
}
$dispatcher = Get-Content (Join-Path $repo '.omp/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('controller -> local OMP task agents',
    'controller -> hmasd-exchange-review -> BrowserMCP Pro exchange',
    'controller <-> experiment_monitor', 'gpt-5.3-codex-spark',
    'hmasd-exp-manager', 'hmasd-review-scout', 'hmasd-exchange-review',
    'hmasd-frontier-implementer', 'BUG_UNRESOLVED', 'five repair attempts',
    'openai-codex/gpt-5.6-sol:max', 'Controller/main conversation alone',
    'compares 2-3 approaches', 'FINAL_IMPLEMENTATION_ROUND_REVIEW',
    'complete planned package', 'External review transport', 'Copy response')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
$controller = Get-Content (Join-Path $repo 'AGENTS.md') -Raw
foreach ($required in @('No external-review transport Skill is active',
    'hmasd-exchange-review', 'Luna-high', 'one-time environmental prerequisite',
    'no-clobber receipt', 'BrowserMCP automation Skill remains disabled',
    'Copy response', 'Controller alone performs')) {
    if (-not $controller.Contains($required)) { throw "Controller does not expose exchange-review topology: $required" }
}
foreach ($removed in @('hmasd-pro-monitor','hmasd-pro-monitor-luna')) {
    if ($dispatcher.Contains($removed) -or $reviewRound.Contains($removed)) { throw "Removed route remains: $removed" }
    if (Test-Path (Join-Path $repo ".omp/agents/$removed.md")) { throw "Removed profile remains: $removed" }
}
$reviewScout = Get-Content (Join-Path $repo '.omp/agents/hmasd-review-scout.md') -Raw
foreach ($required in @('tools: [read, grep, glob, edit, write]',
    'never operate a browser', 'explicit user approval')) {
    if (-not $reviewScout.Contains($required)) { throw "review_scout profile missing: $required" }
}
if (-not (Test-Path (Join-Path $repo '.omp/review_scout/EXPERIENCE.md') -PathType Leaf)) {
    throw 'review_scout experience record is missing'
}
$experience = Get-Content (Join-Path $repo '.omp/review_scout/EXPERIENCE.md') -Raw
if (-not $experience.Contains('Stable automated end-to-end cycles: 0')) {
    throw 'review_scout stable-cycle count changed before one qualifying end-to-end cycle'
}
$acceptedRound = Join-Path $repo 'docs/external-review/rounds/20260724_alpsw_s1_result_review'
foreach ($required in @('19_BROWSER_PRO_SUBMISSION.json','21_PRO_OPEN_RAW.md',
    '30_EVIDENCE_RECONCILIATION.md')) {
    if (-not (Test-Path (Join-Path $acceptedRound $required) -PathType Leaf)) {
        throw "Accepted S1 result round is missing $required"
    }
}
$acceptedS2Round = Join-Path $repo 'docs/external-review/rounds/20260724_alpsc_s2_result_review'
foreach ($required in @('19_BROWSER_PRO_SUBMISSION.json','21_PRO_OPEN_RAW.md',
    '30_EVIDENCE_RECONCILIATION.md')) {
    if (-not (Test-Path (Join-Path $acceptedS2Round $required) -PathType Leaf)) {
        throw "Accepted S2 result round is missing $required"
    }
}
if (-not $currentWork.Contains('browser_pro_round_state=ALREADY_ARCHIVED_CONTROLLER_INTAKE_ACCEPTED_S2_RESULT')) {
    throw 'CURRENT_WORK accepted S2 result round state changed'
}
foreach ($required in @(
    'docs/research/cdc/EVIDENCE_NOTES/20260723_ALPSW_IDENTIFIABILITY_DERIVATION_S1.md',
    'docs/report/DECOUPLED_SKILL_LIFETIME_ITERATION_1.md',
    'docs/research/cdc/EVIDENCE_NOTES/20260724_EXCLUSIVE_SLOW_CHANNEL_IDENTIFIABILITY_S2.md',
    'docs/report/DECOUPLED_SKILL_LIFETIME_ITERATION_2.md',
    'docs/research/cdc/EVIDENCE_NOTES/20260724_ALPSC_S2_RESULT_AND_ALCPS_S3_DIRECTION.md',
    'docs/research/cdc/EVIDENCE_NOTES/20260724_AGENT_LOCAL_CONTROLLED_PREDICTIVE_STATE_S3.md',
    'docs/report/DECOUPLED_SKILL_LIFETIME_ITERATION_3.md')) {
    if (-not (Test-Path (Join-Path $repo $required) -PathType Leaf)) {
        throw "Conclusion boundary is missing $required"
    }
}
$monitor = Get-Content (Join-Path $repo '.omp/skills/hmasd-experiment-monitor/SKILL.md') -Raw
foreach ($required in @('ETA','10 minutes','delete the heartbeat','EXPERIMENT_MONITOR',
    'Do not modify repository files','Do not retry')) {
    if (-not $monitor.Contains($required)) { throw "Experiment Monitor Skill missing: $required" }
}
$resolverPath = Join-Path $repo '.omp/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1'
if (-not (Test-Path $resolverPath -PathType Leaf) -or
    -not $monitor.Contains('`.omp/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1 -Role controller`')) {
    throw 'Experiment Monitor terminal route does not resolve through the native OMP Skill root'
}
$activeSkillText = @(Get-ChildItem (Join-Path $repo '.omp/skills') -Recurse -File |
    ForEach-Object { Get-Content $_.FullName -Raw }) -join "`n"
foreach ($forbiddenSurface in @('$browser:control-in-app-browser',
    'HMASD PROJECT-MANAGER-DIRECT PRO REVIEW HEARTBEAT',
    'This wake belongs to the active Project Manager')) {
    if ($activeSkillText.Contains($forbiddenSurface)) {
        throw "Retired review surface remains active: $forbiddenSurface"
    }
}
if (-not (Test-Path (Join-Path $repo '.omp/config.yml') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo '.omp/mcp.json') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo '.omp/agents') -PathType Container)) {
    throw 'Unified OMP and BrowserMCP execution surface is incomplete'
}
if (Test-Path (Join-Path $repo '.agents')) { throw 'Active legacy .agents root remains' }
if (Test-Path (Join-Path $repo '.codex')) { throw 'Active legacy .codex root remains' }
foreach ($legacy in @('.omp/legacy/roles/PROJECT_MANAGER.md',
    '.omp/legacy/roles/EXPERIMENT_OPERATOR.md',
    '.omp/legacy/codex/config.toml')) {
    if (-not (Test-Path (Join-Path $repo $legacy) -PathType Leaf)) {
        throw "Migrated legacy asset is missing: $legacy"
    }
}
$expectedWorkflow = @('external_pro_scientific_review','controller_intake_and_frozen_plan',
    'local_omp_implementation_and_collective_review','authorized_run_with_experiment_monitor',
    'controller_result_intake','external_pro_result_review')
if ($roles.asset_root.root -ne '.omp' -or $roles.asset_root.legacy_active -or
    (Compare-Object $expectedWorkflow @($roles.workflow_sequence))) {
    throw 'Portable OMP asset root or end-to-end research loop changed'
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=pro_code_monitor_pro asset_root=.omp'
