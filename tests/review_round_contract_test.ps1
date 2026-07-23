[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$round = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$roundAgent = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/agents/openai.yaml') -Raw
$exchange = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-exchange/SKILL.md') -Raw
$registry = Get-Content (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') -Raw | ConvertFrom-Json
$heartbeat = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-exchange/scripts/render_review_heartbeat.ps1') -Raw
$boundaryVerifierPath = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
if ($registry.schema_version -ne 26 -or @($registry.reviewers.PSObject.Properties).Count -ne 1 -or
    $registry.reviewers.open_divergent.session_role -ne 'open_divergent_exchange' -or
    $registry.round_controller.external_scientific_decision -ne 'open_divergent' -or
    $registry.round_controller.kind -ne 'active_controller_mechanical_exchange' -or
    $registry.round_controller.decision_intake -ne 'active_controller_mechanical') { throw 'Review registry mismatch' }
foreach ($required in @('External GPT-5.6 Pro is the scientific decision source','one scheduled research action','Controller mechanical intake','Project Manager','30_PM_CODE_SIDE_RECONCILIATION.md','50_MECHANICAL_INTAKE_RECORD.md','only scientific disposition authority')) {
    if (-not $round.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($required in @('semantic_author=project_manager',
    'artifact_scope=reviewer_visible_code_side', 'repair_owner=project_manager',
    'exact PM-authored files unchanged')) {
    if (-not $round.Contains($required)) { throw "Review round semantic ownership missing: $required" }
    if (-not $exchange.Contains($required)) { throw "Exchange semantic ownership missing: $required" }
}
if ($round.Contains('It creates one reviewer-visible question')) {
    throw 'Review round still assigns reviewer-visible semantic authorship to Controller'
}
if ($roundAgent.Contains('direct evidence intake') -or
    -not $roundAgent.Contains('mechanical provenance intake')) {
    throw 'Review-round agent prompt retains Controller semantic intake'
}
foreach ($required in @('$hmasd-dispatch-task', '$hmasd-review-exchange', 'recovery_exhausted=true')) {
    if (-not $round.Contains($required)) { throw "Review round dispatch contract missing: $required" }
}
if ($round.Contains('role_skill=.agents/skills/')) { throw 'Review round still sends a Skill path trigger' }
foreach ($required in @('$hmasd-review-exchange','skill=$hmasd-review-exchange','reviewer_role=OPEN_DIVERGENT','ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY','COMPLETE_WITH_GAPS','callback delivery','heartbeat was deleted','RECOVERY_ATTEMPT','recovery_exhausted=true','source_thread_id=<registered open_divergent_exchange thread ID>','handoff_id=<round>:OPEN_DIVERGENT:blocked:<question>')) {
    if (-not $exchange.Contains($required)) { throw "Exchange missing: $required" }
}
foreach ($required in @('superseded_process=<true|false>',
    'adoption_authority=<false|external_pro_raw_only>')) {
    if (-not $exchange.Contains($required)) { throw "Exchange legacy fail-closed callback missing: $required" }
}
if (-not $exchange.Contains('Project Manager decides whether a code-side gap needs a focused follow-up')) {
    throw 'Exchange still leaves focused-follow-up semantic judgment with Controller'
}
if ($exchange.Contains('role_skill=.agents/skills/')) { throw 'Exchange transport still relies on a Skill path trigger' }
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
