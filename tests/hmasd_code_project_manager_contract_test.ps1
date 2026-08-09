$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$config = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/config.toml')
$codePmPath = Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md'
$oldPmPath = Join-Path $repo '.agents/roles/PROJECT_MANAGER.md'
$oldOperatorPath = Join-Path $repo '.agents/roles/EXTERNAL_REVIEW_OPERATOR.md'
$retiredProjectOperationsProfilePath = Join-Path $repo '.codex/agents/hmasd-project-operations-operator.toml'
$retiredIndependentReviewRolePath = Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md'
$retiredIndependentReviewProfilePath = Join-Path $repo '.codex/agents/hmasd-independent-research-review-operator.toml'
$codePm = Get-Content -Raw -LiteralPath $codePmPath
$cpmWorkspacePath = Join-Path $repo 'docs/session-workspaces/code_project_manager/README.md'
$cpmFailureContainmentPath = Join-Path $repo 'docs/session-workspaces/code_project_manager/FAILURE_CONTAINMENT.md'
$currentWorkIndexPath = Join-Path $repo 'docs/project/CURRENT_WORK.md'
$currentWorkSessionPath = Join-Path $repo 'docs/project/current-work/sessions/code_project_manager.md'
$writingAssignmentsSkillPath = Join-Path $repo '.agents/skills/hmasd-writing-agent-assignments/SKILL.md'
$writingAssignmentsSkill = Get-Content -Raw -LiteralPath $writingAssignmentsSkillPath
$writingAssignmentsSkillNormalized = $writingAssignmentsSkill -replace '\s+', ' '
$projectCognitionBootstrapPath = Join-Path $repo '.agents/skills/hmasd-writing-agent-assignments/references/project-cognition-bootstrap-prompt.md'
$codeContextGuidePath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/references/code-context-guide.md'
$assignmentBriefExamplesPath = Join-Path $repo '.agents/skills/hmasd-writing-agent-assignments/references/assignment-brief-examples.md'
$retiredProjectCognitionBootstrapPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/references/project-cognition-bootstrap-prompt.md'
$retiredAssignmentBriefExamplesPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/references/assignment-brief-examples.md'
$obsoleteWdmPlanPath = Join-Path $repo 'docs/session-workspaces/workflow_design_manager/AGILE_MODULARIZATION_AND_SUBAGENT_EXECUTION_PLAN.md'
$cpmWorkspace = Get-Content -Raw -LiteralPath $cpmWorkspacePath
$cpmFailureContainment = Get-Content -Raw -LiteralPath $cpmFailureContainmentPath
$currentWorkIndex = Get-Content -Raw -LiteralPath $currentWorkIndexPath
$currentWorkSession = Get-Content -Raw -LiteralPath $currentWorkSessionPath
$verifierRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/VERIFIER.md')
$verifierProfile = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/agents/hmasd-verifier.toml')
$reviewerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/REVIEWER.md')
$reviewerProfile = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/agents/hmasd-reviewer.toml')
$routineImplementerProfile = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/agents/hmasd-implementer-terra.toml')
$protectedImplementerProfile = Get-Content -Raw -LiteralPath (Join-Path $repo '.codex/agents/hmasd-implementer.toml')
$implementerRole = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/IMPLEMENTER.md')
$codePmNormalized = $codePm -replace '\s+', ' '
$verifierRoleNormalized = $verifierRole -replace '\s+', ' '
$implementerRoleNormalized = $implementerRole -replace '\s+', ' '
$reviewerRoleNormalized = $reviewerRole -replace '\s+', ' '
$reviewerProfileNormalized = $reviewerProfile -replace '\s+', ' '
$workflow = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/WORKFLOW_DESIGN_MANAGER.md')
$agile = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agile-research-development/SKILL.md')
$explorerValidationSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-explorer-project-validation/SKILL.md')
$explorerValidationSkillNormalized = $explorerValidationSkill -replace '\s+', ' '
$explorerValidationContract = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md')
$explorerValidationContractNormalized = $explorerValidationContract -replace '\s+', ' '
$publicHandoffContract = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/handoffs/README.md')
$publicHandoffContractNormalized = $publicHandoffContract -replace '\s+', ' '
$retiredExplorerValidationScriptPath = Join-Path $repo '.agents/skills/hmasd-explorer-project-validation/scripts/explorer_project_packet.py'
$agileNormalized = $agile -replace '\s+', ' '
$projectCognitionReferencePaths = @(
    $projectCognitionBootstrapPath,
    $codeContextGuidePath,
    $assignmentBriefExamplesPath
)
foreach ($referencePath in $projectCognitionReferencePaths) {
    if (-not (Test-Path -LiteralPath $referencePath -PathType Leaf)) {
        throw "Project cognition reference is missing: $referencePath"
    }
}
$projectCognitionBootstrap = Get-Content -Raw -LiteralPath $projectCognitionBootstrapPath
$codeContextGuide = Get-Content -Raw -LiteralPath $codeContextGuidePath
$assignmentBriefExamples = Get-Content -Raw -LiteralPath $assignmentBriefExamplesPath
$projectCognitionBootstrapNormalized = $projectCognitionBootstrap -replace '\s+', ' '
$codeContextGuideNormalized = $codeContextGuide -replace '\s+', ' '
$assignmentBriefExamplesNormalized = $assignmentBriefExamples -replace '\s+', ' '
$assertion = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/SCIENTIFIC_ASSERTION_AUDIT.md')
$assertionNormalized = $assertion -replace '\s+', ' '
$readinessScriptPath = Join-Path $repo '.agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py'
$hooksPath = Join-Path $repo '.codex/hooks.json'
$g0ReadinessContractPath = Join-Path $repo 'docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md'
$g0ReadinessContract = Get-Content -Raw -LiteralPath $g0ReadinessContractPath
$g0ReadinessContractNormalized = $g0ReadinessContract -replace '\s+', ' '

