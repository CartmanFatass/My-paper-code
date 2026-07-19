[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$skillPath = Join-Path $repo '.agents/skills/hmasd-task-router/SKILL.md'
$resolver = Join-Path $repo '.agents/skills/hmasd-task-router/scripts/resolve_task_route.ps1'
$reviewSkill = Join-Path $repo '.agents/skills/hmasd-review-round/SKILL.md'
$experimentSkill = Join-Path $repo '.agents/skills/hmasd-experiment/SKILL.md'
$experimentProtocol = Join-Path $repo '.agents/skills/hmasd-experiment/references/experiment-protocol.md'
$monitorRegistry = Join-Path $repo '.agents/skills/hmasd-experiment/references/monitor-task.json'

$skillText = Get-Content -LiteralPath $skillPath -Raw
foreach ($required in @(
    'routing authority.',
    '`thinking` is forbidden',
    'Resolve the controller route again',
    'registered heartbeat automation',
    'heartbeat only schedules one bounded monitor turn',
    'Do not retry an ambiguous delivery')) {
    if (-not $skillText.Contains($required)) {
        throw "Task router Skill is missing: $required"
    }
}

foreach ($path in @($reviewSkill, $experimentSkill, $experimentProtocol)) {
    if (-not (Get-Content -LiteralPath $path -Raw).Contains('hmasd-task-router')) {
        throw "Workflow does not require hmasd-task-router: $path"
    }
}

$monitor = Get-Content -LiteralPath $monitorRegistry -Raw | ConvertFrom-Json
if ($monitor.schema_version -ne 3 -or
    $monitor.monitor_route.thread_id -ne '019f772b-355f-79f3-abbc-2f08800738f8' -or
    $monitor.monitor_route.model -ne 'gpt-5.6-luna' -or
    $monitor.monitor_route.thinking -ne 'medium' -or
    $monitor.controller_return_route.thread_id -ne '019f5c78-0c91-7612-adb4-c1fcfe4484c8' -or
    $monitor.controller_return_route.model -ne 'gpt-5.6-sol' -or
    $monitor.controller_return_route.thinking -ne 'xhigh' -or
    $monitor.automation.id -ne 'hmasd-r35-single-thread-monitor' -or
    $monitor.automation.kind -ne 'heartbeat' -or
    $monitor.automation.target_thread_id -ne $monitor.monitor_route.thread_id -or
    $monitor.routing_skill -ne '.agents/skills/hmasd-task-router/SKILL.md') {
    throw 'Persistent monitor registry is not the exact two-way route contract'
}

$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('hmasd-task-router-' + [guid]::NewGuid().ToString('N'))
$db = Join-Path $tempRoot 'state.sqlite'
$threadId = '11111111-2222-3333-4444-555555555555'
try {
    [void](New-Item -ItemType Directory -Path $tempRoot)
    & sqlite3 $db 'CREATE TABLE threads (id TEXT PRIMARY KEY, model TEXT, reasoning_effort TEXT, archived INTEGER);'
    & sqlite3 $db "INSERT INTO threads VALUES ('$threadId','gpt-5.6-luna','high',0);"
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to create task-router fixture database'
    }

    $route = & $resolver -ThreadId $threadId -ExpectedModel 'gpt-5.6-luna' `
        -ExpectedThinking 'high' -StateDb $db | ConvertFrom-Json
    if ($route.hostId -ne 'local' -or $route.threadId -ne $threadId -or
        $route.model -ne 'gpt-5.6-luna' -or $route.thinking -ne 'high') {
        throw 'Resolver did not preserve the exact live route'
    }

    $mismatchBlocked = $false
    try {
        & $resolver -ThreadId $threadId -ExpectedModel 'gpt-5.6-sol' `
            -ExpectedThinking 'high' -StateDb $db | Out-Null
    } catch {
        $mismatchBlocked = $true
    }
    if (-not $mismatchBlocked) {
        throw 'Resolver accepted a model mismatch'
    }
} finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

Write-Output 'HMASD_TASK_ROUTER_CONTRACT_OK'
