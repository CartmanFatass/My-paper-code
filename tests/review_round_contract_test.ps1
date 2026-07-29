[CmdletBinding()]
param([switch]$RoutingOnly)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$registry = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/external-review/REVIEWER_CONVERSATIONS.json') | ConvertFrom-Json
if ($registry.schema_version -ne 38 -or
    $registry.round_operator.kind -ne 'research_operations_manager_transport_mode' -or
    $registry.round_operator.external_scientific_decision -ne 'external_pro_binding_within_user_boundary' -or
    $registry.round_operator.decision_intake -ne 'same_task_exact_raw_routing' -or
    $registry.round_operator.git_boundary_owner -ne 'research_operations_manager' -or
    $registry.transport_contract.transport_owner -ne 'research_operations_manager' -or
    $registry.transport_contract.response_monitor_agent_type -ne 'hmasd-pro-response-monitor' -or
    $registry.transport_contract.response_monitor_model -ne 'gpt-5.6-luna' -or
    $registry.transport_contract.response_monitor_effort -ne 'low' -or
    $registry.transport_contract.response_monitor_observation -ne 'research_operations_manager_brokered_jsonl_sentinel' -or
    $registry.transport_contract.response_monitor_sentinel_tool -ne 'scripts/hmasd_pro_response_sentinel.py' -or
    $registry.reviewers.open_divergent.transport -ne 'research_operations_manager_in_app_browser') {
    throw 'Research Operations Manager transport registry mismatch'
}

