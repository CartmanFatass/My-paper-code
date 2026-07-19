[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-task-router/SKILL.md'
$resolver = Join-Path $repo '.agents/skills/hmasd-task-router/scripts/resolve_task_route.ps1'
$sessionRoleSkills = @(
    (Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'),
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
    'Resolve the Recipient Live',
    'Copy the recipient''s current values unchanged',
    'Send once',
    'same recipient `threadId`',
    'ambiguous send is never repeated',
    'Before replying, resolve the reply destination again',
    'Receive Contract',
    'native delegation metadata names the registered task ID',
    'stable `handoff_id`',
    'same role and `handoff_id` as the same delivery',
    'do not add a separate relay state machine')) {
    if (-not $normalizedSkillText.Contains($required)) {
        throw "Communication Skill is missing: $required"
    }
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
if ($monitor.schema_version -ne 6 -or
    $monitor.monitor_route.thread_id -ne '019f772b-355f-79f3-abbc-2f08800738f8' -or
    $monitor.controller_return_route.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
    $monitor.controller_return_route.route_policy -ne 'resolve_live_immediately_before_each_send' -or
    $monitor.automation.owner -ne 'registered_monitor_session' -or
    $monitor.automation.target -ne 'self' -or
    $monitor.routing_skill -ne '.agents/skills/hmasd-task-router/SKILL.md') {
    throw 'Persistent monitor registry is not the stable-ID communication contract'
}
foreach ($route in @($monitor.monitor_route, $monitor.controller_return_route)) {
    if ($null -ne $route.PSObject.Properties['model'] -or
        $null -ne $route.PSObject.Properties['thinking'] -or
        $null -ne $route.PSObject.Properties['host_id']) {
        throw 'Monitor registry must not mirror live delivery metadata'
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
