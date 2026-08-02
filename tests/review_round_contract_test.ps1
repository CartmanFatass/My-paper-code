$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

$router = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$cpm = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$explorer = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$operator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md')
$transportSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agentify-transport/SKILL.md')
$runtimePreflightPath = Join-Path $repo '.agents/skills/hmasd-agentify-transport/scripts/ensure_agentify_runtime.ps1'
$researchSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$explorationSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/SKILL.md')

foreach ($entry in @(
    @($router, 'external_review_transport_execution=dedicated_agentify_transport_task'),
    @($router, 'agentify_transport_request=AGENTIFY_REVIEW_BATCH_REQUEST'),
    @($router, 'agentify_transport_manifest_item_fields=request_id|review_channel|provider|expected_model|question_path'),
    @($router, 'agentify_transport_prompt_source=agentify_direct_question_path_read'),
    @($router, 'agentify_transport_queue_semantics=ordered_persistent_conversation_stop_on_noncompletion'),
    @($router, 'agentify_transport_terminal_status=COMPLETE|ERROR'),
    @($router, 'agentify_transport_skill=hmasd-agentify-transport'),
    @($cpm, 'formal_review_transport=agentify_task_request_result'),
    @($cpm, 'AGENTIFY_REVIEW_BATCH_REQUEST'),
    @($explorer, 'independent_review_provider_contract=agentify_task_request_result'),
    @($explorer, 'AGENTIFY_REVIEW_BATCH_RESULT'),
    @($researchSkill, 'AGENTIFY_REVIEW_BATCH_REQUEST'),
    @($operator, 'agentify_transport_runtime_authority=exclusive'),
    @($operator, 'runtime_preflight_owner=agentify_transport_operator'),
    @($operator, 'runtime_preflight_execution=escalated_gui_process'),
    @($operator, 'runtime_setup_failure_route=workflow_design_manager_not_requester'),
    @($operator, 'batch_terminal_status=COMPLETE|ERROR'),
    @($operator, 'request_fields=batch_id|manifest_path|return_task_id'),
    @($operator, 'manifest_item_fields=request_id|review_channel|provider|expected_model|question_path'),
    @($transportSkill, 'timeoutMs=2700000'),
    @($transportSkill, 'BOOT -> PAGE -> SEND -> WAIT -> ARCHIVE -> COMPLETE'),
    @($transportSkill, '`COMPLETE` and `ERROR` are the only terminal states'),
    @($transportSkill, '`tab_not_found`'),
    @($transportSkill, 'proves the page/tab/controller was closed'),
    @($transportSkill, '`model_switcher_unavailable`'),
    @($transportSkill, 'the only retry'),
    @($transportSkill, 'call `agentify_wait_response` once with the same key'),
    @($transportSkill, 'That blocking call sends nothing'),
    @($operator, 'Batch status is `COMPLETE` only when'),
    @($operator, "provider's pinned protected page"),
    @($operator, 'otherwise `ERROR`'),
    @($transportSkill, 'Batch `COMPLETE` means every registered item succeeded'),
    @($transportSkill, '`agentify_status` once for the same pinned page key'),
    @($transportSkill, '`promptPath=question_path`'),
    @($transportSkill, 'Omit `prompt`'),
    @($transportSkill, 'shell stdout/stderr, receipts, warnings'),
    @($transportSkill, '`Pro thinking`, a timeout, an incomplete fragment'),
    @($transportSkill, 'stop the batch without'),
    @($operator, 'persistent ordered conversation, not a list of independent RPC calls'),
    @($transportSkill, 'Omit every optional content field'),
    @($transportSkill, '`expectedModel=expected_model`'),
    @($transportSkill, '`protectedTab=true`'),
    @($transportSkill, 'identity is not a requester field'),
    @($transportSkill, "internally uses Agentify's model selector"),
    @($operator, '`protectedTab=true`'),
    @($operator, 'does not implement another selector'),
    @($transportSkill, 'selects the exact target and'),
    @($transportSkill, 'A ChatGPT Pro item uses the exact visible label `Pro`'),
    @($transportSkill, 'ensure_agentify_runtime.ps1'),
    @($transportSkill, '`sandbox_permissions=require_escalated`'),
    @($transportSkill, 'Do not move it to `C:\tmp`'),
    @($transportSkill, 'is an Operator runtime defect, not an item result'),
    @($transportSkill, 'do not send a batch `ERROR` to the requester'),
    @($transportSkill, 'Never claim an action that no tool result proves')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Dedicated external-review contract missing: $($entry[1])"
    }
}

