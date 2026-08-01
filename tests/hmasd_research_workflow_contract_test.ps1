[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

# Stable workflow surfaces only. Scientific assignments and result labels are
# deliberately not hard-coded here because CURRENT_WORK is the active line.
# Project Skills live under .claude/skills/ so Claude Code resolves them. Only
# the hmasd-* namespace is project workflow; third-party packs are ignored here.
$skills = @(Get-ChildItem (Join-Path $repo '.claude/skills') -Directory -Filter 'hmasd-*' |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedSkills = @(
    'hmasd-acceptance-gate',
    'hmasd-review-round',
    'hmasd-task-design',
    'hmasd-workflow-change-audit') | Sort-Object
if (Compare-Object $expectedSkills $skills) {
    throw "Unexpected active Skill set: $($skills -join ',')"
}

# Every bounded role is a Claude Code subagent definition.
$agentDefs = @(Get-ChildItem (Join-Path $repo '.claude/agents') -File -Filter 'hmasd-*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedAgents = @(
    'hmasd-code-scout.md', 'hmasd-doc-auditor.md',
    'hmasd-exp-recorder.md', 'hmasd-experiment-operator.md',
    'hmasd-guard-sweeper.md',
    'hmasd-implementer.md', 'hmasd-monitor.md',
    'hmasd-patcher.md', 'hmasd-review-monitor.md', 'hmasd-reviewer.md',
    'hmasd-scout.md', 'hmasd-verifier.md') | Sort-Object
if (Compare-Object $expectedAgents $agentDefs) {
    throw "Unexpected subagent roster: $($agentDefs -join ',')"
}

# The tier comparison is suspended and hmasd-frontier-implementer is retired
# (docs/project/IMPLEMENTER_TIER_TEST.md). The body-parity assertion that guarded
# it was removed together with the arm it guarded: it resolved the deleted file,
# so leaving it would turn a passing gate into a hard failure. If the tier
# experiment is ever reactivated, restore the arm and the assertion in one change.
if (Test-Path (Join-Path $repo '.codex')) {
    throw 'The retired Codex agent runtime remains on the active line'
}

# There is no role directory. One document per actor: AGENTS.md is the Project
# Manager's instructions, each subagent carries its own definition, and External
# Pro reads only the question it was sent.
if (Test-Path (Join-Path $repo '.agents')) {
    throw 'The retired .agents/ role directory is back'
}

# Every agent the dispatch table names must exist. A table row pointing at a
# deleted agent_type is a blocker the orchestrator only discovers at dispatch --
# it survived one session after the griller was retired.
$agentsRaw = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$tableAgents = [regex]::Matches($agentsRaw, '`(hmasd-[a-z-]+)`') |
    ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
foreach ($named in $tableAgents) {
    if (-not (Test-Path (Join-Path $repo ".claude/agents/$named.md")) -and
        -not (Test-Path (Join-Path $repo ".claude/skills/$named/SKILL.md"))) {
        throw "AGENTS.md names a subagent or Skill that does not exist: $named"
    }
}

$agents = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')
$current = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/CURRENT_WORK.md')
$context = Get-Content -Raw -LiteralPath (Join-Path $repo 'docs/project/AGENT_CONTEXT.md')
$pmRole = Get-Content -Raw -LiteralPath (Join-Path $repo 'AGENTS.md')

# key=value lines only (charter: contract_test_assertion_target). The prose
# assertions this list once carried duplicated properties these keys already
# state, and two of them pinned exact markdown wording -- every rewording
# became a test edit, and deleted-content assertions protected dead text.
# The no-persistent-roles property keeps its one assertion site in
# hmasd_experiment_operator_contract_test.ps1 against CURRENT_WORK.
foreach ($required in @(
    'project_manager_git_authority=direct',
    'project_manager_external_review_transport=project_manager_direct',
    'scientific_decision_authority=external_pro',
    'local_conversation_scientific_authority=none',
    'project_manager_experiment_orchestration=direct_via_registered_child',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'iteration_report_language=zh-CN',
    'iteration_report_path=docs/report/ITERATION_<n>.md',
    'per_file_hash_handoff=forbidden',
    'same_file_concurrent_writes=forbidden',
    # User ruling 2026-07-30: zero scientific decision rights; touchpoint 2 is
    # a conformance question, never a proposal.
    'scientific_proposal_authority=none',
    'pro_plan_review_question=conformance_to_pro_decision')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
}

# Every Skill must stay routed from AGENTS.md, or a Skill nobody is told to
# load is a Skill nobody loads. Content assertions are key=value only
# (charter): the prose-fragment lists this block once carried pinned Skill
# wording sentence-by-sentence, so every compression became a test edit. The
# one Skill with a fence is asserted on its load-bearing keys.
foreach ($pointer in $expectedSkills) {
    if (-not $agents.Contains("`$$pointer")) {
        throw "AGENTS.md no longer routes to the Skill it moved procedure into: $pointer"
    }
}
$charterSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.claude/skills/hmasd-workflow-change-audit/SKILL.md')
foreach ($required in @(
    # Design charter (2026-08-01): four load-bearing keys assert the fence
    # exists; the full 17-key fence lives only in the SKILL.
    'single_mechanism_line_budget=100',
    'incident_promotion_threshold=2',
    'sha256_whitelist=review_round_archive_integrity_only',
    'contract_test_assertion_target=key_value_fences_only')) {
    if (-not $charterSkill.Contains($required)) { throw "Design charter missing: $required" }
}

# Convergence must stay distinguishable from a fence, or the single-fence rule
# quietly becomes "resubmit whenever the answer is unsatisfying".
$reviewSkill = Get-Content -Raw -LiteralPath (Join-Path $repo '.claude/skills/hmasd-review-round/SKILL.md')
foreach ($required in @(
    '## Convergence turns',
    'A convergence turn is not a fence',
    '22_PRO_CONVERGENCE.md',
    'exactly one per round, never resubmitted')) {
    if (-not $reviewSkill.Contains($required)) { throw "Review Skill missing: $required" }
}

foreach ($required in @(
    'active_assignment_id=',
    'next_boundary=',
    'autonomous_research_grant=',
    'iterations_remaining=',
    'conclusion_bearing_iterations_consumed=',
    'execution_mode=',
    'git_integration_status=project_manager_direct_authorized',
    'experiment_operator_fallback=forbidden',
    'iteration_report_requirement=required_before_successor',
    'uav_user_scope=transient_demand_coverage_plus_charging_roster_change_plus_temporary_detach_failure_robustness',
    'uav_physical_fleet_boundary=fixed_slots_distinct_from_dynamic_service_roster',
    'workflow_hash_validation=disabled')) {
    if (-not $current.Contains($required)) { throw "CURRENT_WORK missing: $required" }
}

$remainingMatch = [regex]::Match($current, '(?m)^iterations_remaining=(\d+)\s*$')
$consumedMatch = [regex]::Match($current, '(?m)^conclusion_bearing_iterations_consumed=(\d+)\s*$')
if (-not $remainingMatch.Success -or -not $consumedMatch.Success) {
    throw 'CURRENT_WORK iteration accounting is not a nonnegative integer contract'
}
if ($current.Contains('autonomous_research_grant=ACTIVE_') -and
    [int]$remainingMatch.Groups[1].Value -le 0) {
    throw 'An active autonomous grant has no remaining conclusion-bearing iterations'
}
# The grant's size lives in its own name and was parsed by nothing, so the check
# above could only fire on a hand-written zero. Parse it, and hold the recorded
# remainder inside it.
#
# What this does NOT do, stated so nobody reads more into it: it cannot detect
# the loop running PAST the grant. Consumption is not machine-countable today --
# `conclusion_bearing_iterations_consumed` is a LIFETIME total (CURRENT_WORK.md
# says so), reports 24-29 are supporting work consuming no quota, and nothing
# emits a countable marker when a conclusion-bearing iteration closes. Deriving
# the remainder needs such a marker to exist first. Until then this guards
# transcription drift, not overrun.
$grantMatch = [regex]::Match($current, '(?m)^autonomous_research_grant=ACTIVE_([A-Z]+)_ITERATION')
if ($grantMatch.Success) {
    $sizeWords = @{ 'FIVE' = 5; 'TEN' = 10; 'FIFTEEN' = 15; 'TWENTY' = 20; 'THIRTY' = 30; 'FIFTY' = 50 }
    $word = $grantMatch.Groups[1].Value
    if (-not $sizeWords.ContainsKey($word)) {
        throw "Active autonomous grant declares an unparseable size '$word'. Its size must be readable by a machine, or the remainder it bounds is unenforceable."
    }
    $grantSize = $sizeWords[$word]
    $remaining = [int]$remainingMatch.Groups[1].Value
    if ($remaining -gt $grantSize) {
        throw "iterations_remaining=$remaining exceeds the active grant's own size ($word=$grantSize)"
    }
}

# The declared mode and the pause contract it implies must agree. Left
# unchecked these drift apart and the loop pauses in the wrong places.
$modeMatch = [regex]::Match($current, '(?m)^execution_mode=(authorized|unauthorized)\s*$')
if (-not $modeMatch.Success) {
    throw 'CURRENT_WORK does not declare execution_mode as authorized or unauthorized'
}
$grantActive = $current.Contains('autonomous_research_grant=ACTIVE_')
if ($modeMatch.Groups[1].Value -eq 'authorized') {
    if (-not $grantActive) {
        throw 'Authorized mode declared without an ACTIVE_ autonomous grant'
    }
    if (-not $current.Contains('intermediate_authorization_prompts=forbidden')) {
        throw 'Authorized mode must record intermediate_authorization_prompts=forbidden'
    }
}
else {
    if ($grantActive) {
        throw 'Unauthorized mode declared while an ACTIVE_ grant is still recorded'
    }
    if (-not $current.Contains('intermediate_authorization_prompts=required_at_plan_and_result')) {
        throw 'Unauthorized mode must record the plan and result checkpoints'
    }
}

# The subagent context carries worker behaviour and NO workflow. Its
# load-bearing rules are anchored by the key=value fence at its top (charter:
# contract_test_assertion_target); the prose stays for the reader, the keys
# are what the test holds. The exclusion below asserts the workflow has not
# crept back in.
foreach ($required in @(
    'subagent_git=forbidden',
    'unattended_waiting=in_band_only',
    'unmeasured_claims=forbidden',
    'shared_workstation=foreign_processes_expected',
    'workflow_content=none')) {
    if (-not $context.Contains($required)) { throw "Agent context missing: $required" }
}
foreach ($leaked in @(
    'eight-step', 'Stage A', 'Stage B', 'iteration budget', 'IMPLEMENTATION_PLAN')) {
    if ($context.Contains($leaked)) {
        throw "Workflow leaked into the subagent context: $leaked"
    }
}

# CLAUDE.md and the implementer definition are no longer content-asserted in
# prose (charter: contract_test_assertion_target). Two assertions here pinned
# the exact line-wrapping of markdown paragraphs; the properties they carried
# are held by the key assertions above and the operator contract's line-count
# cap on CLAUDE.md. The hash/superpowers scan below still reads both files.
$implementerDef = Get-Content -Raw -LiteralPath (Join-Path $repo '.claude/agents/hmasd-implementer.md')
foreach ($text in @($agents, $current, $context, $implementerDef, $pmRole)) {
    if ($text -match '(?m)^\w+_sha256=' -or $text.Contains('path_hash_source_status')) {
        throw 'Active workflow retains a hash handoff'
    }
    if ($text.Contains('superpowers_execution=enabled')) {
        throw 'Active workflow enables generic Superpowers execution'
    }
}

$reportReadme = Join-Path $repo 'docs/report/README.md'
if (-not (Test-Path -LiteralPath $reportReadme -PathType Leaf)) {
    throw 'Iteration-report README is missing'
}
$readme = Get-Content -Raw -Encoding UTF8 -LiteralPath $reportReadme
foreach ($required in @(
    'iteration_report_language=zh-CN',
    'separate_approval=not_required',
    'additional_review=false')) {
    if (-not $readme.Contains($required)) { throw "Iteration-report contract missing: $required" }
}

$consumed = [int]$consumedMatch.Groups[1].Value
for ($iteration = 1; $iteration -le $consumed; $iteration++) {
    $path = Join-Path $repo "docs/report/ITERATION_$iteration.md"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing Chinese iteration report: ITERATION_$iteration.md"
    }
    $report = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
    if (-not [regex]::IsMatch($report, '[\p{IsCJKUnifiedIdeographs}]')) {
        throw "ITERATION_$iteration.md is not a Chinese report"
    }
}

# Retired executable families, one stem per family (charter: tombstone_policy
# is pattern-based, the list never grows per file). A stem matches any file
# resurrecting it in the three executable directories -- module, runner or
# test variant alike. Names generic enough to collide with active work
# (uav_temp_loss_g1, async_commitment_roster_g3 are live) stay OFF this list;
# a stem is added only when its family retires, never widened to a generation.
$retiredStems = @('temporal_duty_g1', 'ehc_g1', 'access_positive_ehc_g1',
    'cross_lifecycle_handoff_g2', 'ehc_handoff_g2', 'useful_effect_roster_g3')
foreach ($dir in @('ha_ctse_process', 'scripts', 'tests')) {
    foreach ($file in (Get-ChildItem -LiteralPath (Join-Path $repo $dir) -File -Filter '*.py')) {
        foreach ($stem in $retiredStems) {
            if ($file.Name -match "(^|_)$stem(_test)?\.py$") {
                throw "Closed executable family '$stem' is back on the active line: $dir/$($file.Name)"
            }
        }
    }
}

# A UTF-8 BOM ahead of the opening '---' makes the runtime fail to parse a
# subagent definition, and the agent silently disappears from the roster --
# no error, just an agent_type that no longer exists. PowerShell 5.1's
# Set-Content -Encoding utf8 writes a BOM, which de-registered eight of ten
# definitions on 2026-07-24. Every definition must also declare a name.
foreach ($definition in (Get-ChildItem -LiteralPath (Join-Path $repo '.claude/agents') -Filter '*.md')) {
    $bytes = [IO.File]::ReadAllBytes($definition.FullName)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        throw "Subagent definition has a UTF-8 BOM and will not register: $($definition.Name)"
    }
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    if ($text -notmatch '\A---\r?\n') {
        throw "Subagent definition does not open with frontmatter: $($definition.Name)"
    }
    if ($text -notmatch '(?m)^name:\s*\S') {
        throw "Subagent definition has no name field: $($definition.Name)"
    }
    # Tier is set per definition and nowhere else, so an omitted field is a
    # silent downgrade to the session default. One retired definition carried a
    # comment explaining why its effort was high, in place of the field itself.
    foreach ($field in @('model', 'effort')) {
        if ($text -notmatch "(?m)^${field}:\s*\S") {
            throw "Subagent definition has no $field field: $($definition.Name)"
        }
    }
    # Presence is not resolvability. A non-blank value that names no real model
    # behaves exactly like an omitted field -- a silent inherit of the session
    # model -- so the check above passes while the tier pin does nothing. Validate
    # against the closed set the harness actually resolves.
    if ($text -match '(?m)^model:\s*(\S+)') {
        $declaredModel = $Matches[1]
        if ($declaredModel -notin @('haiku', 'sonnet', 'opus', 'fable', 'inherit')) {
            throw "Subagent definition declares an unresolvable model '$declaredModel': $($definition.Name)"
        }
    }
}

Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
