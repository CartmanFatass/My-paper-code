[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$registry = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') | ConvertFrom-Json
if ($registry.schema_version -ne 30 -or
    $registry.round_operator.kind -ne 'project_manager_direct_transport' -or
    $registry.round_operator.external_scientific_decision -ne 'external_pro_binding_within_user_boundary' -or
    $registry.round_operator.decision_intake -ne 'project_manager_mechanical_realization' -or
    $registry.round_operator.git_boundary_owner -ne 'project_manager' -or
    $registry.direct_transport_contract.transport_owner -ne 'active_project_manager' -or
    $registry.direct_transport_contract.response_monitor_agent_type -ne 'hmasd-pro-response-monitor' -or
    $registry.direct_transport_contract.response_monitor_model -ne 'gpt-5.6-luna' -or
    $registry.direct_transport_contract.response_monitor_effort -ne 'low' -or
    $registry.direct_transport_contract.response_monitor_observation -ne 'project_manager_brokered_jsonl_sentinel' -or
    $registry.direct_transport_contract.response_monitor_sentinel_tool -ne 'scripts/hmasd_pro_response_sentinel.py' -or
    $registry.reviewers.open_divergent.transport -ne 'project_manager_in_app_browser') {
    throw 'Project-Manager-direct review registry mismatch'
}

$skillPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$skill = Get-Content -Raw -LiteralPath $skillPath
$skillAgent = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/skills/hmasd-review-round/agents/openai.yaml')
foreach ($required in @(
    'Project-Manager-direct transport',
    'active Project Manager',
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'FORMAL_RESULT_SCIENTIFIC_DISPOSITION',
    'hmasd-pro-response-monitor',
    'metadata-only JSONL sentinel',
    'scripts/hmasd_pro_response_sentinel.py record',
    'native child does not inherit the in-app-browser binding',
    'ordinary task wakeups',
    'timer loop or emit pending progress messages',
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
    'monitor terminal -> exact raw -> provenance intake -> monitor absence -> role-defined disposition realization')) {
    if (-not $skill.Contains($required)) { throw "Review Skill missing: $required" }
}
if ($skill -match '(?i)\bcontroller\b|hmasd-dispatch-task|hmasd-experiment-monitor') {
    throw 'Review Skill retains a retired relay or monitor surface'
}
foreach ($required in @(
    'hmasd-pro-response-monitor',
    'Never activate Answer now',
    'PM-brokered JSONL sentinel',
    'child never opens the browser',
    'without PM reinterpretation')) {
    if (-not $skillAgent.Contains($required)) {
        throw "Review Skill agent prompt missing: $required"
    }
}

$sentinel = Join-Path $repo 'scripts/hmasd_pro_response_sentinel.py'
if (-not (Test-Path -LiteralPath $sentinel -PathType Leaf)) {
    throw 'Pro-response sentinel harness is missing'
}

if (Test-Path -LiteralPath (Join-Path $repo '.agents/skills/hmasd-review-round/scripts/render_review_heartbeat.ps1')) {
    throw 'Retired PM heartbeat script remains'
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
