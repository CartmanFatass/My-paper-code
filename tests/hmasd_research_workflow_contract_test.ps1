$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillsRoot = Join-Path $repo ".agents/skills"
$researchSkillPath = Join-Path $skillsRoot "hmasd-research-cycle/SKILL.md"
$experimentSkillPath = Join-Path $skillsRoot "hmasd-experiment/SKILL.md"
$experimentProtocolPath = Join-Path $skillsRoot "hmasd-experiment/references/experiment-protocol.md"
$watcherScriptPath = Join-Path $skillsRoot "hmasd-experiment/scripts/wait_runner_status.ps1"
$reviewSkillPath = Join-Path $skillsRoot "hmasd-review-round/SKILL.md"
$agentsPath = Join-Path $repo "AGENTS.md"
$oldContractTestPath = Join-Path $repo "tests/hmasd_core_development_contract_test.ps1"

function Read-Normalized([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing required workflow file: $Path"
    }
    return (Get-Content -LiteralPath $Path -Raw) -replace '\s+', ' '
}

function Assert-Contains([string]$Text, [string]$Expected, [string]$Label) {
    if (-not $Text.Contains($Expected)) {
        throw "$Label is missing required contract text: $Expected"
    }
}

function Assert-NotContains([string]$Text, [string]$Forbidden, [string]$Label) {
    if ($Text.Contains($Forbidden)) {
        throw "$Label retains forbidden legacy text: $Forbidden"
    }
}

function Publish-StatusAtomic([string]$RunRoot, [string[]]$Lines) {
    $statusPath = Join-Path $RunRoot "runner_status.txt"
    $stagingPath = Join-Path $RunRoot (".runner_status.{0}.tmp" -f [guid]::NewGuid().ToString("N"))
    $content = ($Lines -join [Environment]::NewLine) + [Environment]::NewLine
    [IO.File]::WriteAllText($stagingPath, $content, [Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
        $replaceMethod = [IO.File].GetMethod("Replace", [type[]]@([string], [string], [string]))
        $replaceArguments = New-Object "System.Object[]" 3
        $replaceArguments[0] = [string]$stagingPath
        $replaceArguments[1] = [string]$statusPath
        $replaceArguments[2] = $null
        [void]$replaceMethod.Invoke($null, $replaceArguments)
    } else {
        [IO.File]::Move($stagingPath, $statusPath)
    }
}

function Start-StatusWatcher([string]$RunRoot, [string]$ReadyPath) {
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = (Get-Process -Id $PID).Path
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $escapedScript = $watcherScriptPath.Replace("'", "''")
    $escapedRunRoot = $RunRoot.Replace("'", "''")
    $escapedReadyPath = $ReadyPath.Replace("'", "''")
    $invocation = "& '$escapedScript' -RunPath '$escapedRunRoot' -ReadyPath '$escapedReadyPath'"
    $encodedInvocation = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($invocation))
    $startInfo.Arguments = "-NoProfile -NonInteractive -EncodedCommand $encodedInvocation"
    return [Diagnostics.Process]::Start($startInfo)
}

function Wait-WatcherReady([string]$ReadyPath, [int]$TimeoutMs = 5000) {
    if (Test-Path -LiteralPath $ReadyPath -PathType Leaf) {
        return
    }
    $readyWatcher = [IO.FileSystemWatcher]::new((Split-Path -Parent $ReadyPath), (Split-Path -Leaf $ReadyPath))
    $readyWatcher.NotifyFilter = [IO.NotifyFilters]::FileName
    $readyWatcher.EnableRaisingEvents = $true
    try {
        if (Test-Path -LiteralPath $ReadyPath -PathType Leaf) {
            return
        }
        $change = $readyWatcher.WaitForChanged([IO.WatcherChangeTypes]::Created, $TimeoutMs)
        if ($change.TimedOut -and -not (Test-Path -LiteralPath $ReadyPath -PathType Leaf)) {
            throw "Watcher did not signal ready within $TimeoutMs ms: $ReadyPath"
        }
    } finally {
        $readyWatcher.Dispose()
    }
}

function Wait-WatcherExit([Diagnostics.Process]$Process, [int]$TimeoutMs = 5000) {
    if (-not $Process.WaitForExit($TimeoutMs)) {
        $Process.Kill()
        $Process.WaitForExit()
        throw "Watcher did not exit within $TimeoutMs ms"
    }
    return [pscustomobject]@{
        ExitCode = $Process.ExitCode
        StdOut = $Process.StandardOutput.ReadToEnd()
        StdErr = $Process.StandardError.ReadToEnd()
    }
}

