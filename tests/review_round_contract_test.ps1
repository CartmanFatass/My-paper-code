[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$utf8 = [Text.UTF8Encoding]::new($false)
$validator = Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1'
$recorder = Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1'
$archiver = Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1'
$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
$exchange = Get-Content (Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/SKILL.md') -Raw
$reviewRound = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$registryRaw = Get-Content (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') -Raw
$registry = $registryRaw | ConvertFrom-Json
$mcp = Get-Content (Join-Path $repo '.omp/mcp.json') -Raw | ConvertFrom-Json

function Write-Utf8 { param([string]$Path, [string]$Content)
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path)) | Out-Null
    [IO.File]::WriteAllText($Path, $Content, $utf8)
}
function Get-Sha256 { param([string]$Content)
    $h = [Security.Cryptography.SHA256]::Create()
    try { -join @($h.ComputeHash($utf8.GetBytes($Content)) | ForEach-Object { $_.ToString('x2') }) }
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

$serverKeys = @($mcp.mcpServers.PSObject.Properties.Name)
$server = $mcp.mcpServers.'browsermcp-pro'
if ((Compare-Object @('browsermcp-pro') $serverKeys) -or $server.type -ne 'stdio' -or
    $server.command -ne 'npx' -or @($server.args).Count -ne 2 -or
    $server.args[0] -ne '-y' -or $server.args[1] -ne '@browsermcp/mcp@0.1.3' -or
    $server.timeout -ne 120000) { throw 'Pinned singular BrowserMCP server changed' }
if (-not (Test-Path $boundaryVerifier -PathType Leaf)) { throw 'Pushed-boundary verifier was removed' }
if ($registry.schema_version -ne 31 -or
    $registry.round_controller.kind -ne 'active_controller_owned_browsermcp_state_machine' -or
    $registry.exchange_contract.server_package -ne '@browsermcp/mcp@0.1.3' -or
    $registry.exchange_contract.evidence_transport -ne 'github_connector' -or
    $registry.exchange_contract.repository -ne 'CartmanFatass/My-paper-code' -or
    $registry.exchange_contract.review_branch -ne 'Claude' -or
    $registry.exchange_contract.connection_state -ne 'LIVE_PREFLIGHT_REQUIRED_EVERY_ROUND' -or
    $registry.exchange_contract.receipt_schema -ne 'hmasd.browser_pro_submission.v1' -or
    $registry.exchange_contract.wait_chunk_seconds -ne 20 -or
    $registry.exchange_contract.fallback -ne 'none' -or
    $registry.reviewers.open_divergent.url -ne 'https://chatgpt.com/c/6a61d27c-9278-83e8-ae96-c65c1b52d207' -or
    $registry.reviewers.open_divergent.expected_model_ui -ne 'Pro' -or
    $null -ne $registry.exchange_contract.PSObject.Properties['completion_monitor']) {
    throw 'BrowserMCP review registry mismatch'
}
$states = @('VALIDATED','RECONCILED_IDLE','DRAFT_CONFIRMED','SUBMISSION_CONFIRMED','GENERATING','STABLE_TWICE','ARCHIVED')
if (Compare-Object $states @($registry.exchange_contract.state_machine)) { throw 'Registry state machine mismatch' }
foreach ($required in @('30-second timeout', '20-second', 'browser_type', 'browser_press_key',
    '`Enter`', 'immediately preceding fresh snapshot', 'Never blind retry', '`Send`',
    '`Stop answering`', '`Answer now`', '`Copy response`', 'record_browser_pro_submission.ps1',
    'two distinct temporary BrowserMCP', 'substantive fenced plaintext block',
    'live preflight')) {
    if (-not $exchange.Contains($required)) { throw "Browser exchange missing state-machine rule: $required" }
}
foreach ($required in @('19_BROWSER_PRO_SUBMISSION.json', 'HMASD_BROWSER_PRO_QUESTION_V1',
    'HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN', 'fenced `text` block',
    'record_browser_pro_submission.ps1', 'archive_browser_pro_raw.ps1',
    'requires a live', 'no completion observer')) {
    if (-not $reviewRound.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($forbidden in @('hmasd-pro-monitor', 'hmasd-pro-monitor-luna')) {
    if ($exchange.Contains($forbidden) -or $reviewRound.Contains($forbidden) -or $registryRaw.Contains($forbidden)) {
        throw "Removed completion-agent route remains: $forbidden"
    }
    if (Test-Path (Join-Path $repo ".omp/agents/$forbidden.md")) { throw "Removed profile remains: $forbidden" }
}

$fixtureContainer = Join-Path ([IO.Path]::GetTempPath()) ('hmasd-browser-pro-' + [Guid]::NewGuid().ToString('N'))
$fixtureRepo = Join-Path $fixtureContainer 'source'
$captureRoot = Join-Path $fixtureContainer 'captures'
$roundId = 'fixture_round'
$roundRelative = "docs/external-review/rounds/$roundId"
$roundPath = Join-Path $fixtureRepo $roundRelative
$questionName = '20_PRO_OPEN_QUESTION.md'
$receiptName = '19_BROWSER_PRO_SUBMISSION.json'
$rawName = '21_PRO_OPEN_RAW.md'
$stage = '1111111111111111111111111111111111111111'
$evidence = '2222222222222222222222222222222222222222'
$conversation = 'https://chatgpt.com/c/fixture-conversation'
function Assert-Removed { param([string[]]$Paths, [string]$Label)
    foreach ($path in $Paths) { if (Test-Path -LiteralPath $path) { throw "$Label did not delete accepted snapshot: $path" } }
}
try {
    [IO.Directory]::CreateDirectory($roundPath) | Out-Null
    [IO.Directory]::CreateDirectory($captureRoot) | Out-Null
    Write-Utf8 (Join-Path $roundPath '01_SHARED_SOURCE_MANIFEST.md') "# Fixture manifest`n"
    $bodyLines = @(
        'Read the pushed fixture evidence through the GitHub connector.',
        'Return no substantive text outside exactly one fenced text block.',
        'The first and last block lines must be the supplied response markers.')
    $body = ($bodyLines -join "`n") + "`n"
    $digest = Get-Sha256 $body
    $marker = "HMASD_BROWSER_PRO_QUESTION_V1 round=$roundId body_sha256=$digest"
    Write-Utf8 (Join-Path $roundPath $questionName) "$marker`n`n$body"

    function New-DraftSnapshot { param([string]$Path, [string]$Mode = 'exact')
        $paragraphs = if ($Mode -eq 'marker_only') {
            "    - paragraph: `"$marker`""
        } elseif ($Mode -eq 'wrong_body') {
            "    - paragraph: `"$marker`"`n    - paragraph`n    - paragraph: Wrong body"
        } else {
            "    - paragraph: `"$marker`"`n    - paragraph`n" +
                (($bodyLines | ForEach-Object { "    - paragraph: $_" }) -join "`n")
        }
        Write-Utf8 $Path "- main [ref=draft]:`n  - textbox `"Message ChatGPT`" [ref=composer]:`n$paragraphs`n"
    }
    function New-SubmittedSnapshot { param([string]$Path, [bool]$Stale = $false)
        $later = if ($Stale) {
            "`n  - article [ref=later]:`n    - heading `"You said:`"`n    - paragraph: Later unrelated question"
        } else { '' }
        Write-Utf8 $Path "- main [ref=submitted]:`n  - article [ref=user]:`n    - heading `"You said:`"`n    - paragraph: $marker$later`n  - textbox `"Message ChatGPT`" [ref=composer]:`n"
    }
    function Invoke-Recorder { param([string]$Draft, [string]$Submitted)
        & $recorder -RoundPath $roundRelative -QuestionPath $questionName -ReceiptPath $receiptName `
            -RawPath $rawName -DraftSnapshotPath $Draft -SubmittedSnapshotPath $Submitted `
            -StageCommit $stage -EvidenceCommit $evidence -Repository 'fixture-owner/fixture-repo' `
            -ReviewBranch 'Claude' -ConversationUrl $conversation -RepoRoot $fixtureRepo
    }

    $ready = (& $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($ready.status -ne 'READY_TO_SUBMIT' -or $ready.question_sha256 -ne $digest) { throw 'READY_TO_SUBMIT fixture failed' }
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath '../20_PRO_OPEN_QUESTION.md' `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo } 'canonical basename' 'Question traversal'

    foreach ($mode in @('marker_only','wrong_body')) {
        $draft = Join-Path $captureRoot "draft-$mode.yml"
        $submitted = Join-Path $captureRoot "submitted-$mode.yml"
        New-DraftSnapshot $draft $mode
        New-SubmittedSnapshot $submitted
        Assert-Failure { Invoke-Recorder $draft $submitted } 'does not byte-match' "Draft $mode"
        Assert-Removed @($draft,$submitted) "Draft $mode"
    }
    $draft = Join-Path $captureRoot 'draft-stale.yml'
    $submitted = Join-Path $captureRoot 'submitted-stale.yml'
    New-DraftSnapshot $draft
    New-SubmittedSnapshot $submitted $true
    Assert-Failure { Invoke-Recorder $draft $submitted } 'last visible user turn' 'Stale submitted marker'
    Assert-Removed @($draft,$submitted) 'Stale submitted marker'

    $repoDraft = Join-Path $fixtureRepo 'unsafe-draft.yml'
    $safeSubmitted = Join-Path $captureRoot 'safe-submitted.yml'
    Write-Utf8 $repoDraft 'unsafe'
    New-SubmittedSnapshot $safeSubmitted
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo `
        -SnapshotPaths @($repoDraft,$safeSubmitted) } 'beneath RepoRoot' 'Repository snapshot privacy'
    Remove-Item $repoDraft,$safeSubmitted -Force

    $draft = Join-Path $captureRoot 'draft-success.yml'
    $submitted = Join-Path $captureRoot 'submitted-success.yml'
    New-DraftSnapshot $draft
    New-SubmittedSnapshot $submitted
    $recorded = (Invoke-Recorder $draft $submitted) | ConvertFrom-Json
    Assert-Removed @($draft,$submitted) 'Successful recorder'
    if ($recorded.status -ne 'SUBMISSION_CONFIRMED' -or $recorded.question_sha256 -ne $digest) { throw 'Submission recorder failed' }
    $receiptFile = Join-Path $roundPath $receiptName
    $receiptBytes = [IO.File]::ReadAllBytes($receiptFile)

    $draft = Join-Path $captureRoot 'draft-no-clobber.yml'
    $submitted = Join-Path $captureRoot 'submitted-no-clobber.yml'
    New-DraftSnapshot $draft
    New-SubmittedSnapshot $submitted
    Assert-Failure { Invoke-Recorder $draft $submitted } 'cannot be recorded from state RESUME_SUBMITTED' 'Receipt no-clobber'
    Assert-Removed @($draft,$submitted) 'Receipt no-clobber'
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($receiptFile)) -cne [Convert]::ToBase64String($receiptBytes)) {
        throw 'Receipt no-clobber rerun changed bytes'
    }
    $resume = (& $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($resume.status -ne 'RESUME_SUBMITTED') { throw 'RESUME_SUBMITTED fixture failed' }
    Write-Utf8 $receiptFile '{bad json'
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo } 'Malformed Browser Pro submission receipt' 'Malformed receipt'
    [IO.File]::WriteAllBytes($receiptFile, $receiptBytes)
    $mismatch = ([Text.Encoding]::UTF8.GetString($receiptBytes) | ConvertFrom-Json)
    $mismatch.question_sha256 = '0' * 64
    Write-Utf8 $receiptFile (($mismatch | ConvertTo-Json) + "`n")
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo } 'does not match round and question digest' 'Mismatched receipt'
    [IO.File]::WriteAllBytes($receiptFile, $receiptBytes)

    $begin = "HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN round=$roundId question_sha256=$digest"
    $end = "HMASD_BROWSER_PRO_RESPONSE_V1_END round=$roundId question_sha256=$digest"
    function New-ResponseSnapshot {
        param([string]$Path, [string]$Ref, [string]$Content = 'Natural Pro response',
            [string]$EndMarker = $end, [string]$Extra = '', [bool]$SecondBlock = $false)
        $second = if ($SecondBlock) { "`n      - code [ref=second-$Ref]: 'another substantive block'" } else { '' }
        Write-Utf8 $Path @"
- main [ref=page-$Ref]:
  - article [ref=user-$Ref]:
    - heading "You said:"
    - paragraph: $marker
  - article [ref=assistant-$Ref]:
    - heading "ChatGPT said:"
    - group [ref=group-$Ref]:
      - button "Worked for 1m 2s" [ref=worked-$Ref]
      - button "Copy code" [ref=copy-$Ref]
      - code [ref=code-$Ref]:
        - text: |-
            $begin
            $Content
            $EndMarker$second
$Extra
    - group "Response actions" [ref=actions-$Ref]:
      - button "Good response" [ref=good-$Ref]
  - paragraph: ChatGPT can make mistakes. Check important info.
  - textbox "Message ChatGPT" [ref=composer-$Ref]:
"@
    }
    function Set-StableTimes { param([string]$One, [string]$Two, [int]$Seconds = 10)
        $start = [DateTime]::UtcNow.AddMinutes(-1)
        [IO.File]::SetLastWriteTimeUtc($One, $start)
        [IO.File]::SetLastWriteTimeUtc($Two, $start.AddSeconds($Seconds))
    }
    function Invoke-Archive { param([string]$One, [string]$Two)
        & $archiver -RoundPath $roundRelative -ReceiptPath $receiptName -RawPath $rawName `
            -SnapshotPathOne $One -SnapshotPathTwo $Two -RepoRoot $fixtureRepo
    }
    function Invoke-ArchiveNegative {
        param([string]$Name, [string]$Pattern, [string]$Extra = '', [string]$ContentOne = 'Natural Pro response',
            [string]$ContentTwo = 'Natural Pro response', [string]$EndOne = $end, [string]$EndTwo = $end,
            [bool]$SecondBlock = $false)
        $one = Join-Path $captureRoot "$Name-one.yml"
        $two = Join-Path $captureRoot "$Name-two.yml"
        New-ResponseSnapshot $one "$Name-1" $ContentOne $EndOne $Extra $SecondBlock
        New-ResponseSnapshot $two "$Name-2" $ContentTwo $EndTwo $Extra $SecondBlock
        Set-StableTimes $one $two
        Assert-Failure { Invoke-Archive $one $two } $Pattern $Name
        Assert-Removed @($one,$two) $Name
    }

    $same = Join-Path $captureRoot 'same.yml'
    New-ResponseSnapshot $same 'same'
    Assert-Failure { Invoke-Archive $same $same } 'distinct files' 'Same stable snapshot'
    Remove-Item $same -Force
    $hardSource = Join-Path $captureRoot 'hard-source.yml'
    $hardLink = Join-Path $captureRoot 'hard-link.yml'
    New-ResponseSnapshot $hardSource 'hard'
    New-Item -ItemType HardLink -Path $hardLink -Target $hardSource | Out-Null
    Assert-Failure { Invoke-Archive $hardSource $hardLink } 'distinct file identities' 'Hard-link snapshot identity'
    Remove-Item $hardSource,$hardLink -Force
    $closeOne = Join-Path $captureRoot 'close-one.yml'; $closeTwo = Join-Path $captureRoot 'close-two.yml'
    New-ResponseSnapshot $closeOne 'close-1'; New-ResponseSnapshot $closeTwo 'close-2'; Set-StableTimes $closeOne $closeTwo 9
    Assert-Failure { Invoke-Archive $closeOne $closeTwo } 'at least ten seconds' 'Too-close snapshots'
    Assert-Removed @($closeOne,$closeTwo) 'Too-close snapshots'

    Invoke-ArchiveNegative 'truncated' 'wrong, missing, or truncated' '' 'Natural Pro response' 'Natural Pro response' 'TRUNCATED' 'TRUNCATED'
    Invoke-ArchiveNegative 'mismatch' 'differs across' '' 'First response' 'Different response'
    Invoke-ArchiveNegative 'extra-heading' 'forbidden extra ARIA node' '    - heading "Unexpected response heading"'
    Invoke-ArchiveNegative 'second-block' 'exactly one substantive code block' '' 'Natural Pro response' 'Natural Pro response' $end $end $true
    Invoke-ArchiveNegative 'wrong-marker' 'wrong, missing, or truncated' '' 'Natural Pro response' 'Natural Pro response' `
        "HMASD_BROWSER_PRO_RESPONSE_V1_END round=wrong question_sha256=$digest" `
        "HMASD_BROWSER_PRO_RESPONSE_V1_END round=wrong question_sha256=$digest"
    Invoke-ArchiveNegative 'arbitrary-button' 'forbidden extra ARIA node' '      - button "Read aloud" [ref=bad]'
    Invoke-ArchiveNegative 'named-group' 'forbidden extra ARIA node' '    - group "Injected group" [ref=bad]'
    Invoke-ArchiveNegative 'named-img' 'forbidden extra ARIA node' '    - img "Injected image" [ref=bad]'

    $one = Join-Path $captureRoot 'response-one.yml'
    $two = Join-Path $captureRoot 'response-two.yml'
    $ariaLookingContent = "Natural Pro response`n            - heading `"ChatGPT said:`" [level=4]`n            - group `"Response actions`""
    New-ResponseSnapshot $one '101' $ariaLookingContent
    New-ResponseSnapshot $two '909' $ariaLookingContent
    Set-StableTimes $one $two
    $archived = (Invoke-Archive $one $two) | ConvertFrom-Json
    Assert-Removed @($one,$two) 'Successful archiver'
    $expectedRaw = "Natural Pro response`n- heading `"ChatGPT said:`" [level=4]`n- group `"Response actions`"`n"
    if ($archived.status -ne 'ARCHIVED' -or
        [IO.File]::ReadAllText((Join-Path $roundPath $rawName), $utf8) -cne $expectedRaw -or
        $archived.snapshot_one_sha256 -cne $archived.snapshot_two_sha256) { throw 'Exact two-snapshot raw archival failed' }
    $rawFile = Join-Path $roundPath $rawName
    $rawBytes = [IO.File]::ReadAllBytes($rawFile)
    Assert-Failure { Invoke-Archive 'missing-one' 'missing-two' } 'cannot be archived from state ALREADY_ARCHIVED' 'Immutable raw'
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($rawFile)) -cne [Convert]::ToBase64String($rawBytes)) {
        throw 'Immutable raw changed after rejected overwrite'
    }
    $already = (& $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($already.status -ne 'ALREADY_ARCHIVED') { throw 'ALREADY_ARCHIVED fixture failed' }
    Remove-Item $rawFile -Force
    [IO.Directory]::CreateDirectory($rawFile) | Out-Null
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo } 'occupied by a non-file' 'Non-file raw occupation'
    Remove-Item $rawFile -Recurse -Force
    [IO.File]::WriteAllBytes($rawFile, $rawBytes)
    Write-Output 'HMASD_BROWSER_PRO_FIXTURE_SEQUENCE READY_TO_SUBMIT -> SUBMISSION_CONFIRMED -> RESUME_SUBMITTED -> ARCHIVED -> ALREADY_ARCHIVED'
} finally {
    if (Test-Path $fixtureContainer) { Remove-Item $fixtureContainer -Recurse -Force }
}
Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK state_machine=restart_safe receipt=no_clobber capture=stable_twice'
