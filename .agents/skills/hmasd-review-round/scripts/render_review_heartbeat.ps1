[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RoundPath,

    [Parameter(Mandatory = $true)]
    [ValidateSet("GEMINI_DIVERGENT", "OPEN_DIVERGENT", "CONVERGENT", "CALLBACK_ONLY")]
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
if ($Stage -ne "CALLBACK_ONLY" -and
    -not (Test-Path -LiteralPath $question -PathType Leaf)) {
    throw "Missing review question: $question"
}

$repo = (Resolve-Path (Join-Path $PSScriptRoot "../../../..")).Path
$router = Join-Path $repo ".agents/skills/hmasd-task-router/SKILL.md"
$review = Join-Path $repo ".agents/skills/hmasd-review-round/SKILL.md"
$registry = Join-Path $repo "docs/external-review/REVIEWER_CONVERSATIONS.json"
$roundId = Split-Path -Leaf $round

@"
HMASD EXTERNAL REVIEW HEARTBEAT

Read the current working-tree versions of:
$router
$review
$registry

heartbeat_id=$HeartbeatId
round=$roundId
round_path=$round
stage=$Stage
question=$question
raw=$raw

Perform one bounded External Review Manager inspection for this stage and end.
Never load controller context, infer routing from prior turns, or resubmit an
accepted prompt. Follow the role Skill for byte-exact archival, callback, and
heartbeat deletion.
"@
