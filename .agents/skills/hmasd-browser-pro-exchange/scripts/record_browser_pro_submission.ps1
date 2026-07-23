[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$ReceiptPath,
    [Parameter(Mandatory = $true)][string]$RawPath,
    [Parameter(Mandatory = $true)][string]$DraftSnapshotPath,
    [Parameter(Mandatory = $true)][string]$SubmittedSnapshotPath,
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$EvidenceCommit,
    [Parameter(Mandatory = $true)][string]$Repository,
    [Parameter(Mandatory = $true)][string]$ReviewBranch,
    [Parameter(Mandatory = $true)][string]$ConversationUrl,
    [string]$ExpectedModel = 'Pro',
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
function Get-Indent { param([string]$Line) return ([regex]::Match($Line, '^\s*')).Value.Length }
function Test-UserHeading {
    param([string]$Line)
    return $Line -match '^\s*-\s+heading(?:\s+\[[^\]]+\])?\s+["'']You said:["''](?:\s+\[[^\]]+\])*\s*$'
}
function Test-AssistantHeading {
    param([string]$Line)
    return $Line -match '^\s*-\s+heading(?:\s+\[[^\]]+\])?\s+["'']ChatGPT said:["''](?:\s+\[[^\]]+\])*\s*$'
}
function Convert-ParagraphScalar {
    param([string]$Scalar)
    if ($Scalar.StartsWith(' ')) { $Scalar = $Scalar.Substring(1) }
    if ($Scalar.Length -eq 0) { return '' }
    if ($Scalar.StartsWith('"') -and $Scalar.EndsWith('"')) {
        try { return [string]($Scalar | ConvertFrom-Json) }
        catch { throw 'BrowserMCP composer paragraph has invalid double-quoted scalar' }
    }
    if ($Scalar.StartsWith("'") -and $Scalar.EndsWith("'")) {
        return $Scalar.Substring(1, $Scalar.Length - 2).Replace("''", "'")
    }
    return $Scalar
}
function Get-ComposerText {
    param([string]$Snapshot)
    $lines = $Snapshot -split "`n", -1
    $textboxes = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*-\s+textbox\b.*:\s*$') { $textboxes += $i }
    }
    if ($textboxes.Count -eq 0) { throw 'BrowserMCP snapshot has no structural composer textbox' }
    $textbox = $textboxes[-1]
    $textboxIndent = Get-Indent $lines[$textbox]
    $values = @()
    for ($i = $textbox + 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Trim().Length -eq 0) { continue }
        if ((Get-Indent $lines[$i]) -le $textboxIndent) { break }
        if ($lines[$i] -notmatch '^\s*-\s+paragraph(?:\s+\[[^\]]+\])?\s*(?::(.*))?\s*$') {
            throw "BrowserMCP composer contains unsupported ARIA node: $($lines[$i].Trim())"
        }
        $scalar = if ($null -eq $Matches[1]) { '' } else { [string]$Matches[1] }
        $values += Convert-ParagraphScalar $scalar
    }
    if ($values.Count -eq 0) { return '' }
    return ($values -join "`n") + "`n"
}
function Get-StructuralTurns {
    param([string[]]$Lines)
    $candidates = @()
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if (Test-UserHeading $Lines[$i]) {
            $candidates += [pscustomobject]@{ Type = 'user'; Index = $i; Indent = (Get-Indent $Lines[$i]) }
        } elseif (Test-AssistantHeading $Lines[$i]) {
            $candidates += [pscustomobject]@{ Type = 'assistant'; Index = $i; Indent = (Get-Indent $Lines[$i]) }
        }
    }
    if ($candidates.Count -eq 0) { throw 'BrowserMCP snapshot has no structural ChatGPT turn headings' }
    $turnIndent = ($candidates | Measure-Object -Property Indent -Minimum).Minimum
    return @($candidates | Where-Object { $_.Indent -eq $turnIndent })
}

if ($StageCommit -cnotmatch '^[0-9a-fA-F]{40}$' -or $EvidenceCommit -cnotmatch '^[0-9a-fA-F]{40}$') {
    throw 'Browser Pro receipt requires exact 40-character stage and evidence commits'
}
if ($Repository -cnotmatch '^[^/\s]+/[^/\s]+$' -or [string]::IsNullOrWhiteSpace($ReviewBranch)) {
    throw 'Browser Pro receipt requires repository owner/name and a nonempty review branch'
}
if ($ConversationUrl -cnotmatch '^https://chatgpt\.com/c/[A-Za-z0-9-]+/?$' -or $ExpectedModel -cne 'Pro') {
    throw 'Browser Pro receipt requires the registered ChatGPT conversation URL and expected model Pro'
}

