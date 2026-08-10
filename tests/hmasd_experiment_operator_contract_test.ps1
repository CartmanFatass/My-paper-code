[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$configPath = Join-Path $repo '.codex/config.toml'
$profilePath = Join-Path $repo '.codex/agents/hmasd-experiment-operator.toml'
$rolePath = Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md'
$skillPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md'
$receiptHelperPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/scripts/hmasd_experiment_operator_receipt.py'
$config = Get-Content -Raw -LiteralPath $configPath
$profile = Get-Content -Raw -LiteralPath $profilePath
$role = Get-Content -Raw -LiteralPath $rolePath
$skill = Get-Content -Raw -LiteralPath $skillPath
$manager = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$roleNormalized = $role -replace '\s+', ' '
$skillNormalized = $skill -replace '\s+', ' '
$managerNormalized = $manager -replace '\s+', ' '

if (-not (Test-Path -LiteralPath $receiptHelperPath -PathType Leaf)) {
    throw 'Experiment operator receipt helper is missing'
}

if (-not $config.Contains('[agents."HMASDExperimentOperator"]') -or
    -not $config.Contains('config_file = "./agents/hmasd-experiment-operator.toml"')) {
    throw 'Experiment operator is not registered as a fixed native child'
}
foreach ($required in @(
    'name = "hmasd-experiment-operator"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'sandbox_mode = "workspace-write"',
    'approval_policy = "never"',
    '.agents/roles/EXPERIMENT_OPERATOR.md',
    'natural-language brief',
    'artifact consumers',
    'conclusion-first terminal handoff')) {
    if (-not $profile.Contains($required)) { throw "Operator profile missing: $required" }
}
if ($profile.Contains('Execute train') -or $profile.Contains('Do not emit commentary') -or $profile.Contains('Start a later phase')) {
    throw 'Experiment operator profile must remain thin; procedure belongs to the role charter'
}
foreach ($required in @(
    'callable_agent_type=hmasd-experiment-operator',
    'parent=code_project_manager',
    'model=gpt-5.6-luna',
    'reasoning_effort=low',
    'compute_authority=derived_from_valid_code_project_manager_assignment',
    'per_run_user_authorization_reference=not_required',
    'grant_admission_owner=code_project_manager',
    'concurrency_authority=isolation_only',
    'scheduler_authority=none',
    'progress_notifications=forbidden',
    'terminal_notification_count=exactly_one',
    'terminal_values=COMPLETE|ERROR',
    'terminal_handoff=file_backed_compact_native_final',
    'terminal_receipt_path=assignment_named',
    'conclusion',
    'artifact consumers',
    'protected',
    'conflicting runtime evidence',
    'cross_owner_contact=forbidden_native_final_return_only',
    'Code Project Manager supplies',
    'execution mode from `fresh|retry|resume|restart`',
    'unchanged authorized-boundary binding',
    'A changed source commit requires `fresh`',
    'new run identity',
    'new independent run root',
    'changed source commit + prior run root',
    'never reads a prior failed root',
    'direction identity, treatment identity, seed/RNG namespace',
    'evidence, checkpoint, result and temporary-session roots',
    'result-bearing full',
    'reused worktree/run root',
    'shared mutable checkpoint or trainer state',
    'overlapping output path',
    'never reads a peer treatment''s intermediate result',
    'one pre-full engineering recovery with unchanged scientific literals',
    'never silently relaunches it',
    'new parent-authorized treatment assignment and independent root',
    'selects among scientific outcomes',
    'costs zero scientific iterations',
    'no scientific disposition or abandonment',
    'train -> evaluate -> analyze',
    'client timeout is not a process failure',
    'reattach and wait when the same live process',
    'one assignment-defined',
    'read-only identity/run-root observation recovery',
    'never changes a command',
    'concise operational',
    'direct artifact or consumer consequence',
    'residual uncertainty',
    'No progress, ETA, phase, heartbeat',
    'The receipt is produced by the deterministic standard-library helper',
    'hmasd_experiment_operator_receipt.py',
    'write --record <operator-local-input-json> --receipt <assignment-named-json>',
    'check --receipt <assignment-named-json>',
    'The local input keys and output receipt keys are exact',
    'run',
    'source_commit',
    'execution_mode',
    'phase',
    'exit_codes',
    'artifacts',
    'last_progress',
    'process_live',
    'direct_error',
    'the output adds only `terminal`',
    'phase` is the last attempted/reached phase',
    'never a terminal status',
    'legacy `error`',
    'slash-combined',
    'atomic',
    'derived terminal',
    'never authorizes a rerun')) {
    if (-not $roleNormalized.Contains($required)) { throw "Operator role missing: $required" }
}
foreach ($required in @(
    'receives and executes one exact treatment only',
    'enforces that treatment''s worktree, run, evidence, checkpoint, result and temporary roots are isolated',
    'no authority to schedule, serialize or coordinate peer treatments',
    'Parallel-first admission and any permitted serialization decision belong to Code Project Manager')) {
    if (-not $roleNormalized.Contains($required)) { throw "Operator isolation-only boundary missing: $required" }
}
foreach ($required in @(
    'uppercase enum',
    'operator-local input boundary',
    'exact complete lowercase key set',
    'exact complete uppercase phase-label key set',
    'missing, extra, and mixed-case key sets are rejected',
    'deterministic normalization of uppercase input to lowercase keys',
    'file-backed receipt is always canonical lowercase')) {
    if (-not $roleNormalized.Contains($required)) { throw "Operator receipt casing rule missing: $required" }
}
foreach ($required in @(
    '.agents/roles/EXPERIMENT_OPERATOR.md',
    'hmasd_experiment_operator_receipt.py',
    'train -> evaluate -> analyze',
    'terminal receipt',
    'does not reproduce those lanes',
    'sole technical/mechanical acceptance owner')) {
    if (-not $skillNormalized.Contains($required)) { throw "Agile Skill receipt pointer missing: $required" }
}
if ($profile.Contains('active Workflow Design Manager') -or $role.Contains('parent=workflow_design_manager')) {
    throw 'Experiment runtime is still assigned to Workflow Design Manager'
}
foreach ($retired in @(
    'scheduler_authority=code_project_manager',
    'peer_treatment_scheduler=enabled',
    'global_serial_fallback=allowed')) {
    if ($profile.Contains($retired) -or $role.Contains($retired)) {
        throw "Retired Operator scheduling authority remains: $retired"
    }
}
foreach ($required in @(
    'Every L2 profile declares',
    '`workspace-write` only for those paths',
    'it never stages,',
    'no canonical-state, Git, owner-acceptance')) {
    if (-not $agents.Contains($required)) { throw "AGENTS operator contract missing: $required" }
}
foreach ($required in @(
    'A complete exact assignment delegates compute authority to the child automatically',
    'CPM checks the active grant and remaining balance before dispatch',
    'neither CPM nor the child asks for per-run authorization',
    'reads only its terminal receipt/result',
    'CPM supplies the complete assignment and grant binding',
    '.agents/roles/EXPERIMENT_OPERATOR.md` owns `train -> evaluate -> analyze`')) {
    if (-not $managerNormalized.Contains($required)) { throw "CPM experiment delegation contract missing: $required" }
}
foreach ($required in @(
    'the three-unit runtime pool and live process/resource observations',
    'runtime_admission_observation=stateless_per_admission',
    'runtime_admission_judgment=admit|up-class|pending_runtime_capacity',
    'CPM''s only runtime judgment is `admit`, `up-class` or `pending_runtime_capacity`',
    'Capacity deferral applies only to the not-yet-started treatment',
    'never creates a task, direction or workflow `BLOCKED` state',
    'scientific A/B/C evidence level is independent of runtime class',
    'never infers class, units or barrier closure from a science label or `local_research/`',
    'one independent technical acceptance and one conclusion-first reverse result',
    'An exclusive formal/heavy run reserves only experiment-runtime admission',
    'All non-experiment work that does not contend for the observed bottleneck continues',
    'one command contending for that same actual resource may be delayed without creating `BLOCKED`')) {
    if (-not $managerNormalized.Contains($required)) { throw "CPM runtime-capacity boundary missing: $required" }
}
foreach ($required in @(
    'one assignment-named terminal receipt path',
    'file-backed',
    'single compact final return',
    'receipt retains',
    'receipt write failure is `ERROR`',
    'reconstruct or copy the child record')) {
    if (-not $roleNormalized.Contains($required)) { throw "Operator terminal handoff contract missing: $required" }
}
$catalogMatch = [regex]::Match($config, '(?m)^model_catalog_json\s*=\s*"([^"]+)"\s*$')
if (-not $catalogMatch.Success) { throw 'Missing model_catalog_json setting' }
$catalogPath = $catalogMatch.Groups[1].Value -replace '\\\\', '\'
if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
    throw "Configured model catalog is unavailable: $catalogPath"
}
$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
$luna = @($catalog.models | Where-Object { $_.slug -eq 'gpt-5.6-luna' })
if ($luna.Count -ne 1) { throw 'Configured catalog does not expose exactly one gpt-5.6-luna model' }
$efforts = @($luna[0].supported_reasoning_levels | ForEach-Object { $_.effort })
if ($efforts -notcontains 'low') { throw 'Configured gpt-5.6-luna model does not support low effort' }

foreach ($retired in @(
    '.agents/roles/CONTROLLER.md',
    '.agents/roles/EXPERIMENT_MONITOR.md',
    '.agents/skills/hmasd-dispatch-task/SKILL.md',
    '.agents/skills/hmasd-experiment-monitor/SKILL.md')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Retired execution surface remains: $retired"
    }
}

Write-Output 'HMASD_EXPERIMENT_OPERATOR_CONTRACT_OK'
