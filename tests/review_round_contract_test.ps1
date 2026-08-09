$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

function Read-RepoFile([string] $relativePath) {
    $path = Join-Path $repo $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required Agentify contract file is missing: $relativePath"
    }
    return Get-Content -Raw -LiteralPath $path
}

function Require-ContractTerm([string] $content, [string] $term, [string] $surface) {
    if (-not $content.Contains($term)) {
        throw "Agentify contract missing on $surface`: $term"
    }
}

$router = Read-RepoFile 'AGENTS.md'
$config = Read-RepoFile '.codex/config.toml'
$profile = Read-RepoFile '.codex/agents/hmasd-agentify-transport.toml'
$operator = Read-RepoFile '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md'
$skill = Read-RepoFile '.agents/skills/hmasd-agentify-transport/SKILL.md'
$operatorNormalized = $operator -replace '\s+', ' '
$skillNormalized = $skill -replace '\s+', ' '
$workflowMap = Read-RepoFile 'docs/project/WORKFLOW_MAP.md'
$workspaceContract = Read-RepoFile 'docs/project/SESSION_WORKSPACE_CONTRACT.md'
$workspaceReadme = Read-RepoFile 'docs/session-workspaces/agentify_transport_operator/README.md'
$auditGuide = Read-RepoFile 'docs/session-workspaces/workflow_design_manager/CLAUDE_WORKFLOW_AUDIT_GUIDE.md'

# The two requester roles are intentionally read-only inputs to this focused
# transport contract check; they are owned by CPM/Explorer implementers.
$cpm = Read-RepoFile '.agents/roles/CODE_PROJECT_MANAGER.md'
$explorer = Read-RepoFile '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md'
$researchSkill = Read-RepoFile '.agents/skills/hmasd-independent-research-pro-review/SKILL.md'

$contractSurfaces = @{
    router = $router
    config = $config
    profile = $profile
    operator = $operator
    skill = $skill
    workflowMap = $workflowMap
    workspaceContract = $workspaceContract
    workspaceReadme = $workspaceReadme
    auditGuide = $auditGuide
    cpm = $cpm
    explorer = $explorer
    researchSkill = $researchSkill
}

$childTokenSurfaces = @{
    router = $router
    operator = $operator
    skill = $skill
    cpm = $cpm
    explorer = $explorer
}
foreach ($surface in $childTokenSurfaces.GetEnumerator()) {
    Require-ContractTerm $surface.Value 'agentify_transport_child=hmasd-agentify-transport' $surface.Key
}

foreach ($term in @(
    'agentify_transport_child_parent=code_project_manager|independent_research_explorer',
    'agentify_transport_test_parent=workflow_design_manager',
    'agentify_transport_wdm_test_scope=exact_workflow_acceptance_smoke_batch_only',
    'agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT',
    'agentify_transport_assignment_fields=batch_path|results_path',
    'agentify_transport_batch_file_fields=provider|context_path|question_paths',
    'agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT',
    'agentify_transport_result_fields=status|results_path|error',
    'agentify_transport_terminal_status=COMPLETE|ERROR',
    'agentify_transport_wait_visibility=silent_until_terminal_native_final'
)) {
    Require-ContractTerm $operatorNormalized $term 'AGENTIFY_TRANSPORT_OPERATOR.md'
}
foreach ($term in @(
    'agentify_transport_child=hmasd-agentify-transport',
    'agentify_transport_child_parent=code_project_manager|independent_research_explorer',
    'agentify_transport_test_parent=workflow_design_manager'
)) {
    Require-ContractTerm $router $term 'AGENTS.md'
}
foreach ($term in @(
    'agentify_transport_workspace=temp/sessions/agentify_transport_operator/',
    'agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT',
    'agentify_transport_assignment_locators=batch_path|results_path',
    'agentify_transport_batch_locators=context_path|question_paths',
    'agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT',
    'agentify_transport_result_locator=results_path'
)) {
    Require-ContractTerm $workspaceContract $term 'SESSION_WORKSPACE_CONTRACT.md'
}
foreach ($term in @(
    'requester-owned context brief is the semantic task input',
    'verify its observed URL/ID before binding each send and answer to it',
    'close only tabs created by this task'
)) {
    Require-ContractTerm $operatorNormalized $term 'AGENTIFY_TRANSPORT_OPERATOR.md'
}

foreach ($term in @(
    '[agents."HMASDAgentifyTransport"]',
    'config_file = "./agents/hmasd-agentify-transport.toml"'
)) {
    Require-ContractTerm $config $term '.codex/config.toml'
}
foreach ($term in @(
    'model = "gpt-5.6-luna"',
    'model_reasoning_effort = "medium"',
    'sandbox_mode = "danger-full-access"',
    'approval_policy = "never"',
    '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md',
    '.agents/skills/hmasd-agentify-transport/SKILL.md',
    'AGENTIFY_REVIEW_BATCH_RESULT',
    'silent until COMPLETE or ERROR'
)) {
    Require-ContractTerm $profile $term 'hmasd-agentify-transport.toml'
}

