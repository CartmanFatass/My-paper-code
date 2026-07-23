[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = Join-Path $repo '.omp/config.yml'
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) { throw 'Missing project OMP config' }
if (Test-Path -LiteralPath (Join-Path $repo '.codex')) { throw 'Superseded native Codex profile root remains' }
$config = Get-Content -LiteralPath $configPath -Raw
foreach ($required in @(
    'default: openai-codex/gpt-5.6-sol:high',
    'smol: openai-codex/gpt-5.6-luna:high',
    'slow: openai-codex/gpt-5.6-sol:xhigh',
    'maxConcurrency: 8',
    'maxRecursionDepth: 1',
    'enableLsp: true',
    'hmasd-code-scout: openai-codex/gpt-5.6-luna:high',
    'hmasd-implementer: openai-codex/gpt-5.6-sol:high',
    'hmasd-frontier-implementer: openai-codex/gpt-5.6-sol:max',
    'hmasd-verifier: openai-codex/gpt-5.6-luna:high',
    'hmasd-reviewer: openai-codex/gpt-5.6-sol:xhigh',
    'hmasd-exp-manager: openai-codex/gpt-5.3-codex-spark:high',
    'hmasd-pro-monitor: openai-codex/gpt-5.3-codex-spark:medium',
    'hmasd-pro-monitor-luna: openai-codex/gpt-5.6-luna:low',
    'includeSkills:',
    '- hmasd-*',
    'enableClaudeProject: false')) {
    if (-not $config.Contains($required)) { throw "OMP config missing: $required" }
}

$profiles = @{
    'hmasd-code-scout.md' = @('hmasd-code-scout', 'openai-codex/gpt-5.6-luna', 'high')
    'hmasd-implementer.md' = @('hmasd-implementer', 'openai-codex/gpt-5.6-sol', 'high')
    'hmasd-frontier-implementer.md' = @('hmasd-frontier-implementer', 'openai-codex/gpt-5.6-sol', 'max')
    'hmasd-verifier.md' = @('hmasd-verifier', 'openai-codex/gpt-5.6-luna', 'high')
    'hmasd-reviewer.md' = @('hmasd-reviewer', 'openai-codex/gpt-5.6-sol', 'xhigh')
    'hmasd-exp-manager.md' = @('hmasd-exp-manager', 'openai-codex/gpt-5.3-codex-spark', 'high')
    'hmasd-pro-monitor.md' = @('hmasd-pro-monitor', 'openai-codex/gpt-5.3-codex-spark', 'medium')
    'hmasd-pro-monitor-luna.md' = @('hmasd-pro-monitor-luna', 'openai-codex/gpt-5.6-luna', 'low')
}

