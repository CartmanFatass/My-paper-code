[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$EvidenceCommit,
    [Parameter(Mandatory = $true)][string]$Repository,
    [Parameter(Mandatory = $true)][string]$ReviewBranch,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
$validator = Join-Path $PSScriptRoot 'validate_browser_pro_round.ps1'
$dispatchModule = Join-Path $PSScriptRoot 'browser_pro_dispatch.psm1'
Import-Module $dispatchModule -Force

if ($StageCommit -cnotmatch '^[0-9a-f]{40}$' -or $EvidenceCommit -cnotmatch '^[0-9a-f]{40}$') {
    throw 'Browser Pro dispatch requires exact 40-character lowercase stage and evidence commits'
}
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $resolvedRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
} else {
    $resolvedRepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}

$validated = (& $validator -RoundPath $RoundPath -QuestionPath $QuestionPath `
    -ReceiptPath $ReceiptPath -RawPath $RawPath -RepoRoot $resolvedRepoRoot) | ConvertFrom-Json
if ($validated.status -cne 'READY_TO_SUBMIT') {
    throw "Browser Pro dispatch cannot be rendered from state $($validated.status)"
}

$questionFullPath = [IO.Path]::GetFullPath([string]$validated.question)
$repoPrefix = $resolvedRepoRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if (-not $questionFullPath.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Browser Pro validated question is outside RepoRoot'
}
$questionRepoRelative = $questionFullPath.Substring($repoPrefix.Length).Replace([IO.Path]::DirectorySeparatorChar, '/')
$dispatch = New-HmasdBrowserProDispatch -Repository $Repository -ReviewBranch $ReviewBranch `
    -StageCommit $StageCommit -QuestionSha256 ([string]$validated.question_sha256) `
    -QuestionPath $questionRepoRelative

[ordered]@{
    status = 'DISPATCH_READY'
    dispatch_base64 = [string]$dispatch.dispatch_base64
    dispatch_sha256 = [string]$dispatch.dispatch_sha256
    question_sha256 = [string]$validated.question_sha256
    utf16_length = [int]$dispatch.utf16_length
    byte_count = [int]$dispatch.byte_count
    question_path = [string]$dispatch.question_path
} | ConvertTo-Json -Compress
