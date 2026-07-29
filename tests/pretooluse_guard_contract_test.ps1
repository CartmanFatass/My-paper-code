<#
.SYNOPSIS
    Contract test for .claude/hooks/pretooluse_guard.ps1.

.DESCRIPTION
    The guard existed for a day enforcing nothing: it was registered with
    %CLAUDE_PROJECT_DIR%, which is cmd.exe syntax, so `powershell -File` got a
    literal path, found no script, and errored on every shell call. Nothing
    judged a single command. Then the first commit it ever judged was its own
    repair, BLOCKED because the commit message contained the word it forbids.

    Both defects are covered below, and neither was reachable by reading the
    script -- one lived in the registration, the other only appears when the
    command carries prose. Every case here is paired: for each rule, one command
    that MUST be denied and one adjacent command that MUST be allowed. A guard
    with only red cases cannot show it has stopped over-blocking, and a guard
    with only green cases cannot show it still blocks.

    Exit 0 = contract holds. Exit 1 = a case went the wrong way.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$guard = Join-Path $repo '.claude/hooks/pretooluse_guard.ps1'
$settings = Join-Path $repo '.claude/settings.json'

$failures = @()

# --- The registration, not just the script -----------------------------------
# The script passed every case below on 2026-07-28 while enforcing nothing,
# because the path in settings.json did not resolve. A test that only calls the
# script by hand would have stayed green through the entire outage.
if (-not (Test-Path -LiteralPath $guard -PathType Leaf)) {
    Write-Output "MISSING  $guard"
    exit 1
}
if (-not (Test-Path -LiteralPath $settings -PathType Leaf)) {
    $failures += 'settings.json absent: the guard is registered nowhere and binds nothing'
}
else {
    $raw = Get-Content -LiteralPath $settings -Raw
    if ($raw -match '%CLAUDE_PROJECT_DIR%') {
        $failures += 'settings.json uses %CLAUDE_PROJECT_DIR% (cmd.exe syntax). Claude Code substitutes $CLAUDE_PROJECT_DIR; the literal string reaches powershell -File and the hook errors on EVERY call'
    }
    $registered = $false
    try {
        $parsed = $raw | ConvertFrom-Json -ErrorAction Stop
        foreach ($entry in @($parsed.hooks.PreToolUse)) {
            foreach ($hook in @($entry.hooks)) {
                if ($hook.command -match 'pretooluse_guard\.ps1') { $registered = $true }
            }
        }
    }
    catch {
        $failures += "settings.json does not parse as JSON: $($_.Exception.Message)"
    }
    if (-not $registered) {
        $failures += 'pretooluse_guard.ps1 is not registered under hooks.PreToolUse'
    }
}

# --- Paired cases ------------------------------------------------------------
# Driven through the REAL entry point: Claude Code hands the hook a JSON payload
# on stdin. The -TestCommand parameter is a double, and it lies -- `powershell
# -File` splits an argument at its embedded quotes, so
# `git commit -m "subject" --no-verify` arrived as TestCommand='git commit -m'
# plus ProtectedBranch='subject --no-verify' and was correctly allowed, for a
# reason that has nothing to do with the rule under test. Every case below goes
# through stdin, so what is judged is what the hook will really be handed.
function Invoke-Guard([string]$Command) {
    $payload = @{ tool_input = @{ command = $Command } } | ConvertTo-Json -Depth 4 -Compress
    $payload | & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $guard 2>&1 | Out-Null
    return $LASTEXITCODE
}

# The harness must be able to reach a denial at all. If stdin were not wired up
# the guard would exit 0 on everything and every ALLOW case below would pass
# while proving nothing.
if ((Invoke-Guard 'git commit --no-verify -m x') -ne 2) {
    Write-Output 'PRETOOLUSE_GUARD_CONTRACT_FAILED'
    Write-Output '  harness: stdin payload never reached the guard -- no ALLOW case below is meaningful'
    exit 1
}

$heredocCommit = @"
git commit -m "`$(cat <<'EOF'
Repair the guard.

Explains that --no-verify is a user-directed override and must not be used to
unblock yourself. This body is PROSE. It is not a flag.
EOF
)"
"@

