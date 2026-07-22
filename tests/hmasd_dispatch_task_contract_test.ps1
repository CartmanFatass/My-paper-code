[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json'
$skill = Get-Content -LiteralPath $skillPath -Raw
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json

$expected = @('controller', 'project_manager', 'experiment_monitor', 'open_divergent_exchange')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 11 -or (Compare-Object $expected $actual)) {
    throw 'Persistent role graph must contain controller, project_manager, experiment_monitor and open_divergent_exchange at schema 11'
}
if ($roles.roles.controller.thread_id -ne '019f8995-7550-7c82-8f31-ad08a3d381d4' -or
    $roles.roles.project_manager.thread_id -ne '019f8a2e-ed73-7a02-9bb9-4a57b2054cf3' -or
    $roles.roles.project_manager.registration_status -ne 'ACTIVE' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.registration_status -ne 'ACTIVE' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md' -or
    $roles.roles.open_divergent_exchange.thread_id -ne '019f8a2f-22be-7db3-aa74-7fdeb9c03772' -or
    $roles.roles.open_divergent_exchange.reviewer_role -ne 'OPEN_DIVERGENT' -or
    $roles.roles.open_divergent_exchange.role_skill -ne '.agents/skills/hmasd-review-exchange/SKILL.md') {
    throw 'Persistent controller/Open-Pro binding mismatch'
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
    'resolve_task_route.ps1 -Role <role>',
    'experiment_monitor',
    'hmasd-experiment-monitor',
    'gpt-5.3-codex-spark',
    'open_divergent_exchange',
    'controller <-> open_divergent_exchange',
    'REVIEW_STAGE_COMPLETE',
    'REVIEW_STAGE_BLOCKED',
    'raw path',
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
foreach ($forbidden in @('controller <-> research_project_manager', 'agent://', 'history://')) {
    if ($skill.Contains($forbidden)) { throw "Retired persistent edge remains: $forbidden" }
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
foreach ($required in @("ValidateSet('controller', 'project_manager', 'experiment_monitor', 'open_divergent_exchange')", 'Unregistered Codex role', 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
$currentWork = Get-Content -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if (-not $currentWork.Contains($roles.roles.project_manager.thread_id) -or
    -not $currentWork.Contains($roles.roles.experiment_monitor.thread_id)) {
    throw 'Current boundary does not name the registered native roles'
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
