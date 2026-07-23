[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$StageCommit,
    [Parameter(Mandatory = $true)][string]$EvidenceCommit,
    [Parameter(Mandatory = $true)][string]$Repository,
    [Parameter(Mandatory = $true)][string]$Remote,
    [Parameter(Mandatory = $true)][string]$Branch,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [Parameter(Mandatory = $true)][string]$ValidatedQuestionPath,
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
function Git([string[]]$GitArgs) {
    $out = & git.exe -C $RepoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed: $($out -join [Environment]::NewLine)"
    }
    @($out)
}
foreach ($entry in @(
    @{ Name = 'StageCommit'; Value = $StageCommit },
    @{ Name = 'EvidenceCommit'; Value = $EvidenceCommit }
)) {
    if ($entry.Value -notmatch '^[0-9a-fA-F]{40}$') {
        throw "$($entry.Name) must be exactly 40 hexadecimal characters."
    }
}
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
    throw 'Repository must be an exact GitHub owner/repository identifier.'
}

$question = $QuestionPath.Replace('\', '/')
if ($question -notmatch '^docs/external-review/rounds/(?<round>[A-Za-z0-9][A-Za-z0-9._-]*)/20_PRO_OPEN_QUESTION\.md$') {
    throw 'QuestionPath must be one canonical review-round question.'
}
$round = $Matches.round
$manifest = "docs/external-review/rounds/$round/01_SHARED_SOURCE_MANIFEST.md"
$expectedQuestion = [IO.Path]::GetFullPath((Join-Path $RepoRoot $question))
$validatedQuestion = [IO.Path]::GetFullPath($ValidatedQuestionPath)
if (-not $expectedQuestion.Equals($validatedQuestion, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Boundary question does not match the canonical validator result.'
}
$localManifest = [IO.Path]::GetFullPath((Join-Path $RepoRoot $manifest))
if (-not (Test-Path -LiteralPath $validatedQuestion -PathType Leaf) -or
    -not (Test-Path -LiteralPath $localManifest -PathType Leaf)) {
    throw 'Canonical local question or source manifest is missing.'
}

$stageResolved = ([string]@(Git @('rev-parse', "$StageCommit^{commit}"))[-1]).Trim().ToLowerInvariant()
$evidenceResolved = ([string]@(Git @('rev-parse', "$EvidenceCommit^{commit}"))[-1]).Trim().ToLowerInvariant()
if ($stageResolved -ne $StageCommit.ToLowerInvariant() -or
    $evidenceResolved -ne $EvidenceCommit.ToLowerInvariant()) {
    throw 'Commit resolution changed an exact boundary SHA.'
}
& git.exe -C $RepoRoot merge-base --is-ancestor $evidenceResolved $stageResolved 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Evidence commit $evidenceResolved is not an ancestor of stage commit $stageResolved."
}

$remoteUrl = ([string]@(Git @('remote', 'get-url', $Remote))[-1]).Trim()
$normalizedRemoteUrl = $remoteUrl.Replace('\', '/').TrimEnd('/')
$httpsUrl = "https://github.com/$Repository.git"
$sshUrl = "git@github.com:$Repository.git"
if (-not $normalizedRemoteUrl.Equals($httpsUrl, [StringComparison]::OrdinalIgnoreCase) -and
    -not $normalizedRemoteUrl.Equals($sshUrl, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Remote $Remote does not resolve to GitHub repository $Repository."
}

$remoteLine = (Git @('ls-remote', $Remote, "refs/heads/$Branch")) -join "`n"
$remoteMatch = [regex]::Match($remoteLine, '^(?<sha>[0-9a-fA-F]{40})\s+')
if (-not $remoteMatch.Success) { throw 'Remote branch did not resolve.' }
$tip = $remoteMatch.Groups['sha'].Value.ToLowerInvariant()
$null = Git @('cat-file', '-e', "$tip^{commit}")
& git.exe -C $RepoRoot merge-base --is-ancestor $stageResolved $tip 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Stage commit $stageResolved is not reachable from $Remote/$Branch."
}

$null = Git @('cat-file', '-e', "$stageResolved`:$question")
$null = Git @('cat-file', '-e', "$stageResolved`:$manifest")
$stageQuestionBlob = ([string]@(Git @('rev-parse', "$stageResolved`:$question"))[-1]).Trim()
$stageManifestBlob = ([string]@(Git @('rev-parse', "$stageResolved`:$manifest"))[-1]).Trim()
$localQuestionBlob = ([string]@(Git @('hash-object', '--no-filters', '--', $validatedQuestion))[-1]).Trim()
$localManifestBlob = ([string]@(Git @('hash-object', '--no-filters', '--', $localManifest))[-1]).Trim()
if ($localQuestionBlob -ne $stageQuestionBlob -or $localManifestBlob -ne $stageManifestBlob) {
    throw 'Canonical local question or source manifest differs from the pushed stage blob.'
}
$questionText = (Git @('show', "$stageResolved`:$question")) -join "`n"
$manifestText = (Git @('show', "$stageResolved`:$manifest")) -join "`n"
$metadata = @(
    "Repository: ``$Repository``",
    "Review branch: ``$Branch``",
    "Evidence commit: ``$evidenceResolved``"
)
foreach ($artifact in @(
    @{ Name = 'question'; Text = $questionText },
    @{ Name = 'source manifest'; Text = $manifestText }
)) {
    foreach ($required in $metadata) {
        if (-not $artifact.Text.Contains($required)) {
            throw "$($artifact.Name) is missing exact boundary metadata: $required"
        }
    }
}
foreach ($required in @(
    'docs/project/ALGORITHM_PRINCIPLES.md',
    'docs/external-review/OPEN_REVIEW_PRINCIPLES.md'
)) {
    if (-not $questionText.Contains($required)) {
        throw "Open question is missing: $required"
    }
}
if ($questionText.Contains('CONVERGENT_REVIEW_PRINCIPLES.md')) {
    throw 'Open question contains an internal convergence contract.'
}

function RepositoryPaths([string]$Text) {
    @([regex]::Matches($Text, '`([^`\r\n]+)`') | ForEach-Object {
        $_.Groups[1].Value.Trim().Replace('\', '/')
    } | Where-Object {
        $_ -match '^(docs|ha_ctse_process|scripts|tests|ref)/'
    } | Sort-Object -Unique)
}
$questionPaths = @(RepositoryPaths $questionText)
$manifestPaths = @(RepositoryPaths $manifestText)
if ($questionPaths -notcontains $manifest) {
    throw 'Question does not name its canonical source manifest.'
}
$reviewArtifacts = @($question, $manifest)
$questionEvidence = @($questionPaths | Where-Object { $_ -notin $reviewArtifacts })
$manifestEvidence = @($manifestPaths | Where-Object { $_ -notin $reviewArtifacts })
if ($questionEvidence.Count -eq 0 -or $manifestEvidence.Count -eq 0) {
    throw 'Question and source manifest must name exact repository evidence paths.'
}
if (Compare-Object $questionEvidence $manifestEvidence) {
    throw 'Question and source manifest do not name the same evidence boundary.'
}
foreach ($path in $questionEvidence) {
    $null = Git @('cat-file', '-e', "$evidenceResolved`:$path")
}

[ordered]@{
    status = 'REMOTE_EVIDENCE_READY'
    repository = $Repository
    branch = $Branch
    remote = $Remote
    remote_url = $remoteUrl
    remote_tip = $tip
    stage_commit = $stageResolved
    evidence_commit = $evidenceResolved
    question = $question
    validated_question = $validatedQuestion
    source_manifest = $manifest
    question_blob = $stageQuestionBlob
    source_manifest_blob = $stageManifestBlob
    inspected_paths = $questionEvidence
} | ConvertTo-Json -Depth 4
