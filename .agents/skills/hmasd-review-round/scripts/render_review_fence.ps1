[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Assignment', 'FullHashCorrection', 'ResponseRetry')]
    [string]$Mode,

    [Parameter(Mandatory = $true)][string]$Round,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$Question,
    [string]$SupersedesStageCommit,
    [ValidateSet('format_nonconforming', 'no_response_after_exhausted_recovery')]
    [string]$RetryReason
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$Repository = 'CartmanFatass/My-paper-code'
$Branch = 'aggressive'

function Require-SingleLine([string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match "[\r\n]") {
        throw "$Name must be one nonempty line."
    }
}

foreach ($field in @{
    Round = $Round
    Question = $Question
}.GetEnumerator()) {
    Require-SingleLine $field.Key $field.Value
}

if ($StageCommit -cnotmatch '^[0-9a-f]{40}$') {
    throw 'StageCommit must be exactly 40 lowercase hexadecimal characters.'
}

$instruction = 'Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.'
$identity = @(
    "repository=$Repository"
    "branch=$Branch"
    "round=$Round"
    "stage_commit=$StageCommit"
    "question=$Question"
    "instruction=$instruction"
)

if ($Mode -eq 'Assignment') {
    if (-not [string]::IsNullOrEmpty($SupersedesStageCommit) -or
        -not [string]::IsNullOrEmpty($RetryReason)) {
        throw 'Assignment mode accepts no correction or retry parameters.'
    }
    Write-Output (@('CURRENT_REVIEW_ASSIGNMENT') + $identity -join "`n")
    return
}

if ($Mode -eq 'ResponseRetry') {
    if (-not [string]::IsNullOrEmpty($SupersedesStageCommit)) {
        throw 'SupersedesStageCommit is valid only in FullHashCorrection mode.'
    }
    if ([string]::IsNullOrEmpty($RetryReason)) {
        throw 'RetryReason is required in ResponseRetry mode.'
    }
    $retry = @('CURRENT_REVIEW_ASSIGNMENT') + $identity + @(
        ''
        'CURRENT_REVIEW_RESPONSE_RETRY'
        'submission_attempt=2'
        'supersedes_submission_attempt=1'
        "retry_reason=$RetryReason"
        'RESPONSE_REQUIREMENTS'
        '1. Answer the unchanged question completely.'
        '2. Use every required heading, field, disposition token and section exactly as specified by the question.'
        '3. Do not omit a required item; if it cannot be determined, mark that item UNDETERMINED and state its blocker.'
        '4. Do not return only transport, status or acknowledgement text.'
    )
    Write-Output ($retry -join "`n")
    return
}

if (-not [string]::IsNullOrEmpty($RetryReason)) {
    throw 'RetryReason is valid only in ResponseRetry mode.'
}

Require-SingleLine 'SupersedesStageCommit' $SupersedesStageCommit
if ($SupersedesStageCommit -cnotmatch '^[0-9a-f]{7,39}$') {
    throw 'SupersedesStageCommit must be a 7-39 character lowercase hexadecimal prefix.'
}
if (-not $StageCommit.StartsWith($SupersedesStageCommit, [StringComparison]::Ordinal)) {
    throw 'SupersedesStageCommit is not a strict prefix of StageCommit.'
}

$correction = @(
    'CURRENT_REVIEW_FENCE_CORRECTION'
    "supersedes_stage_commit=$SupersedesStageCommit"
) + $identity + @(
    'correction_scope=stage_commit_prefix_expansion_only; scientific question, evidence allow-list, and scientific instruction are unchanged and are not resubmitted.'
)
Write-Output ($correction -join "`n")
