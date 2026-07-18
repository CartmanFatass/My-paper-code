$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillPath = Join-Path $repo ".agents/skills/hmasd-work/SKILL.md"
$agentsPath = Join-Path $repo "AGENTS.md"
$metadataPath = Join-Path $repo ".agents/skills/hmasd-work/agents/openai.yaml"
$referencesPath = Join-Path $repo ".agents/skills/hmasd-work/references"

$skill = Get-Content -LiteralPath $skillPath -Raw
$agents = Get-Content -LiteralPath $agentsPath -Raw
$metadata = Get-Content -LiteralPath $metadataPath -Raw
$normalizedSkill = ($skill -replace '\s+', ' ').Trim()
$normalizedAgents = ($agents -replace '\s+', ' ').Trim()

$requiredSkillText = @(
    "HMASD domain overlay",
    "superpowers:test-driven-development",
    "superpowers:subagent-driven-development",
    "HMASD Contract",
    "active controller"
)
foreach ($text in $requiredSkillText) {
    if (-not $normalizedSkill.Contains($text)) {
        throw "Missing hmasd-work contract text: $text"
    }
}

$forbiddenSkillText = @(
    ".codex/collaboration/active",
    "PACKAGE_READY",
    "REVIEW_READY",
    "combined reviewer",
    "brief-template.md",
    "collaboration-protocol.md"
)
foreach ($text in $forbiddenSkillText) {
    if ($normalizedSkill.Contains($text)) {
        throw "Obsolete hmasd-work harness text remains: $text"
    }
}

$requiredAgentsText = @(
    "Superpowers is the generic development lifecycle harness",
    "Superpowers test-first and task-review requirements take precedence",
    "Existing HMASD authorization satisfies the approval boundary",
    "Do not create a worktree unless the user explicitly requests one"
)
foreach ($text in $requiredAgentsText) {
    if (-not $normalizedAgents.Contains($text)) {
        throw "Missing AGENTS harness precedence text: $text"
    }
}

if (-not $metadata.Contains("Apply HMASD semantic constraints")) {
    throw "hmasd-work UI metadata is stale"
}

if (Test-Path -LiteralPath $referencesPath) {
    $remaining = @(Get-ChildItem -LiteralPath $referencesPath -File)
    if ($remaining.Count -ne 0) {
        throw "Obsolete hmasd-work reference files remain"
    }
}

Write-Output "HMASD_WORK_HARNESS_CONTRACT_OK"
