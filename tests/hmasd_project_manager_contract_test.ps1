[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-project-manager/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-task-router/references/session-roles.json'
$agentsPath = Join-Path $repo 'AGENTS.md'
$reviewRoundPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'

$skill = (Get-Content -LiteralPath $skillPath -Raw) -replace '\s+', ' '
foreach ($required in @(
    'name: hmasd-project-manager',
    'PROJECT_REVIEW_TASK',
    'purpose=<CONVERGENT_ADOPTION|ROUTE_ALIGNMENT|HANDOFF_BRIEF>',
    'Research objective:',
    'build a more capable and robust MARL algorithm',
    'Diagnostic baseline:',
    'never become a universal prerequisite',
    'Ordinary MARL remains the strongest matched comparator',
    'does not by itself forbid designing or testing a structurally different algorithm',
    'This role is read-only',
    'Communicate only with the registered controller',
    'PROJECT_REVIEW_BRIEF',
    'verdict=<ALIGNED|REVISE|BLOCK>',
    'PROJECT_REVIEW_BLOCKED',
    'This bounded role needs no heartbeat')) {
    if (-not $skill.Contains($required)) {
        throw "Project Manager Skill is missing: $required"
    }
}

$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json
$manager = $roles.roles.research_project_manager
if ($roles.schema_version -ne 5 -or
    $manager.thread_id -ne '019f7e6e-2f81-7463-93a6-4bb836585fb8' -or
    $manager.registration_status -ne 'ACTIVE' -or
    $manager.role_skill -ne '.agents/skills/hmasd-project-manager/SKILL.md') {
    throw 'Research Project Manager registry binding is inconsistent'
}
foreach ($forbidden in @('hostId', 'model', 'thinking')) {
    if ($null -ne $manager.PSObject.Properties[$forbidden]) {
        throw "Research Project Manager registry mirrors live route field: $forbidden"
    }
}

$agents = (Get-Content -LiteralPath $agentsPath -Raw) -replace '\s+', ' '
$reviewRound = (Get-Content -LiteralPath $reviewRoundPath -Raw) -replace '\s+', ' '
foreach ($required in @(
    'Research Project Manager',
    'mission-alignment',
    'PROJECT_REVIEW_BRIEF')) {
    if (-not $agents.Contains($required) -and -not $reviewRound.Contains($required)) {
        throw "Controller workflow does not expose Project Manager boundary: $required"
    }
}
if (-not $reviewRound.Contains('only after `ALIGNED`') -or
    -not $reviewRound.Contains('It is not another scientific reviewer')) {
    throw 'Review-round adoption boundary is incomplete'
}

Write-Output 'HMASD_PROJECT_MANAGER_CONTRACT_OK'
