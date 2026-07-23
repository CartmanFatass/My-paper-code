[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expected = @('hmasd-dispatch-task', 'hmasd-experiment-monitor',
    'hmasd-review-round') | Sort-Object
if (Compare-Object $expected $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }

$current = Get-Content (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
$legacyToken = 'O' + 'MP'
if ($current -match "(?i)\b$legacyToken\b|\.omp") { throw 'Current control plane retains a legacy execution route' }
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
foreach ($role in @('project_manager', 'experiment_monitor')) {
    if ($roles.roles.$role.registration_status -ne 'ACTIVE') { throw "Inactive registered role: $role" }
}
if ($roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Native Spark Monitor registry mismatch'
}

$dispatcher = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('controller <-> project_manager', 'controller <-> experiment_monitor',
    'Controller-direct external review', '$hmasd-review-round',
    'source_boundary=local_and_remote_aggressive_tip',
    'gpt-5.3-codex-spark', 'PROJECT_MANAGER_DELIVERY_BLOCKED')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
if ($dispatcher -match '(?i)\bOMP\b|agent://|history://') { throw 'Dispatcher retains a legacy task-delivery path' }
if ($dispatcher.Contains('open_divergent_exchange') -or $dispatcher.Contains('$hmasd-review-exchange')) {
    throw 'Dispatcher retains the retired Exchange surface'
}

$monitor = Get-Content (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw
foreach ($required in @('ETA', '10 minutes', 'delete the heartbeat', 'EXPERIMENT_MONITOR',
    'Do not modify repository files', '$hmasd-experiment-monitor', 'RECOVERY_ATTEMPT',
    'recovery_exhausted=true')) {
    if (-not $monitor.Contains($required)) { throw "Monitor Skill missing: $required" }
}

if (Test-Path (Join-Path $repo ('.o' + 'mp'))) { throw 'Legacy execution directory remains' }

$batteryDocuments = @{
    'docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'K=1', 'C_total', 'I_TV')
    'docs/project/IMPLEMENTATION_PLAN.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'C_total', 'LCB(C_total_KEEP)>0',
        'LCB(C_total_RENEW)>0')
    'docs/project/CURRENT_WORK.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'four conclusion-bearing iterations')
}
foreach ($relative in $batteryDocuments.Keys) {
    $content = Get-Content (Join-Path $repo $relative) -Raw
    foreach ($required in $batteryDocuments[$relative]) {
        if (-not $content.Contains($required)) {
            throw "Battery contract is not reconciled in ${relative}: $required"
        }
    }
}
if ($current.Contains('One unresolved question stands against the result contract')) {
    throw 'Retired behavioral-battery question remains active in CURRENT_WORK'
}
$agentContext = Get-Content (Join-Path $repo 'docs/project/AGENT_CONTEXT.md') -Raw
foreach ($required in @('C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    'torch 2.7.0+cpu', 'CPU', 'torch threads 1')) {
    if (-not $agentContext.Contains($required)) { throw "Agent context missing CPU contract: $required" }
}
$agents = Get-Content (Join-Path $repo 'AGENTS.md') -Raw
foreach ($required in @('semantic_author=project_manager',
    'artifact_scope=reviewer_visible_code_side', 'repair_owner=project_manager',
    'exact PM-accepted files unchanged', 'pm_acceptance_authority=exclusive',
    'controller_validation_authority=none')) {
    if (-not $agents.Contains($required)) { throw "Controller/PM ownership boundary missing: $required" }
    if (-not $agentContext.Contains($required)) { throw "Agent context ownership boundary missing: $required" }
}
$reviewRound = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$reviewReadme = Get-Content (Join-Path $repo 'docs/external-review/README.md') -Raw
$principles = Get-Content (Join-Path $repo 'docs/project/ALGORITHM_PRINCIPLES.md') -Raw
foreach ($content in @($agents, $agentContext, $dispatcher, $reviewRound, $reviewReadme, $principles)) {
    foreach ($required in @('pm_acceptance_authority=exclusive',
        'controller_validation_authority=none')) {
        if (-not $content.Contains($required)) { throw "PM exclusive acceptance boundary missing: $required" }
    }
}
foreach ($forbidden in @('Controller verifies it independently',
    'Controller mechanically verifies author markers, required fields',
    'Controller validates and transmits those files',
    'mechanically validates the PM-authored package',
    'Controller checks provenance, required fields')) {
    foreach ($content in @($agents, $agentContext, $dispatcher, $reviewRound, $reviewReadme, $principles)) {
        if ($content.Contains($forbidden)) { throw "Controller retains PM validation authority: $forbidden" }
    }
}
if (-not $agentContext.Contains('does not apply to protected scientific choices')) {
    throw 'Agent context reasonable-choice rule still reaches protected science'
}
$portfolio = Get-Content (Join-Path $repo 'docs/research/cdc/IDEA_PORTFOLIO.md') -Raw
foreach ($required in @('ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1', 'C-BASE', 'C-LINK-NULL')) {
    if (-not $portfolio.Contains($required)) { throw "Portfolio missing Pro intake: $required" }
}
$conjectures = Get-Content (Join-Path $repo 'docs/research/cdc/CONJECTURES.md') -Raw
foreach ($content in @($conjectures, $portfolio)) {
    foreach ($required in @('same benchmark', 'information-matched stronger')) {
        if (-not $content.Contains($required)) { throw "C-BASE authority drift: missing $required" }
    }
}
$roundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_formal_result_review'
$rawHash = (Get-FileHash (Join-Path $roundRoot '21_PRO_OPEN_RAW.md') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($rawHash -ne 'd63427fb0fab5ffb1f393eb62370358cda449e6f1dfc8d57bc937ba46493942e') {
    throw "External Pro raw hash mismatch: $rawHash"
}
foreach ($relative in @(
    'docs/external-review/rounds/20260722_ehc_formal_result_review/30_EVIDENCE_RECONCILIATION.md',
    'docs/external-review/rounds/20260722_ehc_formal_result_review/50_DISPOSITION.md')) {
    if (-not (Test-Path (Join-Path $repo $relative) -PathType Leaf)) {
        throw "Missing completed Pro intake file: $relative"
    }
}
foreach ($required in @('external-Pro result review is complete',
    'ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1',
    'cannot authorize code, science, a successor, or iteration-2',
    'Formal compute remains unauthorized')) {
    if (-not $current.Contains($required)) { throw "Current boundary missing Pro intake: $required" }
}
foreach ($required in @('Controller-authored G1 clarification is transport-only',
    'cannot be adopted', 'PM-owned G1 external-Pro raw is archived',
    'PM-authored focused Pro package was transported',
    'exact raw and mechanical intake are archived',
    'exclusively accepted the code-side disposition',
    'ALGORITHM_SCOPE_RECONCILED_EXECUTION_CONTRACT_DEFERRED',
    'EHC_MEASUREMENT_COUNTEREXAMPLE_DERIVATION',
    'Formal compute remains unauthorized')) {
    if (-not $current.Contains($required)) { throw "Current ownership correction missing: $required" }
}
foreach ($required in @('Controller-direct external-Pro transport',
    'persistent Open-Pro Exchange is retired',
    'Any late Exchange')) {
    if (-not $current.Contains($required)) { throw "Current direct-review topology missing: $required" }
}
$g1Mechanical = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/50_MECHANICAL_INTAKE_RECORD.md'
if (-not (Test-Path -LiteralPath $g1Mechanical -PathType Leaf)) {
    throw 'Missing PM-owned G1 mechanical intake record'
}
$g1MechanicalText = Get-Content -Raw -LiteralPath $g1Mechanical
foreach ($required in @('record_author=controller_mechanical',
    'adoption_authority=external_pro_raw_only',
    '1ba6bdd5a8f776c1840462037a6303d587d9dc7777bf064ef2d360d36bc2781f',
    'pm_reconciliation_status=PROTECTED_SOURCE_CONTRACT_INCOMPLETE',
    'eba2160e813b13df5cbe0b819104e83a2c7750882dc4427dbad686f85ef420ae',
    'formal_compute_status=unauthorized')) {
    if (-not $g1MechanicalText.Contains($required)) { throw "G1 mechanical intake missing: $required" }
}
$reconciliation = Get-Content (Join-Path $roundRoot '30_EVIDENCE_RECONCILIATION.md') -Raw
foreach ($required in @('exact G0', 'first-match', 'Lower-precedence `G`', 'K-bin',
    '`I_TV`', '`C_total`', 'cannot relabel', 'no disposition authority')) {
    if (-not $reconciliation.Contains($required)) { throw "Reconciliation authority gap: $required" }
}
$disposition = Get-Content (Join-Path $roundRoot '50_DISPOSITION.md') -Raw
foreach ($required in @('Formal iteration-2 compute remains unauthorized',
    'There is no threshold, budget, seed, backend, diagnostic or branch rescue')) {
    if (-not $disposition.Contains($required)) { throw "Disposition authority gap: $required" }
}
$g1RoundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_source_contract'
$g1Question = Get-Content (Join-Path $g1RoundRoot '20_PRO_OPEN_QUESTION.md') -Raw
$listedEvidence = [regex]::Matches($g1Question, '(?m)^- `([^`]+)`\s*$')
foreach ($match in $listedEvidence) {
    $listedPath = $match.Groups[1].Value
    if ($listedPath -match '(?i)(^|[/_.-])(pm|project[_ -]?manager|internal[_ -]?manager|manager)([/_.-]|$)') {
        throw "G1 Pro question exposes internal manager evidence: $listedPath"
    }
    if (-not (Test-Path (Join-Path $repo $listedPath) -PathType Leaf)) {
        throw "G1 Pro question lists missing evidence: $listedPath"
    }
}
if ($current.Contains('iteration 2 is held at the external result-review boundary')) {
    throw 'CURRENT_WORK still holds iteration 2 at the completed review boundary'
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=native_codex'
