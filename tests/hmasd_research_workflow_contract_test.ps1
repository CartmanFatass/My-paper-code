[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expected = @('hmasd-browser-pro-exchange', 'hmasd-dispatch-task',
    'hmasd-experiment-monitor', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expected $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }

foreach ($legacyRoot in @('.claude/skills', '.claude/agents', 'docs/claude', 'docs/superpowers')) {
    $legacyPath = Join-Path $repo $legacyRoot
    if ((Test-Path -LiteralPath $legacyPath) -and
        @(Get-ChildItem -LiteralPath $legacyPath -File -Recurse).Count -gt 0) {
        throw "Retired Claude execution surface remains: $legacyRoot"
    }
}

$claude = Get-Content -LiteralPath (Join-Path $repo 'CLAUDE.md') -Raw
$retiredRolePattern = ('project' + '_manager|Project' + ' Manager|PROJECT' + '_MANAGER')
if (-not $claude.Contains('only an entry pointer') -or
    -not $claude.Contains('grants no separate authority') -or
    -not $claude.Contains('AGENTS.md') -or
    -not $claude.Contains('docs/project/CURRENT_WORK.md')) {
    throw 'CLAUDE.md is not a non-authoritative entry pointer'
}
if ($claude -match $retiredRolePattern -or
    $claude -match '(?i)\.claude[/\\](skills|agents)|docs[/\\]claude|CODEX_HOME') {
    throw 'CLAUDE.md retains a retired controller contract or implementation relay'
}

$gitignore = Get-Content -LiteralPath (Join-Path $repo '.gitignore') -Raw
if ($gitignore -notmatch '(?m)^\.claude/\r?$' -or
    $gitignore -notmatch '(?m)^\.superpowers/\r?$' -or
    $gitignore -match '(?m)^!\.claude/|^!docs/claude/|^!docs/superpowers/') {
    throw '.gitignore still exposes a retired Claude or Superpowers execution surface'
}

$reviewRound = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$expectedValidators = @(
    '.agents/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1',
    '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1')
foreach ($validatorPath in $expectedValidators) {
    if (-not $reviewRound.Contains(('`' + $validatorPath + '`'))) {
        throw "Review round missing canonical validator path: $validatorPath"
    }
}
$validatorPaths = @([regex]::Matches(
        $reviewRound, '(?:\.agents/|scripts/)[A-Za-z0-9_./-]+\.ps1') |
    ForEach-Object { $_.Value })
foreach ($validatorPath in $validatorPaths) {
    if (-not $validatorPath.StartsWith('.agents/skills/') -or
        -not (Test-Path -LiteralPath (Join-Path $repo $validatorPath) -PathType Leaf)) {
        throw "Review round contains a dangling validator path: $validatorPath"
    }
}

$current = Get-Content (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if (-not $current.Contains('unified OMP Controller') -or
    -not $current.Contains('.omp/agents/') -or
    -not $current.Contains('ACTIVE_AUTONOMOUS_RESEARCH_CHAIN') -or
    $current.Contains('PAUSED_AUTONOMOUS_RESEARCH_CHAIN') -or
    -not $current.Contains('Exactly five conclusion-bearing iteration') -or
    -not $current.Contains('without asking for') -or
    -not $current.Contains('intermediate approval') -or
    -not $current.Contains('shortest discriminating observation') -or
    -not $current.Contains('Git history is the archive') -or
    -not $current.Contains('key algorithm')) {
    throw 'Current control plane does not define the authorized five-round agile OMP state'
}
if ($current -match 'implementation and monitoring\s+surfaces are native Codex|native Codex, Git and evidence gates') {
    throw 'Current control plane retains an ambiguous native implementation surface'
}
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
$expectedRoles = @('controller', 'experiment_monitor')
$actualRoles = @($roles.roles.PSObject.Properties.Name)
if (Compare-Object $expectedRoles $actualRoles) { throw 'Unexpected persistent role graph' }
if ($roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.last_route_check -ne 'ARCHIVED_TASK') {
    throw 'Archived Monitor route is not represented fail-closed'
}
if ($roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Native Spark Monitor registry mismatch'
}

$dispatcher = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('controller -> local OMP task agents',
    'controller -> BrowserMCP Pro submission/capture',
    'controller -> one Pro completion monitor -> BrowserMCP wait/snapshot',
    'controller <-> experiment_monitor', 'gpt-5.3-codex-spark',
    'hmasd-exp-manager', 'hmasd-pro-monitor', 'hmasd-pro-monitor-luna',
    'openai-codex/gpt-5.6-luna:low')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
if ($dispatcher -match $retiredRolePattern) {
    throw 'Dispatcher retains the retired implementation relay'
}

$monitor = Get-Content (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw
foreach ($required in @('ETA', '10 minutes', 'delete the heartbeat', 'EXPERIMENT_MONITOR',
    'Do not modify repository files', 'Do not retry')) {
    if (-not $monitor.Contains($required)) { throw "Monitor Skill missing: $required" }
}

if (-not (Test-Path (Join-Path $repo '.omp/config.yml') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo '.omp/mcp.json') -PathType Leaf) -or
    -not (Test-Path (Join-Path $repo '.omp/agents') -PathType Container) -or
    -not (Test-Path (Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/SKILL.md') -PathType Leaf)) {
    throw 'Unified OMP and BrowserMCP execution surface is incomplete'
}
if (Test-Path (Join-Path $repo '.agents/skills/hmasd-review-exchange')) {
    throw 'Superseded persistent review Exchange remains'
}
if (Test-Path (Join-Path $repo '.codex')) { throw 'Superseded native Codex execution surface remains' }
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=unified_omp_controller'
