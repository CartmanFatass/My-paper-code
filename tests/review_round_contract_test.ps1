[CmdletBinding()]
param([switch]$RoutingOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$registry = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') | ConvertFrom-Json
if ($registry.schema_version -ne 37 -or
    $registry.round_operator.kind -ne 'dedicated_external_review_operator_task' -or
    $registry.round_operator.external_scientific_decision -ne 'external_pro_binding_within_user_boundary' -or
    $registry.round_operator.decision_intake -ne 'project_manager_exact_raw_file_routing' -or
    $registry.round_operator.git_boundary_owner -ne 'project_manager' -or
    $registry.intertask_transport_contract.transport_owner -ne 'dedicated_external_review_operator' -or
    $registry.intertask_transport_contract.cross_task_routing_skill -ne '$hmasd-cross-task-routing' -or
    $registry.intertask_transport_contract.target_identity -ne 'fixed_role_session_from_AGENTS.md' -or
    $registry.intertask_transport_contract.route_cache -ne 'forbidden' -or
    $registry.intertask_transport_contract.model_thinking_preservation -ne 'pre_send_read_only_probe_explicit_echo' -or
    $registry.intertask_transport_contract.live_settings_source -ne 'read_only_local_codex_state' -or
    $registry.intertask_transport_contract.live_settings_probe -ne '.agents/skills/hmasd-cross-task-routing/scripts/read_codex_thread_settings.py' -or
    $registry.intertask_transport_contract.live_settings_cache -ne 'forbidden' -or
    $registry.intertask_transport_contract.settings_unavailable_action -ne 'fail_closed_no_send' -or
    $registry.intertask_transport_contract.tool_call_visibility -ne 'explicit_model_and_thinking_parameters' -or
    $registry.intertask_transport_contract.payload_route_settings -ne 'forbidden' -or
    $registry.intertask_transport_contract.route_replacement -ne 'explicit_user_direction_then_workflow_design_commit' -or
    $registry.intertask_transport_contract.response_monitor_agent_type -ne 'hmasd-pro-response-monitor' -or
    $registry.intertask_transport_contract.response_monitor_model -ne 'gpt-5.6-luna' -or
    $registry.intertask_transport_contract.response_monitor_effort -ne 'low' -or
    $registry.intertask_transport_contract.response_monitor_observation -ne 'external_review_operator_brokered_jsonl_sentinel' -or
    $registry.intertask_transport_contract.response_monitor_sentinel_tool -ne 'scripts/hmasd_pro_response_sentinel.py' -or
    $registry.reviewers.open_divergent.transport -ne 'external_review_operator_in_app_browser') {
    throw 'Dedicated External Review Operator registry mismatch'
}

$skillPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$skill = Get-Content -Raw -LiteralPath $skillPath
$skillAgent = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/skills/hmasd-review-round/agents/openai.yaml')
foreach ($required in @(
    'Dedicated-operator transport',
    '$hmasd-cross-task-routing',
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'FORMAL_RESULT_SCIENTIFIC_DISPOSITION',
    'hmasd-pro-response-monitor',
    'operator-brokered metadata sentinel',
    'scripts/hmasd_pro_response_sentinel.py record',
    'native child does not inherit',
    'in-app-browser',
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
    'probe-confirmed Project-Manager completion notification',
    'monitor terminal -> exact raw -> provenance intake -> monitor absence')) {
    if (-not $skill.Contains($required)) { throw "Review Skill missing: $required" }
}
if ($skill -match '(?i)\bcontroller\b|hmasd-dispatch-task|hmasd-experiment-monitor|Project-Manager-direct transport') {
    throw 'Review Skill retains a retired relay or monitor surface'
}
foreach ($required in @(
    'hmasd-pro-response-monitor',
    'Never activate Answer now',
    'operator-brokered JSONL sentinel',
    'child never opens the browser',
    'fixed Project Manager session',
    'live model and thinking in the visible tool call')) {
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