Push-Location $repo
try {
    $resolvedText = @(& omp.exe config get task.agentModelOverrides --json)
    if ($LASTEXITCODE -ne 0) { throw 'OMP rejected the project agent model overrides' }
    $resolvedOverrides = ($resolvedText -join "`n") | ConvertFrom-Json
    $resolvedSkillsText = @(& omp.exe config get skills.includeSkills --json)
    if ($LASTEXITCODE -ne 0) { throw 'OMP rejected the project skill allowlist' }
    $resolvedSkills = ($resolvedSkillsText -join "`n") | ConvertFrom-Json
}
finally {
    Pop-Location
}
foreach ($spec in $profiles.Values) {
    $expectedSelector = "$($spec[1]):$($spec[2])"
    $actualSelector = [string]$resolvedOverrides.value.PSObject.Properties[$spec[0]].Value
    if ($actualSelector -ne $expectedSelector) {
        throw "Resolved OMP model mismatch for $($spec[0]): $actualSelector"
    }
}
$skillAllowlist = @($resolvedSkills.value)
if ($skillAllowlist.Count -ne 1 -or $skillAllowlist[0] -ne 'hmasd-*') {
    throw "Resolved OMP skill allowlist is not HMASD-only: $($skillAllowlist -join ', ')"
}
foreach ($file in $profiles.Keys) {
    $spec = $profiles[$file]
    $path = Join-Path $repo ".omp/agents/$file"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing OMP profile: $file" }
    $text = Get-Content -LiteralPath $path -Raw
    foreach ($required in @("name: $($spec[0])", "  - `"$($spec[1])`"", "thinkingLevel: $($spec[2])", 'tools:', 'spawn agents')) {
        if (-not $text.Contains($required)) { throw "$file missing: $required" }
    }
    if ($text -match '(?m)^spawns:' -or $text -notmatch '(?m)^tools: \[[^\r\n]+\]$') {
        throw "$file does not enforce an explicit depth-one tool surface"
    }
    $toolLine = [regex]::Match($text, '(?m)^tools: \[([^\r\n]+)\]$').Groups[1].Value
    if (", $toolLine," -match ',\s*task\s*,') { throw "$file can spawn a successor" }
}
foreach ($monitorFile in @('hmasd-pro-monitor.md', 'hmasd-pro-monitor-luna.md')) {
    $proMonitor = Get-Content -LiteralPath (Join-Path $repo ".omp/agents/$monitorFile") -Raw
    foreach ($required in @(
            'mcp__browsermcp_pro_browser_snapshot',
            'mcp__browsermcp_pro_browser_wait',
            'do not submit, edit, click, navigate, stop, retry or interpret anything',
            'STABLE_COMPLETE|BLOCKED')) {
        if (-not $proMonitor.Contains($required)) { throw "$monitorFile missing: $required" }
    }
    $toolLine = [regex]::Match($proMonitor, '(?m)^tools: \[([^\r\n]+)\]$').Groups[1].Value
    foreach ($forbidden in @('browser_click', 'browser_type', 'browser_navigate', 'bash', 'edit', 'write')) {
        if ($toolLine.Contains($forbidden)) { throw "$monitorFile has forbidden tool: $forbidden" }
    }
}

foreach ($file in @('hmasd-implementer.md', 'hmasd-frontier-implementer.md', 'hmasd-verifier.md')) {
    $text = Get-Content -LiteralPath (Join-Path $repo ".omp/agents/$file") -Raw
    foreach ($required in @('C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
            'has no CUDA', 'FORMAL_NUM_ENVS=16')) {
        if (-not $text.Contains($required)) { throw "$file missing current environment fact: $required" }
    }
}

$frontier = Get-Content -LiteralPath (Join-Path $repo '.omp/agents/hmasd-frontier-implementer.md') -Raw
foreach ($required in @('systematic Superpowers debugging discipline',
        'at most five repair attempts', 'BUG_UNRESOLVED', 'BUG_FIXED',
        'BLOCKED_SCIENTIFIC_DECISION', '3-5 ranked falsifiable hypotheses',
        '1. 问题来源', '2. 问题类型', '3. 问题大致规模',
        '4. 推荐解决方案（自动采纳）', 'CODE_ENGINEERING',
        'SCIENTIFIC_DECISION', 'apply it automatically')) {
    if (-not $frontier.Contains($required)) { throw "Frontier profile missing: $required" }
}

$implementer = Get-Content -LiteralPath (Join-Path $repo '.omp/agents/hmasd-implementer.md') -Raw
$reviewer = Get-Content -LiteralPath (Join-Path $repo '.omp/agents/hmasd-reviewer.md') -Raw
$verifier = Get-Content -LiteralPath (Join-Path $repo '.omp/agents/hmasd-verifier.md') -Raw
foreach ($required in @('Controller/main conversation is the sole plan author',
        'do not brainstorm', 'author or revise the plan')) {
    if (-not $implementer.Contains($required)) { throw "Implementer planning boundary missing: $required" }
}
if (-not $frontier.Contains('Controller/main conversation is the sole plan author') -or
    -not $frontier.Contains('do not redesign or expand it')) {
    throw 'Frontier planning boundary is missing'
}
foreach ($profile in @($reviewer, $verifier)) {
    foreach ($required in @('FINAL_IMPLEMENTATION_ROUND_REVIEW',
            'complete stable package', 'Never')) {
        if (-not $profile.Contains($required)) { throw "Collective review profile missing: $required" }
    }
}

$controller = Get-Content -LiteralPath (Join-Path $repo 'AGENTS.md') -Raw
foreach ($required in @('sole implementation-plan author',
        'compare 2-3 viable approaches', 'one collective gate per complete code',
        'dispatch exactly one Reviewer and one', 'Verifier in parallel')) {
    if (-not $controller.Contains($required)) { throw "Controller plan/review contract missing: $required" }
}

foreach ($callable in $profiles.Values | ForEach-Object { $_[0] }) {
    if (-not $controller.Contains($callable)) { throw "AGENTS.md omits callable profile: $callable" }
}
if (-not $controller.Contains('unknown agent') -or -not $controller.Contains('default')) {
    throw 'AGENTS.md does not fail closed against bundled/default-agent fallback'
}
Write-Output 'HMASD_CONTROLLER_SUBAGENT_CONTRACT_OK'
