[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skill = Get-Content (Join-Path $repo '.agents/skills/hmasd-project-manager/SKILL.md') -Raw
$managerYaml = Get-Content (Join-Path $repo '.agents/skills/hmasd-project-manager/agents/openai.yaml') -Raw
$implementer = Get-Content (Join-Path $repo '.agents/skills/hmasd-implementer/SKILL.md') -Raw
$reviewer = Get-Content (Join-Path $repo '.agents/skills/hmasd-reviewer/SKILL.md') -Raw
foreach ($required in @('SCIENTIFIC_CONVERGENCE_TASK','START_IMPLEMENTATION','RESEARCH_CONVERGENCE_BRIEF','IMPLEMENTATION_READY','two or three temporary implementers','model=gpt-5.6-sol','reasoning_effort=high','reasoning_effort=xhigh','fork_turns=none','$hmasd-implementer','$hmasd-reviewer','This manager owns no heartbeat')) {
    if (-not $skill.Contains($required)) { throw "Project Manager missing: $required" }
}
if (-not $managerYaml.Contains('allow_implicit_invocation: false')) { throw 'Manager invocation must be explicit' }
if ($implementer.Contains('$hmasd-dispatch-task') -or $reviewer.Contains('$hmasd-dispatch-task')) { throw 'Temporary subagent uses persistent dispatcher' }
foreach ($text in @($implementer,$reviewer)) {
    foreach ($required in @('native parent-child','Do not read','AGENTS.md','CURRENT_WORK.md')) {
        if (-not $text.Contains($required)) { throw "Subagent isolation missing: $required" }
    }
}
Write-Output 'HMASD_PROJECT_MANAGER_CONTRACT_OK'
