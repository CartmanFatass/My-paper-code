[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json'
$skill = Get-Content -LiteralPath $skillPath -Raw
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json

$expected = @('controller', 'project_manager', 'open_divergent_exchange')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 9 -or (Compare-Object $expected $actual)) {
    throw 'Persistent role graph must contain controller, project_manager and open_divergent_exchange at schema 9'
}
if ($roles.roles.controller.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
    $roles.roles.project_manager.thread_id -ne '019f898b-2c57-79c0-a158-e694295b2254' -or
    $roles.roles.project_manager.registration_status -ne 'ACTIVE' -or
    $roles.roles.open_divergent_exchange.thread_id -ne '019f716c-3c8a-7891-8c89-c94dc94fab4c' -or
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
    'Controller direct control-plane work',
    'Persistent Codex `project_manager`',
    'controller <-> project_manager',
    '-Role project_manager',
    'callers never supply or search for a task ID',
    'hmasd-project-manager',
    'isolated: true',
    'hmasd-experiment-monitor',
    'monitor-<run-id>',
    'open_divergent_exchange',
    'controller <-> open_divergent_exchange',
    'automatic result delivery',
    'agent://',
    'history://',
    'Resolve the same task again immediately after delivery',
    'already-terminal',
    'replacement reads retained status',
    'REVIEW_STAGE_COMPLETE',
    'REVIEW_STAGE_BLOCKED',
    'source_thread_id',
    'registered Controller task ID',
    'Persistent Project Manager terminal delivery',
    'IMPLEMENTATION_READY',
    'RESEARCH_MANAGER_BLOCKED',
    'codex_app__send_message_to_thread',
    'PROJECT_MANAGER_DELIVERY_BLOCKED',
    'resolve `-Role controller`')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
foreach ($forbidden in @('controller <-> research_project_manager', 'controller <-> experiment_monitor', '-ThreadId <registered id>')) {
    if ($skill.Contains($forbidden)) { throw "Retired persistent edge remains: $forbidden" }
}
$resolver = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1') -Raw
foreach ($required in @("ValidateSet('controller', 'project_manager', 'open_divergent_exchange')", 'Unregistered Codex role', 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
$currentWork = Get-Content -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if ($currentWork.Contains('OMP: PAUSED') -and -not $currentWork.Contains($roles.roles.project_manager.thread_id)) {
    throw 'Paused-OMP boundary does not name the registered project_manager'
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