function ConvertTo-HmasdRecordMap {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $record = @{}
    foreach ($match in [regex]::Matches($Text, '(?m)^([A-Za-z0-9_]+)=(.*)$')) {
        $key = [string]$match.Groups[1].Value
        $value = ([string]$match.Groups[2].Value).TrimEnd("`r")
        if ($record.ContainsKey($key)) {
            throw "$Label duplicates key: $key"
        }
        $record[$key] = $value
    }
    return $record
}

function Assert-ExactHmasdKeyInventory {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Actual,
        [Parameter(Mandatory = $true)][string[]]$ExpectedKeys,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $actualKeys = @($Actual.Keys | Sort-Object)
    $sortedExpectedKeys = @($ExpectedKeys | Sort-Object)
    if (($actualKeys -join '|') -cne ($sortedExpectedKeys -join '|')) {
        throw "$Label key inventory mismatch: actual=$($actualKeys -join '|') expected=$($sortedExpectedKeys -join '|')"
    }
}

function Assert-HmasdRequiredKeys {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Actual,
        [Parameter(Mandatory = $true)][string[]]$RequiredKeys,
        [Parameter(Mandatory = $true)][string]$Label
    )
    foreach ($key in $RequiredKeys) {
        if (-not $Actual.ContainsKey($key)) {
            throw "$Label missing required key: $key"
        }
    }
}

if (Test-Path -LiteralPath $retiredExplorerValidationScriptPath) {
    throw 'Retired Explorer packet admission script remains'
}
foreach ($required in @(
    'temp/handoffs/explorer_to_code_manager/',
    'temp/handoffs/code_manager_to_explorer/',
    'requires no Git operation',
    'semantic writing aids, not required field names',
    'bounded safe read-only reconnaissance',
    'not a packet validator, dispatcher, queue engine or state machine',
    'direction-local binding',
    'smallest set of canonical decision/source context',
    'do not preload or merge unrequested siblings',
    'preserve the original handoff/artifact',
    'ask exactly one concrete semantic clarification')) {
    if (-not $explorerValidationSkillNormalized.Contains($required)) {
        throw "Explorer semantic handoff Skill missing: $required"
    }
}
foreach ($required in @(
    'explorer_toy_assignment_intake=semantic_treatment_brief_or_explicit_pro_frozen_review',
    'explorer_toy_local_research_read=forbidden',
    'explorer_toy_code_acceptance=exclusive_for_named_treatment',
    'explorer_public_handoff_inbound=temp/handoffs/explorer_to_code_manager/',
    'explorer_public_result_outbound=temp/handoffs/code_manager_to_explorer/',
    'explorer_public_handoff_git_authority=none',
    'explorer_public_handoff_intake=semantic_judgment_after_bounded_read_only_reconnaissance',
    'explorer_treatment_substitution_authority=none',
    'explorer_acceptance_review_route=explorer_to_agentify_after_cpm_technical_acceptance',
    'explorer_task_instruction_intake=execute_named_treatment_without_extra_confirmation',
    'explorer_result_semantic_acceptance_owner=external_pro',
    'explorer_acceptance_review_request_authority=none',
    'explorer_result_remote_evidence=exact_pushed_commit_and_public_github_locators',
    'The brief''s explicit instruction authorizes CPM to execute its named treatment',
    'resolve missing objects through direct semantic exchange',
    'When implementation derives from a submitted External Pro review',
    'Read `local_research/`')) {
    if (-not $codePmNormalized.Contains($required)) {
        throw "Code PM Explorer-toy boundary missing: $required"
    }
}
foreach ($required in @(
    'These are semantic completeness cues, not a schema or admission check',
    'order is work organization rather than queue state',
    'does not substitute External Pro for experiment, instance binding, pause or abandon',
    'Explorer gives one clear instruction naming implementation, instance binding',
    'without separate code or experiment permission fields',
    'does not reject a handoff because of formatting or a missing object',
    'External Pro uses the GitHub connection to inspect the exact pushed revision',
    'Explorer never substitutes its own acceptance',
    'The review starts only after CPM technical acceptance and push',
    'Missing formatting or a prior mechanical BLOCKED receipt is not candidate evidence',
    'selected direction identity',
    'Direction-local context binding',
    'reverse result begins with its conclusion',
    'mirrors that same primary direction or explicitly named direction set',
    'Codex-native message fallback carries the same binding',
    'preserves the original handoff/artifact',
    'asks exactly one concrete semantic clarification',
    'never reads `local_research/`')) {
    if (-not $explorerValidationContractNormalized.Contains($required)) {
        throw "Explorer validation contract missing semantic rule: $required"
    }
}
foreach ($required in @(
    'Explorer alone creates, edits and deletes its outbound files',
    'Code Manager alone creates, edits and deletes its outbound files',
    'missing schema, `document_kind`, validator receipt, hash, byte count',
    'begins with its natural-language conclusion and then appends the necessary exact evidence',
    'live files never enter Git',
    'Direction-specific briefs and reverse results follow the direction-local',
    'Codex-native message fallback carries the same binding',
    'ask exactly one concrete semantic clarification')) {
    if (-not $publicHandoffContractNormalized.Contains($required)) {
        throw "Public handoff contract missing: $required"
    }
}
if ($codePmNormalized.Contains('begin code from an Explorer public brief before External Pro freezes science')) {
    throw 'Code PM retains the retired Pro-first Explorer treatment gate'
}
if ($codePmNormalized.Contains('The active Pro disposition, frozen contract and audit status must contain')) {
    throw 'Code PM retains an unqualified Pro-derived implementation gate'
}

if ((Test-Path $oldPmPath) -or (Test-Path $oldOperatorPath) -or
    (Test-Path $retiredProjectOperationsProfilePath) -or
    (Test-Path $retiredIndependentReviewRolePath) -or
    (Test-Path $retiredIndependentReviewProfilePath)) {
    throw 'Retired manager role path remains live'
}

