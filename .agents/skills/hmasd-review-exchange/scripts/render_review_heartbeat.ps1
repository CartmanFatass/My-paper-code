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
response and end. Never load controller or manager context, operate another
reviewer, or resubmit an accepted prompt. Follow the exchange Skill for raw
validation, manager callback, and heartbeat deletion.
"@
