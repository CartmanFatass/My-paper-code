<#
.SYNOPSIS
    Preflight a long HMASD analysis run, and report its true terminal state, so
    that "finished" means "artifact exists" rather than "the child said so".

.DESCRIPTION
    Two orphaned runs this session shared one cause: a background run launched
    from inside a turn died when that turn ended, leaving a 0-byte log and an
    empty output directory, and was reported as "build complete".

    THIS SCRIPT DOES NOT LAUNCH THE RUN, and that is a finding, not an omission.
    Measured 2026-07-28 on this machine:

      * Start-Process from the PowerShell tool  -> child dead within seconds
      * bash `nohup ... &` from the PowerShell tool -> child dead within seconds
      * bash `nohup ... &` from the Bash tool with run_in_background -> SURVIVES

    The surviving path is the harness's own background facility, which no script
    can invoke on its own behalf. A script that pretended to detach would
    reproduce exactly the orphan it exists to prevent, so this one refuses to
    pretend: -Mode Preflight prepares and hands back the exact command, and the
    caller runs it through a backgrounded Bash call.

    -Mode Preflight
        Routes the timing question through check_compute_free.ps1, creates the
        stamped run directory, writes a manifest, and returns the exact command
        to run. Refuses when compute is not free.

    -Mode Status
        Classifies RUNNING / COMPLETED / CRASHED / VANISHED by finding the
        process whose COMMAND LINE contains this run directory -- not by a
        recorded pid, so it works no matter how the run was started and cannot
        be fooled by pid reuse. VANISHED is the orphan signature and is never
        reported as COMPLETED.

    The interpreter is pinned: bare `python` here is a WindowsApps stub, and a
    setup step that silently no-ops has already produced a false green.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Preflight', 'Status')][string]$Mode,
    [string]$Script = 'scripts/audit_d7_s_event_aligned.py',
    [string]$ScriptArgs = '',
    [string]$Tag = 'run',
    [string]$RunDir,
    [switch]$IgnoreComputeBusy
)

$ErrorActionPreference = 'Stop'
$interpreter = 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe'
$repo = Split-Path -Parent $PSScriptRoot
function Write-Result($obj) { $obj | ConvertTo-Json -Depth 5 }

if ($Mode -eq 'Status') {
    if (-not $RunDir) { throw '-RunDir is required for -Mode Status' }
    $normalised = $RunDir -replace '\\', '/'
    $dir = Join-Path $repo $normalised
    if (-not (Test-Path -LiteralPath $dir)) {
        Write-Result ([ordered]@{ status = 'VANISHED'; run_dir = $RunDir
            reason = "Run directory does not exist: $RunDir" }); exit 1
    }

    $stdout = Join-Path $dir 'stdout.json'
    $stderr = Join-Path $dir 'stderr.log'
    $stdoutBytes = if (Test-Path -LiteralPath $stdout) { (Get-Item $stdout).Length } else { 0 }
    $stderrBytes = if (Test-Path -LiteralPath $stderr) { (Get-Item $stderr).Length } else { 0 }

    # Identify by command line, not by pid. A recorded pid is wrong for a run
    # someone launched by hand, and a reused pid is worse than no pid at all.
    $leaf = Split-Path $normalised -Leaf
    $match = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine.Replace('\', '/') -like "*$leaf*" })
    $alive = $match.Count -gt 0

    $tail = if ($stderrBytes -gt 0) { (Get-Content -LiteralPath $stderr -Tail 40) -join "`n" } else { '' }
    $crashed = $tail -match 'Traceback \(most recent call last\)|MemoryError|CUDA out of memory|Killed'

    # SIZE, never existence: a redirect target is created the instant a process
    # starts and survives a process that wrote nothing. Checking existence is how
    # an already-dead run reads as finished.
    $status = if ($alive) { 'RUNNING' }
        elseif ($stdoutBytes -gt 0) { 'COMPLETED' }
        elseif ($crashed) { 'CRASHED' }
        else { 'VANISHED' }

    $result = [ordered]@{
        status = $status; run_dir = $RunDir
        pids = @($match | ForEach-Object { $_.ProcessId })
        stdout_bytes = $stdoutBytes; stderr_bytes = $stderrBytes
        last_progress = if ($stderrBytes -gt 0) { (Get-Content -LiteralPath $stderr -Tail 1) } else { '' }
    }
    if ($status -eq 'VANISHED') {
        $result.reason = 'No process holds this run directory, no artifact was written, and nothing in the log looks like a crash. This is the ORPHAN signature -- the run most likely died with the turn that launched it. Do not report it as completed, and do not treat the log as evidence of a result.'
    }
    if ($status -eq 'CRASHED') { $result.crash_tail = $tail }
    Write-Result $result
    if ($status -in @('RUNNING', 'COMPLETED')) { exit 0 } else { exit 1 }
}

# --- Preflight ---------------------------------------------------------------
if (-not $IgnoreComputeBusy) {
    $freeCheck = Join-Path $repo 'scripts/check_compute_free.ps1'
    if (Test-Path -LiteralPath $freeCheck) {
        $free = (& powershell -NoProfile -ExecutionPolicy Bypass -File $freeCheck 2>&1 | Out-String)
        if ($free -notmatch 'COMPUTE_FREE') {
            Write-Result ([ordered]@{
                status = 'PREFLIGHT_REFUSED'
                reason = "check_compute_free.ps1 did not report COMPUTE_FREE. Read heavy_pids before deciding: another line's run means wake in an hour and re-check; our own run means wait on its completion instead of sleeping beside it."
            })
            exit 1
        }
    }
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDirRel = "logs/${Tag}_${stamp}"
$dir = Join-Path $repo $runDirRel
New-Item -ItemType Directory -Path $dir -Force | Out-Null

$commit = (& git -C $repo rev-parse --short HEAD 2>$null)
$manifest = [ordered]@{
    tag = $Tag; run_dir = $runDirRel; interpreter = $interpreter
    script = $Script; script_args = $ScriptArgs
    stage_commit = if ($commit) { $commit.Trim() } else { 'unknown' }
    prepared = (Get-Date).ToString('s')
}
[System.IO.File]::WriteAllText((Join-Path $dir 'run_manifest.json'),
    ($manifest | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))

$argPart = if ($ScriptArgs) { " $ScriptArgs" } else { '' }
$command = "nohup '$($interpreter -replace '\\', '/')' $Script$argPart --out $runDirRel > $runDirRel/stdout.json 2> $runDirRel/stderr.log &"

Write-Result ([ordered]@{
    status = 'PREFLIGHT_OK'; run_dir = $runDirRel; stage_commit = $manifest.stage_commit
    command = $command
    how_to_run = 'Run this through the Bash tool with run_in_background enabled. That is the only detach path measured to survive here: Start-Process and a nohup issued from PowerShell were both killed when the tool call returned.'
    then = "Poll with: launch_and_watch_run.ps1 -Mode Status -RunDir $runDirRel"
})
exit 0
