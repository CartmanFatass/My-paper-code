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
if ($registry.schema_version -ne 22 -or
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
    $registry.exchange_contract.browser.access_policy -ne 'operate_only_registered_conversation_and_avoid_unnecessary_duplicates_or_reloads' -or
    $registry.exchange_contract.browser.waiting_policy -ne 'preserve_registered_page_for_next_wake' -or
    $registry.exchange_contract.browser.terminal_policy -ne 'release_page_after_raw_callback_and_heartbeat_cleanup' -or
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
    '$hmasd-task-router',
    '$hmasd-review-exchange',
    '$hmasd-project-manager',
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
    'observed error as `recovery_context`',
    'Do not prescribe selectors, browser commands, click sequences, shell recipes',
    'same Exchange',
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
    "completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY",
    '$hmasd-task-router',
    '$hmasd-review-exchange',
    'recovery_context=<optional prior error evidence or none>',
    "gemini_divergent_exchange",
    "open_divergent_exchange",
    "convergent_exchange",
    "Contact only the controller",
    "CURRENT_REVIEW_ASSIGNMENT",
    "Ignore every earlier round, SHA and question path in this conversation",
    "Do not append generic full-round requests",
    "require the visible user turn to contain the exact current",
    "inspected a different commit or question path",
    "control only this Exchange session's registered reviewer conversation",
    "How the page is found, claimed, inspected, released between wakes and recovered is model judgment",
    "Never use an unrelated ambient page",
    "Diagnose and recover transport problems inside that registered state and evidence boundary",
    "duplicate consent",
    "--dangerously-skip-permissions",
    "user's standing approval",
    "Write every naturally completed response to the assigned raw",
    "exact text equality",
    "Never discard completed evidence",
    "semantic quality note",
    "COMPLETE_WITH_GAPS",
    "For Gemini recovery, compare an existing raw",
    "keep identity strict and inspection flexible",
    "whatever read-only evidence is reliable on the live surface",
    "A stale locator, DOM ambiguity or layout change is not evidence",
    "send the completion callback without resubmitting or overwriting it",
    "a compacted-context summary",
    "Terminal evidence rule",
    "tool-level facts",
    "Text saying that a callback or deletion happened is never evidence",
    'rather than heading-string equality, regular expressions',
    "current page evidence supports continued generation or changing output",
    "stable completed answer",
    "not ordinary deferred thinking, content quality",
    'assignment interface is narrow; transport and page inspection are wide',
    'do not require the controller to supply selectors, browser commands or Antigravity steps',
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
    'invalid scientific-principle binding',
    'Question does not contain any exact repository evidence paths.'
)) {
    if (-not $verifierText.Contains($required)) {
        throw "Review-boundary verifier is missing: $required"
    }
}
if ($verifierText.Contains('Repository files to inspect section')) {
    throw 'Review-boundary verifier still requires one literal evidence heading'
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
    'Every naturally completed response is preserved',
    'A content gap is not a transport failure',
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
    $normalizedPrompt = $prompt -replace '\s+', ' '
    foreach ($required in @(
        '$hmasd-task-router',
        '$hmasd-review-exchange',
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
        if (-not $normalizedPrompt.Contains($required)) {
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
        if ($normalizedPrompt.Contains($forbidden)) {
            throw "Rendered heartbeat leaks unrelated context or routing: $forbidden"
        }
    }
    foreach ($required in @(
        "Reread both explicitly invoked Skills",
        "choose any reliable",
        "read-only inspection method",
        "Diagnose and adapt",
        "Archive every stable naturally completed response exactly",
        "COMPLETE_WITH_GAPS",
        "never convert a content gap into a transport BLOCKED result",
        "preserve the owned page for the next wake",
        "heartbeat ownership and terminal cleanup")) {
        if (-not $normalizedPrompt.Contains($required)) {
            throw "Rendered heartbeat lacks stable browser lifecycle: $required"
        }
    }
} finally {
    if (Test-Path -LiteralPath $round) {
        Remove-Item -LiteralPath $round -Recurse -Force
    }
}

Write-Output "REVIEW_DIRECT_EXCHANGE_CONTRACT_OK"
