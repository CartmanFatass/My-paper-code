[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Read-Text([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing code-workflow file: $Path"
    }
    Get-Content -LiteralPath $Path -Raw
}

$manager = Read-Text (Join-Path $repo '.agents/skills/hmasd-code-manager/SKILL.md')
$normalizedManager = $manager -replace '\s+', ' '
$reviewer = Read-Text (Join-Path $repo '.agents/skills/hmasd-code-reviewer/SKILL.md')
$managerYaml = Read-Text (Join-Path $repo '.agents/skills/hmasd-code-manager/agents/openai.yaml')
$reviewerYaml = Read-Text (Join-Path $repo '.agents/skills/hmasd-code-reviewer/agents/openai.yaml')
$agents = Read-Text (Join-Path $repo 'AGENTS.md')
$normalizedAgents = $agents -replace '\s+', ' '
$current = Read-Text (Join-Path $repo 'docs/project/CURRENT_WORK.md')
$plan = Read-Text (Join-Path $repo 'docs/project/IMPLEMENTATION_PLAN.md')
$roles = Read-Text (Join-Path $repo '.agents/skills/hmasd-task-router/references/session-roles.json') | ConvertFrom-Json

foreach ($required in @(
    'START_CODE_WORK',
    'base_commit=<40-character pushed SHA>',
    'source_commit=<40-character pushed SHA>',
    'git merge-base --is-ancestor <source_commit> My-paper-code/aggressive',
    'never run a network Git command',
    'Own the concrete executable architecture',
    'standing permanent grant',
    'without a separate approval or retry loop',
    'spawn one implementer with `$hmasd-implementer`',
    'spawn one fresh read-only reviewer with `$hmasd-code-reviewer`',
    'after two failed delegated attempts',
    'One file has one writer',
    'CODE_GIT_PUSH_REQUIRED',
    'CODE_COMPLETE',
    'CODE_BLOCKED',
    'hostId',
    'threadId',
    'model',
    'thinking',
    'This manager owns no heartbeat'
)) {
    if (-not $normalizedManager.Contains($required)) {
        throw "Code Manager contract is missing: $required"
    }
}

foreach ($forbidden in @(
    'git push My-paper-code aggressive',
    'launch the experiment',
    'select the next hypothesis'
)) {
    if ($manager.Contains($forbidden)) {
        throw "Code Manager contract exceeds authority: $forbidden"
    }
}

foreach ($required in @(
    'temporary read-only HMASD reviewer subagent',
    'actual integrated diff against `base_commit`',
    'probability support and likelihood replay',
    'gradient, detach, credit, recurrent-state',
    'repeated packing, scalar CUDA',
    'CODE_REVIEW_APPROVED',
    'CODE_REVIEW_CHANGES_REQUIRED',
    'never edits',
    'Do not send a cross-session message'
)) {
    if (-not $reviewer.Contains($required)) {
        throw "Code Reviewer contract is missing: $required"
    }
}

if (-not $managerYaml.Contains('$hmasd-code-manager') -or
    -not $reviewerYaml.Contains('$hmasd-code-reviewer')) {
    throw 'Code role default prompts lost their literal Skill invocation'
}

foreach ($required in @(
    'Code Implementation Manager owns concrete executable architecture',
    '$hmasd-code-manager',
    '$hmasd-code-reviewer',
    'controller communicates only with the Code Implementation Manager',
    'controller neither dispatches these subagents nor performs implementation review',
    'standing, permanent, exclusive write authority',
    'must not trigger repeated protected-file approval requests'
)) {
    if (-not $normalizedAgents.Contains($required)) {
        throw "AGENTS code-role isolation is missing: $required"
    }
}

if (-not $current.Contains('Code Implementation Manager') -or
    -not $current.Contains('Active controller:') -or
    -not ($plan.Contains('Status: NONE') -or $plan.Contains('Status: AUTHORIZED_IN_PROGRESS')) -or
    -not ($plan.Contains('registered Code Implementation Manager') -or
          $plan.Contains('Code Implementation Manager is the sole writer'))) {
    throw 'Project control does not preserve controller/code-manager ownership'
}

$codeManagerRole = $roles.roles.code_implementation_manager
if ($roles.schema_version -ne 4 -or
    [string]::IsNullOrWhiteSpace($codeManagerRole.thread_id) -or
    $codeManagerRole.registration_status -ne 'ACTIVE' -or
    $codeManagerRole.role_skill -ne '.agents/skills/hmasd-code-manager/SKILL.md') {
    throw 'The persistent Code Implementation Manager is not actively registered'
}
foreach ($forbidden in @('hostId', 'model', 'thinking')) {
    if ($null -ne $codeManagerRole.PSObject.Properties[$forbidden]) {
        throw "Code manager registry stores live route metadata: $forbidden"
    }
}

Write-Output 'HMASD_CODE_MANAGER_CONTRACT_OK'
