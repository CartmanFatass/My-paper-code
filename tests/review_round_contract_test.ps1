[CmdletBinding()]
param([switch]$RoutingOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$cpm = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/CODE_PROJECT_MANAGER.md')
$explorer = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md')
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
$explorerNormalized = $explorer -replace '\s+', ' '

foreach ($entry in @(
    @($cpm, 'prepare -> submit -> verify -> archive -> local_FIFO_intake'), @($cpm, 'transport_owner=code_project_manager'), @($explorer, 'persistent_explorer_session_direct'), @($explorer, 'hmasd-independent-research-explorer-pro'), @($explorer, 'hmasd-independent-research-explorer-gemini'), @($independentSkill, '$hmasd-agentify-pro-transport'), @($agentifySkillNormalized, 'provider=chatgpt|gemini'), @($agentifySkillNormalized, 'standalone `RAW_QUESTION`'), @($agentifySkillNormalized, '`present=false`'), @($agentifySkillNormalized, 'first ChatGPT binding'), @($agentifyContractNormalized, 'transport_tab_mutation=forbidden_except_first_chatgpt_binding_or_post_restart_reopen'), @($agentifyContractNormalized, 'missing_or_mismatched_tab=fail_before_review_query'), @($agentifyContractNormalized, 'stable_key_tab_policy=one_live_tab_per_stable_key'), @($agentifyScript, 'AGENTIFY_REQUIRED_COMMIT = "e9f636740bf94d7db260c8817554904cdcb68870"'), @($agentifyScript, 'HMASD_AGENTIFY_EXISTING_USER_MESSAGE'))
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
foreach ($entry in @(
    @(($cpm -replace '\s+', ' '), 'does not spawn a transport or monitor child'),
    @(($explorer -replace '\s+', ' '), 'never spawns a review/monitor child or heartbeat'),
    @($agentifySkillNormalized, 'authenticated `/tabs` and scoped `/status` must show one exact, idle, unblocked and prompt-visible page'),
    @($agentifySkillNormalized, 'strict `/review-query`'),
    @($agentifyContractNormalized, 'transport_tab_mutation=forbidden'),
    @($agentifyContractNormalized, 'missing_or_mismatched_tab=fail_before_review_query'),
    @($agentifyContractNormalized, 'prompt_visible_required_before_send=true'),
    @($agentifyScript, 'require_send_ready=require_send_ready'),
    @($agentifyScript, 'agentify_preexisting_tab_missing'),
    @($agentifyScript, 'agentify_preexisting_tab_busy'),
    @($agentifyScript, 'agentify_preexisting_tab_prompt_unavailable'),
    @($agentifyScript, 'MESSAGE_CONFIRMED'),
    @($agentifyScript, 'PRE_SEND_BLOCKED'),
    @($agentifyScript, 'POST_SEND_BLOCKED'),
    @($agentifyScript, 'sendActionCount'),
    @($agentifyScript, '_terminate_owned_worker')
)) {
    if (-not $entry[0].Contains($entry[1])) {
        throw "Existing-tab-only Agentify contract missing: $($entry[1])"
    }
}
$tabPreflightCall = $agentifyScript.IndexOf('tab_id = _require_preexisting_review_tab(')
$reviewQueryCall = $agentifyScript.IndexOf('f"{base}/review-query"')
if ($tabPreflightCall -lt 0 -or $reviewQueryCall -lt 0 -or $tabPreflightCall -ge $reviewQueryCall) {
    throw 'Existing-tab proof does not precede Agentify review-query'
}
foreach ($forbiddenEndpoint in @('/tabs/close', '/tabs/show', '/tabs/activate', '/navigate', '/refresh', '/replace', '/rebind')) {
    if ($agentifyScript.Contains($forbiddenEndpoint)) {
        throw "HMASD Agentify wrapper mutates page state: $forbiddenEndpoint"
    }
}
foreach ($required in @(
    'independent_pro_review_transport_authority=exclusive_for_explorer_direction_and_methodology_reviews',
    'independent_pro_review_transport_execution=persistent_explorer_session_direct',
    'independent_pro_review_terminal_intake=exact_archived_response_fifo',
    'never spawns a review/monitor child or heartbeat',
    'submit --verify-existing` returns `present=false`',
    'archives the exact response under its assigned')) {
    if (-not $explorerNormalized.Contains($required)) {
        throw "Direct Explorer transport boundary missing: $required"
    }
}
foreach ($required in @('/tabs/create', 'allow_tab_creation', 'agentify_tab_creation_requires_first_binding_or_restart_recovery')) {
    if (-not $agentifyScript.Contains($required)) {
        throw "Restricted tab-creation recovery missing: $required"
    }
}
if ($agentifyScript.Contains('"prompt_sha256"')) {
    throw 'Agentify wrapper must not use prompt_sha256 as a request or recovery gate'
}
foreach ($forbiddenWorkflowHashField in @('hashlib', 'SHA256_RE', 'requestFingerprint', 'responseSha256', 'textSha256', '_sha256')) {
    if ($agentifyScript.Contains($forbiddenWorkflowHashField)) {
        throw "Agentify wrapper retains forbidden workflow hash field/helper: $forbiddenWorkflowHashField"
    }
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
