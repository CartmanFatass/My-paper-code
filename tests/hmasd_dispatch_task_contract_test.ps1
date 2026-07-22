[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json'
$skill = Get-Content -LiteralPath $skillPath -Raw
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json

$expected = @('controller', 'open_divergent_exchange')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 8 -or (Compare-Object $expected $actual)) {
    throw 'Persistent role graph must contain only controller and open_divergent_exchange at schema 8'
}
if ($roles.roles.controller.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
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
    'registered Controller task ID')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
foreach ($forbidden in @('controller <-> research_project_manager', 'controller <-> experiment_monitor')) {
    if ($skill.Contains($forbidden)) { throw "Retired persistent edge remains: $forbidden" }
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
