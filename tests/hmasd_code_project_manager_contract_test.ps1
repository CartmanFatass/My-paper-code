$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Read-RepoFile([string]$Path) { Get-Content -Raw -LiteralPath (Join-Path $repo $Path) }
$cm = Read-RepoFile '.agents/roles/CODE_PROJECT_MANAGER.md'
$agile = Read-RepoFile '.agents/skills/hmasd-agile-research-development/SKILL.md'
$router = Read-RepoFile 'AGENTS.md'
$text = (($cm + $agile + $router) -replace '\s+', ' ')
foreach ($required in @(
    'technical_acceptance_authority=exclusive',
    'CM owns code, runner, adapter, package, dependency',
    'pre-full recovery',
    'Operator receives only an exact run-ready assignment',
    'never installs, repairs, changes source/configuration',
    'root_lifecycle_git_relay=exclusive',
    'root_final_git_integration_authority=accepted_paths_only',
    'code_project_manager_scope_key_forms=direction:<id>|shared:<component>')) {
    if (-not $text.Contains($required)) { throw "CM ownership/safety contract missing: $required" }
}
Write-Output 'HMASD_CODE_PROJECT_MANAGER_CONTRACT_OK'
