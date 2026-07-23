[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @('hmasd-browser-pro-exchange','hmasd-dispatch-task',
    'hmasd-experiment-monitor','hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }

$reviewRound = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
foreach ($path in @(
    '.agents/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1',
    '.agents/skills/hmasd-browser-pro-exchange/scripts/render_browser_pro_dispatch.ps1',
    '.agents/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1',
    '.agents/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1',
    '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1')) {
    if (-not $reviewRound.Contains($path)) { throw "Review workflow omits executable interface: $path" }
    if (-not (Test-Path (Join-Path $repo $path) -PathType Leaf)) { throw "Missing workflow interface: $path" }
}
if (-not (Test-Path (Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/scripts/browser_pro_dispatch.psm1') -PathType Leaf)) {
    throw 'Missing shared Browser Pro dispatch constructor'
}
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
if (Compare-Object @('controller','experiment_monitor') @($roles.roles.PSObject.Properties.Name)) {
    throw 'Unexpected persistent role graph'
}
if ($roles.schema_version -ne 21 -or
    $roles.external_review_transport.dispatch_marker -ne 'HMASD_BP_D1' -or
    $roles.external_review_transport.dispatch_max_utf16_code_units -ne 352 -or
    $roles.external_review_transport.receipt_schema -ne 'hmasd.browser_pro_submission.v2' -or
    $roles.external_review_transport.browser_type_actions -ne 1 -or
    $roles.external_review_transport.file_upload_allowed -or
    $roles.external_review_transport.full_question_browser_type_allowed) {
    throw 'Bounded Browser Pro transport registry changed'
}
if ($roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.last_route_check -ne 'ARCHIVED_TASK' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Archived experiment Monitor route changed'
}
$dispatcher = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('controller -> local OMP task agents',
    'controller -> BrowserMCP Pro submission/observation/capture',
    'controller <-> experiment_monitor', 'gpt-5.3-codex-spark',
    'hmasd-exp-manager', 'hmasd-frontier-implementer', 'BUG_UNRESOLVED',
    'five repair attempts', 'openai-codex/gpt-5.6-sol:max',
    'Controller/main conversation alone', 'compares 2-3 approaches',
    'FINAL_IMPLEMENTATION_ROUND_REVIEW', 'complete planned package',
    'no local observer', 'live preflight')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
$controller = Get-Content (Join-Path $repo 'AGENTS.md') -Raw
foreach ($required in @('one Controller-owned state machine',
    'No local or persistent role may', 'no-clobber submission receipt',
    'two stable snapshots', 'hmasd-exp-manager')) {
    if (-not $controller.Contains($required)) { throw "Controller does not expose frozen topology: $required" }
}
foreach ($removed in @('hmasd-pro-monitor','hmasd-pro-monitor-luna')) {
    if ($dispatcher.Contains($removed) -or $reviewRound.Contains($removed)) { throw "Removed route remains: $removed" }
    if (Test-Path (Join-Path $repo ".omp/agents/$removed.md")) { throw "Removed profile remains: $removed" }
}
$monitor = Get-Content (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw
foreach ($required in @('ETA','10 minutes','delete the heartbeat','EXPERIMENT_MONITOR',
    'Do not modify repository files','Do not retry')) {
    if (-not $monitor.Contains($required)) { throw "Experiment Monitor Skill missing: $required" }
}
if (-not (Test-Path (Join-Path $repo '.omp/config.yml') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo '.omp/mcp.json') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo '.omp/agents') -PathType Container)) {
    throw 'Unified OMP and BrowserMCP execution surface is incomplete'
}
if (Test-Path (Join-Path $repo '.agents/skills/hmasd-review-exchange')) { throw 'Superseded review Exchange remains' }
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=unified_controller_browser_state_machine'
