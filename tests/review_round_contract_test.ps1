$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot

$router = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$cpm = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$explorer = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
$operator = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md')
$skill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-agentify-transport/SKILL.md')
$researchSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$preflightPath = Join-Path $repo '.agents/skills/hmasd-agentify-transport/scripts/ensure_agentify_runtime.ps1'

foreach ($entry in @(
    @($router, 'agentify_transport_request=AGENTIFY_REVIEW_REQUEST'),
    @($router, 'agentify_transport_request_fields=provider|question_path|return_task_id'),
    @($router, 'agentify_transport_result=AGENTIFY_REVIEW_RESULT'),
    @($router, 'agentify_transport_result_fields=status|response_path|error'),
    @($cpm, 'formal_review_transport=agentify_single_request_result'),
    @($explorer, 'independent_review_provider_contract=agentify_single_request_result'),
    @($operator, 'request_fields=provider|question_path|return_task_id'),
    @($operator, 'result_fields=status|response_path|error'),
    @($operator, 'terminal_status=COMPLETE|ERROR'),
    @($skill, 'promptPath=question_path'),
    @($skill, 'expectedModel=Pro'),
    @($skill, 'repeat the same `agentify_query` once'),
    @($skill, 'manifest, batch, identifier or archive merely to retry transport'),
    @($researchSkill, 'provider|question_path|return_task_id'),
    @($researchSkill, 'requires no Explorer file change')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Simple Agentify contract missing: $($entry[1])"
    }
}

if (-not (Test-Path -LiteralPath $preflightPath -PathType Leaf)) {
    throw 'Agentify runtime preflight script is missing'
}
$preflight = Get-Content -Raw -LiteralPath $preflightPath
foreach ($term in @('Get-Process', 'Start-Process', 'AGENTIFY_RUNTIME_READY')) {
    if (-not $preflight.Contains($term)) {
        throw "Agentify runtime preflight script missing: $term"
    }
}

$currentProcess = Get-Process -Id $PID
$probe = & $preflightPath `
    -ServiceProcessName $currentProcess.ProcessName `
    -BrowserProcessName $currentProcess.ProcessName `
    -ProbeOnly
if (($probe -join '') -notmatch 'AGENTIFY_RUNTIME_READY') {
    throw 'Agentify runtime preflight probe failed'
}

$active = $router + $cpm + $explorer + $operator + $skill + $researchSkill
foreach ($retired in @(
    'AGENTIFY_REVIEW_BATCH_REQUEST',
    'AGENTIFY_REVIEW_BATCH_RESULT',
    'batch_id|manifest_path|return_task_id',
    'request_id|review_channel|provider|expected_model|question_path',
    'stable_key',
    'SHA-256',
    'idempotency',
    'prepare -> submit -> verify -> archive',
    'submit --verify-existing'
)) {
    if ($active.Contains($retired)) {
        throw "Retired Agentify mechanism remains active: $retired"
    }
}

Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
