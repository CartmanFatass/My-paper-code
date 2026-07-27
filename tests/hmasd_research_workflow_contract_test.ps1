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
$expectedSkills = @('hmasd-review-round') | Sort-Object
if (Compare-Object $expectedSkills $skills) {
    throw "Unexpected active Skill set: $($skills -join ',')"
}

# Every bounded role is a Claude Code subagent definition.
$agentDefs = @(Get-ChildItem (Join-Path $repo '.claude/agents') -File -Filter 'hmasd-*.md' |
    Select-Object -ExpandProperty Name | Sort-Object)
$expectedAgents = @(
    'hmasd-code-scout.md', 'hmasd-doc-auditor.md',
    'hmasd-exp-recorder.md', 'hmasd-experiment-operator.md',
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

foreach ($required in @(
    'single project owner at any moment',
    'has no persistent task',
    'There is no Controller, persistent Monitor',
    'project_manager_git_authority=direct',
    'project_manager_external_review_transport=project_manager_direct',
    'scientific_decision_authority=external_pro',
    'local_conversation_scientific_authority=none',
    '## Execution modes',
    'project_manager_experiment_orchestration=direct_via_registered_child',
    'superpowers_execution=disabled',
    'backward_compatibility=not_required',
    'test_scope=proof_sized',
    'iteration_report_language=zh-CN',
    'iteration_report_path=docs/report/ITERATION_<n>.md',
    'not another review, approval or scientific evidence source',
    'per_file_hash_handoff=forbidden',
    'same_file_concurrent_writes=forbidden',
    '### Crossing the boundary',
    'converge with External Pro',
    '## Context compaction',
    'context boundary, not a control boundary',
    'continue straight into the next iteration')) {
    if (-not $agents.Contains($required)) { throw "AGENTS missing: $required" }
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

# The subagent context carries worker behaviour and NO workflow. A worker that
# has to reconstruct the process from documents is a worker guessing, so these
# assert the behavioural rules are present -- and the exclusion below asserts the
# workflow has not crept back in. IMPLEMENTATION_PLAN.md was deleted 2026-07-27:
# it was a third copy of the boundary, three days stale, and pointed at here as
# the frozen contract. Its assertions were static boilerplate that could not fail
# on the drift they were meant to catch.
foreach ($required in @(
    'Subagents never run Git',
    'It carries **no workflow**',
    'Never end your turn to wait for your own work',
    'Never assert a property you did not measure',
    'Never report an elapsed time you did not measure',
    'Protected semantics')) {
    if (-not $context.Contains($required)) { throw "Agent context missing: $required" }
}
foreach ($leaked in @(
    'eight-step', 'Stage A', 'Stage B', 'iteration budget', 'IMPLEMENTATION_PLAN')) {
    if ($context.Contains($leaked)) {
        throw "Workflow leaked into the subagent context: $leaked"
    }
}
foreach ($required in @(
    'docs/report/ITERATION_<n>.md',
    'creates a second acceptance owner',
    'blocks on separate approval')) {
    if (-not $pmRole.Contains($required)) { throw "Project Manager role missing: $required" }
}
# The agile development procedure was a Skill until 2026-07-27, read by exactly
# one agent definition. It had two audiences doing different things with it -- the
# orchestrator sizing a task, the implementer executing one -- so it split by use
# rather than staying a shared document nobody is guaranteed to load. Assert both
# halves landed, and that neither drifted into being the other.
$implementerDef = Get-Content -Raw -LiteralPath (Join-Path $repo '.claude/agents/hmasd-implementer.md')
foreach ($required in @(
    'never trade
reproducibility',
    'Remove what it
   replaces',
    'Never weaken a check and never')) {
    if (-not $implementerDef.Contains($required)) {
        throw "Implementer execution procedure missing: $required"
    }
}
foreach ($required in @(
    '## Sizing the task',
    'Smallest sufficient evidence',
    'Trade maintainability away freely',
    'out-of-scope list is deliberate staging')) {
    if (-not $agents.Contains($required)) { throw "Task-sizing procedure missing: $required" }
}

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

foreach ($retired in @(
    'ha_ctse_process/temporal_duty_g1.py',
    'ha_ctse_process/ehc_g1.py',
    'scripts/run_access_positive_ehc_g1.py',
    'tests/ha_ctse_process_temporal_duty_g1_test.py',
    'tests/ha_ctse_process_ehc_g1_test.py',
    'tests/run_access_positive_ehc_g1_test.py',
    'ha_ctse_process/cross_lifecycle_handoff_g2.py',
    'ha_ctse_process/ehc_handoff_g2.py',
    'scripts/run_cross_lifecycle_handoff_g2.py',
    'tests/ha_ctse_process_cross_lifecycle_handoff_g2_test.py',
    'tests/ha_ctse_process_ehc_handoff_g2_test.py',
    'tests/run_cross_lifecycle_handoff_g2_test.py',
    'ha_ctse_process/useful_effect_roster_g3.py',
    'scripts/run_useful_effect_roster_g3.py',
    'tests/ha_ctse_process_useful_effect_roster_g3_test.py',
    'tests/run_useful_effect_roster_g3_test.py')) {
    if (Test-Path -LiteralPath (Join-Path $repo $retired)) {
        throw "Closed executable remains on the active line: $retired"
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
}

Write-Output 'HMASD_RESEARCH_WORKFLOW_CONTRACT_OK'
