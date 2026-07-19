$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillsRoot = Join-Path $repo ".agents/skills"
$canonicalRoot = Join-Path $repo "docs/project"
$expectedSkills = @("hmasd-experiment", "hmasd-research-cycle", "hmasd-review-round", "hmasd-task-router")
$canonicalDocs = @(
    "CURRENT_WORK.md",
    "ALGORITHM_PRINCIPLES.md",
    "MARL_ENGINEERING_PRINCIPLES.md",
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
    Sort-Object Name | Select-Object -ExpandProperty Name)
if (($skillNames -join "|") -ne ($expectedSkills -join "|")) {
    throw "Project Skill set must be exactly: $($expectedSkills -join ', ')"
}

foreach ($name in $canonicalDocs) {
    [void](Read-Text (Join-Path $canonicalRoot $name))
}
foreach ($legacy in @(
    "memory/CURRENT_WORK.md",
    "memory/ALGORITHM_PRINCIPLES.md",
    "memory/IMPLEMENTATION_PLAN.md",
    "memory/ExpRecord.md",
    "docs/research/MARL_ENGINEERING_PRINCIPLES.md"
)) {
    if (Test-Path -LiteralPath (Join-Path $repo $legacy)) {
        throw "Legacy canonical path must not exist: $legacy"
    }
}

$agents = Read-Text (Join-Path $repo "AGENTS.md")
foreach ($required in @(
    "docs/project/CURRENT_WORK.md",
    "Direct controller work is the default",
    "MARL exploration is agile by default",
    "Active-line development is the default",
    "No Skill recursively triggers itself",
    "convergent GPT-5.6 Pro stage",
    '`gpt-5.6-sol` / `xhigh`',
    '`$hmasd-task-router'
)) {
    if (-not $agents.Contains($required)) {
        throw "AGENTS.md is missing structural contract: $required"
    }
}
foreach ($legacy in @("memory/CURRENT_WORK.md", "memory/IMPLEMENTATION_PLAN.md")) {
    if ($agents.Contains($legacy)) {
        throw "AGENTS.md still points to a legacy control path: $legacy"
    }
}

$research = Read-Text (Join-Path $skillsRoot "hmasd-research-cycle/SKILL.md")
if ($research -notmatch '(?s)^---.*description:.*explicitly invokes \$hmasd-research-cycle.*ACTIVE Autonomous Boundary.*---' -or
    $research -notmatch '(?s)## Stop.*Do not invoke this Skill\s+again' -or
    -not $research.Contains('BLOCKED_MISSING_PRO_DISPOSITION')) {
    throw "Research-cycle trigger or stop boundary is incomplete"
}

$experiment = Read-Text (Join-Path $skillsRoot "hmasd-experiment/SKILL.md")
$protocol = Read-Text (Join-Path $skillsRoot "hmasd-experiment/references/experiment-protocol.md")
if (-not $experiment.Contains("references/experiment-protocol.md") -or
    -not $experiment.Contains("references/monitor-task.json") -or
    -not $protocol.Contains("Persistent Luna Monitor Task") -or
    -not $protocol.Contains('relays `TIMEOUT`') -or
    -not $protocol.Contains("BLOCKED_REPEATED_OPERATIONAL_FAILURE")) {
    throw "Experiment lifecycle deadline or retry boundary is incomplete"
}

$review = Read-Text (Join-Path $skillsRoot "hmasd-review-round/SKILL.md")
$reviewState = Read-Text (Join-Path $skillsRoot "hmasd-review-round/scripts/review_state.ps1")
if (-not $review.Contains("dispatched exactly once") -or
    -not $review.Contains("BLOCKED_TIMEOUT") -or
    -not $review.Contains("gpt-5.6-terra") -or
    -not $review.Contains("single-line document pointer") -or
    -not $review.Contains("one registered Luna Exchange") -or
    -not $review.Contains("30_EVIDENCE_RECONCILIATION.md") -or
    -not $review.Contains("Codex in-app browser") -or
    -not $reviewState.Contains("schema_version = 5") -or
    -not $reviewState.Contains("dispatch_count")) {
    throw "Review dispatch loop guard is incomplete"
}

foreach ($skill in $expectedSkills) {
    [void](Read-Text (Join-Path $skillsRoot "$skill/agents/openai.yaml"))
}

Write-Output "HMASD_RESEARCH_WORKFLOW_CONTRACT_OK"
