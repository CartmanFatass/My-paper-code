<#
.SYNOPSIS
Single mandatory gate a review round must pass before any browser session opens.

.DESCRIPTION
Unifies the evidence-declaration contract that verify_pro_review_boundary.ps1 and
build_review_evidence_archive.ps1 previously disagreed about. The boundary
verifier accepted any backticked repository path anywhere in the question; the
archive builder required a literal "## Evidence to read" allow-list. A question
could pass the first and be refused by the second, which retired round
20260724_g20_credit_rule_zero_fixed_point after it had already been dispatched.

This script is the one definition. The allow-list is the contract.

The fence artifact is read from the WORKING TREE, not from -Commit. A fence
naming stage_commit cannot live inside the commit it names, so the intended
order is: commit question and evidence, take the SHA, write the fence with that
SHA, run this preflight, dispatch, then commit the fence as the round record.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Commit,
    [Parameter(Mandatory = $true)][string]$RoundPath,
    [Parameter(Mandatory = $true)][string]$Branch,
    # The git remote NAME (origin), never the GitHub slug. Conflating the two is
    # why verify_pro_review_boundary.ps1 crashed on its own default.
    [string]$Remote = 'origin',
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
function Git([string[]]$GitArgs) {
    $out = & git.exe -C $RepoRoot @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git $($GitArgs -join ' ') failed: $($out -join [Environment]::NewLine)" }
    @($out)
}

$round = $RoundPath.Replace('\', '/').TrimEnd('/')
$roundId = Split-Path -Leaf $round
$question = "$round/20_PRO_OPEN_QUESTION.md"
$failures = [Collections.Generic.List[string]]::new()

# --- 1. the commit is real and actually pushed -------------------------------
$resolved = ([string](@(Git @('rev-parse', "$Commit^{commit}"))[-1])).Trim()
if ($resolved -notmatch '^[0-9a-fA-F]{40}$') { throw 'Commit must resolve to 40 hexadecimal characters.' }
$remoteLine = (Git @('ls-remote', $Remote, "refs/heads/$Branch")) -join "`n"
$m = [regex]::Match($remoteLine, '^(?<sha>[0-9a-fA-F]{40})\s+')
if (-not $m.Success) { throw "Remote branch did not resolve: $Remote/$Branch" }
& git.exe -C $RepoRoot merge-base --is-ancestor $resolved $m.Groups['sha'].Value 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Commit $resolved is not reachable from $Remote/$Branch. The reviewer reads the remote; unpushed work is invisible."
}

# --- 2. the question exists at that commit -----------------------------------
& git.exe -C $RepoRoot cat-file -e "$resolved`:$question" 2>$null
if ($LASTEXITCODE -ne 0) { throw "Question is not present at commit: $question" }
$lines = @(Git @('show', "$resolved`:$question"))

