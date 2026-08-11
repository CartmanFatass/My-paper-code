$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Read-RepoFile([string]$Path) { Get-Content -Raw -LiteralPath (Join-Path $repo $Path) }
$em = Read-RepoFile '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md'
$cm = Read-RepoFile '.agents/roles/CODE_PROJECT_MANAGER.md'
$pro = Read-RepoFile '.agents/roles/EXTERNAL_PRO.md'
$research = Read-RepoFile '.agents/skills/hmasd-independent-research-exploration/SKILL.md'
$agile = Read-RepoFile '.agents/skills/hmasd-agile-research-development/SKILL.md'
$session = Read-RepoFile 'docs/project/SESSION_WORKSPACE_CONTRACT.md'
$router = Read-RepoFile 'AGENTS.md'
$startup = Read-RepoFile 'docs/project/L1_STARTUP_CONTEXT.md'
$routes = Read-RepoFile 'docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md'
$validation = Read-RepoFile 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
$combined = (($em + $cm + $pro + $research + $agile + $session + $router + $startup + $routes + $validation) -replace '\s+', ' ')
foreach ($required in @(
    'EM owns a direction''s scientific question, candidate and comparator choice',
    'CM owns code, runner, adapter, package, dependency',
    'technical-result return and scientific intake',
    'Direction Action Map semantic-delta installation',
    'Root alone accepts the complete Direction Action Map',
    'EXPLORER_PROJECT_ALIGNMENT_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'ordinary B has no automatic Pro call',
    'conclusion-bearing C',
    'pre-full recovery',
    'ordinary non-force',
    'raw response is completely archived, committed, and pushed',
    'max_subagent_depth=2',
    'root_cross_owner_relay_authority=exclusive')) {
    if (-not $combined.Contains($required)) { throw "Research delivery relationship missing: $required" }
}
foreach ($required in @(
    'Independent direction or methodology Pro review',
    'Explorer project-alignment or overnight branch-blocker external review',
    'EXPLORER_PROJECT_VALIDATION_WORKFLOW.md',
    'exact pushed aggressive revision',
    'raw response is fully archived, committed, and pushed')) {
    if (-not $combined.Contains($required)) { throw "Review-route relationship missing: $required" }
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
