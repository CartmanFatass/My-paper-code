$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

$router = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$cpm = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$explorer = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$researchSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$explorationSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-exploration/SKILL.md')

foreach ($entry in @(
    @($router, 'external_review_transport=owning_session_direct_agentify_call'),
    @($router, 'HMASD adds no transport control plane'),
    @($cpm, 'formal_review_transport=direct_agentify_call'),
    @($cpm, 'invokes Agentify directly'),
    @($explorer, 'independent_review_provider_contract=direct_agentify_call'),
    @($explorer, 'calls Agentify directly'),
    @($researchSkill, 'Invoke Agentify directly'),
    @($researchSkill, 'Never interrupt an active generation')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Direct external-review contract missing: $($entry[1])"
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

$active = $router + $cpm + $explorer + $researchSkill + $explorationSkill
foreach ($retiredTerm in @(
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

Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
