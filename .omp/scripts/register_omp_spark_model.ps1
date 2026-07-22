[CmdletBinding()]
param(
    [string]$CodexCatalogPath = (Join-Path $env:USERPROFILE '.codex\models_cache.json'),
    [string]$OmpModelDbPath = (Join-Path $env:USERPROFILE '.omp\agent\models.db')
)

$ErrorActionPreference = 'Stop'

foreach ($path in @($CodexCatalogPath, $OmpModelDbPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required model catalog not found: $path"
    }
}
if (-not (Get-Command sqlite3 -ErrorAction SilentlyContinue)) {
    throw 'sqlite3 is required to register the Spark model with OMP'
}

$codexCatalog = Get-Content -LiteralPath $CodexCatalogPath -Raw | ConvertFrom-Json
$sparkMatches = @($codexCatalog.models | Where-Object { $_.slug -eq 'gpt-5.3-codex-spark' })
if ($sparkMatches.Count -ne 1) {
    throw "Expected one entitled gpt-5.3-codex-spark entry, found $($sparkMatches.Count)"
}
$sparkSource = $sparkMatches[0]
$efforts = @($sparkSource.supported_reasoning_levels | ForEach-Object { [string]$_.effort })
if ($efforts.Count -eq 0) {
    throw 'The Spark catalog entry has no supported reasoning levels'
}

$rowsJson = & sqlite3 -json $OmpModelDbPath "SELECT models FROM model_cache WHERE provider_id = 'openai-codex';"
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to read the OMP openai-codex model cache'
}
$parsedRows = $rowsJson | ConvertFrom-Json
$rows = @($parsedRows | ForEach-Object { $_ })
if ($rows.Count -ne 1) {
    throw "Expected one OMP openai-codex cache row, found $($rows.Count)"
}
$parsedModels = $rows[0].models | ConvertFrom-Json
$models = @($parsedModels | ForEach-Object { $_ })
$models = @($models | Where-Object { $_.id -ne 'gpt-5.3-codex-spark' })

$sparkModel = [ordered]@{
    id = 'gpt-5.3-codex-spark'
    name = [string]$sparkSource.display_name
    api = 'openai-codex-responses'
    provider = 'openai-codex'
    baseUrl = 'https://chatgpt.com/backend-api'
    reasoning = $true
    input = @('text')
    cost = [ordered]@{
        input = 0
        output = 0
        cacheRead = 0
        cacheWrite = 0
    }
    contextWindow = [int]$sparkSource.context_window
    maxTokens = [int]$sparkSource.truncation_policy.limit
    preferWebsockets = $false
    useResponsesLite = [bool]$sparkSource.use_responses_lite
    priority = [int]$sparkSource.priority
    applyPatchToolType = [string]$sparkSource.apply_patch_tool_type
    thinking = [ordered]@{
        mode = 'effort'
        efforts = $efforts
    }
}
$models += [pscustomobject]$sparkModel

$modelsJson = ConvertTo-Json -InputObject $models -Depth 20 -Compress
$updatedAt = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$tempJsonPath = Join-Path ([IO.Path]::GetTempPath()) ("omp-spark-models-{0}.json" -f [guid]::NewGuid().ToString('N'))
try {
    [IO.File]::WriteAllText($tempJsonPath, $modelsJson, [Text.UTF8Encoding]::new($false))
    $sqlJsonPath = $tempJsonPath.Replace('\', '/').Replace("'", "''")
    & sqlite3 $OmpModelDbPath "UPDATE model_cache SET models = CAST(readfile('$sqlJsonPath') AS TEXT), updated_at = $updatedAt WHERE provider_id = 'openai-codex';"
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to update the OMP openai-codex model cache'
    }
}
finally {
    Remove-Item -LiteralPath $tempJsonPath -Force -ErrorAction SilentlyContinue
}
$count = & sqlite3 $OmpModelDbPath "SELECT COUNT(*) FROM model_cache, json_each(models) WHERE provider_id = 'openai-codex' AND json_extract(value, '$.id') = 'gpt-5.3-codex-spark';"
if ($LASTEXITCODE -ne 0 -or [int]$count -ne 1) {
    throw 'OMP Spark model registration verification failed'
}

[pscustomobject]@{
    selector = 'openai-codex/gpt-5.3-codex-spark'
    thinking = ($efforts -join ',')
    context_window = [int]$sparkSource.context_window
    max_tokens = [int]$sparkSource.truncation_policy.limit
}
