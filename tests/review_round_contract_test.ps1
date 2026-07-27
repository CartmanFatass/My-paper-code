[CmdletBinding()]
param([switch]$RoutingOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$registry = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') | ConvertFrom-Json
if ($registry.schema_version -ne 38 -or
    $registry.round_operator.kind -ne 'research_operations_manager_transport_mode' -or
    $registry.round_operator.external_scientific_decision -ne 'external_pro_binding_within_user_boundary' -or
    $registry.round_operator.decision_intake -ne 'same_task_exact_raw_routing' -or
    $registry.round_operator.git_boundary_owner -ne 'research_operations_manager' -or
    $registry.transport_contract.transport_owner -ne 'research_operations_manager' -or
    $registry.transport_contract.response_monitor_agent_type -ne 'hmasd-pro-response-monitor' -or
    $registry.transport_contract.response_monitor_model -ne 'gpt-5.6-luna' -or
    $registry.transport_contract.response_monitor_effort -ne 'low' -or
    $registry.transport_contract.response_monitor_observation -ne 'research_operations_manager_brokered_jsonl_sentinel' -or
    $registry.transport_contract.response_monitor_sentinel_tool -ne 'scripts/hmasd_pro_response_sentinel.py' -or
    $registry.reviewers.open_divergent.transport -ne 'research_operations_manager_in_app_browser') {
    throw 'Research Operations Manager transport registry mismatch'
}

$skillPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$skill = Get-Content -Raw -LiteralPath $skillPath
$operations = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md')
$skillNormalized = $skill -replace '\s+', ' '
$operationsNormalized = $operations -replace '\s+', ' '
$skillAgent = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/skills/hmasd-review-round/agents/openai.yaml')
foreach ($required in @(
    'Operations-manager transport mode',
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'FORMAL_RESULT_SCIENTIFIC_DISPOSITION',
    'hmasd-pro-response-monitor',
    'operations-manager-brokered metadata sentinel',
    'monitor_assignment_token',
    'sole monitor assignment identity',
    '--assignment-token <exact-init-token>',
    'Do not parse, shorten or rebuild the token',
    'returns that exact fence identity',
    'scripts/hmasd_pro_response_sentinel.py record',
    'native child does not inherit',
    'in-app-browser',
    'ordinary task wakeups',
    'timer loop or emit pending progress messages',
    '$browser:control-in-app-browser',
    'VERIFY_FRESHNESS_FENCE',
    'An accepted matching fence is never resubmitted',
    'same tab once for that stuck episode',
    'Reloading never proves the matching fence absent and never authorizes submission',
    'a new observed stuck episode',
    'instead of a reload loop',
    'two stable snapshots',
    'at least three seconds',
    'Never activate `Answer now`',
    'its presence or absence is neutral',
    'Only Pro''s natural completion is admissible',
    'transport diagnostic',
    'materialize them from `stage_commit`',
    'not from the current working tree',
    'resume operations loop',
    'monitor terminal -> exact raw -> provenance intake -> monitor absence')) {
    if (-not $skillNormalized.Contains($required)) { throw "Review Skill missing: $required" }
}
foreach ($forbidden in @(
    'reload until',
    'refresh until',
    'reload proves the matching fence absent',
    'reload authorizes submission',
    'watch --state <absolute-jsonl> --conversation-id')) {
    if ($skillNormalized.Contains($forbidden)) {
        throw "Review Skill permits unsafe stuck-page recovery: $forbidden"
    }
}

$monitorRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/PRO_RESPONSE_MONITOR.md')
$monitorProfile = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-pro-response-monitor.toml')
foreach ($required in @(
    'monitor_assignment_token',
    '--assignment-token <exact-init-token>',
    'never parses, shortens or reconstructs',
    'exact identity decoded and verified from the assignment token')) {
    if (-not $monitorRole.Contains($required)) {
        throw "Pro-response monitor role missing opaque identity transport: $required"
    }
}
foreach ($required in @(
    'monitor_assignment_token',
    'Copy the token unchanged into `--assignment-token`',
    'never parse,',
    'exact Sentinel-verified fence identity')) {
    if (-not $monitorProfile.Contains($required)) {
        throw "Pro-response monitor profile missing opaque identity transport: $required"
    }
}
foreach ($required in @(
    'browser_stuck_page_recovery=same_tab_reload_once_per_observed_episode',
    'browser_reload_fence_effect=none',
    'Reloading never proves a freshness fence absent and never authorizes submission')) {
    if (-not $operationsNormalized.Contains($required)) {
        throw "Research Operations Manager role missing stuck-page recovery boundary: $required"
    }
}
if ($skill -match '(?i)\bcontroller\b|hmasd-dispatch-task|hmasd-experiment-monitor|fixed Project Manager session|completion notification') {
    throw 'Review Skill retains a retired relay or monitor surface'
}
foreach ($required in @(
    'hmasd-pro-response-monitor',
    'Never activate Answer now',
    'operations-manager-brokered JSONL sentinel',
    'child never opens the browser',
    'resume the local operations loop')) {
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

if ($RoutingOnly) {
    Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
    return
}

$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
$head = (& git.exe -C $repo rev-parse HEAD).Trim()
$boundary = & $boundaryVerifier `
    -Commit $head `
    -QuestionPath 'docs/external-review/rounds/20260725_uav_localized_demand_burst_g33_design_assertion_audit/20_PRO_OPEN_QUESTION.md' `
    -Remote $repo `
    -Branch 'aggressive' `
    -RepoRoot $repo | ConvertFrom-Json
if ($boundary.status -ne 'REMOTE_EVIDENCE_READY' -or
    $boundary.commit -ne $head -or
    @($boundary.inspected_paths).Count -ne 20 -or
    @($boundary.inspected_paths) -notcontains 'config_1.py' -or
    @($boundary.inspected_paths) -notcontains 'envs/pettingzoo/scenario7_energy_aware.py') {
    throw 'Review boundary verifier failed a reachable exact commit'
}

Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
