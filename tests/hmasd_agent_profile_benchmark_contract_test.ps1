[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$benchmark = Get-Content -Raw -LiteralPath (
    Join-Path $repo 'docs/project/AGENT_PROFILE_BENCHMARK.md')
$result = Get-Content -Raw -LiteralPath (
    Join-Path $repo 'docs/project/AGENT_PROFILE_BENCHMARK_RESULT.md')
$implementer = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-implementer.toml')
$reviewer = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-reviewer.toml')

foreach ($required in @(
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "high"',
    'Use only the assignment-named runtime')) {
    if (-not $implementer.Contains($required)) {
        throw "Selected implementer profile missing: $required"
    }
}
foreach ($required in @(
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "max"',
    'Inspect scalar device work')) {
    if (-not $reviewer.Contains($required)) {
        throw "Selected reviewer profile missing: $required"
    }
}
foreach ($required in @(
    '[agents."HMASDImplementer"]',
    'config_file = "./agents/hmasd-implementer.toml"',
    '[agents."HMASDReviewer"]',
    'config_file = "./agents/hmasd-reviewer.toml"')) {
    if (-not $config.Contains($required)) {
        throw "Selected normal profile is not registered: $required"
    }
}

$temporaryProfiles = @(
    'hmasd-benchmark-implementer-sol-high.toml',
    'hmasd-benchmark-implementer-terra-high.toml',
    'hmasd-benchmark-implementer-luna-max.toml',
    'hmasd-benchmark-reviewer-sol-high.toml',
    'hmasd-benchmark-reviewer-terra-high.toml',
    'hmasd-benchmark-reviewer-luna-max.toml')
foreach ($basename in $temporaryProfiles) {
    if (Test-Path -LiteralPath (Join-Path $repo ".codex/agents/$basename")) {
        throw "Temporary benchmark profile remains: $basename"
    }
    if ($config.Contains($basename)) {
        throw "Temporary benchmark profile remains registered: $basename"
    }
}
foreach ($role in @('BENCHMARK_IMPLEMENTER.md', 'BENCHMARK_REVIEWER.md')) {
    if (Test-Path -LiteralPath (Join-Path $repo ".agents/roles/$role")) {
        throw "Temporary benchmark role remains: $role"
    }
}

foreach ($required in @(
    'same_class_instructions=byte_identical',
    'same_task=true',
    'blinded=true',
    'formal=false',
    'scientific_iteration_cost=0',
    'A failed attempt is evidence, not a global blocker',
    'multiple bounded repair turns',
    'PM-created workspace ticket',
    'child `resolve` and PM `verify`',
    'monetary_cost_unavailable')) {
    if (-not $benchmark.Contains($required)) {
        throw "Benchmark contract missing: $required"
    }
}
foreach ($required in @(
    'benchmark_status=COMPLETE',
    'implementer_winner=gpt-5.6-terra/high',
    'reviewer_winner=gpt-5.6-luna/max',
    'monetary_cost=unavailable_from_native_child_runtime',
    'harness_failure=worktree_path_resolution',
    'scripts/hmasd_workspace_ticket.py',
    'hidden_oracle=IMPLEMENTER_ORACLE_PASS')) {
    if (-not $result.Contains($required)) {
        throw "Benchmark result missing: $required"
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
    'metadata-only JSONL sentinel',
    'no browser authority',
    'Never activate Answer now',
    'Return exactly one final')) {
    if (-not $monitorProfile.Contains($required)) {
        throw "Pro monitor profile missing: $required"
    }
}
foreach ($required in @(
    'callable_agent_type=hmasd-pro-response-monitor',
    'observation_mode=external_review_operator_brokered_jsonl_sentinel',
    'terminal_notification_count=exactly_one',
    'answer_now_activated=false')) {
    if (-not $monitorRole.Contains($required)) {
        throw "Pro monitor role missing: $required"
    }
}
if (-not $config.Contains('[agents."HMASDProResponseMonitor"]') -or
    -not $config.Contains(
        'config_file = "./agents/hmasd-pro-response-monitor.toml"')) {
    throw 'Pro response monitor is not registered'
}

$catalogMatch = [regex]::Match(
    $config, '(?m)^model_catalog_json\s*=\s*"([^"]+)"\s*$')
if (-not $catalogMatch.Success) { throw 'Missing model_catalog_json setting' }
$catalogPath = $catalogMatch.Groups[1].Value -replace '\\\\', '\'
$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
foreach ($selected in @(
    @{ Model='gpt-5.6-sol'; Effort='high' },
    @{ Model='gpt-5.6-luna'; Effort='max' })) {
    $model = @($catalog.models | Where-Object { $_.slug -eq $selected.Model })
    if ($model.Count -ne 1) { throw "Missing model catalog entry: $($selected.Model)" }
    $efforts = @($model[0].supported_reasoning_levels | ForEach-Object { $_.effort })
    if ($efforts -notcontains $selected.Effort) {
        throw "Unsupported selected effort: $($selected.Model)/$($selected.Effort)"
    }
}

Write-Output 'HMASD_AGENT_PROFILE_BENCHMARK_RESULT_OK'
