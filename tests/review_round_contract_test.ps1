$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

$router = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$cpm = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$explorer = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$operator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md')
$transportSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agentify-transport/SKILL.md')
$researchSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$explorationSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/SKILL.md')

foreach ($entry in @(
    @($router, 'external_review_transport_execution=dedicated_agentify_transport_task'),
    @($router, 'agentify_transport_request=AGENTIFY_REVIEW_BATCH_REQUEST'),
    @($router, 'agentify_transport_manifest_item_fields=request_id|review_channel|provider|expected_model|stable_key|question_path'),
    @($router, 'agentify_transport_terminal_status=COMPLETE|ERROR'),
    @($router, 'agentify_transport_skill=hmasd-agentify-transport'),
    @($cpm, 'formal_review_transport=agentify_task_request_result'),
    @($cpm, 'AGENTIFY_REVIEW_BATCH_REQUEST'),
    @($explorer, 'independent_review_provider_contract=agentify_task_request_result'),
    @($explorer, 'AGENTIFY_REVIEW_BATCH_RESULT'),
    @($researchSkill, 'AGENTIFY_REVIEW_BATCH_REQUEST'),
    @($operator, 'agentify_transport_runtime_authority=exclusive'),
    @($operator, 'batch_terminal_status=COMPLETE|ERROR'),
    @($operator, 'request_fields=batch_id|manifest_path|return_task_id'),
    @($operator, 'manifest_item_fields=request_id|review_channel|provider|expected_model|stable_key|question_path'),
    @($transportSkill, 'timeoutMs=2700000'),
    @($transportSkill, 'Never call `agentify_query` twice for one item'),
    @($transportSkill, 'call `agentify_wait_response` once with the same key'),
    @($transportSkill, 'That blocking call sends nothing'),
    @($operator, 'Batch status is `COMPLETE` only when'),
    @($operator, 'otherwise `ERROR`'),
    @($transportSkill, 'Batch `COMPLETE` means every registered item succeeded'),
    @($transportSkill, '`agentify_status` once for the same key'),
    @($transportSkill, 'key unavailable for the remainder of the batch'),
    @($transportSkill, 'items on other keys may'),
    @($transportSkill, 'Omit every optional content field'),
    @($transportSkill, '`expectedModel=expected_model`'),
    @($transportSkill, 'selects the exact target and'),
    @($transportSkill, 'A ChatGPT Pro item uses `GPT-5.6 Pro`'),
    @($transportSkill, 'Never claim an action that no tool result proves')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Dedicated external-review contract missing: $($entry[1])"
    }
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
