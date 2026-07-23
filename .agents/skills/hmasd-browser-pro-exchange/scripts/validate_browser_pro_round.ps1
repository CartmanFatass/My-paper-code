[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [string]$RepoRoot,
    [string[]]$SnapshotPaths = @(),
    [string]$ExpectedStageCommit,
    [string]$ExpectedEvidenceCommit,
    [string]$ExpectedRepository,
    [string]$ExpectedReviewBranch,
    [string]$ExpectedConversationUrl,
    [string]$ExpectedModel
)

$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$dispatchModule = Join-Path $PSScriptRoot 'browser_pro_dispatch.psm1'
Import-Module $dispatchModule -Force

function Get-Sha256 {
    param([byte[]]$Bytes)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        return -join @($hasher.ComputeHash($Bytes) | ForEach-Object { $_.ToString('x2') })
    } finally {
        $hasher.Dispose()
    }
}

function Read-Utf8NoBom {
    param([string]$Path, [string]$Label)
    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xef -and $bytes[1] -eq 0xbb -and $bytes[2] -eq 0xbf) {
        throw "$Label must be UTF-8 without a BOM: $Path"
    }
    try {
        return $utf8.GetString($bytes)
    } catch {
        throw "$Label is not valid UTF-8: $Path"
    }
}

function Resolve-SafeBrowserSnapshot {
    param([string]$Path, [string]$TempRoot, [string]$RepositoryRoot)
    if (-not [IO.Path]::IsPathRooted($Path)) {
        throw "BrowserMCP snapshot path must be absolute: $Path"
    }
    $candidate = [IO.Path]::GetFullPath($Path)
    $tempPrefix = $TempRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $repoPrefix = $RepositoryRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($tempPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        $candidate.Equals($TempRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "BrowserMCP snapshot must be strictly under the canonical OS temp root: $candidate"
    }
    if ($candidate.Equals($RepositoryRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $candidate.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "BrowserMCP snapshot cannot equal or reside beneath RepoRoot: $candidate"
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "BrowserMCP snapshot must be an existing regular file: $candidate"
    }
    $file = Get-Item -LiteralPath $candidate -Force
    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        ($file.Attributes -band [IO.FileAttributes]::Directory) -ne 0) {
        throw "BrowserMCP snapshot cannot be a reparse point or directory: $candidate"
    }
    $ancestor = [IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($candidate))
    while ($null -ne $ancestor) {
        if (($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "BrowserMCP snapshot ancestor cannot be a reparse point: $($ancestor.FullName)"
        }
        if ($ancestor.FullName.Equals($TempRoot, [StringComparison]::OrdinalIgnoreCase)) { break }
        $ancestor = $ancestor.Parent
    }
    if ($null -eq $ancestor) { throw "BrowserMCP snapshot ancestry did not reach canonical temp root: $candidate" }
    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    if (-not $resolved.StartsWith($tempPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        $resolved.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "BrowserMCP snapshot resolves outside the safe temp boundary: $resolved"
    }
    return $resolved
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
} else {
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}

$canonical = [ordered]@{
    QuestionPath = '20_PRO_OPEN_QUESTION.md'
    ReceiptPath = '19_BROWSER_PRO_SUBMISSION.json'
    RawPath = '21_PRO_OPEN_RAW.md'
}
foreach ($entry in $canonical.GetEnumerator()) {
    $value = Get-Variable -Name $entry.Key -ValueOnly
    if ([IO.Path]::GetFileName($value) -cne $value -or $value -cne $entry.Value) {
        throw "Browser Pro $($entry.Key) must be canonical basename $($entry.Value)"
    }
}

$roundCandidate = if ([IO.Path]::IsPathRooted($RoundPath)) { $RoundPath } else { Join-Path $RepoRoot $RoundPath }
$round = (Resolve-Path -LiteralPath $roundCandidate).Path
$reviewRoot = (Resolve-Path -LiteralPath (Join-Path $RepoRoot 'docs/external-review/rounds')).Path
$reviewPrefix = $reviewRoot + [IO.Path]::DirectorySeparatorChar
if (-not $round.StartsWith($reviewPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Browser Pro round escapes review root: $round"
}
$roundId = Split-Path -Leaf $round
$manifest = [IO.Path]::GetFullPath((Join-Path $round '01_SHARED_SOURCE_MANIFEST.md'))
$question = [IO.Path]::GetFullPath((Join-Path $round $QuestionPath))
$receipt = [IO.Path]::GetFullPath((Join-Path $round $ReceiptPath))
$raw = [IO.Path]::GetFullPath((Join-Path $round $RawPath))
$roundPrefix = $round + [IO.Path]::DirectorySeparatorChar
foreach ($path in @($manifest, $question, $receipt, $raw)) {
    if (-not $path.StartsWith($roundPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Browser Pro path escapes round directory: $path"
    }
}

# Raw is the terminal durable fact. Once present, no browser or receipt work is allowed.
if (Test-Path -LiteralPath $raw) {
    if (-not (Test-Path -LiteralPath $raw -PathType Leaf)) {
        throw "Browser Pro canonical raw path is occupied by a non-file: $raw"
    }
    [ordered]@{
        status = 'ALREADY_ARCHIVED'
        round = $round
        receipt = $receipt
        question = $question
        raw = $raw
    } | ConvertTo-Json -Compress
    return
}
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw "Missing Browser Pro source manifest: $manifest"
}
if (-not (Test-Path -LiteralPath $question -PathType Leaf)) {
    throw "Missing Browser Pro question: $question"
}

$questionText = (Read-Utf8NoBom $question 'Browser Pro question') -replace "`r`n", "`n" -replace "`r", "`n"
$firstLf = $questionText.IndexOf("`n", [StringComparison]::Ordinal)
if ($firstLf -lt 0) { throw 'Browser Pro question must contain a marker line, one blank line, and a nonempty body' }
$secondLf = $questionText.IndexOf("`n", $firstLf + 1)
if ($secondLf -lt 0 -or $secondLf -ne ($firstLf + 1)) {
    throw 'Browser Pro question marker must be followed by exactly one blank line'
}
$marker = $questionText.Substring(0, $firstLf)
$body = $questionText.Substring($secondLf + 1)
if ([string]::IsNullOrWhiteSpace($body)) { throw 'Browser Pro question body must be nonempty' }
$markerMatch = [regex]::Match($marker, '^HMASD_BROWSER_PRO_QUESTION_V1 round=([^\s]+) body_sha256=([0-9a-f]{64})$')
if (-not $markerMatch.Success) { throw 'Browser Pro question has an invalid question marker' }
if ($markerMatch.Groups[1].Value -cne $roundId) {
    throw "Browser Pro question marker round mismatch: $($markerMatch.Groups[1].Value)"
}
$questionSha256 = Get-Sha256 $utf8.GetBytes($body)
if ($markerMatch.Groups[2].Value -cne $questionSha256) {
    throw 'Browser Pro question marker body digest mismatch'
}

$receiptSha256 = $null
$status = 'READY_TO_SUBMIT'
if (Test-Path -LiteralPath $receipt) {
    if (-not (Test-Path -LiteralPath $receipt -PathType Leaf)) { throw "Browser Pro receipt is not a file: $receipt" }
    $expectedParameters = @(
        'ExpectedStageCommit', 'ExpectedEvidenceCommit', 'ExpectedRepository',
        'ExpectedReviewBranch', 'ExpectedConversationUrl', 'ExpectedModel')
    $missingExpected = @($expectedParameters | Where-Object {
        -not $PSBoundParameters.ContainsKey($_) -or
        [string]::IsNullOrWhiteSpace([string](Get-Variable -Name $_ -ValueOnly))
    })
    if ($missingExpected.Count -gt 0) {
        throw "Browser Pro active receipt requires the complete trusted expected identity tuple; missing: $($missingExpected -join ', ')"
    }
    if ($ExpectedStageCommit -cnotmatch '^[0-9a-f]{40}$' -or
        $ExpectedEvidenceCommit -cnotmatch '^[0-9a-f]{40}$') {
        throw 'Browser Pro trusted expected identity requires exact 40-character lowercase stage and evidence commits'
    }
    if ($ExpectedRepository -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$' -or
        $ExpectedRepository.Contains('..') -or $ExpectedRepository.EndsWith('.') -or
        $ExpectedReviewBranch -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._/-]*$' -or
        $ExpectedReviewBranch.Contains('..') -or $ExpectedReviewBranch.Contains('//') -or
        $ExpectedReviewBranch.Contains('@{') -or $ExpectedReviewBranch.EndsWith('/') -or
        $ExpectedReviewBranch.EndsWith('.') -or $ExpectedReviewBranch.EndsWith('.lock')) {
        throw 'Browser Pro trusted expected identity requires valid repository and review branch tokens'
    }
    if ($ExpectedConversationUrl -cnotmatch '^https://chatgpt\.com/c/[A-Za-z0-9-]+/?$' -or
        $ExpectedModel -cne 'Pro') {
        throw 'Browser Pro trusted expected identity requires the registered ChatGPT conversation URL and expected model Pro'
    }
    try {
        $receiptStream = [IO.FileStream]::new(
            $receipt, [IO.FileMode]::Open, [IO.FileAccess]::Read,
            ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        try {
            $receiptMemory = [IO.MemoryStream]::new()
            try {
                $receiptStream.CopyTo($receiptMemory)
                [byte[]]$receiptBytes = $receiptMemory.ToArray()
            } finally {
                $receiptMemory.Dispose()
            }
        } finally {
            $receiptStream.Dispose()
        }
        $receiptSha256 = Get-Sha256 $receiptBytes
        if ($receiptBytes.Length -ge 3 -and
            $receiptBytes[0] -eq 0xef -and $receiptBytes[1] -eq 0xbb -and $receiptBytes[2] -eq 0xbf) {
            throw 'receipt has a UTF-8 BOM'
        }
        $receiptObject = $utf8.GetString($receiptBytes) | ConvertFrom-Json
    } catch {
        throw "Malformed Browser Pro submission receipt: $receipt"
    }
    $requiredFields = @('schema', 'status', 'round', 'question_sha256', 'dispatch_sha256',
        'stage_commit', 'evidence_commit', 'repository', 'review_branch', 'conversation_url',
        'expected_model')
    $actualFields = @($receiptObject.PSObject.Properties.Name)
    if ((Compare-Object $requiredFields $actualFields) -or
        $receiptObject.schema -cne 'hmasd.browser_pro_submission.v2' -or
        $receiptObject.status -cne 'SUBMISSION_CONFIRMED' -or
        $receiptObject.round -cne $roundId -or
        $receiptObject.question_sha256 -cne $questionSha256 -or
        [string]$receiptObject.dispatch_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        [string]$receiptObject.stage_commit -cnotmatch '^[0-9a-f]{40}$' -or
        [string]$receiptObject.evidence_commit -cnotmatch '^[0-9a-f]{40}$' -or
        [string]$receiptObject.repository -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$' -or
        [string]$receiptObject.review_branch -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._/-]*$' -or
        [string]$receiptObject.conversation_url -cnotmatch '^https://chatgpt\.com/c/[A-Za-z0-9-]+/?$' -or
        $receiptObject.expected_model -cne 'Pro') {
        throw "Browser Pro submission receipt does not match round and question digest or required shape: $receipt"
    }
    $identityMismatches = @()
    foreach ($identity in ([ordered]@{
        stage_commit = $ExpectedStageCommit
        evidence_commit = $ExpectedEvidenceCommit
        repository = $ExpectedRepository
        review_branch = $ExpectedReviewBranch
        conversation_url = $ExpectedConversationUrl
        expected_model = $ExpectedModel
    }).GetEnumerator()) {
        if ([string]$receiptObject.($identity.Key) -cne [string]$identity.Value) {
            $identityMismatches += $identity.Key
        }
    }
    if ($identityMismatches.Count -gt 0) {
        throw "Browser Pro submission receipt does not match trusted expected identity: $($identityMismatches -join ', ')"
    }
    $receiptQuestionPath = "docs/external-review/rounds/$roundId/20_PRO_OPEN_QUESTION.md"
    $expectedDispatch = New-HmasdBrowserProDispatch -Repository $ExpectedRepository `
        -ReviewBranch $ExpectedReviewBranch -StageCommit $ExpectedStageCommit `
        -QuestionSha256 $questionSha256 -QuestionPath $receiptQuestionPath
    if ($receiptObject.dispatch_sha256 -cne $expectedDispatch.dispatch_sha256) {
        throw "Browser Pro submission receipt dispatch digest does not match deterministic trusted dispatch: $receipt"
    }
    $status = 'RESUME_SUBMITTED'
}

if ($SnapshotPaths.Count -gt 0 -and -not ('HmasdBrowserSnapshotFileIdentity' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public static class HmasdBrowserSnapshotFileIdentity {
    [StructLayout(LayoutKind.Sequential)]
    private struct FileInformation {
        public uint FileAttributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
        public uint VolumeSerialNumber;
        public uint FileSizeHigh;
        public uint FileSizeLow;
        public uint NumberOfLinks;
        public uint FileIndexHigh;
        public uint FileIndexLow;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandle(
        SafeFileHandle handle, out FileInformation information);

    public static string Get(string path) {
        using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                                           FileShare.ReadWrite | FileShare.Delete)) {
            FileInformation information;
            if (!GetFileInformationByHandle(stream.SafeFileHandle, out information)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            ulong index = ((ulong)information.FileIndexHigh << 32) | information.FileIndexLow;
            return information.VolumeSerialNumber.ToString("X8") + ":" + index.ToString("X16");
        }
    }
}
'@
}

$safeSnapshots = @()
if ($SnapshotPaths.Count -gt 0) {
    $tempRoot = (Resolve-Path -LiteralPath ([IO.Path]::GetTempPath())).Path.TrimEnd([IO.Path]::DirectorySeparatorChar)
    foreach ($snapshotPath in $SnapshotPaths) {
        $safeSnapshots += Resolve-SafeBrowserSnapshot $snapshotPath $tempRoot $RepoRoot
    }
    $uniqueSnapshots = @($safeSnapshots | Sort-Object -Unique)
    if ($uniqueSnapshots.Count -ne $safeSnapshots.Count) {
        throw 'BrowserMCP snapshot inputs must resolve to distinct files'
    }
    $identities = @($safeSnapshots | ForEach-Object { [HmasdBrowserSnapshotFileIdentity]::Get($_) })
    if (@($identities | Sort-Object -Unique).Count -ne $identities.Count) {
        throw 'BrowserMCP snapshot inputs must have distinct file identities'
    }
}

[ordered]@{
    status = $status
    round = $round
    round_id = $roundId
    source_manifest = $manifest
    question = $question
    receipt = $receipt
    raw = $raw
    question_sha256 = $questionSha256
    receipt_sha256 = $receiptSha256
    question_marker = $marker
    snapshot_paths = $safeSnapshots
} | ConvertTo-Json -Compress
