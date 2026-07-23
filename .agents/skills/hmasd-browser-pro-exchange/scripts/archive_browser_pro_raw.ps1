[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [Parameter(Mandatory = $true)][string]$Content,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
} else {
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}
if ([string]::IsNullOrWhiteSpace($Content)) {
    throw 'Browser Pro raw content must contain a natural non-whitespace response'
}
if ([IO.Path]::GetFileName($RawPath) -ne $RawPath -or
    $RawPath -ne '21_PRO_OPEN_RAW.md') {
    throw 'Browser Pro raw must be the canonical round basename'
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
$raw = [IO.Path]::GetFullPath((Join-Path $round $RawPath))
$roundPrefix = $round + [IO.Path]::DirectorySeparatorChar
if (-not $raw.StartsWith($roundPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Browser Pro raw escapes round directory: $raw"
}

$encoding = [Text.UTF8Encoding]::new($false)
$temp = Join-Path $round (".$RawPath." + [Guid]::NewGuid().ToString('N') + '.tmp')
$stream = $null
$writer = $null
try {
    if (Test-Path -LiteralPath $raw) {
        throw [IO.IOException]::new("Final raw already exists: $raw")
    }
    $stream = [IO.FileStream]::new($temp, [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write, [IO.FileShare]::None)
    $writer = [IO.StreamWriter]::new($stream, $encoding)
    $writer.Write($Content)
    $writer.Flush()
    $stream.Flush($true)
    $writer.Dispose()
    $writer = $null
    $stream = $null

    $prepared = [IO.File]::ReadAllText($temp, $encoding)
    if ($prepared -cne $Content) {
        throw "Browser Pro temporary raw reread mismatch: $temp"
    }
    [IO.File]::Move($temp, $raw)
} catch [IO.IOException] {
    throw "Browser Pro raw cannot be atomically published without clobbering: $raw"
} finally {
    if ($null -ne $writer) { $writer.Dispose() }
    elseif ($null -ne $stream) { $stream.Dispose() }
    if (Test-Path -LiteralPath $temp) {
        Remove-Item -LiteralPath $temp -Force
    }
}

$archived = [IO.File]::ReadAllText($raw, $encoding)
if ($archived -cne $Content) {
    throw "Browser Pro published raw reread mismatch; preserve for manual recovery: $raw"
}
$hasher = [Security.Cryptography.SHA256]::Create()
try {
    $hashBytes = $hasher.ComputeHash($encoding.GetBytes($archived))
} finally {
    $hasher.Dispose()
}
$sha256 = -join @($hashBytes | ForEach-Object { $_.ToString('x2') })
[ordered]@{
    status = 'BROWSER_PRO_RAW_ARCHIVED_NO_CLOBBER'
    raw = $raw
    sha256 = $sha256
    bytes = $encoding.GetByteCount($archived)
} | ConvertTo-Json -Compress
