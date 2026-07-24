[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = Join-Path $repo '.omp/config.yml'
if (-not (Test-Path $configPath -PathType Leaf)) { throw 'Missing project OMP config' }
if (-not (Test-Path (Join-Path $repo '.omp/skills') -PathType Container)) {
    throw 'Missing native project OMP Skill root'
}
$config = Get-Content $configPath -Raw
foreach ($required in @('default: openai-codex/gpt-5.6-sol:high',
    'smol: openai-codex/gpt-5.6-luna:high', 'slow: openai-codex/gpt-5.6-sol:xhigh',
    'maxConcurrency: 8', 'maxRecursionDepth: 1', 'enableLsp: true',
    'hmasd-code-scout: openai-codex/gpt-5.6-luna:high',
    'hmasd-implementer: openai-codex/gpt-5.6-sol:high',
    'hmasd-frontier-implementer: openai-codex/gpt-5.6-sol:max',
    'hmasd-verifier: openai-codex/gpt-5.6-luna:high',
    'hmasd-reviewer: openai-codex/gpt-5.6-sol:xhigh',
    'hmasd-exp-manager: openai-codex/gpt-5.3-codex-spark:high',
    'includeSkills:', '- hmasd-*', 'enableClaudeProject: false')) {
    if (-not $config.Contains($required)) { throw "OMP config missing: $required" }
}
foreach ($removed in @('hmasd-pro-monitor','hmasd-pro-monitor-luna')) {
    if ($config.Contains($removed)) { throw "OMP config retains removed override: $removed" }
    if (Test-Path (Join-Path $repo ".omp/agents/$removed.md")) { throw "OMP retains removed profile: $removed" }
}
$profiles = @{
    'hmasd-code-scout.md' = @('hmasd-code-scout','openai-codex/gpt-5.6-luna','high')
    'hmasd-implementer.md' = @('hmasd-implementer','openai-codex/gpt-5.6-sol','high')
    'hmasd-frontier-implementer.md' = @('hmasd-frontier-implementer','openai-codex/gpt-5.6-sol','max')
    'hmasd-verifier.md' = @('hmasd-verifier','openai-codex/gpt-5.6-luna','high')
    'hmasd-reviewer.md' = @('hmasd-reviewer','openai-codex/gpt-5.6-sol','xhigh')
    'hmasd-exp-manager.md' = @('hmasd-exp-manager','openai-codex/gpt-5.3-codex-spark','high')
}
Push-Location $repo
try {
    $resolvedText = @(& omp.exe config get task.agentModelOverrides --json)
    if ($LASTEXITCODE -ne 0) { throw 'OMP rejected project agent model overrides' }
    $resolved = ($resolvedText -join "`n") | ConvertFrom-Json
    $skillsText = @(& omp.exe config get skills.includeSkills --json)
    if ($LASTEXITCODE -ne 0) { throw 'OMP rejected project skill allowlist' }
    $resolvedSkills = ($skillsText -join "`n") | ConvertFrom-Json
} finally { Pop-Location }
$resolvedNames = @($resolved.value.PSObject.Properties.Name)
$expectedNames = @($profiles.Values | ForEach-Object { $_[0] })
if (Compare-Object $expectedNames $resolvedNames) { throw 'Resolved OMP overrides are not exactly the six local agents' }
foreach ($spec in $profiles.Values) {
    $actual = [string]$resolved.value.PSObject.Properties[$spec[0]].Value
    if ($actual -ne "$($spec[1]):$($spec[2])") { throw "Resolved OMP model mismatch for $($spec[0]): $actual" }
}
$skillAllowlist = @($resolvedSkills.value)
if ($skillAllowlist.Count -ne 1 -or $skillAllowlist[0] -ne 'hmasd-*') {
    throw "Resolved OMP skill allowlist mismatch: $($skillAllowlist -join ', ')"
}
foreach ($file in $profiles.Keys) {
    $spec = $profiles[$file]
    $path = Join-Path $repo ".omp/agents/$file"
    if (-not (Test-Path $path -PathType Leaf)) { throw "Missing OMP profile: $file" }
    $text = Get-Content $path -Raw
    foreach ($required in @("name: $($spec[0])", "  - `"$($spec[1])`"", "thinkingLevel: $($spec[2])", 'tools:', 'spawn agents')) {
        if (-not $text.Contains($required)) { throw "$file missing: $required" }
    }
    if ($text -match '(?m)^spawns:' -or $text -notmatch '(?m)^tools: \[[^\r\n]+\]$') {
        throw "$file does not enforce an explicit depth-one tool surface"
    }
    $toolLine = [regex]::Match($text, '(?m)^tools: \[([^\r\n]+)\]$').Groups[1].Value
    if (", $toolLine," -match ',\s*task\s*,') { throw "$file can spawn a successor" }
}
foreach ($file in @('hmasd-implementer.md','hmasd-frontier-implementer.md','hmasd-verifier.md')) {
    $text = Get-Content (Join-Path $repo ".omp/agents/$file") -Raw
    foreach ($required in @('C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe','has no CUDA','FORMAL_NUM_ENVS=16')) {
        if (-not $text.Contains($required)) { throw "$file missing execution invariant: $required" }
    }
}
$controller = Get-Content (Join-Path $repo 'AGENTS.md') -Raw
foreach ($callable in $expectedNames) {
    if (-not $controller.Contains($callable)) { throw "AGENTS.md omits callable profile: $callable" }
}
foreach ($removed in @('hmasd-pro-monitor','hmasd-pro-monitor-luna')) {
    if ($controller.Contains($removed)) { throw "AGENTS.md retains removed callable profile: $removed" }
}
foreach ($required in @('sole implementation-plan author','compare 2-3 viable approaches',
    'one collective gate per complete code','dispatch exactly one Reviewer and one','Verifier in parallel',
    'one Controller-owned state machine','No local or persistent role may')) {
    if (-not $controller.Contains($required)) { throw "Controller contract missing: $required" }
}
if (Test-Path (Join-Path $repo '.agents')) { throw 'Legacy active .agents root remains' }
if (Test-Path (Join-Path $repo '.codex')) { throw 'Legacy active .codex root remains' }
Write-Output 'HMASD_CONTROLLER_SUBAGENT_CONTRACT_OK profiles=six skills=native-omp'
