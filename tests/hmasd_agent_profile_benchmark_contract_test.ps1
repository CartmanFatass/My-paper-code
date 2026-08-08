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
$routineImplementer = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-implementer-terra.toml')
$implementerRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/IMPLEMENTER.md')
$implementerRoleNormalized = $implementerRole -replace '\s+', ' '
$reviewer = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-reviewer.toml')
$reviewerRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/REVIEWER.md')
$reviewerRoleNormalized = $reviewerRole -replace '\s+', ' '
$codeScout = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-code-scout.toml')
$codeScoutRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/CODE_SCOUT.md')
$codeScoutRoleNormalized = $codeScoutRole -replace '\s+', ' '
$experimentOperator = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-experiment-operator.toml')
$experimentOperatorRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/EXPERIMENT_OPERATOR.md')
$experimentOperatorRoleNormalized = $experimentOperatorRole -replace '\s+', ' '
$mechanicalOperatorPath = Join-Path $repo '.codex/agents/hmasd-cpm-mechanical.toml'
if (-not (Test-Path -LiteralPath $mechanicalOperatorPath)) {
    throw 'CPM mechanical child profile is missing'
}
$mechanicalOperator = Get-Content -Raw -LiteralPath $mechanicalOperatorPath
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
$researchScoutRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_SCOUT.md')
$researchInnovatorRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_INNOVATOR.md')
$researchCriticRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_CRITIC.md')
$researchPrinciplesRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md')

