[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [Parameter(Mandatory = $true)][string]$SnapshotPathOne,
    [Parameter(Mandatory = $true)][string]$SnapshotPathTwo,
    [Parameter(Mandatory = $true)][string]$CopiedResponsePath,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$EvidenceCommit,
    [Parameter(Mandatory = $true)][string]$Repository,
    [Parameter(Mandatory = $true)][string]$ReviewBranch,
    [Parameter(Mandatory = $true)][string]$ConversationUrl,
    [Parameter(Mandatory = $true)][string]$ExpectedModel,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$validator = Join-Path $PSScriptRoot 'validate_browser_pro_round.ps1'
$receiptLockModule = Join-Path $PSScriptRoot 'browser_pro_receipt_lock.psm1'
Import-Module $receiptLockModule -Force

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
function Convert-IdentityWhitespace {
    param([string]$Content)
    $normalized = $Content -replace "`r`n", "`n" -replace "`r", "`n"
    return ([regex]::Replace($normalized, '\s+', ' ')).Trim()
}
function Get-CopiedResponse {
    param([string]$Path, [string]$RoundId, [string]$QuestionSha256)
    $document = (Read-Utf8NoBom $Path 'Copied BrowserMCP response') `
        -replace "`r`n", "`n" -replace "`r", "`n"
    if ($document.EndsWith("`n", [StringComparison]::Ordinal)) {
        $document = $document.Substring(0, $document.Length - 1)
    }
    $lines = $document -split "`n", -1
    if ($lines.Count -lt 5 -or $lines[0] -cne '```text' -or $lines[-1] -cne '```') {
        throw 'Copied BrowserMCP response must have exact outer ```text and ``` fence lines'
    }
    for ($i = 1; $i -lt $lines.Count - 1; $i++) {
        if ($lines[$i].Contains('```')) {
            throw 'Copied BrowserMCP response contains a nested triple-backtick sequence'
        }
    }
    $begin = "HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN round=$RoundId question_sha256=$QuestionSha256"
    $end = "HMASD_BROWSER_PRO_RESPONSE_V1_END round=$RoundId question_sha256=$QuestionSha256"
    if ($lines[1] -cne $begin -or $lines[-2] -cne $end) {
        throw 'Copied BrowserMCP response has wrong, missing, or misplaced response markers'
    }
    $body = @($lines[2..($lines.Count - 3)]) -join "`n"
    if ([string]::IsNullOrWhiteSpace($body)) {
        throw 'Copied BrowserMCP marked response content is empty'
    }
    $response = $body.TrimEnd([char]"`n") + "`n"
    $marked = @($lines[1..($lines.Count - 2)]) -join "`n"
    return [pscustomobject]@{ Response = $response; MarkedContent = $marked }
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
function Convert-YamlScalar {
    param([string]$Scalar)
    $trimmed = $Scalar.Trim()
    if ($trimmed.StartsWith('"')) {
        if (-not $trimmed.EndsWith('"')) {
            throw 'BrowserMCP code scalar has invalid YAML/JSON double quoting'
        }
        try { return [string]($trimmed | ConvertFrom-Json) }
        catch { throw 'BrowserMCP code scalar has invalid YAML/JSON double quoting' }
    }
    if ($trimmed.StartsWith("'")) {
        if (-not $trimmed.EndsWith("'")) {
            throw 'BrowserMCP code scalar has invalid YAML single quoting'
        }
        return $trimmed.Substring(1, $trimmed.Length - 2).Replace("''", "'")
    }
    return $trimmed
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
    return [pscustomobject]@{ Content = (Convert-YamlScalar $scalar); End = $scalarAnchor }
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
    if ($block.Contains("`n")) {
        $blockLines = $block -split "`n", -1
        if ($blockLines.Count -gt 0 -and $blockLines[-1] -eq '') {
            $blockLines = @($blockLines[0..($blockLines.Count - 2)])
        }
        if ($blockLines.Count -lt 3 -or $blockLines[0] -cne $begin -or $blockLines[-1] -cne $end) {
            throw 'BrowserMCP response block has wrong, missing, or truncated response markers'
        }
        $response = @($blockLines[1..($blockLines.Count - 2)]) -join "`n"
        if ([string]::IsNullOrWhiteSpace($response)) {
            throw 'BrowserMCP marked response content is empty'
        }
        return $blockLines -join "`n"
    }
    $collapsed = Convert-IdentityWhitespace $block
    $prefix = $begin + ' '
    $suffix = ' ' + $end
    if (-not $collapsed.StartsWith($prefix, [StringComparison]::Ordinal) -or
        -not $collapsed.EndsWith($suffix, [StringComparison]::Ordinal) -or
        $collapsed.Length -le ($prefix.Length + $suffix.Length)) {
        throw 'BrowserMCP response block has wrong, missing, or truncated response markers'
    }
    $response = $collapsed.Substring($prefix.Length, $collapsed.Length - $prefix.Length - $suffix.Length)
    if ([string]::IsNullOrWhiteSpace($response)) {
        throw 'BrowserMCP marked response content is empty'
    }
    return $collapsed
}

$validated = (& $validator -RoundPath $RoundPath -QuestionPath '20_PRO_OPEN_QUESTION.md' `
    -ReceiptPath $ReceiptPath -RawPath $RawPath -RepoRoot $RepoRoot `
    -SnapshotPaths @($SnapshotPathOne, $SnapshotPathTwo, $CopiedResponsePath) `
    -ExpectedStageCommit $StageCommit -ExpectedEvidenceCommit $EvidenceCommit `
    -ExpectedRepository $Repository -ExpectedReviewBranch $ReviewBranch `
    -ExpectedConversationUrl $ConversationUrl -ExpectedModel $ExpectedModel) | ConvertFrom-Json
if ($validated.status -ne 'RESUME_SUBMITTED') {
    throw "Browser Pro response cannot be archived from state $($validated.status)"
}
$acceptedInputs = @($validated.snapshot_paths)
try {
    $archiveAction = {
        param([byte[]]$LockedReceiptBytes)

        $captureOne = Get-Item -LiteralPath $acceptedInputs[0]
        $captureTwo = Get-Item -LiteralPath $acceptedInputs[1]
        if ($captureTwo.LastWriteTimeUtc -lt $captureOne.LastWriteTimeUtc.AddSeconds(10)) {
            throw 'BrowserMCP stable snapshots must be captured at least ten seconds apart in chronological order'
        }
        $contentOne = Get-StableResponse $acceptedInputs[0] `
            ([string]$validated.round_id) ([string]$validated.question_sha256)
        $contentTwo = Get-StableResponse $acceptedInputs[1] `
            ([string]$validated.round_id) ([string]$validated.question_sha256)
        $copied = Get-CopiedResponse $acceptedInputs[2] `
            ([string]$validated.round_id) ([string]$validated.question_sha256)
        $copiedIdentity = Convert-IdentityWhitespace ([string]$copied.MarkedContent)
        $identityOne = Convert-IdentityWhitespace $contentOne
        $identityTwo = Convert-IdentityWhitespace $contentTwo
        if ($identityOne -cne $copiedIdentity -or $identityTwo -cne $copiedIdentity) {
            throw 'BrowserMCP snapshot marked response differs from the exact copied response'
        }
        $bytesOne = $utf8.GetBytes($identityOne)
        $bytesTwo = $utf8.GetBytes($identityTwo)
        $rawBytes = $utf8.GetBytes([string]$copied.Response)

        $raw = [string]$validated.raw
        $temp = Join-Path ([IO.Path]::GetDirectoryName($raw)) `
            ('.' + [IO.Path]::GetFileName($raw) + '.' + [Guid]::NewGuid().ToString('N') + '.tmp')
        try {
            if (Test-Path -LiteralPath $raw) { throw [IO.IOException]::new("Final raw already exists: $raw") }
            $stream = [IO.FileStream]::new(
                $temp, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try {
                $stream.Write($rawBytes, 0, $rawBytes.Length)
                $stream.Flush($true)
            } finally {
                $stream.Dispose()
            }
            $prepared = [IO.File]::ReadAllBytes($temp)
            if ([Convert]::ToBase64String($prepared) -cne [Convert]::ToBase64String($rawBytes)) {
                throw 'Browser Pro temporary raw reread mismatch'
            }
            [IO.File]::Move($temp, $raw)
        } catch [IO.IOException] {
            throw "Browser Pro raw cannot be atomically published without clobbering: $raw"
        } finally {
            if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
        }

        $archived = [IO.File]::ReadAllBytes($raw)
        if ([Convert]::ToBase64String($archived) -cne [Convert]::ToBase64String($rawBytes)) {
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
    }
    Invoke-HmasdBrowserProReceiptLock -ReceiptPath ([string]$validated.receipt) `
        -ExpectedSha256 ([string]$validated.receipt_sha256) -Action $archiveAction
} finally {
    foreach ($inputPath in $acceptedInputs) {
        if (Test-Path -LiteralPath $inputPath -PathType Leaf) { Remove-Item -LiteralPath $inputPath -Force }
    }
}
