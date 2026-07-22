[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$agentRoot = Join-Path $repo '.omp/agents'

$profiles = @{
    'hmasd-project-manager.md' = @(
        'name: hmasd-project-manager',
        'model: openai-codex/gpt-5.6-sol',
        'thinking-level: xhigh',
        '  - task',
        '  - hmasd-code-scout',
        '  - hmasd-implementer',
        '  - hmasd-verifier',
        '  - hmasd-reviewer')
    'hmasd-code-scout.md' = @('name: hmasd-code-scout', 'model: openai-codex/gpt-5.6-luna', 'thinking-level: medium')
    'hmasd-implementer.md' = @('name: hmasd-implementer', 'model: openai-codex/gpt-5.6-sol', 'thinking-level: high')
    'hmasd-verifier.md' = @('name: hmasd-verifier', 'model: openai-codex/gpt-5.6-luna', 'thinking-level: high')
    'hmasd-reviewer.md' = @('name: hmasd-reviewer', 'model: openai-codex/gpt-5.6-sol', 'thinking-level: xhigh')
}
foreach ($file in $profiles.Keys) {
    $path = Join-Path $agentRoot $file
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing OMP profile: $file" }
    $text = Get-Content -LiteralPath $path -Raw
    if (-not $text.StartsWith("---`n") -and -not $text.StartsWith("---`r`n")) { throw "Missing frontmatter: $file" }
    foreach ($required in $profiles[$file]) {
        if (-not $text.Contains($required)) { throw "$file missing: $required" }
    }
    if ($file -ne 'hmasd-project-manager.md') {
        if ($text -notmatch '(?m)^spawns:\s*\[\]\s*$') { throw "$file must deny child spawn" }
        if ($text -match '(?m)^\s*-\s+task\s*$') { throw "$file exposes task tool" }
    }
}

$manager = Get-Content -LiteralPath (Join-Path $agentRoot 'hmasd-project-manager.md') -Raw
$normalizedManager = $manager -replace '\s+', ' '
foreach ($required in @(
    'algorithm realization',
    'scientific direction',
    'IMPLEMENTATION_PLAN.md',
    'isolated',
    'sole tracked-worktree write lease',
    'one writer',
    'one bounded repair cycle',
    'formal compute',
    'Git authority',
    'external reviewer',
    'project control')) {
    if ($normalizedManager -notmatch [regex]::Escape($required)) { throw "Project Manager authority missing: $required" }
}
$scout = Get-Content -LiteralPath (Join-Path $agentRoot 'hmasd-code-scout.md') -Raw
$reviewer = Get-Content -LiteralPath (Join-Path $agentRoot 'hmasd-reviewer.md') -Raw
foreach ($pair in @(@('Scout', $scout), @('Reviewer', $reviewer))) {
    foreach ($forbidden in @('  - edit', '  - write', '  - bash', '  - task')) {
        if ($pair[1] -match "(?m)^$([regex]::Escape($forbidden))\s*$") { throw "$($pair[0]) exposes mutation/spawn tool: $forbidden" }
    }
}
$engineering = Join-Path $agentRoot 'references/hmasd-engineering-principles.md'
if (-not (Test-Path -LiteralPath $engineering -PathType Leaf)) { throw 'Missing OMP engineering principles' }
Write-Output 'HMASD_PROJECT_MANAGER_CONTRACT_OK'
