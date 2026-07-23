[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
} else {
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}
if ([IO.Path]::GetFileName($QuestionPath) -ne $QuestionPath -or
    [IO.Path]::GetFileName($RawPath) -ne $RawPath -or
    $QuestionPath -ne '20_PRO_OPEN_QUESTION.md' -or
    $RawPath -ne '21_PRO_OPEN_RAW.md') {
    throw 'Browser Pro question/raw must be the canonical round basenames'
}
$roundCandidate = if ([IO.Path]::IsPathRooted($RoundPath)) {
    $RoundPath
} else {
    Join-Path $RepoRoot $RoundPath
}
$round = (Resolve-Path -LiteralPath $roundCandidate).Path
$reviewRoot = (Resolve-Path -LiteralPath (Join-Path $RepoRoot 'docs/external-review/rounds')).Path
$reviewPrefix = $reviewRoot + [IO.Path]::DirectorySeparatorChar
if (-not $round.StartsWith($reviewPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Browser Pro round escapes review root: $round"
}
$manifest = [IO.Path]::GetFullPath((Join-Path $round '01_SHARED_SOURCE_MANIFEST.md'))
$question = [IO.Path]::GetFullPath((Join-Path $round $QuestionPath))
$raw = [IO.Path]::GetFullPath((Join-Path $round $RawPath))
$roundPrefix = $round + [IO.Path]::DirectorySeparatorChar
foreach ($path in @($manifest, $question, $raw)) {
    if (-not $path.StartsWith($roundPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Browser Pro path escapes round directory: $path"
    }
}
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw "Missing Browser Pro source manifest: $manifest"
}
if (-not (Test-Path -LiteralPath $question -PathType Leaf)) {
    throw "Missing Browser Pro question: $question"
}
if (Test-Path -LiteralPath $raw) {
    throw "Browser Pro raw already exists and is immutable: $raw"
}
[ordered]@{
    round = $round
    source_manifest = $manifest
    question = $question
    raw = $raw
} | ConvertTo-Json -Compress
