[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json'
$skill = Get-Content -LiteralPath $skillPath -Raw
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json

foreach ($legacyRoot in @('.claude/skills', '.claude/agents', 'docs/claude', 'docs/superpowers')) {
    $legacyPath = Join-Path $repo $legacyRoot
    if ((Test-Path -LiteralPath $legacyPath) -and
        @(Get-ChildItem -LiteralPath $legacyPath -File -Recurse).Count -gt 0) {
        throw "Retired Claude execution surface remains: $legacyRoot"
    }
}

$claude = Get-Content -LiteralPath (Join-Path $repo 'CLAUDE.md') -Raw
$retiredRelayPattern = ('project' + '_manager|Project' + ' Manager|PROJECT' + '_MANAGER')
if (-not $claude.Contains('only an entry pointer') -or
    -not $claude.Contains('grants no separate authority') -or
    -not $claude.Contains('AGENTS.md') -or
    -not $claude.Contains('docs/project/CURRENT_WORK.md')) {
    throw 'CLAUDE.md is not a non-authoritative entry pointer'
}
if ($claude -match $retiredRelayPattern -or
    $claude -match '(?i)\.claude[/\\](skills|agents)|docs[/\\]claude|CODEX_HOME') {
    throw 'CLAUDE.md retains a retired controller contract or implementation relay'
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

$expected = @('controller', 'experiment_monitor')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 19 -or (Compare-Object $expected $actual)) {
    throw 'Persistent role graph must contain only controller and experiment_monitor at schema 19'
}
if ($roles.roles.controller.thread_id -ne '019f8995-7550-7c82-8f31-ad08a3d381d4' -or
    $roles.roles.controller.kind -ne 'active_unified_omp_controller' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.registration_status -ne 'ARCHIVED_REBUILD_REQUIRED' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Persistent controller/Monitor binding mismatch'
}
if ($roles.external_review_transport.kind -ne 'controller_owned_browsermcp_with_readonly_task_monitor' -or
    $roles.external_review_transport.server -ne 'browsermcp-pro' -or
    $roles.external_review_transport.package -ne '@browsermcp/mcp@0.1.3' -or
    $roles.external_review_transport.state -ne 'CONNECTED_PREFLIGHT_OK' -or
    $roles.external_review_transport.evidence_transport -ne 'github_connector' -or
    $roles.external_review_transport.repository -ne 'CartmanFatass/My-paper-code' -or
    $roles.external_review_transport.review_branch -ne (& git.exe -C $repo branch --show-current).Trim() -or
    -not $roles.external_review_transport.long_lived_controller_required -or
    $roles.external_review_transport.completion_monitor_agents.primary -ne 'hmasd-pro-monitor' -or
    $roles.external_review_transport.completion_monitor_agents.backup -ne 'hmasd-pro-monitor-luna' -or
    $roles.external_review_transport.completion_monitor_agents.selection -ne 'exactly_one' -or
    $roles.external_review_transport.completion_monitor_mode -ne 'one_shot_wait_snapshot_only' -or
    $roles.external_review_transport.fallback -ne 'none') {
    throw 'BrowserMCP external-review transport mismatch'
}
$expectedLocal = @('hmasd-code-scout', 'hmasd-exp-manager',
    'hmasd-frontier-implementer', 'hmasd-implementer', 'hmasd-pro-monitor',
    'hmasd-pro-monitor-luna', 'hmasd-reviewer', 'hmasd-verifier') | Sort-Object
$actualLocal = @($roles.local_agents.types) | Sort-Object
if ($roles.local_agents.root -ne '.omp/agents' -or
    $roles.local_agents.controller_dispatch_only -ne $true -or
    $roles.local_agents.max_depth -ne 1 -or
    (Compare-Object $expectedLocal $actualLocal)) {
    throw 'Local OMP agent registry mismatch'
}
foreach ($entry in $roles.roles.PSObject.Properties.Value) {
    foreach ($field in @('hostId', 'model', 'thinking')) {
        if ($null -ne $entry.PSObject.Properties[$field]) { throw "Static route field: $field" }
    }
}
foreach ($required in @(
    'The Controller owns scientific-to-code translation',
    'controller -> local OMP task agents',
    'controller -> BrowserMCP Pro submission/capture',
    'controller -> one Pro completion monitor -> BrowserMCP wait/snapshot',
    'resolve_task_route.ps1 -Role <role>',
    'hmasd-code-scout',
    'hmasd-implementer',
    'hmasd-frontier-implementer',
    'hmasd-verifier',
    'hmasd-reviewer',
    'hmasd-exp-manager',
    'hmasd-pro-monitor',
    'hmasd-pro-monitor-luna',
    'openai-codex/gpt-5.6-luna:high',
    'openai-codex/gpt-5.6-sol:high',
    'openai-codex/gpt-5.6-sol:xhigh',
    'openai-codex/gpt-5.6-sol:max',
    'openai-codex/gpt-5.3-codex-spark:high',
    'openai-codex/gpt-5.3-codex-spark:medium',
    'openai-codex/gpt-5.6-luna:low',
    'experiment_monitor',
    'hmasd-experiment-monitor',
    'gpt-5.3-codex-spark',
    'hmasd-browser-pro-exchange',
    'browsermcp-pro',
    'current branch',
    'working-tree changes',
    'at most five repair attempts',
    'Controller/main conversation alone',
    'compare 2-3 approaches',
    'Local agents execute that plan',
    'FINAL_IMPLEMENTATION_ROUND_REVIEW',
    'complete planned package',
    'exactly one',
    'BUG_UNRESOLVED')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
$retiredRole = 'project' + '_manager'
$retiredTitle = 'Project' + ' Manager'
$retiredUpper = 'PROJECT' + '_MANAGER'
foreach ($forbidden in @($retiredRole, $retiredTitle, $retiredUpper,
        'controller <-> research_' + $retiredRole)) {
    if ($skill.Contains($forbidden)) { throw "Retired implementation relay remains: $forbidden" }
}
$resolver = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1') -Raw
foreach ($required in @("ValidateSet('controller', 'experiment_monitor')", 'Unregistered Codex role', 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
if ($resolver.Contains($retiredRole)) { throw 'Route resolver retains the retired implementation relay' }
$currentWork = Get-Content -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if (-not $currentWork.Contains($roles.roles.experiment_monitor.thread_id) -or
    -not $currentWork.Contains('.omp/agents/') -or
    -not $currentWork.Contains('hmasd-pro-monitor') -or
    -not $currentWork.Contains('hmasd-pro-monitor-luna') -or
    -not $currentWork.Contains('CONNECTED_PREFLIGHT_OK')) {
    throw 'Current boundary does not name the unified local, BrowserMCP and Monitor surfaces'
}
if ($currentWork.Contains('019f8a2e-ed73-7a02-9bb9-4a57b2054cf3')) {
    throw 'Current boundary retains the retired implementation-relay task'
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
