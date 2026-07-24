[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skill = Get-Content (Join-Path $repo '.omp/skills/hmasd-dispatch-task/SKILL.md') -Raw
$metadata = Get-Content (Join-Path $repo '.omp/skills/hmasd-dispatch-task/agents/openai.yaml') -Raw
$rolesRaw = Get-Content (Join-Path $repo '.omp/skills/hmasd-dispatch-task/references/session-roles.json') -Raw
$roles = $rolesRaw | ConvertFrom-Json

$expectedRoles = @('controller', 'experiment_monitor')
if ($roles.schema_version -ne 25 -or (Compare-Object $expectedRoles @($roles.roles.PSObject.Properties.Name))) {
    throw 'Persistent role graph must contain only controller and experiment_monitor at schema 25'
}
$expectedWorkflow = @('external_pro_scientific_review','controller_intake_and_frozen_plan',
    'local_omp_implementation_and_collective_review','authorized_run_with_experiment_monitor',
    'controller_result_intake','external_pro_result_review')
if ($roles.asset_root.root -ne '.omp' -or $roles.asset_root.active_skills -ne '.omp/skills' -or
    $roles.asset_root.active_agents -ne '.omp/agents' -or $roles.asset_root.legacy_active -or
    (Compare-Object $expectedWorkflow @($roles.workflow_sequence))) {
    throw 'OMP asset root or end-to-end workflow sequence changed'
}
if ($roles.roles.controller.thread_id -ne '019f8995-7550-7c82-8f31-ad08a3d381d4' -or
    $roles.roles.controller.kind -ne 'active_unified_omp_controller' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.role_skill -ne '.omp/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Persistent controller/experiment Monitor binding changed'
}
$transport = $roles.external_review_transport
if ($transport.kind -ne 'controller_direct_browsermcp_exploration' -or
    -not $transport.transport_exploration_enabled -or
    $transport.status -ne 'EXPLORATION_NO_ACTIVE_TRANSPORT_SKILL' -or
    $transport.automation_skill_enabled -or
    $transport.automation_skill_archive -ne '.omp/legacy/review-round/BROWSER_PRO_EXCHANGE_DISABLED.md' -or
    $transport.skill_abstraction_gate -ne 'multiple_stable_automated_cycles_then_explicit_user_approval' -or
    $transport.experience_recorder -ne 'hmasd-review-scout' -or
    $transport.experience_path -ne '.omp/review_scout/EXPERIENCE.md' -or
    $transport.config -ne '.omp/mcp.json' -or
    $transport.server -ne 'browsermcp-pro' -or
    $transport.package -ne '@browsermcp/mcp@0.1.3' -or
    $transport.connection_state -ne 'EXPLORATION_LIVE_PREFLIGHT_REQUIRED' -or
    $transport.authenticated_registered_tab_prerequisite -ne 'ONE_TIME_ENVIRONMENTAL_NOT_ROUTINE_STEP' -or
    $transport.routine_human_interaction_allowed -or
    $transport.evidence_transport -ne 'github_connector' -or
    $transport.repository -ne 'CartmanFatass/My-paper-code' -or
    $transport.review_branch -ne 'Claude' -or
    $transport.dispatch_marker -ne 'HMASD_BP_D1' -or
    $transport.dispatch_max_utf16_code_units -ne 352 -or
    $transport.dispatch_line_breaks_allowed -or
    $transport.file_upload_allowed -or
    $transport.full_question_browser_type_allowed -or
    $transport.receipt_schema -ne 'hmasd.browser_pro_submission.v2' -or
    -not $transport.controller_only -or
    $transport.fallback -ne 'none') {
    throw 'Controller-direct BrowserMCP exploration registry mismatch'
}
foreach ($removedField in @('enabled','skill','skill_enabled','state_machine',
    'browser_type_actions','enter_action','type_timeout_policy','wait_chunk_seconds',
    'user_connected_tab_required','completion_monitor_agents','completion_monitor_mode',
    'controller_only_actions')) {
    if ($null -ne $transport.PSObject.Properties[$removedField]) { throw "Removed transport field remains: $removedField" }
}
$expectedLocal = @('hmasd-code-scout','hmasd-exp-manager','hmasd-frontier-implementer',
    'hmasd-implementer','hmasd-reviewer','hmasd-review-scout','hmasd-verifier') | Sort-Object
if ($roles.local_agents.root -ne '.omp/agents' -or -not $roles.local_agents.controller_dispatch_only -or
    $roles.local_agents.max_depth -ne 1 -or
    (Compare-Object $expectedLocal (@($roles.local_agents.types) | Sort-Object))) {
    throw 'Seven-agent local OMP registry mismatch'
}
foreach ($entry in $roles.roles.PSObject.Properties.Value) {
    foreach ($field in @('hostId','model','thinking')) {
        if ($null -ne $entry.PSObject.Properties[$field]) { throw "Static route field remains: $field" }
    }
}
foreach ($required in @('controller -> local OMP task agents',
    'controller -> direct BrowserMCP exploration -> hmasd-review-scout record',
    'controller <-> experiment_monitor', 'The Controller owns scientific-to-code translation',
    'hmasd-code-scout', 'hmasd-review-scout', 'hmasd-implementer',
    'hmasd-frontier-implementer', 'hmasd-verifier', 'hmasd-reviewer',
    'hmasd-exp-manager', 'openai-codex/gpt-5.6-luna:high',
    'openai-codex/gpt-5.6-sol:high', 'openai-codex/gpt-5.6-sol:xhigh',
    'openai-codex/gpt-5.6-sol:max', 'openai-codex/gpt-5.3-codex-spark:high',
    'resolve_task_route.ps1 -Role <role>', 'current branch',
    'working-tree changes', 'five repair attempts',
    'Controller/main conversation alone', 'compares 2-3 approaches',
    'Local agents execute that plan', 'FINAL_IMPLEMENTATION_ROUND_REVIEW',
    'complete planned package', 'BUG_UNRESOLVED',
    'External review transport exploration', 'explicitly approves')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
foreach ($forbidden in @('hmasd-pro-monitor','hmasd-pro-monitor-luna','completion observer','completion monitor')) {
    if ($skill.Contains($forbidden) -or $metadata.Contains($forbidden) -or $rolesRaw.Contains($forbidden)) {
        throw "Removed Pro monitor route remains: $forbidden"
    }
}
$resolver = Get-Content (Join-Path $repo '.omp/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1') -Raw
foreach ($required in @("ValidateSet('controller', 'experiment_monitor')", 'Unregistered Codex role', 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK topology=pro-code-monitor-pro asset_root=.omp'
