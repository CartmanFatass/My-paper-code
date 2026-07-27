$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$codePmPath = Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md'
$operationsPath = Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md'
$oldPmPath = Join-Path $repo '.agents/roles/PROJECT_MANAGER.md'
$oldOperatorPath = Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md'
$codePm = Get-Content -Raw -LiteralPath $codePmPath
$operations = Get-Content -Raw -LiteralPath $operationsPath
$workflow = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$agileNormalized = $agile -replace '\s+', ' '
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$assertionNormalized = $assertion -replace '\s+', ' '
$handoff = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/RESTART_HANDOFF.md')

if ((Test-Path $oldPmPath) -or (Test-Path $oldOperatorPath)) {
    throw 'Retired manager role path remains live'
}

$routerRequired = @(
    'code_project_manager_session=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'research_operations_manager_session=019f9c6a-9401-7ae0-ace5-dd827dccba2b',
    'code_project_manager_code_authority=exclusive',
    'code_project_manager_technical_acceptance_authority=exclusive',
    'code_project_manager_runtime_authority=none',
    'code_project_manager_current_work_read=bounded_read_only_on_demand',
    'code_project_manager_current_work_write_authority=none',
    'research_operations_manager_runtime_authority=exclusive',
    'research_operations_manager_current_work_authority=exclusive',
    'research_operations_manager_external_review_transport_authority=exclusive',
    'research_operations_manager_mechanical_result_acceptance=exclusive',
    'research_operations_manager_code_authority=none',
    'research_operations_manager_code_acceptance_authority=none',
    'operational_recovery_owner=research_operations_manager',
    '.agents/roles/CODE_PROJECT_MANAGER.md',
    '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md'
)
foreach ($required in $routerRequired) {
    if (-not $agents.Contains($required)) { throw "AGENTS split authority missing: $required" }
}

$codeRequired = @(
    'role=code_project_manager',
    'code_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'runtime_authority=none',
    'current_work_read=bounded_read_only_on_demand',
    'current_work_write_authority=none',
    'scientific_authority=none',
    'git_execution=direct_for_code_tests_and_code_science_index',
    'code_children=code_scout|implementer|reviewer|verifier',
    'may read `docs/project/CURRENT_WORK.md` only to check the current',
    'not replace a complete incoming assignment',
    'Never edit, stage, commit or advance',
    'CODE_ACCEPTED',
    'CODE_SCIENCE_INDEX.md',
    'Research Operations Manager',
    'Workflow Design Manager'
)
foreach ($required in $codeRequired) {
    if (-not $codePm.Contains($required)) { throw "Code Project Manager contract missing: $required" }
}

$operationsRequired = @(
    'role=research_operations_manager',
    'runtime_authority=exclusive',
    'current_work_authority=exclusive',
    'external_review_transport_authority=exclusive',
    'experiment_dispatch_and_result_routing=exclusive',
    'mechanical_result_acceptance=exclusive',
    'code_authority=none',
    'code_acceptance_authority=none',
    'scientific_authority=none',
    'MECHANICALLY_VALID_RESULT',
    'OPERATIONAL_FAILURE',
    'CODE_DIAGNOSIS_REQUIRED',
    'EXTERNAL_TECHNICAL_BLOCKER',
    'Use `$hmasd-review-round` directly in this task',
    'Code Project Manager',
    'Workflow Design Manager'
)
foreach ($required in $operationsRequired) {
    if (-not $operations.Contains($required)) { throw "Research Operations Manager contract missing: $required" }
}

$forbiddenCodePm = @(
    'runtime_authority=exclusive',
    'current_work_authority=exclusive',
    'external_review_transport_authority=exclusive',
    'experiment_dispatch_and_result_routing=exclusive'
)
foreach ($forbidden in $forbiddenCodePm) {
    if ($codePm.Contains($forbidden)) { throw "Code Project Manager claims operations authority: $forbidden" }
}
if ($codePm.Contains('Never load `docs/project/CURRENT_WORK.md`')) {
    throw 'Code Project Manager retains the obsolete CURRENT_WORK read prohibition'
}

$forbiddenOperations = @(
    'code_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'git_execution=direct_for_code_tests_and_code_science_index'
)
foreach ($forbidden in $forbiddenOperations) {
    if ($operations.Contains($forbidden)) { throw "Research Operations Manager claims code authority: $forbidden" }
}

if (-not $workflow.Contains('fixed Code Project Manager or Research') -or
    -not $workflow.Contains('Operations Manager session that made the request')) {
    throw 'Workflow Design Manager does not return to either exact requester'
}
if (-not $agileNormalized.Contains('Code Project Manager alone accepts code') -or
    -not $agileNormalized.Contains('Research Operations Manager owns runtime and transport')) {
    throw 'Agile Skill does not preserve code/runtime split'
}
if ($agile.Contains('External Review Operator') -or
    -not $agileNormalized.Contains('returns its exact commit and index to Research Operations Manager') -or
    -not $agileNormalized.Contains('Research Operations Manager routes the one comparison-only')) {
    throw 'Agile Skill retains a stale or ambiguous review route'
}
if ($assertionNormalized.Contains('Research Operations Manager executes the smallest repair') -or
    -not $assertionNormalized.Contains('sends one exact correction assignment to Code Project Manager') -or
    -not $assertionNormalized.Contains('After `CODE_ACCEPTED`')) {
    throw 'Alignment mismatch repair ownership is ambiguous'
}
if (-not $handoff.Contains('Code Project Manager inspects only the G35 diff') -or
    -not $handoff.Contains('and updates the code-science index') -or
    -not $handoff.Contains('docs/research/designs/CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_CODE_SCIENCE_INDEX.md') -or
    -not $handoff.Contains('stages exactly the three G35 code/index paths') -or
    -not $handoff.Contains('returns `CODE_ACCEPTED`') -or
    -not $handoff.Contains('Research Operations Manager dispatches exactly one fresh') -or
    $handoff.Contains('Research Operations Manager updates the G35 prelaunch note, code-science index')) {
    throw 'Restart handoff assigns code work to the wrong role'
}
if ($workflow.Contains('Project-Manager workflow-design assignment')) {
    throw 'Workflow Design Manager retains the retired requester identity'
}

$parentContracts = @{
    '.agents/roles/CODE_SCOUT.md' = 'parent=code_project_manager'
    '.agents/roles/IMPLEMENTER.md' = 'parent=code_project_manager'
    '.agents/roles/REVIEWER.md' = 'parent=code_project_manager'
    '.agents/roles/VERIFIER.md' = 'parent=code_project_manager'
    '.agents/roles/EXPERIMENT_OPERATOR.md' = 'parent=research_operations_manager'
    '.agents/roles/PRO_RESPONSE_MONITOR.md' = 'parent=research_operations_manager'
}
foreach ($entry in $parentContracts.GetEnumerator()) {
    $text = Get-Content -Raw -LiteralPath (Join-Path $repo $entry.Key)
    if (-not $text.Contains($entry.Value)) {
        throw "Child ownership mismatch: $($entry.Key) requires $($entry.Value)"
    }
}

Write-Output 'HMASD_CODE_PROJECT_MANAGER_CONTRACT_OK'
