[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$watcherScriptPath = Join-Path $repo ".agents/skills/hmasd-experiment/scripts/wait_runner_status.ps1"
if (-not (Test-Path -LiteralPath $watcherScriptPath -PathType Leaf)) {
    throw "Missing experiment status watcher: $watcherScriptPath"
}

function Publish-StatusAtomic([string]$RunRoot, [string[]]$Lines) {
    $statusPath = Join-Path $RunRoot "runner_status.txt"
    $stagingPath = Join-Path $RunRoot (".runner_status.{0}.tmp" -f [guid]::NewGuid().ToString("N"))
    $content = ($Lines -join [Environment]::NewLine) + [Environment]::NewLine
    [IO.File]::WriteAllText($stagingPath, $content, [Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
        [IO.File]::Move($stagingPath, $statusPath, $true)
    } else {
        [IO.File]::Move($stagingPath, $statusPath)
    }
}

function Start-Watcher([string]$RunRoot, [string]$ReadyPath) {
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = (Get-Process -Id $PID).Path
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $script = $watcherScriptPath.Replace("'", "''")
    $root = $RunRoot.Replace("'", "''")
    $ready = $ReadyPath.Replace("'", "''")
    $invocation = "& '$script' -RunPath '$root' -ReadyPath '$ready'"
    $startInfo.Arguments = "-NoProfile -NonInteractive -EncodedCommand " +
        [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($invocation))
    [Diagnostics.Process]::Start($startInfo)
}

function Wait-Ready([string]$ReadyPath, [int]$TimeoutMs = 5000) {
    if (Test-Path -LiteralPath $ReadyPath -PathType Leaf) { return }
    $watcher = [IO.FileSystemWatcher]::new((Split-Path -Parent $ReadyPath), (Split-Path -Leaf $ReadyPath))
    $watcher.NotifyFilter = [IO.NotifyFilters]::FileName
    $watcher.EnableRaisingEvents = $true
    try {
        if (Test-Path -LiteralPath $ReadyPath -PathType Leaf) { return }
        $change = $watcher.WaitForChanged([IO.WatcherChangeTypes]::Created, $TimeoutMs)
        if ($change.TimedOut -and -not (Test-Path -LiteralPath $ReadyPath -PathType Leaf)) {
            throw "Watcher did not signal ready"
        }
    } finally {
        $watcher.Dispose()
    }
}

function Wait-Exit([Diagnostics.Process]$Process, [int]$TimeoutMs = 5000) {
    if (-not $Process.WaitForExit($TimeoutMs)) {
        $Process.Kill()
        $Process.WaitForExit()
        throw "Watcher did not exit"
    }
    [pscustomobject]@{
        ExitCode = $Process.ExitCode
        StdOut = $Process.StandardOutput.ReadToEnd()
        StdErr = $Process.StandardError.ReadToEnd()
    }
}

$tmp = Join-Path ([IO.Path]::GetTempPath()) ("hmasd-monitor-watcher-" + [guid]::NewGuid().ToString("N"))
[void](New-Item -ItemType Directory -Path $tmp)
try {
    $success = Join-Path $tmp "success"
    [void](New-Item -ItemType Directory -Path $success)
    $ready = Join-Path $success "watcher.ready"
    $result = Join-Path $success "result.json"
    [IO.File]::WriteAllText($result, "{}", [Text.UTF8Encoding]::new($false))
    Publish-StatusAtomic $success @(
        "state=running", "updated=2026-07-19T00:00:00+08:00", "phase=train",
        "run_root=$success", "run_id=success"
    )
    $process = Start-Watcher $success $ready
    try {
        Wait-Ready $ready
        Publish-StatusAtomic $success @(
            "state=complete", "updated=2026-07-19T00:00:01+08:00", "phase=done",
            "run_root=$success", "run_id=success", "result_path=$result"
        )
        $outcome = Wait-Exit $process
    } finally {
        if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
        $process.Dispose()
    }
    if ($outcome.ExitCode -ne 0) { throw $outcome.StdErr }
    $terminal = $outcome.StdOut.Trim() | ConvertFrom-Json
    if ($terminal.state -ne "complete" -or $terminal.phase -ne "done") {
        throw "Watcher returned the wrong terminal state"
    }

    $invalid = Join-Path $tmp "invalid"
    [void](New-Item -ItemType Directory -Path $invalid)
    $invalidReady = Join-Path $invalid "watcher.ready"
    Publish-StatusAtomic $invalid @(
        "state=running", "updated=2026-07-19T00:01:00+08:00", "phase=train",
        "run_root=$invalid", "run_id=invalid"
    )
    $process = Start-Watcher $invalid $invalidReady
    try {
        Wait-Ready $invalidReady
        Publish-StatusAtomic $invalid @(
            "state=unknown", "updated=2026-07-19T00:01:01+08:00", "phase=invalid",
            "run_root=$invalid", "run_id=invalid"
        )
        $outcome = Wait-Exit $process
    } finally {
        if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit() }
        $process.Dispose()
    }
    if ($outcome.ExitCode -eq 0 -or $outcome.StdErr -notmatch "Unknown status state") {
        throw "Watcher did not reject unknown state correctly"
    }
} finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force
    }
}

Write-Output "HMASD_MONITOR_WATCHER_OK"
