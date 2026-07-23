[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [Parameter(Mandatory = $true)][string]$SnapshotPathOne,
    [Parameter(Mandatory = $true)][string]$SnapshotPathTwo,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$validator = Join-Path $PSScriptRoot 'validate_browser_pro_round.ps1'

function Get-Sha256 {
    param([byte[]]$Bytes)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return -join @($hasher.ComputeHash($Bytes) | ForEach-Object { $_.ToString('x2') }) }
    finally { $hasher.Dispose() }
}
function Read-Utf8NoBom {
    param([string]$Path, [string]$Label)
    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xef -and $bytes[1] -eq 0xbb -and $bytes[2] -eq 0xbf) {
        throw "$Label must be UTF-8 without a BOM: $Path"
    }
    try { return $utf8.GetString($bytes) }
    catch { throw "$Label is not valid UTF-8: $Path" }
}
function Test-UserAnchor {
    param([string]$Line)
    return $Line -match '^\s*-\s+heading(?:\s+\[[^\]]+\])?\s+["'']You said:["''](?:\s+\[[^\]]+\])*\s*$'
}
function Test-AssistantAnchor {
    param([string]$Line)
    return $Line -match '^\s*-\s+heading(?:\s+\[[^\]]+\])?\s+["'']ChatGPT said:["''](?:\s+\[[^\]]+\])*\s*$'
}
function Get-Indent { param([string]$Line) return ([regex]::Match($Line, '^\s*')).Value.Length }
function Convert-QuotedYamlScalar {
    param([string]$Scalar)
    $trimmed = $Scalar.Trim()
    if ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) {
        try { return [string]($trimmed | ConvertFrom-Json) }
        catch { throw 'BrowserMCP code scalar has invalid YAML/JSON double quoting' }
    }
    if ($trimmed.StartsWith("'") -and $trimmed.EndsWith("'")) {
        return $trimmed.Substring(1, $trimmed.Length - 2).Replace("''", "'")
    }
    throw 'BrowserMCP code scalar must be a YAML literal or quoted scalar'
}
function Read-LiteralScalar {
    param([string[]]$Lines, [int]$Anchor, [int]$Limit, [string]$Indicator)
    $anchorIndent = Get-Indent $Lines[$Anchor]
    $end = $Anchor + 1
    while ($end -lt $Limit) {
        if ($Lines[$end].Length -gt 0 -and (Get-Indent $Lines[$end]) -le $anchorIndent) { break }
        $end++
    }
    $contentLines = @($Lines[($Anchor + 1)..($end - 1)])
    $nonempty = @($contentLines | Where-Object { $_.Trim().Length -gt 0 })
    if ($nonempty.Count -eq 0) {
        return [pscustomobject]@{ Content = ''; End = $end - 1 }
    }
    $contentIndent = ($nonempty | ForEach-Object { Get-Indent $_ } | Measure-Object -Minimum).Minimum
    $decoded = @($contentLines | ForEach-Object {
        if ($_.Length -ge $contentIndent) { $_.Substring($contentIndent) } else { '' }
    }) -join "`n"
    if ($Indicator -eq '|') { $decoded += "`n" }
    elseif ($Indicator -eq '|+') { $decoded += "`n" }
    return [pscustomobject]@{ Content = $decoded; End = $end - 1 }
}
function Get-CodeScalar {
    param([string[]]$Lines, [int]$CodeIndex, [int]$Limit, [string]$Remainder)
    $scalarAnchor = $CodeIndex
    $scalar = $Remainder.Trim()
    if ($scalar.Length -eq 0) {
        $child = $CodeIndex + 1
        while ($child -lt $Limit -and $Lines[$child].Trim().Length -eq 0) { $child++ }
        if ($child -ge $Limit -or $Lines[$child] -notmatch '^\s*-?\s*(?:text|generic)(?:\s+\[[^\]]+\])?\s*:\s*(.*)$') {
            return [pscustomobject]@{ Content = ''; End = $CodeIndex }
        }
        $scalarAnchor = $child
        $scalar = $Matches[1].Trim()
    }
    if ($scalar -in @('|-', '|', '|+')) {
        return Read-LiteralScalar $Lines $scalarAnchor $Limit $scalar
    }
    return [pscustomobject]@{ Content = (Convert-QuotedYamlScalar $scalar); End = $scalarAnchor }
}
function Get-StableResponse {
    param([string]$SnapshotPath, [string]$RoundId, [string]$QuestionSha256)
    if (-not (Test-Path -LiteralPath $SnapshotPath -PathType Leaf)) {
        throw "Missing temporary BrowserMCP response snapshot: $SnapshotPath"
    }
    $snapshot = (Read-Utf8NoBom (Resolve-Path -LiteralPath $SnapshotPath).Path 'BrowserMCP response snapshot') `
        -replace "`r`n", "`n" -replace "`r", "`n"
    $lines = $snapshot -split "`n", -1
    $turnCandidates = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if (Test-AssistantAnchor $lines[$i]) {
            $turnCandidates += [pscustomobject]@{ Type = 'assistant'; Index = $i; Indent = (Get-Indent $lines[$i]) }
        } elseif (Test-UserAnchor $lines[$i]) {
            $turnCandidates += [pscustomobject]@{ Type = 'user'; Index = $i; Indent = (Get-Indent $lines[$i]) }
        }
    }
    if ($turnCandidates.Count -eq 0) { throw 'BrowserMCP snapshot has no structural conversation turns' }
    $turnIndent = ($turnCandidates | Measure-Object -Property Indent -Minimum).Minimum
    $assistantAnchors = @($turnCandidates | Where-Object { $_.Indent -eq $turnIndent -and $_.Type -eq 'assistant' } |
        ForEach-Object { $_.Index })
    $userAnchors = @($turnCandidates | Where-Object { $_.Indent -eq $turnIndent -and $_.Type -eq 'user' } |
        ForEach-Object { $_.Index })
    if ($assistantAnchors.Count -eq 0) { throw 'BrowserMCP snapshot has no visible assistant turn' }
    $lastAssistant = $assistantAnchors[-1]
    if (@($userAnchors | Where-Object { $_ -gt $lastAssistant }).Count -gt 0) {
        throw 'BrowserMCP final visible conversation turn is not the assistant response'
    }
    $segmentEnd = $lines.Count
    for ($i = $lastAssistant + 1; $i -lt $lines.Count; $i++) {
        $isTurn = @($turnCandidates | Where-Object { $_.Indent -eq $turnIndent -and $_.Index -eq $i }).Count -gt 0
        $isResponseActions = (Get-Indent $lines[$i]) -eq $turnIndent -and
            $lines[$i] -match '^\s*-\s+group(?:\s+\[[^\]]+\])?\s+["'']Response actions["''](?:\s+\[[^\]]+\])*\s*:?\s*$'
        if ($isTurn -or $isResponseActions) {
            $segmentEnd = $i
            break
        }
    }
    $blocks = @()
    $covered = @{}
    for ($i = $lastAssistant; $i -lt $segmentEnd; $i++) {
        if ($lines[$i] -match '^\s*-\s+code(?:\s+\[[^\]]+\])?\s*:\s*(.*)$') {
            $parsed = Get-CodeScalar $lines $i $segmentEnd $Matches[1]
            $blocks += [pscustomobject]@{ Content = [string]$parsed.Content; Start = $i; End = [int]$parsed.End }
            for ($j = $i; $j -le [int]$parsed.End; $j++) { $covered[$j] = $true }
            $i = [int]$parsed.End
        }
    }
    if ($blocks.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$blocks[0].Content)) {
        throw "BrowserMCP final assistant turn must contain exactly one substantive code block; found $($blocks.Count)"
    }
    for ($i = $lastAssistant + 1; $i -lt $segmentEnd; $i++) {
        if ($covered.ContainsKey($i) -or [string]::IsNullOrWhiteSpace($lines[$i])) { continue }
        $line = $lines[$i]
        if ($line -match '^\s*-\s+(?:group|img)(?:\s+\[[^\]]+\])*\s*:?\s*$') { continue }
        if ($line -match '^\s*-\s+button\s+["'']([^"'']+)["''](?:\s+\[[^\]]+\])*\s*:?\s*$') {
            $name = $Matches[1]
            if ($name -in @('Copy', 'Copy code', 'Sources') -or
                $name -match '^Worked for (?:(?:\d+h )?(?:\d+m )?\d+s|\d+(?:\.\d+)? seconds?)$') {
                continue
            }
        }
        throw "BrowserMCP final assistant turn contains forbidden extra ARIA node: $($line.Trim())"
    }
    $block = ([string]$blocks[0].Content) -replace "`r`n", "`n" -replace "`r", "`n"
    $begin = "HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN round=$RoundId question_sha256=$QuestionSha256"
    $end = "HMASD_BROWSER_PRO_RESPONSE_V1_END round=$RoundId question_sha256=$QuestionSha256"
    $blockLines = $block -split "`n", -1
    if ($blockLines.Count -gt 0 -and $blockLines[-1] -eq '') { $blockLines = @($blockLines[0..($blockLines.Count - 2)]) }
    if ($blockLines.Count -lt 3 -or $blockLines[0] -cne $begin -or $blockLines[-1] -cne $end) {
        throw 'BrowserMCP response block has wrong, missing, or truncated response markers'
    }
    $responseLines = @($blockLines[1..($blockLines.Count - 2)])
    $response = ($responseLines -join "`n") + "`n"
    if ([string]::IsNullOrWhiteSpace($response)) { throw 'BrowserMCP marked response content is empty' }
    return $response
}

