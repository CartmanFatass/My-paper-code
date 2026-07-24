[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$utf8 = [Text.UTF8Encoding]::new($false)
$renderer = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/render_browser_pro_dispatch.ps1'
$recorder = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1'
$validator = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1'

function Write-Utf8 { param([string]$Path, [string]$Content)
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path)) | Out-Null
    [IO.File]::WriteAllText($Path, $Content, $utf8)
}
function Get-Sha256 { param([byte[]]$Bytes)
    $h = [Security.Cryptography.SHA256]::Create()
    try { -join @($h.ComputeHash($Bytes) | ForEach-Object { $_.ToString('x2') }) }
    finally { $h.Dispose() }
}
function Assert-Failure { param([scriptblock]$Action, [string]$Pattern, [string]$Label)
    $failed = $false
    try { & $Action | Out-Null } catch {
        $failed = $true
        if ([string]$_ -notmatch $Pattern) { throw "$Label failed for the wrong reason: $_" }
    }
    if (-not $failed) { throw "$Label unexpectedly succeeded" }
}

if (-not (Test-Path -LiteralPath $renderer -PathType Leaf)) {
    throw 'Bounded BrowserMCP message dispatcher is missing; long browser_type payloads can overlap after timeout'
}

$fixture = Join-Path ([IO.Path]::GetTempPath()) ('hmasd-browser-dispatch-' + [Guid]::NewGuid().ToString('N'))
$repoFixture = Join-Path $fixture 'repo'
$capture = Join-Path $fixture 'captures'
$roundId = 'fixture_dispatch_round'
$roundRelative = "docs/external-review/rounds/$roundId"
$roundPath = Join-Path $repoFixture $roundRelative
$questionName = '20_PRO_OPEN_QUESTION.md'
$receiptName = '19_BROWSER_PRO_SUBMISSION.json'
$rawName = '21_PRO_OPEN_RAW.md'
$stage = '1111111111111111111111111111111111111111'
$evidence = '2222222222222222222222222222222222222222'
$repository = 'fixture-owner/fixture-repo'
$branch = 'Claude'
$conversation = 'https://chatgpt.com/c/fixture-dispatch'
$requiredNoNestedFenceInstruction = 'Do not put any triple-backtick sequence or nested fenced block between the response markers.'
try {
    [IO.Directory]::CreateDirectory($roundPath) | Out-Null
    [IO.Directory]::CreateDirectory($capture) | Out-Null
    Write-Utf8 (Join-Path $roundPath '01_SHARED_SOURCE_MANIFEST.md') "# Fixture manifest`n"
    $body = ('Long canonical scientific question. ' + ('X' * 4096) + "`n$requiredNoNestedFenceInstruction`n")
    $questionSha = Get-Sha256 $utf8.GetBytes($body)
    $questionMarker = "HMASD_BROWSER_PRO_QUESTION_V1 round=$roundId body_sha256=$questionSha"
    $questionText = "$questionMarker`n`n$body"
    Write-Utf8 (Join-Path $roundPath $questionName) $questionText

    function Invoke-Renderer {
        param(
            [string]$ReviewBranch = $branch,
            [string]$StageCommit = $stage,
            [string]$Repository = $repository,
            [string]$QuestionFile = $questionName
        )
        & $renderer -RoundPath $roundRelative -QuestionPath $QuestionFile -ReceiptPath $receiptName `
            -RawPath $rawName -StageCommit $StageCommit -EvidenceCommit $evidence -Repository $Repository `
            -ReviewBranch $ReviewBranch -RepoRoot $repoFixture
    }
    $rendered = (Invoke-Renderer) | ConvertFrom-Json
    $dispatchBytes = [Convert]::FromBase64String([string]$rendered.dispatch_base64)
    $dispatch = $utf8.GetString($dispatchBytes)
    $expectedDispatch = "HMASD_BP_D1 repo=$repository b=$branch stage=$stage q=$questionSha round=$roundId file=$questionName Read via GitHub connector; follow fully; no upload/code/compute."
    if ($dispatch -cne $expectedDispatch -or
        $rendered.status -ne 'DISPATCH_READY' -or $rendered.question_sha256 -ne $questionSha -or
        $rendered.dispatch_sha256 -ne (Get-Sha256 $dispatchBytes) -or
        $rendered.utf16_length -ne $dispatch.Length -or $rendered.byte_count -ne $dispatchBytes.Length -or
        $dispatch.Length -gt 352 -or $dispatch -match '[\r\n]' -or
        $dispatch -notmatch '^HMASD_BP_D1 ' -or
        -not $dispatch.Contains($stage) -or -not $dispatch.Contains($questionSha) -or
        -not $dispatch.Contains("round=$roundId file=$questionName") -or
        $dispatch.Contains($body.Substring(0, 32))) {
        throw 'Bounded dispatch renderer did not produce the exact compact message contract'
    }
    Assert-Failure { Invoke-Renderer "bad`nbranch" } 'single-line|invalid|bounded' 'Multiline dispatch identity'
    Assert-Failure { Invoke-Renderer ('b' * 250) } '352 UTF-16|bounded' 'Over-limit dispatch identity'
    Assert-Failure { Invoke-Renderer $branch ('1' * 39) } '40-character|stage' 'Wrong dispatch stage'
    Assert-Failure { Invoke-Renderer $branch $stage $repository '../20_PRO_OPEN_QUESTION.md' } 'canonical basename' 'Wrong dispatch path'
    Write-Utf8 (Join-Path $roundPath $questionName) ($questionText.Replace($questionSha, ('0' * 64)))
    Assert-Failure { Invoke-Renderer } 'digest mismatch' 'Wrong question digest'
    Write-Utf8 (Join-Path $roundPath $questionName) $questionText

    $dispatchScalar = (($dispatch.TrimEnd("`n")) | ConvertTo-Json -Compress)
    function New-Draft {
        param([string]$Path, [bool]$UseFullQuestion = $false, [bool]$MutateDispatch = $false)
        $text = if ($UseFullQuestion) { $questionText.TrimEnd("`n") } else { $dispatch + $(if ($MutateDispatch) { 'x' } else { '' }) }
        $value = $text | ConvertTo-Json -Compress
        Write-Utf8 $Path "- main [ref=draft]:`n  - textbox `"Message ChatGPT`" [ref=composer]:`n    - paragraph: $value`n"
    }
    function New-Submitted { param([string]$Path, [bool]$Stale = $false)
        $later = if ($Stale) { "`n  - article [ref=later]:`n    - heading `"You said:`"`n    - paragraph: Later message" } else { '' }
        Write-Utf8 $Path "- main [ref=submitted]:`n  - article [ref=user]:`n    - heading `"You said:`"`n    - paragraph: $dispatchScalar$later`n  - textbox `"Message ChatGPT`" [ref=composer]:`n"
    }
    function Invoke-Recorder { param([string]$Draft, [string]$Submitted)
        & $recorder -RoundPath $roundRelative -QuestionPath $questionName -ReceiptPath $receiptName `
            -RawPath $rawName -DraftSnapshotPath $Draft -SubmittedSnapshotPath $Submitted `
            -StageCommit $stage -EvidenceCommit $evidence -Repository $repository `
            -ReviewBranch $branch -ConversationUrl $conversation -RepoRoot $repoFixture
    }
    function Invoke-ValidatorExpected {
        & $validator -RoundPath $roundRelative -QuestionPath $questionName `
            -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $repoFixture `
            -ExpectedStageCommit $stage -ExpectedEvidenceCommit $evidence `
            -ExpectedRepository $repository -ExpectedReviewBranch $branch `
            -ExpectedConversationUrl $conversation -ExpectedModel 'Pro'
    }

    $oldDraft = Join-Path $capture 'old-full-question.yml'
    $oldSubmitted = Join-Path $capture 'old-submitted.yml'
    New-Draft $oldDraft $true
    New-Submitted $oldSubmitted
    Assert-Failure { Invoke-Recorder $oldDraft $oldSubmitted } 'dispatch|byte-match' 'Legacy full-question typing'

    $wrongBytesDraft = Join-Path $capture 'wrong-bytes-draft.yml'
    $wrongBytesSubmitted = Join-Path $capture 'wrong-bytes-submitted.yml'
    New-Draft $wrongBytesDraft $false $true
    New-Submitted $wrongBytesSubmitted
    Assert-Failure { Invoke-Recorder $wrongBytesDraft $wrongBytesSubmitted } 'dispatch|byte-match' 'Wrong dispatch bytes'

    $staleDraft = Join-Path $capture 'stale-draft.yml'
    $staleSubmitted = Join-Path $capture 'stale-submitted.yml'
    New-Draft $staleDraft
    New-Submitted $staleSubmitted $true
    Assert-Failure { Invoke-Recorder $staleDraft $staleSubmitted } 'last visible user turn' 'Stale dispatch turn'

    $draft = Join-Path $capture 'draft.yml'
    $submitted = Join-Path $capture 'submitted.yml'
    New-Draft $draft
    New-Submitted $submitted
    $recorded = (Invoke-Recorder $draft $submitted) | ConvertFrom-Json
    if ($recorded.status -ne 'SUBMISSION_CONFIRMED' -or
        $recorded.question_sha256 -ne $questionSha -or
        $recorded.dispatch_sha256 -ne $rendered.dispatch_sha256) {
        throw 'Bounded dispatch recorder failed'
    }
    $receipt = Join-Path $roundPath $receiptName
    $receiptObject = Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
    if ($receiptObject.schema -ne 'hmasd.browser_pro_submission.v2' -or
        $receiptObject.dispatch_sha256 -ne $rendered.dispatch_sha256) {
        throw 'Bounded dispatch v2 receipt mismatch'
    }
    $saved = [IO.File]::ReadAllBytes($receipt)
    $receiptObject.dispatch_sha256 = '0' * 64
    Write-Utf8 $receipt (($receiptObject | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'does not match|dispatch' 'Mutated dispatch receipt'
    [IO.File]::WriteAllBytes($receipt, $saved)
    $legacyReceipt = $utf8.GetString($saved) | ConvertFrom-Json
    $legacyReceipt.schema = 'hmasd.browser_pro_submission.v1'
    $legacyReceipt.PSObject.Properties.Remove('dispatch_sha256')
    Write-Utf8 $receipt (($legacyReceipt | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'does not match' 'Active legacy v1 receipt'
    [IO.File]::WriteAllBytes($receipt, $saved)
    $wrongStageReceipt = $utf8.GetString($saved) | ConvertFrom-Json
    $wrongStageReceipt.stage_commit = '3' * 40
    Write-Utf8 $receipt (($wrongStageReceipt | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'expected identity|stage' 'Receipt stage mutation'
    [IO.File]::WriteAllBytes($receipt, $saved)
    $wrongEvidenceReceipt = $utf8.GetString($saved) | ConvertFrom-Json
    $wrongEvidenceReceipt.evidence_commit = '4' * 40
    Write-Utf8 $receipt (($wrongEvidenceReceipt | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'expected identity|evidence' 'Receipt evidence mutation'
    [IO.File]::WriteAllBytes($receipt, $saved)
    $wrongConversationReceipt = $utf8.GetString($saved) | ConvertFrom-Json
    $wrongConversationReceipt.conversation_url = 'https://chatgpt.com/c/other-conversation'
    Write-Utf8 $receipt (($wrongConversationReceipt | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'expected identity|conversation' 'Receipt conversation mutation'
    [IO.File]::WriteAllBytes($receipt, $saved)
    $coherentReceipt = $utf8.GetString($saved) | ConvertFrom-Json
    $coherentReceipt.stage_commit = '5' * 40
    $coherentReceipt.repository = 'other-owner/other-repo'
    $coherentReceipt.review_branch = 'other-branch'
    $coherentDispatch = "HMASD_BP_D1 repo=$($coherentReceipt.repository) b=$($coherentReceipt.review_branch) stage=$($coherentReceipt.stage_commit) q=$questionSha round=$roundId file=$questionName Read via GitHub connector; follow fully; no upload/code/compute."
    $coherentReceipt.dispatch_sha256 = Get-Sha256 $utf8.GetBytes($coherentDispatch)
    Write-Utf8 $receipt (($coherentReceipt | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'expected identity|stage|repository|branch' 'Coherent receipt identity mutation'
    [IO.File]::WriteAllBytes($receipt, $saved)
    $resumed = (Invoke-ValidatorExpected) | ConvertFrom-Json
    if ($resumed.status -ne 'RESUME_SUBMITTED') {
        throw 'Exact trusted receipt identity did not resume'
    }
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $repoFixture } 'expected identity|trusted tuple' 'Missing expected receipt identity'

    Write-Output 'HMASD_BROWSER_PRO_DISPATCH_CONTRACT_OK mode=bounded_single_line no_upload=true timeout_retry=forbidden'
} finally {
    if (Test-Path -LiteralPath $fixture) { Remove-Item -LiteralPath $fixture -Recurse -Force }
}
