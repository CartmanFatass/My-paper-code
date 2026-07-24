[CmdletBinding()]
param(
    [string]$SourcePath = (Join-Path $env:USERPROFILE ".codex\models_cache.json"),
    [string]$OutputPath = (Join-Path (Split-Path $PSScriptRoot -Parent) "runtime\model-catalog-v2-workaround.json")
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $SourcePath)) { throw "Codex account model cache not found: $SourcePath" }
$catalog = Get-Content -LiteralPath $SourcePath -Raw | ConvertFrom-Json
if (-not $catalog.models) { throw "The Codex account model cache has no models array" }

$targets = @("gpt-5.6-luna", "gpt-5.3-codex-spark")
foreach ($slug in $targets) {
    $matches = @($catalog.models | Where-Object { $_.slug -eq $slug })
    if ($matches.Count -ne 1) { throw "Expected exactly one catalog entry for $slug, found $($matches.Count)" }
    $matches[0] | Add-Member -NotePropertyName multi_agent_version -NotePropertyValue "v2" -Force
}

$parent = Split-Path -Parent $OutputPath
if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
$catalog | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $OutputPath -Encoding utf8NoBOM
$written = Get-Content -LiteralPath $OutputPath -Raw | ConvertFrom-Json
if (@($written.models | Where-Object { $_.slug -in $targets -and $_.multi_agent_version -ne "v2" }).Count -ne 0) {
    throw "Generated catalog failed the v2 routing verification"
}
$written.models | Where-Object { $_.slug -in $targets } | Select-Object slug,multi_agent_version,default_reasoning_level