$skillPath = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$skill = Get-Content -Raw -LiteralPath $skillPath
$operations = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/RESEARCH_OPERATIONS_MANAGER.md')
$skillNormalized = $skill -replace '\s+', ' '
$operationsNormalized = $operations -replace '\s+', ' '
$skillAgent = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/skills/hmasd-review-round/agents/openai.yaml')
foreach ($required in @(
    'Operations-manager transport mode',
    'DESIGN_ASSERTION_AUDIT',
    'CODE_SCIENCE_ALIGNMENT_AUDIT',
    'FORMAL_RESULT_SCIENTIFIC_DISPOSITION',
    'hmasd-pro-response-monitor',
    'operations-manager-brokered metadata sentinel',
    'monitor_assignment_token',
    'sole monitor assignment identity',
    '--assignment-token <exact-init-token>',
    'Do not parse, shorten or rebuild the token',
    'returns that exact fence identity',
    'scripts/hmasd_pro_response_sentinel.py record',
    'native child does not inherit',
    'in-app-browser',
    'ordinary task wakeups',
    'timer loop or emit pending progress messages',
    '$browser:control-in-app-browser',
    'VERIFY_FRESHNESS_FENCE',
    'RECOVER_UNPERSISTED_ASSIGNMENT',
    'POST_ERROR_PERSISTENCE_RECHECK',
    'USER_AUTHORIZED_ASSIGNMENT_SEND',
    'USER_AUTHORIZED_ASSIGNMENT_RESEND',
    'CORRECT_PREFIX_FENCE',
    'RETRY_RESPONSE_CONTRACT',
    'render_review_fence.ps1',
    'Full-hash prefix correction',
    'One response-contract retry',
    'rejected transport record',
    'no assistant response is visible',
    'no prior correction',
    'contains no scientific question body',
    'same pending review turn and registered conversation',
    'At most one monitor and sentinel generation may be live',
    'recovery consumes zero scientific iterations',
    'submission_attempt=2',
    'supersedes_submission_attempt=1',
    'Exactly one main-body or attachment-backed identity is verified',
    'Assignment identity evidence',
    'MAIN_BODY_IDENTITY_VERIFIED',
    'ATTACHMENT_IDENTITY_VERIFIED',
    'IDENTITY_UNREADABLE',
    'IDENTITY_MISMATCH',
    'verify_assignment_attachment_identity.py',
    'client_send_consumed=true|false',
    'main_body_fence_visible=true|false',
    'attachment_identity_verified=true|false',
    'assistant_generation_started=true|false',
    'natural_completion_verified=true|false',
    'complete canonical `sentinel_fence_identity`',
    'The attachment filename, icon, preview, ordinary file size',
    'never proves natural completion',
    'UNPERSISTED_CLIENT_SEND',
    'one fresh exact-URL reopen',
    'zero complete matching fences',
    'A same-tab reload alone is insufficient',
    'replay payload to equal the first complete payload byte-for-byte',
    'This automatic recovery grants no third Assignment client attempt',
    'REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT',
    'signed-in conversation search',
    'Do not send or render a message',
    'cannot repeat',
    'without a new send',
    'REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED',
    'One direct-user-authorized Assignment send',
    'The client action consumes the grant',
    'take one fresh readable snapshot only',
    'Do not reload, reopen',
    'grant cannot be inherited',
    'REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_RESEND_UNPERSISTED',
    'One direct-user-authorized Assignment resend',
    'USER_AUTHORIZED_ASSIGNMENT_RESEND_TERMINAL',
    'EXISTING_FENCE_ADOPTED|FENCE_ACCEPTED|UNPERSISTED|BLOCKED',
    'one local terminal operations callback',
    'Do not emit a pending callback',
    'cross-task completion relay',
    'attempt 1 is neither `USER_AUTHORIZED_ASSIGNMENT_SEND` nor `USER_AUTHORIZED_ASSIGNMENT_RESEND`',
    'ineligible for this correction',
    'the accepted attempt is neither `USER_AUTHORIZED_ASSIGNMENT_SEND` nor',
    'never submit attempt 3',
    'same tab once for that stuck episode',
    'Reloading never proves the matching fence absent and never authorizes submission',
    'a new observed stuck episode',
    'instead of a reload loop',
    'two stable snapshots',
    'at least three seconds',
    'Never activate `Answer now`',
    'its presence or absence is neutral',
    'Only Pro''s natural completion is admissible',
    'transport diagnostic',
    'materialize them from `stage_commit`',
    'not from the current working tree',
    'resume operations loop',
    'monitor terminal -> exact raw -> provenance intake -> monitor absence')) {
    if (-not $skillNormalized.Contains($required)) { throw "Review Skill missing: $required" }
}
foreach ($forbidden in @(
    'reload until',
    'refresh until',
    'reload proves the matching fence absent',
    'reload authorizes submission',
    'Never send a second fence.',
    'watch --state <absolute-jsonl> --conversation-id',
    'review_assignment_acceptance=server_visible_exact_fence_only',
    'review_client_send_effect=uncommitted_until_server_visible')) {
    if ($skillNormalized.Contains($forbidden)) {
        throw "Review Skill permits unsafe stuck-page recovery: $forbidden"
    }
}

$monitorRole = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.agents/roles/PRO_RESPONSE_MONITOR.md')
$monitorProfile = Get-Content -Raw -LiteralPath (
    Join-Path $repo '.codex/agents/hmasd-pro-response-monitor.toml')