$skillNames = @(Get-ChildItem -LiteralPath $skillsRoot -Directory | Sort-Object Name | Select-Object -ExpandProperty Name)
$expectedSkillNames = @("hmasd-experiment", "hmasd-research-cycle", "hmasd-review-round")
if (($skillNames -join "|") -ne ($expectedSkillNames -join "|")) {
    throw "Project Skill set must be exactly: $($expectedSkillNames -join ', ')"
}

if (Test-Path -LiteralPath $oldContractTestPath) {
    throw "The legacy mandatory-Superpowers contract test must be deleted"
}

$agents = Read-Normalized $agentsPath
$research = Read-Normalized $researchSkillPath
$experiment = Read-Normalized $experimentSkillPath
$experimentProtocol = Read-Normalized $experimentProtocolPath
$watcherScript = Read-Normalized $watcherScriptPath
$review = Read-Normalized $reviewSkillPath

foreach ($required in @(
    "Direct controller work is the default",
    '$hmasd-research-cycle',
    '$hmasd-experiment',
    '$hmasd-review-round',
    "does not imply one permitted research direction",
    'at most one active `wait_agent`',
    "native wait times out",
    "mailbox wait"
)) {
    Assert-Contains $agents $required "AGENTS.md"
}
foreach ($forbidden in @(
    "Superpowers owns the generic core-development lifecycle",
    'superpowers:subagent-driven-development` when subagents are available',
    "Implementation and review permissions, edit and commit boundaries, task handoffs and fix loops follow the invoked Superpowers workflow"
)) {
    Assert-NotContains $agents $forbidden "AGENTS.md"
}

foreach ($required in @(
    "two to four live",
    "one coherent implementer",
    "one whole-change reviewer",
    "at most one repair cycle",
    "Do not create task briefs, reports, progress ledgers, review packages, or task commits",
    "valid scientific negative",
    "Stop after one accepted evidence source"
)) {
    Assert-Contains $research $required "hmasd-research-cycle"
}

foreach ($required in @(
    "final run root",
    "runner_status.txt",
    "payload staging",
    "inside the final run root",
    'at most one active `wait_agent`',
    "same child",
    "native wait times out",
    "mailbox wait",
    "only nonterminal state",
    "malformed line",
    "missing state",
    "unknown state",
    "Do not poll"
)) {
    Assert-Contains $experiment $required "hmasd-experiment"
}
Assert-NotContains $experiment 'do not poll the status, read the child repeatedly, call `wait_agent`' "hmasd-experiment"
foreach ($required in @(
    "live from launch",
    "inside the final run root",
    'at most one active `wait_agent`',
    "same child",
    "native wait times out",
    "mailbox wait",
    "only nonterminal state",
    "malformed line",
    "missing state",
    "unknown state",
    "file or result-directory publication"
)) {
    Assert-Contains $experimentProtocol $required "experiment-protocol"
}
foreach ($legacyWait in @(
    'exactly one native `wait_agent`',
    'exactly one `wait_agent`'
)) {
    Assert-NotContains $agents $legacyWait "AGENTS.md"
    Assert-NotContains $experiment $legacyWait "hmasd-experiment"
    Assert-NotContains $experimentProtocol $legacyWait "experiment-protocol"
}

foreach ($required in @(
    "tracked HMASD five-stage external-review round",
    "controller write disposition",
    "cannot authorize code, experiments, promotion, retirement"
)) {
    Assert-Contains $review $required "hmasd-review-round"
}

foreach ($skillName in $expectedSkillNames) {
    $metadata = Join-Path $skillsRoot "$skillName/agents/openai.yaml"
    if (-not (Test-Path -LiteralPath $metadata -PathType Leaf)) {
        throw "Missing Skill UI metadata: $metadata"
    }
}

foreach ($required in @(
    "Malformed status line",
    "Status is missing state",
    "Unknown status state",
    '@("running", "complete", "completed", "failed")',
    "ReadyPath"
)) {
    Assert-Contains $watcherScript $required "wait_runner_status.ps1"
}

if (-not (Test-Path -LiteralPath $watcherScriptPath -PathType Leaf)) {
    throw "Missing experiment status watcher: $watcherScriptPath"
}