$validated = (& $validator -RoundPath $RoundPath -QuestionPath $QuestionPath `
    -ReceiptPath $ReceiptPath -RawPath $RawPath -RepoRoot $RepoRoot `
    -SnapshotPaths @($DraftSnapshotPath, $SubmittedSnapshotPath)) | ConvertFrom-Json
$acceptedSnapshots = @($validated.snapshot_paths)
try {
    if ($validated.status -ne 'READY_TO_SUBMIT') {
        throw "Browser Pro submission cannot be recorded from state $($validated.status)"
    }
    $draft = (Read-Utf8NoBom $acceptedSnapshots[0] 'BrowserMCP draft snapshot') -replace "`r`n", "`n" -replace "`r", "`n"
    $submitted = (Read-Utf8NoBom $acceptedSnapshots[1] 'BrowserMCP submitted snapshot') -replace "`r`n", "`n" -replace "`r", "`n"
    $canonicalQuestion = (Read-Utf8NoBom ([string]$validated.question) 'Browser Pro question') -replace "`r`n", "`n" -replace "`r", "`n"
    $draftQuestion = Get-ComposerText $draft
    if ([Convert]::ToBase64String($utf8.GetBytes($draftQuestion)) -cne
        [Convert]::ToBase64String($utf8.GetBytes($canonicalQuestion))) {
        throw 'BrowserMCP draft composer does not byte-match the canonical question'
    }
    if ((Get-ComposerText $submitted).Length -ne 0) {
        throw 'BrowserMCP submitted composer is not empty'
    }

    $marker = [string]$validated.question_marker
    $markerCount = [regex]::Matches($submitted, [regex]::Escape($marker)).Count
    if ($markerCount -ne 1) {
        throw "BrowserMCP submitted snapshot must contain the exact unique question marker once; found $markerCount"
    }
    $lines = $submitted -split "`n", -1
    $turns = Get-StructuralTurns $lines
    $userTurns = @($turns | Where-Object { $_.Type -eq 'user' })
    if ($userTurns.Count -eq 0) { throw 'BrowserMCP submitted snapshot has no visible user turn' }
    $lastUser = $userTurns[-1].Index
    $segmentEnd = $lines.Count
    foreach ($turn in $turns) {
        if ($turn.Index -gt $lastUser) { $segmentEnd = $turn.Index; break }
    }
    $lastUserText = $lines[$lastUser..($segmentEnd - 1)] -join "`n"
    if (-not $lastUserText.Contains($marker)) {
        throw 'Exact question marker is stale; the last visible user turn does not contain it'
    }

    $receiptObject = [ordered]@{
        schema = 'hmasd.browser_pro_submission.v1'
        status = 'SUBMISSION_CONFIRMED'
        round = [string]$validated.round_id
        question_sha256 = [string]$validated.question_sha256
        stage_commit = $StageCommit.ToLowerInvariant()
        evidence_commit = $EvidenceCommit.ToLowerInvariant()
        repository = $Repository
        review_branch = $ReviewBranch
        conversation_url = $ConversationUrl
        expected_model = 'Pro'
    }
    $receiptBytes = $utf8.GetBytes((($receiptObject | ConvertTo-Json) + "`n"))
    $receiptPathResolved = [string]$validated.receipt
    $temp = Join-Path ([IO.Path]::GetDirectoryName($receiptPathResolved)) `
        ('.' + [IO.Path]::GetFileName($receiptPathResolved) + '.' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        if (Test-Path -LiteralPath $receiptPathResolved) {
            throw [IO.IOException]::new("Submission receipt already exists: $receiptPathResolved")
        }
        $stream = [IO.FileStream]::new($temp, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try { $stream.Write($receiptBytes, 0, $receiptBytes.Length); $stream.Flush($true) }
        finally { $stream.Dispose() }
        if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($temp)) -cne [Convert]::ToBase64String($receiptBytes)) {
            throw 'Browser Pro temporary submission receipt reread mismatch'
        }
        [IO.File]::Move($temp, $receiptPathResolved)
    } catch [IO.IOException] {
        throw "Browser Pro submission receipt cannot be atomically published without clobbering: $receiptPathResolved"
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force }
    }
    $published = [IO.File]::ReadAllBytes($receiptPathResolved)
    if ([Convert]::ToBase64String($published) -cne [Convert]::ToBase64String($receiptBytes)) {
        throw "Browser Pro published submission receipt reread mismatch: $receiptPathResolved"
    }
    [ordered]@{
        status = 'SUBMISSION_CONFIRMED'
        receipt = $receiptPathResolved
        receipt_sha256 = Get-Sha256 $published
        question_sha256 = [string]$validated.question_sha256
        bytes = $published.Length
    } | ConvertTo-Json -Compress
} finally {
    foreach ($snapshot in $acceptedSnapshots) {
        if (Test-Path -LiteralPath $snapshot -PathType Leaf) { Remove-Item -LiteralPath $snapshot -Force }
    }
}