foreach ($required in @(
    'monitor_assignment_token',
    '--assignment-token <exact-init-token>',
    'never parses, shortens or reconstructs',
    'exact identity decoded and verified from the assignment token')) {
    if (-not $monitorRole.Contains($required)) {
        throw "Pro-response monitor role missing opaque identity transport: $required"
    }
}
foreach ($required in @(
    'monitor_assignment_token',
    'Copy the token unchanged into `--assignment-token`',
    'never parse,',
    'exact Sentinel-verified fence identity')) {
    if (-not $monitorProfile.Contains($required)) {
        throw "Pro-response monitor profile missing opaque identity transport: $required"
    }
}
foreach ($required in @(
    'browser_stuck_page_recovery=same_tab_reload_once_per_observed_episode',
    'browser_reload_fence_effect=none',
    'review_fence_stage_commit=full_40_hex_only',
    'review_fence_prefix_correction=once_same_conversation_before_assistant_response',
    'review_fence_correction_question_resubmission=forbidden',
    'review_fence_monitor_concurrency=one_live',
    'review_assignment_acceptance=server_visible_main_body_or_verified_attachment_identity',
    'review_assignment_identity_sources=main_body_exact_fence|verified_attachment_payload',
    'review_assignment_attachment_validator=.agents/skills/hmasd-review-round/scripts/verify_assignment_attachment_identity.py',
    'review_assignment_attachment_filename_authority=none',
    'review_assignment_attachment_unreadable=IDENTITY_UNREADABLE',
    'review_assignment_observation_fields=client_send_consumed|main_body_fence_visible|attachment_identity_verified|assistant_generation_started|natural_completion_verified',
    'review_client_send_effect=uncommitted_until_assignment_identity_verified',
    'review_unpersisted_assignment_recovery=once_same_conversation_exact_assignment_replay',
    'review_unpersisted_assignment_recovery_eligible=reload_then_exact_url_reopen_both_show_zero_matching_fence',
    'review_unpersisted_assignment_recovery_prior_server_visible_count=zero',
    'review_unpersisted_assignment_recovery_client_send_limit=2_assignment_sends_total',
    'review_unpersisted_assignment_recovery_scientific_iteration_cost=zero',
    'review_post_error_persistence_recheck=once_observe_only_after_unpersisted_assignment_terminal',
    'review_post_error_persistence_recheck_send_authority=none',
    'review_post_error_persistence_recheck_observations=exact_url_history_plus_registered_conversation_search',
    'review_post_error_persistence_recheck_success=exactly_one_full_fence',
    'review_post_error_persistence_recheck_zero=REVIEW_TRANSPORT_CLOSED_UNPERSISTED_ASSIGNMENT',
    'review_post_error_persistence_recheck_uncertain=REVIEW_TRANSPORT_BLOCKED',
    'review_post_error_persistence_recheck_monitor_before_fence=forbidden',
    'review_post_error_persistence_recheck_scientific_iteration_cost=zero',
    'review_user_authorized_assignment_send=once_after_closed_unpersisted_assignment',
    'review_user_authorized_assignment_send_authority=direct_user_only',
    'review_user_authorized_assignment_send_package=reuse_exact_existing_package',
    'review_user_authorized_assignment_send_presend=exact_url_plus_registered_search_both_zero',
    'review_user_authorized_assignment_send_count=one',
    'review_user_authorized_assignment_send_postsend=one_snapshot_no_reload',
    'review_user_authorized_assignment_send_automatic_recovery=forbidden',
    'review_user_authorized_assignment_send_zero=REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_SEND_UNPERSISTED',
    'review_user_authorized_assignment_send_uncertain=REVIEW_TRANSPORT_BLOCKED',
    'review_user_authorized_assignment_send_monitor_before_fence=forbidden',
    'review_user_authorized_assignment_send_scientific_iteration_cost=zero',
    'review_user_authorized_assignment_resend=once_after_closed_user_authorized_send',
    'review_user_authorized_assignment_resend_authority=direct_user_only',
    'review_user_authorized_assignment_resend_package=reuse_exact_existing_package',
    'review_user_authorized_assignment_resend_presend=exact_url_plus_registered_search_both_zero',
    'review_user_authorized_assignment_resend_count=one',
    'review_user_authorized_assignment_resend_postsend=one_snapshot_no_reload',
    'review_user_authorized_assignment_resend_automatic_recovery=forbidden',
    'review_user_authorized_assignment_resend_zero=REVIEW_TRANSPORT_CLOSED_USER_AUTHORIZED_RESEND_UNPERSISTED',
    'review_user_authorized_assignment_resend_uncertain=REVIEW_TRANSPORT_BLOCKED',
    'review_user_authorized_assignment_resend_monitor_before_fence=forbidden',
    'review_user_authorized_assignment_resend_terminal_callback=one_local_ops_return',
    'review_user_authorized_assignment_resend_pending_callback=forbidden',
    'review_user_authorized_assignment_resend_scientific_iteration_cost=zero',
    'review_response_retry=once_same_conversation_after_terminal_attempt',
    'review_response_retry_eligible=format_nonconforming_or_no_response_after_exhausted_recovery',
    'review_response_retry_requires_server_visible_original_fence=true',
    'review_response_retry_unproven_persistence=forbidden',
    'review_response_retry_submission_limit=2_total',
    'review_response_retry_scientific_iteration_cost=zero',
    'rejected transport record',
    'Reloading never proves a freshness fence absent and never authorizes submission')) {
    if (-not $operationsNormalized.Contains($required)) {
        throw "Research Operations Manager role missing stuck-page recovery boundary: $required"
    }
}
if ($skill -match '(?i)\bcontroller\b|hmasd-dispatch-task|hmasd-experiment-monitor|fixed Project Manager session|completion notification') {
    throw 'Review Skill retains a retired relay or monitor surface'
}
foreach ($required in @(
    'hmasd-pro-response-monitor',
    'main body or its same-turn Pasted_text attachment',
    'IDENTITY_UNREADABLE rather than send failure',
    'Record client-send, main-body identity, attachment identity, generation-started and natural-completion facts independently',
    'exact 40-character stage commit',
    'strict stage-commit prefix',
    'UNPERSISTED_CLIENT_SEND',
    'one byte-exact complete-payload Assignment replay',
    'without resubmitting the scientific question',
    'One ResponseRetry',
    'uncertain persistence is ineligible',
    'there is no third submission',
    'Never activate Answer now',
    'operations-manager-brokered JSONL sentinel',
    'child never opens the browser',
    'resume the local operations loop')) {
    if (-not $skillAgent.Contains($required)) {
        throw "Review Skill agent prompt missing: $required"
    }
}

