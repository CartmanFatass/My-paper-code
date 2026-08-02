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
    @($router, 'agentify_transport_terminal_status=COMPLETE|ERROR'),
    @($router, 'agentify_transport_skill=hmasd-agentify-transport'),
    @($cpm, 'formal_review_transport=agentify_task_request_result'),
    @($cpm, 'AGENTIFY_REVIEW_REQUEST'),
    @($explorer, 'independent_review_provider_contract=agentify_task_request_result'),
    @($explorer, 'AGENTIFY_REVIEW_RESULT'),
    @($researchSkill, 'Send one `AGENTIFY_REVIEW_REQUEST`'),
    @($operator, 'agentify_transport_runtime_authority=exclusive'),
    @($operator, 'terminal_status=COMPLETE|ERROR'),
    @($operator, 'request_fields=request_id|review_channel|provider|stable_key|question_path|return_task_id'),
    @($transportSkill, 'Call `agentify_query` once'),
    @($transportSkill, 'timeoutMs=2700000'),
    @($transportSkill, 'Never call `agentify_query` twice for one request'),
    @($transportSkill, 'observe that page until natural completion without sending'),
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

Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
