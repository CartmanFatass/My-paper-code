[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$legacyRoot = Join-Path $repo '.omp/legacy'
$config = Get-Content -Raw -LiteralPath (Join-Path $legacyRoot 'codex/config.toml')
$projectManager = Get-Content -Raw -LiteralPath (Join-Path $legacyRoot 'roles/PROJECT_MANAGER.md')
foreach ($relative in @(
    'codex/agents/hmasd-code-scout.toml',
    'codex/agents/hmasd-implementer.toml',
    'codex/agents/hmasd-reviewer.toml',
    'codex/agents/hmasd-verifier.toml',
    'codex/agents/hmasd-experiment-operator.toml',
    'roles/EXTERNAL_PRO.md',
    'roles/EXPERIMENT_OPERATOR.md')) {
    if (-not (Test-Path -LiteralPath (Join-Path $legacyRoot $relative) -PathType Leaf)) {
        throw "Migrated legacy workflow asset is missing: $relative"
    }
}
foreach ($required in @('[agents."HMASDCodeScout"]','[agents."HMASDImplementer"]',
    '[agents."HMASDReviewer"]','[agents."HMASDVerifier"]',
    '[agents."HMASDExperimentOperator"]')) {
    if (-not $config.Contains($required)) { throw "Legacy Codex registry lost: $required" }
}
foreach ($required in @('role_kind=sole_persistent_project_task',
    'external_review_transport=direct','experiment_orchestration=registered_native_child')) {
    if (-not $projectManager.Contains($required)) { throw "Legacy Project Manager charter lost: $required" }
}

$controller = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$roles = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.omp/skills/hmasd-dispatch-task/references/session-roles.json') | ConvertFrom-Json
if ($controller.Contains('role=project_manager') -or
    @($roles.roles.PSObject.Properties.Name) -contains 'project_manager' -or
    $roles.asset_root.legacy_active) {
    throw 'Migrated Project Manager asset became active'
}
if ((Test-Path (Join-Path $repo '.agents')) -or
    (Test-Path (Join-Path $repo '.codex'))) {
    throw 'Legacy discovery root remains active outside .omp'
}

Write-Output 'HMASD_LEGACY_PROJECT_MANAGER_ASSET_OK location=.omp/legacy active=false'