$validated = (& $validator -RoundPath $RoundPath -QuestionPath '20_PRO_OPEN_QUESTION.md' `
    -ReceiptPath $ReceiptPath -RawPath $RawPath -RepoRoot $RepoRoot `
    -SnapshotPaths @($SnapshotPathOne, $SnapshotPathTwo)) | ConvertFrom-Json
if ($validated.status -ne 'RESUME_SUBMITTED') {
    throw "Browser Pro response cannot be archived from state $($validated.status)"
}
$acceptedSnapshots = @($validated.snapshot_paths)
try {
    $captureOne = Get-Item -LiteralPath $acceptedSnapshots[0]
    $captureTwo = Get-Item -LiteralPath $acceptedSnapshots[1]
    if ($captureTwo.LastWriteTimeUtc -lt $captureOne.LastWriteTimeUtc.AddSeconds(10)) {
        throw 'BrowserMCP stable snapshots must be captured at least ten seconds apart in chronological order'
    }
    $receipt = (Read-Utf8NoBom ([string]$validated.receipt) 'Browser Pro submission receipt') | ConvertFrom-Json
    $contentOne = Get-StableResponse $acceptedSnapshots[0] ([string]$receipt.round) ([string]$receipt.question_sha256)
    $contentTwo = Get-StableResponse $acceptedSnapshots[1] ([string]$receipt.round) ([string]$receipt.question_sha256)
    $bytesOne = $utf8.GetBytes($contentOne)
    $bytesTwo = $utf8.GetBytes($contentTwo)
    if ([Convert]::ToBase64String($bytesOne) -cne [Convert]::ToBase64String($bytesTwo)) {
        throw 'BrowserMCP marked response content differs across the two snapshots'
    }

    $raw = [string]$validated.raw
    $temp = Join-Path ([IO.Path]::GetDirectoryName($raw)) `
        ('.' + [IO.Path]::GetFileName($raw) + '.' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        if (Test-Path -LiteralPath $raw) { throw [IO.IOException]::new("Final raw already exists: $raw") }
        $stream = [IO.FileStream]::new($temp, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $stream.Write($bytesOne, 0, $bytesOne.Length)
        $stream.Flush($true)
    } finally { $stream.Dispose() }
    $prepared = [IO.File]::ReadAllBytes($temp)
    if ([Convert]::ToBase64String($prepared) -cne [Convert]::ToBase64String($bytesOne)) {
        throw 'Browser Pro temporary raw reread mismatch'
    }
    [IO.File]::Move($temp, $raw)
} catch [IO.IOException] {
    throw "Browser Pro raw cannot be atomically published without clobbering: $raw"
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
}
$archived = [IO.File]::ReadAllBytes($raw)
if ([Convert]::ToBase64String($archived) -cne [Convert]::ToBase64String($bytesOne)) {
    throw "Browser Pro published raw reread mismatch; preserve for manual recovery: $raw"
}
[ordered]@{
    status = 'ARCHIVED'
    raw = $raw
    sha256 = Get-Sha256 $archived
    snapshot_one_sha256 = Get-Sha256 $bytesOne
    snapshot_two_sha256 = Get-Sha256 $bytesTwo
    bytes = $archived.Length
} | ConvertTo-Json -Compress
} finally {
    foreach ($snapshot in $acceptedSnapshots) {
        if (Test-Path -LiteralPath $snapshot -PathType Leaf) { Remove-Item -LiteralPath $snapshot -Force }
    }
}
