[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = Join-Path $repo '.codex/config.toml'
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) { throw 'Missing native Codex agent registry' }
$config = Get-Content -LiteralPath $configPath -Raw
$profiles = @{
    'HMASDCodeScout' = @('hmasd-code-scout.toml', 'hmasd-code-scout', 'gpt-5.6-luna', 'medium', 'read-only')
    'HMASDImplementer' = @('hmasd-implementer.toml', 'hmasd-implementer', 'gpt-5.6-sol', 'high', 'workspace-write')
    'HMASDVerifier' = @('hmasd-verifier.toml', 'hmasd-verifier', 'gpt-5.6-luna', 'high', 'workspace-write')
    'HMASDReviewer' = @('hmasd-reviewer.toml', 'hmasd-reviewer', 'gpt-5.6-sol', 'xhigh', 'read-only')
}
foreach ($key in $profiles.Keys) {
    $spec = $profiles[$key]
    if (-not $config.Contains("[agents.`"$key`"]")) { throw "Missing registry entry: $key" }
    $path = Join-Path $repo ".codex/agents/$($spec[0])"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing profile: $($spec[0])" }
    $text = Get-Content -LiteralPath $path -Raw
    foreach ($required in @("name = `"$($spec[1])`"", "model = `"$($spec[2])`"", "model_reasoning_effort = `"$($spec[3])`"", "sandbox_mode = `"$($spec[4])`"", 'spawn agents')) {
        if (-not $text.Contains($required)) { throw "$($spec[0]) missing: $required" }
    }
}
foreach ($path in @('AGENTS.md')) {
    $text = Get-Content (Join-Path $repo $path) -Raw
    foreach ($callable in @('hmasd-code-scout', 'hmasd-implementer', 'hmasd-verifier', 'hmasd-reviewer')) {
        if (-not $text.Contains($callable)) { throw "$path omits callable profile: $callable" }
    }
    if (-not $text.Contains('unknown agent_type') -or -not $text.Contains('default')) {
        throw "$path does not fail closed against default-agent fallback"
    }
}
Write-Output 'HMASD_PROJECT_MANAGER_CONTRACT_OK'