foreach ($term in @(
    'runtime_process_receipt=AGENTIFY_RUNTIME_PROCESS_READY',
    'IN_PROGRESS',
    'exactly once',
    'silent',
    'current composer model',
    'open the model picker',
    'select Pro',
    'composer visibly shows Pro after the action',
    'expectedModel=Pro',
    'tool `COMPLETE` token',
    'provider-home URL',
    'partial response fragment',
    'natural-language conclusion',
    'question_path',
    'conversation_url',
    'model_evidence',
    'natural-language answer'
)) {
    Require-ContractTerm $operator $term 'AGENTIFY_TRANSPORT_OPERATOR.md'
}
foreach ($term in @(
    'agentify_query',
    'context_path',
    'expectedModel=Pro',
    'current composer model',
    'open the model picker',
    'select Pro',
    'composer visibly',
    'status=COMPLETE',
    'A tool',
    'response fragment',
    'modelEvidence=Pro',
    'https://chatgpt.com/c/<id>',
    'IN_PROGRESS',
    'one ordered row per question',
    'at most one suitable page/session recovery',
    'exactly once',
    'silent',
    'question_path',
    'conversation_url',
    'model_evidence',
    'Treat tool state as page evidence'
)) {
    Require-ContractTerm $skill $term 'hmasd-agentify-transport Skill'
}
foreach ($term in @(
    'hmasd-agentify-transport',
    'batch_path',
    'context_path',
    'results_path',
    'wait silently',
    'one native terminal result',
    'question_path',
    'conversation_url'
)) {
    Require-ContractTerm $workspaceReadme $term 'agentify transport workspace README'
}

$preflightPath = Join-Path $repo '.agents/skills/hmasd-agentify-transport/scripts/ensure_agentify_runtime.ps1'
if (-not (Test-Path -LiteralPath $preflightPath -PathType Leaf)) {
    throw 'Agentify runtime preflight script is missing'
}
$preflight = Get-Content -Raw -LiteralPath $preflightPath
foreach ($term in @(
    'Get-Process',
    'Start-Process',
    'AGENTIFY_RUNTIME_PROCESS_READY',
    'process_presence_only_use_scoped_agentify_status_for_runtime_readiness'
)) {
    Require-ContractTerm $preflight $term 'ensure_agentify_runtime.ps1'
}

$probeRejected = $false
try {
    & $preflightPath `
        -ServiceProcessName 'hmasd-agentify-nonexistent-service' `
        -BrowserProcessName 'hmasd-agentify-nonexistent-browser' `
        -ProbeOnly | Out-Null
} catch {
    $probeRejected = $_.Exception.Message -match 'Agentify runtime is not running'
}
if (-not $probeRejected) {
    throw 'Agentify process preflight did not reject absent processes'
}

# The parent owns conversation meaning. Transport observes identity, realizes
# the explicit brief and cleans only its task-owned idle tabs.
foreach ($entry in @(
    @($operatorNormalized, 'The requester-owned context brief is the semantic task input'),
    @($operatorNormalized, 'it does not infer scientific direction, review independence, contamination risk, future reuse or grouping'),
    @($operatorNormalized, 'Questions may finish out of order, but result rows remain in the original `question_paths` order.'),
    @($skillNormalized, 'Requester-authorized independent conversations may perform these steps concurrently on separate owned tabs'),
    @($skillNormalized, 'Never close the default tab, a pre-existing/unowned tab, or a tab with an active answer.'),
    @($skillNormalized, 'never guess or silently substitute another conversation')
)) {
    Require-ContractTerm $entry[0] $entry[1] 'Agentify conversation authority/lifecycle'
}

# The old top-level/cross-task contract must not remain active anywhere in the
# requester, child, router or transport surfaces.
$active = ($contractSurfaces.Values -join "`n")
foreach ($retired in @(
    'AGENTIFY_REVIEW_BATCH_REQUEST',
    'AGENTIFY_REVIEW_REQUEST',
    'AGENTIFY_REVIEW_RESULT',
    'return_task_id',
    'dedicated-task',
    'dedicated top-level',
    'batch_id|manifest_path|return_task_id',
    'request_id|review_channel|provider|expected_model|question_path',
    'stable_key',
    'SHA-256',
    'idempotency',
    'prepare -> submit -> verify -> archive',
    'submit --verify-existing',
    'BOOT -> PAGE',
    'protectedTab=true',
    'Do not create another page',
    'switch conversations, send a placeholder'
)) {
    if ($active.Contains($retired)) {
        throw "Retired Agentify mechanism remains active: $retired"
    }
}

Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
