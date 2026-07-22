[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$round = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$exchange = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-exchange/SKILL.md') -Raw
$registry = Get-Content (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') -Raw | ConvertFrom-Json
$heartbeat = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-exchange/scripts/render_review_heartbeat.ps1') -Raw
$boundaryVerifierPath = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
if ($registry.schema_version -ne 25 -or @($registry.reviewers.PSObject.Properties).Count -ne 1 -or
    $registry.reviewers.open_divergent.session_role -ne 'open_divergent_exchange' -or
    $registry.round_controller.external_scientific_decision -ne 'open_divergent' -or
    $registry.round_controller.decision_intake -ne 'active_controller_direct') { throw 'Review registry mismatch' }
foreach ($required in @('External GPT-5.6 Pro is the scientific decision source','one scheduled research action','Controller direct evidence intake','Project Manager','50_DISPOSITION.md')) {
    if (-not $round.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($required in @('reviewer_role=OPEN_DIVERGENT','ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY','COMPLETE_WITH_GAPS','callback delivery','heartbeat was deleted','source_thread_id=<registered open_divergent_exchange thread ID>','handoff_id=<round>:OPEN_DIVERGENT:blocked:<question>')) {
    if (-not $exchange.Contains($required)) { throw "Exchange missing: $required" }
}
if (-not $heartbeat.Contains('[ValidateSet("OPEN_DIVERGENT")]') -or
    ([regex]::Matches($heartbeat, 'ValidateSet\(').Count -ne 1)) { throw 'Heartbeat role set is not singular' }
try {
    & $boundaryVerifierPath -Commit 'not-a-commit' -QuestionPath 'docs/external-review/rounds/invalid/20_PRO_OPEN_QUESTION.md' -RepoRoot $repo
    throw 'Boundary verifier unexpectedly accepted an invalid commit'
}
catch {
    if ($_.FullyQualifiedErrorId -match 'CallDepthOverflow') {
        throw 'Boundary verifier recursively invoked its Git wrapper'
    }
    if ([string]$_ -notmatch 'git rev-parse|fatal: ambiguous argument') {
        throw "Boundary verifier did not reach external git: $_"
    }
}
$head = (& git.exe -C $repo rev-parse HEAD).Trim()
$boundaryJson = & $boundaryVerifierPath `
    -Commit $head `
    -QuestionPath 'docs/external-review/rounds/20260720_noncalendar_g0_no_access_portfolio/20_PRO_OPEN_QUESTION.md' `
    -Remote $repo `
    -Branch 'aggressive' `
    -RepoRoot $repo
$boundary = $boundaryJson | ConvertFrom-Json
if ($boundary.status -ne 'REMOTE_EVIDENCE_READY' -or $boundary.commit -ne $head) {
    throw 'Boundary verifier failed a local reachable review boundary'
}
Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
