[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$stateScript = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/review_state.ps1"

$registryText = Get-Content -LiteralPath $registryPath -Raw
$registry = $registryText | ConvertFrom-Json
if ($registry.schema_version -ne 7 -or
    $registry.pro_transport.kind -ne "codex_chatgpt_control_visible_ui" -or
    $registry.reviewers.open_divergent.transport -ne "codex_chatgpt_control" -or
    $registry.reviewers.convergent.transport -ne "codex_chatgpt_control") {
    throw "Registry is not the current review transport contract"
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @("chatgpt-delegate", "schema 4", "dispatched exactly once", "BLOCKED_TIMEOUT")) {
    if (-not $skillText.Contains($required)) {
        throw "Review Skill is missing current contract: $required"
    }
}

$stateText = Get-Content -LiteralPath $stateScript -Raw
foreach ($required in @("schema_version = 4", "dispatch_count", "deadline_at")) {
    if (-not $stateText.Contains($required)) {
        throw "Review state script is missing: $required"
    }
}
foreach ($forbidden in @("migrate", "ConsentState", "Parse-Receipt", "legacy_codex_exchange", "source=manual")) {
    if ($stateText.Contains($forbidden)) {
        throw "Review state retains legacy machinery: $forbidden"
    }
}

function New-Round {
    $path = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-review-state-" + [guid]::NewGuid().ToString("N"))
    [void](New-Item -ItemType Directory -Path $path)
    & $stateScript -Mode init -RoundPath $path | Out-Null
    $path
}

function Route([string]$RoundPath, [string]$Role, [string]$Artifact) {
    $id = Split-Path -Leaf $RoundPath
    "$id`:$Role`:$("a" * 40)`:docs/external-review/rounds/$id/$Artifact"
}

function Complete-External([string]$RoundPath, [string]$Stage, [string]$Role, [string]$Artifact) {
    $route = Route $RoundPath $Role $Artifact
    $deadline = [DateTimeOffset]::Now.AddHours(2).ToString("o")
    & $stateScript -Mode transition -RoundPath $RoundPath -Stage $Stage `
        -State DISPATCHED -RouteToken $route -DeadlineAt $deadline | Out-Null
    Set-Content -LiteralPath (Join-Path $RoundPath $Artifact) -Value "RAW" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $RoundPath -Stage $Stage `
        -State COMPLETE -RouteToken $route | Out-Null
}

$happy = New-Round
$blocked = New-Round
try {
    $initial = Get-Content -LiteralPath (Join-Path $happy "05_REVIEW_STATE.json") -Raw | ConvertFrom-Json
    if ($initial.schema_version -ne 4 -or $initial.stages.gemini_divergent.dispatch_count -ne 0) {
        throw "Review state did not initialize schema 4"
    }

    Complete-External $happy "gemini_divergent" "GEMINI_DIVERGENT" "11_GEMINI_DIVERGENT_RAW.md"
    Complete-External $happy "open_pro" "OPEN_DIVERGENT" "21_PRO_OPEN_RAW.md"
    Set-Content -LiteralPath (Join-Path $happy "30_CONTROLLER_SYNTHESIS.md") -Value "SYNTHESIS" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $happy -Stage controller_synthesis -State COMPLETE | Out-Null
    Complete-External $happy "convergent_pro" "CONVERGENT" "41_PRO_CONVERGENT_RAW.md"
    Set-Content -LiteralPath (Join-Path $happy "50_DISPOSITION.md") -Value "DISPOSITION" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $happy -Stage controller_disposition -State COMPLETE | Out-Null
    if ((& $stateScript -Mode next -RoundPath $happy) -ne "CLOSED") {
        throw "Completed review round did not close"
    }

    & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
        -State BLOCKED -Blocker "PRE_DISPATCH_BOUNDARY" | Out-Null
    $route = Route $blocked "GEMINI_DIVERGENT" "11_GEMINI_DIVERGENT_RAW.md"
    $deadline = [DateTimeOffset]::Now.AddHours(2).ToString("o")
    & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
        -State DISPATCHED -RouteToken $route -DeadlineAt $deadline | Out-Null
    & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
        -State BLOCKED -Blocker "BLOCKED_TIMEOUT" | Out-Null

    $redispatchFailed = $false
    try {
        & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
            -State DISPATCHED -RouteToken $route -DeadlineAt $deadline | Out-Null
    } catch {
        $redispatchFailed = $true
    }
    if (-not $redispatchFailed) {
        throw "Post-dispatch blocker allowed a duplicate dispatch"
    }
    $state = Get-Content -LiteralPath (Join-Path $blocked "05_REVIEW_STATE.json") -Raw | ConvertFrom-Json
    if ($state.stages.gemini_divergent.dispatch_count -ne 1 -or
        $state.stages.gemini_divergent.route_token -ne $route -or
        $state.stages.gemini_divergent.state -ne "BLOCKED") {
        throw "Blocked review stage lost immutable dispatch evidence"
    }
} finally {
    foreach ($path in @($happy, $blocked)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}

Write-Output "REVIEW_ROUND_CONTRACT_OK"
