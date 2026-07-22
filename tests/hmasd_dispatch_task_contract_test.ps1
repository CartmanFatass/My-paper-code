[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skill = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
$expected = @('controller','research_project_manager','open_divergent_exchange','experiment_monitor')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 7 -or (Compare-Object $expected $actual)) { throw 'Persistent role graph mismatch' }
if ($roles.roles.controller.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
    $roles.roles.research_project_manager.role_skill -ne '.agents/skills/hmasd-project-manager/SKILL.md' -or
    $roles.roles.open_divergent_exchange.reviewer_role -ne 'OPEN_DIVERGENT' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment/SKILL.md') { throw 'Role binding mismatch' }
foreach ($entry in $roles.roles.PSObject.Properties.Value) {
    foreach ($field in @('hostId','model','thinking')) {
        if ($null -ne $entry.PSObject.Properties[$field]) { throw "Static route field: $field" }
    }
}
foreach ($required in @(
    'ordinary inspection, project management, Git',
    'external-Pro CDC decision intake or controller-authorized implementation management',
    'external GPT-5.6 Pro CDC decision',
    'monitoring an already authorized run',
    'controller <-> research_project_manager',
    'controller <-> open_divergent_exchange',
    'controller <-> experiment_monitor',
    'Temporary implementation and review subagents belong only to the Research',
    'Resolve the same task again immediately after delivery',
    'Controller continuation duty',
    'Do not stop at',
    'never prohibits controller continuation')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
