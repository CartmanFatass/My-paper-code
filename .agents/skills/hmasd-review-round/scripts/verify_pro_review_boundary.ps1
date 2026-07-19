[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Commit,

    [Parameter(Mandatory = $true)]
    [string]$QuestionPath,

    [string]$Remote = 'My-paper-code',
    [string]$Branch = 'aggressive',
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'

function Invoke-GitChecked {
    param([string[]]$Arguments)

    $output = & git -C $RepoRoot @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return @($output)
}

function Assert-CommitPath {
    param(
        [string]$ResolvedCommit,
        [string]$Path
    )

    $normalized = $Path.Replace('\', '/')
    $null = Invoke-GitChecked -Arguments @('cat-file', '-e', "$ResolvedCommit`:$normalized")
    return $normalized
}

$resolvedOutput = @(Invoke-GitChecked -Arguments @('rev-parse', "$Commit^{commit}"))
$resolved = ([string]$resolvedOutput[-1]).Trim()
if ($resolved -notmatch '^[0-9a-fA-F]{40}$') {
    throw "Commit did not resolve to exactly 40 hexadecimal characters: $resolved"
}

$remoteLines = Invoke-GitChecked -Arguments @('ls-remote', $Remote, "refs/heads/$Branch")
$remoteMatch = [regex]::Match(($remoteLines -join "`n"), '^(?<sha>[0-9a-fA-F]{40})\s+')
if (-not $remoteMatch.Success) {
    throw "Remote branch $Remote/$Branch did not resolve to a commit."
}
$remoteTip = $remoteMatch.Groups['sha'].Value.ToLowerInvariant()

$null = Invoke-GitChecked -Arguments @('cat-file', '-e', "$remoteTip^{commit}")
& git -C $RepoRoot merge-base --is-ancestor $resolved $remoteTip 2>$null
if ($LASTEXITCODE -eq 1) {
    throw "Commit $resolved is not reachable from $Remote/$Branch at $remoteTip."
}
if ($LASTEXITCODE -ne 0) {
    throw "Unable to verify ancestry between $resolved and $remoteTip."
}

$question = Assert-CommitPath -ResolvedCommit $resolved -Path $QuestionPath
$questionText = (Invoke-GitChecked -Arguments @('show', "$resolved`:$question")) -join "`n"
$questionName = [System.IO.Path]::GetFileName($question)

if ($questionName -in @('10_GEMINI_DIVERGENT_QUESTION.md', '20_PRO_OPEN_QUESTION.md') -and
    $questionText -notmatch '(?i)divergent') {
    throw 'The open-review question does not explicitly identify the divergent role.'
}
if ($questionName -eq '40_PRO_CONVERGENT_QUESTION.md' -and
    $questionText -notmatch '(?i)convergent') {
    throw 'The convergent-Pro question does not explicitly identify the convergent role.'
}

$basePrinciples = 'docs/project/ALGORITHM_PRINCIPLES.md'
$openPrinciples = 'docs/external-review/OPEN_REVIEW_PRINCIPLES.md'
$convergentPrinciples = 'docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md'
if ($questionName -in @('10_GEMINI_DIVERGENT_QUESTION.md', '20_PRO_OPEN_QUESTION.md')) {
    if (-not $questionText.Contains($basePrinciples) -or
        -not $questionText.Contains($openPrinciples) -or
        $questionText.Contains($convergentPrinciples)) {
        throw 'The open-Pro question has an invalid scientific-principle binding.'
    }
}
if ($questionName -eq '40_PRO_CONVERGENT_QUESTION.md') {
    if (-not $questionText.Contains($basePrinciples) -or
        -not $questionText.Contains($convergentPrinciples) -or
        $questionText.Contains($openPrinciples)) {
        throw 'The convergent-Pro question has an invalid scientific-principle binding.'
    }
}

$section = [regex]::Match(
    $questionText,
    '(?ms)^## Repository files to inspect\s*\r?\n(?<body>.*?)(?=^##\s|\z)'
)
if (-not $section.Success) {
    throw 'Question is missing the exact Repository files to inspect section.'
}

$listedPaths = @(
    [regex]::Matches($section.Groups['body'].Value, '`([^`\r\n]+)`') |
        ForEach-Object { $_.Groups[1].Value.Trim().Replace('\', '/') } |
        Where-Object { $_ -match '/' -and $_ -notmatch '[*?]' } |
        Select-Object -Unique
)
if ($listedPaths.Count -eq 0) {
    throw 'Repository files to inspect does not contain any exact repository paths.'
}

$verifiedPaths = @()
foreach ($path in $listedPaths) {
    $verifiedPaths += Assert-CommitPath -ResolvedCommit $resolved -Path $path
}

[ordered]@{
    status = 'REMOTE_EVIDENCE_READY'
    commit = $resolved.ToLowerInvariant()
    remote = $Remote
    branch = $Branch
    remote_tip = $remoteTip
    question = $question
    inspected_paths = $verifiedPaths
} | ConvertTo-Json -Depth 3