$routerRequired = @(
    'cross_task_transport=codex_native_send_message_to_thread',
    'code_project_manager_code_authority=exclusive',
    'code_project_manager_technical_acceptance_authority=exclusive',
    'code_project_manager_routine_implementation_agent=hmasd-implementer-terra',
    'code_project_manager_protected_implementation_agent=hmasd-implementer',
    'code_project_manager_runtime_authority=exclusive',
    'code_project_manager_current_work_authority=exclusive',
    'code_project_manager_formal_external_review_request_and_intake_authority=exclusive',
    'code_project_manager_mechanical_result_acceptance=exclusive',
    '.agents/roles/CODE_PROJECT_MANAGER.md',
    'agentify_transport_child=hmasd-agentify-transport',
    'agentify_transport_child_parent=code_project_manager|independent_research_explorer',
    'workflow_change_request_route=workflow_design_manager',
    'docs/project/SESSION_WORKSPACE_CONTRACT.md'
)
foreach ($required in $routerRequired) {
    if (-not $agents.Contains($required)) { throw "AGENTS split authority missing: $required" }
}
foreach ($retiredRouterDetail in @(
    'agentify_transport_assignment_fields=',
    'agentify_transport_result_fields=',
    'cpm_mechanical_result_fields=',
    'explorer_mechanical_result_fields=')) {
    if ($agents.Contains($retiredRouterDetail)) {
        throw "AGENTS duplicates delegated transport/mechanical schema: $retiredRouterDetail"
    }
}
foreach ($retired in @('cross_task_routing=', 'cross_task_routing_skill=', 'code_project_manager_session=')) {
    if ($agents.Contains($retired)) { throw "AGENTS retains retired fixed routing: $retired" }
}

$codeRequired = @(
    'role=code_project_manager',
    'code_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'runtime_authority=exclusive',
    'current_work_authority=exclusive_for_project_operational_records',
    'formal_external_review_request_and_intake_authority=exclusive',
    'formal_review_transport=agentify_file_batch_result',
    'scientific_authority=none',
    'workflow_design_authority=none',
    'workflow_modification_authority=none',
    'workflow_acceptance_authority=none',
    'workflow_git_authority=none',
    'workflow_change_request_route=workflow_design_manager',
    'session_owner_role=code_project_manager',
    'session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'session_workspace=docs/session-workspaces/code_project_manager|temp/sessions/code_project_manager',
    'failure_containment_contract=docs/session-workspaces/code_project_manager/FAILURE_CONTAINMENT.md',
    'local_failure_task_terminal=false',
    'git_execution=direct_for_code_runtime_review_evidence_report_ledger_and_state',
    'code_children=code_scout|implementer|reviewer|verifier',
    'routine_implementation_child=hmasd-implementer-terra',
    'protected_implementation_child=hmasd-implementer',
    'AGENTIFY_REVIEW_BATCH_ASSIGNMENT',
    'AGENTIFY_REVIEW_BATCH_RESULT',
    'experiment_child=hmasd-experiment-operator',
    'mechanical_child=hmasd-cpm-mechanical',
    'mechanical_assignment_authority=exclusive',
    'mechanical_terminal_receipt=required',
    'ticket_finalize_integrate=direct_after_acceptance',
    'reads only its terminal receipt/result',
    'orchestrator, engineering and technical-judgment owner',
    'exact-assignment author',
    'repair/retry chooser',
    'sole technical/mechanical acceptance owner',
    'sole code/Git/canonical-state integrator',
    'CODE_ACCEPTED',
    'CODE_SCIENCE_INDEX.md',
    'execution_readiness_owner=code_project_manager',
    'execution_readiness_executor=hmasd-verifier_when_triggered',
    'execution_readiness_receipt=required_when_triggered',
    'execution_readiness_phase_executor=wrapper_ordered_run_only',
    'execution_readiness_receipt_finalizer=wrapper_finalize_only',
    'only zero-compute `finalize` receives narrow elevation',
    'test_acceptance_basis=risk_and_claim_coverage',
    'test_suite_purpose=technical_acceptance_not_cpm_scoring_or_scientific_proof',
    'cross_task_transport=codex_native_send_message_to_thread',
    'cross_task_target=current_thread_id_from_user_or_native_task_context',
    'cross_task_model_and_thinking_overrides=omit',
    'passing no model or thinking override',
    'research_stage=EXPLORATION|FORMALIZATION',
    'code_change_shape=coherent_module_responsibility_with_focused_evidence',
    'successor_replaces_predecessor=same_commit_delete_code_runner_direction_test',
    'shared_abstraction_justification=ownership_or_multiple_live_callers',
    'superseded_paths_deleted=<paths-or-none-with-reason>',
    'direction_local_artifacts_deleted=<paths-or-not_applicable>',
    'module_boundary=<single-owner-module>',
    'coherent module responsibility, minimal public interfaces, directed dependencies, explicit state ownership, complexity isolation, change locality, preserved behavior and focused evidence',
    'Line and file statistics may be reported as optional diagnostics, but they cannot reject work, force arbitrary slicing or substitute for architecture review',
    'Extract a shared abstraction when it improves ownership or serves multiple live callers',
    'Focused tests alone are insufficient',
    '`interface_smoke`',
    '`bounded_exercise`',
    '`artifact_validation`',
    '`artifact_reload`',
    '`evaluate_entry`',
    '`analyze_entry`',
    'dispatches the registered `hmasd-verifier` on the clean',
    'readiness wrapper owns its mechanical lifecycle and the verifier returns typed evidence',
    'there is no Research Operations Manager',
    'Workflow Design Manager',
    'workflow_change_request_route=workflow_design_manager',
    'does not edit, accept, stage, commit or push'
)
foreach ($required in $codeRequired) {
    if (-not $codePmNormalized.Contains($required)) { throw "Code Project Manager contract missing: $required" }
}

