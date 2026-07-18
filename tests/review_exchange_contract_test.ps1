[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$stateScript = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/review_state.ps1"
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

if ($registry.schema_version -ne 6 -or
    $registry.gemini_exchange_transport.send_tool -ne "codex_app__send_message_to_thread" -or
    $registry.gemini_exchange_transport.optional_model_fields -ne "FORBIDDEN") {
    throw "Registry does not preserve the guarded Gemini Exchange contract"
}

$geminiExchange = $registry.reviewers.gemini_divergent.codex_exchange
if ($geminiExchange.thread_id -ne "019f6e7a-8671-7463-9615-8eea2fa5d7d1" -or
    $geminiExchange.host_id -ne "local" -or
    $geminiExchange.model_frozen -ne $true) {
    throw "Gemini Exchange identity mismatch"
}

if ($registry.pro_transport.kind -ne "codex_chatgpt_control_visible_ui" -or
    $registry.pro_transport.plugin -ne "codex-chatgpt-control@codex-chatgpt-control" -or
    $registry.pro_transport.version -ne "0.5.1-alpha.1+codex.20260717041128" -or
    $registry.pro_transport.source_commit -ne "73c5737f222709e324a1c7ba1637cef9966000ce" -or
    $registry.pro_transport.skill -ne "chatgpt-delegate" -or
    $registry.pro_transport.experience -ne "chat" -or
    $registry.pro_transport.intelligence -ne "Pro") {
    throw "Registry does not pin the verified ChatGPT-control Pro transport"
}
foreach ($key in @("open_divergent", "convergent")) {
    $reviewer = $registry.reviewers.$key
    if ($reviewer.transport -ne "codex_chatgpt_control" -or
        $reviewer.url -notmatch '^https://chatgpt\.com/c/[0-9a-f-]+$' -or
        $reviewer.expected_model_ui -ne "Pro" -or
        $null -eq $reviewer.legacy_codex_exchange -or
        $null -ne $reviewer.codex_exchange) {
        throw "Active Pro transport is not direct and role-specific: $key"
    }
}

$stateText = Get-Content -LiteralPath $stateScript -Raw
foreach ($forbidden in @("subagent_transport", "Get-ExpectedSubagentSession", 'source -eq "subagent"')) {
    if ($stateText.Contains($forbidden)) {
        throw "State validator still contains review subagent transport: $forbidden"
    }
}

$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @(
    "chatgpt-delegate",
    'thread: { type: "url", url: registered.url }',
    'configuration: { intelligence: "Pro" }',
    "messages.waitAndRead",
    "source=chatgpt_control",
    "plugin:submitted",
    "plugin:completed"
)) {
    if (-not $skillText.Contains($required)) {
        throw "Skill is missing direct ChatGPT-control contract: $required"
    }
}
foreach ($forbidden in @(
    "Open Pro and Convergent Pro each have one persistent local Codex Exchange",
    "REVIEW_RELAY",
    "WAIT_PRO_THINKING"
)) {
    if ($skillText.Contains($forbidden)) {
        throw "Skill retains obsolete Pro Exchange transport: $forbidden"
    }
}

$activeRound = Join-Path $repo "docs/external-review/rounds/20260718_stage_c_skill_bottleneck_portfolio"
$state = Get-Content -LiteralPath (Join-Path $activeRound "05_REVIEW_STATE.json") -Raw | ConvertFrom-Json
if (-not ([string]$state.stages.gemini_divergent.dispatch_receipt).StartsWith("source=gemini;") -or
    -not ([string]$state.stages.open_pro.dispatch_receipt).StartsWith("source=exchange;") -or
    -not ([string]$state.stages.convergent_pro.dispatch_receipt).StartsWith("source=exchange;")) {
    throw "Active round does not exercise the retained Gemini and Exchange receipt paths"
}

$validation = & $stateScript -Mode validate -RoundPath $activeRound
if (($validation -join "`n") -notmatch "review_state=VALID") {
    throw "Active review state did not validate"
}

Write-Output "REVIEW_EXCHANGE_CONTRACT_OK"
