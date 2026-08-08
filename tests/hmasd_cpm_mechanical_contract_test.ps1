[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$profilePath = Join-Path $repo '.codex/agents/hmasd-cpm-mechanical.toml'
$rolePath = Join-Path $repo '.agents/roles/CPM_MECHANICAL_OPERATOR.md'
$scriptPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/scripts/hmasd_cpm_mechanical.py'
foreach ($path in @($profilePath, $rolePath, $scriptPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing CPM mechanical path: $path" }
}

$profile = Get-Content -Raw -LiteralPath $profilePath
$role = Get-Content -Raw -LiteralPath $rolePath
$script = Get-Content -Raw -LiteralPath $scriptPath

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
    'fork_turns=none',
    'CPM_MECHANICAL_TASK_ASSIGNMENT',
    'CPM_MECHANICAL_TASK_RESULT',
    'PYTHONDONTWRITEBYTECODE=1',
    'prepare-integrate')) {
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
    'Git',
    'acceptance')) {
    if (-not $role.Contains($required)) { throw "CPM mechanical role missing: $required" }
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
