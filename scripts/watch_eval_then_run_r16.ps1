param(
    [Parameter(Mandatory = $true)]
    [int]$EvalPid,
    [string]$EvalLogDir = "logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_014614\seed1\a2r_roster_reward_coef01",
    [int]$TargetSteps = 320000,
    [int]$TargetEpisodes = 20,
    [int]$PollSeconds = 60,
    [int]$MaxWaitHours = 12,
    [int]$RunnerTotalTimesteps = 960000,
    [string]$RunnerScript = "scripts\run_r16_a2r_overnight_local_cuda.ps1"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$watchRoot = Join-Path "logs\ha_ctse_r16_a2r_overnight_local_cuda" "watchers"
New-Item -ItemType Directory -Path $watchRoot -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$watchLog = Join-Path $watchRoot "watch_eval_then_run_$stamp.log"
$runnerLog = Join-Path $watchRoot "watch_eval_then_run_$stamp.runner.log"
$statusFile = Join-Path $watchRoot "watch_eval_then_run_$stamp.status.txt"

function Write-WatchLog {
    param([string]$Message)
    $line = "$(Get-Date -Format o) $Message"
    $line | Tee-Object -FilePath $watchLog -Append
}

function Get-EvalEpisodeCount {
    param(
        [string]$LogDir,
        [int]$Steps
    )
    $evalCsv = Join-Path $LogDir "metrics\eval_episodes.csv"
    if (-not (Test-Path $evalCsv)) {
        return 0
    }
    try {
        $rows = Import-Csv $evalCsv
        return @($rows | Where-Object { "$($_.total_steps)" -eq "$Steps" }).Count
    } catch {
        Write-WatchLog "WARN failed to read eval CSV: $($_.Exception.Message)"
        return 0
    }
}

Write-WatchLog "watch_start eval_pid=$EvalPid eval_log_dir=$EvalLogDir target_steps=$TargetSteps target_episodes=$TargetEpisodes runner_total_timesteps=$RunnerTotalTimesteps"
$deadline = (Get-Date).AddHours($MaxWaitHours)

while ($true) {
    $proc = Get-Process -Id $EvalPid -ErrorAction SilentlyContinue
    $count = Get-EvalEpisodeCount -LogDir $EvalLogDir -Steps $TargetSteps
    if ($proc) {
        Write-WatchLog "eval_running pid=$EvalPid target_eval_episodes=$count/$TargetEpisodes"
        if ((Get-Date) -gt $deadline) {
            Write-WatchLog "watch_timeout eval still running after ${MaxWaitHours}h; runner will not start"
            @(
                "finished=$(Get-Date -Format o)"
                "status=timeout"
                "eval_pid=$EvalPid"
                "eval_episodes=$count/$TargetEpisodes"
                "runner_started=0"
            ) | Set-Content -Path $statusFile -Encoding UTF8
            exit 2
        }
        Start-Sleep -Seconds $PollSeconds
        continue
    }

    Write-WatchLog "eval_process_finished pid=$EvalPid final_target_eval_episodes=$count/$TargetEpisodes"
    break
}

if (-not (Test-Path $RunnerScript)) {
    Write-WatchLog "ERROR runner script not found: $RunnerScript"
    @(
        "finished=$(Get-Date -Format o)"
        "status=missing_runner"
        "eval_pid=$EvalPid"
        "runner_started=0"
    ) | Set-Content -Path $statusFile -Encoding UTF8
    exit 3
}

Write-WatchLog "runner_start script=$RunnerScript total_timesteps=$RunnerTotalTimesteps continue_on_error=1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File $RunnerScript `
    -TotalTimesteps $RunnerTotalTimesteps `
    -ContinueOnError 2>&1 | Tee-Object -FilePath $runnerLog
$exitCode = $LASTEXITCODE
Write-WatchLog "runner_finished exit_code=$exitCode runner_log=$runnerLog"

@(
    "finished=$(Get-Date -Format o)"
    "status=finished"
    "eval_pid=$EvalPid"
    "runner_started=1"
    "runner_exit_code=$exitCode"
    "watch_log=$watchLog"
    "runner_log=$runnerLog"
) | Set-Content -Path $statusFile -Encoding UTF8

exit $exitCode
