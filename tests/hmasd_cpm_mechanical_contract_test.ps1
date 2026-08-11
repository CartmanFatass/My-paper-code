[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$profilePath = Join-Path $repo '.codex/agents/hmasd-cpm-mechanical.toml'
$rolePath = Join-Path $repo '.agents/roles/CPM_MECHANICAL_OPERATOR.md'
$cpmRolePath = Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md'
$skillPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md'
$scriptPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/scripts/hmasd_cpm_mechanical.py'
foreach ($path in @($profilePath, $rolePath, $cpmRolePath, $skillPath, $scriptPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing CPM mechanical path: $path" }
}

$profile = Get-Content -Raw -LiteralPath $profilePath
$role = Get-Content -Raw -LiteralPath $rolePath
$cpmRole = Get-Content -Raw -LiteralPath $cpmRolePath
$skill = Get-Content -Raw -LiteralPath $skillPath
$skillNormalized = $skill -replace '\s+', ' '
$script = Get-Content -Raw -LiteralPath $scriptPath
$runtimeAnchorSurface = @($cpmRole, $role, $skillNormalized) -join ' '

foreach ($path in @($profilePath, $rolePath, $cpmRolePath, $scriptPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing CPM mechanical path: $path" }
}

foreach ($required in @(
    '[agents."HMASDCPMMechanical"]',
    'config_file = "./agents/hmasd-cpm-mechanical.toml"')) {
    if (-not $config.Contains($required)) { throw "CPM mechanical registration missing: $required" }
}
if ([regex]::Matches($config, 'hmasd-cpm-mechanical\.toml').Count -ne 1) {
    throw 'CPM mechanical profile must be registered exactly once'
}
foreach ($required in @(
    'name = "hmasd-cpm-mechanical"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'sandbox_mode = "workspace-write"',
    '.agents/roles/CPM_MECHANICAL_OPERATOR.md',
    'CPM_MECHANICAL_TASK_ASSIGNMENT',
    'CPM_MECHANICAL_TASK_RESULT',
    'natural-language brief',
    'deterministic execution anchor',
    'use direct Git commands or mutate Git')) {
    if (-not $profile.Contains($required)) { throw "CPM mechanical profile missing: $required" }
}
foreach ($required in @(
    'role=cpm_mechanical_operator',
    'assignment_fields=spec_path|result_path',
    'terminal_notification_count=exactly_one',
    'inspect_identity',
    'run_focused_checks',
    'verify_result',
    'assemble_handoff',
    'render_state',
    'mechanical_task_classes=inspect_identity|run_focused_checks|verify_result|assemble_handoff|render_state',
    'canonical_state_write_authority=none',
    'git_authority=none',
    'acceptance_authority=none',
    'semantic task authority',
    'CPM consumers',
    'protected',
    'at most one',
    'read-only observation recovery',
    'automatic repair or retry',
    'natural-language mechanical conclusion',
    'direct consequence',
    'residual uncertainty',
    '`COMPLETE` means',
    'accepted the underlying result',
    'no Git or canonical-state acceptance authority')) {
    if (-not $role.Contains($required)) { throw "CPM mechanical role missing: $required" }
}
# Runtime admission is no longer a mechanical child capability.  The active
# contract records the absence of a unit pool while leaving scope-local
# judgment with CPM and factual host observation with Root.
foreach ($required in @(
    'runtime_unit_accounting=none',
    'runtime_pool=none',
    'runtime_class_quota=none',
    'runtime_reservation=none',
    'runtime_admission_ledger=none',
    'runtime_observation_owner=root_mechanical',
    'runtime_observation_facts=live_processes|cpu|memory|concrete_resource_conflicts',
    'runtime_judgment_owner=code_project_manager_scope_local',
    'high_cost_runtime_authorization=explicit_user_task_via_root',
    'max_threads=20',
    'max_threads_semantics=agent_concurrency_ceiling_only',
    'max_threads_runtime_authorization=none',
    'parallelism_runtime_authorization=none')) {
    if (-not $runtimeAnchorSurface.Contains($required)) {
        throw "CPM runtime anchor missing: $required"
    }
}
foreach ($retired in @(
    'fixed three-unit arithmetic',
    'runtime_capacity_pool_units=3',
    'admit|up-class|pending_runtime_capacity',
    'reserved and free units before and after the request',
    'runtime class/units',
    'runtime admission ledger')) {
    if ($role.Contains($retired) -or $skill.Contains($retired) -or $script.Contains($retired)) {
        throw "Retired CPM runtime-pool contract remains: $retired"
    }
}
if ($profile.Contains('hmasd_cpm_mechanical.py run --spec') -or $profile.Contains('schema_version=1') -or $profile.Contains('PYTHONDONTWRITEBYTECODE=1')) {
    throw 'CPM mechanical profile must remain thin; dispatcher procedure belongs to the role/Skill'
}
foreach ($required in @(
    'For deterministic inspection, result extraction, handoff preparation or state rendering',
    'CPM may trigger `hmasd-cpm-mechanical`',
    '.agents/roles/CPM_MECHANICAL_OPERATOR.md',
    'mechanical result fields and bounded observation recovery')) {
    if (-not $skillNormalized.Contains($required)) { throw "Agile Skill context boundary missing: $required" }
}
foreach ($required in @(
    'SCHEMA_VERSION = 1',
    'TASK_CLASSES',
    'inspect_identity',
    'run_focused_checks',
    'verify_result',
    'assemble_handoff',
    'render_state',
    'run --spec',
    'shell=False',
    'PYTHONDONTWRITEBYTECODE',
    'subprocess.TimeoutExpired',
    'os.replace',
    'first_failure')) {
    if (-not $script.Contains($required)) { throw "CPM mechanical dispatcher missing: $required" }
}
if ($script.Contains('hashlib') -or $script.Contains('sha256') -or $script.Contains('bytes_count')) {
    throw 'CPM mechanical dispatcher must not use hashes or byte counts'
}
Write-Output 'HMASD_CPM_MECHANICAL_CONTRACT_OK'