# CPM owns conversation meaning; the child realizes the frozen brief.
$cpmConversationSurface = "$codePmNormalized $agileNormalized"
foreach ($required in @(
    'CPM owns the per-question conversation intent',
    'context brief states clean start versus one exact continuation URL',
    'prior memory helps or contaminates later reuse',
    'transmitted question contains no local filesystem path, task history or unrelated corpus',
    'reviewer-facing source locators use the public remote URL',
    'preserves conversation meaning and performs mechanical intake'
)) {
    if (-not $cpmConversationSurface.Contains($required)) {
        throw "CPM conversation authority contract missing: $required"
    }
}
if ((Test-Path -LiteralPath $retiredProjectCognitionBootstrapPath) -or
    (Test-Path -LiteralPath $retiredAssignmentBriefExamplesPath)) {
    throw 'General assignment-writing references remain under the code-only Agile Skill'
}

foreach ($retired in @(
    'AGENTIFY_REVIEW_BATCH_REQUEST',
    'dedicated Agentify task',
    'dedicated_agentify_transport_task',
    'return_task_id',
    'cross-task return',
    'repeated wait/poll/progress')) {
    if ($codePm.Contains($retired) -or $agile.Contains($retired)) {
        throw "Retired Agentify transport wording remains: $retired"
    }
}

foreach ($required in @(
    '## Triggered transport and mechanical lanes',
    'hmasd-agentify-transport',
    '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md',
    '.agents/skills/hmasd-agentify-transport/SKILL.md',
    'AGENTIFY_REVIEW_BATCH_ASSIGNMENT',
    'CPM owns the per-question conversation intent')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill Agentify child contract missing: $required"
    }
}
foreach ($required in @(
    '## Triggered transport and mechanical lanes',
    'hmasd-cpm-mechanical',
    '.agents/roles/CPM_MECHANICAL_OPERATOR.md',
    'its dispatcher own the mechanical result fields',
    'CPM remains the orchestrator, assignment author and sole technical/mechanical acceptance owner',
    '.agents/roles/EXPERIMENT_OPERATOR.md')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill mechanical protocol missing: $required"
    }
}
if ($agile.Contains('no relay or completion receipt exists')) {
    throw 'Agile Skill retains stale no-completion-receipt wording'
}

$retiredArchitectureGates = @(
    'small_' + 'active_line_only',
    'new_tracked_source_files_per_change<=' + '3',
    'refactor_' + 'active_line_delta<0',
    'new_mechanism_' + 'active_line_growth<=500',
    'existing_file_over_' + '1200_lines=must_not_grow',
    'active_' + 'line_delta=<added-minus-deleted>',
    'negative active-' + 'line delta',
    'at most 500 active ' + 'lines',
    'three tracked source files',
    'file already above 1200 ' + 'lines')
foreach ($surface in @($agents, $codePm, $agile)) {
    foreach ($retired in $retiredArchitectureGates) {
        if ($surface.Contains($retired)) {
            throw "Retired line/file acceptance gate remains: $retired"
        }
    }
}

foreach ($required in @(
    'name = "hmasd-implementer-terra"',
    'model = "gpt-5.6-terra"',
    'model_reasoning_effort = "high"',
    '.agents/roles/IMPLEMENTER.md',
    'registered child of Code Project Manager',
    'exact assignment')) {
    if (-not $routineImplementerProfile.Contains($required)) {
        throw "Routine Terra implementer profile missing: $required"
    }
}

foreach ($registration in @(
    @{ Agent = 'HMASDImplementer'; Profile = 'hmasd-implementer.toml'; Model = 'gpt-5.6-sol'; Effort = 'high' },
    @{ Agent = 'HMASDRoutineImplementer'; Profile = 'hmasd-implementer-terra.toml'; Model = 'gpt-5.6-terra'; Effort = 'high' })) {
    $header = '[agents."' + $registration.Agent + '"]'
    $headerCount = [regex]::Matches($config, [regex]::Escape($header)).Count
    if ($headerCount -ne 1) {
        throw "Implementer registration must appear exactly once: $($registration.Agent)"
    }
    $configFile = 'config_file = "./agents/' + $registration.Profile + '"'
    if ([regex]::Matches($config, [regex]::Escape($configFile)).Count -ne 1) {
        throw "Implementer profile path must appear exactly once: $($registration.Profile)"
    }
}
foreach ($profileRoute in @(
    @{ Text = $protectedImplementerProfile; Model = 'gpt-5.6-sol'; Effort = 'high'; Label = 'protected Sol' },
    @{ Text = $routineImplementerProfile; Model = 'gpt-5.6-terra'; Effort = 'high'; Label = 'routine Terra' })) {
    foreach ($required in @(
        ('model = "' + $profileRoute.Model + '"'),
        ('model_reasoning_effort = "' + $profileRoute.Effort + '"'),
        '.agents/roles/IMPLEMENTER.md')) {
        if (-not $profileRoute.Text.Contains($required)) {
            throw "$($profileRoute.Label) profile routing missing: $required"
        }
    }
}

