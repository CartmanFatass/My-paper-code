[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @('hmasd-dispatch-task', 'hmasd-review-exchange', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }
$expectedAgents = @(
    'hmasd-project-manager.md',
    'hmasd-experiment-monitor.md',
    'hmasd-code-scout.md',
    'hmasd-implementer.md',
    'hmasd-verifier.md',
    'hmasd-reviewer.md')
foreach ($agent in $expectedAgents) {
    if (-not (Test-Path -LiteralPath (Join-Path $repo ".omp/agents/$agent") -PathType Leaf)) { throw "Missing active OMP agent: $agent" }
}
$activePaths = @(
    'AGENTS.md',
    'docs/project/CURRENT_WORK.md',
    'docs/external-review/README.md',
    '.agents/skills/hmasd-dispatch-task/SKILL.md',
    '.agents/skills/hmasd-review-exchange/SKILL.md',
    '.agents/skills/hmasd-review-round/SKILL.md',
    '.agents/skills/hmasd-dispatch-task/references/session-roles.json',
    '.omp/agents/hmasd-project-manager.md',
    '.omp/agents/hmasd-experiment-monitor.md')
$text = ($activePaths | ForEach-Object { Get-Content -LiteralPath (Join-Path $repo $_) -Raw }) -join "`n"
foreach ($required in @(
    'open_divergent_exchange',
    'hmasd-project-manager',
    'hmasd-experiment-monitor',
    'algorithm realization',
    'scientific direction',
    'direct evidence intake',
    'automatic result delivery',
    'controller continuation')) {
    if (-not $text.Contains($required)) { throw "Active workflow missing: $required" }
}
foreach ($retiredPath in @(
    '.agents/skills/hmasd-project-manager',
    '.agents/skills/hmasd-experiment',
    '.codex/agents',
    '.codex/config.toml',
    'runtime/model-catalog-v2-workaround.json',
    'scripts/register_g_info_monitor_task.ps1')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retiredPath)) { throw "Superseded workflow path remains: $retiredPath" }
}
foreach ($retired in @('controller <-> research_project_manager', 'controller <-> experiment_monitor', 'HMASDCodeScout', 'HMASDImplementer', 'HMASDVerifier', 'HMASDReviewer', 'CDC_DECISION_INTAKE')) {
    if ($text.Contains($retired)) { throw "Superseded active workflow remains: $retired" }
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
