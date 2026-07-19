[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$heartbeatRenderer = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/render_review_heartbeat.ps1"
$readmePath = Join-Path $repo "docs/external-review/README.md"

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
$manager = $registry.review_manager
if ($registry.schema_version -ne 17 -or
    $manager.kind -ne "persistent_full_round_manager" -or
    $manager.thread_id -ne "019f716c-676f-7673-9782-f37b72f200d2" -or
    $manager.role_skill -ne ".agents/skills/hmasd-review-round/SKILL.md" -or
    $manager.routing_skill -ne ".agents/skills/hmasd-task-router/SKILL.md" -or
    $manager.route_policy -ne "resolve_live_immediately_before_each_send" -or
    ($manager.controller_messages -join '|') -ne "START_REVIEW" -or
    ($manager.manager_messages -join '|') -ne "REVIEW_COMPLETE|REVIEW_BLOCKED" -or
    $manager.git_boundary.manager_role -ne "stage_commit_push_active_round_only" -or
    $manager.git_boundary.controller_role -ne "consume_terminal_disposition_only" -or
    $manager.heartbeat.owner -ne "review_manager_session" -or
    $manager.heartbeat.target -ne "self" -or
    $manager.heartbeat.interval_minutes -ne 5 -or
    $manager.heartbeat.terminal_order -ne "archive_or_disposition_then_confirm_callback_then_delete" -or
    $manager.heartbeat.duplicate_policy -ne "same_handoff_id_is_idempotent" -or
    $manager.browser.ui_scope -ne "application_shared" -or
    $manager.browser.logical_owner -ne "review_manager" -or
    $registry.reviewers.gemini_divergent.transport -ne "review_manager_antigravity_cli" -or
    $registry.reviewers.open_divergent.transport -ne "review_manager_in_app_browser" -or
    $registry.reviewers.convergent.transport -ne "review_manager_in_app_browser") {
    throw "External Review Manager registry is inconsistent"
}
foreach ($routeEntry in @($manager, $manager.controller_return_route)) {
    if ($null -ne $routeEntry.PSObject.Properties['model'] -or
        $null -ne $routeEntry.PSObject.Properties['thinking'] -or
        $null -ne $routeEntry.PSObject.Properties['host_id']) {
        throw "External Review Manager registry must not mirror live delivery metadata"
    }
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @(
    "role_skill=.agents/skills/hmasd-review-round/SKILL.md",
    "Do not load",
    "conversation history",
    "git push My-paper-code aggressive",
    "There is no review state machine",
    "create one 5-minute heartbeat",
    "scripts/render_review_heartbeat.ps1",
    "controller never creates, updates",
    "handoff_id=<round>:complete:<pushed-disposition-commit>",
    "keep the heartbeat active",
    "delete it and verify deletion",
    'same `handoff_id`'
)) {
    if (-not $skillText.Contains($required)) {
        throw "Review Manager contract is missing: $required"
    }
}
foreach ($forbidden in @(
    "CONTINUE_REVIEW",
    "RESUME_REVIEW",
    "REVIEW_BOUNDARY_READY",
    "05_REVIEW_STATE.json",
    "pause and verify the heartbeat"
)) {
    if ($skillText.Contains($forbidden)) {
        throw "Review Manager retains obsolete controller/state lifecycle: $forbidden"
    }
}

$readme = Get-Content -LiteralPath $readmePath -Raw
foreach ($forbidden in @("CONTINUE_REVIEW", "RESUME_REVIEW", "REVIEW_BOUNDARY_READY", "05_REVIEW_STATE.json")) {
    if ($readme.Contains($forbidden)) {
        throw "External-review overview exposes obsolete manager mechanics: $forbidden"
    }
}

$round = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-review-heartbeat-" + [guid]::NewGuid().ToString("N"))
try {
    [void](New-Item -ItemType Directory -Path $round)
    Set-Content -LiteralPath (Join-Path $round "20_PRO_OPEN_QUESTION.md") -Value "QUESTION" -Encoding utf8NoBOM
    $prompt = (& $heartbeatRenderer `
        -RoundPath $round `
        -Stage OPEN_DIVERGENT `
        -QuestionPath "20_PRO_OPEN_QUESTION.md" `
        -RawPath "21_PRO_OPEN_RAW.md" `
        -HeartbeatId "review-heartbeat-test") -join [Environment]::NewLine
    foreach ($required in @(
        "hmasd-task-router",
        "hmasd-review-round",
        "REVIEWER_CONVERSATIONS.json",
        "stage=OPEN_DIVERGENT",
        "20_PRO_OPEN_QUESTION.md",
        "21_PRO_OPEN_RAW.md",
        "heartbeat_id=review-heartbeat-test")) {
        if (-not $prompt.Contains($required)) {
            throw "Rendered heartbeat is missing: $required"
        }
    }
    foreach ($forbidden in @(
        "05_REVIEW_STATE.json",
        "CURRENT_WORK.md",
        "model=",
        "thinking=",
        "hostId=",
        "threadId=")) {
        if ($prompt.Contains($forbidden)) {
            throw "Rendered heartbeat leaks unrelated context or routing: $forbidden"
        }
    }
} finally {
    if (Test-Path -LiteralPath $round) {
        Remove-Item -LiteralPath $round -Recurse -Force
    }
}

Write-Output "REVIEW_MANAGER_CONTRACT_OK"
