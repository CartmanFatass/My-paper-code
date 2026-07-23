[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @('hmasd-agile-research-development', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) {
    throw "Unexpected active Skill set: $($skills -join ',')"
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
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$pmRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/PROJECT_MANAGER.md')

foreach ($required in @(
    'sole persistent project task',
    'There is no Controller, persistent Monitor',
    'project_manager_git_authority=direct',
    'project_manager_external_review_transport=direct',
    'project_manager_experiment_orchestration=direct_via_registered_child',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'iteration_report_language=zh-CN',
    'iteration_report_path=docs/report/ITERATION_<n>.md',
    'not another review, approval or scientific evidence source',
    'per_file_hash_handoff=forbidden',
    'same_file_concurrent_writes=forbidden')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($required in @(
    'active_assignment_id=USEFUL_EFFECT_ROSTER_G3_IMPLEMENTATION',
    'iterations_remaining=2',
    'conclusion_bearing_iterations_consumed=3',
    'intermediate_authorization_prompts=forbidden',
    'formal_compute_status=not_launchable_until_g3_implementation_acceptance',
    'g2_formal_result=TEAM_REC_SUFFICIENT_HANDOFF_G2',
    'g2_g_team_ci95=[0.0,0.0]',
    'g2_g_link_ci95=[0.5,0.5]',
    'g3_gate_contract=docs/research/designs/ASYNC_COMMITMENT_ROSTER_G3.md',
    'g3_gate_result=PASS_ASYNC_ROSTER_INFORMATION_GATE_G3',
    'g3_gate_cases=18400',
    'g3_gate_tests=5_passed',
    'g3_formal_contract=docs/research/designs/USEFUL_EFFECT_ROSTER_G3.md',
    'g3_primary_arm=ROSTER_ATTN',
    'g3_primary_comparator=TEAM_REC',
    'iteration_report_status=iterations_1_to_3_complete',
    'latest_iteration_report=docs/report/ITERATION_3.md',
    'workflow_hash_validation=disabled')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing: $required" }
}
foreach ($required in @(
    'formal_run_status=not_launchable_until_implementation_acceptance',
    'active_implementation=USEFUL_EFFECT_ROSTER_G3',
    'ROSTER_ATTN/TEAM_REC/NO_ROSTER',
    'primary_comparator=TEAM_REC',
    'Implementation and exercise consume zero iterations')) {
    if (-not $plan.Contains($required)) { throw "Implementation plan missing: $required" }
}
foreach ($required in @(
    'root Project Manager directly stages, commits, and pushes',
    'Native children never run Git',
    'fixed native child, not a persistent task')) {
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

$reportResults = @(
    @{ Name = 'ITERATION_1.md'; Result = 'NO_ACCESS_THIS_BENCHMARK' },
    @{ Name = 'ITERATION_2.md'; Result = 'ORDINARY_EXPLANATION_G1' },
    @{ Name = 'ITERATION_3.md'; Result = 'TEAM_REC_SUFFICIENT_HANDOFF_G2' }
)
foreach ($item in $reportResults) {
    $path = Join-Path $repo (Join-Path 'docs/report' $item.Name)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing Chinese iteration report: $($item.Name)"
    }
    $report = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    if (-not [regex]::IsMatch($report, '[\p{IsCJKUnifiedIdeographs}]')) {
        throw "$($item.Name) is not a Chinese report"
    }
    foreach ($required in @(
        'source_commit=',
        'backend=cpu',
        'formal=true',
        $item.Result)) {
        if (-not $report.Contains($required)) {
            throw "$($item.Name) missing: $required"
        }
    }
}

foreach ($retired in @(
    'ha_ctse_process/temporal_duty_g1.py',
    'ha_ctse_process/ehc_g1.py',
    'scripts/run_access_positive_ehc_g1.py',
    'tests/ha_ctse_process_temporal_duty_g1_test.py',
    'tests/ha_ctse_process_ehc_g1_test.py',
    'tests/run_access_positive_ehc_g1_test.py')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Closed G1 executable remains on the active line: $retired"
    }
}

Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
