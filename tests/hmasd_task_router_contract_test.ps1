[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-task-router/SKILL.md'
$resolver = Join-Path $repo '.agents/skills/hmasd-task-router/scripts/resolve_task_route.ps1'
$rolesPath = Join-Path $repo '.agents/skills/hmasd-task-router/references/session-roles.json'
$sessionRoleSkills = @(
    (Join-Path $repo '.agents/skills/hmasd-code-manager/SKILL.md'),
    (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'),
    (Join-Path $repo '.agents/skills/hmasd-review-exchange/SKILL.md'),
    (Join-Path $repo '.agents/skills/hmasd-experiment/SKILL.md')
)
$implementerSkill = Join-Path $repo '.agents/skills/hmasd-implementer/SKILL.md'
$monitorRegistry = Join-Path $repo '.agents/skills/hmasd-experiment/references/monitor-task.json'

$skillText = Get-Content -LiteralPath $skillPath -Raw
$normalizedSkillText = $skillText -replace '\s+', ' '
foreach ($required in @(
    'Own persistent-session communication only',
    'Never use this Skill for a temporary',
    'exactly one session-role Skill',
    'HMASD_SESSION_TASK',
    'task_id=<stable id>',
    'role_skill=<one .agents/skills/.../SKILL.md path>',
    'Conversation history, nearby files, registries, and earlier assignments are not implicit inputs',
    'Every compact message must still contain exactly one',
    'Session and Role Directory',
    'references/session-roles.json',
    'one-to-one role bindings',
    'active controller alone maintains this directory',
    'current task ID equals the directory entry',
    'Resolve the Recipient Live',
    'Copy the recipient''s current values unchanged',
    'Send once',
    'same recipient `threadId`',
    'ambiguous send is never repeated',
    'Before replying, resolve the reply destination again',
    'Controller Send Contract',
    'take the recipient `thread_id` only from that role entry',
    'controller records no waiting state',
    'External Review Topology',
    'controller <-> external_review_manager',
    'controller-to-reviewer',
    'manager-to-exchange send',
    'Code Implementation Topology',
    'controller <-> code_implementation_manager',
    'START_CODE_WORK',
    'CODE_GIT_PUSH_REQUIRED',
    'CODE_COMPLETE',
    'CODE_BLOCKED',
    'subagents are not persistent-session destinations',
    'Receive Contract',
    'native delegation metadata `source_thread_id` equals the session ID',
    'stable `handoff_id`',
    'same role and `handoff_id` as the same delivery',
    'do not add a separate relay state machine')) {
    if (-not $normalizedSkillText.Contains($required)) {
        throw "Communication Skill is missing: $required"
    }
}

$roles = Get-Content -LiteralPath $rolesPath -Raw | ConvertFrom-Json
$managerId = $roles.roles.external_review_manager.thread_id
$managerStatus = $roles.roles.external_review_manager.registration_status
$codeManagerId = $roles.roles.code_implementation_manager.thread_id
$codeManagerStatus = $roles.roles.code_implementation_manager.registration_status
if ($roles.schema_version -ne 3 -or
    $roles.roles.controller.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
    $roles.roles.code_implementation_manager.role_skill -ne '.agents/skills/hmasd-code-manager/SKILL.md' -or
    $roles.roles.external_review_manager.role_skill -ne '.agents/skills/hmasd-review-round/SKILL.md' -or
    $roles.roles.gemini_divergent_exchange.thread_id -ne '019f76cc-580b-7c40-8c92-97bfffaf51b1' -or
    $roles.roles.gemini_divergent_exchange.reviewer_role -ne 'GEMINI_DIVERGENT' -or
    $roles.roles.open_divergent_exchange.thread_id -ne '019f716c-3c8a-7891-8c89-c94dc94fab4c' -or
    $roles.roles.open_divergent_exchange.reviewer_role -ne 'OPEN_DIVERGENT' -or
    $roles.roles.convergent_exchange.thread_id -ne '019f716c-676f-7673-9782-f37b72f200d2' -or
    $roles.roles.convergent_exchange.reviewer_role -ne 'CONVERGENT' -or
    $roles.roles.gemini_divergent_exchange.role_skill -ne '.agents/skills/hmasd-review-exchange/SKILL.md' -or
    $roles.roles.open_divergent_exchange.role_skill -ne '.agents/skills/hmasd-review-exchange/SKILL.md' -or
    $roles.roles.convergent_exchange.role_skill -ne '.agents/skills/hmasd-review-exchange/SKILL.md' -or
    $roles.roles.experiment_monitor.thread_id -ne '019f772b-355f-79f3-abbc-2f08800738f8' -or
    $roles.roles.experiment_monitor.role_skill -ne '.agents/skills/hmasd-experiment/SKILL.md' -or
    -not $roles.policy.one_session_one_role -or
    $roles.policy.update_owner -ne 'active_controller') {
    throw 'Session-role directory is inconsistent'
}
if (($null -eq $codeManagerId -and $codeManagerStatus -ne 'UNASSIGNED') -or
    ($null -ne $codeManagerId -and $codeManagerStatus -ne 'ACTIVE')) {
    throw 'Code Implementation Manager registration state is inconsistent'
}
if (($null -eq $managerId -and $managerStatus -ne 'UNASSIGNED') -or
    ($null -ne $managerId -and $managerStatus -ne 'ACTIVE')) {
    throw 'External Review Manager registration state is inconsistent'
}
foreach ($entry in @(
    $roles.roles.controller,
    $roles.roles.code_implementation_manager,
    $roles.roles.external_review_manager,
    $roles.roles.gemini_divergent_exchange,
    $roles.roles.open_divergent_exchange,
    $roles.roles.convergent_exchange,
    $roles.roles.experiment_monitor
)) {
    foreach ($forbidden in @('hostId', 'model', 'thinking')) {
        if ($null -ne $entry.PSObject.Properties[$forbidden]) {
            throw "Session-role directory mirrors live route field: $forbidden"
        }
    }
}
$assignedIds = @(
    $roles.roles.controller.thread_id,
    $codeManagerId,
    $managerId,
    $roles.roles.gemini_divergent_exchange.thread_id,
    $roles.roles.open_divergent_exchange.thread_id,
    $roles.roles.convergent_exchange.thread_id,
    $roles.roles.experiment_monitor.thread_id
) | Where-Object { $null -ne $_ }
if (@($assignedIds | Select-Object -Unique).Count -ne $assignedIds.Count) {
    throw 'A persistent Codex task is bound to more than one role'
}
foreach ($forbidden in @(
    'ExpectedModel',
    'ExpectedThinking',
    'frozen route',
    'resolve both tasks')) {
    if ($normalizedSkillText.Contains($forbidden)) {
        throw "Communication Skill retains static or sender-owned routing: $forbidden"
    }
}

foreach ($path in $sessionRoleSkills) {
    $text = Get-Content -LiteralPath $path -Raw
    if (-not $text.Contains('hmasd-task-router') -or
        -not $text.Contains('role_skill=')) {
        throw "Role Skill lacks the common router or explicit role grant: $path"
    }
}
$implementerText = Get-Content -LiteralPath $implementerSkill -Raw
if (-not $implementerText.Contains('native subagent result channel') -or
    -not $implementerText.Contains('invoke `$hmasd-task-router`') -or
    $implementerText.Contains('../hmasd-task-router/SKILL.md')) {
    throw 'Implementer incorrectly uses persistent-session routing'
}

$monitor = Get-Content -LiteralPath $monitorRegistry -Raw | ConvertFrom-Json
if ($monitor.schema_version -ne 7 -or
    $monitor.session_role_registry -ne '.agents/skills/hmasd-task-router/references/session-roles.json' -or
    $monitor.automation.owner -ne 'registered_monitor_session' -or
    $monitor.automation.target -ne 'self') {
    throw 'Persistent monitor registry is not isolated from session routing'
}
foreach ($forbidden in @('monitor_route', 'controller_return_route', 'routing_skill', 'route_policy')) {
    if ($null -ne $monitor.PSObject.Properties[$forbidden]) {
        throw "Monitor registry duplicates router-owned session data: $forbidden"
    }
}

$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('hmasd-task-router-' + [guid]::NewGuid().ToString('N'))
$db = Join-Path $tempRoot 'state.sqlite'
$threadId = '11111111-2222-3333-4444-555555555555'
try {
    [void](New-Item -ItemType Directory -Path $tempRoot)
    & sqlite3 $db 'CREATE TABLE threads (id TEXT PRIMARY KEY, model TEXT, reasoning_effort TEXT, archived INTEGER);'
    & sqlite3 $db "INSERT INTO threads VALUES ('$threadId','gpt-5.6-luna','max',0);"
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to create communication fixture database'
    }

    $route = & $resolver -ThreadId $threadId -StateDb $db | ConvertFrom-Json
    if ($route.hostId -ne 'local' -or $route.threadId -ne $threadId -or
        $route.model -ne 'gpt-5.6-luna' -or $route.thinking -ne 'max') {
        throw 'Resolver did not return the exact live route'
    }

    & sqlite3 $db "UPDATE threads SET archived=1 WHERE id='$threadId';"
    $archivedBlocked = $false
    try { & $resolver -ThreadId $threadId -StateDb $db | Out-Null } catch { $archivedBlocked = $true }
    if (-not $archivedBlocked) {
        throw 'Resolver accepted an archived task'
    }
} finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

Write-Output 'HMASD_TASK_ROUTER_CONTRACT_OK'
