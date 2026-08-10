[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Read-RepoFile([string] $relativePath) {
    $path = Join-Path $repo $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required native-default contract surface is missing: $relativePath"
    }
    Get-Content -Raw -LiteralPath $path
}

function Normalize([string] $content) {
    ($content -replace '\s+', ' ').Trim().ToLowerInvariant()
}

function Require-Term([string] $content, [string] $term, [string] $surface) {
    $normalizedContent = Normalize $content
    $normalizedTerm = Normalize $term
    if (-not $normalizedContent.Contains($normalizedTerm)) {
        throw "Native-default contract missing on $surface`: $term"
    }
}

# This is deliberately a static source contract. It verifies caller wording and
# boundaries; it does not invoke or claim that a future native child was spawned.
$sources = [ordered]@{
    router = Read-RepoFile 'AGENTS.md'
    wdm = Read-RepoFile '.agents/roles/WORKFLOW_DESIGN_MANAGER.md'
    cpm = Read-RepoFile '.agents/roles/CODE_PROJECT_MANAGER.md'
    explorer = Read-RepoFile '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md'
    assignmentSkill = Read-RepoFile '.agents/skills/hmasd-writing-agent-assignments/SKILL.md'
}

$normalizedSources = [ordered]@{}
foreach ($entry in $sources.GetEnumerator()) {
    $normalizedSources[$entry.Key] = Normalize $entry.Value
}

# Every caller uses the same literal action anchors, with fork_turns remaining a
# one-turn background action rather than a profile/TOML setting.
$callerAnchors = @(
    'agent_type="default"'
    'model="gpt-5.6-luna"'
    'reasoning_effort="high"'
    'fork_turns="1"'
)
foreach ($entry in $normalizedSources.GetEnumerator()) {
    foreach ($anchor in $callerAnchors) {
        Require-Term $entry.Value $anchor $entry.Key
    }
}
Require-Term $normalizedSources.router 'caller action must use exactly' 'AGENTS.md'
foreach ($surface in @('wdm', 'cpm', 'explorer')) {
    Require-Term $normalizedSources[$surface] 'caller action is exactly' $surface
}
Require-Term $normalizedSources.assignmentSkill 'literal caller-action anchors' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.router 'single forked turn is background only' 'AGENTS.md'
Require-Term $normalizedSources.router 'is not a TOML/profile enforcement field' 'AGENTS.md'
foreach ($surface in @('wdm', 'cpm', 'explorer')) {
    Require-Term $normalizedSources[$surface] 'one forked turn is background only and is not a profile/TOML field' $surface
}
Require-Term $normalizedSources.assignmentSkill 'one forked turn is background only, not a profile/TOML field' 'hmasd-writing-agent-assignments'

# Specialist leaves are always selected first; the default child is only one
# narrow fallback for an exact bounded task and never displaces a specialist.
Require-Term $normalizedSources.router 'listed specialist leaves remain the first-choice and authoritative route' 'AGENTS.md'
Require-Term $normalizedSources.router 'only when no listed specialist leaf can perform the bounded task' 'AGENTS.md'
Require-Term $normalizedSources.router 'native child remains an L2' 'AGENTS.md'
Require-Term $normalizedSources.router 'never displaces a matching professional leaf' 'AGENTS.md'
foreach ($surface in @('wdm', 'cpm', 'explorer')) {
    Require-Term $normalizedSources[$surface] 'first-choice specialist route' $surface
    Require-Term $normalizedSources[$surface] 'only when no listed specialist leaf can perform the exact bounded task' $surface
    Require-Term $normalizedSources[$surface] 'one native default child as an L2' $surface
    Require-Term $normalizedSources[$surface] 'does not displace a matching registered specialist' $surface
}
Require-Term $normalizedSources.assignmentSkill 'only as the narrow temporary L2 exception' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'why no listed specialist matches or can perform this task' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'specialist-first condition is satisfied' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'never displaces a matching professional leaf' 'hmasd-writing-agent-assignments'

# The brief is semantic and self-contained before its factual anchors, and the
# caller owns an exact temporary root with read-only default behavior.
Require-Term $normalizedSources.router 'caller must provide a self-contained brief under' 'AGENTS.md'
Require-Term $normalizedSources.router 'confine any permitted writes to exact temporary paths under that caller''s task-scoped temporary root' 'AGENTS.md'
Require-Term $normalizedSources.router 'default mode is read-only' 'AGENTS.md'
Require-Term $normalizedSources.router 'never writes durable state, project code or a non-temporary path' 'AGENTS.md'
Require-Term $normalizedSources.assignmentSkill 'its self-contained brief must state' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'before factual anchors' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'exact caller-owned temporary paths and the mode, which is read-only unless the brief explicitly grants writes only to those exact temporary paths' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'expected observable completion product and the direct evidence' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'named caller''s task-scoped temporary root' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'existing root-to-l1-to-l2 return boundary' 'hmasd-writing-agent-assignments'

