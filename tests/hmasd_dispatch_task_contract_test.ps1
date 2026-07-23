[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skill = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
$metadata = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/agents/openai.yaml') -Raw
$rolesRaw = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw
$roles = $rolesRaw | ConvertFrom-Json

$expectedRoles = @('controller', 'experiment_monitor')
if ($roles.schema_version -ne 21 -or (Compare-Object $expectedRoles @($roles.roles.PSObject.Properties.Name))) {
    throw 'Persistent role graph must contain only controller and experiment_monitor at schema 21'
}
if ($roles.roles.controller.thread_id -ne '019f8995-7550-7c82-8f31-ad08a3d381d4' -or
    $roles.roles.controller.kind -ne 'active_unified_omp_controller' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Persistent controller/experiment Monitor binding changed'
}
$transport = $roles.external_review_transport
$states = @('VALIDATED','RECONCILED_IDLE','DRAFT_CONFIRMED','SUBMISSION_CONFIRMED','GENERATING','STABLE_TWICE','ARCHIVED')
if ($transport.kind -ne 'controller_owned_browsermcp_state_machine' -or
    $transport.server -ne 'browsermcp-pro' -or
    $transport.package -ne '@browsermcp/mcp@0.1.3' -or
    $transport.connection_state -ne 'LIVE_PREFLIGHT_REQUIRED_EVERY_ROUND' -or
    $transport.evidence_transport -ne 'github_connector' -or
    $transport.repository -ne 'CartmanFatass/My-paper-code' -or
    $transport.review_branch -ne 'Claude' -or
    $transport.dispatch_marker -ne 'HMASD_BP_D1' -or
    $transport.dispatch_max_utf16_code_units -ne 352 -or
    $transport.dispatch_line_breaks_allowed -or $transport.browser_type_actions -ne 1 -or
    $transport.enter_action -ne 'separate_browser_press_key' -or $transport.file_upload_allowed -or
    $transport.full_question_browser_type_allowed -or
    $transport.type_timeout_policy -ne 'fresh_process_extension_connection_required_no_retry_retype_submit_even_empty_snapshot' -or
    $transport.receipt_schema -ne 'hmasd.browser_pro_submission.v2' -or
    $transport.wait_chunk_seconds -ne 20 -or
    -not $transport.controller_only -or
    $transport.fallback -ne 'none' -or
    (Compare-Object $states @($transport.state_machine))) {
    throw 'Controller-owned BrowserMCP transport mismatch'
}
foreach ($removedField in @('completion_monitor_agents','completion_monitor_mode','controller_only_actions')) {
    if ($null -ne $transport.PSObject.Properties[$removedField]) { throw "Removed monitor registry field remains: $removedField" }
}
$expectedLocal = @('hmasd-code-scout','hmasd-exp-manager','hmasd-frontier-implementer',
    'hmasd-implementer','hmasd-reviewer','hmasd-verifier') | Sort-Object
if ($roles.local_agents.root -ne '.omp/agents' -or -not $roles.local_agents.controller_dispatch_only -or
    $roles.local_agents.max_depth -ne 1 -or
    (Compare-Object $expectedLocal (@($roles.local_agents.types) | Sort-Object))) {
    throw 'Six-agent local OMP registry mismatch'
}
foreach ($entry in $roles.roles.PSObject.Properties.Value) {
    foreach ($field in @('hostId','model','thinking')) {
        if ($null -ne $entry.PSObject.Properties[$field]) { throw "Static route field remains: $field" }
    }
}
foreach ($required in @('controller -> local OMP task agents',
    'controller -> BrowserMCP Pro submission/observation/capture',
    'controller <-> experiment_monitor', 'The Controller owns scientific-to-code translation',
    'hmasd-code-scout', 'hmasd-implementer', 'hmasd-frontier-implementer',
    'hmasd-verifier', 'hmasd-reviewer', 'hmasd-exp-manager',
    'openai-codex/gpt-5.6-luna:high', 'openai-codex/gpt-5.6-sol:high',
    'openai-codex/gpt-5.6-sol:xhigh', 'openai-codex/gpt-5.6-sol:max',
    'openai-codex/gpt-5.3-codex-spark:high', 'resolve_task_route.ps1 -Role <role>',
    'current branch', 'working-tree changes', 'five repair attempts',
    'Controller/main conversation alone', 'compares 2-3 approaches',
    'Local agents execute that plan', 'FINAL_IMPLEMENTATION_ROUND_REVIEW',
    'complete planned package', 'BUG_UNRESOLVED', 'live preflight')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
foreach ($forbidden in @('hmasd-pro-monitor','hmasd-pro-monitor-luna','completion observer','completion monitor')) {
    if ($skill.Contains($forbidden) -or $metadata.Contains($forbidden) -or $rolesRaw.Contains($forbidden)) {
        throw "Removed Pro monitor route remains: $forbidden"
    }
}
$resolver = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1') -Raw
foreach ($required in @("ValidateSet('controller', 'experiment_monitor')", 'Unregistered Codex role', 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK topology=controller_inline_browser six_local_agents=true'