$cases = @(
    # rule 1 -- the bypass flag, and the same words as message text
    @{ Deny = $true;  Why = 'rule 1: the bypass flag itself';
       Cmd = 'git commit --no-verify -m x' },
    @{ Deny = $true;  Why = 'rule 1: the flag AFTER a quoted message';
       Cmd = 'git commit -m "ordinary subject" --no-verify' },
    @{ Deny = $true;  Why = 'rule 1: the short spelling';
       Cmd = "git commit -m 'ordinary subject' -n" },
    @{ Deny = $false; Why = 'rule 1 paired negative: the flag NAMED inside a quoted message';
       Cmd = 'git commit -m "explain why --no-verify is the wrong repair"' },
    @{ Deny = $false; Why = 'rule 1 paired negative: the flag named inside a heredoc body';
       Cmd = $heredocCommit },
    @{ Deny = $false; Why = 'rule 1 paired negative: message supplied by file';
       Cmd = 'git commit -F msg.txt' },

    # rule 2 -- tagging, and the word "tag" as message text
    @{ Deny = $false; Why = 'rule 2 paired negative: "tag" appearing in a commit message';
       Cmd = 'git commit -m "always tag the stage commit"' },

    # A commit message is prose. None of these verbs may summon a rule; every
    # one of them appears in this repository's real commit messages, and the
    # first draft of the sanitization denied all three.
    @{ Deny = $false; Why = 'prose: "push" in a commit message must not read as a push';
       Cmd = 'git commit -m "push before tag, always"' },
    @{ Deny = $false; Why = 'prose: "checkout" and a branch name in a commit message';
       Cmd = 'git commit -m "the runner does a checkout of new-test, not of untied-k"' },
    @{ Deny = $false; Why = 'prose: a foreign branch named in a commit message';
       Cmd = 'git commit -m "these files came from the aggressive line"' },

    # rule 3 -- branch scope. Reads the RAW command on purpose; a quoted branch
    # name must still be caught, because a false allow here is the one failure
    # the user ruling exists to prevent.
    @{ Deny = $true;  Why = 'rule 3a: push naming another line''s branch';
       Cmd = 'git push origin aggressive' },
    @{ Deny = $true;  Why = 'rule 3a: the same branch name, quoted';
       Cmd = 'git push origin "aggressive"' },
    @{ Deny = $false; Why = 'rule 3a paired negative: push of the protected branch';
       Cmd = 'git push origin untied-k' },
    @{ Deny = $true;  Why = 'rule 3b: branch deletion';
       Cmd = 'git branch -D aggressive' },
    @{ Deny = $true;  Why = 'rule 3c: checkout of an existing foreign branch';
       Cmd = 'git checkout new-test' },
    @{ Deny = $false; Why = 'rule 3c paired negative: path restore, not a branch switch';
       Cmd = 'git checkout -- envs/pettingzoo/scenario_base.py' },
    @{ Deny = $false; Why = 'rule 3c paired negative: checkout of the protected branch';
       Cmd = 'git checkout untied-k' },

    # the guard must stay out of the way of everything else
    @{ Deny = $false; Why = 'ordinary git read';
       Cmd = 'git status --short' },
    @{ Deny = $false; Why = 'ordinary non-git command';
       Cmd = 'ls -la docs/project' }
)

foreach ($case in $cases) {
    $code = Invoke-Guard $case.Cmd
    $denied = ($code -eq 2)
    if ($denied -ne $case.Deny) {
        $expected = if ($case.Deny) { 'DENY (2)' } else { 'ALLOW (0)' }
        $oneline = ($case.Cmd -replace '\r?\n', ' | ')
        $failures += "$($case.Why): expected $expected, got exit $code -- $oneline"
    }
}

# --- The rule-2 push-before-tag branch, exercised against real repo state -----
# State-dependent by nature, so assert the DIRECTION rather than a fixed verdict:
# with unpushed commits present, creating a tag must be denied; the assertion is
# skipped, loudly, when the working branch is already pushed.
$branch = (& git -C $repo rev-parse --abbrev-ref HEAD 2>$null)
if ($branch) {
    $branch = $branch.Trim()
    & git -C $repo merge-base --is-ancestor HEAD "origin/$branch" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $code = Invoke-Guard 'git tag d7s-probe'
        if ($code -ne 2) {
            $failures += "rule 2: HEAD is ahead of origin/$branch, so tag creation must be denied, got exit $code"
        }
    }
    else {
        Write-Output "SKIP     rule 2 live branch: HEAD is already an ancestor of origin/$branch, nothing unpushed to catch"
    }
}

if ($failures.Count -gt 0) {
    Write-Output 'PRETOOLUSE_GUARD_CONTRACT_FAILED'
    $failures | ForEach-Object { Write-Output "  $_" }
    exit 1
}
Write-Output 'PRETOOLUSE_GUARD_CONTRACT_OK'
exit 0
