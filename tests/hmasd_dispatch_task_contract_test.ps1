[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/SKILL.md'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/references/session-roles.json'
$skill = Get-Content -LiteralPath $skillPath -Raw
$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json
$agents = Get-Content -LiteralPath (Join-Path $repo 'AGENTS.md') -Raw
$review = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md') -Raw
$monitor = Get-Content -LiteralPath (Join-Path $repo '.agents/skills/hmasd-experiment-monitor/SKILL.md') -Raw
$roleRoot = Join-Path $repo '.agents/roles'
$controllerRolePath = Join-Path $roleRoot 'CONTROLLER.md'
$projectManagerRolePath = Join-Path $roleRoot 'PROJECT_MANAGER.md'
$monitorRolePath = Join-Path $roleRoot 'EXPERIMENT_MONITOR.md'
$externalProRolePath = Join-Path $roleRoot 'EXTERNAL_PRO.md'

foreach ($path in @($controllerRolePath, $projectManagerRolePath,
        $monitorRolePath, $externalProRolePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing normative role contract: $path"
    }
}
$controllerRole = Get-Content -LiteralPath $controllerRolePath -Raw
$projectManagerRole = Get-Content -LiteralPath $projectManagerRolePath -Raw
$monitorRole = Get-Content -LiteralPath $monitorRolePath -Raw
$externalProRole = Get-Content -LiteralPath $externalProRolePath -Raw

$expected = @('controller', 'project_manager')
$actual = @($roles.roles.PSObject.Properties.Name)
if ($roles.schema_version -ne 13 -or (Compare-Object $expected $actual)) {
    throw 'Persistent role graph must contain only controller and project_manager at schema 13'
}
if ($roles.roles.controller.thread_id -ne '019f8995-7550-7c82-8f31-ad08a3d381d4' -or
    $roles.roles.controller.contract -ne '.agents/roles/CONTROLLER.md' -or
    $roles.roles.project_manager.thread_id -ne '019f8a2e-ed73-7a02-9bb9-4a57b2054cf3' -or
    $roles.roles.project_manager.registration_status -ne 'ACTIVE' -or
    $roles.roles.project_manager.contract -ne '.agents/roles/PROJECT_MANAGER.md') {
    throw 'Persistent controller/manager binding mismatch'
}
if ($roles.interfaces.experiment_monitor.persistent_task -ne $false -or
    $roles.interfaces.experiment_monitor.operator -ne 'controller' -or
    $roles.interfaces.experiment_monitor.contract -ne '.agents/roles/EXPERIMENT_MONITOR.md' -or
    $roles.interfaces.experiment_monitor.procedure -ne '.agents/skills/hmasd-experiment-monitor/SKILL.md') {
    throw 'Controller-direct monitor interface mismatch'
}
if ($roles.policy.update_owner -ne 'project_manager' -or
    $roles.policy.integration_executor -ne 'controller_mechanical' -or
    $roles.policy.concurrency_policy -ne 'file_ownership_only' -or
    $roles.policy.global_write_lease -ne 'disabled' -or
    $roles.policy.preserve_live_execution_profile -ne $true) {
    throw 'Role registry does not make PM the workflow semantic owner and Controller the mechanical integrator'
}
foreach ($entry in $roles.roles.PSObject.Properties.Value) {
    foreach ($field in @('hostId', 'model', 'thinking')) {
        if ($null -ne $entry.PSObject.Properties[$field]) { throw "Static route field: $field" }
    }
}
foreach ($required in @(
    'Role contracts are normative',
    '.agents/roles/',
    'resolve_task_route.ps1 -Role <role>',
    'cross_thread_model_effort_preservation=required',
    'live_target_profile_is_authoritative=true',
    'resolved_model_effort_copy=exact',
    'static_profile_expectation=forbidden',
    'experiment_monitor',
    'hmasd-experiment-monitor',
    'Controller-direct external review',
    '$hmasd-review-round',
    '$browser:control-in-app-browser',
    'Before `IMPLEMENTATION_READY`',
    'IMPLEMENTATION_READY',
    'RESEARCH_MANAGER_BLOCKED',
    'codex_app__send_message_to_thread',
    'PROJECT_MANAGER_DELIVERY_BLOCKED',
    'Controller completion callback',
    'CONTROLLER_OPERATION_RECEIPT',
    'return_role=project_manager',
    'operation_status',
    'result_identity',
    'path_source_status',
    'remaining_authority',
    'resolve_task_route.ps1 -Role project_manager',
    'CONTROLLER_CALLBACK_BLOCKED',
    '`controller` and calls',
    'resolve_source_boundary.ps1',
    'source_boundary=local_and_remote_aggressive_tip',
    'SOURCE_BOUNDARY_DIVERGED')) {
    if (-not $skill.Contains($required)) { throw "Dispatcher missing: $required" }
}
if ($skill.Contains('path_hash_source_status')) {
    throw 'Dispatcher retains the workflow hash receipt field'
}
foreach ($forbidden in @(
    'controller <-> research_project_manager',
    'controller <-> open_divergent_exchange',
    'open_divergent_exchange',
    '$hmasd-review-exchange',
    'REVIEW_STAGE_COMPLETE',
    'REVIEW_STAGE_BLOCKED',
    'pm_acceptance_authority=exclusive',
    'controller_validation_authority=none',
    'External GPT-5.6 Pro owns',
    'Project Manager owns',
    'The Controller owns routing',
    'agent://',
    'history://')) {
    if ($skill.Contains($forbidden)) { throw "Dispatcher contains retired or normative role policy: $forbidden" }
}
if ($skill.Contains('direct evidence intake')) {
    throw 'Dispatcher still assigns semantic evidence intake to Controller'
}
foreach ($required in @('$hmasd-dispatch-task', '$hmasd-review-round',
    '$browser:control-in-app-browser', '$hmasd-experiment-monitor')) {
    if (-not $controllerRole.Contains($required)) { throw "Controller role missing operation trigger: $required" }
}
foreach ($required in @(
    '# HMASD Role Constitution',
    'Mandatory role bootstrap',
    'project_manager_project_authority=primary',
    'project_manager_research_workflow_authority=exclusive',
    'pm_acceptance_authority=exclusive',
    'controller_role=mechanical_operator',
    'controller_validation_authority=none',
    'controller_research_authority=none',
    'controller_workflow_decision_authority=none',
    'one_artifact_one_acceptance_owner=true',
    'concurrency_policy=file_ownership_only',
    'global_write_lease=disabled',
    'same_file_concurrent_writes=forbidden',
    'disjoint_file_parallelism=allowed',
    'cross_thread_model_effort_preservation=required',
    'live_target_profile_is_authoritative=true',
    'resolved_model_effort_copy=exact',
    'static_profile_expectation=forbidden',
    'sender_profile_override=forbidden',
    'mechanical_completion_callback=required',
    'mechanical_completion_receipt_wakes_project_manager=true',
    'at most one independent advisory code-side review',
    'does not create a repository-wide write lease')) {
    if (-not $agents.Contains($required)) { throw "Global role constitution missing: $required" }
}
foreach ($required in @(
    'role=project_manager',
    'project_authority=primary',
    'research_workflow_authority=exclusive',
    'technical_acceptance_authority=exclusive',
    'external_review_need_authority=project_manager',
    'formal_compute_authority=user_only',
    'git_execution=controller_mechanical',
    'one_artifact_one_acceptance_owner=true',
    'file_ownership_required=true',
    'mechanical_completion_receipt_wakes_project_manager=true')) {
    if (-not $projectManagerRole.Contains($required)) { throw "Project Manager role missing: $required" }
}
foreach ($required in @(
    'role=controller',
    'role_class=mechanical_operator',
    'scientific_authority=none',
    'technical_validation_authority=none',
    'workflow_decision_authority=none',
    'external_review_transport=mechanical_exact',
    'git_execution=mechanical_exact',
    'experiment_operations=authorized_commands_and_direct_monitoring_only',
    'cross_thread_model_effort_preservation=required',
    'live_target_profile_is_authoritative=true',
    'resolved_model_effort_copy=exact',
    'static_profile_expectation=forbidden',
    'sender_profile_override=forbidden',
    'mechanical_completion_callback=required',
    'CONTROLLER_OPERATION_RECEIPT')) {
    if (-not $controllerRole.Contains($required)) { throw "Controller role missing: $required" }
}
foreach ($required in @('role=experiment_monitor',
    'authority=read_only_observation', 'scientific_interpretation=forbidden')) {
    if (-not $monitorRole.Contains($required)) { throw "Monitor role missing: $required" }
}
foreach ($required in @('role=external_pro',
    'role_kind=external_question_scoped_scientific_authority',
    'transport_owner=controller_mechanical', 'workflow_authority=none',
    'code_authority=none')) {
    if (-not $externalProRole.Contains($required)) { throw "External Pro interface missing: $required" }
}
foreach ($required in @(
    'inspect the registered conversation before submission',
    'Role contracts are normative',
    'late output from a retired role has no authority')) {
    if (-not $review.Contains($required)) { throw "Direct review contract missing: $required" }
}
foreach ($required in @('$hmasd-experiment-monitor', 'RECOVERY_ATTEMPT', 'recovery_exhausted=true')) {
    if (-not $monitor.Contains($required)) { throw "Monitor recovery contract missing: $required" }
}
$sourceResolver = Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_source_boundary.ps1'
if (-not (Test-Path -LiteralPath $sourceResolver -PathType Leaf)) { throw 'Missing source-boundary resolver' }
$sourceBoundary = & $sourceResolver | ConvertFrom-Json
if ($sourceBoundary.source_boundary -ne 'local_and_remote_aggressive_tip' -or
    $sourceBoundary.branch -ne 'aggressive' -or
    $sourceBoundary.source_commit -notmatch '^[0-9a-f]{40}$') {
    throw 'Source-boundary resolver did not return a canonical aggressive tip'
}
$resolverPath = Join-Path $repo '.agents/skills/hmasd-dispatch-task/scripts/resolve_task_route.ps1'
$resolver = Get-Content -LiteralPath $resolverPath -Raw
foreach ($required in @("ValidateSet('controller', 'project_manager')", 'Unregistered Codex role',
    "if ([string]`$entry.registration_status -ne 'ACTIVE')", 'role = $Role')) {
    if (-not $resolver.Contains($required)) { throw "Role resolver missing: $required" }
}
if ($resolver.Contains("`$Role -ne 'controller'")) {
    throw 'Role resolver exempts Controller from ACTIVE-status validation'
}
if ($resolver.Contains('open_divergent_exchange')) { throw 'Role resolver retains retired Exchange route' }
foreach ($role in @('project_manager', 'controller')) {
    $liveRoute = & $resolverPath -Role $role | ConvertFrom-Json
    if ($liveRoute.threadId -ne $roles.roles.$role.thread_id -or
        [string]::IsNullOrWhiteSpace([string]$liveRoute.model) -or
        [string]::IsNullOrWhiteSpace([string]$liveRoute.thinking)) {
        throw "Live route does not expose the current target model/effort: $role"
    }
}
$inactiveRegistryPath = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-inactive-controller-$([Guid]::NewGuid().ToString('N')).json")
try {
    $inactiveRegistry = Get-Content -Raw -LiteralPath $rolesPath | ConvertFrom-Json
    $inactiveRegistry.roles.controller.registration_status = 'INACTIVE'
    $inactiveRegistry | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $inactiveRegistryPath -Encoding utf8
    try {
        & $resolverPath -Role controller -RegistryPath $inactiveRegistryPath | Out-Null
        throw 'Resolver unexpectedly accepted an inactive Controller'
    }
    catch {
        if ([string]$_ -notmatch 'Codex role is not ACTIVE: controller') {
            throw "Resolver failed closed for the wrong reason: $_"
        }
    }
}
finally {
    if (Test-Path -LiteralPath $inactiveRegistryPath) {
        Remove-Item -LiteralPath $inactiveRegistryPath -Force
    }
}
foreach ($forbidden in @('gpt-5.3-codex-spark', 'expected_target_model',
    'expected_target_effort', 'expected profile')) {
    if ($skill.Contains($forbidden) -or
        ($roles | ConvertTo-Json -Depth 10).Contains($forbidden)) {
        throw "Dispatcher retains a fixed target execution-profile expectation: $forbidden"
    }
}
$currentWork = Get-Content -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md') -Raw
if (-not $currentWork.Contains($roles.roles.project_manager.thread_id) -or
    -not $currentWork.Contains('No persistent Experiment Monitor task is active') -or
    -not $currentWork.Contains('Controller-direct external-Pro transport') -or
    -not $currentWork.Contains('callback_contract_activation=on_integration_commit') -or
    -not $currentWork.Contains('callback_receipt_requires_followup_commit=false')) {
    throw 'Current boundary does not name the active direct-transport topology'
}
if ($currentWork.Contains('callback_contract_repair_status=pm_accepted_pending_mechanical_integration')) {
    throw 'Current boundary creates a recursive post-integration status commit'
}
Write-Output 'HMASD_DISPATCH_TASK_CONTRACT_OK'
