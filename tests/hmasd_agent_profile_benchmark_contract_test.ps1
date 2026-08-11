[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$benchmark = Get-Content -Raw -LiteralPath (
    Join-Path $repo 'docs/project/AGENT_PROFILE_BENCHMARK.md')
$benchmarkNormalized = $benchmark -replace '\s+', ' '
$result = Get-Content -Raw -LiteralPath (
    Join-Path $repo 'docs/project/AGENT_PROFILE_BENCHMARK_RESULT.md')
$resultNormalized = $result -replace '\s+', ' '
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
$explorerMechanicalOperatorPath = Join-Path $repo '.codex/agents/hmasd-explorer-mechanical.toml'
if (-not (Test-Path -LiteralPath $explorerMechanicalOperatorPath)) {
    throw 'Explorer mechanical child profile is missing'
}
$explorerMechanicalOperator = Get-Content -Raw -LiteralPath $explorerMechanicalOperatorPath
$explorerMechanicalRolePath = Join-Path $repo '.agents/roles/EXPLORER_MECHANICAL_OPERATOR.md'
if (-not (Test-Path -LiteralPath $explorerMechanicalRolePath)) {
    throw 'Explorer mechanical child Role is missing'
}
$explorerMechanicalRole = Get-Content -Raw -LiteralPath $explorerMechanicalRolePath
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
    'compute_authority=derived_from_valid_root_or_code_project_manager_assignment',
    'per_run_user_authorization_reference=not_required')) {
    if (-not $experimentOperatorRoleNormalized.Contains($required)) {
        throw "Experiment Operator role missing delegated-compute contract: $required"
    }
}
foreach ($profileRoute in @(
    @{ Text = $implementer; Model = 'gpt-5.6-sol'; Effort = 'high'; Role = '.agents/roles/IMPLEMENTER.md'; Label = 'protected Sol' },
    @{ Text = $routineImplementer; Model = 'gpt-5.6-terra'; Effort = 'high'; Role = '.agents/roles/ROUTINE_IMPLEMENTER.md'; Label = 'routine Terra' })) {
    foreach ($required in @(
        ('model = "' + $profileRoute.Model + '"'),
        ('model_reasoning_effort = "' + $profileRoute.Effort + '"'),
        'sandbox_mode = "workspace-write"',
        'approval_policy = "never"',
        $profileRoute.Role,
        'registered child invokable',
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
    'approval_policy = "never"',
    '.agents/roles/CPM_MECHANICAL_OPERATOR.md',
    'CPM_MECHANICAL_TASK_ASSIGNMENT',
    'CPM_MECHANICAL_TASK_RESULT',
    'fork_turns=1',
    'agent_tree_level=1_or_2',
    'parent=root|code_project_manager',
    'spawn_authority=none',
    'user_contact_authority=none',
    'cross_branch_transport=none',
    'inspect_identity|run_focused_checks|verify_result|assemble_handoff|render_state',
    'ticket and worktree admission is outside this leaf',
    'There is no',
    'Hook route, runtime',
    'Git/canonical-state mutation or acceptance authority',
    'workspace-write only for the exact assignment result path')) {
    if (-not $mechanicalOperator.Contains($required)) {
        throw "CPM mechanical profile missing: $required"
    }
}

# Verify the TOML route and thin Role pointer without imposing a packet schema
# or copying Role procedure into the profile.
foreach ($required in @(
    'name = "hmasd-explorer-mechanical"',
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "low"',
    'sandbox_mode = "read-only"',
    'approval_policy = "never"',
    '.agents/roles/EXPLORER_MECHANICAL_OPERATOR.md',
    '.agents/skills/hmasd-explorer-mechanical/SKILL.md',
    'fork_turns=1',
    'self-contained natural-language task model',
    'one conclusion-first native result')) {
    if (-not $explorerMechanicalOperator.Contains($required)) {
        throw "Explorer mechanical profile missing: $required"
    }
}
foreach ($forbidden in @(
    'Return one native terminal result only',
    'If the first observation exposes one missing or disputed named fact',
    'There is no mandatory output file')) {
    if ($explorerMechanicalOperator.Contains($forbidden)) {
        throw "Explorer mechanical profile duplicates Role procedure: $forbidden"
    }
}
foreach ($required in @(
    'role=explorer_mechanical_operator',
    'callable_agent_type=hmasd-explorer-mechanical',
    'parent=root|independent_research_explorer',
    'write_authority=none',
    'scientific_authority=none',
    'technical_acceptance_authority=none',
    'child_authority=none',
    'cross_owner_contact_authority=none',
    'cross_branch_transport=none',
    'self-contained natural-language task model',
    'Return one native terminal result only')) {
    if (-not (($explorerMechanicalRole -replace '\s+', ' ').Contains($required))) {
        throw "Explorer Mechanical Role contract missing: $required"
    }
}
if ([regex]::Matches($config, 'hmasd-explorer-mechanical\.toml').Count -ne 1) {
    throw 'Explorer Mechanical profile must be registered exactly once'
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
        'approval_policy = "never"',
        $profileRoute.Role,
        'fork_turns=1',
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

# Research profiles advertise both their bounded adaptive-question capability
# and their canonical campaign use in the description while leaving procedure
# and packet/phase meaning in the Role charter.
foreach ($profileRoute in @(
    @{ Text = $researchScout; Name = 'hmasd-research-scout'; Description = 'one bounded source/evidence-fidelity scientific question or campaign source assignment' },
    @{ Text = $researchInnovator; Name = 'hmasd-research-innovator'; Description = 'one bounded mechanism, repair, discriminator, or campaign innovation assignment' },
    @{ Text = $researchPrinciples; Name = 'hmasd-research-principles-analyst'; Description = 'one bounded constructive learning-dynamics/mechanism question or campaign principles analysis' },
    @{ Text = $researchCritic; Name = 'hmasd-research-critic'; Description = 'one bounded exact criticism or canonical campaign adversarial assessment' })) {
    if (-not $profileRoute.Text.Contains($profileRoute.Description)) {
        throw "$($profileRoute.Name) description must cover adaptive and canonical use: $($profileRoute.Description)"
    }
    if ($profileRoute.Text.Contains('campaign phase')) {
        throw "$($profileRoute.Name) profile must not define a campaign phase"
    }
    foreach ($packet in @(
        'SOURCE_RESULT_PACKET',
        'ALGORITHM_INSPIRATION_PACKET',
        'RL_PRINCIPLE_ANALYSIS_PACKET',
        'CRITIC_ASSESSMENT_PACKET')) {
        if ($profileRoute.Text.Contains($packet)) {
            throw "$($profileRoute.Name) profile must leave packet procedure to its Role"
        }
    }
}

foreach ($roleRoute in @(
    @{ Text = $codeScoutRole; Name = 'Code Scout'; Required = @('default_fork_turns=1', 'self-contained natural-language task model', 'concise natural-language conclusion', 'reopen one named immediate interface once', 'not a schema or admission gate') },
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
if (-not $config.Contains('max_threads = 20') -or
    $config.Contains('max_concurrent_threads_per_session') -or
    -not $config.Contains('max_depth = 2')) {
    throw 'Two-level topology capacity/depth is not configured'
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
    'coherent scope-local candidate',
    'review_scope=one_scope_local_coherent_candidate_after_same_cpm_combines_l2_outputs',
    'review_scope_boundary=no_cross_direction_union_review',
    'review_acceptance=advisory_only',
    'owning CPM alone makes technical acceptance')) {
    if (-not $reviewerRoleNormalized.Contains($required)) {
        throw "Reviewer Role protected-boundary contract missing: $required"
    }
}
foreach ($retired in @(
    'authority=one_exact_read_only_integrated_package_review',
    'review_scope=coherent_integrated_batch_not_each_implementer',
    'whole_integrated_diff_visibility=allowed')) {
    if ($reviewerRole.Contains($retired)) {
        throw "Reviewer retains retired integrated/union scope: $retired"
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
    'monetary_cost_unavailable',
    'All tracked writers use Root-managed worktrees',
    'Read-only, ignored-only and temp-only work is exempt',
    'ticket, ticket identity or ticket precondition is not part of child authority or workspace admission')) {
    if (-not $benchmarkNormalized.Contains($required)) {
        throw "Benchmark contract missing: $required"
    }
}
foreach ($required in @(
    'benchmark_status=COMPLETE',
    'implementer_winner=gpt-5.6-terra/high',
    'reviewer_winner=gpt-5.6-luna/max',
    'monetary_cost=unavailable_from_native_child_runtime',
    'hidden_oracle=IMPLEMENTER_ORACLE_PASS',
    'historical benchmark evidence',
    'ticket/worktree identity is superseded policy')) {
    if (-not $resultNormalized.Contains($required)) {
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

# Static regression coverage only: these checks do not prove runtime
# registration/live spawn and do not claim that the profile repair is complete.
$standardL1Keys = @(
    'name', 'description', 'model', 'model_reasoning_effort',
    'sandbox_mode', 'approval_policy', 'nickname_candidates',
    'developer_instructions')
$rejectedL1Keys = @('role', 'role_pointer', 'registered_child_pointers')
$l1Routes = @(
    @{ Section = 'HMASDCodeProjectManager'; Name = 'hmasd-code-project-manager'; Model = 'gpt-5.6-sol'; Effort = 'high'; Role = '.agents/roles/CODE_PROJECT_MANAGER.md'; Children = @('hmasd-code-scout', 'hmasd-implementer', 'hmasd-implementer-terra', 'hmasd-reviewer', 'hmasd-verifier', 'hmasd-experiment-operator', 'hmasd-cpm-mechanical', 'hmasd-cpm-agentify-transport') },
    @{ Section = 'HMASDIndependentResearchExplorer'; Name = 'hmasd-independent-research-explorer'; Model = 'gpt-5.6-sol'; Effort = 'max'; Role = '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md'; Children = @('hmasd-research-scout', 'hmasd-research-innovator', 'hmasd-research-critic', 'hmasd-research-principles-analyst', 'hmasd-explorer-mechanical', 'hmasd-research-artifact-writer', 'hmasd-explorer-agentify-transport') })
foreach ($route in $l1Routes) {
    $sectionMatch = [regex]::Match(
        $config,
        '(?ms)^\[agents\."' + [regex]::Escape($route.Section) + '"\](?<body>.*?)(?=^\[|\z)')
    if (-not $sectionMatch.Success) { throw "Missing L1 config section: $($route.Section)" }
    $sectionBody = $sectionMatch.Groups['body'].Value
    $configEntry = 'config_file = "./agents/' + $route.Name + '.toml"'
    if (-not $sectionBody.Contains($configEntry)) { throw "Wrong L1 config path: $($route.Name)" }

    $profilePath = Join-Path $repo ('.codex/agents/' + $route.Name + '.toml')
    $rolePath = Join-Path $repo $route.Role
    if (-not (Test-Path -LiteralPath $profilePath) -or -not (Test-Path -LiteralPath $rolePath)) {
        throw "Missing L1 profile or Role: $($route.Name)"
    }
    $profile = Get-Content -Raw -LiteralPath $profilePath
    # Restrict key extraction to the TOML header; developer instructions are
    # multiline prose and can legitimately contain tokens such as fork_turns=1.
    $profileHeader = ($profile -split 'developer_instructions\s*=\s*"""', 2)[0]
    $profileKeys = @([regex]::Matches($profileHeader, '(?m)^([A-Za-z_][A-Za-z0-9_]*)\s*=') | ForEach-Object { $_.Groups[1].Value })
    foreach ($key in $profileKeys) {
        if ($standardL1Keys -notcontains $key) { throw "Unsupported L1 profile key $key in $($route.Name)" }
    }
    foreach ($key in $rejectedL1Keys) {
        if ([regex]::IsMatch($profileHeader, '(?m)^' + [regex]::Escape($key) + '\s*=')) {
            throw "Rejected L1 profile key remains: $key in $($route.Name)"
        }
    }
    foreach ($required in @(
        ('name = "' + $route.Name + '"'),
        ('model = "' + $route.Model + '"'),
        ('model_reasoning_effort = "' + $route.Effort + '"'),
        'sandbox_mode = "read-only"',
        'approval_policy = "never"',
        'developer_instructions = """',
        $route.Role)) {
        if (-not $profile.Contains($required)) { throw "L1 profile contract missing: $($route.Name): $required" }
    }
    $instructions = ($profile -replace '\s+', ' ').ToLowerInvariant()
    $roleText = ((Get-Content -Raw -LiteralPath $rolePath) -replace '\s+', ' ').ToLowerInvariant()
    foreach ($child in $route.Children) {
        if (-not $instructions.Contains($child) -and -not $roleText.Contains($child)) {
            throw "L1 child allow-list missing: $($route.Name): $child"
        }
    }
    if ($route.Name -eq 'hmasd-independent-research-explorer' -and
        (-not $instructions.Contains('root') -or -not $instructions.Contains('fork_turns=1'))) {
        throw "L1 Root caller fork_turns=1 contract missing: $($route.Name)"
    }
}

Write-Output 'HMASD_AGENT_PROFILE_BENCHMARK_RESULT_OK'
