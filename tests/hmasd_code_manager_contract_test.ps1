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
$engineering = Read-Text (Join-Path $repo '.agents/skills/hmasd-code-manager/references/engineering-principles.md')
$managerYaml = Read-Text (Join-Path $repo '.agents/skills/hmasd-code-manager/agents/openai.yaml')
$agents = Read-Text (Join-Path $repo 'AGENTS.md')
$normalizedAgents = $agents -replace '\s+', ' '
$roles = Read-Text (Join-Path $repo '.agents/skills/hmasd-task-router/references/session-roles.json') | ConvertFrom-Json

foreach ($required in @(
    'START_CODE_WORK',
    'base_commit=<40-character pushed SHA>',
    'source_commit=<40-character pushed SHA>',
    'git merge-base --is-ancestor <source_commit> My-paper-code/aggressive',
    'references/engineering-principles.md',
    'standing, permanent, exclusive authority',
    "model's native coding workflow",
    'Shared-Worktree Lease',
    'sole tracked workspace write lease',
    'CODE_GIT_PUSH_REQUIRED',
    'CODE_EXTERNAL_REVIEW_REQUIRED',
    'CODE_COMPLETE',
    'CODE_BLOCKED',
    'Never stage, commit, or push',
    'This manager owns no heartbeat'
)) {
    if (-not $normalizedManager.Contains($required)) {
        throw "Code Manager contract is missing: $required"
    }
}

foreach ($forbidden in @(
    'hmasd-implementer',
    'hmasd-code-reviewer',
    'CODE_REVIEW_APPROVED',
    'spawn one implementer',
    'spawn one fresh read-only reviewer'
)) {
    if ($normalizedManager.Contains($forbidden) -or $agents.Contains($forbidden)) {
        throw "Obsolete prescribed internal workflow remains: $forbidden"
    }
}

foreach ($required in @(
    'Pack padded or indexed data once',
    'Sampling, storage, replay',
    'stage-level wall time'
)) {
    if (-not $engineering.Contains($required)) {
        throw "Code Manager engineering reference is missing: $required"
    }
}

foreach ($required in @(
    'sole tracked-worktree write lease',
    'manager acceptance of the integrated result',
    'does not prescribe internal roles, models, effort settings'
)) {
    if (-not $normalizedAgents.Contains($required)) {
        throw "AGENTS code-manager boundary is missing: $required"
    }
}

foreach ($removed in @(
    '.agents/skills/hmasd-implementer/SKILL.md',
    '.agents/skills/hmasd-code-reviewer/SKILL.md'
)) {
    if (Test-Path -LiteralPath (Join-Path $repo $removed)) {
        throw "Removed internal-role Skill still exists: $removed"
    }
}

if (-not $managerYaml.Contains('$hmasd-code-manager')) {
    throw 'Code Manager default prompt lost its literal Skill invocation'
}

$role = $roles.roles.code_implementation_manager
if ($roles.schema_version -ne 4 -or
    [string]::IsNullOrWhiteSpace($role.thread_id) -or
    $role.registration_status -ne 'ACTIVE' -or
    $role.role_skill -ne '.agents/skills/hmasd-code-manager/SKILL.md') {
    throw 'The persistent Code Implementation Manager is not actively registered'
}
foreach ($forbidden in @('hostId', 'model', 'thinking')) {
    if ($null -ne $role.PSObject.Properties[$forbidden]) {
        throw "Code manager registry stores live route metadata: $forbidden"
    }
}

Write-Output 'HMASD_CODE_MANAGER_CONTRACT_OK'