if (-not (Test-Path -LiteralPath $runtimePreflightPath -PathType Leaf)) {
    throw 'Agentify runtime preflight script is missing'
}
$runtimePreflight = Get-Content -Raw -LiteralPath $runtimePreflightPath
foreach ($requiredRuntimePreflightTerm in @(
    'Get-Process',
    'Start-Process',
    'AGENTIFY_RUNTIME_READY',
    'service_process_ids',
    'browser_process_ids',
    'AGENTIFY_DESKTOP_CHROME_PROFILE_MODE',
    "AGENTIFY_DESKTOP_CHROME_PROFILE_MODE = 'isolated'",
    'launched'
)) {
    if (-not $runtimePreflight.Contains($requiredRuntimePreflightTerm)) {
        throw "Agentify runtime preflight script missing: $requiredRuntimePreflightTerm"
    }
}

$currentProcess = Get-Process -Id $PID
$probeOutput = & $runtimePreflightPath `
    -ServiceProcessName $currentProcess.ProcessName `
    -BrowserProcessName $currentProcess.ProcessName `
    -ProbeOnly
if (($probeOutput -join '') -notmatch 'AGENTIFY_RUNTIME_READY') {
    throw "Agentify runtime preflight did not report an existing process: $($probeOutput -join ' ')"
}

$missingProbeFailed = $false
$missingProbeOutput = ''
try {
    & $runtimePreflightPath `
        -ServiceProcessName 'hmasd_missing_agentify_probe' `
        -BrowserProcessName $currentProcess.ProcessName `
        -ProbeOnly -ErrorAction Stop
} catch {
    $missingProbeFailed = $true
    $missingProbeOutput = $_.Exception.Message
}
if (-not $missingProbeFailed -or $missingProbeOutput -notmatch 'Agentify runtime is not running') {
    throw "Agentify runtime preflight accepted a missing process: $($missingProbeOutput -join ' ')"
}

foreach ($retired in @(
    '.agents/skills/hmasd-agentify-pro-transport',
    'docs/project/AGENTIFY_PRO_TRANSPORT.md',
    'docs/session-workspaces/code_project_manager/PRO_REVIEW_TRANSPORT.md',
    'docs/session-workspaces/independent_research_explorer/PRO_REVIEW_TRANSPORT.md',
    'tests/hmasd_agentify_pro_transport_test.py'
)) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Retired Agentify control-plane surface remains: $retired"
    }
}

$active = $router + $cpm + $explorer + $operator + $transportSkill + $researchSkill + $explorationSkill
if ($active.Contains('stable_key')) {
    throw 'Retired cross-session Agentify stable_key identity remains active'
}
foreach ($retiredTerm in @(
    'external_review_transport=owning_session_direct_agentify_call',
    'direct_agentify_call',
    'persistent_explorer_session_direct',
    'prepare -> submit -> verify -> archive',
    'submit --verify-existing',
    '--allow-tab-creation',
    'PRE_SEND_BLOCKED',
    'POST_SEND_BLOCKED',
    'MESSAGE_CONFIRMED',
    'STABLE_COMPLETE'
)) {
    if ($active.Contains($retiredTerm)) {
        throw "Retired Agentify control-plane term remains active: $retiredTerm"
    }
}

foreach ($forbidden in @('SHA-256', 'idempotency')) {
    if ($transportSkill.Contains($forbidden)) {
        throw "Agentify transport Skill retains a strict transport mechanism: $forbidden"
    }
}

foreach ($retiredSingleItemContract in @('AGENTIFY_REVIEW_REQUEST', 'AGENTIFY_REVIEW_RESULT')) {
    if ($active.Contains($retiredSingleItemContract)) {
        throw "Retired single-item transport contract remains active: $retiredSingleItemContract"
    }
}

Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
