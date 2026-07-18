[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$registryPath = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$stateScript = Join-Path $repo ".agents/skills/hmasd-review-round/scripts/review_state.ps1"
$registry = Get-Content -LiteralPath $registryPath -Raw | ConvertFrom-Json

if ($registry.schema_version -ne 5 -or
    $registry.exchange_transport.send_tool -ne "codex_app__send_message_to_thread" -or
    $registry.exchange_transport.optional_model_fields -ne "FORBIDDEN") {
    throw "Registry does not enforce the no-model-override send contract"
}

$roles = @(
    @{ key = "gemini_divergent"; thread = "019f6e7a-8671-7463-9615-8eea2fa5d7d1" },
    @{ key = "open_divergent"; thread = "019f716c-3c8a-7891-8c89-c94dc94fab4c" },
    @{ key = "convergent"; thread = "019f716c-676f-7673-9782-f37b72f200d2" }
)
$threadIds = @()
foreach ($role in $roles) {
    $exchange = $registry.reviewers.($role.key).codex_exchange
    if ($exchange.thread_id -ne $role.thread -or
        $exchange.host_id -ne "local" -or
        $exchange.model_frozen -ne $true) {
        throw "Exchange identity mismatch: $($role.key)"
    }
    $threadIds += [string]$exchange.thread_id
}
if (@($threadIds | Sort-Object -Unique).Count -ne $roles.Count) {
    throw "Each reviewer must have a distinct Exchange task"
}

$stateText = Get-Content -LiteralPath $stateScript -Raw
foreach ($forbidden in @("subagent_transport", "Get-ExpectedSubagentSession", 'source -eq "subagent"')) {
    if ($stateText.Contains($forbidden)) {
        throw "State validator still contains review subagent transport: $forbidden"
    }
}

$skillPath = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$skillText = Get-Content -LiteralPath $skillPath -Raw
$sendExamples = [regex]::Matches(
    $skillText,
    '(?s)await tools\.codex_app__send_message_to_thread\(\{.*?\}\)'
)
if ($sendExamples.Count -ne 2) {
    throw "Skill must contain exactly two guarded direct-message examples"
}
foreach ($example in $sendExamples) {
    if ($example.Value -match '(?m)^\s*(model|thinking)\s*:') {
        throw "Direct-message example contains a model override field"
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
