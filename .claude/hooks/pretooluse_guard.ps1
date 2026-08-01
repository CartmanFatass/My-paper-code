<#
.SYNOPSIS
    PreToolUse guard. Turns standing constraints that were enforced only by
    a sentence into things the shell cannot do.

.DESCRIPTION
    Registered once in .claude/settings.json against Bash|PowerShell. All logic
    lives here, so new checks are added by editing this file and never by editing
    the hook registration again.

    Exit 2 blocks the call and returns the stderr text to the agent. Exit 0
    allows it.

    RULE 1 -- --no-verify
        AGENTS.md: the drift guard's bypass "is for a user-directed override, not
        for unblocking yourself; a bypassed guard reads as covered forever after."
        That sentence protected all four contract tests and the control-plane
        checker, in a file only the orchestrator reads, against a command
        settings.local.json pre-approves without a prompt (`Bash(git commit *)`
        matches `git commit --no-verify`). Highest leverage rule here: bypass it
        and every other mechanical guard in the repository is off.

    RULE 2 (push before tag) was retired with the cloud vehicle on 2026-08-01:
    no runner checks out tags any more, so the rule guarded nothing.

    RULE 3 -- branch scope
        CURRENT_WORK.md: `branch_scope=untied-k only, never touch another branch`
        and `aggressive_branch=another line's, never push`. A user ruling,
        enforced by nothing.

        Deliberately narrow. It blocks a push whose refspec names another branch,
        a branch deletion, and a checkout/switch to an EXISTING local branch that
        is not untied-k -- resolved against the real branch list, so
        `git checkout -- <path>` and `git checkout <commit>` are untouched. Those
        are used constantly for restores; blocking them would make the guard the
        obstacle rather than the seatbelt.

    A malformed payload ALLOWS. A parse failure is a harness fault, not a policy
    violation, and a guard that bricks every shell command on one is worse than
    the risk it covers. Every rule here fails closed only on the thing it names.
#>
[CmdletBinding()]
param(
    # For testing: bypass stdin and judge this command directly.
    [string]$TestCommand,
    [string]$ProtectedBranch = 'untied-k'
)

$ErrorActionPreference = 'Continue'

function Deny([string]$message) {
    [Console]::Error.WriteLine("BLOCKED: $message")
    exit 2
}

$command = $TestCommand
if (-not $command) {
    try {
        $raw = [Console]::In.ReadToEnd()
        if (-not $raw) { exit 0 }
        $payload = $raw | ConvertFrom-Json -ErrorAction Stop
        $command = $payload.tool_input.command
    }
    catch { exit 0 }   # unparseable payload: allow, see header
}
if (-not $command) { exit 0 }