foreach ($profile in @($routineImplementerProfile, $protectedImplementerProfile)) {
    foreach ($required in @('exact assignment', '.agents/roles/IMPLEMENTER.md',
            'registered child of Code Project Manager', 'Do not mutate Git')) {
        if (-not $profile.Contains($required)) {
            throw "Thin implementer profile missing the shared pointer/boundary: $required"
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
        if ($profile.Contains($forbidden)) {
            throw "Thin implementer profile duplicates Role procedure: $forbidden"
        }
    }
}
foreach ($required in @('returned `resolved_worktree` as the only edit root',
        '`apply_patch` does not inherit a shell working directory',
        'every patch target', 'absolute path', 'After the first patch')) {
    if (-not $implementerRole.Contains($required)) {
        throw "Implementer role missing ticketed apply_patch targeting rule: $required"
    }
}
if (-not $implementerRole.Contains('reversible local engineering choice')) {
    throw 'Implementers lack bounded local engineering judgment'
}
foreach ($required in @(
        'purpose, observed behavior or failure, consumer relationships',
        'frozen scientific or technical choices',
        'necessary consequential scope',
        'focused evidence',
        'Assignment quality governs executability and outcome',
        'model strength adds no authority and never substitutes for a complete assignment',
        'Every result must begin with a concise natural-language conclusion',
        'what outcome was achieved or remains unresolved',
        'direct consumer or cross-module consequence checked',
        'residual uncertainty',
        'A mechanical status or changed-path list alone is not a complete result')) {
    if (-not $implementerRoleNormalized.Contains(($required -replace '\s+', ' '))) {
        throw "Implementer result/context contract missing: $required"
    }
}
if (-not $routineImplementerProfile.Contains('material or outcome-changing') -or
    -not $routineImplementerProfile.Contains('reversible internal organization') -or
    $routineImplementerProfile.Contains('You do not choose scientific semantics, architecture direction')) {
    throw 'Terra local-judgment boundary is not precise'
}
foreach ($required in @('protected Sol route', 'assignment-specified semantics')) {
    if (-not $protectedImplementerProfile.Contains($required)) {
        throw "Protected Sol routing distinction missing: $required"
    }
}
foreach ($profile in @($reviewerProfile)) {
    if (-not $profile.Contains('child-context') -or
        -not $profile.Contains('exact assignment controls')) {
        throw 'Reviewer profile does not point to the shared assignment contract'
    }
}
foreach ($required in @(
        'exact Code Project Manager readiness assignment',
        '.agents/roles/VERIFIER.md',
        "assignment's natural-language brief")) {
    if (-not $verifierProfile.Contains($required)) {
        throw "Verifier profile does not point to the shared assignment contract: $required"
    }
}
foreach ($required in @('default_fork_turns=3',
        'natural-language assignment is the source of outcome',
        'rigid schema or admission gate')) {
    if (-not $implementerRoleNormalized.Contains($required)) {
        throw "Implementer role missing assignment contract: $required"
    }
}
foreach ($required in @('default_fork_turns=none',
        'review_passes_per_reviewer=1',
        'review_scope=coherent_integrated_batch_not_each_implementer',
        'parallel_review_condition=genuinely_independent_questions_only',
        'automatic_re_review=forbidden')) {
    if (-not $reviewerRoleNormalized.Contains($required)) {
        throw "Reviewer role missing batch-review contract: $required"
    }
}
if (-not $verifierRoleNormalized.Contains('invocation/observation failure') -or
    -not $verifierRoleNormalized.Contains('Never start a second wrapper run')) {
    throw 'Verifier does not distinguish tool observation loss from phase evidence'
}
foreach ($required in @('default_fork_turns=1',
        'existing Code Project Manager readiness trigger',
        'rigid schema or admission gate')) {
    if (-not $verifierRoleNormalized.Contains($required)) {
        throw "Verifier role missing assignment contract: $required"
    }
}
foreach ($surface in @($codePmNormalized, $agileNormalized)) {
    foreach ($required in @('coherent group of implementer changes',
            'one independent reviewer by default',
            'genuinely independent review questions',
            'Never review once per implementer', 'existing readiness trigger')) {
        if (-not $surface.Contains($required)) {
            throw "Code review batching contract missing: $required"
        }
    }
}

if ($codePm.Contains('Never load `docs/project/CURRENT_WORK.md`')) {
    throw 'Code Project Manager retains the obsolete CURRENT_WORK read prohibition'
}

foreach ($required in @(
    'new persistent coding task',
    'clearly lacks the project mental model',
    'never copied to each child',
    'Local tasks remain local',
    'Coupled tasks read only the relevant',
    'Load-bearing tasks read only the relevant',
    'not schemas or admission gates')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill missing project-cognition loading rule: $required"
    }
}
foreach ($required in @(
    'hmasd-writing-agent-assignments',
    '.agents/skills/hmasd-writing-agent-assignments/references/project-cognition-bootstrap-prompt.md',
    'references/code-context-guide.md',
    '.agents/skills/hmasd-writing-agent-assignments/references/assignment-brief-examples.md',
    'forked turns are background')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill missing project-cognition reference pointer: $required"
    }
}
foreach ($required in @(
    'smallest sufficient understanding',
    'context depth',
    'parent is a context compiler')) {
    if (-not $projectCognitionBootstrapNormalized.Contains($required) -and
        -not $codeContextGuideNormalized.Contains($required)) {
        throw "Project cognition references missing structural cue: $required"
    }
}
if (-not $assignmentBriefExamplesNormalized.Contains('natural-language assignments') -or
    -not $assignmentBriefExamplesNormalized.Contains('not templates')) {
    throw 'Assignment brief examples are missing their non-schema contract'
}
foreach ($required in @(
    'PROJECT_MAP.md',
    'owns map accuracy',
    'same code commit',
    'stable lineage role',
    'default execution shape',
    'load-bearing state owner',
    'stable dependency direction',
    'isolated/legacy membership in the default route',
    'Ordinary local internals',
    'temporary experiments',
    'discovered discrepancy',
    'integrated reviewer checks map consistency only when',
    'no additional reviewer or approval gate')) {
    if (-not $codePmNormalized.Contains($required)) {
        throw "Code Project Manager map-maintenance contract missing: $required"
    }
}
foreach ($required in @(
    'project_map_owner=code_project_manager',
    'project_map_update=same_commit_when_stable_architecture_fact_changes')) {
    if (-not $agents.Contains($required)) {
        throw "AGENTS project-cognition pointer missing: $required"
    }
}
if (-not $currentWorkIndex.Contains('docs/project/PROJECT_MAP.md')) {
    throw 'CURRENT_WORK index is missing the stable project-map pointer'
}
if (Test-Path -LiteralPath $obsoleteWdmPlanPath) {
    throw 'Obsolete WDM modularization plan remains live'
}

