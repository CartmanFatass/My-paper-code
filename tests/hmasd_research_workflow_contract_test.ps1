[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Stable workflow surfaces only. Scientific assignments and result labels are
# deliberately not hard-coded here because CURRENT_WORK is the active line.
# Project Skills live under .claude/skills/ so Claude Code resolves them. Only
# the hmasd-* namespace is project workflow; third-party packs are ignored here.
$skills = @(Get-ChildItem (Join-Path $repo '.claude/skills') -Directory -Filter 'hmasd-*' |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @('hmasd-agile-research-development', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) {
    throw "Unexpected active Skill set: $($skills -join ',')"
}
if (Test-Path (Join-Path $repo '.agents/skills/hmasd-agile-research-development')) {
    throw 'A project Skill remains at its pre-migration .agents/skills location'
}

# Every bounded role is a Claude Code subagent definition.
$agentDefs = @(Get-ChildItem (Join-Path $repo '.claude/agents') -File -Filter 'hmasd-*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedAgents = @(
    'hmasd-code-scout.md', 'hmasd-exp-recorder.md', 'hmasd-experiment-operator.md',
    'hmasd-implementer.md', 'hmasd-monitor.md', 'hmasd-patcher.md',
    'hmasd-review-exchanger.md', 'hmasd-reviewer.md', 'hmasd-scout.md',
    'hmasd-verifier.md') | Sort-Object
if (Compare-Object $expectedAgents $agentDefs) {
    throw "Unexpected subagent roster: $($agentDefs -join ',')"
}
if (Test-Path (Join-Path $repo '.codex')) {
    throw 'The retired Codex agent runtime remains on the active line'
}

$roles = @(Get-ChildItem (Join-Path $repo '.agents/roles') -File -Filter '*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedRoles = @('EXPERIMENT_OPERATOR.md', 'EXTERNAL_PRO.md', 'PROJECT_MANAGER.md') | Sort-Object
if (Compare-Object $expectedRoles $roles) {
    throw "Unexpected active role set: $($roles -join ',')"
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')
$context = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/AGENT_CONTEXT.md')
$plan = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/IMPLEMENTATION_PLAN.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.claude/skills/hmasd-agile-research-development/SKILL.md')
$pmRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PROJECT_MANAGER.md')

foreach ($required in @(
    'single project owner at any moment',
    'has no persistent task',
    'There is no Controller, persistent Monitor',
    'project_manager_git_authority=direct',
    'project_manager_external_review_transport=registration_then_exchanger',
    'scientific_decision_authority=external_pro',
    'local_conversation_scientific_authority=none',
    '## Execution modes',
    'project_manager_experiment_orchestration=direct_via_registered_child',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'iteration_report_language=zh-CN',
    'iteration_report_path=docs/report/ITERATION_<n>.md',
    'not another review, approval or scientific evidence source',
    'per_file_hash_handoff=forbidden',
    'same_file_concurrent_writes=forbidden',
    '### Crossing the boundary',
    'converge with External Pro',
    '## Context compaction',
    'end of a complete iteration')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}

# Convergence must stay distinguishable from a fence, or the single-fence rule
# quietly becomes "resubmit whenever the answer is unsatisfying".
$reviewSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.claude/skills/hmasd-review-round/SKILL.md')
foreach ($required in @(
    '## Convergence turns',
    'A convergence turn is not a fence',
    '22_PRO_CONVERGENCE.md',
    'exactly one per round, never resubmitted')) {
    if (-not $reviewSkill.Contains($required)) { throw "Review Skill missing: $required" }
}

foreach ($required in @(
    'active_assignment_id=',
    'next_boundary=',
    'autonomous_research_grant=',
    'iterations_remaining=',
    'conclusion_bearing_iterations_consumed=',
    'execution_mode=',
    'git_integration_status=project_manager_direct_authorized',
    'experiment_operator_fallback=forbidden',
    'iteration_report_requirement=required_before_successor',
    'uav_user_scope=transient_demand_coverage_plus_charging_roster_change_plus_temporary_detach_failure_robustness',
    'uav_physical_fleet_boundary=fixed_slots_distinct_from_dynamic_service_roster',
    'workflow_hash_validation=disabled')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing: $required" }
}

$remainingMatch = [regex]::Match($current, '(?m)^iterations_remaining=(\d+)\s*$')
$consumedMatch = [regex]::Match($current, '(?m)^conclusion_bearing_iterations_consumed=(\d+)\s*$')
if (-not $remainingMatch.Success -or -not $consumedMatch.Success) {
    throw 'CURRENT_WORK iteration accounting is not a nonnegative integer contract'
}
if ($current.Contains('autonomous_research_grant=ACTIVE_') -and
    [int]$remainingMatch.Groups[1].Value -le 0) {
    throw 'An active autonomous grant has no remaining conclusion-bearing iterations'
}

# The declared mode and the pause contract it implies must agree. Left
# unchecked these drift apart and the loop pauses in the wrong places.
$modeMatch = [regex]::Match($current, '(?m)^execution_mode=(authorized|unauthorized)\s*$')
if (-not $modeMatch.Success) {
    throw 'CURRENT_WORK does not declare execution_mode as authorized or unauthorized'
}
$grantActive = $current.Contains('autonomous_research_grant=ACTIVE_')
if ($modeMatch.Groups[1].Value -eq 'authorized') {
    if (-not $grantActive) {
        throw 'Authorized mode declared without an ACTIVE_ autonomous grant'
    }
    if (-not $current.Contains('intermediate_authorization_prompts=forbidden')) {
        throw 'Authorized mode must record intermediate_authorization_prompts=forbidden'
    }
}
else {
    if ($grantActive) {
        throw 'Unauthorized mode declared while an ACTIVE_ grant is still recorded'
    }
    if (-not $current.Contains('intermediate_authorization_prompts=required_at_plan_and_result')) {
        throw 'Unauthorized mode must record the plan and result checkpoints'
    }
}

foreach ($required in @(
    'backend=cpu',
    'torch_threads=1',
    'docs/research/designs/',
    'Generic Superpowers execution')) {
    if (-not $plan.Contains($required)) { throw "Implementation plan missing: $required" }
}

foreach ($required in @(
    'root Project Manager directly stages, commits, and pushes',
    'Subagents never run Git',
    'fixed subagent, not a persistent task',
    '.claude/skills/hmasd-agile-research-development/SKILL.md',
    '.claude/agents/*.md')) {
    if (-not $context.Contains($required)) { throw "Agent context missing: $required" }
}
foreach ($required in @(
    'docs/report/ITERATION_<n>.md',
    'creates a second acceptance owner',
    'blocks on separate approval')) {
    if (-not $pmRole.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'superpowers_execution=disabled',
    'workflow_hash_validation=disabled',
    'Project Manager integrates the exact accepted',
    'no relay or completion receipt exists')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing: $required" }
}

foreach ($text in @($agents, $current, $context, $plan, $agile, $pmRole)) {
    if ($text -match '(?m)^\w+_sha256=' -or $text.Contains('path_hash_source_status')) {
        throw 'Active workflow retains a hash handoff'
    }
    if ($text.Contains('superpowers_execution=enabled')) {
        throw 'Active workflow enables generic Superpowers execution'
    }
}

$reportReadme = Join-Path $repo 'docs/report/README.md'
if (-not (Test-Path -LiteralPath $reportReadme -PathType Leaf)) {
    throw 'Iteration-report README is missing'
}
$readme = Get-Content -Raw -Encoding UTF8 -LiteralPath $reportReadme
foreach ($required in @(
    'iteration_report_language=zh-CN',
    'separate_approval=not_required',
    'additional_review=false')) {
    if (-not $readme.Contains($required)) { throw "Iteration-report contract missing: $required" }
}

$consumed = [int]$consumedMatch.Groups[1].Value
for ($iteration = 1; $iteration -le $consumed; $iteration++) {
    $path = Join-Path $repo "docs/report/ITERATION_$iteration.md"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing Chinese iteration report: ITERATION_$iteration.md"
    }
    $report = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    if (-not [regex]::IsMatch($report, '[\p{IsCJKUnifiedIdeographs}]')) {
        throw "ITERATION_$iteration.md is not a Chinese report"
    }
}

foreach ($retired in @(
    'ha_ctse_process/temporal_duty_g1.py',
    'ha_ctse_process/ehc_g1.py',
    'scripts/run_access_positive_ehc_g1.py',
    'tests/ha_ctse_process_temporal_duty_g1_test.py',
    'tests/ha_ctse_process_ehc_g1_test.py',
    'tests/run_access_positive_ehc_g1_test.py',
    'ha_ctse_process/cross_lifecycle_handoff_g2.py',
    'ha_ctse_process/ehc_handoff_g2.py',
    'scripts/run_cross_lifecycle_handoff_g2.py',
    'tests/ha_ctse_process_cross_lifecycle_handoff_g2_test.py',
    'tests/ha_ctse_process_ehc_handoff_g2_test.py',
    'tests/run_cross_lifecycle_handoff_g2_test.py',
    'ha_ctse_process/useful_effect_roster_g3.py',
    'scripts/run_useful_effect_roster_g3.py',
    'tests/ha_ctse_process_useful_effect_roster_g3_test.py',
    'tests/run_useful_effect_roster_g3_test.py')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Closed executable remains on the active line: $retired"
    }
}

Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
