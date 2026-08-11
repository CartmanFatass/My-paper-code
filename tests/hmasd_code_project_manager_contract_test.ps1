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
    'code_scope_key_grammar=direction:<id>|shared:<component>',
    'Root handles ordinary questions')) {
    if (-not $text.Contains($required)) { throw "CM ownership/safety contract missing: $required" }
}
Write-Output 'HMASD_CODE_PROJECT_MANAGER_CONTRACT_OK'
