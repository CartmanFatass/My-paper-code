$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillsRoot = Join-Path $repo ".agents/skills"
$canonicalRoot = Join-Path $repo "docs/project"
$expectedSkills = @(
    "hmasd-experiment",
    "hmasd-implementer",
    "hmasd-research-cycle",
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
    "docs/research/MARL_ENGINEERING_PRINCIPLES.md"
)) {
    if (Test-Path -LiteralPath (Join-Path $repo $legacy)) {
        throw "Legacy canonical path must not exist: $legacy"
    }
}

$agents = Read-Text (Join-Path $repo "AGENTS.md")
foreach ($required in @(
    "Every HMASD Codex session reads",
    "docs/project/CURRENT_WORK.md",
    "Direct controller work is the default",
    "MARL exploration is agile by default",
    "Do not implement or retain backward",
    "External Review Manager",
    '`$hmasd-implementer',
    '`$hmasd-task-router'
)) {
    if (-not $agents.Contains($required)) {
        throw "AGENTS.md is missing structural contract: $required"
    }
}
foreach ($forbidden in @("MARL_ENGINEERING_PRINCIPLES.md", "normal-research expectation")) {
    if ($agents.Contains($forbidden)) {
        throw "AGENTS.md retains obsolete global workflow text: $forbidden"
    }
}

$implementer = Read-Text (Join-Path $skillsRoot "hmasd-implementer/SKILL.md")
$engineering = Read-Text (Join-Path $skillsRoot "hmasd-implementer/references/engineering-principles.md")
foreach ($required in @(
    'the controller''s current task message',
    'docs/project/ALGORITHM_PRINCIPLES.md',
    'Do not load `CURRENT_WORK.md`',
    'Do not add backward-compatibility branches',
    'Run the single focused check'
)) {
    if (-not $implementer.Contains($required)) {
        throw "Implementer Skill is missing: $required"
    }
}
foreach ($required in @('Pack padded or indexed data once', 'Sampling, storage, replay', 'stage-level wall time')) {
    if (-not $engineering.Contains($required)) {
        throw "Implementer engineering reference is missing: $required"
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
if (-not $experiment.Contains("inside the persistent HMASD experiment-monitor task") -or
    -not $experiment.Contains("hmasd-task-router") -or
    -not $protocol.Contains("One bounded heartbeat") -or
    -not $protocol.Contains('send exactly one payload')) {
    throw "Experiment-monitor role boundary is incomplete"
}

$review = Read-Text (Join-Path $skillsRoot "hmasd-review-round/SKILL.md")
$reviewState = Read-Text (Join-Path $skillsRoot "hmasd-review-round/scripts/review_state.ps1")
if (-not $review.Contains("START_REVIEW") -or
    -not $review.Contains("REVIEW_COMPLETE") -or
    -not $review.Contains("persistent Luna External Review Manager") -or
    -not $review.Contains("30_EVIDENCE_RECONCILIATION.md") -or
    -not $reviewState.Contains("schema_version = 5")) {
    throw "External Review Manager boundary is incomplete"
}

foreach ($skill in $expectedSkills) {
    [void](Read-Text (Join-Path $skillsRoot "$skill/agents/openai.yaml"))
}

Write-Output "HMASD_RESEARCH_WORKFLOW_CONTRACT_OK"
