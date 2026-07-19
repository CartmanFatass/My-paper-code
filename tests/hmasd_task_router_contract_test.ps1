[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-task-router/SKILL.md'
$resolver = Join-Path $repo '.agents/skills/hmasd-task-router/scripts/resolve_task_route.ps1'
$reviewSkill = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$experimentSkill = Join-Path $repo '.agents/skills/hmasd-experiment/SKILL.md'
$monitorRegistry = Join-Path $repo '.agents/skills/hmasd-experiment/references/monitor-task.json'

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @(
    'Mandatory communication contract for every HMASD Codex session',
    'for the recipient only',
    'not store expected values, compare models',
    'Omitting `model` or `thinking` is forbidden',
    'treats the reply destination as the new',
    'one `START_REVIEW`',
    '`REVIEW_COMPLETE`',
    '`REVIEW_BLOCKED` from the External Review Manager',
    'heartbeat ticks remain inside the monitor task',
    'ambiguous delivery is never repeated',
    'Require Delivery Proof',
    'tool result identifies the resolved recipient `threadId`',
    'final response',
    'not cross-task')) {
    if (-not $skillText.Contains($required)) {
        throw "Communication Skill is missing: $required"
    }
}
foreach ($forbidden in @(
    'ExpectedModel',
    'ExpectedThinking',
    'frozen route',
    'for the sender and recipient',
    'resolve both tasks')) {
    if ($skillText.Contains($forbidden)) {
        throw "Communication Skill retains static routing: $forbidden"
    }
}

foreach ($path in @($reviewSkill, $experimentSkill)) {
    if (-not (Get-Content -LiteralPath $path -Raw).Contains('hmasd-task-router')) {
        throw "Role Skill does not require common communication: $path"
    }
}

$monitor = Get-Content -LiteralPath $monitorRegistry -Raw | ConvertFrom-Json
if ($monitor.schema_version -ne 5 -or
    $monitor.monitor_route.thread_id -ne '019f772b-355f-79f3-abbc-2f08800738f8' -or
    $monitor.controller_return_route.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
    $monitor.controller_return_route.route_policy -ne 'resolve_live_immediately_before_each_send' -or
    $monitor.automation.id -ne 'hmasd-r35-single-thread-monitor' -or
    $monitor.automation.target_thread_id -ne $monitor.monitor_route.thread_id -or
    $monitor.routing_skill -ne '.agents/skills/hmasd-task-router/SKILL.md') {
    throw 'Persistent monitor registry is not the stable-ID communication contract'
}
foreach ($route in @($monitor.monitor_route, $monitor.controller_return_route)) {
    if ($null -ne $route.PSObject.Properties['model'] -or
        $null -ne $route.PSObject.Properties['thinking']) {
        throw 'Monitor registry must not mirror task model or thinking'
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
