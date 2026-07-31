[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)]
    [ValidateSet("OPEN_DIVERGENT")][string]$Stage,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')][string]$StageCommit,
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

$roundId = Split-Path -Leaf $round
@"
`$hmasd-review-round
claude-in-chrome

HMASD PROJECT-MANAGER-DIRECT PRO REVIEW HEARTBEAT
This wake belongs to the active Project Manager. Read the current review Skill and
reviewer registry, then inspect the registered conversation once.
heartbeat_id=$HeartbeatId
round=$roundId
round_path=$round
reviewer_role=$Stage
stage_commit=$StageCommit
question=$question
raw=$raw

Never submit or resubmit from a heartbeat. If the matching response is pending,
leave this single heartbeat active. A home-page redirect triggers registered
conversation discovery, not blocking. Identify the assistant message after the
matching fence and use two stable text snapshots plus generation-control state;
a Thinking label alone is not pending, while an active Stop answering control is.
If a completed message explicitly reports missing question-listed evidence,
treat it as a transport diagnostic and do not archive it as scientific raw.
Leave the round active for Project Manager evidence-access recovery under the same
fence. If the response is naturally complete and is not a transport diagnostic,
archive it as the active Project Manager: verify stable completion per the review
Skill, run archive_pro_response.ps1 yourself, then delete this
heartbeat and confirm absence, then reconcile the exact raw. Deciding that a response is the
completed answer is the judgment that once archived a mid-generation thinking
trace as scientific raw, so it is never delegable; capture may be delegated only
under the digest bond the Skill defines, and the child writes nothing into the
round directory.
Do not interpret scientific completeness, repair the package,
authorize code, or start compute.
"@
