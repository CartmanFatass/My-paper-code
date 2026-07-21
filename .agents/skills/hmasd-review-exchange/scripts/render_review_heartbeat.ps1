[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)]
    [ValidateSet("OPEN_DIVERGENT")][string]$Stage,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [Parameter(Mandatory = $true)][string]$HeartbeatId
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
$roundId = Split-Path -Leaf $round
@"
`$hmasd-dispatch-task
`$hmasd-review-exchange

HMASD OPEN-PRO EXCHANGE HEARTBEAT
Read the current dispatcher, role directory, Exchange Skill and reviewer registry.
heartbeat_id=$HeartbeatId
round=$roundId
round_path=$round
reviewer_role=$Stage
question=$question
raw=$raw

Confirm the registered conversation and current assignment, then perform one
bounded read-only inspection using any reliable method. Preserve the owned page
while pending. Archive a stable natural response exactly and report semantic
gaps separately. Never resubmit, operate another task, or claim completion
without raw equality, controller callback proof and heartbeat-deletion proof.
"@
