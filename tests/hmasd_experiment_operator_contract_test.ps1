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
# Asserting the hook TEXT exists is a guard on a guard: it stayed green while the
# hook itself failed open, because the hook piped through jq and jq is not
# installed here -- an empty command matched nothing and it exited 0 = allow.
# Extract the real hook body and execute it, so the check fails when the hook does.
$shell = (Get-Command bash -ErrorAction SilentlyContinue).Source
if (-not $shell) {
    $gitExe = (Get-Command git -ErrorAction SilentlyContinue).Source
    if ($gitExe) { $shell = Join-Path (Split-Path (Split-Path $gitExe)) 'bin\bash.exe' }
}
# No skip-if-absent: an unrunnable guard check is a failed guard check, which is
# how the previous text-only assertion stayed green over an inert hook.
if (-not $shell -or -not (Test-Path $shell)) {
    throw 'No POSIX shell available to execute the child git hooks; the no-Git boundary cannot be proven'
}
foreach ($definition in @('hmasd-experiment-operator', 'hmasd-implementer')) {
    $text = Get-Content -Raw -LiteralPath (Join-Path $repo ".claude/agents/$definition.md")
    $matcherMatch = [regex]::Match($text, '(?m)^\s*- matcher:\s*"([^"]*)"')
    if (-not $matcherMatch.Success) { throw "$definition hook has no matcher" }
    # Capture before comparing -- a further -match would clobber $Matches.
    $matcher = $matcherMatch.Groups[1].Value
    if ($matcher -notmatch 'Bash' -or $matcher -notmatch 'PowerShell') {
        throw "$definition hook matcher misses a shell tool: $matcher"
    }
    $body = [regex]::Match($text, '(?ms)^          command: \|-\r?\n(.*?)(?=\r?\n---|\r?\n\w)').Groups[1].Value
    if (-not $body.Trim()) { throw "$definition hook body not found" }
    $script = Join-Path ([IO.Path]::GetTempPath()) "hookcheck_$definition.sh"
    [IO.File]::WriteAllText($script, ($body -replace '^\s{12}', '' -replace "(?m)^\s{12}", '') + "`nexit 0`n")
    foreach ($case in @(
        @{ cmd = 'git commit -m wip';    expect = 2 },
        @{ cmd = 'git -C /repo push';    expect = 2 },
        @{ cmd = 'ls && git add -A';     expect = 2 },
        @{ cmd = 'git status --short';   expect = 0 })) {
        $json = '{"tool_input":{"command":"' + $case.cmd + '"}}'
        # A blocking hook writes its reason to stderr, and PowerShell 5.1 wraps a
        # native command's stderr in an ErrorRecord that trips ErrorActionPreference
        # 'Stop'. The exit code is the contract here, so judge on that alone.
        $previous = $ErrorActionPreference
        $ErrorActionPreference = 'SilentlyContinue'
        $json | & $shell $script 2>&1 | Out-Null
        $ErrorActionPreference = $previous
        if ($LASTEXITCODE -ne $case.expect) {
            throw "$definition hook returned $LASTEXITCODE for '$($case.cmd)', expected $($case.expect)"
        }
    }
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
