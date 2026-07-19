[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$rolesPath = Join-Path $repo ".agents/skills/hmasd-task-router/references/session-roles.json"
$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$exchangeSkillPath = Join-Path $repo ".agents/skills/hmasd-review-exchange/SKILL.md"
$heartbeatRenderer = Join-Path $repo ".agents/skills/hmasd-review-exchange/scripts/render_review_heartbeat.ps1"
$readmePath = Join-Path $repo "docs/external-review/README.md"

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json
$manager = $registry.review_manager
if ($registry.schema_version -ne 19 -or
    $manager.kind -ne "persistent_full_round_manager" -or
    $manager.session_role_registry -ne ".agents/skills/hmasd-task-router/references/session-roles.json" -or
    ($manager.controller_messages -join '|') -ne "START_REVIEW" -or
    ($manager.manager_messages -join '|') -ne "REVIEW_COMPLETE|REVIEW_BLOCKED" -or
    $manager.exchange_messages.manager_to_exchange -ne "REVIEW_STAGE" -or
    ($manager.exchange_messages.exchange_to_manager -join '|') -ne "REVIEW_STAGE_COMPLETE|REVIEW_STAGE_BLOCKED" -or
    $manager.git_boundary.manager_role -ne "stage_commit_push_active_round_only" -or
    $manager.git_boundary.controller_role -ne "consume_terminal_disposition_only" -or
    $registry.exchange_contract.role_skill -ne ".agents/skills/hmasd-review-exchange/SKILL.md" -or
    -not $registry.exchange_contract.one_reviewer_per_session -or
    $registry.exchange_contract.controller_contact -ne "forbidden" -or
    $registry.exchange_contract.heartbeat.owner -ne "registered_reviewer_exchange_session" -or
    $registry.exchange_contract.heartbeat.target -ne "self" -or
    $registry.exchange_contract.heartbeat.interval_minutes -ne 5 -or
    $registry.exchange_contract.browser.logical_owner -ne "registered_pro_exchange" -or
    $registry.reviewers.gemini_divergent.session_role -ne "gemini_divergent_exchange" -or
    $registry.reviewers.open_divergent.session_role -ne "open_divergent_exchange" -or
    $registry.reviewers.convergent.session_role -ne "convergent_exchange" -or
    $registry.reviewers.gemini_divergent.transport -ne "reviewer_exchange_antigravity_cli" -or
    $registry.reviewers.open_divergent.transport -ne "reviewer_exchange_in_app_browser" -or
    $registry.reviewers.convergent.transport -ne "reviewer_exchange_in_app_browser") {
    throw "External Review Manager registry is inconsistent"
}
foreach ($forbidden in @('thread_id', 'role_skill', 'routing_skill', 'controller_return_route', 'route_resolver', 'route_policy', 'model', 'thinking', 'host_id', 'browser', 'heartbeat')) {
    if ($null -ne $manager.PSObject.Properties[$forbidden]) {
        throw "External Review Manager registry duplicates router-owned session data: $forbidden"
    }
}
$managerId = $roles.roles.external_review_manager.thread_id
$managerStatus = $roles.roles.external_review_manager.registration_status
if ($roles.roles.external_review_manager.role_skill -ne '.agents/skills/hmasd-review-round/SKILL.md' -or
    $roles.roles.gemini_divergent_exchange.thread_id -ne '019f76cc-580b-7c40-8c92-97bfffaf51b1' -or
    $roles.roles.open_divergent_exchange.thread_id -ne '019f716c-3c8a-7891-8c89-c94dc94fab4c' -or
    $roles.roles.convergent_exchange.thread_id -ne '019f716c-676f-7673-9782-f37b72f200d2' -or
    $roles.roles.controller.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8') {
    throw 'Review role is not bound by the common session-role directory'
}
if (($null -eq $managerId -and $managerStatus -ne 'UNASSIGNED') -or
    ($null -ne $managerId -and $managerStatus -ne 'ACTIVE')) {
    throw 'Review Manager registration state is inconsistent'
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
$normalizedSkillText = $skillText -replace '\s+', ' '
foreach ($required in @(
    "role_skill=.agents/skills/hmasd-review-round/SKILL.md",
    "Do not load",
    "conversation history",
    "session-roles.json.roles.external_review_manager.thread_id",
    "session-roles.json.roles.controller.thread_id",
    'returned `hostId`',
    "ID or model setting from the assignment",
    "git push My-paper-code aggressive",
    "There is no review state machine",
    "REVIEW_STAGE",
    "controller is never a stage recipient",
    "gemini_divergent_exchange",
    "open_divergent_exchange",
    "convergent_exchange",
    "Nonempty is not",
    "manager never creates or manages a heartbeat",
    "handoff_id=<round>:complete:<pushed-disposition-commit>",
    "REVIEW_DELIVERY_UNCONFIRMED",
    'same `handoff_id`'
)) {
    if (-not $normalizedSkillText.Contains($required)) {
        throw "Review Manager contract is missing: $required"
    }
}
foreach ($forbidden in @(
    "CONTINUE_REVIEW",
    "RESUME_REVIEW",
    "REVIEW_BOUNDARY_READY",
    "05_REVIEW_STATE.json",
    "pause and verify the heartbeat",
    "codex_app__navigate_to_codex_page",
    "Antigravity interaction",
    "create one 5-minute heartbeat"
)) {
    if ($skillText.Contains($forbidden)) {
        throw "Review Manager retains obsolete controller/state lifecycle: $forbidden"
    }
}

$exchangeText = Get-Content -LiteralPath $exchangeSkillPath -Raw
$normalizedExchangeText = $exchangeText -replace '\s+', ' '
foreach ($required in @(
    "role_skill=.agents/skills/hmasd-review-exchange/SKILL.md",
    "gemini_divergent_exchange",
    "open_divergent_exchange",
    "convergent_exchange",
    "do not contact the controller",
    "codex_app__navigate_to_codex_page",
    "ambient browser state",
    "retry that exact command once",
    "duplicate consent",
    "A second permission failure is terminal",
    "Nonempty is not",
    "exact text equality",
    "create one 5-minute heartbeat",
    "Reply to Review Manager",
    "session-roles.json.roles.external_review_manager.thread_id",
    'returned `hostId`'
)) {
    if (-not $normalizedExchangeText.Contains($required)) {
        throw "Reviewer Exchange contract is missing: $required"
    }
}
foreach ($forbidden in @("REVIEW_COMPLETE", "REVIEW_BLOCKED", "session-roles.json.roles.controller.thread_id")) {
    if ($exchangeText.Contains($forbidden)) {
        throw "Reviewer Exchange bypasses the manager: $forbidden"
    }
}

$readme = Get-Content -LiteralPath $readmePath -Raw
$normalizedReadme = $readme -replace '\s+', ' '
foreach ($required in @("nonempty alone is not completion", "exact captured-text equality")) {
    if (-not $normalizedReadme.Contains($required)) {
        throw "External-review overview is missing raw acceptance: $required"
    }
}
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
        "session-roles.json",
        "hmasd-review-exchange",
        "REVIEWER_CONVERSATIONS.json",
        "reviewer_role=OPEN_DIVERGENT",
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
