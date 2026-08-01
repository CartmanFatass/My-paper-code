[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$registry = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') | ConvertFrom-Json
if ($registry.schema_version -ne 31 -or
    $registry.direct_transport_contract.conversation_binding -ne 'one_dedicated_conversation_per_branch_per_reviewer_role' -or
    $registry.round_operator.kind -ne 'project_manager_direct_transport' -or
    $registry.round_operator.decision_intake -ne 'project_manager_direct' -or
    $registry.round_operator.git_boundary_owner -ne 'project_manager' -or
    $registry.direct_transport_contract.transport_owner -ne 'active_project_manager' -or
    $registry.direct_transport_contract.heartbeat_owner -ne 'active_project_manager' -or
    $registry.direct_transport_contract.browser_skill -ne 'claude-in-chrome' -or
    $registry.direct_transport_contract.transport_agent -ne 'project_manager_direct' -or
    $registry.reviewers.open_divergent.transport -ne 'claude_in_chrome') {
    throw 'Project-Manager-direct review registry mismatch'
}
# A reviewer must fail closed until the Project Manager registers its exact
# conversation. A retired registration is never a fallback. This loops over every
# reviewer rather than checking open_divergent alone -- when a second reviewer was
# registered on 2026-07-25 its registration integrity was entirely unguarded,
# because the original check named one key.
$reviewerNames = @($registry.reviewers.PSObject.Properties.Name)
if ($reviewerNames.Count -lt 1) { throw 'Registry declares no reviewers' }
$conversationIds = @()
foreach ($name in $reviewerNames) {
    $reviewer = $registry.reviewers.$name
    if ($reviewer.registration_status -eq 'registered') {
        if ([string]::IsNullOrWhiteSpace($reviewer.conversation_id) -or
            [string]::IsNullOrWhiteSpace($reviewer.url)) {
            throw "Registered reviewer '$name' must carry an exact conversation_id and url"
        }
        if ($reviewer.url -notlike "*$($reviewer.conversation_id)*") {
            throw "Reviewer '$name' has a url that does not contain its conversation_id"
        }
        $conversationIds += $reviewer.conversation_id
    } elseif ($null -ne $reviewer.conversation_id -or $null -ne $reviewer.url) {
        throw "Unregistered reviewer '$name' must not carry a conversation_id or url"
    }
    if ([string]::IsNullOrWhiteSpace($reviewer.role)) {
        throw "Reviewer '$name' must declare a role; role targeting is explicit, never inferred"
    }
}
# Two reviewer roles may share a branch, but never a conversation -- that would
# silently merge a blinded reviewer's context with an unblinded one.
$duplicateConversations = @($conversationIds | Group-Object | Where-Object { $_.Count -gt 1 })
if ($duplicateConversations.Count -gt 0) {
    throw "Two reviewers share conversation_id $($duplicateConversations[0].Name); roles must not share a conversation"
}
# Any reviewer that declares blinding must say what it may never receive, or the
# blinding is an assertion with nothing behind it.
foreach ($name in $reviewerNames) {
    $blinding = $registry.reviewers.$name.blinding
    if ($null -ne $blinding -and $blinding.required -eq $true) {
        if (-not $blinding.must_never_receive -or @($blinding.must_never_receive).Count -lt 1) {
            throw "Blinded reviewer '$name' declares no must_never_receive list"
        }
        if ([string]::IsNullOrWhiteSpace($blinding.reason)) {
            throw "Blinded reviewer '$name' declares no reason for blinding"
        }
    }
}
if (-not $registry.registration_rule) { throw 'Registry is missing its registration rule' }
if (-not $registry.role_targeting_rule) { throw 'Registry is missing its role targeting rule' }
# Every reviewer must say which branch it serves, and none may resurrect a
# retired conversation. Both checks now cover all reviewers; they previously
# named open_divergent alone.
foreach ($name in $reviewerNames) {
    $reviewer = $registry.reviewers.$name
    if ([string]::IsNullOrWhiteSpace($reviewer.branch)) {
        throw "Reviewer '$name' does not declare the branch its conversation is bound to"
    }
    foreach ($retired in @($registry.retired_registrations)) {
        if ($retired.conversation_id -and $retired.conversation_id -eq $reviewer.conversation_id) {
            throw "Reviewer '$name' reuses a retired conversation: $($retired.conversation_id)"
        }
    }
}

$skillPath = Join-Path $repo '.claude/skills/hmasd-review-round/SKILL.md'
$skill = Get-Content -Raw -LiteralPath $skillPath
foreach ($required in @(
    'Project-Manager-direct transport',
    'active Project Manager',
    'claude-in-chrome',
    'mcp__claude-in-chrome__',
    'file_upload',
    'project_manager_direct',
    'registration_status',
    'VERIFY_FRESHNESS_FENCE',
    'An accepted matching fence is never resubmitted',
    'materialize them from `stage_commit`',
    'not from the current working tree',
    'exact raw -> provenance intake -> heartbeat deletion -> Project Manager reconciliation')) {
    if (-not $skill.Contains($required)) { throw "Review Skill missing: $required" }
}
if ($skill -match '(?i)\bcontroller\b|hmasd-dispatch-task|hmasd-experiment-monitor') {
    throw 'Review Skill retains a retired relay or monitor surface'
}
if ($skill -match 'browser:control-in-app-browser') {
    throw 'Review Skill retains the retired Codex browser surface'
}
if ($skill -match '\.agents/skills/') {
    throw 'Review Skill retains a pre-migration .agents/skills path'
}
# Conversations are bound per branch, so the fence carries a parameter.
if ($skill -match '(?m)^branch=(?!<)') {
    throw 'Review Skill hard-codes a branch in the freshness fence'
}

$heartbeatPath = Join-Path $repo '.claude/skills/hmasd-review-round/scripts/render_review_heartbeat.ps1'
$roundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned'
$prompt = & $heartbeatPath `
    -RoundPath $roundRoot `
    -Stage 'OPEN_DIVERGENT' `
    -StageCommit '50f95da37496b092128c2136d50503ac3e18a5c1' `
    -QuestionPath '20_PRO_OPEN_QUESTION.md' `
    -RawPath '21_PRO_OPEN_RAW.md' `
    -HeartbeatId 'contract-test-heartbeat'
foreach ($required in @(
    'PROJECT-MANAGER-DIRECT',
    'active Project Manager',
    'Never submit or resubmit',
    'contract-test-heartbeat',
    'delete',
    'heartbeat and confirm absence')) {
    if (-not $prompt.Contains($required)) { throw "Rendered heartbeat missing: $required" }
}
if ($prompt -match '(?i)\bcontroller\b|hmasd-dispatch-task') {
    throw 'Rendered heartbeat retains a retired Controller route'
}
# The exchanger was retired 2026-07-25, yet its dispatch instruction survived in
# this rendered prompt until 2026-07-31 -- unseen because nothing scanned the
# runtime output of a .ps1 (check G covers only .md). Assert on the OUTPUT.
if ($prompt -match '(?i)exchanger') {
    throw 'Rendered heartbeat retains the retired exchanger role'
}

$preflight = Join-Path $repo '.claude/skills/hmasd-review-round/scripts/preflight_review_round.ps1'
if (-not (Test-Path $preflight)) { throw 'Round preflight gate is missing' }

# The superseded verifier accepted any backticked path anywhere in a question and
# so passed rounds the archive builder refused. It must not come back.
if (Test-Path (Join-Path $repo '.claude/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1')) {
    throw 'Superseded verify_pro_review_boundary.ps1 is present; preflight_review_round.ps1 is the single gate'
}

# The gate previously defaulted -Remote to the GitHub slug rather than a git
# remote name and crashed on every production call, while this test passed
# because it supplied its own remote. Assert the default is real.
$preflightText = Get-Content -Raw $preflight
$defaultRemote = [regex]::Match($preflightText, '\[string\]\$Remote\s*=\s*''(?<r>[^'']+)''')
if (-not $defaultRemote.Success) { throw 'Round preflight has no default -Remote to validate' }
$configuredRemotes = @(& git.exe -C $repo remote)
if ($configuredRemotes -notcontains $defaultRemote.Groups['r'].Value) {
    throw "Round preflight default -Remote '$($defaultRemote.Groups['r'].Value)' is not a configured git remote"
}

# A gate that cannot fail is decoration. The fixture is a dedicated round
# directory whose name says what it is; it carries no '## Evidence to read'
# allow-list and must be rejected. It replaced a real retired round that this
# test had pinned alive against the policy of deleting superseded rounds.
$fixture = 'docs/external-review/rounds/00000000_preflight_reject_fixture'
# Do NOT wrap this in a Test-Path guard. A skip-if-absent probe would silently
# vacate itself and leave the suite green over an unexercised gate -- the
# exact defect this probe exists to prevent.
if (-not (Test-Path (Join-Path $repo "$fixture/20_PRO_OPEN_QUESTION.md"))) {
    throw "Preflight rejection fixture is missing: $fixture. Restore it rather than deleting the check."
}
# Probe with the remote branch tip, not local HEAD: preflight's reachability
# gate is production behaviour at send time, but probing it with HEAD forced a
# push after every local commit before the next commit's hook could pass --
# hit twice on 2026-08-01, and a second recurrence is the charter's threshold
# for fixing the mechanism.
$branch = (& git.exe -C $repo rev-parse --abbrev-ref HEAD).Trim()
$probeCommit = (& git.exe -C $repo rev-parse --verify --quiet "origin/$branch")
if (-not $probeCommit) { $probeCommit = (& git.exe -C $repo rev-parse HEAD) }
$rejected = & $preflight `
    -Commit $probeCommit.Trim() `
    -RoundPath $fixture `
    -Branch $branch `
    -RepoRoot $repo 2>$null | ConvertFrom-Json
if ($rejected.status -ne 'ROUND_PREFLIGHT_FAILED') {
    throw 'Round preflight accepted a question with no evidence allow-list'
}
# Assert on this guard's OWN wording, not on `status`. The fixture is illegal in
# two independent ways -- no allow-list and no fence artifact -- so a status-only
# check stays green even with the entire allow-list contract deleted from the
# preflight. One fixture violating two guards tests neither.
if (-not ($rejected.failures -match 'no "## Evidence to read" allow-list')) {
    throw "Round preflight rejected the fixture, but not for the missing evidence allow-list -- this probe was masked by a sibling guard. Failures: $($rejected.failures -join ' | ')"
}

# --- the transport-fault channel must actually carry something --------------
#
# Added 2026-07-30 after an audit found that `## Transport faults` was a TODO
# nobody checked: no test and no preflight script mentioned it, so a transport
# defect observed during a round had somewhere to be written and no reason to be.
# That is the "duty without an affordance" failure CLAUDE.md names -- it does not
# produce a refusal, it produces an invention.
#
# SCOPE, deliberately narrow. Most historical intake records predate the scaffold
# section entirely and are exempt: history is evidence, not a repair target. The
# rule binds the shape the scaffold now emits, so every round created from here on
# is covered automatically.
$roundsRoot = Join-Path $repo 'docs/external-review/rounds'
$faultsFilled = 0
foreach ($dir in (Get-ChildItem -LiteralPath $roundsRoot -Directory)) {
    $intakePath = Join-Path $dir.FullName '50_MECHANICAL_INTAKE_RECORD.md'
    if (-not (Test-Path -LiteralPath $intakePath)) { continue }
    $intake = Get-Content -Raw -LiteralPath $intakePath
    $m = [regex]::Match($intake, '(?s)##\s+Transport faults\s*(?<body>.*)$')
    if (-not $m.Success) { continue }          # pre-scaffold record, exempt
    $body = $m.Groups['body'].Value.Trim()
    # Between scaffold and capture the faults are genuinely unknowable, and the
    # first shape of this rule blocked every guarded commit in that window --
    # pressuring an invented `none` before transport ran. PENDING is the honest
    # in-flight state, tolerated exactly until the response capture exists.
    $rawPresent = Test-Path -LiteralPath (Join-Path $dir.FullName '21_PRO_OPEN_RAW.md')
    if ($body -match '^PENDING') {
        if ($rawPresent) {
            throw "Round '$($dir.Name)' has its response captured (21_PRO_OPEN_RAW.md exists) but '## Transport faults' still says PENDING. Transport has run; record what it did -- observed faults, or ``none``."
        }
        continue
    }
    if ($body.Length -eq 0 -or $body -match '^TODO') {
        throw "Round '$($dir.Name)' carries a '## Transport faults' section that is empty or still TODO. A round that observed no fault must say ``none`` -- silence is indistinguishable from a fault nobody wrote down, which is the whole reason this channel exists."
    }
    $faultsFilled++
}
# Do NOT let this vacate itself. If every round lost the heading the loop above
# would pass over an empty set and stay green -- the same shape as the retired
# fixture guard higher in this file, and the same reason it is written this way.
if ($faultsFilled -lt 1) {
    throw 'No round carries a filled "## Transport faults" section, so the check above ran over nothing. Point it at a round that does, rather than leaving a guard that cannot fail.'
}
$scaffoldPath = Join-Path $repo '.claude/skills/hmasd-review-round/scripts/new_review_round.ps1'
if (-not (Test-Path -LiteralPath $scaffoldPath)) { throw 'Round scaffolder is missing' }
$scaffold = Get-Content -Raw -LiteralPath $scaffoldPath
if (-not $scaffold.Contains('## Transport faults')) {
    throw 'new_review_round.ps1 no longer emits a "## Transport faults" section; future rounds would silently escape the check above'
}
# The scaffold must emit the tolerated in-flight marker, not TODO -- a TODO
# scaffold re-arms the trap where every guarded commit before capture is blocked.
if ($scaffold -match '(?s)## Transport faults.{0,40}TODO' -or $scaffold -notmatch '(?s)## Transport faults.{0,10}PENDING') {
    throw 'new_review_round.ps1 must scaffold "## Transport faults" as PENDING (in-flight marker), not TODO'
}

Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
# The deliberate rejection probe above exits 1 by design; do not inherit it.
exit 0
