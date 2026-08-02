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
$experimentOperator = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-experiment-operator.toml')
$cpm = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$explorer = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$researchScoutPath = Join-Path $repo '.codex/agents/hmasd-research-scout.toml'
$researchInnovatorPath = Join-Path $repo '.codex/agents/hmasd-research-innovator.toml'
$researchCriticPath = Join-Path $repo '.codex/agents/hmasd-research-critic.toml'
$researchPrinciplesPath = Join-Path $repo '.codex/agents/hmasd-research-principles-analyst.toml'
if (-not (Test-Path -LiteralPath $researchScoutPath) -or
    -not (Test-Path -LiteralPath $researchInnovatorPath) -or
    -not (Test-Path -LiteralPath $researchCriticPath) -or
    -not (Test-Path -LiteralPath $researchPrinciplesPath)) {
    throw 'Independent research child profiles are missing'
}
$researchScout = Get-Content -Raw -LiteralPath $researchScoutPath
$researchInnovator = Get-Content -Raw -LiteralPath $researchInnovatorPath
$researchCritic = Get-Content -Raw -LiteralPath $researchCriticPath
$researchPrinciples = Get-Content -Raw -LiteralPath $researchPrinciplesPath

foreach ($required in @(
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "high"',
    'Use only the assignment-named runtime')) {
    if (-not $implementer.Contains($required)) {
        throw "Selected implementer profile missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-experiment-operator"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'as delegated compute authority',
    'Do not request or require a separate per-run user authorization reference')) {
    if (-not $experimentOperator.Contains($required)) {
        throw "Experiment Operator profile missing: $required"
    }
}
foreach ($retired in @(
    '[agents."HMASDIndependentResearchReviewOperator"]',
    'hmasd-independent-research-review-operator.toml',
    'hmasd-project-operations-operator.toml',
    'HMASDProjectOperationsOperator')) {
    if ($config.Contains($retired)) {
        throw "Retired duplicate direction-review profile remains registered: $retired"
    }
}
foreach ($required in @(
    'name = "hmasd-research-innovator"',
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "max"',
    'sandbox_mode = "read-only"',
    '.agents/roles/RESEARCH_INNOVATOR.md',
    'research-methodology.md only for candidate_validation',
    'ALGORITHM_INSPIRATION_PACKET',
    'adapt, combine, develop',
    'delete-retain-add ledger',
    'Do not force an affirmative result',
    'spawn children')) {
    if (-not $researchInnovator.Contains($required)) {
        throw "Research Innovator profile missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-research-scout"',
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "high"',
    'sandbox_mode = "read-only"',
    '.agents/roles/RESEARCH_SCOUT.md',
    'catalog.v2',
    'quality and provenance',
    'structured JSON',
    'PDF verification',
    'SOURCE_RESULT_PACKET',
    'source absorption, not idea competition')) {
    if (-not $researchScout.Contains($required)) {
        throw "Research Scout profile missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-research-critic"',
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "max"',
    'sandbox_mode = "read-only"',
    '.agents/roles/RESEARCH_CRITIC.md',
    'research-methodology.md',
    'only for candidate_validation',
    'Metadata v2',
    'quality and provenance',
    'structured JSON',
    'PDF verification',
    'SOURCE_RESULT_PACKET',
    'ALGORITHM_INSPIRATION_PACKET',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'after constructive principles analysis',
    'Formal proof and routine counterexample construction are not required')) {
    if (-not $researchCritic.Contains($required)) {
        throw "Research Critic profile missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-research-principles-analyst"',
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "max"',
    'sandbox_mode = "read-only"',
    '.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md',
    'information-theoretic',
    'exploration/exploitation',
    'posterior-collapse',
    'RL_PRINCIPLE_ANALYSIS_PACKET',
    'Do not demand a theorem')) {
    if (-not $researchPrinciples.Contains($required)) {
        throw "Research Principles Analyst profile missing: $required"
    }
}
foreach ($required in @(
    '[agents."HMASDResearchScout"]',
    'config_file = "./agents/hmasd-research-scout.toml"',
    '[agents."HMASDResearchInnovator"]',
    'config_file = "./agents/hmasd-research-innovator.toml"',
    '[agents."HMASDResearchCritic"]',
    'config_file = "./agents/hmasd-research-critic.toml"',
    '[agents."HMASDResearchPrinciplesAnalyst"]',
    'config_file = "./agents/hmasd-research-principles-analyst.toml"')) {
    if (-not $config.Contains($required)) {
        throw "Independent research profile is not registered: $required"
    }
}
if (-not $config.Contains('max_depth = 1')) {
    throw 'Independent research child no-spawn depth is not enforced'
}
foreach ($required in @(
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "xhigh"',
    'Inspect scalar device work')) {
    if (-not $reviewer.Contains($required)) {
        throw "Selected reviewer profile missing: $required"
    }
}
foreach ($required in @(
    '[agents."HMASDImplementer"]',
    'config_file = "./agents/hmasd-implementer.toml"',
    '[agents."HMASDReviewer"]',
    'config_file = "./agents/hmasd-reviewer.toml"',
    '[agents."HMASDExperimentOperator"]',
    'config_file = "./agents/hmasd-experiment-operator.toml"')) {
    if (-not $config.Contains($required)) {
        throw "Selected normal profile is not registered: $required"
    }
}
foreach ($required in @(
    'formal_external_review_transport_authority=exclusive',
    'transport_owner=code_project_manager',
    'prepare -> submit -> verify -> archive -> local_FIFO_intake')) {
    if (-not $cpm.Contains($required)) {
        throw "CPM direct transport contract missing: $required"
    }
}
foreach ($required in @(
    'independent_pro_review_transport_authority=exclusive_for_explorer_direction_and_methodology_reviews',
    'independent_pro_review_transport_execution=persistent_explorer_session_direct',
    'transport_owner=independent_research_explorer',
    'hmasd-independent-research-explorer-pro',
    'hmasd-independent-research-explorer-gemini',
    'prepare -> submit -> verify -> archive')) {
    if (-not $explorer.Contains($required)) {
        throw "Explorer direct transport contract missing: $required"
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

$catalogMatch = [regex]::Match(
    $config, '(?m)^model_catalog_json\s*=\s*"([^"]+)"\s*$')
if (-not $catalogMatch.Success) { throw 'Missing model_catalog_json setting' }
$catalogPath = $catalogMatch.Groups[1].Value -replace '\\\\', '\'
$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
foreach ($selected in @(
    @{ Model='gpt-5.6-sol'; Effort='high' },
    @{ Model='gpt-5.6-sol'; Effort='xhigh' },
    @{ Model='gpt-5.6-sol'; Effort='max' })) {
    $model = @($catalog.models | Where-Object { $_.slug -eq $selected.Model })
    if ($model.Count -ne 1) { throw "Missing model catalog entry: $($selected.Model)" }
    $efforts = @($model[0].supported_reasoning_levels | ForEach-Object { $_.effort })
    if ($efforts -notcontains $selected.Effort) {
        throw "Unsupported selected effort: $($selected.Model)/$($selected.Effort)"
    }
}

Write-Output 'HMASD_AGENT_PROFILE_BENCHMARK_RESULT_OK'