foreach ($required in @(
    'model = "gpt-5.6-sol"',
    'model_reasoning_effort = "high"',
    '.agents/roles/IMPLEMENTER.md')) {
    if (-not $implementer.Contains($required)) {
        throw "Selected implementer profile missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-experiment-operator"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    '.agents/roles/EXPERIMENT_OPERATOR.md',
    'delegated compute boundary')) {
    if (-not $experimentOperator.Contains($required)) {
        throw "Experiment Operator profile missing: $required"
    }
}
foreach ($required in @(
    'compute_authority=derived_from_valid_code_project_manager_assignment',
    'per_run_user_authorization_reference=not_required',
    'valid exact assignment from Code Project Manager is the delegated compute authority',
    'begins with a concise operational conclusion')) {
    if (-not $experimentOperatorRoleNormalized.Contains($required)) {
        throw "Experiment Operator role missing delegated-compute contract: $required"
    }
}
foreach ($profileRoute in @(
    @{ Text = $implementer; Model = 'gpt-5.6-sol'; Effort = 'high'; Label = 'protected Sol' },
    @{ Text = $routineImplementer; Model = 'gpt-5.6-terra'; Effort = 'high'; Label = 'routine Terra' })) {
    foreach ($required in @(
        ('model = "' + $profileRoute.Model + '"'),
        ('model_reasoning_effort = "' + $profileRoute.Effort + '"'),
        'sandbox_mode = "workspace-write"',
        '.agents/roles/IMPLEMENTER.md',
        'registered child of Code Project Manager',
        'exact assignment',
        'Do not mutate Git')) {
        if (-not $profileRoute.Text.Contains($required)) {
            throw "$($profileRoute.Label) implementer route missing: $required"
        }
    }
    foreach ($forbidden in @(
            'purpose, observed behavior or failure',
            'necessary consequential scope',
            'Every result must begin with a concise natural-language conclusion',
            'scripts/hmasd_workspace_ticket.py',
            'absolute `apply_patch` targets',
            'core.longpaths=true',
            'Use only the assignment-named runtime',
            'Return status, changed files, checks')) {
        if ($profileRoute.Text.Contains($forbidden)) {
            throw "$($profileRoute.Label) profile duplicates Role procedure: $forbidden"
        }
    }
}
foreach ($required in @(
    'Every result must begin with a concise natural-language conclusion',
    'what outcome was achieved or remains unresolved',
    'direct consumer or cross-module consequence checked',
    'residual uncertainty',
    'A mechanical status or changed-path list alone is not a complete result',
    'necessary consequential scope',
    'model strength adds no authority and never substitutes for a complete assignment',
    'rigid schema or admission gate')) {
    if (-not $implementerRoleNormalized.Contains($required)) {
        throw "Implementer role conclusion/context contract missing: $required"
    }
}
if (-not $routineImplementer.Contains('material or outcome-changing') -or
    -not $routineImplementer.Contains('reversible internal organization') -or
    $routineImplementer.Contains('You do not choose scientific semantics, architecture direction')) {
    throw 'Terra implementer local-judgment distinction is missing'
}
foreach ($required in @('protected Sol route', 'assignment-specified semantics')) {
    if (-not $implementer.Contains($required)) {
        throw "Protected Sol routing distinction missing: $required"
    }
}
foreach ($required in @(
    'name = "hmasd-cpm-mechanical"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'sandbox_mode = "workspace-write"',
    'CPM_MECHANICAL_TASK_ASSIGNMENT',
    'CPM_MECHANICAL_TASK_RESULT',
    'fork_turns=none',
    'prepare-integrate')) {
    if (-not $mechanicalOperator.Contains($required)) {
        throw "CPM mechanical profile missing: $required"
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
foreach ($profileRoute in @(
    @{ Text = $codeScout; Name = 'hmasd-code-scout'; Model = 'gpt-5.6-luna'; Effort = 'medium'; Role = '.agents/roles/CODE_SCOUT.md' },
    @{ Text = $reviewer; Name = 'hmasd-reviewer'; Model = 'gpt-5.6-sol'; Effort = 'xhigh'; Role = '.agents/roles/REVIEWER.md' },
    @{ Text = $researchScout; Name = 'hmasd-research-scout'; Model = 'gpt-5.6-sol'; Effort = 'high'; Role = '.agents/roles/RESEARCH_SCOUT.md' },
    @{ Text = $researchPrinciples; Name = 'hmasd-research-principles-analyst'; Model = 'gpt-5.6-sol'; Effort = 'max'; Role = '.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md' },
    @{ Text = $researchCritic; Name = 'hmasd-research-critic'; Model = 'gpt-5.6-sol'; Effort = 'max'; Role = '.agents/roles/RESEARCH_CRITIC.md' },
    @{ Text = $researchInnovator; Name = 'hmasd-research-innovator'; Model = 'gpt-5.6-sol'; Effort = 'max'; Role = '.agents/roles/RESEARCH_INNOVATOR.md' })) {
    foreach ($required in @(
        ('name = "' + $profileRoute.Name + '"'),
        ('model = "' + $profileRoute.Model + '"'),
        ('model_reasoning_effort = "' + $profileRoute.Effort + '"'),
        'sandbox_mode = "read-only"',
        $profileRoute.Role,
        'fork_turns=none',
        'self-contained natural-language task model',
        'Role charter owns',
        'thin')) {
        if (-not $profileRoute.Text.Contains($required)) {
            throw "$($profileRoute.Name) thin profile missing: $required"
        }
    }
    foreach ($forbidden in @(
        'SOURCE_RESULT_PACKET',
        'ALGORITHM_INSPIRATION_PACKET',
        'RL_PRINCIPLE_ANALYSIS_PACKET',
        'CRITIC_ASSESSMENT_PACKET',
        'Metadata v2',
        'structured JSON',
        'PDF verification',
        'Return exactly one',
        'reopen one',
        'reread one',
        'recheck one')) {
        if ($profileRoute.Text.Contains($forbidden)) {
            throw "$($profileRoute.Name) profile duplicates Role procedure: $forbidden"
        }
    }
}

foreach ($roleRoute in @(
    @{ Text = $codeScoutRole; Name = 'Code Scout'; Required = @('default_fork_turns=none', 'self-contained natural-language task model', 'concise natural-language conclusion', 'reopen one named immediate interface once', 'not a schema or admission gate') },
    @{ Text = $reviewerRole; Name = 'Reviewer'; Required = @('self-contained natural-language task model', 'concise natural-language conclusion', 'reread one indispensable changed artifact or immediate interface once', 'not a schema or admission gate') },
    @{ Text = $researchScoutRole; Name = 'Research Scout'; Required = @('self-contained natural-language task model', 'SOURCE_RESULT_PACKET', 'concise natural-language conclusion', 'one JSON or PDF fidelity recheck at that disputed locator', 'not a schema or admission gate') },
    @{ Text = $researchPrinciplesRole; Name = 'Research Principles Analyst'; Required = @('self-contained natural-language task model', 'RL_PRINCIPLE_ANALYSIS_PACKET', 'concise natural-language conclusion', 'reread one supplied candidate or source fact', 'not a schema or admission gate') },
    @{ Text = $researchCriticRole; Name = 'Research Critic'; Required = @('self-contained natural-language task model', 'CRITIC_ASSESSMENT_PACKET', 'concise natural-language conclusion', 'recheck one named source or principles packet', 'not a schema or admission gate') },
    @{ Text = $researchInnovatorRole; Name = 'Research Innovator'; Required = @('self-contained natural-language task model', 'ALGORITHM_INSPIRATION_PACKET', 'concise natural-language conclusion', 'reread one frozen input or named parent packet', 'not a schema or admission gate') })) {
    $normalizedRole = $roleRoute.Text -replace '\s+', ' '
    foreach ($required in $roleRoute.Required) {
        if (-not $normalizedRole.Contains($required)) {
            throw "$($roleRoute.Name) Role procedure missing: $required"
        }
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
    '.agents/roles/REVIEWER.md',
    'exact assignment controls')) {
    if (-not $reviewer.Contains($required)) {
        throw "Selected reviewer profile missing: $required"
    }
}
foreach ($required in @(
    '[agents."HMASDImplementer"]',
    'config_file = "./agents/hmasd-implementer.toml"',
    '[agents."HMASDRoutineImplementer"]',
    'config_file = "./agents/hmasd-implementer-terra.toml"',
    '[agents."HMASDReviewer"]',
    'config_file = "./agents/hmasd-reviewer.toml"',
    '[agents."HMASDExperimentOperator"]',
    'config_file = "./agents/hmasd-experiment-operator.toml"')) {
    if (-not $config.Contains($required)) {
        throw "Selected normal profile is not registered: $required"
    }
}
foreach ($required in @(
    'actionable_finding_requires=normal_path_defect|material_effect|proportionate_repair',
    'protected scientific semantics',
    'coherent implementer batch')) {
    if (-not $reviewerRoleNormalized.Contains($required)) {
        throw "Reviewer Role protected-boundary contract missing: $required"
    }
}
foreach ($required in @(
    '[agents."HMASDCPMMechanical"]',
    'config_file = "./agents/hmasd-cpm-mechanical.toml"')) {
    if (-not $config.Contains($required)) {
        throw "CPM mechanical profile is not registered: $required"
    }
}
if ([regex]::Matches($config, 'hmasd-cpm-mechanical\.toml').Count -ne 1) {
    throw 'CPM mechanical profile must be registered exactly once'
}
foreach ($profileName in @('hmasd-implementer.toml', 'hmasd-implementer-terra.toml')) {
    if ([regex]::Matches($config, [regex]::Escape($profileName)).Count -ne 1) {
        throw "Implementer profile must be registered exactly once: $profileName"
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
