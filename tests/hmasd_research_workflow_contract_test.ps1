$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillsRoot = Join-Path $repo ".agents/skills"
$canonicalRoot = Join-Path $repo "docs/project"
$sessionRolesPath = Join-Path $skillsRoot "hmasd-task-router/references/session-roles.json"
$expectedSkills = @(
    "hmasd-code-manager",
    "hmasd-experiment",
    "hmasd-project-manager",
    "hmasd-review-exchange",
    "hmasd-review-round",
    "hmasd-task-router"
)
$canonicalDocs = @(
    "CURRENT_WORK.md",
    "ALGORITHM_PRINCIPLES.md",
    "IMPLEMENTATION_PLAN.md",
    "ExpRecord.md"
)

function Read-Text([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing workflow file: $Path"
    }
    Get-Content -LiteralPath $Path -Raw
}

$skillNames = @(Get-ChildItem -LiteralPath $skillsRoot -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') } |
    Sort-Object Name | Select-Object -ExpandProperty Name)
if (($skillNames -join "|") -ne ($expectedSkills -join "|")) {
    throw "Project Skill set must be exactly: $($expectedSkills -join ', ')"
}

foreach ($name in $canonicalDocs) {
    [void](Read-Text (Join-Path $canonicalRoot $name))
}
foreach ($legacy in @(
    "docs/project/MARL_ENGINEERING_PRINCIPLES.md",
    "memory/CURRENT_WORK.md",
    "memory/ALGORITHM_PRINCIPLES.md",
    "memory/IMPLEMENTATION_PLAN.md",
    "memory/ExpRecord.md",
    "docs/research/MARL_ENGINEERING_PRINCIPLES.md",
    ".codex/collaboration/.gitignore",
    ".codex/collaboration/conversations.json",
    ".codex/collaboration/active/stage-c-performance-diagnosis/BRIEF.md"
)) {
    if (Test-Path -LiteralPath (Join-Path $repo $legacy)) {
        throw "Legacy workflow path must not exist: $legacy"
    }
}

$agents = Read-Text (Join-Path $repo "AGENTS.md")
foreach ($required in @(
    "Every persistent HMASD Codex session reads",
    "Any persistent-session topology change also uses that Skill",
    "Do not send across a partially migrated graph",
    "docs/project/CURRENT_WORK.md",
    "The controller alone owns",
    "There is no general controller orchestration Skill",
    "Mutation Tiers",
    "ordinary files inside an assigned working scope",
    "Role and Context Firewall",
    "MARL exploration remains agile",
    "Do not retain backward-compatibility adapters",
    "sole tracked-worktree write lease",
    "hmasd-review-exchange",
    "hmasd-review-round",
    "hmasd-experiment",
    "hmasd-task-router"
)) {
    if (-not $agents.Contains($required)) {
        throw "AGENTS.md is missing controller contract: $required"
    }
}
foreach ($forbidden in @(
    "MARL_ENGINEERING_PRINCIPLES.md",
    "hmasd-research-cycle",
    "combined reviewer",
    "BRIEF.md"
)) {
    if ($agents.Contains($forbidden)) {
        throw "AGENTS.md retains obsolete workflow text: $forbidden"
    }
}

$current = Read-Text (Join-Path $canonicalRoot "CURRENT_WORK.md")
if (-not $current.Contains("## Controller Ownership") -or
    -not $current.Contains("## Current Boundary") -or
    -not $current.Contains("## Next Action") -or
    -not $current.Contains("## Autonomous Boundary") -or
    $current.Contains("MARL_ENGINEERING_PRINCIPLES.md")) {
    throw "CURRENT_WORK does not preserve the controller control-plane structure"
}

$plan = Read-Text (Join-Path $canonicalRoot "IMPLEMENTATION_PLAN.md")
if (-not $plan.Contains("# HA-CTSE Active Implementation Plan") -or
    -not $plan.Contains("Status:") -or
    $plan.Contains("MARL_ENGINEERING_PRINCIPLES.md")) {
    throw "IMPLEMENTATION_PLAN does not preserve its active-plan interface"
}

$codeManager = Read-Text (Join-Path $skillsRoot "hmasd-code-manager/SKILL.md")
foreach ($required in @(
    'START_CODE_WORK',
    'code_implementation_manager',
    'docs/project/IMPLEMENTATION_PLAN.md',
    'references/engineering-principles.md',
    "model's native coding workflow",
    'Shared-Worktree Lease',
    'CODE_GIT_PUSH_REQUIRED',
    'CODE_EXTERNAL_REVIEW_REQUIRED',
    'CODE_COMPLETE',
    'CODE_BLOCKED',
    'Never stage, commit, or push'
)) {
    if (-not $codeManager.Contains($required)) {
        throw "Code Implementation Manager Skill is missing: $required"
    }
}