$pytestTmpRoot = [IO.Path]::GetFullPath((Join-Path $repo "tests/.pytest_tmp"))
$runtimeTmpRoot = [IO.Path]::GetFullPath((Join-Path $pytestTmpRoot "hmasd-research-workflow-contract"))
if (-not $runtimeTmpRoot.StartsWith($pytestTmpRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Runtime test path escapes tests/.pytest_tmp: $runtimeTmpRoot"
}
if (Test-Path -LiteralPath $runtimeTmpRoot) {
    Remove-Item -LiteralPath $runtimeTmpRoot -Recurse -Force
}
[void](New-Item -ItemType Directory -Path $runtimeTmpRoot)

$runtimePassed = $false
try {
    $successRoot = Join-Path $runtimeTmpRoot "watcher-success"
    [void](New-Item -ItemType Directory -Path $successRoot)
    $successRunId = Split-Path -Leaf $successRoot
    $successReady = Join-Path $successRoot "watcher.ready"
    $resultDirectory = Join-Path $successRoot "result"
    [void](New-Item -ItemType Directory -Path $resultDirectory)
    $resultPath = Join-Path $resultDirectory "result.json"
    [IO.File]::WriteAllText($resultPath, "{}", [Text.UTF8Encoding]::new($false))
    Publish-StatusAtomic $successRoot @(
        "state=running",
        "updated=2026-07-18T20:00:00+08:00",
        "phase=train",
        "run_root=$successRoot",
        "run_id=$successRunId"
    )

    $successProcess = Start-StatusWatcher $successRoot $successReady
    try {
        Wait-WatcherReady $successReady
        Publish-StatusAtomic $successRoot @(
            "state=complete",
            "updated=2026-07-18T20:00:01+08:00",
            "phase=done",
            "run_root=$successRoot",
            "run_id=$successRunId",
            "result_path=$resultPath"
        )
        $successOutcome = Wait-WatcherExit $successProcess
    } finally {
        if (-not $successProcess.HasExited) {
            $successProcess.Kill()
            $successProcess.WaitForExit()
        }
        $successProcess.Dispose()
    }
    if ($successOutcome.ExitCode -ne 0) {
        throw "Watcher terminal transition failed: $($successOutcome.StdErr.Trim())"
    }
    $terminal = $successOutcome.StdOut.Trim() | ConvertFrom-Json
    if ($terminal.state -ne "complete" -or $terminal.phase -ne "done") {
        throw "Watcher returned the wrong terminal JSON: $($successOutcome.StdOut.Trim())"
    }
    if (-not [string]::Equals([IO.Path]::GetFullPath([string]$terminal.payload), [IO.Path]::GetFullPath($resultPath), [StringComparison]::OrdinalIgnoreCase)) {
        throw "Watcher returned the wrong terminal payload path"
    }

    $invalidRoot = Join-Path $runtimeTmpRoot "watcher-invalid"
    [void](New-Item -ItemType Directory -Path $invalidRoot)
    $invalidRunId = Split-Path -Leaf $invalidRoot
    $invalidReady = Join-Path $invalidRoot "watcher.ready"
    Publish-StatusAtomic $invalidRoot @(
        "state=running",
        "updated=2026-07-18T20:01:00+08:00",
        "phase=train",
        "run_root=$invalidRoot",
        "run_id=$invalidRunId"
    )

    $invalidProcess = Start-StatusWatcher $invalidRoot $invalidReady
    try {
        Wait-WatcherReady $invalidReady
        Publish-StatusAtomic $invalidRoot @(
            "state=unknown",
            "updated=2026-07-18T20:01:01+08:00",
            "phase=invalid",
            "run_root=$invalidRoot",
            "run_id=$invalidRunId"
        )
        $invalidOutcome = Wait-WatcherExit $invalidProcess
    } finally {
        if (-not $invalidProcess.HasExited) {
            $invalidProcess.Kill()
            $invalidProcess.WaitForExit()
        }
        $invalidProcess.Dispose()
    }
    if ($invalidOutcome.ExitCode -eq 0) {
        throw "Watcher accepted an unknown existing status state"
    }
    if ($invalidOutcome.StdErr -notmatch "Unknown status state") {
        throw "Watcher failed for the wrong unknown-state reason: $($invalidOutcome.StdErr.Trim())"
    }

    $runtimePassed = $true
} finally {
    if ($runtimePassed -and (Test-Path -LiteralPath $runtimeTmpRoot)) {
        Remove-Item -LiteralPath $runtimeTmpRoot -Recurse -Force
    }
}

Write-Output "HMASD_RESEARCH_WORKFLOW_CONTRACT_OK"