if (-not $workflow.Contains('workflow_design_authority=exclusive_for_all_workflow_control_plane_surfaces') -or
    -not $workflow.Contains('other persistent sessions report a precise requirement or defect')) {
    throw 'Workflow Design Manager centralized ownership boundary is missing'
}
if (-not $agileNormalized.Contains('Code Project Manager alone accepts code') -or
    -not $agileNormalized.Contains('owns runtime, transport and Git integration')) {
    throw 'Agile Skill does not preserve CPM ownership'
}
if ($agileNormalized.Contains('External Review Operator') -or
    $agileNormalized.Contains('Project Operations Operator')) {
    throw 'Agile Skill retains a stale or ambiguous review route'
}
if (-not $agileNormalized.Contains('CODE_SCIENCE_ALIGNMENT_AUDIT') -or
    -not $agileNormalized.Contains('Agentify Transport Operator')) {
    throw 'Agile Skill does not route the code-science audit through Agentify transport'
}
foreach ($surface in @($codePm, $agile)) {
    foreach ($required in @(
        'scripts/hmasd_workspace_ticket.py provision',
        'C:/worktrees/HMASD',
        'Raw external `git worktree`')) {
        if (-not $surface.Contains($required)) {
            throw "Code-PM worktree provisioning contract missing: $required"
        }
    }
}
if ($assertionNormalized.Contains('Research Operations Manager') -or
    -not $assertionNormalized.Contains('opens one exact correction assignment') -or
    -not $assertionNormalized.Contains('After `CODE_ACCEPTED`')) {
    throw 'Alignment mismatch repair ownership is ambiguous'
}
if ($workflow.Contains('Project-Manager workflow-design assignment')) {
    throw 'Workflow Design Manager retains the retired requester identity'
}

foreach ($required in @(
    'session_owner_role=code_project_manager',
    'session_owner_id=019f9e4f-f4d0-7fe0-b214-c47fd034e84d',
    'durable_workspace=docs/session-workspaces/code_project_manager/',
    'temporary_workspace=temp/sessions/code_project_manager/')) {
    if (-not $cpmWorkspace.Contains($required)) {
        throw "Code PM session workspace missing: $required"
    }
}
foreach ($required in @(
    'document_kind=code_project_manager_role_local_failure_containment_contract',
    'mechanical_operation_state_owner=originating_tool_or_script',
    'typed_terminal_evidence=registered_receipt_or_exit_evidence',
    'model_authored_operation_state_machine=forbidden',
    'child_terminal_effect=evidence_only',
    'local_failure_task_terminal=false',
    'continuation_default=select_next_legal_action',
    'session_blocked_evidence=global_integrity_witness_or_complete_no_legal_action_receipts')) {
    if (-not $cpmFailureContainment.Contains($required)) {
        throw "Code PM failure-containment contract missing: $required"
    }
}
foreach ($required in @(
    'mechanical_operation_state_owner=originating_tool_or_script',
    'model_authored_operation_state_machine=forbidden',
    'cpm_decision_surface=semantic_next_action_only',
    'local_failure_default=continue_next_legal_action')) {
    if (-not $agile.Contains($required)) {
        throw "Agile Skill missing mechanical-state ownership rule: $required"
    }
}
foreach ($forbidden in @(
    'failure_scope=operation|workstream|session',
    'runnable_queue_scan=',
    'Required routing witnesses:',
    'scan the authorized runnable queue',
    'classify every runtime terminal event', 'terminal-event routing')) {
    if ($cpmFailureContainment.Contains($forbidden) -or $codePmNormalized.Contains($forbidden) -or
        $agileNormalized.Contains($forbidden)) {
        throw "Code PM still requires a model-authored workflow state machine: $forbidden"
    }
}

$currentWorkIndexMap = ConvertTo-HmasdRecordMap -Text $currentWorkIndex -Label 'CURRENT_WORK index'
Assert-ExactHmasdKeyInventory -Actual $currentWorkIndexMap -ExpectedKeys @(
    'document_kind', 'schema_version', 'index_owner', 'state_updated',
    'session_record_ids', 'common_record_ids', 'legacy_snapshot') -Label 'CURRENT_WORK index'
if ($currentWorkIndexMap.document_kind -cne 'current_work_index' -or
    $currentWorkIndexMap.schema_version -cne '3' -or
    $currentWorkIndexMap.index_owner -cne 'workflow_design_manager' -or
    $currentWorkIndexMap.state_updated -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw 'CURRENT_WORK index identity/schema is invalid'
}

$currentWorkSessionMap = ConvertTo-HmasdRecordMap -Text $currentWorkSession -Label 'Code PM current-work session'
Assert-ExactHmasdKeyInventory -Actual $currentWorkSessionMap -ExpectedKeys @(
    'document_kind', 'schema_version', 'session_owner_role', 'session_owner_id',
    'workstream_ids', 'external_pointer_ids') -Label 'Code PM current-work session'
if ($currentWorkSessionMap.document_kind -cne 'current_work_session' -or
    $currentWorkSessionMap.schema_version -cne '1' -or
    $currentWorkSessionMap.session_owner_role -cne 'code_project_manager' -or
    $currentWorkSessionMap.session_owner_id -cne '019f9e4f-f4d0-7fe0-b214-c47fd034e84d') {
    throw 'Code PM current-work session identity/schema is invalid'
}

$stateBearingKeys = @(
    'status', 'active_assignment_id', 'next_boundary', 'environment',
    'grant_or_authority_reference', 'grant_iterations_authorized',
    'grant_iterations_remaining', 'conclusion_bearing_iterations_consumed_total',
    'scientific_iteration_cost_current_boundary', 'completed_candidate_ids',
    'next_candidate_id', 'current_evidence_pointer', 'state_source',
    'latest_artifact_pointer', 'project_state_replication')
