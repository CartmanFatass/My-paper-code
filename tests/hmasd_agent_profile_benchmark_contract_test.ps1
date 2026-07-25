[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$benchmark = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/AGENT_PROFILE_BENCHMARK.md')

$variants = @(
    @{ Class='implementer'; Name='sol-high'; Model='gpt-5.6-sol'; Effort='high'; Config='HMASDBenchmarkImplementerSolHigh' },
    @{ Class='implementer'; Name='terra-high'; Model='gpt-5.6-terra'; Effort='high'; Config='HMASDBenchmarkImplementerTerraHigh' },
    @{ Class='implementer'; Name='luna-max'; Model='gpt-5.6-luna'; Effort='max'; Config='HMASDBenchmarkImplementerLunaMax' },
    @{ Class='reviewer'; Name='sol-high'; Model='gpt-5.6-sol'; Effort='high'; Config='HMASDBenchmarkReviewerSolHigh' },
    @{ Class='reviewer'; Name='terra-high'; Model='gpt-5.6-terra'; Effort='high'; Config='HMASDBenchmarkReviewerTerraHigh' },
    @{ Class='reviewer'; Name='luna-max'; Model='gpt-5.6-luna'; Effort='max'; Config='HMASDBenchmarkReviewerLunaMax' }
)

$instructions = @{ implementer=@(); reviewer=@() }
foreach ($variant in $variants) {
    $basename = "hmasd-benchmark-$($variant.Class)-$($variant.Name).toml"
    $path = Join-Path $repo ".codex/agents/$basename"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing benchmark profile: $basename"
    }
    $profile = Get-Content -Raw -LiteralPath $path
    foreach ($required in @(
        "model = `"$($variant.Model)`"",
        "model_reasoning_effort = `"$($variant.Effort)`"",
        'approval_policy = "never"')) {
        if (-not $profile.Contains($required)) {
            throw "$basename missing: $required"
        }
    }
    if (-not $config.Contains("[agents.`"$($variant.Config)`"]") -or
        -not $config.Contains("config_file = `"./agents/$basename`"")) {
        throw "Benchmark profile is not registered: $basename"
    }
    $match = [regex]::Match(
        $profile,
        '(?s)developer_instructions\s*=\s*"""(.*?)"""')
    if (-not $match.Success) {
        throw "Cannot parse developer_instructions: $basename"
    }
    $instructions[$variant.Class] += $match.Groups[1].Value
}

foreach ($class in @('implementer', 'reviewer')) {
    $rows = @($instructions[$class])
    if ($rows.Count -ne 3) { throw "$class instruction inventory mismatch" }
    if ($rows[0] -cne $rows[1] -or $rows[0] -cne $rows[2]) {
        throw "$class benchmark developer_instructions are not byte-identical"
    }
}

$monitorProfile = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-pro-response-monitor.toml')
$monitorRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/PRO_RESPONSE_MONITOR.md')
foreach ($required in @(
    'name = "hmasd-pro-response-monitor"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'approval_policy = "never"',
    'Never activate Answer now',
    'Return exactly one final')) {
    if (-not $monitorProfile.Contains($required)) {
        throw "Pro monitor profile missing: $required"
    }
}
foreach ($required in @(
    'callable_agent_type=hmasd-pro-response-monitor',
    'terminal_notification_count=exactly_one',
    'answer_now_activated=false',
    'two snapshots at least three seconds apart')) {
    if (-not $monitorRole.Contains($required)) {
        throw "Pro monitor role missing: $required"
    }
}
if (-not $config.Contains('[agents."HMASDProResponseMonitor"]') -or
    -not $config.Contains('config_file = "./agents/hmasd-pro-response-monitor.toml"')) {
    throw 'Pro response monitor is not registered'
}

foreach ($required in @(
    'same_class_instructions=byte_identical',
    'same_task=true',
    'blinded=true',
    'formal=false',
    'scientific_iteration_cost=0',
    'Quality is compared first',
    'platform-reported token/compute usage')) {
    if (-not $benchmark.Contains($required)) {
        throw "Benchmark contract missing: $required"
    }
}

$catalogMatch = [regex]::Match($config, '(?m)^model_catalog_json\s*=\s*"([^"]+)"\s*$')
if (-not $catalogMatch.Success) { throw 'Missing model_catalog_json setting' }
$catalogPath = $catalogMatch.Groups[1].Value -replace '\\\\', '\'
$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
foreach ($variant in $variants) {
    $model = @($catalog.models | Where-Object { $_.slug -eq $variant.Model })
    if ($model.Count -ne 1) { throw "Missing model catalog entry: $($variant.Model)" }
    $efforts = @($model[0].supported_reasoning_levels | ForEach-Object { $_.effort })
    if ($efforts -notcontains $variant.Effort) {
        throw "Unsupported benchmark effort: $($variant.Model)/$($variant.Effort)"
    }
}

Write-Output 'HMASD_AGENT_PROFILE_BENCHMARK_CONTRACT_OK'
