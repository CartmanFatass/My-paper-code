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

foreach ($required in @(
    'sole persistent project task',
    'There is no Controller, persistent Monitor',
    'project_manager_git_authority=direct',
    'project_manager_external_review_transport=direct',
    'project_manager_experiment_orchestration=direct_via_registered_child',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'per_file_hash_handoff=forbidden',
    'same_file_concurrent_writes=forbidden')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}
foreach ($required in @(
    'active_assignment_id=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_ITERATION_2_OPERATIONAL_REPAIR',
    'iterations_remaining=4',
    'conclusion_bearing_iterations_consumed_by_failed_r1=0',
    'intermediate_authorization_prompts=forbidden',
    'formal_run_status=r1_operational_error_no_valid_analysis',
    'formal_r1_scientific_disposition=none',
    'restart_policy=clean_run_root_after_repair_commit_no_cross_commit_resume',
    'workflow_hash_validation=disabled')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing: $required" }
}
foreach ($required in @(
    'formal_run_status=operational_repair_pending_clean_operator_launch',
    'bounded five-second window',
    'hmasd-experiment-operator',
    'emits no intermediate',
    'fresh r2 run root')) {
    if (-not $plan.Contains($required)) { throw "Implementation plan missing: $required" }
}
foreach ($required in @(
    'root Project Manager directly stages, commits, and pushes',
    'Native children never run Git',
    'fixed native child, not a persistent task')) {
    if (-not $context.Contains($required)) { throw "Agent context missing: $required" }
}
foreach ($required in @(
    'superpowers_execution=disabled',
    'workflow_hash_validation=disabled',
    'Project Manager integrates the exact accepted',
    'no relay or completion receipt exists')) {
    if (-not $agile.Contains($required)) { throw "Agile Skill missing: $required" }
}

foreach ($text in @($agents, $current, $context, $plan, $agile)) {
    if ($text -match '(?m)^\w+_sha256=' -or $text.Contains('path_hash_source_status')) {
        throw 'Active workflow retains a hash handoff'
    }
    if ($text.Contains('superpowers_execution=enabled')) {
        throw 'Active workflow enables generic Superpowers execution'
    }
}

Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