foreach ($container in @(
    @{ Label = 'CURRENT_WORK index'; Record = $currentWorkIndexMap },
    @{ Label = 'Code PM current-work session'; Record = $currentWorkSessionMap })) {
    foreach ($key in $stateBearingKeys) {
        if ($container.Record.ContainsKey($key)) {
            throw "$($container.Label) duplicates state-bearing key: $key"
        }
    }
}

$sessionWorkstreamIds = @($currentWorkSessionMap.workstream_ids -split '\|')
$sessionPointerIds = @($currentWorkSessionMap.external_pointer_ids -split '\|')
$cpmRecordIds = @($sessionWorkstreamIds + $sessionPointerIds)
$publicSessionIds = @($currentWorkIndexMap.session_record_ids -split '\|')
$indexedRecordIds = @($currentWorkIndexMap.common_record_ids -split '\|')
if (($cpmRecordIds | Sort-Object -Unique).Count -ne $cpmRecordIds.Count -or
    ($publicSessionIds | Sort-Object -Unique).Count -ne $publicSessionIds.Count -or
    ($indexedRecordIds | Sort-Object -Unique).Count -ne $indexedRecordIds.Count -or
    $publicSessionIds -cnotcontains 'code_project_manager' -or
    $publicSessionIds -cnotcontains 'workflow_design_manager' -or
    $indexedRecordIds -cnotcontains 'workflow_control_plane') {
    throw 'Current-work session/index inventories contain duplicates or omit Code PM'
}
foreach ($recordId in $cpmRecordIds) {
    if ($indexedRecordIds -cnotcontains $recordId) {
        throw "Code PM session record is absent from the public index: $recordId"
    }
}

$commonDirectory = Join-Path $repo 'docs/project/current-work/common'
foreach ($recordId in $cpmRecordIds) {
    $recordPath = Join-Path $commonDirectory "$recordId.md"
    $record = ConvertTo-HmasdRecordMap -Text (Get-Content -Raw -LiteralPath $recordPath) -Label $recordId
    Assert-HmasdRequiredKeys -Actual $record -RequiredKeys @(
        'document_kind', 'schema_version', 'record_id', 'record_kind', 'owner_role') -Label $recordId
    if ($record.document_kind -cne 'current_work_common_record' -or
        $record.schema_version -cne '1' -or $record.record_id -cne $recordId -or
        $record.owner_role -cne 'code_project_manager') {
        throw "Current-work common record identity/schema mismatch: $recordId"
    }
    if (-not $currentWorkIndex.Contains("current-work/common/$recordId.md")) {
        throw "CURRENT_WORK index omits the link for: $recordId"
    }
    if ($sessionWorkstreamIds -ccontains $recordId) {
        Assert-HmasdRequiredKeys -Actual $record -RequiredKeys @(
            'workstream_id', 'status', 'active_assignment_id', 'next_boundary',
            'environment', 'grant_or_authority_reference', 'current_evidence_pointer') -Label $recordId
        if ($record.record_kind -cne 'workstream' -or $record.workstream_id -cne $recordId) {
            throw "Current-work workstream identity mismatch: $recordId"
        }
    } elseif ($sessionPointerIds -ccontains $recordId) {
        Assert-HmasdRequiredKeys -Actual $record -RequiredKeys @(
            'pointer_id', 'subject_owner_role', 'session_id', 'state_source',
            'latest_artifact_pointer', 'project_state_replication') -Label $recordId
        if ($record.record_kind -cne 'external_owner_pointer' -or
            $record.project_state_replication -cne 'forbidden') {
            throw "Current-work external pointer identity mismatch: $recordId"
        }
    } else {
        throw "Common record is not owned by the Code PM session roster: $recordId"
    }
}