$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# --- A flag inside a quoted message is prose, not a flag ---------------------
# The first commit this guard ever judged was BLOCKED by its own commit message,
# which described the bypass it forbids. Rules 1 and 1b match FLAGS and
# SUBCOMMANDS, so a heredoc body or a quoted -m argument is noise to them.
# Blocking that teaches the next reader to route around the guard, which costs
# more than the bypass it covers.
#
# Rule 3 deliberately keeps reading the RAW command. It matches branch NAMES,
# and stripping a quoted `"aggressive"` would open the one hole the user ruling
# exists to close. There, a false block is recoverable and a false allow is not.
$scan = [regex]::Replace($command, "(?s)<<-?\s*['`"]?(\w+)['`"]?.*?\r?\n\s*\1", ' ')
$scan = [regex]::Replace($scan, "`"[^`"]*`"|'[^']*'", ' ')

# --- RULE 1: --no-verify -----------------------------------------------------
if ($scan -match 'git\b' -and $scan -match '\bcommit\b') {
    if ($scan -match '(^|\s)(--no-verify|-n)(\s|$)') {
        Deny @"
--no-verify is a user-directed override, not a way to unblock yourself.

The workflow drift guard is the only thing running the four contract tests and
the control-plane checker on a commit that touches a guarded path. Bypassing it
does not make the commit safe; it makes every later reader believe those checks
passed. Repair the cause, not the assertion.

If the user has directed this override, say so and ask them to run it.
"@
    }
}

# --- RULE 1b: core.hooksPath is --no-verify with a different spelling --------
# Measured 2026-07-31: `git -c core.hooksPath=nul commit` reached exit 0 while
# --no-verify was blocked, and `Bash(git commit *)` is pre-approved without a
# prompt. Redirecting or unsetting the hooks path turns off the same drift guard
# RULE 1 exists to protect, for every subsequent command if set persistently.
# Matched in $scan like the flag itself, so quoted prose naming it stays allowed.
# This also denies reads (`git config --get core.hooksPath`); that false block
# is recoverable -- read .git/config directly, or ask the user.
if ($scan -match 'git\b' -and $scan -match 'core\.hooksPath') {
    Deny @"
core.hooksPath reaches the same leverage as --no-verify: repoint or clear it and
the workflow drift guard stops running, silently, for every commit after.

If you meant to READ the current value, inspect .git/config with a file tool
instead. If the user has directed a hooks-path change, say so and ask them to
run it.
"@
}

# --- RULE 3: branch scope ----------------------------------------------------
# Two strings, on purpose. The VERB is detected in $scan, so prose cannot summon
# the rule: `git commit -m "push before tag, always"` is a commit, and reading
# `push` out of its message denied it outright -- a guard that blocks ordinary
# commits gets routed around, and then it guards nothing. The ARGUMENTS are read
# from the raw $command and unquoted per token, so `git push origin "aggressive"`
# is still caught. Prose cannot invent a push; quoting cannot hide a branch.
function Get-RefTokens([string]$tail) {
    return @($tail -split '\s+' | ForEach-Object { $_.Trim('"', "'") } | Where-Object { $_ })
}

# The git SUBCOMMAND, not any occurrence of a word. `git stash push -- <path>`
# is a stash, and reading its pathspec as a refspec denied it as a branch push.
# Anything before the subcommand is an option or `-C <path>`.
$subcommand = ''
if ($scan -match 'git\b((?:\s+-\S+|\s+-C\s+\S+)*)\s+([a-z][a-z-]*)') {
    $subcommand = $Matches[2]
}

if ($scan -match 'git\b') {
    # 3a. a push whose refspec names a branch other than the protected one
    if ($subcommand -eq 'push' -and
        $command -match 'git\b[^|;&]*\bpush\b([^|;&]*)') {
        $refs = @(Get-RefTokens $Matches[1] | Where-Object {
            $_ -notmatch '^-' -and $_ -notmatch '^(origin|upstream)$' -and $_ -notmatch 'refs/tags'
        })
        foreach ($ref in $refs) {
            $name = ($ref -replace '^.*:', '')      # local:remote refspec
            if ($name -and $name -ne $ProtectedBranch -and $name -notmatch '^(HEAD|--.*)$' -and $name -notmatch '^v?\d') {
                Deny "push names '$name', but branch_scope is '$ProtectedBranch' only (user ruling 2026-07-27). Another line owns other branches and this session never pushes them."
            }
        }
    }
    # 3b. branch deletion, anywhere
    if ($scan -match 'git\b[^|;&]*\bbranch\b[^|;&]*\s-(D|d)\b') {
        Deny 'branch deletion is outside this session. Branches other than the protected one belong to another line.'
    }
    # 3c. switching to an EXISTING local branch that is not the protected one.
    #     Resolved against the real branch list so `git checkout -- <path>` and
    #     `git checkout <commit>` stay untouched -- both are used constantly for
    #     restores, and blocking them would make this guard the obstacle.
    if ($scan -match 'git\b[^|;&]*\b(checkout|switch)\b' -and
        $command -match 'git\b[^|;&]*\b(checkout|switch)\b([^|;&]*)') {
        $targets = @(Get-RefTokens $Matches[2] | Where-Object { $_ -notmatch '^-' })
        if ($targets.Count -gt 0) {
            $branches = @(& git -C $repo for-each-ref --format='%(refname:short)' refs/heads 2>$null)
            foreach ($target in $targets) {
                if ($branches -contains $target -and $target -ne $ProtectedBranch) {
                    Deny "'$target' is another branch. branch_scope is '$ProtectedBranch' only; this session never checks out another line's work."
                }
            }
        }
    }
}

exit 0
