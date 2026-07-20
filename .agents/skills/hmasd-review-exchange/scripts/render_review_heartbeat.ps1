[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RoundPath,

    [Parameter(Mandatory = $true)]
    [ValidateSet("GEMINI_DIVERGENT", "OPEN_DIVERGENT", "CONVERGENT")]
    [string]$Stage,

    [Parameter(Mandatory = $true)]
    [string]$QuestionPath,

    [Parameter(Mandatory = $true)]
    [string]$RawPath,

    [Parameter(Mandatory = $true)]
    [string]$HeartbeatId
)

$ErrorActionPreference = "Stop"
$round = (Resolve-Path -LiteralPath $RoundPath).Path
$question = [IO.Path]::GetFullPath((Join-Path $round $QuestionPath))
$raw = [IO.Path]::GetFullPath((Join-Path $round $RawPath))
$prefix = $round + [IO.Path]::DirectorySeparatorChar
foreach ($path in @($question, $raw)) {
    if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Heartbeat path escapes round directory: $path"
    }
}
if (-not (Test-Path -LiteralPath $question -PathType Leaf)) {
    throw "Missing review question: $question"
}

$repo = (Resolve-Path (Join-Path $PSScriptRoot "../../../..")).Path
$router = Join-Path $repo ".agents/skills/hmasd-task-router/SKILL.md"
$roles = Join-Path $repo ".agents/skills/hmasd-task-router/references/session-roles.json"
$exchange = Join-Path $repo ".agents/skills/hmasd-review-exchange/SKILL.md"
$registry = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$roundId = Split-Path -Leaf $round

@"
HMASD REVIEWER EXCHANGE HEARTBEAT

Read the current working-tree versions of:
$router
$roles
$exchange
$registry

heartbeat_id=$HeartbeatId
round=$roundId
round_path=$round
reviewer_role=$Stage
question=$question
raw=$raw

Perform one bounded inspection of this exchange session's registered external
response. Reuse a matching controlled tab or claim the exact registered page
from browser.user.openTabs(); never create a duplicate when that page exists.
Scope completion and control detection to the exact assigned user turn and its
following assistant response. Ignore matching buttons in historical turns or
other page regions; a current completed response's regenerate control is not a
thinking signal. Use robust current-turn message-role scoping rather than page
position assumptions. WAIT is legal only for a current generation indicator or
changing text.

Archive every stable naturally completed response exactly. Then use semantic
judgment to return COMPLETE or COMPLETE_WITH_GAPS with a concise quality note.
Do not implement heading, regular-expression or field-presence gates in page
code, and never convert a content gap into a transport BLOCKED result.
While Pro is thinking, preserve it by making browser.tabs.finalize({ keep })
with status handoff the final browser action of this wake. Recover the page by
opening it only if neither controlled nor user tabs contain the registered URL.
Never load controller context, operate another reviewer, or resubmit an
accepted prompt. Follow the exchange Skill for raw archival and controller callback,
heartbeat deletion, handoff preservation, and the single terminal page close.
Prior-turn text and compacted context are not terminal evidence. Never claim callback or
deletion unless the current stage has its assigned raw and the current wake
obtains the required send-message and automation-delete tool confirmations. If
any confirmation is missing, leave this exact heartbeat active and make no
terminal claim.
"@