$temporaryRoots = @{
    wdm = 'temp/sessions/workflow_design_manager/<root-assignment>/native-default/'
    cpm = 'temp/sessions/code_project_manager/<root-assignment>/native-default/'
    explorer = 'temp/sessions/independent_research_explorer/<root-assignment>/native-default/'
}
foreach ($entry in $temporaryRoots.GetEnumerator()) {
    Require-Term $normalizedSources[$entry.Key] $entry.Value $entry.Key
    Require-Term $normalizedSources[$entry.Key] 'read-only unless that assignment explicitly grants writes to exact temporary paths under that root' $entry.Key
    Require-Term $normalizedSources[$entry.Key] 'never writes durable state, project code or a non-temporary path' $entry.Key
}

# The child remains an L2 evidence producer with no cross-boundary authority.
$commonAuthorityLimits = @(
    'no spawn'
    'cross-owner'
    'canonical-state'
    'Git'
)
foreach ($entry in $normalizedSources.GetEnumerator()) {
    foreach ($limit in $commonAuthorityLimits) {
        Require-Term $entry.Value $limit $entry.Key
    }
}
Require-Term $normalizedSources.router 'owner-acceptance' 'AGENTS.md'
Require-Term $normalizedSources.router 'returns only to' 'AGENTS.md'
Require-Term $normalizedSources.router 'no generic profile or Role' 'AGENTS.md'
foreach ($surface in @('wdm', 'cpm', 'explorer')) {
    Require-Term $normalizedSources[$surface] 'owner-acceptance' $surface
    Require-Term $normalizedSources[$surface] 'cannot bypass Root relay' $surface
    Require-Term $normalizedSources[$surface] 'returns only to' $surface
    Require-Term $normalizedSources[$surface] 'no generic profile or Role' $surface
}
Require-Term $normalizedSources.router 'no spawn, user, sibling, cross-owner or cross-branch contact' 'AGENTS.md'
Require-Term $normalizedSources.router 'no canonical-state, Git, owner-acceptance, compute, external-review, science, code-acceptance, runtime or transport authority' 'AGENTS.md'
Require-Term $normalizedSources.router 'no ability to bypass Root relay' 'AGENTS.md'
Require-Term $normalizedSources.router 'returns only to its invoking L1 parent' 'AGENTS.md'
Require-Term $normalizedSources.assignmentSkill 'no spawn, user/sibling/cross-owner/cross-branch contact' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'canonical-state or Git write' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'owner acceptance, routing, compute' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'external-review, science, code-acceptance, runtime or transport authority' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'no durable, project-code or non-temporary write' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'return only to the invoking l1' 'hmasd-writing-agent-assignments'
Require-Term $normalizedSources.assignmentSkill 'does not create a generic profile or Role' 'hmasd-writing-agent-assignments'

# The exception must not grow a generic registered profile or Role. Check both
# source references and the repository surfaces, while allowing the prose
# phrase "no generic profile or Role" that explicitly forbids that mechanism.
$genericProfileReference = '(?i)\.codex/agents/hmasd-[^\s`)]*generic[^\s`)]*'
$genericRoleReference = '(?i)\.agents/roles/[^\s`)]*generic[^\s`)]*'
foreach ($entry in $sources.GetEnumerator()) {
    if ($entry.Value -match $genericProfileReference) {
        throw "Generic native-default profile reference remains on $($entry.Key)"
    }
    if ($entry.Value -match $genericRoleReference) {
        throw "Generic native-default Role reference remains on $($entry.Key)"
    }
}
$profileDir = Join-Path $repo '.codex/agents'
$roleDir = Join-Path $repo '.agents/roles'
$genericProfiles = @(Get-ChildItem -LiteralPath $profileDir -File -ErrorAction Stop |
        Where-Object { $_.Name -like 'hmasd-*-generic*' })
$genericRoles = @(Get-ChildItem -LiteralPath $roleDir -File -ErrorAction Stop |
        Where-Object { $_.Name -like '*generic*' })
if ($genericProfiles.Count -gt 0 -or $genericRoles.Count -gt 0) {
    throw 'Generic native-default profile or Role file exists'
}

Write-Output 'Native-default temporary-task contract: PASS (static source assertions only)'
