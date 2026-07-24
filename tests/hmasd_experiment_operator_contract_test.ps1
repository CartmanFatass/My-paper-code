[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$definitionPath = Join-Path $repo '.claude/agents/hmasd-experiment-operator.md'
$rolePath = Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md'
if (-not (Test-Path -LiteralPath $definitionPath -PathType Leaf)) {
    throw 'The experiment operator has no registered subagent definition'
}
$operatorDef = Get-Content -Raw -LiteralPath $definitionPath
$role = Get-Content -Raw -LiteralPath $rolePath
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')

# The operator is deliberately pinned to the mechanical tier.
foreach ($required in @(
    'name: hmasd-experiment-operator',
    'model: haiku',
    'effort: low')) {
    if (-not $operatorDef.Contains($required)) { throw "Operator definition missing: $required" }
}
# No source-write authority: the tool grant must expose no editing tool.
$toolLine = [regex]::Match($operatorDef, '(?m)^tools:\s*(.+)$')
if (-not $toolLine.Success) { throw 'Operator definition does not declare an explicit tool grant' }
foreach ($forbidden in @('Edit', 'Write', 'MultiEdit', 'NotebookEdit')) {
    if ($toolLine.Groups[1].Value -match "\b$forbidden\b") {
        throw "Operator tool grant exposes a source-write tool: $forbidden"
    }
}
# Git authority is none, enforced rather than merely stated.
if ($operatorDef -notmatch '(?m)^hooks:' -or $operatorDef -notmatch 'PreToolUse') {
    throw 'Operator definition does not enforce its no-Git boundary with a hook'
}

foreach ($required in @(
    'one already-authorized run',
    'fails closed',
    'foreground',
    'run_in_background',
    'Start-Process',
    'repeatedly open its progress file',
    'Send nothing while the run is healthy',
    'No progress, ETA, phase, heartbeat',
    'exactly once',
    'EXPERIMENT_OPERATOR_TERMINAL',
    'terminal=<COMPLETE|ERROR>',
    'never launch a second run',
    'resume a checkpoint',
    'spawn an agent',
    'You never run Git')) {
    if (-not $operatorDef.Contains($required)) { throw "Operator definition missing: $required" }
}

foreach ($required in @(
    'callable_agent_type=hmasd-experiment-operator',
    'definition=.claude/agents/hmasd-experiment-operator.md',
    'model=haiku',
    'effort=low',
    'progress_notifications=forbidden',
    'terminal_notification_count=exactly_one',
    'terminal_values=COMPLETE|ERROR',
    'restart policy, whose default is `forbidden`',
    'train -> evaluate -> analyze',
    'No progress, ETA, phase, heartbeat')) {
    if (-not $role.Contains($required)) { throw "Operator role missing: $required" }
}

foreach ($required in @(
    'project_manager_experiment_orchestration=direct_via_registered_child',
    'experiment_operator_authority=one_exact_authorized_run',
    'There is no dispatch or experiment-monitor Skill')) {
    if (-not $agents.Contains($required)) { throw "AGENTS operator contract missing: $required" }
}

# Runtime detail belongs to CLAUDE.md; the constitution stays runtime-agnostic.
$claude = Get-Content -Raw -LiteralPath (Join-Path $repo 'CLAUDE.md')
foreach ($required in @(
    'subagent_runtime=claude_code',
    'subagent_definitions=.claude/agents/*.md',
    'implementer_tier=sonnet_high',
    'reviewer_tier=opus_high',
    'mechanical_tier=haiku_low',
    'hmasd-experiment-operator')) {
    if (-not $claude.Contains($required)) { throw "CLAUDE runtime contract missing: $required" }
}
foreach ($leaked in @('_tier=', 'subagent_runtime=', '| Subagent | Tier |')) {
    if ($agents.Contains($leaked)) {
        throw "Runtime detail leaked into the constitution: $leaked"
    }
}

foreach ($required in @(
    'hmasd-experiment-operator',
    '`haiku` with `low` effort',
    'returns exactly one `COMPLETE` or',
    'No Controller, persistent Monitor, dispatcher')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK operator state missing: $required" }
}

foreach ($retired in @(
    '.agents/roles/CONTROLLER.md',
    '.agents/roles/EXPERIMENT_MONITOR.md',
    '.agents/skills/hmasd-dispatch-task/SKILL.md',
    '.agents/skills/hmasd-experiment-monitor/SKILL.md',
    '.codex/config.toml',
    '.codex/agents/hmasd-experiment-operator.toml')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Retired execution surface remains: $retired"
    }
}

Write-Output 'HMASD_EXPERIMENT_OPERATOR_CONTRACT_OK'
