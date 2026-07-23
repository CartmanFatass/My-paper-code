[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expected = @('hmasd-dispatch-task', 'hmasd-experiment-monitor',
    'hmasd-review-exchange', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expected $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }

$current = Get-Content (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
$legacyToken = 'O' + 'MP'
if ($current -match "(?i)\b$legacyToken\b|\.omp") { throw 'Current control plane retains a legacy execution route' }
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
foreach ($role in @('project_manager', 'experiment_monitor', 'open_divergent_exchange')) {
    if ($roles.roles.$role.registration_status -ne 'ACTIVE') { throw "Inactive registered role: $role" }
}
if ($roles.roles.experiment_monitor.thread_id -ne '019f8a2f-08a2-73e1-b539-2dc5a6db0fc1' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Native Spark Monitor registry mismatch'
}

$dispatcher = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('controller <-> project_manager', 'controller <-> experiment_monitor',
    'controller <-> open_divergent_exchange', 'source_boundary=local_and_remote_aggressive_tip',
    'gpt-5.3-codex-spark', 'PROJECT_MANAGER_DELIVERY_BLOCKED')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
if ($dispatcher -match '(?i)\bOMP\b|agent://|history://') { throw 'Dispatcher retains a legacy task-delivery path' }

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
foreach ($required in @('external-Pro review is complete',
    'ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1',
    'no iteration-2 formal compute is authorized yet',
    'No iteration-2 formal compute is authorized until')) {
    if (-not $current.Contains($required)) { throw "Current boundary missing Pro intake: $required" }
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
if ($current.Contains('iteration 2 is held at the external result-review boundary')) {
    throw 'CURRENT_WORK still holds iteration 2 at the completed review boundary'
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=native_codex'
