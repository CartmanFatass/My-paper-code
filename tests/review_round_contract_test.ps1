[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$stateScript = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/review_state.ps1"
$agentsPath = Join-Path $repo "AGENTS.md"

$registryText = Get-Content -LiteralPath $registryPath -Raw
$registry = $registryText | ConvertFrom-Json
if ($registry.schema_version -ne 7 -or
    $registry.pro_transport.kind -ne "codex_chatgpt_control_visible_ui" -or
    $registry.reviewers.open_divergent.transport -ne "codex_chatgpt_control" -or
    $registry.reviewers.convergent.transport -ne "codex_chatgpt_control") {
    throw "Registry is not the current-only review transport contract"
}
foreach ($forbidden in @("legacy_codex_exchange", "backward_compatibility")) {
    if ($registryText -match $forbidden) {
        throw "Registry retains a superseded Pro transport: $forbidden"
    }
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @("chatgpt-delegate", "messages.waitAndRead", "05_REVIEW_STATE.json")) {
    if (-not $skillText.Contains($required)) {
        throw "Skill is missing the current review path: $required"
    }
}
foreach ($forbidden in @("Historical Compatibility", "source=exchange", "source=manual", "completion receipt")) {
    if ($skillText.Contains($forbidden)) {
        throw "Skill retains compatibility process: $forbidden"
    }
}

$stateText = Get-Content -LiteralPath $stateScript -Raw
foreach ($forbidden in @("migrate", "ConsentState", "Parse-Receipt", "legacy_codex_exchange", "source=manual")) {
    if ($stateText.Contains($forbidden)) {
        throw "State script retains legacy machinery: $forbidden"
    }
}

$agentsText = Get-Content -LiteralPath $agentsPath -Raw
foreach ($required in @(
    "Active-line development is the default",
    "MARL exploration is agile by default"
)) {
    if (-not $agentsText.Contains($required)) {
        throw "AGENTS.md is missing the current development rule: $required"
    }
}

$tmpRound = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-review-state-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmpRound -Force | Out-Null
try {
    & $stateScript -Mode init -RoundPath $tmpRound | Out-Null
    $roundId = Split-Path -Leaf $tmpRound
    $commit = "a" * 40
    $route = "$roundId`:OPEN_DIVERGENT`:$commit`:docs/external-review/rounds/$roundId/21_PRO_OPEN_RAW.md"
    & $stateScript -Mode transition -RoundPath $tmpRound -Stage open_pro `
        -State DISPATCHED -RouteToken $route | Out-Null
    Set-Content -LiteralPath (Join-Path $tmpRound "21_PRO_OPEN_RAW.md") `
        -Value "CURRENT_PRO_RAW" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $tmpRound -Stage open_pro `
        -State COMPLETE -RouteToken $route | Out-Null
    $validation = & $stateScript -Mode validate -RoundPath $tmpRound
    if (($validation -join "`n") -notmatch "review_state=VALID") {
        throw "Current review state did not validate"
    }
} finally {
    if (Test-Path -LiteralPath $tmpRound) {
        Remove-Item -LiteralPath $tmpRound -Recurse -Force
    }
}

Write-Output "REVIEW_ROUND_CONTRACT_OK"
