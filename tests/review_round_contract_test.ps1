[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$round = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$browserExchange = Get-Content (Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/SKILL.md') -Raw
$controller = Get-Content (Join-Path $repo 'AGENTS.md') -Raw
$registryRaw = Get-Content (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') -Raw
$registry = $registryRaw | ConvertFrom-Json
$mcp = Get-Content (Join-Path $repo '.omp/mcp.json') -Raw | ConvertFrom-Json
$roundValidator = Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/scripts/validate_browser_pro_round.ps1'
$rawArchiver = Join-Path $repo '.agents/skills/hmasd-browser-pro-exchange/scripts/archive_browser_pro_raw.ps1'
$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'

$reviewerKeys = @($registry.reviewers.PSObject.Properties.Name)
$serverKeys = @($mcp.mcpServers.PSObject.Properties.Name)
$currentBranch = (& git.exe -C $repo branch --show-current).Trim()
if ($registry.schema_version -ne 29 -or
    (Compare-Object @('open_divergent') $reviewerKeys) -or
    $registry.round_controller.kind -ne 'active_controller_owned_browsermcp_with_readonly_task_monitor' -or
    $registry.round_controller.external_scientific_decision -ne 'open_divergent' -or
    $registry.round_controller.decision_intake -ne 'active_controller_direct' -or
    $registry.exchange_contract.transport_server -ne 'browsermcp-pro' -or
    $registry.exchange_contract.server_package -ne '@browsermcp/mcp@0.1.3' -or
    $registry.exchange_contract.evidence_transport -ne 'github_connector' -or
    $registry.exchange_contract.repository -ne 'CartmanFatass/My-paper-code' -or
    $registry.exchange_contract.review_branch -ne $currentBranch -or
    -not $registry.exchange_contract.terminal_order.Contains('verify_pushed_boundary') -or
    -not $registry.exchange_contract.terminal_order.Contains('archive_raw_no_clobber') -or
    $registry.exchange_contract.connection_state -ne 'CONNECTED_PREFLIGHT_OK' -or
    $registry.exchange_contract.completion_monitor.agent -ne 'hmasd-pro-monitor' -or
    $registry.exchange_contract.completion_monitor.model -ne 'openai-codex/gpt-5.3-codex-spark' -or
    $registry.exchange_contract.completion_monitor.thinking -ne 'medium' -or
    $registry.exchange_contract.completion_monitor.lifecycle -ne 'one_shot_task_callback' -or
    (Compare-Object @('mcp__browsermcp_pro_browser_snapshot',
        'mcp__browsermcp_pro_browser_wait') @($registry.exchange_contract.completion_monitor.tools)) -or
    $registry.exchange_contract.fallback -ne 'none' -or
    $registry.reviewers.open_divergent.conversation_id -ne '6a61d27c-9278-83e8-ae96-c65c1b52d207' -or
    $registry.reviewers.open_divergent.url -ne 'https://chatgpt.com/c/6a61d27c-9278-83e8-ae96-c65c1b52d207' -or
    $registry.reviewers.open_divergent.expected_model_ui -ne 'Pro' -or
    $registry.reviewers.open_divergent.transport -ne 'browsermcp_connected_tab' -or
    $registry.reviewers.open_divergent.connection_state -ne 'CONNECTED_PREFLIGHT_OK' -or
    $registry.reviewers.open_divergent.question_file -ne '20_PRO_OPEN_QUESTION.md' -or
    $registry.reviewers.open_divergent.raw_file -ne '21_PRO_OPEN_RAW.md') {
    throw 'BrowserMCP review registry mismatch'
}
foreach ($forbidden in @('headless', 'cdp', 'codex_exchange', 'alternate_transport')) {
    if ($registryRaw.Contains($forbidden)) { throw "Review registry retains alternate transport: $forbidden" }
}

$server = $mcp.mcpServers.'browsermcp-pro'
if ((Compare-Object @('browsermcp-pro') $serverKeys) -or
    $server.type -ne 'stdio' -or $server.command -ne 'npx' -or
    @($server.args).Count -ne 2 -or $server.args[0] -ne '-y' -or
    $server.args[1] -ne '@browsermcp/mcp@0.1.3' -or
    $server.timeout -ne 120000) {
    throw 'Pinned singular BrowserMCP server config mismatch'
}

foreach ($required in @('External GPT-5.6 Pro is the scientific decision source',
    'one scheduled research action', 'Controller direct evidence intake',
    'Controller later freezes executable architecture', '$hmasd-browser-pro-exchange',
    'stage_commit=<40-character pushed SHA>',
    'evidence_commit=<40-character pushed evidence SHA>',
    'evidence_transport=github_connector', 'source_manifest=01_SHARED_SOURCE_MANIFEST.md',
    'question=20_PRO_OPEN_QUESTION.md', 'raw=21_PRO_OPEN_RAW.md',
    'exclusive no-clobber archival', '50_DISPOSITION.md')) {
    if (-not $round.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($required in @('browsermcp-pro', '@browsermcp/mcp@0.1.3',
    'BROWSERMCP_PRO_BLOCKED', 'GITHUB_CONNECTOR_EVIDENCE_BLOCKED',
    'GitHub connector', 'ARCHIVE_NATURAL_RESPONSE_EXACTLY',
    'archive_browser_pro_raw.ps1', 'same-directory temporary file',
    'ephemeral `omp --no-session` probe', 'long-lived',
    'hmasd-pro-monitor', 'wait and snapshot', 'neither a persistent role',
    'a transport relay', 'never compensate by pasting local source')) {
    if (-not $browserExchange.Contains($required)) { throw "Browser Pro Exchange missing: $required" }
}
$proMonitorPath = Join-Path $repo '.omp/agents/hmasd-pro-monitor.md'
if (-not (Test-Path -LiteralPath $proMonitorPath -PathType Leaf)) {
    throw 'Missing read-only Pro completion monitor profile'
}
$proMonitor = Get-Content -LiteralPath $proMonitorPath -Raw
foreach ($required in @('mcp__browsermcp_pro_browser_snapshot',
        'mcp__browsermcp_pro_browser_wait', 'STABLE_COMPLETE|BLOCKED',
        'The Controller remains the sole owner')) {
    if (-not $proMonitor.Contains($required)) { throw "Pro monitor missing: $required" }
}
$proMonitorTools = [regex]::Match($proMonitor, '(?m)^tools: \[([^\r\n]+)\]$').Groups[1].Value
foreach ($forbidden in @('click', 'type', 'navigate', 'bash', 'edit', 'write')) {
    if ($proMonitorTools.Contains($forbidden)) { throw "Pro monitor exposes forbidden tool: $forbidden" }
}
foreach ($required in @('ephemeral process is not a valid',
    'name one exact ancestor evidence commit', 'Raw archival is exclusive and no-clobber',
    'BrowserMCP does not upload local source')) {
    if (-not $controller.Contains($required)) { throw "Controller contract missing: $required" }
}
if (Test-Path (Join-Path $repo '.agents/skills/hmasd-review-exchange')) {
    throw 'Superseded persistent review Exchange remains'
}

function Invoke-FixtureGit {
    param([string]$Root, [string[]]$GitArgs)
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & git.exe -C $Root @GitArgs 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($exitCode -ne 0) {
        throw "fixture git $($GitArgs -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    @($output)
}
function Write-Utf8 {
    param([string]$Path, [string]$Content)
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path)) | Out-Null
    [IO.File]::WriteAllText($Path, $Content, [Text.UTF8Encoding]::new($false))
}
function Assert-Failure {
    param([scriptblock]$Action, [string]$Pattern, [string]$Label)
    $failed = $false
    try {
        & $Action | Out-Null
    } catch {
        $failed = $true
        if ([string]$_ -notmatch $Pattern) {
            throw "$Label failed for the wrong reason: $_"
        }
    }
    if (-not $failed) { throw "$Label unexpectedly succeeded" }
}

$fixtureRoot = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-browser-pro-" + [Guid]::NewGuid().ToString('N'))
$fixtureRepo = Join-Path $fixtureRoot 'source'
$fixtureRemote = Join-Path $fixtureRoot 'fixture-owner/fixture-repo.git'
$fixtureRound = 'docs/external-review/rounds/fixture_round'
$questionRelative = "$fixtureRound/20_PRO_OPEN_QUESTION.md"
$manifestRelative = "$fixtureRound/01_SHARED_SOURCE_MANIFEST.md"
try {
    [IO.Directory]::CreateDirectory($fixtureRepo) | Out-Null
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($fixtureRemote)) | Out-Null
    Invoke-FixtureGit $fixtureRoot @('init', '--bare', $fixtureRemote) | Out-Null
    Invoke-FixtureGit $fixtureRepo @('init', '-b', 'Claude') | Out-Null
    Invoke-FixtureGit $fixtureRepo @('config', 'user.name', 'HMASD Contract Test') | Out-Null
    Invoke-FixtureGit $fixtureRepo @('config', 'user.email', 'hmasd-contract@example.invalid') | Out-Null
    Invoke-FixtureGit $fixtureRepo @('config', 'core.autocrlf', 'false') | Out-Null
    Write-Utf8 (Join-Path $fixtureRepo 'docs/project/ALGORITHM_PRINCIPLES.md') "# Algorithm principles`n"
    Write-Utf8 (Join-Path $fixtureRepo 'docs/external-review/OPEN_REVIEW_PRINCIPLES.md') "# Open review principles`n"
    Write-Utf8 (Join-Path $fixtureRepo 'docs/results/result.json') "{`"status`":`"fixture`"}`n"
    Write-Utf8 (Join-Path $fixtureRepo 'ha_ctse_process/reference.py') "VALUE = 1`n"
    Invoke-FixtureGit $fixtureRepo @('add', '.') | Out-Null
    Invoke-FixtureGit $fixtureRepo @('commit', '-m', 'fixture evidence') | Out-Null
    $evidenceCommit = ([string]@(Invoke-FixtureGit $fixtureRepo @('rev-parse', 'HEAD'))[-1]).Trim()

    $metadata = @(
        'Repository: `fixture-owner/fixture-repo`',
        'Review branch: `Claude`',
        "Evidence commit: ``$evidenceCommit``"
    ) -join "`n"
    $evidencePaths = @(
        'docs/project/ALGORITHM_PRINCIPLES.md',
        'docs/external-review/OPEN_REVIEW_PRINCIPLES.md',
        'docs/results/result.json',
        'ha_ctse_process/reference.py'
    )
    $pathList = ($evidencePaths | ForEach-Object { "- ``$_``" }) -join "`n"
    $manifestText = "# Shared Source Manifest`n`n$metadata`n`n$pathList`n"
    $questionText = "# Pro Review Question`n`n$metadata`n`n- ``$manifestRelative```n$pathList`n"
    Write-Utf8 (Join-Path $fixtureRepo $manifestRelative) $manifestText
    Write-Utf8 (Join-Path $fixtureRepo $questionRelative) $questionText
    Invoke-FixtureGit $fixtureRepo @('add', '.') | Out-Null
    Invoke-FixtureGit $fixtureRepo @('commit', '-m', 'fixture review stage') | Out-Null
    $stageCommit = ([string]@(Invoke-FixtureGit $fixtureRepo @('rev-parse', 'HEAD'))[-1]).Trim()
    Invoke-FixtureGit $fixtureRepo @('remote', 'add', 'origin', $fixtureRemote) | Out-Null
    Invoke-FixtureGit $fixtureRepo @('push', 'origin', 'HEAD:refs/heads/Claude') | Out-Null
    Invoke-FixtureGit $fixtureRepo @('remote', 'add', 'wrong-origin', $fixtureRemote) | Out-Null
    Invoke-FixtureGit $fixtureRepo @('remote', 'add', 'ssh-origin', $fixtureRemote) | Out-Null

    $validatedJson = & $roundValidator `
        -RoundPath $fixtureRound `
        -QuestionPath '20_PRO_OPEN_QUESTION.md' `
        -RawPath '21_PRO_OPEN_RAW.md' `
        -RepoRoot $fixtureRepo
    $validated = $validatedJson | ConvertFrom-Json
    $global:HmasdRealGitExe = @(Get-Command git.exe -CommandType Application)[0].Source
    $global:HmasdFixtureRepo = [IO.Path]::GetFullPath($fixtureRepo)
    function global:git.exe {
        $arguments = @($args)
        if ($arguments.Count -ge 5 -and $arguments[0] -eq '-C' -and
            [IO.Path]::GetFullPath([string]$arguments[1]) -eq $global:HmasdFixtureRepo -and
            $arguments[2] -eq 'remote' -and $arguments[3] -eq 'get-url' -and
            $arguments[4] -in @('origin', 'ssh-origin')) {
            $reportedUrl = if ($arguments[4] -eq 'ssh-origin') {
                'git@github.com:fixture-owner/fixture-repo.git'
            } else {
                'https://github.com/fixture-owner/fixture-repo.git'
            }
            Write-Output $reportedUrl
            $global:LASTEXITCODE = 0
            return
        }
        $output = & $global:HmasdRealGitExe @arguments
        $exitCode = $LASTEXITCODE
        $global:LASTEXITCODE = $exitCode
        $output
    }
    $boundaryJson = & $boundaryVerifier `
        -StageCommit $stageCommit `
        -EvidenceCommit $evidenceCommit `
        -Repository 'fixture-owner/fixture-repo' `
        -Remote 'origin' `
        -Branch 'Claude' `
        -QuestionPath $questionRelative `
        -ValidatedQuestionPath $validated.question `
        -RepoRoot $fixtureRepo
    $boundary = $boundaryJson | ConvertFrom-Json
    if ($boundary.status -ne 'REMOTE_EVIDENCE_READY' -or
        $boundary.stage_commit -ne $stageCommit -or
        $boundary.evidence_commit -ne $evidenceCommit -or
        $boundary.validated_question -ne $validated.question -or
        $boundary.source_manifest -ne $manifestRelative) {
        throw 'Boundary verifier failed the exact staged/evidence fixture'
    }

    $sshBoundary = (& $boundaryVerifier -StageCommit $stageCommit `
        -EvidenceCommit $evidenceCommit -Repository 'fixture-owner/fixture-repo' `
        -Remote 'ssh-origin' -Branch 'Claude' -QuestionPath $questionRelative `
        -ValidatedQuestionPath $validated.question -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($sshBoundary.status -ne 'REMOTE_EVIDENCE_READY' -or
        $sshBoundary.remote_url -ne 'git@github.com:fixture-owner/fixture-repo.git') {
        throw 'Boundary verifier rejected the exact SCP-style GitHub remote'
    }

    Assert-Failure {
        & $boundaryVerifier -StageCommit $stageCommit -EvidenceCommit $evidenceCommit `
            -Repository 'fixture-owner/fixture-repo' -Remote 'wrong-origin' -Branch 'Claude' `
            -QuestionPath $questionRelative -ValidatedQuestionPath $validated.question `
            -RepoRoot $fixtureRepo
    } 'does not resolve to GitHub repository' 'Non-GitHub remote'
    Assert-Failure {
        & $boundaryVerifier -StageCommit $stageCommit.Substring(0, 12) `
            -EvidenceCommit $evidenceCommit -Repository 'fixture-owner/fixture-repo' `
            -Remote 'origin' -Branch 'Claude' -QuestionPath $questionRelative `
            -ValidatedQuestionPath $validated.question -RepoRoot $fixtureRepo
    } 'exactly 40 hexadecimal' 'Short stage SHA'
    Invoke-FixtureGit $fixtureRepo @('push', 'origin', "$stageCommit`:refs/heads/wrong") | Out-Null
    Assert-Failure {
        & $boundaryVerifier -StageCommit $stageCommit -EvidenceCommit $evidenceCommit `
            -Repository 'fixture-owner/fixture-repo' -Remote 'origin' -Branch 'wrong' `
            -QuestionPath $questionRelative -ValidatedQuestionPath $validated.question `
            -RepoRoot $fixtureRepo
    } 'missing exact boundary metadata' 'Wrong branch'
    Assert-Failure {
        & $boundaryVerifier -StageCommit $stageCommit -EvidenceCommit $evidenceCommit `
            -Repository 'other-owner/other-repo' -Remote 'origin' -Branch 'Claude' `
            -QuestionPath $questionRelative -ValidatedQuestionPath $validated.question `
            -RepoRoot $fixtureRepo
    } 'does not resolve to GitHub repository' 'Wrong remote/repository identity'
    Assert-Failure {
        & $boundaryVerifier -StageCommit $stageCommit -EvidenceCommit $evidenceCommit `
            -Repository 'fixture-owner/fixture-repo' -Remote 'origin' -Branch 'Claude' `
            -QuestionPath "$fixtureRound/../fixture_round/20_PRO_OPEN_QUESTION.md" `
            -ValidatedQuestionPath $validated.question `
            -RepoRoot $fixtureRepo
    } 'canonical review-round question' 'Wrong round path'

    Write-Utf8 (Join-Path $fixtureRepo $questionRelative) "$questionText`nDIRTY"
    Assert-Failure {
        & $boundaryVerifier -StageCommit $stageCommit -EvidenceCommit $evidenceCommit `
            -Repository 'fixture-owner/fixture-repo' -Remote 'origin' -Branch 'Claude' `
            -QuestionPath $questionRelative -ValidatedQuestionPath $validated.question `
            -RepoRoot $fixtureRepo
    } 'differs from the pushed stage blob' 'Dirty local question'
    Write-Utf8 (Join-Path $fixtureRepo $questionRelative) $questionText

    $orphanTemp = Join-Path (Join-Path $fixtureRepo $fixtureRound) '.21_PRO_OPEN_RAW.md.orphan.tmp'
    Write-Utf8 $orphanTemp 'incomplete temporary capture'
    $orphanValidated = (& $roundValidator -RoundPath $fixtureRound `
        -QuestionPath '20_PRO_OPEN_QUESTION.md' -RawPath '21_PRO_OPEN_RAW.md' `
        -RepoRoot $fixtureRepo) | ConvertFrom-Json
    if ($orphanValidated.raw -ne $validated.raw) {
        throw 'Orphan temporary capture poisoned canonical raw validation'
    }
    Remove-Item -LiteralPath $orphanTemp -Force
    Assert-Failure {
        & $rawArchiver -RoundPath $fixtureRound -RawPath '21_PRO_OPEN_RAW.md' `
            -Content '   ' -RepoRoot $fixtureRepo
    } 'natural non-whitespace response' 'Empty raw archive'

    $rawContent = "Natural Pro response`nSecond line"
    $archiveJson = & $rawArchiver -RoundPath $fixtureRound `
        -RawPath '21_PRO_OPEN_RAW.md' -Content $rawContent -RepoRoot $fixtureRepo
    $archive = $archiveJson | ConvertFrom-Json
    if ($archive.status -ne 'BROWSER_PRO_RAW_ARCHIVED_NO_CLOBBER' -or
        [IO.File]::ReadAllText($archive.raw, [Text.UTF8Encoding]::new($false)) -cne $rawContent) {
        throw 'Browser Pro no-clobber archive failed exact reread equality'
    }
    Assert-Failure {
        & $roundValidator -RoundPath $fixtureRound -QuestionPath '20_PRO_OPEN_QUESTION.md' `
            -RawPath '21_PRO_OPEN_RAW.md' -RepoRoot $fixtureRepo
    } 'raw already exists and is immutable' 'Completed raw validation'
    Assert-Failure {
        & $rawArchiver -RoundPath $fixtureRound -RawPath '21_PRO_OPEN_RAW.md' `
            -Content 'replacement' -RepoRoot $fixtureRepo
    } 'cannot be atomically published without clobbering' 'Raw overwrite'

    Invoke-FixtureGit $fixtureRepo @('rm', $manifestRelative) | Out-Null
    Invoke-FixtureGit $fixtureRepo @('commit', '-m', 'fixture missing manifest') | Out-Null
    $missingManifestCommit = ([string]@(Invoke-FixtureGit $fixtureRepo @('rev-parse', 'HEAD'))[-1]).Trim()
    Invoke-FixtureGit $fixtureRepo @('push', 'origin', 'HEAD:refs/heads/MissingManifest') | Out-Null
    Assert-Failure {
        & $boundaryVerifier -StageCommit $missingManifestCommit -EvidenceCommit $evidenceCommit `
            -Repository 'fixture-owner/fixture-repo' -Remote 'origin' -Branch 'MissingManifest' `
            -QuestionPath $questionRelative -ValidatedQuestionPath $validated.question `
            -RepoRoot $fixtureRepo
    } 'Canonical local question or source manifest is missing' 'Missing pushed manifest'
} finally {
    if (Test-Path Function:\git.exe) {
        Remove-Item Function:\git.exe -Force
    }
    Remove-Variable HmasdRealGitExe -Scope Global -ErrorAction SilentlyContinue
    Remove-Variable HmasdFixtureRepo -Scope Global -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $fixtureRoot) {
        Remove-Item -LiteralPath $fixtureRoot -Recurse -Force
    }
}

Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK transport=browsermcp github_connector=exact no_clobber=true'