foreach ($required in @(
    '## Triggered execution-readiness lane',
    'focused tests alone are insufficient',
    'hmasd-verifier',
    '.agents/roles/VERIFIER.md',
    'hmasd_execution_readiness.py',
    'consumes the typed receipt and alone accepts or repairs the candidate')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill missing execution-readiness rule: $required"
    }
}
foreach ($required in @(
    'role=verifier',
    'authority=one_exact_execution_readiness_assignment',
    'execution_readiness_executor=required_when_triggered_by_code_project_manager',
    'formal_compute_authority=none',
    'readiness_phase_executor=wrapper_run_only',
    'readiness_receipt_finalizer=wrapper_finalize_only',
    'never pre-run, replay or manually invoke',
    'Do not elevate `run`',
    'sum of the six phase timeouts plus 60 seconds',
    'exact proof-sized exercise root',
    "readiness script's Git-private receipt",
    'terminal_handoff=file_backed_compact_native_final',
    'terminal_receipt_path=assignment_named_final_receipt',
    'file-backed terminal handoff',
    'compact status',
    'VERIFIER_TERMINAL',
    'receipt_path=<exact final receipt path or unavailable>',
    'first direct failure',
    'Do not transcribe model or',
    'Code Project Manager classifies the failure and alone accepts the code')) {
    if (-not $verifierRoleNormalized.Contains($required)) {
        throw "Verifier role missing execution-readiness boundary: $required"
    }
}
foreach ($required in @(
    'request_id=UAV_G0_READINESS_PERFORMANCE_CONTRACT_V3',
    'candidate_identity=checked_out_clean_HEAD',
    'source_execution_bridge=forbidden',
    'execution_support_delta=forbidden',
    'interface_smoke_timeout_seconds=60',
    'bounded_exercise_timeout_seconds=1200',
    'artifact_validation_timeout_seconds=300',
    'artifact_reload_timeout_seconds=300',
    'evaluate_entry_timeout_seconds=300',
    'analyze_entry_timeout_seconds=300',
    'outer_run_timeout_seconds=2520',
    'finalize_timeout_seconds=120',
    'candidate_attempt_limit=3',
    'fresh_absent_root_required=true',
    'full_six_phase_candidate_bound_receipt=required',
    'formal_compute=forbidden',
    'scientific_iteration_cost=zero')) {
    if (-not $g0ReadinessContractNormalized.Contains($required)) {
        throw "G0 readiness performance contract missing: $required"
    }
}
$g0CodePaths = @(
    'ha_ctse_process/uav_episode_schema.py',
    'ha_ctse_process/uav_episode_serialization.py',
    'ha_ctse_process/uav_g0_geometry.py',
    'ha_ctse_process/uav_g0_statistics.py',
    'ha_ctse_process/uav_g0_oracle_evidence.py',
    'ha_ctse_process/uav_g0_controllers.py',
    'ha_ctse_process/uav_g0_environment.py',
    'ha_ctse_process/uav_source_identifiability_g0.py',
    'scripts/uav_g0_artifact_io.py',
    'scripts/run_uav_source_identifiability_g0.py',
    'tests/ha_ctse_process_uav_source_identifiability_g0_test.py',
    'tests/run_uav_source_identifiability_g0_test.py',
    'docs/research/designs/UAV_SOURCE_IDENTIFIABILITY_G0_CODE_SCIENCE_INDEX.md'
)
if (-not $g0ReadinessContract.Contains('exact thirteen-path implementation boundary')) {
    throw 'G0 readiness performance contract does not freeze the thirteen-path boundary'
}
foreach ($required in $g0CodePaths) {
    if (-not $g0ReadinessContract.Contains($required)) {
        throw "G0 readiness performance path boundary missing: $required"
    }
}
foreach ($required in @(
    'test_acceptance_basis=risk_and_claim_coverage',
    'line_coverage_target=none',
    'test_count_target=none',
    'cpm_performance_scoring_from_tests=forbidden',
    'formal_result_snapshot_oracle=forbidden',
    'direction_local_test_lifetime=active_implementation_only',
    'shared_defect_regression_promotion=plausible_recurrence_only',
    'these classes are alternatives selected by the task, not four mandatory gates',
    'The implementer normally owns the assigned code and its corresponding focused test together',
    'verifier use remains optional',
    'registered verifier is the required mechanical executor on the clean candidate commit',
    'This is not a routine gate for ordinary code changes',
    'A focused test should reject one plausible wrong implementation',
    'remove its code and test together when the direction leaves the active line',
    'Run a broad suite only for an actually changed shared surface')) {
    if (-not $agileNormalized.Contains($required)) {
        throw "Agile Skill missing proof-sized test strategy: $required"
    }
}
foreach ($required in @(
    'Persistent tests protect stable shared contracts',
    'A direction-local test has the lifetime of its active implementation',
    'Test count, line coverage and a prior formal result are not technical-acceptance targets')) {
    if (-not $codePmNormalized.Contains($required)) {
        throw "Code Project Manager test-acceptance boundary missing: $required"
    }
}
if (-not (Test-Path -LiteralPath $readinessScriptPath -PathType Leaf)) {
    throw 'Execution-readiness script is missing'
}
$readinessScript = Get-Content -Raw -LiteralPath $readinessScriptPath
if ($readinessScript.Contains('019f9e4f-f4d0-7fe0-b214-c47fd034e84d') -or
    -not $readinessScript.Contains('session_owner_id=')) {
    throw 'Execution-readiness hook duplicates the fixed Code PM session instead of reading the role charter'
}
if (-not (Test-Path -LiteralPath $hooksPath -PathType Leaf)) {
    throw 'Code acceptance hook configuration is missing'
}
$hooks = Get-Content -Raw -LiteralPath $hooksPath | ConvertFrom-Json
$preHooks = @($hooks.hooks.PreToolUse)
$boundaryHooks = @($preHooks | Where-Object { $_.matcher -match 'shell_command' })
if ($boundaryHooks.Count -ne 1 -or
    @($boundaryHooks[0].hooks).Count -ne 1 -or
    $boundaryHooks[0].hooks[0].command -notmatch 'hmasd_workspace_boundary_guard\.py' -or
    $boundaryHooks[0].hooks[0].timeout -ne 5) {
    throw 'Workspace-boundary PreToolUse hook is missing or ambiguous'
}
$stopHooks = @($hooks.hooks.Stop)
if ($stopHooks.Count -ne 1 -or
    @($stopHooks[0].hooks).Count -ne 1 -or
    $stopHooks[0].hooks[0].type -ne 'command' -or
    $stopHooks[0].hooks[0].command -notmatch 'hmasd_execution_readiness\.py.*hook-stop' -or
    $stopHooks[0].hooks[0].timeout -ne 10) {
    throw 'Code acceptance Stop hook is not narrow and deterministic'
}
$configuredHookPayload = @{ session_id = 'non-code-pm-hook-command-smoke'; stop_hook_active = $false; last_assistant_message = 'ordinary turn' } | ConvertTo-Json -Compress
Push-Location $repo
try {
    $configuredHookOutput = $configuredHookPayload | & cmd.exe /d /s /c $stopHooks[0].hooks[0].command
    if ($LASTEXITCODE -ne 0 -or $configuredHookOutput) {
        throw 'Configured Stop hook command is not executable from the repository root'
    }
}
finally {
    Pop-Location
}


$parentContracts = @{
    '.agents/roles/CODE_SCOUT.md' = 'parent=code_project_manager'
    '.agents/roles/IMPLEMENTER.md' = 'parent=code_project_manager'
    '.agents/roles/REVIEWER.md' = 'parent=code_project_manager'
    '.agents/roles/VERIFIER.md' = 'parent=code_project_manager'
    '.agents/roles/EXPERIMENT_OPERATOR.md' = 'parent=code_project_manager'
}
foreach ($entry in $parentContracts.GetEnumerator()) {
    $text = Get-Content -Raw -LiteralPath (Join-Path $repo $entry.Key)
    if (-not $text.Contains($entry.Value)) {
        throw "Child ownership mismatch: $($entry.Key) requires $($entry.Value)"
    }
}

Write-Output 'HMASD_CODE_PROJECT_MANAGER_CONTRACT_OK'
