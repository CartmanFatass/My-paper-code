[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$profilePath = Join-Path $repo '.codex/agents/hmasd-cpm-mechanical.toml'
$rolePath = Join-Path $repo '.agents/roles/CPM_MECHANICAL_OPERATOR.md'
$skillPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md'
$scriptPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/scripts/hmasd_cpm_mechanical.py'
foreach ($path in @($profilePath, $rolePath, $skillPath, $scriptPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing CPM mechanical path: $path" }
}

$profile = Get-Content -Raw -LiteralPath $profilePath
$role = Get-Content -Raw -LiteralPath $rolePath
$skill = Get-Content -Raw -LiteralPath $skillPath
$skillNormalized = $skill -replace '\s+', ' '
$script = Get-Content -Raw -LiteralPath $scriptPath

foreach ($path in @($profilePath, $rolePath, $scriptPath)) {
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
    'sandbox_mode = "danger-full-access"',
    '.agents/roles/CPM_MECHANICAL_OPERATOR.md',
    'CPM_MECHANICAL_TASK_ASSIGNMENT',
    'CPM_MECHANICAL_TASK_RESULT',
    'natural-language brief',
    'deterministic execution anchor')) {
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
    'ticket_prepare',
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
    'Git',
    'acceptance')) {
    if (-not $role.Contains($required)) { throw "CPM mechanical role missing: $required" }
}
if ($profile.Contains('hmasd_cpm_mechanical.py run --spec') -or $profile.Contains('schema_version=1') -or $profile.Contains('PYTHONDONTWRITEBYTECODE=1')) {
    throw 'CPM mechanical profile must remain thin; dispatcher procedure belongs to the role/Skill'
}
foreach ($required in @(
    'For deterministic inspection, result extraction, handoff preparation or ticket preparation',
    'CPM may trigger `hmasd-cpm-mechanical`',
    '.agents/roles/CPM_MECHANICAL_OPERATOR.md',
    'mechanical result fields and bounded observation recovery')) {
    if (-not $skillNormalized.Contains($required)) { throw "Agile Skill context boundary missing: $required" }
}
foreach ($required in @(
    'SCHEMA_VERSION = 1',
    'REGISTERED_INTERPRETER',
    'TASK_CLASSES',
    'run --spec',
    'shell=False',
    'PYTHONDONTWRITEBYTECODE',
    'subprocess.TimeoutExpired',
    'prepare-integrate',
    'os.replace',
    'first_failure')) {
    if (-not $script.Contains($required)) { throw "CPM mechanical dispatcher missing: $required" }
}
if ($script.Contains('hashlib') -or $script.Contains('sha256') -or $script.Contains('bytes_count')) {
    throw 'CPM mechanical dispatcher must not use hashes or byte counts'
}
Write-Output 'HMASD_CPM_MECHANICAL_CONTRACT_OK'
