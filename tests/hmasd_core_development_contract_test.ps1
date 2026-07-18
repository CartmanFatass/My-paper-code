$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$agentsPath = Join-Path $repo "AGENTS.md"
$currentWorkPath = Join-Path $repo "memory/CURRENT_WORK.md"
$removedSkillPath = Join-Path $repo ".agents/skills/hmasd-work"

$agents = (Get-Content -LiteralPath $agentsPath -Raw) -replace '\s+', ' '
$currentWork = Get-Content -LiteralPath $currentWorkPath -Raw

if (Test-Path -LiteralPath $removedSkillPath) {
    throw "hmasd-work must be removed after its durable rules move to AGENTS.md"
}

$requiredAgentsText = @(
    "Direct controller work is the default",
    "superpowers:brainstorming",
    "superpowers:writing-plans",
    "superpowers:test-driven-development",
    "superpowers:subagent-driven-development",
    "superpowers:verification-before-completion",
    "HMASD Contract",
    "does not imply one research hypothesis, architecture or permitted successor",
    "gpt-5.6-terra` medium",
    "gpt-5.6-terra` high",
    "gpt-5.6-sol` high"
)
foreach ($text in $requiredAgentsText) {
    if (-not $agents.Contains($text)) {
        throw "Missing core-development contract text: $text"
    }
}

$forbiddenRepositoryText = @(
    '$hmasd-work',
    'strongest available model',
    'Controller model:',
    'Controller reasoning:'
)
foreach ($text in $forbiddenRepositoryText) {
    if ($agents.Contains($text) -or $currentWork.Contains($text)) {
        throw "Controller model selection or removed Skill remains in project state: $text"
    }
}

Write-Output "HMASD_CORE_DEVELOPMENT_CONTRACT_OK"
