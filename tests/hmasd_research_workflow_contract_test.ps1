$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Read-RepoFile([string]$Path) { Get-Content -Raw -LiteralPath (Join-Path $repo $Path) }
$em = Read-RepoFile '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md'
$cm = Read-RepoFile '.agents/roles/CODE_PROJECT_MANAGER.md'
$pro = Read-RepoFile '.agents/roles/EXTERNAL_PRO.md'
$research = Read-RepoFile '.agents/skills/hmasd-independent-research-exploration/SKILL.md'
$agile = Read-RepoFile '.agents/skills/hmasd-agile-research-development/SKILL.md'
$router = Read-RepoFile 'AGENTS.md'
$validation = Read-RepoFile 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md'
$combined = (($em + $cm + $pro + $research + $agile + $router + $validation) -replace '\s+', ' ')
foreach ($required in @(
    'EM owns one direction''s scientific question, treatment and comparator',
    'CM owns code, runner, adapter, package, dependency',
    'technical-result return and scientific intake',
    'Direction Action Map semantic-delta installation',
    'Root accepts the full map and installs it',
    'EXPLORER_PROJECT_ALIGNMENT_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'An ordinary B never calls Pro merely because it is B',
    'conclusion-bearing C',
    'pre-full recovery',
    'ordinary non-force',
    'raw response is completely archived, committed, and pushed',
    'max_subagent_depth=2',
    'same-direction direct channel',
    'Cross-direction relay remains Root-only')) {
    if (-not $combined.Contains($required)) { throw "Research delivery relationship missing: $required" }
}
foreach ($required in @(
    'EXPLORER_PROJECT_ALIGNMENT_AUDIT',
    'OVERNIGHT_BRANCH_BLOCKER_REVIEW',
    'exact pushed aggressive revision',
    'raw response is fully archived, committed, and pushed')) {
    if (-not $combined.Contains($required)) { throw "Review-route relationship missing: $required" }
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
