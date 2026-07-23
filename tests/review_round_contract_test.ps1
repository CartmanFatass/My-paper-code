[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$round = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$roundAgent = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/agents/openai.yaml') -Raw
$cdc = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/references/cdc-principles.md') -Raw
$registry = Get-Content (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') -Raw | ConvertFrom-Json
$heartbeatPath = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/render_review_heartbeat.ps1'
$heartbeat = Get-Content $heartbeatPath -Raw
$boundaryVerifierPath = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
$retiredExchange = Join-Path $repo '.agents/skills/hmasd-review-exchange'
$activeRound = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned'
$activeRaw = Get-Content (Join-Path $activeRound '21_PRO_OPEN_RAW.md') -Raw
$proReadme = Get-Content (Join-Path $repo 'docs/external-review/gpt5_6_pro/README.md') -Raw

if ($registry.schema_version -ne 27 -or @($registry.reviewers.PSObject.Properties).Count -ne 1 -or
    $null -ne $registry.reviewers.open_divergent.PSObject.Properties['session_role'] -or
    $registry.reviewers.open_divergent.transport -ne 'controller_in_app_browser' -or
    $registry.round_controller.external_scientific_decision -ne 'open_divergent' -or
    $registry.round_controller.kind -ne 'active_controller_direct_transport' -or
    $registry.round_controller.decision_intake -ne 'active_controller_mechanical' -or
    $registry.direct_transport_contract.transport_owner -ne 'active_controller' -or
    $registry.direct_transport_contract.heartbeat_owner -ne 'active_controller' -or
    $registry.direct_transport_contract.heartbeat_uniqueness -ne 'one_per_round' -or
    $registry.direct_transport_contract.retired_task_output_authority -ne 'none' -or
    $registry.direct_transport_contract.terminal_order -ne 'archive_exact_raw_then_mechanical_intake_then_delete_heartbeat_then_return_raw_to_pm') {
    throw 'Controller-direct review registry mismatch'
}
if (Test-Path -LiteralPath $retiredExchange) { throw 'Retired Exchange Skill remains active' }
foreach ($required in @(
    'External GPT-5.6 Pro is the scientific decision source',
    'one scheduled research action',
    'Controller mechanical intake',
    'Project Manager',
    '30_PM_CODE_SIDE_RECONCILIATION.md',
    '50_MECHANICAL_INTAKE_RECORD.md',
    'only scientific disposition authority',
    'Controller-direct transport',
    '$browser:control-in-app-browser',
    'inspect the registered conversation before submission',
    'An accepted matching fence is never resubmitted',
    'never classifies scientific completeness',
    'exact raw -> Controller mechanical intake -> heartbeat deletion -> Project Manager reconciliation',
    'late output from a retired role has no authority',
    'A redirect to the ChatGPT home page is not a blocker',
    'Conversation discovery ladder',
    'visible conversation links',
    'two stable snapshots',
    'at least three seconds',
    'candidate URL',
    'data-message-author-role',
    'Stop generating',
    'Retry',
    'A visible `Thinking` label alone does not prove generation is active',
    'recovery_exhausted=true')) {
    if (-not $round.Contains($required)) { throw "Review round missing: $required" }
}
foreach ($required in @('semantic_author=project_manager',
    'artifact_scope=reviewer_visible_code_side', 'repair_owner=project_manager',
    'exact PM-authored files unchanged')) {
    if (-not $round.Contains($required)) { throw "Review round semantic ownership missing: $required" }
}
foreach ($required in @('Project Manager authors code-side reconciliation',
    'Controller owns only exact raw archival and mechanical intake',
    'External Pro owns the scientific content',
    'Controller may mechanically apply only an exact Pro-authored target-file delta',
    'Project Manager does not author these scientific records')) {
    if (-not $cdc.Contains($required)) { throw "CDC reference ownership missing: $required" }
}
foreach ($forbidden in @('Controller preserves the decision, writes factual reconciliation',
    'The Controller owns:',
    'Project Manager authors proposed changes to:')) {
    if ($cdc.Contains($forbidden)) { throw "CDC reference retains Controller semantic authorship: $forbidden" }
}
foreach ($forbidden in @(
    'open_divergent_exchange',
    '$hmasd-review-exchange',
    'REVIEW_STAGE_COMPLETE',
    'REVIEW_STAGE_BLOCKED',
    'callback delivery',
    'Judge content gaps semantically')) {
    if ($round.Contains($forbidden)) { throw "Review round retains Exchange behavior: $forbidden" }
}
if ($round.Contains('It creates one reviewer-visible question')) {
    throw 'Review round still assigns reviewer-visible semantic authorship to Controller'
}
if ($roundAgent.Contains('direct evidence intake') -or
    -not $roundAgent.Contains('mechanical provenance intake') -or
    -not $roundAgent.Contains('$browser:control-in-app-browser')) {
    throw 'Review-round agent prompt does not enforce direct mechanical transport'
}
if ($roundAgent.Contains('allow_implicit_invocation: false')) {
    throw 'Review-round Skill is hidden from runtime catalog discovery'
}
foreach ($required in @('$hmasd-review-round', '$browser:control-in-app-browser',
    'Never submit or resubmit', 'active Controller', 'stage_commit=',
    'home-page redirect', 'two stable text snapshots', 'Thinking label alone',
    'Write the mechanical intake', 'return the exact raw to Project Manager',
    'delete this heartbeat')) {
    if (-not $heartbeat.Contains($required)) { throw "Controller heartbeat missing: $required" }
}
if ($heartbeat.Contains('$hmasd-review-exchange') -or $heartbeat.Contains('callback')) {
    throw 'Controller heartbeat retains Exchange callback behavior'
}
$roundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned'
$heartbeatPrompt = & $heartbeatPath `
    -RoundPath $roundRoot `
    -Stage 'OPEN_DIVERGENT' `
    -StageCommit '50f95da37496b092128c2136d50503ac3e18a5c1' `
    -QuestionPath '20_PRO_OPEN_QUESTION.md' `
    -RawPath '21_PRO_OPEN_RAW.md' `
    -HeartbeatId 'contract-test-heartbeat'
foreach ($required in @('$hmasd-review-round', '$browser:control-in-app-browser',
    '20260722_ehc_g1_focused_source_fields_pm_owned',
    '50f95da37496b092128c2136d50503ac3e18a5c1',
    'contract-test-heartbeat')) {
    if (-not $heartbeatPrompt.Contains($required)) { throw "Rendered heartbeat missing: $required" }
}
if ($heartbeatPrompt.Contains('$hmasd-review-exchange')) { throw 'Rendered heartbeat activates retired Skill' }
foreach ($stale in @('registered Open-Pro Exchange must replace',
    'single registered Luna Exchange task',
    'Exchange submits the freshness fence',
    'Exchange archives the natural raw')) {
    if ($activeRaw.Contains($stale) -or $proReadme.Contains($stale)) {
        throw "Active review source retains retired transport authority: $stale"
    }
}
foreach ($required in @('status=AWAITING_EXTERNAL_PRO_RESPONSE',
    'semantic_author=project_manager',
    'scientific_authority=external_pro',
    'active Controller under `$hmasd-review-round` is the sole mechanical writer')) {
    if (-not $activeRaw.Contains($required)) { throw "Active raw placeholder missing: $required" }
}
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
    -QuestionPath 'docs/external-review/rounds/20260722_ehc_g1_focused_source_fields_pm_owned/20_PRO_OPEN_QUESTION.md' `
    -Remote $repo `
    -Branch 'aggressive' `
    -RepoRoot $repo
$boundary = $boundaryJson | ConvertFrom-Json
if ($boundary.status -ne 'REMOTE_EVIDENCE_READY' -or $boundary.commit -ne $head) {
    throw 'Boundary verifier failed a local reachable review boundary'
}
Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
