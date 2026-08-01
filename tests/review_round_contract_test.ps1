[CmdletBinding()]
param([switch]$RoutingOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$operations = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md')
$independentOperator = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md')
$independentSkill = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/skills/hmasd-independent-research-pro-review/SKILL.md')
$agentifySkillPath = Join-Path $repo '.agents/skills/hmasd-agentify-pro-transport/SKILL.md'
$agentifyScriptPath = Join-Path $repo '.agents/skills/hmasd-agentify-pro-transport/scripts/hmasd_agentify_pro_transport.py'
$agentifyContractPath = Join-Path $repo 'docs/project/AGENTIFY_PRO_TRANSPORT.md'
foreach ($path in @($agentifySkillPath, $agentifyScriptPath, $agentifyContractPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Agentify transport surface is missing: $path"
    }
}
$agentifySkill = Get-Content -Raw -LiteralPath $agentifySkillPath
$agentifyScript = Get-Content -Raw -LiteralPath $agentifyScriptPath
$agentifyContract = Get-Content -Raw -LiteralPath $agentifyContractPath
$agentifySkillNormalized = $agentifySkill -replace '\s+', ' '
$agentifyContractNormalized = $agentifyContract -replace '\s+', ' '

foreach ($entry in @(
    @($operations, 'review_transport_recovery_rule=.agents/skills/hmasd-agentify-pro-transport/SKILL.md#minimal-recovery'), @($independentSkill, '$hmasd-agentify-pro-transport'), @($agentifySkillNormalized, 'Active generation or a readable complete response always suppresses another send'), @($agentifySkillNormalized, 'client submission limit is three per assignment'), @($agentifySkillNormalized, 'existing immutable request records'), @($agentifySkillNormalized, 'adds no hash, ledger or validator gate'), @($agentifySkillNormalized, 'Ordinary recovery never launches a synthetic smoke'), @($agentifySkillNormalized, 'duplicate submission of the same operation'), @($agentifyContractNormalized, 'agentify_required_commit=read_AGENTIFY_REQUIRED_COMMIT_from_wrapper'), @($agentifyContractNormalized, 'browser_backend=chrome-cdp'), @($agentifyContractNormalized, 'browser_window_policy=one_agentify_process_one_chrome_window'), @($agentifyContractNormalized, 'stable_key_tab_policy=one_live_tab_per_stable_key'), @($agentifyScript, 'AGENTIFY_REQUIRED_COMMIT = "d82e0ad377cd5ba8bdc484b7531a8b68cc92a8d7"'), @($agentifyScript, 'HMASD_AGENTIFY_EXISTING_USER_MESSAGE'))
) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Agentify transport contract missing: $($entry[1])"
    }
}
foreach ($staleGate in @('resend requires a new user instruction', 'only no recorded user message permits')) {
    if ($agentifySkillNormalized.Contains($staleGate)) {
        throw "Agentify transport retains a per-resend user gate: $staleGate"
    }
}
if ($agentifyScript.Contains('"prompt_sha256"')) {
    throw 'Agentify wrapper must not use prompt_sha256 as a request or recovery gate'
}

$renderer = Join-Path $repo '.agents/skills/hmasd-agentify-pro-transport/scripts/render_review_fence.ps1'
if (-not (Test-Path -LiteralPath $renderer -PathType Leaf)) {
    throw 'Deterministic review-fence renderer is missing'
}
$round = '20260727_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43_formal_result_review'
$fullCommit = '13ac7eb0eb1adac63a83e55754f7e516d2f40c5b'
$prefix = '13ac7eb'
$question = '20_PRO_OPEN_QUESTION.md'
$assignment = (& $renderer `
    -Mode Assignment `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question) -replace "`r`n", "`n"
$expectedAssignment = @(
    'CURRENT_REVIEW_ASSIGNMENT'
    'repository=CartmanFatass/My-paper-code'
    'branch=aggressive'
    "round=$round"
    "stage_commit=$fullCommit"
    "question=$question"
    'instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.'
) -join "`n"
if ($assignment -cne $expectedAssignment) {
    throw 'Assignment renderer did not preserve the exact full-hash identity'
}
$shortAssignmentRejected = $false
try {
    & $renderer -Mode Assignment -Round $round -StageCommit $prefix -Question $question | Out-Null
} catch {
    $shortAssignmentRejected = $_.Exception.Message.Contains('exactly 40 lowercase hexadecimal')
}
if (-not $shortAssignmentRejected) {
    throw 'Assignment renderer accepted a shortened stage commit'
}

if ($RoutingOnly) {
    Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
    return
}

$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-agentify-pro-transport/scripts/verify_pro_review_boundary.ps1'
$head = (& git.exe -C $repo rev-parse HEAD).Trim()
$boundary = & $boundaryVerifier `
    -Commit $head `
    -QuestionPath 'docs/external-review/rounds/20260725_uav_localized_demand_burst_g33_design_assertion_audit/20_PRO_OPEN_QUESTION.md' `
    -Remote $repo `
    -Branch 'aggressive' `
    -RepoRoot $repo | ConvertFrom-Json
if ($boundary.status -ne 'REMOTE_EVIDENCE_READY' -or
    $boundary.commit -ne $head -or
    @($boundary.inspected_paths).Count -ne 20 -or
    @($boundary.inspected_paths) -notcontains 'config_1.py' -or
    @($boundary.inspected_paths) -notcontains 'envs/pettingzoo/scenario7_energy_aware.py') {
    throw 'Review boundary verifier failed a reachable exact commit'
}

Write-Output 'HMASD_REVIEW_ROUND_CONTRACT_OK'
