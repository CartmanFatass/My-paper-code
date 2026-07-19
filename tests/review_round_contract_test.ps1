[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$stateScript = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/review_state.ps1"

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
$manager = $registry.review_manager
if ($registry.schema_version -ne 15 -or
    $manager.kind -ne "persistent_full_round_manager" -or
    $manager.thread_id -ne "019f716c-676f-7673-9782-f37b72f200d2" -or
    $manager.route_policy -ne "resolve_live_immediately_before_each_send" -or
    $manager.start_message -ne "START_REVIEW" -or
    $manager.browser.ui_scope -ne "application_shared" -or
    $manager.browser.logical_owner -ne "review_manager" -or
    $manager.heartbeat.target_thread_id -ne $manager.thread_id -or
    $registry.reviewers.gemini_divergent.transport -ne "review_manager_antigravity_cli" -or
    $registry.reviewers.open_divergent.transport -ne "review_manager_in_app_browser" -or
    $registry.reviewers.convergent.transport -ne "review_manager_in_app_browser") {
    throw "External Review Manager registry is inconsistent"
}
if ($null -ne $manager.PSObject.Properties['model'] -or
    $null -ne $manager.PSObject.Properties['thinking'] -or
    $null -ne $manager.controller_return_route.PSObject.Properties['model'] -or
    $null -ne $manager.controller_return_route.PSObject.Properties['thinking']) {
    throw "External Review Manager registry must not mirror Codex model or thinking"
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @(
    "START_REVIEW",
    "Do not spawn a Gemini transport subagent",
    "browser tools for a tracked review",
    "controller's only scientific input from the round"
)) {
    if (-not $skillText.Contains($required)) {
        throw "Review Manager contract is missing: $required"
    }
}
if ($skillText -match "repair_incomplete|repair_unaccepted_dispatch|fork_turns") {
    throw "Review Manager retains removed recovery or subagent machinery"
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
        -State COMPLETE | Out-Null
}

$happy = New-Round
$blocked = New-Round
try {
    $initial = Get-Content -LiteralPath (Join-Path $happy "05_REVIEW_STATE.json") -Raw | ConvertFrom-Json
    if ($initial.schema_version -ne 5 -or $initial.stages.gemini_divergent.dispatch_count -ne 0) {
        throw "Review state did not initialize schema 5"
    }

    Complete-External $happy "gemini_divergent" "GEMINI_DIVERGENT" "11_GEMINI_DIVERGENT_RAW.md"
    Complete-External $happy "open_pro" "OPEN_DIVERGENT" "21_PRO_OPEN_RAW.md"
    Set-Content -LiteralPath (Join-Path $happy "30_EVIDENCE_RECONCILIATION.md") -Value "RECONCILIATION" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $happy -Stage evidence_reconciliation -State COMPLETE | Out-Null
    Complete-External $happy "convergent_pro" "CONVERGENT" "41_PRO_CONVERGENT_RAW.md"
    Set-Content -LiteralPath (Join-Path $happy "50_DISPOSITION.md") -Value "DISPOSITION" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $happy -Stage controller_disposition -State COMPLETE | Out-Null
    if ((& $stateScript -Mode next -RoundPath $happy) -ne "CLOSED") {
        throw "Completed review round did not close"
    }

    & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
        -State BLOCKED -Blocker "TRANSPORT_FAILURE" | Out-Null
    $route = Route $blocked "GEMINI_DIVERGENT" "11_GEMINI_DIVERGENT_RAW.md"
    $deadline = [DateTimeOffset]::Now.AddHours(2).ToString("o")
    $retrySucceeded = $false
    try {
        & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
            -State DISPATCHED -RouteToken $route -DeadlineAt $deadline | Out-Null
        $retrySucceeded = $true
    } catch {}
    if ($retrySucceeded) {
        throw "Terminal blocker allowed an implicit repair or duplicate dispatch"
    }

    $activeRound = Join-Path $repo `
        "docs/external-review/rounds/20260719_clean_process_access_portfolio"
    & $stateScript -Mode validate -RoundPath $activeRound | Out-Null
} finally {
    foreach ($path in @($happy, $blocked)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}

Write-Output "REVIEW_MANAGER_CONTRACT_OK"