$renderer = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/render_review_fence.ps1'
if (-not (Test-Path -LiteralPath $renderer -PathType Leaf)) {
    throw 'Deterministic review-fence renderer is missing'
}
$attachmentValidator = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_assignment_attachment_identity.py'
if (-not (Test-Path -LiteralPath $attachmentValidator -PathType Leaf)) {
    throw 'Deterministic attachment-assignment identity validator is missing'
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

$assignmentReplay = (& $renderer `
    -Mode Assignment `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question) -replace "`r`n", "`n"
if ($assignmentReplay -cne $assignment) {
    throw 'Unpersisted Assignment replay was not byte-exact renderer output'
}

$userAuthorizedAssignment = (& $renderer `
    -Mode Assignment `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question) -replace "`r`n", "`n"
if ($userAuthorizedAssignment -cne $assignment) {
    throw 'User-authorized Assignment send did not reuse byte-exact renderer output'
}

$userAuthorizedResend = (& $renderer `
    -Mode Assignment `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question) -replace "`r`n", "`n"
if ($userAuthorizedResend -cne $assignment) {
    throw 'User-authorized Assignment resend did not reuse byte-exact renderer output'
}

$responseRetry = (& $renderer `
    -Mode ResponseRetry `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question `
    -RetryReason format_nonconforming) -replace "`r`n", "`n"
$retryPrefix = $assignment + "`n`n"
if (-not $responseRetry.StartsWith($retryPrefix, [StringComparison]::Ordinal)) {
    throw 'Response retry did not preserve the original Assignment as its exact prefix'
}
foreach ($required in @(
    'CURRENT_REVIEW_RESPONSE_RETRY',
    'submission_attempt=2',
    'supersedes_submission_attempt=1',
    'retry_reason=format_nonconforming',
    'RESPONSE_REQUIREMENTS',
    '1. Answer the unchanged question completely.',
    '2. Use every required heading, field, disposition token and section exactly as specified by the question.',
    '3. Do not omit a required item; if it cannot be determined, mark that item UNDETERMINED and state its blocker.',
    '4. Do not return only transport, status or acknowledgement text.')) {
    if (-not $responseRetry.Contains($required)) {
        throw "Response retry renderer missing: $required"
    }
}

$noResponseRetry = (& $renderer `
    -Mode ResponseRetry `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question `
    -RetryReason no_response_after_exhausted_recovery) -replace "`r`n", "`n"
if (-not $noResponseRetry.StartsWith($retryPrefix, [StringComparison]::Ordinal) -or
    -not $noResponseRetry.Contains('retry_reason=no_response_after_exhausted_recovery')) {
    throw 'No-response retry renderer did not preserve the bounded retry identity'
}

$missingRetryReasonRejected = $false
try {
    & $renderer `
        -Mode ResponseRetry `
        -Round $round `
        -StageCommit $fullCommit `
        -Question $question | Out-Null
} catch {
    $missingRetryReasonRejected = $_.Exception.Message.Contains('RetryReason is required')
}
if (-not $missingRetryReasonRejected) {
    throw 'Response retry renderer accepted a missing RetryReason'
}

$assignmentRetryParameterRejected = $false
try {
    & $renderer `
        -Mode Assignment `
        -Round $round `
        -StageCommit $fullCommit `
        -Question $question `
        -RetryReason format_nonconforming | Out-Null
} catch {
    $assignmentRetryParameterRejected = $_.Exception.Message.Contains('accepts no correction or retry parameters')
}
if (-not $assignmentRetryParameterRejected) {
    throw 'Assignment renderer accepted a response-retry parameter'
}

$responseRetryCorrectionParameterRejected = $false
try {
    & $renderer `
        -Mode ResponseRetry `
        -Round $round `
        -StageCommit $fullCommit `
        -Question $question `
        -RetryReason format_nonconforming `
        -SupersedesStageCommit $prefix | Out-Null
} catch {
    $responseRetryCorrectionParameterRejected = $_.Exception.Message.Contains('valid only in FullHashCorrection mode')
}
if (-not $responseRetryCorrectionParameterRejected) {
    throw 'Response retry renderer accepted a full-hash correction parameter'
}

$correctionRetryParameterRejected = $false
try {
    & $renderer `
        -Mode FullHashCorrection `
        -Round $round `
        -StageCommit $fullCommit `
        -Question $question `
        -SupersedesStageCommit $prefix `
        -RetryReason format_nonconforming | Out-Null
} catch {
    $correctionRetryParameterRejected = $_.Exception.Message.Contains('valid only in ResponseRetry mode')
}
if (-not $correctionRetryParameterRejected) {
    throw 'Full-hash correction renderer accepted a response-retry parameter'
}

$correction = (& $renderer `
    -Mode FullHashCorrection `
    -Round $round `
    -StageCommit $fullCommit `
    -Question $question `
    -SupersedesStageCommit $prefix) -replace "`r`n", "`n"
foreach ($required in @(
    'CURRENT_REVIEW_FENCE_CORRECTION',
    "supersedes_stage_commit=$prefix",
    "stage_commit=$fullCommit",
    'correction_scope=stage_commit_prefix_expansion_only; scientific question, evidence allow-list, and scientific instruction are unchanged and are not resubmitted.')) {
    if (-not $correction.Contains($required)) {
        throw "Full-hash correction renderer missing: $required"
    }
}
if ($correction -match '(?m)^stage_commit=13ac7eb$') {
    throw 'Correction renderer retained a shortened stage_commit field'
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

$unrelatedPrefixRejected = $false
try {
    & $renderer `
        -Mode FullHashCorrection `
        -Round $round `
        -StageCommit $fullCommit `
        -Question $question `
        -SupersedesStageCommit 'deadbee' | Out-Null
} catch {
    $unrelatedPrefixRejected = $_.Exception.Message.Contains('not a strict prefix')
}
if (-not $unrelatedPrefixRejected) {
    throw 'Correction renderer accepted an unrelated commit prefix'
}

$sentinel = Join-Path $repo 'scripts/hmasd_pro_response_sentinel.py'
if (-not (Test-Path -LiteralPath $sentinel -PathType Leaf)) {
    throw 'Pro-response sentinel harness is missing'
}

if (Test-Path -LiteralPath (Join-Path $repo '.agents/skills/hmasd-review-round/scripts/render_review_heartbeat.ps1')) {
    throw 'Retired PM heartbeat script remains'
}

if ($RoutingOnly) {
    Write-Output 'HMASD_REVIEW_ROUND_ROUTING_CONTRACT_OK'
    return
}

$boundaryVerifier = Join-Path $repo '.agents/skills/hmasd-review-round/scripts/verify_pro_review_boundary.ps1'
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
