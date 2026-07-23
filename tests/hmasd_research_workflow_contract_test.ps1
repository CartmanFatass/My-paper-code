[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skills = @(Get-ChildItem (Join-Path $repo '.agents/skills') -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expected = @('hmasd-agile-research-development', 'hmasd-dispatch-task',
    'hmasd-experiment-monitor', 'hmasd-review-round') | Sort-Object
if (Compare-Object $expected $skills) { throw "Unexpected active Skill set: $($skills -join ',')" }

$current = Get-Content (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
$implementationPlan = Get-Content (Join-Path $repo 'docs/project/IMPLEMENTATION_PLAN.md') -Raw
if (-not $implementationPlan.Contains('$hmasd-agile-research-development')) {
    throw 'Active implementation plan does not route through the HMASD development Skill'
}
if ($implementationPlan.Contains('superpowers:')) {
    throw 'Active implementation plan still activates a generic Superpowers Skill'
}
$legacyToken = 'O' + 'MP'
if ($current -match "(?i)\b$legacyToken\b|\.omp") { throw 'Current control plane retains a legacy execution route' }
$roles = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json') -Raw | ConvertFrom-Json
foreach ($role in @('controller', 'project_manager')) {
    if ($roles.roles.$role.registration_status -ne 'ACTIVE') { throw "Inactive registered role: $role" }
}
if ($roles.interfaces.experiment_monitor.persistent_task -ne $false -or
    $roles.interfaces.experiment_monitor.operator -ne 'controller' -or
    $roles.interfaces.experiment_monitor.procedure -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Controller-direct monitor interface mismatch'
}

$dispatcher = Get-Content (Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md') -Raw
foreach ($required in @('Role contracts are normative', '.agents/roles/',
    'Controller-direct external review', '$hmasd-review-round',
    'cross_thread_model_effort_preservation=required',
    'live_target_profile_is_authoritative=true',
    'resolved_model_effort_copy=exact',
    'static_profile_expectation=forbidden',
    'source_boundary=local_and_remote_aggressive_tip',
    'PROJECT_MANAGER_DELIVERY_BLOCKED')) {
    if (-not $dispatcher.Contains($required)) { throw "Dispatcher missing: $required" }
}
if ($dispatcher -match '(?i)\bOMP\b|agent://|history://') { throw 'Dispatcher retains a legacy task-delivery path' }
if ($dispatcher.Contains('open_divergent_exchange') -or $dispatcher.Contains('$hmasd-review-exchange')) {
    throw 'Dispatcher retains the retired Exchange surface'
}

$monitor = Get-Content (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw
foreach ($required in @('ETA', '10 minutes', 'delete the heartbeat', 'EXPERIMENT_MONITOR',
    'Do not modify repository files', '$hmasd-experiment-monitor', 'RECOVERY_ATTEMPT',
    'recovery_exhausted=true')) {
    if (-not $monitor.Contains($required)) { throw "Monitor Skill missing: $required" }
}

if (Test-Path (Join-Path $repo ('.o' + 'mp'))) { throw 'Legacy execution directory remains' }

$batteryDocuments = @{
    'docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'K=1', 'C_total', 'I_TV')
    'docs/project/IMPLEMENTATION_PLAN.md' = @(
        'active_implementation=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1',
        'formal_path_exercise=forbidden', 'select_result_branch=forbidden')
    'docs/project/CURRENT_WORK.md' = @(
        'BATTERY_CONTRACT_RECONCILED', 'four conclusion-bearing iterations')
}
foreach ($relative in $batteryDocuments.Keys) {
    $content = Get-Content (Join-Path $repo $relative) -Raw
    foreach ($required in $batteryDocuments[$relative]) {
        if (-not $content.Contains($required)) {
            throw "Battery contract is not reconciled in ${relative}: $required"
        }
    }
}
if ($current.Contains('One unresolved question stands against the result contract')) {
    throw 'Retired behavioral-battery question remains active in CURRENT_WORK'
}
$agentContext = Get-Content (Join-Path $repo 'docs/project/AGENT_CONTEXT.md') -Raw
foreach ($required in @('C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe',
    'torch 2.7.0+cpu', 'CPU', 'torch threads 1')) {
    if (-not $agentContext.Contains($required)) { throw "Agent context missing CPU contract: $required" }
}
$agents = Get-Content (Join-Path $repo 'AGENTS.md') -Raw
$projectManagerRole = Get-Content (Join-Path $repo '.agents/roles/PROJECT_MANAGER.md') -Raw
$controllerRole = Get-Content (Join-Path $repo '.agents/roles/CONTROLLER.md') -Raw
foreach ($required in @('project_manager_project_authority=primary',
    'project_manager_research_workflow_authority=exclusive',
    'pm_acceptance_authority=exclusive', 'controller_role=mechanical_operator',
    'controller_validation_authority=none')) {
    if (-not $agents.Contains($required)) { throw "Global role constitution missing: $required" }
}
$agileDevelopment = Get-Content (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md') -Raw
$agileDevelopmentLines = @(Get-Content (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md'))
if ($agileDevelopmentLines.Count -lt 4 -or
    $agileDevelopmentLines[0] -ne '---' -or
    $agileDevelopmentLines[1] -ne 'name: hmasd-agile-research-development' -or
    $agileDevelopmentLines[2] -notmatch '^description: Use when .+' -or
    $agileDevelopmentLines[3] -ne '---') {
    throw 'Agile development Skill frontmatter is malformed or undiscoverable'
}
foreach ($required in @(
    'name: hmasd-agile-research-development',
    'superpowers_plugin=reference_only',
    'superpowers_execution=disabled',
    'development_mode=agile_algorithm_research',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'codebase_policy=small_active_line_only',
    'No backward compatibility',
    'Proof proportional to the claim',
    'This procedure grants no science, formal compute, Git, transport, or acceptance authority',
    'A bounded child requires an exact assignment',
    'Only Project Manager acting within direct user authority',
    'Inspect and report',
    'Project Manager alone accepts or directs repair',
    'At most one integrated advisory review is optional when protected semantics, cross-file integration, or material execution risk makes it useful',
    'Additional targeted review is allowed only after a failed check or a concrete protected cross-scope anomaly',
    'is not another approval layer')) {
    if (-not $agileDevelopment.Contains($required)) { throw "Agile development Skill missing: $required" }
}
foreach ($forbidden in @('superpowers_execution=enabled',
    'generic_superpowers_workflow_authority=enabled')) {
    if ($agileDevelopment.Contains($forbidden)) { throw "Agile development Skill contradicts isolation: $forbidden" }
}
foreach ($required in @('superpowers_plugin=reference_only',
    'superpowers_execution=disabled',
    'project_development_skill=hmasd-agile-research-development',
    'development_mode=agile_algorithm_research',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'codebase_policy=small_active_line_only')) {
    if (-not $agents.Contains($required)) { throw "Global Skill isolation missing: $required" }
}
$reviewRound = Get-Content (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$reviewReadme = Get-Content (Join-Path $repo 'docs/external-review/README.md') -Raw
$principles = Get-Content (Join-Path $repo 'docs/project/ALGORITHM_PRINCIPLES.md') -Raw
if (-not $reviewReadme.Contains('Persistent task IDs contain only Controller and Project Manager') -or
    $reviewReadme.Contains('Persistent task IDs contain only Controller, Project Manager and Experiment Monitor')) {
    throw 'External-review README retains the retired persistent Monitor topology'
}
foreach ($required in @('question-scoped scientific analysis and recommendations',
    'Project Manager selects and schedules the next workflow action',
    'structures the scientific response')) {
    if (-not $reviewReadme.Contains($required)) {
        throw "External-review README missing question-scoped boundary: $required"
    }
}
foreach ($forbidden in @('selecting one scheduled research action',
    'specializes the external Pro role')) {
    if ($reviewReadme.Contains($forbidden)) {
        throw "External-review README gives Pro workflow authority: $forbidden"
    }
}
foreach ($content in @($agentContext, $dispatcher, $reviewRound, $reviewReadme, $principles)) {
    foreach ($forbidden in @('pm_acceptance_authority=exclusive',
        'controller_validation_authority=none',
        'project_manager_project_authority=primary')) {
        if ($content.Contains($forbidden)) { throw "Normative role policy is duplicated outside AGENTS/role contracts: $forbidden" }
    }
}
foreach ($required in @('role=project_manager', 'project_authority=primary',
    'research_workflow_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'subtask_independent_review=not_required',
    'package_independent_review=max_one_risk_triggered',
    'additional_review=only_after_failure_or_protected_cross_scope_anomaly',
    'project_development_skill=hmasd-agile-research-development')) {
    if (-not $projectManagerRole.Contains($required)) { throw "PM role contract missing: $required" }
}
foreach ($required in @(
    'Subtasks close with their TDD evidence and one fresh focused Project Manager check',
    'Do not queue an independent reviewer for every implementation subtask',
    'Additional targeted review is allowed',
    'only after a failed check')) {
    if (-not $agents.Contains($required)) { throw "Root acceptance policy missing: $required" }
}
foreach ($required in @('role=controller', 'role_class=mechanical_operator',
    'scientific_authority=none', 'workflow_decision_authority=none')) {
    if (-not $controllerRole.Contains($required)) { throw "Controller role contract missing: $required" }
}
foreach ($forbidden in @('Controller verifies it independently',
    'Controller mechanically verifies author markers, required fields',
    'Controller validates and transmits those files',
    'mechanically validates the PM-authored package',
    'Controller checks provenance, required fields')) {
    foreach ($content in @($agents, $agentContext, $dispatcher, $reviewRound, $reviewReadme, $principles)) {
        if ($content.Contains($forbidden)) { throw "Controller retains PM validation authority: $forbidden" }
    }
}
if (-not $agentContext.Contains('does not apply to protected scientific choices')) {
    throw 'Agent context reasonable-choice rule still reaches protected science'
}
$portfolio = Get-Content (Join-Path $repo 'docs/research/cdc/IDEA_PORTFOLIO.md') -Raw
foreach ($required in @('ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1', 'C-BASE', 'C-LINK-NULL')) {
    if (-not $portfolio.Contains($required)) { throw "Portfolio missing Pro intake: $required" }
}
$conjectures = Get-Content (Join-Path $repo 'docs/research/cdc/CONJECTURES.md') -Raw
foreach ($content in @($conjectures, $portfolio)) {
    foreach ($required in @('same benchmark', 'information-matched stronger')) {
        if (-not $content.Contains($required)) { throw "C-BASE authority drift: missing $required" }
    }
}
$roundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_formal_result_review'
$rawHash = (Get-FileHash (Join-Path $roundRoot '21_PRO_OPEN_RAW.md') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($rawHash -ne 'd63427fb0fab5ffb1f393eb62370358cda449e6f1dfc8d57bc937ba46493942e') {
    throw "External Pro raw hash mismatch: $rawHash"
}
foreach ($relative in @(
    'docs/external-review/rounds/20260722_ehc_formal_result_review/30_EVIDENCE_RECONCILIATION.md',
    'docs/external-review/rounds/20260722_ehc_formal_result_review/50_DISPOSITION.md')) {
    if (-not (Test-Path (Join-Path $repo $relative) -PathType Leaf)) {
        throw "Missing completed Pro intake file: $relative"
    }
}
foreach ($required in @(
    'last_completed_assignment_id=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1',
    'active_assignment_id=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION',
    'accepted_reconciliation_sha256=700ca469ca131c58186a872dc3d8149dbb35f100910a632de0a81689d43d1a28',
    'iterations_remaining=4',
    'autonomous_research_grant=ACTIVE',
    'grant_scope=remaining_four_conclusion_bearing_iterations',
    'intermediate_authorization_prompts=forbidden',
    'implementation_status=authorized',
    'nonformal_compute_status=authorized',
    'formal_compute_status=authorized_cpu_only_under_frozen_evidence_contract',
    'git_integration_status=authorized_for_pm_accepted_packages',
    'external_review_transport_status=authorized_when_pm_selected',
    'monitoring_status=authorized_for_active_runs',
    'prototype_status=complete_valid_nonformal',
    'next_boundary=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION',
    'prototype_authorization_status=authorized_under_autonomous_grant',
    'prototype_artifact=logs/nonformal_ehc_sequence_mediation_g1_20260723_pm3',
    'prototype_manifest_sha256=40ac6659d4c8ef67a35aafc6b40bc2529b9c131c2c2888851bda4335c9324608',
    'prototype_analysis_sha256=d40b3849679bada56cbfffb5c06f6ec1b1d19757b7adc55d6c386578f6cff316',
    'prototype_measurement_disposition=measurement_path_valid_recurrence_remains_sufficient',
    'formal_evidence_contract_status=not_yet_frozen',
    'prototype_conclusion_bearing_iterations_consumed=0',
    'global_write_lease=disabled',
    'Different ownership sets may proceed concurrently')) {
    if (-not $current.Contains($required)) { throw "Current active boundary missing: $required" }
}
$prototypeNotePath = Join-Path $repo 'docs/research/cdc/EVIDENCE_NOTES/20260723_EHC_SEQUENCE_MEDIATION_PROTOTYPE_G1.md'
if (-not (Test-Path -LiteralPath $prototypeNotePath -PathType Leaf)) {
    throw 'Missing G1 prototype evidence note'
}
$prototypeNote = Get-Content -Raw -LiteralPath $prototypeNotePath
foreach ($required in @(
    'disposition=MEASUREMENT_PATH_VALID_RECURRENCE_REMAINS_SUFFICIENT',
    'manifest_sha256=40ac6659d4c8ef67a35aafc6b40bc2529b9c131c2c2888851bda4335c9324608',
    'analysis_sha256=d40b3849679bada56cbfffb5c06f6ec1b1d19757b7adc55d6c386578f6cff316',
    'measurement_tuple_sha256=673db4684404f1ac45f0bb797a0c0570f4fa0f5739757e0bb774ab56f1029f45',
    'CE-RANDOM-USE', 'CE-EXOGENOUS-LIFETIME', 'CE-LOGIT-WITHOUT-BEHAVIOR',
    'RECURRENT_CONTROL',
    'next_boundary=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION',
    'iterations_remaining=4')) {
    if (-not $prototypeNote.Contains($required)) { throw "G1 prototype evidence note missing: $required" }
}
foreach ($required in @(
    'completed_action=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1',
    'next_action=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION',
    'prototype_disposition=MEASUREMENT_PATH_VALID_RECURRENCE_REMAINS_SUFFICIENT')) {
    if (-not $portfolio.Contains($required)) { throw "Portfolio missing prototype delta: $required" }
}
foreach ($forbidden in @(
    'prototype_authorization_status=requested_not_authorized',
    'formal_compute_status=unauthorized',
    'implementation_status=unauthorized')) {
    if ($current.Contains($forbidden)) { throw "Current boundary retains superseded authorization state: $forbidden" }
}
foreach ($required in @('Controller-direct external-Pro transport',
    'primary research/workflow/algorithm/engineering authority',
    'ACTIVE mechanical operator',
    'No persistent Experiment Monitor task is active')) {
    if (-not $current.Contains($required)) { throw "Current direct-review topology missing: $required" }
}
foreach ($forbidden in @('pm_acceptance_authority=exclusive',
    'controller_validation_authority=none',
    'controller_workflow_decision_authority=none')) {
    if ($current.Contains($forbidden)) {
        throw "CURRENT_WORK duplicates normative role policy: $forbidden"
    }
}
$g1Mechanical = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_source_contract_pm_owned/50_MECHANICAL_INTAKE_RECORD.md'
if (-not (Test-Path -LiteralPath $g1Mechanical -PathType Leaf)) {
    throw 'Missing PM-owned G1 mechanical intake record'
}
$g1MechanicalText = Get-Content -Raw -LiteralPath $g1Mechanical
foreach ($required in @('record_author=controller_mechanical',
    'adoption_authority=external_pro_raw_only',
    '1ba6bdd5a8f776c1840462037a6303d587d9dc7777bf064ef2d360d36bc2781f',
    'pm_reconciliation_status=PROTECTED_SOURCE_CONTRACT_INCOMPLETE',
    'eba2160e813b13df5cbe0b819104e83a2c7750882dc4427dbad686f85ef420ae',
    'formal_compute_status=unauthorized')) {
    if (-not $g1MechanicalText.Contains($required)) { throw "G1 mechanical intake missing: $required" }
}
$reconciliation = Get-Content (Join-Path $roundRoot '30_EVIDENCE_RECONCILIATION.md') -Raw
foreach ($required in @('exact G0', 'first-match', 'Lower-precedence `G`', 'K-bin',
    '`I_TV`', '`C_total`', 'cannot relabel', 'no disposition authority')) {
    if (-not $reconciliation.Contains($required)) { throw "Reconciliation authority gap: $required" }
}
$disposition = Get-Content (Join-Path $roundRoot '50_DISPOSITION.md') -Raw
foreach ($required in @('Formal iteration-2 compute remains unauthorized',
    'There is no threshold, budget, seed, backend, diagnostic or branch rescue')) {
    if (-not $disposition.Contains($required)) { throw "Disposition authority gap: $required" }
}
$g1RoundRoot = Join-Path $repo 'docs/external-review/rounds/20260722_ehc_g1_source_contract'
$g1Question = Get-Content (Join-Path $g1RoundRoot '20_PRO_OPEN_QUESTION.md') -Raw
$listedEvidence = [regex]::Matches($g1Question, '(?m)^- `([^`]+)`\s*$')
foreach ($match in $listedEvidence) {
    $listedPath = $match.Groups[1].Value
    if ($listedPath -match '(?i)(^|[/_.-])(pm|project[_ -]?manager|internal[_ -]?manager|manager)([/_.-]|$)') {
        throw "G1 Pro question exposes internal manager evidence: $listedPath"
    }
    if (-not (Test-Path (Join-Path $repo $listedPath) -PathType Leaf)) {
        throw "G1 Pro question lists missing evidence: $listedPath"
    }
}
if ($current.Contains('iteration 2 is held at the external result-review boundary')) {
    throw 'CURRENT_WORK still holds iteration 2 at the completed review boundary'
}
$derivationNotePath = Join-Path $repo 'docs/research/cdc/EVIDENCE_NOTES/20260722_EHC_MEASUREMENT_COUNTEREXAMPLES.md'
if (-not (Test-Path -LiteralPath $derivationNotePath -PathType Leaf)) {
    throw 'Missing EHC measurement-counterexample derivation note'
}
$derivationNote = Get-Content -Raw -LiteralPath $derivationNotePath
foreach ($required in @('CE-RANDOM-USE', 'CE-EXOGENOUS-LIFETIME',
    'CE-LOGIT-WITHOUT-BEHAVIOR', 'policy-dependent persistence',
    'sequence-level intervention', 'natural mediation',
    'simpler-explanation resistance', 'held-out robustness',
    'prototype_selected=true',
    'next_boundary=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1',
    '`{6,14}` only in fitting cells',
    '`{10,18}` only in held-out cells',
    'conclusion_bearing_iterations_consumed=0',
    'iterations_remaining=4')) {
    if (-not $derivationNote.Contains($required)) {
        throw "EHC derivation note missing: $required"
    }
}
$prototypeDesignPath = Join-Path $repo 'docs/research/designs/EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1.md'
$gitignore = Get-Content -Raw -LiteralPath (Join-Path $repo '.gitignore')
if (-not $gitignore.Contains('!docs/research/designs/*.md')) {
    throw 'Durable PM research designs are not Git-visible'
}
if (-not (Test-Path -LiteralPath $prototypeDesignPath -PathType Leaf)) {
    throw 'Missing PM-accepted G1 sequence-mediation prototype design'
}
$prototypeDesign = Get-Content -Raw -LiteralPath $prototypeDesignPath
foreach ($required in @(
    'assignment_id=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1',
    'design_status=PM_ACCEPTED',
    'action_kind=bounded_nonformal_measurement_prototype',
    'conclusion_bearing_iterations_consumed=0',
    'fitting_duration_support={6,14}',
    'heldout_duration_support={10,18}',
    'registered_roster_sizes={2,3}',
    'horizon=80',
    'sequence_window_active_steps=6',
    'opportunity_rule=every_active_transition',
    'maximum_roster_capacity=4',
    'normalized_active_count_denominator=4',
    'schedule_mapping=cyclic_split_permutation',
    'action_selection=greedy_argmax_lowest_index_tie_break',
    'episode_cutoff=unfinished_segment_censored_and_eligible',
    'splits=2', 'roster_sizes=2', 'durations_per_split=2',
    'duty_sign_starts=2', 'schedule_rotations=2', 'controller_count=6',
    'episodes_per_controller=32', 'total_natural_episodes=192',
    'exact-snapshot paired sequence mediation',
    'MECHANISM_CONTROL', 'RANDOM_USE', 'EXOGENOUS_LIFETIME',
    'LOGIT_WITHOUT_BEHAVIOR', 'RECURRENT_CONTROL',
    'primitive_logits = base_logits + W_z(m*z)',
    'policy_dependence', 'sequence_hamming', 'terminal_utility_delta',
    'natural_mediation', 'heldout_robustness',
    'analysis_output=measurement_tuple_only',
    'interpretation_authority=project_manager',
    'formal_result_branch=none',
    'G0 source, runner, analyzer, thresholds, seeds and result remain closed')) {
    if (-not $prototypeDesign.Contains($required)) {
        throw "G1 sequence-mediation prototype design missing: $required"
    }
}
if ((2 * 2 * 2 * 2 * 2) -ne 32 -or (32 * 6) -ne 192) {
    throw 'G1 prototype inventory arithmetic is inconsistent'
}
foreach ($forbidden in @('MEASUREMENT_PATH_DISTINGUISHES_THREE_NULLS',
    'SURVIVING_COUNTEREXAMPLE',
    'MEASUREMENT_PATH_WITH_ORDINARY_REDUCTION_UNRESOLVED')) {
    if ($prototypeDesign.Contains($forbidden)) {
        throw "Prototype analyzer retains a post-result scientific label: $forbidden"
    }
}
$implementationPlan = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/IMPLEMENTATION_PLAN.md')
if ($implementationPlan.Contains('diagnostic disposition')) {
    throw 'G1 implementation plan retains a scientific-disposition analyzer requirement'
}
foreach ($required in @('policy-dependent persistence',
    'sequence-level intervention', 'natural mediation',
    'simpler-explanation resistance', 'held-out robustness',
    'CE-RANDOM-USE', 'CE-EXOGENOUS-LIFETIME',
    'CE-LOGIT-WITHOUT-BEHAVIOR')) {
    if (-not $conjectures.Contains($required)) {
        throw "Corrected conjecture/measurement contract missing: $required"
    }
}
$ledger = Get-Content (Join-Path $repo 'docs/research/cdc/LEMMA_COUNTEREXAMPLE_LEDGER.md') -Raw
foreach ($required in @('L-EHC-MEASUREMENT-NECESSITY',
    'CE-RANDOM-USE', 'CE-EXOGENOUS-LIFETIME',
    'CE-LOGIT-WITHOUT-BEHAVIOR', 'Preserves:', 'Violates:')) {
    if (-not $ledger.Contains($required)) { throw "CDC ledger missing derivation delta: $required" }
}
foreach ($required in @('EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1',
    'MEASUREMENT_PATH_VALID_RECURRENCE_REMAINS_SUFFICIENT',
    'ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_EXECUTABLE_DEFINITION',
    'authorization_status=authorized_under_autonomous_grant')) {
    if (-not $portfolio.Contains($required)) { throw "Portfolio missing derivation delta: $required" }
}
Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK mode=native_codex'
