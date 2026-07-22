[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$codexConfigPath = Join-Path $repo '.codex/config.toml'
if (-not (Test-Path -LiteralPath $codexConfigPath -PathType Leaf)) { throw 'Missing native Codex agent registry' }
$codexConfig = Get-Content -LiteralPath $codexConfigPath -Raw
$nativeProfiles = @{
    'HMASDCodeScout' = @('hmasd-code-scout.toml', 'hmasd-code-scout', 'model = "gpt-5.6-luna"', 'model_reasoning_effort = "medium"', 'sandbox_mode = "read-only"')
    'HMASDImplementer' = @('hmasd-implementer.toml', 'hmasd-implementer', 'model = "gpt-5.6-sol"', 'model_reasoning_effort = "high"', 'sandbox_mode = "workspace-write"')
    'HMASDVerifier' = @('hmasd-verifier.toml', 'hmasd-verifier', 'model = "gpt-5.6-luna"', 'model_reasoning_effort = "high"', 'sandbox_mode = "workspace-write"')
    'HMASDReviewer' = @('hmasd-reviewer.toml', 'hmasd-reviewer', 'model = "gpt-5.6-sol"', 'model_reasoning_effort = "xhigh"', 'sandbox_mode = "read-only"')
}
foreach ($agentType in $nativeProfiles.Keys) {
    if (-not $codexConfig.Contains("[agents.`"$agentType`"]")) { throw "Missing native agent_type: $agentType" }
    $profileName = $nativeProfiles[$agentType][0]
    if (-not $codexConfig.Contains("config_file = `"./agents/$profileName`"")) { throw "Registry path mismatch: $agentType" }
    $profilePath = Join-Path $repo ".codex/agents/$profileName"
    if (-not (Test-Path -LiteralPath $profilePath -PathType Leaf)) { throw "Missing native profile: $profileName" }
    $profile = Get-Content -LiteralPath $profilePath -Raw
    $callableType = $nativeProfiles[$agentType][1]
    if (-not $profile.Contains("name = `"$callableType`"")) { throw "$profileName callable agent_type mismatch" }
    foreach ($required in $nativeProfiles[$agentType][2..($nativeProfiles[$agentType].Count - 1)]) {
        if (-not $profile.Contains($required)) { throw "$profileName missing: $required" }
    }
    if (-not $profile.Contains('spawn agents')) { throw "$profileName must explicitly deny child spawn" }
}
foreach ($contractPath in @('AGENTS.md', '.agents/skills/hmasd-dispatch-task/SKILL.md')) {
    $contract = Get-Content -LiteralPath (Join-Path $repo $contractPath) -Raw
    foreach ($agentType in $nativeProfiles.Keys) {
        $callableType = $nativeProfiles[$agentType][1]
        if (-not $contract.Contains($callableType)) { throw "$contractPath omits callable agent_type: $callableType" }
    }
    if (-not $contract.Contains('unknown agent_type') -or -not $contract.Contains('default')) {
        throw "$contractPath does not fail closed against default-agent fallback"
    }
}

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
