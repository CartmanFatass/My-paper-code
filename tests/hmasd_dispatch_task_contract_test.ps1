[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json'
$skill = Get-Content -LiteralPath $skillPath -Raw
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json
$agents = Get-Content -LiteralPath (Join-Path $repo 'AGENTS.md') -Raw
$review = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$monitor = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw

$expected = @('controller', 'project_manager', 'experiment_monitor')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 12 -or (Compare-Object $expected $actual)) {
    throw 'Persistent role graph must contain only controller, project_manager and experiment_monitor at schema 12'
}
if ($roles.roles.controller.thread_id -ne '019f8995-7550-7c82-8f31-ad08a3d381d4' -or
    $roles.roles.project_manager.thread_id -ne '019f8a2e-ed73-7a02-9bb9-4a57b2054cf3' -or
    $roles.roles.project_manager.registration_status -ne 'ACTIVE' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.registration_status -ne 'ACTIVE' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Persistent controller/manager/monitor binding mismatch'
}
foreach ($entry in $roles.roles.PSObject.Properties.Value) {
    foreach ($field in @('hostId', 'model', 'thinking')) {
        if ($null -ne $entry.PSObject.Properties[$field]) { throw "Static route field: $field" }
    }
}
foreach ($required in @(
    'The Controller owns routing',
    'Use `project_manager`',
    'controller <-> project_manager',
    'controller <-> experiment_monitor',
    'resolve_task_route.ps1 -Role <role>',
    'experiment_monitor',
    'hmasd-experiment-monitor',
    'gpt-5.3-codex-spark',
    'Controller-direct external review',
    '$hmasd-review-round',
    '$browser:control-in-app-browser',
    'Before `IMPLEMENTATION_READY`',
    'IMPLEMENTATION_READY',
    'RESEARCH_MANAGER_BLOCKED',
    'codex_app__send_message_to_thread',
    'PROJECT_MANAGER_DELIVERY_BLOCKED',
    '`controller` and calls',
    'resolve_source_boundary.ps1',
    'source_boundary=local_and_remote_aggressive_tip',
    'SOURCE_BOUNDARY_DIVERGED')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
foreach ($forbidden in @(
    'controller <-> research_project_manager',
    'controller <-> open_divergent_exchange',
    'open_divergent_exchange',
    '$hmasd-review-exchange',
    'REVIEW_STAGE_COMPLETE',
    'REVIEW_STAGE_BLOCKED',
    'agent://',
    'history://')) {
    if ($skill.Contains($forbidden)) { throw "Retired persistent edge remains: $forbidden" }
}
if ($skill.Contains('direct evidence intake')) {
    throw 'Dispatcher still assigns semantic evidence intake to Controller'
}
foreach ($required in @('$hmasd-dispatch-task', '$hmasd-review-round',
    '$browser:control-in-app-browser', '$hmasd-experiment-monitor',
    'bounded self-recovery', 'recovery attempts')) {
    if (-not $agents.Contains($required)) { throw "Controller contract missing: $required" }
    if (-not $skill.Contains($required)) { throw "Dispatcher recovery contract missing: $required" }
}
foreach ($required in @(
    'semantic_author=project_manager',
    'artifact_scope=reviewer_visible_code_side',
    'repair_owner=project_manager',
    'exact PM-accepted files unchanged',
    'pm_acceptance_authority=exclusive',
    'controller_validation_authority=none')) {
    if (-not $agents.Contains($required)) { throw "Controller semantic-ownership contract missing: $required" }
    if (-not $skill.Contains($required)) { throw "Dispatcher semantic-ownership contract missing: $required" }
}
foreach ($required in @(
    'inspect the registered conversation before submission',
    'never classifies scientific completeness',
    'late output from a retired role has no authority')) {
    if (-not $review.Contains($required)) { throw "Direct review contract missing: $required" }
}
foreach ($required in @('$hmasd-experiment-monitor', 'RECOVERY_ATTEMPT', 'recovery_exhausted=true')) {
    if (-not $monitor.Contains($required)) { throw "Monitor recovery contract missing: $required" }
}
$sourceResolver = Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_source_boundary.ps1'
if (-not (Test-Path -LiteralPath $sourceResolver -PathType Leaf)) { throw 'Missing source-boundary resolver' }
$sourceBoundary = & $sourceResolver | ConvertFrom-Json
if ($sourceBoundary.source_boundary -ne 'local_and_remote_aggressive_tip' -or
    $sourceBoundary.branch -ne 'aggressive' -or
    $sourceBoundary.source_commit -notmatch '^[0-9a-f]{40}$') {
    throw 'Source-boundary resolver did not return a canonical aggressive tip'
}
$resolver = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1') -Raw
foreach ($required in @("ValidateSet('controller', 'project_manager', 'experiment_monitor')", 'Unregistered Codex role', 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
if ($resolver.Contains('open_divergent_exchange')) { throw 'Role resolver retains retired Exchange route' }
$currentWork = Get-Content -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if (-not $currentWork.Contains($roles.roles.project_manager.thread_id) -or
    -not $currentWork.Contains($roles.roles.experiment_monitor.thread_id) -or
    -not $currentWork.Contains('Controller-direct external-Pro transport')) {
    throw 'Current boundary does not name the active direct-transport topology'
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
