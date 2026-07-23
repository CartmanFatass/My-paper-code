[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expected = @('hmasd-dispatch-task', 'hmasd-experiment-monitor',
    'hmasd-review-exchange', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expected $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }

$current = Get-Content (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
$legacyToken = 'O' + 'MP'
if ($current -match "(?i)\b$legacyToken\b|\.omp") { throw 'Current control plane retains a legacy execution route' }
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
foreach ($role in @('project_manager', 'experiment_monitor', 'open_divergent_exchange')) {
    if ($roles.roles.$role.registration_status -ne 'ACTIVE') { throw "Inactive registered role: $role" }
}
if ($roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Native Spark Monitor registry mismatch'
}

$dispatcher = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('controller <-> project_manager', 'controller <-> experiment_monitor',
    'controller <-> open_divergent_exchange', 'source_boundary=local_and_remote_aggressive_tip',
    'gpt-5.3-codex-spark', 'PROJECT_MANAGER_DELIVERY_BLOCKED')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
if ($dispatcher -match '(?i)\bOMP\b|agent://|history://') { throw 'Dispatcher retains a legacy task-delivery path' }

$monitor = Get-Content (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw
foreach ($required in @('ETA', '10 minutes', 'delete the heartbeat', 'EXPERIMENT_MONITOR',
    'Do not modify repository files', '$hmasd-experiment-monitor', 'RECOVERY_ATTEMPT',
    'recovery_exhausted=true')) {
    if (-not $monitor.Contains($required)) { throw "Monitor Skill missing: $required" }
}

if (Test-Path (Join-Path $repo ('.o' + 'mp'))) { throw 'Legacy execution directory remains' }

$batteryDocuments = @{
    'docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'K=1', 'C_total', 'I_TV')
    'docs/project/IMPLEMENTATION_PLAN.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'C_total', 'LCB(C_total_KEEP)>0',
        'LCB(C_total_RENEW)>0')
    'docs/project/CURRENT_WORK.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'four conclusion-bearing iterations')
}
foreach ($relative in $batteryDocuments.Keys) {
    $content = Get-Content (Join-Path $repo $relative) -Raw
    foreach ($required in $batteryDocuments[$relative]) {
        if (-not $content.Contains($required)) {
            throw "Battery contract is not reconciled in ${relative}: $required"
        }
    }
}
if ($current.Contains('One unresolved question stands against the result contract')) {
    throw 'Retired behavioral-battery question remains active in CURRENT_WORK'
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=native_codex'
