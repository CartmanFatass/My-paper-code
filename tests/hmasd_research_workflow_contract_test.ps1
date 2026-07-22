[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @('hmasd-dispatch-task', 'hmasd-review-exchange', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }
$currentWork = Get-Content -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if ($currentWork.Contains('OMP: PAUSED')) {
    $roles = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
    $dispatcher = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
    if ($roles.roles.project_manager.registration_status -ne 'ACTIVE' -or
        $roles.roles.project_manager.thread_id -ne '019f898b-2c57-79c0-a158-e694295b2254') {
        throw 'Paused-OMP mode requires the registered persistent Codex project_manager'
    }
    foreach ($required in @('Persistent Codex Project Manager delivery', '-Role project_manager', 'controller <-> project_manager')) {
        if (-not $dispatcher.Contains($required)) { throw "Paused-OMP dispatcher missing: $required" }
    }
    foreach ($forbidden in @('current OMP root task', 'authorized OMP Project Manager work', 'authorized rebuildable OMP Monitor work')) {
        if ($currentWork.Contains($forbidden)) { throw "Paused-OMP active boundary retains OMP authority: $forbidden" }
    }
    Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=codex_persistent'
    exit 0
}
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
$config = Get-Content -LiteralPath (Join-Path $repo '.omp/config.yml') -Raw
foreach ($required in @('skills:', 'includeSkills:', '- "hmasd-*"')) {
    if (-not $config.Contains($required)) { throw "Project Skill allowlist missing: $required" }
}
if ($config.Contains('skills.enabled: false') -or $config.Contains('using-superpowers')) {
    throw 'Project Skill filter must preserve HMASD Skills and exclude Superpowers by allowlist'
}

if ($null -eq (Get-Command omp -ErrorAction SilentlyContinue)) {
    throw 'OMP CLI is required to verify the effective project Skill boundary'
}
$effective = @{}
Push-Location $repo
try {
    foreach ($key in @('skills.includeSkills', 'skills.enabled', 'skills.enableAgentsProject')) {
        $effective[$key] = (& omp config get $key | Out-String).Trim()
        if ($LASTEXITCODE -ne 0) { throw "OMP config lookup failed: $key" }
    }
} finally {
    Pop-Location
}
if ($effective['skills.includeSkills'] -ne '["hmasd-*"]' -or
    $effective['skills.enabled'] -ne 'true' -or
    $effective['skills.enableAgentsProject'] -ne 'true') {
    throw "Unexpected effective project Skill boundary: $($effective | ConvertTo-Json -Compress)"
}

$managerProfile = Get-Content -LiteralPath (Join-Path $repo '.omp/agents/hmasd-project-manager.md') -Raw
foreach ($required in @(
    'Before any',
    'implementation begins',
    'changes any protected algorithm semantics',
    'couples several',
    'needs more than one writer',
    'whether you edit directly',
    'Only ordinary, uncoupled, single-writer work with no protected')) {
    if (-not $managerProfile.Contains($required)) { throw "Project Manager planning safeguard missing: $required" }
}

$agentContext = Get-Content -LiteralPath (Join-Path $repo 'docs/project/AGENT_CONTEXT.md') -Raw
foreach ($required in @(
    'Any protected-semantics change',
    'requires its frozen plan before',
    'reward and',
    'recurrent state')) {
    if (-not $agentContext.Contains($required)) { throw "Agent design safeguard missing: $required" }
}

$engineering = Get-Content -LiteralPath (Join-Path $repo 'docs/project/ENGINEERING_ADDITIONS.md') -Raw
foreach ($required in @(
    'replica dimension inside one known-good process',
    'per replica is not a scaling strategy',
    'Batch branches and replicas when they are independent')) {
    if (-not $engineering.Contains($required)) { throw "Engineering topology safeguard missing: $required" }
}

$lightweight = @(
    'docs/project/AGENT_CONTEXT.md',
    '.omp/agents/hmasd-project-manager.md',
    '.omp/agents/hmasd-implementer.md') |
    ForEach-Object { Get-Content -LiteralPath (Join-Path $repo $_) -Raw }
$lightweight = $lightweight -join "`n"
foreach ($required in @(
    'conclusion-bearing iteration',
    'Ordinary work does not require a separate',
    'Match proof to the claim',
    'Parallelize only genuinely independent scopes',
    'independent reviewer for protected semantics',
    'standalone spec or plan artifact',
    'Do not create a brainstorm, spec or broad implementation plan')) {
    if (-not $lightweight.Contains($required)) { throw "Lightweight execution principle missing: $required" }
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