# --- 3. the allow-list, parsed exactly as the archive builder parses it ------
$inEvidence = $false
$paths = [Collections.Generic.List[string]]::new()
foreach ($line in $lines) {
    if ($line -ceq '## Evidence to read') { $inEvidence = $true; continue }
    if ($inEvidence -and $line -match '^##\s+') { break }
    if ($inEvidence -and $line -match '^\s*-\s+`([^`]+)`\s*$') {
        $paths.Add($Matches[1].Trim().Replace('\', '/'))
    }
}
if ($paths.Count -eq 0) {
    $failures.Add('Question has no "## Evidence to read" allow-list. The freshness fence names only the question, so paths declared in a side manifest or in the exchanger brief never reach the reviewer.')
}
$duplicates = @($paths | Group-Object | Where-Object Count -gt 1 | ForEach-Object Name)
foreach ($d in $duplicates) { $failures.Add("Allow-list contains a duplicate path: $d") }

foreach ($path in ($paths | Sort-Object -Unique)) {
    & git.exe -C $RepoRoot cat-file -e "$resolved`:$path" 2>$null
    if ($LASTEXITCODE -ne 0) { $failures.Add("Allow-listed path is absent at commit: $path") }
}

# --- 4. the standing scientific contracts must be allow-listed, not merely
#        mentioned somewhere in prose -----------------------------------------
foreach ($required in @(
    'docs/project/ALGORITHM_PRINCIPLES.md',
    'docs/external-review/OPEN_REVIEW_PRINCIPLES.md'
)) {
    if ($paths -notcontains $required) { $failures.Add("Allow-list is missing a standing contract: $required") }
}
$questionText = $lines -join "`n"
if ($questionText.Contains('CONVERGENT_REVIEW_PRINCIPLES.md')) {
    $failures.Add('Open question contains an internal convergence contract.')
}

# --- 5. the fence artifact, from the working tree ----------------------------
$fencePath = Join-Path $RepoRoot "$round/10_FENCE.txt"
$fenceFields = @{}
if (-not (Test-Path $fencePath)) {
    $failures.Add("Fence artifact is missing: $round/10_FENCE.txt. Compose the fence as a file and paste it; do not type it line by line.")
} else {
    $fenceText = Get-Content -Raw -Encoding UTF8 $fencePath
    if ($fenceText -notmatch '(?m)^CURRENT_REVIEW_ASSIGNMENT\s*$') {
        $failures.Add('Fence artifact does not open with a bare CURRENT_REVIEW_ASSIGNMENT line.')
    }
    foreach ($kv in [regex]::Matches($fenceText, '(?m)^(?<k>[a-z_]+)=(?<v>.*)$')) {
        $fenceFields[$kv.Groups['k'].Value] = $kv.Groups['v'].Value.Trim()
    }
    $remoteUrl = ([string](@(Git @('remote', 'get-url', $Remote))[-1])).Trim()
    $slugMatch = [regex]::Match($remoteUrl, 'github\.com[:/](?<slug>[^/]+/[^/]+?)(\.git)?$')
    if (-not $slugMatch.Success) { throw "Cannot derive a GitHub slug from remote URL: $remoteUrl" }
    $expected = @{
        repository   = $slugMatch.Groups['slug'].Value
        branch       = $Branch
        round        = $roundId
        stage_commit = $resolved
        question     = $question
    }
    foreach ($k in $expected.Keys) {
        if (-not $fenceFields.ContainsKey($k)) { $failures.Add("Fence is missing field: $k") }
        elseif ($fenceFields[$k] -cne $expected[$k]) {
            $failures.Add("Fence $k mismatch: fence has '$($fenceFields[$k])', expected '$($expected[$k])'")
        }
    }
    if (-not $fenceFields.ContainsKey('instruction')) { $failures.Add('Fence is missing field: instruction') }
}

# --- 6. the recovery archive must actually build ------------------------------
$archiveProbe = Join-Path ([IO.Path]::GetTempPath()) ("round_preflight_" + $resolved.Substring(0, 12) + ".zip")
$archiveStatus = 'not_attempted'
if ($paths.Count -gt 0) {
    try {
        $builder = Join-Path $PSScriptRoot 'build_review_evidence_archive.ps1'
        $built = & $builder -Commit $resolved -QuestionPath $question -OutputPath $archiveProbe 2>&1 | ConvertFrom-Json
        $archiveStatus = $built.status
        if ($built.status -ne 'REVIEW_EVIDENCE_ARCHIVE_READY') { $failures.Add("Evidence archive did not build: $($built.status)") }
    } catch {
        $archiveStatus = 'build_failed'
        $failures.Add("Evidence archive did not build: $_")
    } finally {
        if (Test-Path $archiveProbe) { Remove-Item $archiveProbe -Force }
    }
}

if ($failures.Count -gt 0) {
    [pscustomobject]@{
        status   = 'ROUND_PREFLIGHT_FAILED'
        round    = $roundId
        commit   = $resolved
        failures = @($failures)
    } | ConvertTo-Json -Depth 4
    exit 1
}

[pscustomobject]@{
    status              = 'ROUND_PREFLIGHT_READY'
    round               = $roundId
    commit              = $resolved
    branch              = $Branch
    question            = $question
    allow_list_count    = $paths.Count
    allow_list          = @($paths)
    fence_artifact      = "$round/10_FENCE.txt"
    archive_build       = $archiveStatus
} | ConvertTo-Json -Depth 4
