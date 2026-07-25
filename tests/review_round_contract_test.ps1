[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$registry = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') | ConvertFrom-Json
if ($registry.schema_version -ne 28 -or
    $registry.round_operator.kind -ne 'project_manager_direct_transport' -or
    $registry.round_operator.decision_intake -ne 'project_manager_direct' -or
    $registry.round_operator.git_boundary_owner -ne 'project_manager' -or
    $registry.direct_transport_contract.transport_owner -ne 'active_project_manager' -or
    $registry.direct_transport_contract.heartbeat_owner -ne 'active_project_manager' -or
    $registry.reviewers.open_divergent.transport -ne 'project_manager_in_app_browser') {
    throw 'Project-Manager-direct review registry mismatch'
}

$skillPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$skill = Get-Content -Raw -LiteralPath $skillPath
foreach ($required in @(
    'Project-Manager-direct transport',
    'active Project Manager',
    '$browser:control-in-app-browser',
    'VERIFY_FRESHNESS_FENCE',
    'An accepted matching fence is never resubmitted',
    'two stable snapshots',
    'at least three seconds',
    'Never activate `Answer now`',
    'its presence or absence is neutral',
    'Only Pro''s natural completion is admissible',
    'transport diagnostic',
    'materialize them from `stage_commit`',
    'not from the current working tree',
    'exact raw -> provenance intake -> heartbeat deletion -> Project Manager reconciliation')) {
    if (-not $skill.Contains($required)) { throw "Review Skill missing: $required" }
}
if ($skill -match '(?i)\bcontroller\b|hmasd-dispatch-task|hmasd-experiment-monitor') {
    throw 'Review Skill retains a retired relay or monitor surface'
}

$heartbeatPath = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/render_review_heartbeat.ps1'
$roundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned'
$prompt = & $heartbeatPath `
    -RoundPath $roundRoot `
    -Stage 'OPEN_DIVERGENT' `
    -StageCommit '50f95da37496b092128c2136d50503ac3e18a5c1' `
    -QuestionPath '20_PRO_OPEN_QUESTION.md' `
    -RawPath '21_PRO_OPEN_RAW.md' `
    -HeartbeatId 'contract-test-heartbeat'
foreach ($required in @(
    'PROJECT-MANAGER-DIRECT',
    'active Project Manager',
    'Never submit or resubmit',
    'Never click, invoke, or script Answer now',
    'presence or absence is neutral',
    'contract-test-heartbeat',
    'delete',
    'heartbeat and confirm absence')) {
    if (-not $prompt.Contains($required)) { throw "Rendered heartbeat missing: $required" }
}
if ($prompt -match '(?i)\bcontroller\b|hmasd-dispatch-task') {
    throw 'Rendered heartbeat retains a retired Controller route'
}

$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
$head = (& git.exe -C $repo rev-parse HEAD).Trim()
$boundary = & $boundaryVerifier `
    -Commit $head `
    -QuestionPath 'docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/20_PRO_OPEN_QUESTION.md' `
    -Remote $repo `
    -Branch 'aggressive' `
    -RepoRoot $repo | ConvertFrom-Json
if ($boundary.status -ne 'REMOTE_EVIDENCE_READY' -or $boundary.commit -ne $head) {
    throw 'Review boundary verifier failed a reachable exact commit'
}

Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
