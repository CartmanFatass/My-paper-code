[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$stateScript = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/review_state.ps1"

$registryText = Get-Content -LiteralPath $registryPath -Raw
$registry = $registryText | ConvertFrom-Json
if ($registry.schema_version -ne 12 -or
    $registry.gemini_transport.kind -ne "one_shot_subagent_antigravity_cli" -or
    $registry.gemini_transport.subagent_model -ne "gpt-5.6-terra" -or
    $registry.gemini_transport.reasoning_effort -ne "medium" -or
    $registry.gemini_transport.handoff -ne "single_line_document_pointer" -or
    -not $registry.gemini_transport.state_write_scope.Contains("last_conversations.json") -or
    -not $registry.gemini_transport.state_write_scope.Contains("log and crashes") -or
    $registry.pro_transport.kind -ne "single_luna_exchange_multi_page_in_app_browser" -or
    $registry.pro_transport.dispatch_tool -ne "codex_app__send_message_to_thread" -or
    $registry.pro_transport.routing_skill -ne ".agents/skills/hmasd-task-router/SKILL.md" -or
    $registry.pro_transport.route_resolver -ne ".agents/skills/hmasd-task-router/scripts/resolve_task_route.ps1" -or
    $registry.pro_transport.target_route_fields -ne "REQUIRED_EXACT_REGISTERED_VALUES" -or
    $registry.pro_transport.codex_exchange.thread_id -ne "019f716c-676f-7673-9782-f37b72f200d2" -or
    $registry.pro_transport.codex_exchange.model -ne "gpt-5.6-luna" -or
    $registry.pro_transport.codex_exchange.thinking -ne "high" -or
    $registry.reviewers.open_divergent.transport -ne "shared_luna_exchange_in_app_browser" -or
    $registry.reviewers.open_divergent.codex_exchange_ref -ne "pro_transport.codex_exchange" -or
    $registry.reviewers.convergent.transport -ne "shared_luna_exchange_in_app_browser" -or
    $registry.reviewers.convergent.codex_exchange_ref -ne "pro_transport.codex_exchange" -or
    $registry.pro_transport.controller_return_route.thread_id -ne "019f5c78-0c91-7612-adb4-c1fcfe4484c8" -or
    $registry.pro_transport.controller_return_route.model -ne "gpt-5.6-sol" -or
    $registry.pro_transport.controller_return_route.thinking -ne "xhigh") {
    throw "Registry is not the current review transport contract"
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @("one registered Luna Exchange", "two role-specific browser URLs", "Codex in-app browser", "schema 5", "dispatched exactly once", "BLOCKED_TIMEOUT", "gpt-5.6-terra", "single-line document pointer", "last_conversations.json", "runtime-output directories", "empty current-session tab list is normal", "creates a fresh in-app-browser tab", "active-thinking control", "repair_incomplete", "../hmasd-task-router/SKILL.md", "freshly resolved controller route", "30_EVIDENCE_RECONCILIATION.md", "one selected next evidence source or an explicit stop")) {
    if (-not $skillText.Contains($required)) {
        throw "Review Skill is missing current contract: $required"
    }
}

$stateText = Get-Content -LiteralPath $stateScript -Raw
foreach ($required in @("schema_version = 5", "dispatch_count", "deadline_at", "evidence_reconciliation", "repair_incomplete")) {
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
$repair = New-Round
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
        -State BLOCKED -Blocker "PRE_DISPATCH_BOUNDARY" | Out-Null
    & $stateScript -Mode transition -RoundPath $blocked -Stage gemini_divergent `
        -State BLOCKED -Blocker "PRE_DISPATCH_BOUNDARY_UPDATED" | Out-Null
    $preDispatchState = Get-Content -LiteralPath (Join-Path $blocked "05_REVIEW_STATE.json") -Raw | ConvertFrom-Json
    if ($preDispatchState.stages.gemini_divergent.dispatch_count -ne 0 -or
        $preDispatchState.stages.gemini_divergent.blocker -ne "PRE_DISPATCH_BOUNDARY_UPDATED") {
        throw "Pre-dispatch blocker could not be updated without consuming dispatch"
    }
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

    Complete-External $repair "gemini_divergent" "GEMINI_DIVERGENT" "11_GEMINI_DIVERGENT_RAW.md"
    Complete-External $repair "open_pro" "OPEN_DIVERGENT" "21_PRO_OPEN_RAW.md"
    Set-Content -LiteralPath (Join-Path $repair "30_EVIDENCE_RECONCILIATION.md") `
        -Value "PREMATURE" -Encoding utf8NoBOM
    & $stateScript -Mode transition -RoundPath $repair -Stage evidence_reconciliation `
        -State COMPLETE | Out-Null
    $beforeRepair = Get-Content -LiteralPath (Join-Path $repair "05_REVIEW_STATE.json") `
        -Raw | ConvertFrom-Json
    $openRoute = $beforeRepair.stages.open_pro.route_token
    & $stateScript -Mode repair_incomplete -RoundPath $repair -Stage open_pro `
        -Blocker "ACTIVE_THINKING_CONTROL_PRESENT" | Out-Null
    $afterRepair = Get-Content -LiteralPath (Join-Path $repair "05_REVIEW_STATE.json") `
        -Raw | ConvertFrom-Json
    if ($afterRepair.stages.open_pro.state -ne "DISPATCHED" -or
        $afterRepair.stages.open_pro.dispatch_count -ne 1 -or
        $afterRepair.stages.open_pro.route_token -ne $openRoute -or
        $afterRepair.stages.evidence_reconciliation.state -ne "NOT_STARTED" -or
        $afterRepair.stages.convergent_pro.dispatch_count -ne 0) {
        throw "Incomplete raw repair changed dispatch identity or retained downstream state"
    }
} finally {
    foreach ($path in @($happy, $blocked, $repair)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}

Write-Output "REVIEW_ROUND_CONTRACT_OK"
