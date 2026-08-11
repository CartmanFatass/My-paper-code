$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Read-RepoFile([string]$Path) { Get-Content -Raw -LiteralPath (Join-Path $repo $Path) }
$role = Read-RepoFile '.agents/roles/EXPERIMENT_OPERATOR.md'
$profile = Read-RepoFile '.codex/agents/hmasd-experiment-operator.toml'
$text = (($role + $profile) -replace '\s+', ' ')
foreach ($required in @(
    'parent=code_project_manager',
    'agent_tree_level=2',
    'user_contact_authority=none',
    'git_authority=none',
    'only to this treatment',
    'train -> evaluate -> analyze',
    'COMPLETE',
    'ERROR',
    'reconstructs/copies it as rerun authorization')) {
    if (-not $text.Contains($required)) { throw "Operator safety/receipt contract missing: $required" }
}
Write-Output 'HMASD_EXPERIMENT_OPERATOR_CONTRACT_OK'
