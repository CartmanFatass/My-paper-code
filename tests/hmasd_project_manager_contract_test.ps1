[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skill = Get-Content (Join-Path $repo '.agents/skills/hmasd-project-manager/SKILL.md') -Raw
$managerYaml = Get-Content (Join-Path $repo '.agents/skills/hmasd-project-manager/agents/openai.yaml') -Raw
$config = Get-Content (Join-Path $repo '.codex/config.toml') -Raw
foreach ($required in @('CDC_DECISION_INTAKE','CDC_DECISION_BRIEF','START_IMPLEMENTATION','IMPLEMENTATION_PLAN_BRIEF','IMPLEMENTATION_READY','HMASDCodeScout','HMASDImplementer','HMASDVerifier','HMASDReviewer','native parent-child','This manager owns no heartbeat')) {
    if (-not $skill.Contains($required)) { throw "Project Manager missing: $required" }
}
if (-not $managerYaml.Contains('allow_implicit_invocation: false')) { throw 'Manager invocation must be explicit' }
foreach ($required in @('does not replace or independently converge','override or silently substitute','boundary fails twice')) {
    if (-not $skill.Contains($required)) { throw "Manager authority boundary missing: $required" }
}
$profiles = @{
    HMASDCodeScout = @('hmasd-code-scout.toml','model = "gpt-5.6-luna"','model_reasoning_effort = "high"','sandbox_mode = "read-only"')
    HMASDImplementer = @('hmasd-implementer.toml','model = "gpt-5.6-sol"','model_reasoning_effort = "high"','sandbox_mode = "workspace-write"')
    HMASDVerifier = @('hmasd-verifier.toml','model = "gpt-5.6-luna"','model_reasoning_effort = "high"','sandbox_mode = "workspace-write"')
    HMASDReviewer = @('hmasd-reviewer.toml','model = "gpt-5.6-sol"','model_reasoning_effort = "xhigh"','sandbox_mode = "read-only"')
}
foreach ($name in $profiles.Keys) {
    if (-not $config.Contains("[agents.`"$name`"]")) { throw "Custom agent not registered: $name" }
    $profile = Get-Content (Join-Path $repo ".codex/agents/$($profiles[$name][0])") -Raw
    foreach ($required in $profiles[$name][1..3]) {
        if (-not $profile.Contains($required)) { throw "$name profile missing: $required" }
    }
    if ($profile.Contains('$hmasd-dispatch-task')) { throw "$name uses persistent dispatcher" }
}
if (Test-Path (Join-Path $repo '.agents/skills/hmasd-implementer/SKILL.md')) { throw 'Superseded implementer Skill remains' }
if (Test-Path (Join-Path $repo '.agents/skills/hmasd-reviewer/SKILL.md')) { throw 'Superseded reviewer Skill remains' }
Write-Output 'HMASD_PROJECT_MANAGER_CONTRACT_OK'
