[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | Select-Object -ExpandProperty Name | Sort-Object)
$expected = @('hmasd-dispatch-task','hmasd-experiment','hmasd-project-manager','hmasd-review-exchange','hmasd-review-round') | Sort-Object
if (Compare-Object $expected $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }
$paths = @('AGENTS.md','docs/external-review/README.md','.agents/skills/hmasd-dispatch-task/SKILL.md','.agents/skills/hmasd-project-manager/SKILL.md','.agents/skills/hmasd-review-exchange/SKILL.md','.agents/skills/hmasd-review-round/SKILL.md','.codex/config.toml')
$text = ($paths | ForEach-Object { Get-Content (Join-Path $repo $_) -Raw }) -join "`n"
foreach ($required in @('open_divergent_exchange','research_project_manager','experiment_monitor','HMASDCodeScout','HMASDImplementer','HMASDVerifier','HMASDReviewer','native parent-child','active bounded autonomous grant','controller continuation')) {
    if (-not $text.Contains($required)) { throw "Active workflow missing: $required" }
}
foreach ($retired in @('.agents/skills/hmasd-implementer','.agents/skills/hmasd-reviewer','SCIENTIFIC_CONVERGENCE_TASK','RESEARCH_CONVERGENCE_BRIEF')) {
    if ($text.Contains($retired)) { throw "Superseded workflow remains active: $retired" }
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
