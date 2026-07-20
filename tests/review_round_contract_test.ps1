[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$registryPath = Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-task-router/references/session-roles.json'
$skillPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$exchangeSkillPath = Join-Path $repo '.agents/skills/hmasd-review-exchange/SKILL.md'
$heartbeatRenderer = Join-Path $repo '.agents/skills/hmasd-review-exchange/scripts/render_review_heartbeat.ps1'
$geminiInvoker = Join-Path $repo 'scripts/invoke_gemini_reviewer.ps1'
$geminiLive = Join-Path $repo 'scripts/start_gemini_reviewer_live.ps1'
$readmePath = Join-Path $repo 'docs/external-review/README.md'
$openPrinciplesPath = Join-Path $repo 'docs/external-review/OPEN_REVIEW_PRINCIPLES.md'
$convergentPrinciplesPath = Join-Path $repo 'docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md'
$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'

$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json
$roundController = $registry.round_controller
if ($registry.schema_version -ne 21 -or
    $roundController.kind -ne 'active_controller_direct_exchange' -or
    $roundController.session_role_registry -ne '.agents/skills/hmasd-task-router/references/session-roles.json' -or
    $roundController.exchange_messages.controller_to_exchange -ne 'REVIEW_STAGE' -or
    ($roundController.exchange_messages.exchange_to_controller -join '|') -ne 'REVIEW_STAGE_COMPLETE|REVIEW_STAGE_BLOCKED' -or
    $roundController.git_boundary.controller_role -ne 'inspect_commit_push_before_each_downstream_dispatch' -or
    $registry.exchange_contract.role_skill -ne '.agents/skills/hmasd-review-exchange/SKILL.md' -or
    -not $registry.exchange_contract.one_reviewer_per_session -or
    $registry.exchange_contract.controller_contact -ne 'required_terminal_callback' -or
    $registry.exchange_contract.heartbeat.owner -ne 'registered_reviewer_exchange_session' -or
    $registry.exchange_contract.heartbeat.target -ne 'self' -or
    $registry.exchange_contract.heartbeat.interval_minutes -ne 5 -or
    $registry.exchange_contract.browser.logical_owner -ne 'registered_pro_exchange' -or
    $registry.exchange_contract.browser.foreground_policy -ne 'reuse_controlled_or_claim_registered_user_tab' -or
    $registry.exchange_contract.browser.waiting_policy -ne 'finalize_keep_handoff_without_reload_or_duplicate' -or
    $registry.exchange_contract.browser.terminal_policy -ne 'close_once_after_raw_callback_and_heartbeat_cleanup' -or
    $registry.reviewers.gemini_divergent.session_role -ne 'gemini_divergent_exchange' -or
    $registry.reviewers.open_divergent.session_role -ne 'open_divergent_exchange' -or
    $registry.reviewers.convergent.session_role -ne 'convergent_exchange') {
    throw 'Direct external-review registry is inconsistent'
}
if ($null -ne $registry.PSObject.Properties['review_manager'] -or
    $null -ne $roles.roles.PSObject.Properties['external_review_manager']) {
    throw 'External Review Manager topology remains registered'
}
if ($roles.roles.gemini_divergent_exchange.thread_id -ne '019f76cc-580b-7c40-8c92-97bfffaf51b1' -or
    $roles.roles.open_divergent_exchange.thread_id -ne '019f716c-3c8a-7891-8c89-c94dc94fab4c' -or
    $roles.roles.convergent_exchange.thread_id -ne '019f716c-676f-7673-9782-f37b72f200d2' -or
    $roles.roles.controller.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8') {
    throw 'Direct review tasks are not bound by the common session-role directory'
}

$skillText = Get-Content -LiteralPath $skillPath -Raw
$normalizedSkillText = $skillText -replace '\s+', ' '
foreach ($required in @(
    'This is a controller workflow, not a persistent-session role',
    'controller owns round files',
    'Direct Exchange Procedure',
    'REVIEW_STAGE',
    'gemini_divergent_exchange',
    'open_divergent_exchange',
    'convergent_exchange',
    'copy its live `hostId`, `threadId`, `model`, and `thinking` unchanged',
    'There is no review state machine and no controller heartbeat',
    'OPEN_REVIEW_PRINCIPLES.md',
    'CONVERGENT_REVIEW_PRINCIPLES.md',
    'Open questions request a plural portfolio',
    'Focused Convergent Follow-up',
    'dispatch only the registered `convergent_exchange`',
    'Do not create divergent questions, dispatch Gemini or Open Pro',
    'not a new full external-review round',
    '50_DISPOSITION.md'
)) {
    if (-not $normalizedSkillText.Contains($required)) {
        throw "Controller review contract is missing: $required"
    }
}
foreach ($forbidden in @(
    'REVIEW_GIT_PUSH_REQUIRED',
    'START_REVIEW',
    'external_review_manager',
    'REVIEW_DELIVERY_UNCONFIRMED'
)) {
    if ($skillText.Contains($forbidden)) {
        throw "Controller review contract retains manager lifecycle: $forbidden"
    }
}

$exchangeText = Get-Content -LiteralPath $exchangeSkillPath -Raw
$normalizedExchangeText = $exchangeText -replace '\s+', ' '
foreach ($required in @(
    "role_skill=.agents/skills/hmasd-review-exchange/SKILL.md",
    "gemini_divergent_exchange",
    "open_divergent_exchange",
    "convergent_exchange",
    "Contact only the controller",
    "codex_app__navigate_to_codex_page",
    "Keep that owned page open for the whole assigned stage",
    "browser.user.openTabs()",
    "browser.user.claimTab",
    "Do not create a duplicate tab",
    "browser.tabs.finalize({ keep:",
    'status: "handoff"',
    "final browser action",
    "only normal close point for the stage",
    "ambient browser state",
    "retry that exact command once",
    "duplicate consent",
    "A second transport failure is terminal",
    "--dangerously-skip-permissions",
    "user's explicit standing approval",
    "Nonempty is not",
    "exact text equality",
    'question at the assigned `stage_commit`',
    "never add a field from conversation memory",
    "For Gemini recovery, validate an existing raw against the current pinned",
    "send the completion callback without resubmitting or overwriting it",
    "existing raw does not satisfy it",
    "a compacted-context summary",
    "Terminal evidence rule",
    "codex_app__send_message_to_thread",
    "codex_app__automation_update",
    "Text saying that a callback or deletion happened is never evidence",
    'current assigned turn only',
    'Never scan all page buttons',
    'current-turn `停止回答` or deferred `立即回答`',
    '`重新生成` on a stable completed current response is a completion affordance',
    'Do not decide from controls alone',
    '`[data-message-author-role="user"]`',
    '`[data-message-author-role="assistant"]`',
    'ChatGPT page sections are not a stable one-message-per-section contract',
    "waiting state, never a transport failure",
    "not for ordinary deferred Pro thinking",
    "OPEN_REVIEW_PRINCIPLES.md",
    "CONVERGENT_REVIEW_PRINCIPLES.md",
    "Reject an open question that lists the convergent principle",
    "create one 5-minute heartbeat",
    "Reply to Controller",
    "session-roles.json.roles.controller.thread_id",
    "REVIEW_STAGE_COMPLETE",
    "REVIEW_STAGE_BLOCKED"
)) {
    if (-not $normalizedExchangeText.Contains($required)) {
        throw "Reviewer Exchange contract is missing: $required"
    }
}

$openPrinciples = Get-Content -LiteralPath $openPrinciplesPath -Raw
$convergentPrinciples = Get-Content -LiteralPath $convergentPrinciplesPath -Raw
$normalizedOpenPrinciples = $openPrinciples -replace '\s+', ' '
$normalizedConvergentPrinciples = $convergentPrinciples -replace '\s+', ' '
foreach ($required in @(
    'Expand and stress-test the scientific portfolio',
    'Do not choose a unique successor',
    'two to four structurally distinct causal explanations',
    'unselected-ideas section'
)) {
    if (-not $normalizedOpenPrinciples.Contains($required)) {
        throw "Open-review principles are missing: $required"
    }
}
foreach ($required in @(
    'Own the scientific decision pressure',
    'One serialized implementation or experiment is not the same as one legal hypothesis',
    'select the smallest next evidence source or an explicit stop',
    'valuable unselected ideas'
)) {
    if (-not $normalizedConvergentPrinciples.Contains($required)) {
        throw "Convergent-review principles are missing: $required"
    }
}
if ($normalizedOpenPrinciples.Contains('Own the scientific decision pressure') -or
    $normalizedConvergentPrinciples.Contains('Do not choose a unique successor')) {
    throw 'Open and convergent scientific responsibilities are conflated'
}

$verifierText = Get-Content -LiteralPath $boundaryVerifier -Raw
foreach ($required in @(
    'docs/project/ALGORITHM_PRINCIPLES.md',
    'docs/external-review/OPEN_REVIEW_PRINCIPLES.md',
    'docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md',
    'invalid scientific-principle binding'
)) {
    if (-not $verifierText.Contains($required)) {
        throw "Review-boundary verifier is missing: $required"
    }
}

foreach ($path in @($geminiInvoker, $geminiLive)) {
    $text = Get-Content -LiteralPath $path -Raw
    foreach ($required in @('--mode', 'plan', '--sandbox', '--dangerously-skip-permissions')) {
        if (-not $text.Contains($required)) {
            throw "Gemini transport lacks permanently approved headless permissions: $path $required"
        }
    }
}
foreach ($forbidden in @('external_review_manager', 'REVIEW_GIT_PUSH_REQUIRED', 'REVIEW_COMPLETE')) {
    if ($exchangeText.Contains($forbidden)) {
        throw "Reviewer Exchange retains manager lifecycle: $forbidden"
    }
}

$readme = Get-Content -LiteralPath $readmePath -Raw
$normalizedReadme = $readme -replace '\s+', ' '
foreach ($required in @(
    'controller owns round sequencing',
    'return `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED` directly to the controller',
    'nonempty alone is not completion',
    'The workflow uses no intermediate persistent session'
    'OPEN_REVIEW_PRINCIPLES.md'
    'CONVERGENT_REVIEW_PRINCIPLES.md'
)) {
    if (-not $normalizedReadme.Contains($required)) {
        throw "External-review overview is missing: $required"
    }
}
foreach ($forbidden in @('REVIEW_GIT_PUSH_REQUIRED', 'START_REVIEW', 'role=external_review_manager')) {
    if ($readme.Contains($forbidden)) {
        throw "External-review overview exposes manager mechanics: $forbidden"
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
        "heartbeat_id=review-heartbeat-test",
        "controller callback",
        "Prior-turn text",
        "send-message and automation-delete tool confirmations")) {
        if (-not $prompt.Contains($required)) {
            throw "Rendered heartbeat is missing: $required"
        }
    }
    foreach ($forbidden in @(
        "manager callback",
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
    foreach ($required in @(
        "claim the exact registered page",
        "never create a duplicate",
        "Scope completion and control detection to the exact assigned user turn",
        "regenerate control is not a thinking signal",
        "data-message-author-role user/assistant containers",
        "never infer the reply with section index plus one",
        "browser.tabs.finalize({ keep })",
        "status handoff",
        "single terminal page close")) {
        if (-not $prompt.Contains($required)) {
            throw "Rendered heartbeat lacks stable browser lifecycle: $required"
        }
    }
} finally {
    if (Test-Path -LiteralPath $round) {
        Remove-Item -LiteralPath $round -Recurse -Force
    }
}

Write-Output "REVIEW_DIRECT_EXCHANGE_CONTRACT_OK"