$engineering = Read-Text (Join-Path $skillsRoot "hmasd-code-manager/references/engineering-principles.md")
foreach ($required in @(
    'Pack padded or indexed data once',
    'Sampling, storage, replay',
    'stage-level wall time'
)) {
    if (-not $engineering.Contains($required)) {
        throw "Code Manager engineering reference is missing: $required"
    }
}

$experiment = Read-Text (Join-Path $skillsRoot "hmasd-experiment/SKILL.md")
$protocol = Read-Text (Join-Path $skillsRoot "hmasd-experiment/references/experiment-protocol.md")
if (-not $experiment.Contains("inside the persistent HMASD experiment-monitor session") -or
    -not $experiment.Contains("role_skill=.agents/skills/hmasd-experiment/SKILL.md") -or
    -not $experiment.Contains("Do not read project-control") -or
    -not $experiment.Contains("monitor session creates and owns its heartbeat") -or
    -not $experiment.Contains("session-roles.json.roles.experiment_monitor.thread_id") -or
    -not $experiment.Contains("session-roles.json.roles.controller.thread_id") -or
    -not $experiment.Contains("interval is never shorter than 10") -or
    -not $protocol.Contains("One bounded heartbeat") -or
    -not $protocol.Contains('delete this heartbeat with `automation_update`')) {
    throw "Experiment-monitor role boundary is incomplete"
}

$review = Read-Text (Join-Path $skillsRoot "hmasd-review-round/SKILL.md")
if (-not $review.Contains("This is a controller workflow") -or
    -not $review.Contains("controller owns round files") -or
    -not $review.Contains("REVIEW_STAGE") -or
    -not $review.Contains("gemini_divergent_exchange") -or
    -not $review.Contains("open_divergent_exchange") -or
    -not $review.Contains("convergent_exchange") -or
    -not $review.Contains("There is no review state machine") -or
    -not $review.Contains("no controller heartbeat") -or
    -not $review.Contains("commit and push")) {
    throw "Controller-owned external review boundary is incomplete"
}

$exchange = Read-Text (Join-Path $skillsRoot "hmasd-review-exchange/SKILL.md")
$normalizedExchange = $exchange -replace '\s+', ' '
foreach ($required in @(
    'role_skill=.agents/skills/hmasd-review-exchange/SKILL.md',
    'gemini_divergent_exchange',
    'open_divergent_exchange',
    'convergent_exchange',
    'Contact only the controller',
    'CURRENT_REVIEW_ASSIGNMENT',
    'Ignore every earlier round, SHA and question path in this conversation',
    'create one 5-minute heartbeat',
    'exact text equality',
    'Reply to Controller'
)) {
    if (-not $normalizedExchange.Contains($required)) {
        throw "Reviewer Exchange role boundary is incomplete: $required"
    }
}

$router = Read-Text (Join-Path $skillsRoot "hmasd-task-router/SKILL.md")
$sessionRoles = Read-Text $sessionRolesPath | ConvertFrom-Json
if (-not $router.Contains("Controller Send Contract") -or
    -not $router.Contains("Session and Role Directory") -or
    $sessionRoles.policy.update_owner -ne "active_controller" -or
    -not $sessionRoles.policy.one_session_one_role) {
    throw "Controller communication or session-role ownership is incomplete"
}
foreach ($forbidden in @("CONTINUE_REVIEW", "RESUME_REVIEW", "REVIEW_BOUNDARY_READY", "05_REVIEW_STATE.json")) {
    if ($review.Contains($forbidden)) {
        throw "External Review Manager retains obsolete controller/state lifecycle: $forbidden"
    }
}
if ($review.Contains('external_review_manager') -or
    $exchange.Contains('external_review_manager') -or
    $null -ne $sessionRoles.roles.PSObject.Properties['external_review_manager']) {
    throw 'Obsolete External Review Manager topology remains'
}

foreach ($skill in $expectedSkills) {
    [void](Read-Text (Join-Path $skillsRoot "$skill/agents/openai.yaml"))
}

Write-Output "HMASD_ROLE_ISOLATION_CONTRACT_OK"
