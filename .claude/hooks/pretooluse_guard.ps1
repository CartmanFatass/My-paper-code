<#
.SYNOPSIS
    PreToolUse guard. Turns three standing constraints that were enforced only by
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

    RULE 2 -- push before tag
        COMPUTE_ROUTING.md: "Unpushed work is invisible. The runner checks out
        the tagged commit. Push before tagging, always." A tag pushed ahead of
        its commits produces a cloud run at the wrong tree -- hours of compute,
        or worse, a result computed from code that is not the code being claimed.
        The review-round preflight already makes this assertion; the cloud path
        never got it.

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

# --- RULE 1: --no-verify -----------------------------------------------------
if ($command -match 'git\b' -and $command -match '\bcommit\b') {
    if ($command -match '(^|\s)(--no-verify|-n)(\s|$)') {
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

# --- RULE 2: push before tag -------------------------------------------------
$isTagCreate = $command -match 'git\b[^|;&]*\btag\b(?!\s+-[dl])'
$isTagPush = $command -match 'git\b[^|;&]*\bpush\b[^|;&]*(--tags|refs/tags|\btag\b)'
if ($isTagCreate -or $isTagPush) {
    $branch = (& git -C $repo rev-parse --abbrev-ref HEAD 2>$null)
    if ($branch) {
        $branch = $branch.Trim()
        & git -C $repo merge-base --is-ancestor HEAD "origin/$branch" 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $unpushed = (& git -C $repo log --oneline "origin/$branch..HEAD" 2>$null) -join "`n"
            Deny @"
HEAD is not an ancestor of origin/$branch -- there are unpushed commits, and the
cloud runner checks out the TAGGED COMMIT, not your working tree.

Tagging now produces a run at a tree that does not contain this work, which is
either hours of wasted compute or, worse, a result computed from code that is
not the code being claimed.

Unpushed:
$unpushed

Push first, then tag.
"@
        }
    }
}

# --- RULE 3: branch scope ----------------------------------------------------
if ($command -match 'git\b') {
    # 3a. a push whose refspec names a branch other than the protected one
    if ($command -match 'git\b[^|;&]*\bpush\b([^|;&]*)') {
        $tail = $Matches[1]
        $refs = @($tail -split '\s+' | Where-Object {
            $_ -and $_ -notmatch '^-' -and $_ -notmatch '^(origin|upstream)$' -and $_ -notmatch 'refs/tags'
        })
        foreach ($ref in $refs) {
            $name = ($ref -replace '^.*:', '')      # local:remote refspec
            if ($name -and $name -ne $ProtectedBranch -and $name -notmatch '^(HEAD|--.*)$' -and $name -notmatch '^v?\d') {
                Deny "push names '$name', but branch_scope is '$ProtectedBranch' only (user ruling 2026-07-27). Another line owns other branches and this session never pushes them."
            }
        }
    }
    # 3b. branch deletion, anywhere
    if ($command -match 'git\b[^|;&]*\bbranch\b[^|;&]*\s-(D|d)\b') {
        Deny 'branch deletion is outside this session. Branches other than the protected one belong to another line.'
    }
    # 3c. switching to an EXISTING local branch that is not the protected one.
    #     Resolved against the real branch list so `git checkout -- <path>` and
    #     `git checkout <commit>` stay untouched -- both are used constantly for
    #     restores, and blocking them would make this guard the obstacle.
    if ($command -match 'git\b[^|;&]*\b(checkout|switch)\b([^|;&]*)') {
        $args = @($Matches[2] -split '\s+' | Where-Object { $_ -and $_ -notmatch '^-' })
        if ($args.Count -gt 0) {
            $branches = @(& git -C $repo for-each-ref --format='%(refname:short)' refs/heads 2>$null)
            foreach ($a in $args) {
                if ($branches -contains $a -and $a -ne $ProtectedBranch) {
                    Deny "'$a' is another branch. branch_scope is '$ProtectedBranch' only; this session never checks out another line's work."
                }
            }
        }
    }
}

exit 0
