[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Commit,
    [Parameter(Mandatory = $true)][string]$QuestionPath,
    [string]$Remote = 'My-paper-code',
    [string]$Branch = 'aggressive',
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
function Git([string[]]$Args) {
    $out = & git -C $RepoRoot @Args 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git $($Args -join ' ') failed: $($out -join [Environment]::NewLine)" }
    @($out)
}

$resolved = ([string](Git @('rev-parse', "$Commit^{commit}"))[-1]).Trim()
if ($resolved -notmatch '^[0-9a-fA-F]{40}$') { throw 'Commit must resolve to 40 hexadecimal characters.' }
$remoteLine = (Git @('ls-remote', $Remote, "refs/heads/$Branch")) -join "`n"
$m = [regex]::Match($remoteLine, '^(?<sha>[0-9a-fA-F]{40})\s+')
if (-not $m.Success) { throw 'Remote branch did not resolve.' }
$tip = $m.Groups['sha'].Value.ToLowerInvariant()
$null = Git @('cat-file', '-e', "$tip^{commit}")
& git -C $RepoRoot merge-base --is-ancestor $resolved $tip 2>$null
if ($LASTEXITCODE -ne 0) { throw "Commit $resolved is not reachable from $Remote/$Branch." }

$question = $QuestionPath.Replace('\', '/')
if ([IO.Path]::GetFileName($question) -ne '20_PRO_OPEN_QUESTION.md') {
    throw 'Only the registered Open-Pro question is externally dispatched.'
}
$null = Git @('cat-file', '-e', "$resolved`:$question")
$text = (Git @('show', "$resolved`:$question")) -join "`n"
foreach ($required in @(
    'docs/project/ALGORITHM_PRINCIPLES.md',
    'docs/external-review/OPEN_REVIEW_PRINCIPLES.md'
)) {
    if (-not $text.Contains($required)) { throw "Open question is missing: $required" }
}
if ($text.Contains('CONVERGENT_REVIEW_PRINCIPLES.md')) {
    throw 'Open question contains an internal convergence contract.'
}

$paths = @([regex]::Matches($text, '`([^`\r\n]+)`') | ForEach-Object {
    $_.Groups[1].Value.Trim().Replace('\', '/')
} | Where-Object { $_ -match '^(docs|ha_ctse_process|scripts|tests|ref)/' } | Sort-Object -Unique)
if ($paths.Count -eq 0) { throw 'Question does not contain exact repository evidence paths.' }
foreach ($path in $paths) { $null = Git @('cat-file', '-e', "$resolved`:$path") }

[pscustomobject]@{
    status = 'REMOTE_EVIDENCE_READY'
    commit = $resolved
    remote = $Remote
    branch = $Branch
    remote_tip = $tip
    question = $question
    inspected_paths = $paths
} | ConvertTo-Json -Depth 4
