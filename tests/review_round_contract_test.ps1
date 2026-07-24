[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$utf8 = [Text.UTF8Encoding]::new($false)
$validator = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1'
$recorder = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/record_browser_pro_submission.ps1'
$renderer = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/render_browser_pro_dispatch.ps1'
$archiver = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1'
$receiptLockModule = Join-Path $repo '.omp/skills/hmasd-browser-pro-exchange/scripts/browser_pro_receipt_lock.psm1'
if (-not (Test-Path -LiteralPath $receiptLockModule -PathType Leaf)) {
    throw 'Browser Pro receipt lock module is missing; validated receipt bytes can change before raw publication'
}
Import-Module $receiptLockModule -Force
$boundaryVerifier = Join-Path $repo '.omp/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
$exchangeArchive = Get-Content (Join-Path $repo '.omp/legacy/review-round/BROWSER_PRO_EXCHANGE_DISABLED.md') -Raw
$reviewRound = Get-Content (Join-Path $repo '.omp/skills/hmasd-review-round/SKILL.md') -Raw
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
function Get-ByteSha256 { param([byte[]]$Bytes)
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

$serverKeys = @($mcp.mcpServers.PSObject.Properties.Name)
$server = $mcp.mcpServers.'browsermcp-pro'
if ((Compare-Object @('browsermcp-pro') $serverKeys) -or $server.type -ne 'stdio' -or
    $server.command -ne 'powershell.exe' -or @($server.args).Count -ne 5 -or
    $server.args[0] -ne '-NoProfile' -or $server.args[1] -ne '-ExecutionPolicy' -or
    $server.args[2] -ne 'Bypass' -or $server.args[3] -ne '-File' -or
    $server.args[4] -ne '.omp/browsermcp-direct/start_browsermcp_direct.ps1' -or
    $server.timeout -ne 120000) { throw 'Controller-direct BrowserMCP server changed' }
if (-not (Test-Path $boundaryVerifier -PathType Leaf)) { throw 'Pushed-boundary verifier was removed' }
if ($registry.schema_version -ne 37 -or
    $registry.round_controller.kind -ne 'controller_intake_with_local_exchange_review' -or
    $registry.exchange_contract.transport_exploration_enabled -or
    $registry.exchange_contract.status -ne 'ACTIVE_LUNA_HIGH_EXCHANGE_REVIEW_AGENT' -or
    $registry.exchange_contract.automation_skill_enabled -or
    $registry.exchange_contract.automation_skill_archive -ne '.omp/legacy/review-round/BROWSER_PRO_EXCHANGE_DISABLED.md' -or
    $registry.exchange_contract.operator_agent -ne 'hmasd-exchange-review' -or
    $registry.exchange_contract.operator_profile -ne '.omp/agents/hmasd-exchange-review.md' -or
    $registry.exchange_contract.experience_recorder -ne 'hmasd-review-scout' -or
    $registry.exchange_contract.experience_path -ne '.omp/review_scout/EXPERIENCE.md' -or
    $registry.exchange_contract.server_package -ne '@browsermcp/mcp@0.1.3' -or
    $registry.exchange_contract.evidence_transport -ne 'github_connector' -or
    $registry.exchange_contract.repository -ne 'CartmanFatass/My-paper-code' -or
    $registry.exchange_contract.review_branch -ne 'Claude' -or
    $registry.exchange_contract.response_capture -ne 'page_copy_response_button' -or
    $registry.exchange_contract.keyboard_copy_allowed -or
    $registry.exchange_contract.controller_contact -ne 'assignment_then_direct_controller_intake' -or
    $registry.exchange_contract.connection_state -ne 'REGISTERED_TAB_PREFLIGHT_REQUIRED_EVERY_ASSIGNMENT' -or
    $registry.exchange_contract.authenticated_registered_tab_prerequisite -ne 'ONE_TIME_ENVIRONMENTAL_NOT_ROUTINE_STEP' -or
    $registry.exchange_contract.routine_human_interaction_allowed -or
    $registry.exchange_contract.dispatch_marker -ne 'HMASD_BP_D1' -or
    $registry.exchange_contract.dispatch_max_utf16_code_units -ne 352 -or
    $registry.exchange_contract.dispatch_line_breaks_allowed -or
    $registry.exchange_contract.file_upload_allowed -or
    $registry.exchange_contract.full_question_browser_type_allowed -or
    $registry.exchange_contract.receipt_schema -ne 'hmasd.browser_pro_submission.v2' -or
    $registry.exchange_contract.execution_order -ne 'validate_identity_then_verify_pushed_boundary_then_preflight_then_clipboard_paste_dispatch_then_separate_enter_then_receipt_then_bounded_observe_then_two_stable_snapshots_then_click_copy_response_then_archive_no_clobber' -or
    $registry.exchange_contract.fallback -ne 'none' -or
    $registry.reviewers.open_divergent.url -ne 'https://chatgpt.com/c/6a61d27c-9278-83e8-ae96-c65c1b52d207' -or
    $registry.reviewers.open_divergent.expected_model_ui -ne 'Pro' -or
    $registry.reviewers.open_divergent.transport -ne 'hmasd-exchange-review' -or
    $registry.reviewers.open_divergent.connection_state -ne 'REGISTERED_TAB_PREFLIGHT_REQUIRED_EVERY_ASSIGNMENT') {
    throw 'Controller-direct BrowserMCP exchange-review registry mismatch'
}
foreach ($removedField in @('enabled','role_skill','skill_enabled','state_machine',
    'browser_type_actions','enter_action','type_timeout_policy','wait_chunk_seconds',
    'terminal_order')) {
    if ($null -ne $registry.exchange_contract.PSObject.Properties[$removedField]) {
        throw "Removed exchange-contract field remains: $removedField"
    }
}
foreach ($required in @('Disabled by user directive', 'explicit user',
    'Multiple stable, fully automated')) {
    if (-not $exchangeArchive.Contains($required)) { throw "Legacy browser exchange marker missing: $required" }
}
foreach ($required in @('Transport execution boundary', 'hmasd-exchange-review',
    'hmasd-review-scout', 'Routine human recovery', 'Luna-high',
    'Copy response', 'one-time environmental prerequisite')) {
    if (-not $reviewRound.Contains($required)) { throw "Review-round exchange boundary missing: $required" }
}
foreach ($forbidden in @('$hmasd-browser-pro-exchange','browser_type',
    'browser_press_key','then_user_connect','Skill-owned validate',
    'runs the exchange Skill')) {
    if ($reviewRound.Contains($forbidden)) { throw "Active review-round reactivates transport: $forbidden" }
}
foreach ($required in @('19_BROWSER_PRO_SUBMISSION.json',
    'HMASD_BROWSER_PRO_QUESTION_V1', 'HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN',
    'fenced `text` block', 'validate_browser_pro_round.ps1',
    'render_browser_pro_dispatch.ps1', 'record_browser_pro_submission.ps1',
    'archive_browser_pro_raw.ps1', 'verify_pro_review_boundary.ps1',
    'Do not put any triple-backtick sequence or nested fenced block between the response markers.',
    'plain or indented text', 'no-clobber')) {
    if (-not $reviewRound.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($forbidden in @('hmasd-pro-monitor', 'hmasd-pro-monitor-luna')) {
    if ($exchangeArchive.Contains($forbidden) -or $reviewRound.Contains($forbidden) -or $registryRaw.Contains($forbidden)) {
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
$repository = 'fixture-owner/fixture-repo'
$branch = 'Claude'
$requiredNoNestedFenceInstruction = 'Do not put any triple-backtick sequence or nested fenced block between the response markers.'
function Assert-Removed { param([string[]]$Paths, [string]$Label)
    foreach ($path in $Paths) { if (Test-Path -LiteralPath $path) { throw "$Label did not delete accepted temporary input: $path" } }
}
try {
    [IO.Directory]::CreateDirectory($roundPath) | Out-Null
    [IO.Directory]::CreateDirectory($captureRoot) | Out-Null
    Write-Utf8 (Join-Path $roundPath '01_SHARED_SOURCE_MANIFEST.md') "# Fixture manifest`n"
    $bodyLines = @(
        'Read the pushed fixture evidence through the GitHub connector.',
        'Return no substantive text outside exactly one fenced text block.',
        $requiredNoNestedFenceInstruction,
        'The first and last block lines must be the supplied response markers.')
    $body = ($bodyLines -join "`n") + "`n"
    $digest = Get-Sha256 $body
    $marker = "HMASD_BROWSER_PRO_QUESTION_V1 round=$roundId body_sha256=$digest"
    Write-Utf8 (Join-Path $roundPath $questionName) "$marker`n`n$body"
    $bodyWithoutRequiredInstruction = (@($bodyLines | Where-Object {
        -not $_.Equals($requiredNoNestedFenceInstruction, [StringComparison]::Ordinal)
    }) -join "`n") + "`n"
    $digestWithoutRequiredInstruction = Get-Sha256 $bodyWithoutRequiredInstruction
    $markerWithoutRequiredInstruction = "HMASD_BROWSER_PRO_QUESTION_V1 round=$roundId body_sha256=$digestWithoutRequiredInstruction"
    Write-Utf8 (Join-Path $roundPath $questionName) "$markerWithoutRequiredInstruction`n`n$bodyWithoutRequiredInstruction"
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo } `
        'exact required no-nested-fence instruction' 'Digest-correct question missing required no-nested-fence instruction'
    Write-Utf8 (Join-Path $roundPath $questionName) "$marker`n`n$body"
    $rendered = (& $renderer -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -StageCommit $stage -EvidenceCommit $evidence `
        -Repository $repository -ReviewBranch $branch -RepoRoot $fixtureRepo) | ConvertFrom-Json
    $dispatch = $utf8.GetString([Convert]::FromBase64String([string]$rendered.dispatch_base64))
    $dispatchScalar = $dispatch | ConvertTo-Json -Compress

    function New-DraftSnapshot { param([string]$Path, [string]$Mode = 'exact')
        $value = if ($Mode -eq 'legacy_question') {
            ("$marker`n`n$body").TrimEnd("`n")
        } elseif ($Mode -eq 'wrong_bytes') {
            $dispatch + 'x'
        } else {
            $dispatch
        }
        $scalar = $value | ConvertTo-Json -Compress
        Write-Utf8 $Path "- main [ref=draft]:`n  - textbox `"Message ChatGPT`" [ref=composer]:`n    - paragraph: $scalar`n"
    }
    function New-SubmittedSnapshot {
        param(
            [string]$Path,
            [bool]$Stale = $false,
            [string]$ComposerText = '',
            [bool]$SendPrompt = $false,
            [bool]$DirectText = $false)
        $userTurn = if ($DirectText) {
            "- main [ref=submitted]:`n  - heading `"You said:`" [level=4] [ref=user-heading]`n  - text: $dispatch"
        } else {
            "- main [ref=submitted]:`n  - article [ref=user]:`n    - heading `"You said:`"`n    - paragraph: $dispatchScalar"
        }
        $later = if ($Stale) {
            "`n  - article [ref=later]:`n    - heading `"You said:`"`n    - paragraph: Later unrelated question"
        } else { '' }
        $composerParagraph = if ($ComposerText.Length -gt 0) {
            $composerScalar = $ComposerText | ConvertTo-Json -Compress
            "`n    - paragraph: $composerScalar"
        } else { '' }
        $sendButton = if ($SendPrompt) { "`n  - button `"Send prompt`" [ref=send]" } else { '' }
        Write-Utf8 $Path "$userTurn$later`n  - textbox `"Message ChatGPT`" [ref=composer]:$composerParagraph$sendButton`n"
    }
    function Invoke-Recorder { param([string]$Draft, [string]$Submitted)
        & $recorder -RoundPath $roundRelative -QuestionPath $questionName -ReceiptPath $receiptName `
            -RawPath $rawName -DraftSnapshotPath $Draft -SubmittedSnapshotPath $Submitted `
            -StageCommit $stage -EvidenceCommit $evidence -Repository $repository `
            -ReviewBranch $branch -ConversationUrl $conversation -RepoRoot $fixtureRepo
    }
    function Invoke-ValidatorExpected {
        & $validator -RoundPath $roundRelative -QuestionPath $questionName `
            -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo `
            -ExpectedStageCommit $stage -ExpectedEvidenceCommit $evidence `
            -ExpectedRepository $repository -ExpectedReviewBranch $branch `
            -ExpectedConversationUrl $conversation -ExpectedModel 'Pro'
    }

    $ready = (& $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($ready.status -ne 'READY_TO_SUBMIT' -or $ready.question_sha256 -ne $digest -or
        $null -ne $ready.receipt_sha256) { throw 'READY_TO_SUBMIT fixture failed' }
    Assert-Failure { & $validator -RoundPath $roundRelative -QuestionPath '../20_PRO_OPEN_QUESTION.md' `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo } 'canonical basename' 'Question traversal'

    foreach ($mode in @('legacy_question','wrong_bytes')) {
        $draft = Join-Path $captureRoot "draft-$mode.yml"
        $submitted = Join-Path $captureRoot "submitted-$mode.yml"
        New-DraftSnapshot $draft $mode
        New-SubmittedSnapshot $submitted
        Assert-Failure { Invoke-Recorder $draft $submitted } 'dispatch|does not byte-match' "Draft $mode"
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

    $draft = Join-Path $captureRoot 'draft-literal-follow-up.yml'
    $submitted = Join-Path $captureRoot 'submitted-literal-follow-up.yml'
    New-DraftSnapshot $draft
    New-SubmittedSnapshot -Path $submitted -ComposerText 'Follow up' -SendPrompt $true
    Assert-Failure { Invoke-Recorder $draft $submitted } 'submitted composer is not empty' 'Literal Follow up draft'
    Assert-Removed @($draft,$submitted) 'Literal Follow up draft'

    $draft = Join-Path $captureRoot 'draft-success.yml'
    $submitted = Join-Path $captureRoot 'submitted-success.yml'
    New-DraftSnapshot $draft
    New-SubmittedSnapshot -Path $submitted -ComposerText 'Follow up' -DirectText $true
    $recorded = (Invoke-Recorder $draft $submitted) | ConvertFrom-Json
    Assert-Removed @($draft,$submitted) 'Successful recorder'
    if ($recorded.status -ne 'SUBMISSION_CONFIRMED' -or $recorded.question_sha256 -ne $digest -or
        $recorded.dispatch_sha256 -ne $rendered.dispatch_sha256) { throw 'Submission recorder failed' }
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
    $resume = (Invoke-ValidatorExpected) | ConvertFrom-Json
    if ($resume.status -ne 'RESUME_SUBMITTED') { throw 'RESUME_SUBMITTED fixture failed' }
    $receiptDigest = Get-ByteSha256 $receiptBytes
    if ($resume.status -ne 'RESUME_SUBMITTED' -or $resume.receipt_sha256 -cne $receiptDigest) {
        throw 'RESUME_SUBMITTED receipt digest does not match the exact receipt bytes'
    }
    $lockedRenameFile = Join-Path $fixtureContainer 'receipt-lock-rename.json'
    $lockedBase64 = Invoke-HmasdBrowserProReceiptLock -ReceiptPath $receiptFile `
        -ExpectedSha256 $receiptDigest -Action {
            param([byte[]]$LockedReceiptBytes)
            $writerDenied = $false
            $writer = $null
            try {
                $writer = [IO.FileStream]::new(
                    $receiptFile, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite)
            } catch [IO.IOException] {
                $writerDenied = $true
            } finally {
                if ($null -ne $writer) { $writer.Dispose() }
            }
            if (-not $writerDenied) { throw 'Receipt lock allowed a concurrent writer handle' }
            $deleteDenied = $false
            try {
                [IO.File]::Delete($receiptFile)
            } catch [IO.IOException] {
                $deleteDenied = $true
            }
            if (-not $deleteDenied) { throw 'Receipt lock allowed a concurrent delete' }
            $renameDenied = $false
            try {
                [IO.File]::Move($receiptFile, $lockedRenameFile)
            } catch [IO.IOException] {
                $renameDenied = $true
            }
            if (-not $renameDenied) { throw 'Receipt lock allowed a concurrent rename' }
            [Convert]::ToBase64String($LockedReceiptBytes)
        }
    if ($lockedBase64 -cne [Convert]::ToBase64String($receiptBytes)) {
        throw 'Receipt lock action did not receive the exact held receipt bytes'
    }
    Assert-Failure {
        Invoke-HmasdBrowserProReceiptLock -ReceiptPath $receiptFile `
            -ExpectedSha256 $receiptDigest -Action { throw 'Intentional receipt action failure' }
    } 'Intentional receipt action failure' 'Receipt lock action exception'
    $releasedWriter = [IO.FileStream]::new(
        $receiptFile, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite)
    $releasedWriter.Dispose()
    $wrongReceiptDigest = '0' + $receiptDigest.Substring(1)
    if ($wrongReceiptDigest -ceq $receiptDigest) {
        $wrongReceiptDigest = '1' + $receiptDigest.Substring(1)
    }
    Assert-Failure {
        Invoke-HmasdBrowserProReceiptLock -ReceiptPath $receiptFile `
            -ExpectedSha256 $wrongReceiptDigest -Action { throw 'Digest mismatch action must not run' }
    } 'changed between validation and locked archival' 'Receipt lock digest mismatch'
    $reparseTarget = Join-Path $fixtureContainer 'receipt-target'
    $reparseAncestor = Join-Path $fixtureContainer 'receipt-junction'
    $finalReparse = Join-Path $fixtureContainer 'receipt-final-junction'
    [IO.Directory]::CreateDirectory($reparseTarget) | Out-Null
    $reparseReceipt = Join-Path $reparseTarget $receiptName
    [IO.File]::WriteAllBytes($reparseReceipt, $receiptBytes)
    New-Item -ItemType Junction -Path $reparseAncestor -Target $reparseTarget | Out-Null
    New-Item -ItemType Junction -Path $finalReparse -Target $reparseTarget | Out-Null
    try {
        Assert-Failure {
            Invoke-HmasdBrowserProReceiptLock -ReceiptPath $finalReparse `
                -ExpectedSha256 $receiptDigest -Action { 'Final reparse action must not run' }
        } 'reparse' 'Receipt final reparse'
        Assert-Failure {
            Invoke-HmasdBrowserProReceiptLock -ReceiptPath (Join-Path $reparseAncestor $receiptName) `
                -ExpectedSha256 $receiptDigest -Action { 'Reparse action must not run' }
        } 'reparse|resolved.*path|canonical.*path' 'Receipt reparse ancestry'
    } finally {
        if (Test-Path -LiteralPath $finalReparse) { [IO.Directory]::Delete($finalReparse) }
        if (Test-Path -LiteralPath $reparseAncestor) { [IO.Directory]::Delete($reparseAncestor) }
        if (Test-Path -LiteralPath $reparseTarget) { Remove-Item -LiteralPath $reparseTarget -Recurse -Force }
    }
    Write-Utf8 $receiptFile '{bad json'
    Assert-Failure { Invoke-ValidatorExpected } 'Malformed Browser Pro submission receipt' 'Malformed receipt'
    [IO.File]::WriteAllBytes($receiptFile, $receiptBytes)
    $mismatch = ([Text.Encoding]::UTF8.GetString($receiptBytes) | ConvertFrom-Json)
    $mismatch.question_sha256 = '0' * 64
    Write-Utf8 $receiptFile (($mismatch | ConvertTo-Json) + "`n")
    Assert-Failure { Invoke-ValidatorExpected } 'does not match round and question digest' 'Mismatched receipt'
    [IO.File]::WriteAllBytes($receiptFile, $receiptBytes)

    $begin = "HMASD_BROWSER_PRO_RESPONSE_V1_BEGIN round=$roundId question_sha256=$digest"
    $end = "HMASD_BROWSER_PRO_RESPONSE_V1_END round=$roundId question_sha256=$digest"
    function New-ResponseSnapshot {
        param([string]$Path, [string]$Ref, [string]$Content = 'Natural Pro response',
            [string]$EndMarker = $end, [string]$Extra = '', [bool]$SecondBlock = $false,
            [bool]$Flattened = $false)
        if ($Flattened) {
            $flatContent = ([regex]::Replace($Content, '\s+', ' ')).Trim()
            Write-Utf8 $Path @"
- main [ref=page-$Ref]:
  - article [ref=user-$Ref]:
    - heading "You said:"
    - paragraph: $dispatchScalar
  - article [ref=assistant-$Ref]:
    - heading "ChatGPT said:"
    - group [ref=group-$Ref]:
      - button "Worked for 1m 2s" [ref=worked-$Ref]
      - button "Copy code" [ref=copy-$Ref]
      - code [ref=code-$Ref]: $begin $flatContent $EndMarker
    - group "Response actions" [ref=actions-$Ref]:
      - button "Good response" [ref=good-$Ref]
  - paragraph: ChatGPT can make mistakes. Check important info.
  - textbox "Message ChatGPT" [ref=composer-$Ref]:
"@
            return
        }
        $second = if ($SecondBlock) { "`n      - code [ref=second-$Ref]: 'another substantive block'" } else { '' }
        Write-Utf8 $Path @"
- main [ref=page-$Ref]:
  - article [ref=user-$Ref]:
    - heading "You said:"
    - paragraph: $dispatchScalar
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
    function New-CopiedResponse {
        param([string]$Path, [string]$Content = 'Natural Pro response',
            [string]$BeginMarker = $begin, [string]$EndMarker = $end,
            [string]$OpeningFence = '```text', [string]$ClosingFence = '```')
        Write-Utf8 $Path "$OpeningFence`n$BeginMarker`n$Content`n$EndMarker`n$ClosingFence"
    }
    function Set-StableTimes { param([string]$One, [string]$Two, [int]$Seconds = 10)
        $start = [DateTime]::UtcNow.AddMinutes(-1)
        [IO.File]::SetLastWriteTimeUtc($One, $start)
        [IO.File]::SetLastWriteTimeUtc($Two, $start.AddSeconds($Seconds))
    }
    function Invoke-Archive { param([string]$One, [string]$Two, [string]$Copy)
        & $archiver -RoundPath $roundRelative -ReceiptPath $receiptName -RawPath $rawName `
            -SnapshotPathOne $One -SnapshotPathTwo $Two -CopiedResponsePath $Copy `
            -StageCommit $stage -EvidenceCommit $evidence -Repository $repository `
            -ReviewBranch $branch -ConversationUrl $conversation -ExpectedModel 'Pro' -RepoRoot $fixtureRepo
    }
    function Invoke-ArchiveNegative {
        param([string]$Name, [string]$Pattern, [string]$Extra = '', [string]$ContentOne = 'Natural Pro response',
            [string]$ContentTwo = 'Natural Pro response', [string]$EndOne = $end, [string]$EndTwo = $end,
            [bool]$SecondBlock = $false, [string]$CopyContent = 'Natural Pro response',
            [string]$CopyBegin = $begin, [string]$CopyEnd = $end,
            [string]$CopyOpening = '```text', [string]$CopyClosing = '```')
        $one = Join-Path $captureRoot "$Name-one.yml"
        $two = Join-Path $captureRoot "$Name-two.yml"
        $copy = Join-Path $captureRoot "$Name-copy.md"
        New-ResponseSnapshot $one "$Name-1" $ContentOne $EndOne $Extra $SecondBlock
        New-ResponseSnapshot $two "$Name-2" $ContentTwo $EndTwo $Extra $SecondBlock
        New-CopiedResponse $copy $CopyContent $CopyBegin $CopyEnd $CopyOpening $CopyClosing
        Set-StableTimes $one $two
        Assert-Failure { Invoke-Archive $one $two $copy } $Pattern $Name
        Assert-Removed @($one,$two,$copy) $Name
    }

    $same = Join-Path $captureRoot 'same.yml'
    $sameCopy = Join-Path $captureRoot 'same-copy.md'
    New-ResponseSnapshot $same 'same'
    New-CopiedResponse $sameCopy
    Assert-Failure { Invoke-Archive $same $same $sameCopy } 'distinct files' 'Same stable snapshot'
    Remove-Item $same,$sameCopy -Force
    $hardSource = Join-Path $captureRoot 'hard-source.yml'
    $hardLink = Join-Path $captureRoot 'hard-link.yml'
    $hardCopy = Join-Path $captureRoot 'hard-copy.md'
    New-ResponseSnapshot $hardSource 'hard'
    New-CopiedResponse $hardCopy
    New-Item -ItemType HardLink -Path $hardLink -Target $hardSource | Out-Null
    Assert-Failure { Invoke-Archive $hardSource $hardLink $hardCopy } 'distinct file identities' 'Hard-link snapshot identity'
    Remove-Item $hardSource,$hardLink,$hardCopy -Force
    $closeOne = Join-Path $captureRoot 'close-one.yml'
    $closeTwo = Join-Path $captureRoot 'close-two.yml'
    $closeCopy = Join-Path $captureRoot 'close-copy.md'
    New-ResponseSnapshot $closeOne 'close-1'
    New-ResponseSnapshot $closeTwo 'close-2'
    New-CopiedResponse $closeCopy
    Set-StableTimes $closeOne $closeTwo 9
    Assert-Failure { Invoke-Archive $closeOne $closeTwo $closeCopy } 'at least ten seconds' 'Too-close snapshots'
    Assert-Removed @($closeOne,$closeTwo,$closeCopy) 'Too-close snapshots'

    Invoke-ArchiveNegative 'truncated' 'wrong, missing, or truncated' '' 'Natural Pro response' 'Natural Pro response' 'TRUNCATED' 'TRUNCATED'
    Invoke-ArchiveNegative 'mismatch' 'differs from the exact copied response' '' 'First response' 'Different response'
    Invoke-ArchiveNegative 'extra-heading' 'forbidden extra ARIA node' '    - heading "Unexpected response heading"'
    Invoke-ArchiveNegative 'second-block' 'exactly one substantive code block' '' 'Natural Pro response' 'Natural Pro response' $end $end $true
    Invoke-ArchiveNegative 'wrong-marker' 'wrong, missing, or truncated' '' 'Natural Pro response' 'Natural Pro response' `
        "HMASD_BROWSER_PRO_RESPONSE_V1_END round=wrong question_sha256=$digest" `
        "HMASD_BROWSER_PRO_RESPONSE_V1_END round=wrong question_sha256=$digest"
    Invoke-ArchiveNegative 'arbitrary-button' 'forbidden extra ARIA node' '      - button "Read aloud" [ref=bad]'
    Invoke-ArchiveNegative 'named-group' 'forbidden extra ARIA node' '    - group "Injected group" [ref=bad]'
    Invoke-ArchiveNegative 'named-img' 'forbidden extra ARIA node' '    - img "Injected image" [ref=bad]'
    Invoke-ArchiveNegative -Name 'copy-malformed-fence' -Pattern 'exact outer' -CopyOpening '~~~text'
    Invoke-ArchiveNegative -Name 'copy-missing-fence' -Pattern 'exact outer' -CopyClosing ''
    Invoke-ArchiveNegative -Name 'copy-marker-mismatch' -Pattern 'wrong, missing, or misplaced' `
        -CopyEnd "HMASD_BROWSER_PRO_RESPONSE_V1_END round=wrong question_sha256=$digest"
    Invoke-ArchiveNegative -Name 'copy-nested-fence' -Pattern 'nested triple-backtick' `
        -CopyContent 'Natural Pro response with ``` nested fence'
    Invoke-ArchiveNegative -Name 'copy-snapshot-mismatch' -Pattern 'differs from the exact copied response' `
        -CopyContent 'Different exact copied response'
    Invoke-ArchiveNegative -Name 'copy-empty-body' -Pattern 'content is empty' -CopyContent '   '
    $bomOne = Join-Path $captureRoot 'copy-bom-one.yml'
    $bomTwo = Join-Path $captureRoot 'copy-bom-two.yml'
    $bomCopy = Join-Path $captureRoot 'copy-bom.md'
    New-ResponseSnapshot $bomOne 'copy-bom-1'
    New-ResponseSnapshot $bomTwo 'copy-bom-2'
    $bomDocument = '```text' + "`n$begin`nNatural Pro response`n$end`n" + '```'
    [IO.File]::WriteAllText($bomCopy, $bomDocument, [Text.UTF8Encoding]::new($true))
    Set-StableTimes $bomOne $bomTwo
    Assert-Failure { Invoke-Archive $bomOne $bomTwo $bomCopy } 'UTF-8 without a BOM' 'Copied response BOM'
    Assert-Removed @($bomOne,$bomTwo,$bomCopy) 'Copied response BOM'
    $lockOne = Join-Path $captureRoot 'lock-failure-one.yml'
    $lockTwo = Join-Path $captureRoot 'lock-failure-two.yml'
    $lockCopy = Join-Path $captureRoot 'lock-failure-copy.md'
    New-ResponseSnapshot $lockOne 'lock-failure-1'
    New-ResponseSnapshot $lockTwo 'lock-failure-2'
    New-CopiedResponse $lockCopy
    Set-StableTimes $lockOne $lockTwo
    $openWriter = [IO.FileStream]::new(
        $receiptFile, [IO.FileMode]::Open, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite)
    try {
        Assert-Failure { Invoke-Archive $lockOne $lockTwo $lockCopy } 'lock/open failed' 'Receipt writer exclusion'
    } finally {
        $openWriter.Dispose()
    }
    Assert-Removed @($lockOne,$lockTwo,$lockCopy) 'Receipt writer exclusion'
    if (Test-Path -LiteralPath (Join-Path $roundPath $rawName)) {
        throw 'Receipt writer exclusion published raw before acquiring the held receipt lock'
    }

    $one = Join-Path $captureRoot 'response-one.yml'
    $two = Join-Path $captureRoot 'response-two.yml'
    $copy = Join-Path $captureRoot 'response-copy.md'
    $ariaLookingContent = "Natural Pro response`n            - heading `"ChatGPT said:`" [level=4]`n            - group `"Response actions`""
    $exactCopiedContent = "Natural Pro response`n- heading `"ChatGPT said:`" [level=4]`n- group `"Response actions`""
    New-ResponseSnapshot $one '101' $ariaLookingContent
    New-ResponseSnapshot -Path $two -Ref '909' -Content $ariaLookingContent -Flattened $true
    $copiedDocument = '```text' + "`n$begin`n$exactCopiedContent`n$end`n" + '```'
    Write-Utf8 $copy ($copiedDocument -replace "`n", "`r`n")
    Set-StableTimes $one $two
    $archived = (Invoke-Archive $one $two $copy) | ConvertFrom-Json
    Assert-Removed @($one,$two,$copy) 'Successful archiver'
    $expectedRaw = "Natural Pro response`n- heading `"ChatGPT said:`" [level=4]`n- group `"Response actions`"`n"
    if ($archived.status -ne 'ARCHIVED' -or
        [IO.File]::ReadAllText((Join-Path $roundPath $rawName), $utf8) -cne $expectedRaw -or
        $archived.snapshot_one_sha256 -cne $archived.snapshot_two_sha256) { throw 'Exact two-snapshot raw archival failed' }
    $rawFile = Join-Path $roundPath $rawName
    $rawBytes = [IO.File]::ReadAllBytes($rawFile)
    Assert-Failure { Invoke-Archive 'missing-one' 'missing-two' 'missing-copy' } 'cannot be archived from state ALREADY_ARCHIVED' 'Immutable raw'
    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($rawFile)) -cne [Convert]::ToBase64String($rawBytes)) {
        throw 'Immutable raw changed after rejected overwrite'
    }
    $already = (& $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($already.status -ne 'ALREADY_ARCHIVED') { throw 'ALREADY_ARCHIVED fixture failed' }
    $historicalReceipt = $utf8.GetString($receiptBytes) | ConvertFrom-Json
    $historicalReceipt.schema = 'hmasd.browser_pro_submission.v1'
    $historicalReceipt.PSObject.Properties.Remove('dispatch_sha256')
    Write-Utf8 $receiptFile (($historicalReceipt | ConvertTo-Json) + "`n")
    $historical = (& $validator -RoundPath $roundRelative -QuestionPath $questionName `
        -ReceiptPath $receiptName -RawPath $rawName -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($historical.status -ne 'ALREADY_ARCHIVED') { throw 'Raw-first historical v1 archival failed' }
    [IO.File]::WriteAllBytes($receiptFile, $receiptBytes)
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
