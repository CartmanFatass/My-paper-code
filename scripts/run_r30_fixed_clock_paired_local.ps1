param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 30031
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$SourceCheckpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_final.pt"
$PairAnalyzer = Join-Path $PSScriptRoot "analyze_r30_fixed_clock_pair.py"
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir ("logs\r30_fixed_clock_paired_320k_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$Arms = @("legacy_duration", "r30_fixed_clock_ar_edit")
$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

function Write-Status([string]$State, [string]$Phase, [string[]]$Details = @()) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=EXP-20260714-r30-fixed-clock-paired-320k",
        "seed=$Seed",
        "run_root=$RunRoot"
    ) + $Details
    $temporary = "$StatusPath.tmp.$PID"
    [System.IO.File]::WriteAllLines($temporary, $lines)
    Move-Item -LiteralPath $temporary -Destination $StatusPath -Force
}

function Start-Worker(
    [string]$Id,
    [string[]]$Arguments,
    [string]$LogRoot
) {
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    [System.IO.File]::WriteAllText(
        (Join-Path $LogRoot "command.txt"),
        "$PythonBin $($Arguments -join ' ')"
    )
    $process = Start-Process `
        -FilePath $PythonBin `
        -ArgumentList $Arguments `
        -WorkingDirectory $RepoDir `
        -RedirectStandardOutput (Join-Path $LogRoot "runner_stdout.log") `
        -RedirectStandardError (Join-Path $LogRoot "runner_stderr.log") `
        -WindowStyle Hidden `
        -PassThru
    return [pscustomobject]@{ Id = $Id; Process = $process }
}

function Wait-Workers([object[]]$Workers) {
    while ($true) {
        $failed = @()
        $running = @()
        foreach ($worker in $Workers) {
            if ($worker.Process.HasExited) {
                $worker.Process.WaitForExit()
                if ($worker.Process.ExitCode -ne 0) {
                    $failed += "$($worker.Id):$($worker.Process.ExitCode)"
                }
            }
            else {
                $running += $worker
            }
        }
        if ($failed.Count -gt 0) {
            foreach ($worker in $running) {
                Stop-Process -Id $worker.Process.Id -Force -ErrorAction SilentlyContinue
            }
            throw "training worker failure: $($failed -join ', ')"
        }
        if ($running.Count -eq 0) {
            break
        }
        Start-Sleep -Seconds 15
    }
    foreach ($worker in $Workers) {
        $worker.Process.Dispose()
    }
}

function Training-Arguments([string]$Arm, [string]$LogDir) {
    return @(
        "-m", "ha_ctse_process.train",
        "--config", "ha_ctse_process.config",
        "--scenario", "energy",
        "--preset", "S7-S1",
        "--seed", [string]$Seed,
        "--n_agents", "6",
        "--collector_backend", "subproc",
        "--collector_start_method", "spawn",
        "--num_envs", "16",
        "--rollout_length", "501",
        "--skill_interval", "10",
        "--skill_lifetime_candidates", "1,2,3,4",
        "--total_timesteps", "1320000",
        "--eval_interval", "320000",
        "--eval_episodes", "20",
        "--eval_action_mode", "deterministic",
        "--save_interval", "0",
        "--checkpoint_keep_last", "1",
        "--plot_interval", "0",
        "--low_ppo_epochs", "15",
        "--low_clip_epsilon", "0.1",
        "--smdp_bootstrap_coef", "0.25",
        "--edit_penalty_alpha", "0",
        "--switch_penalty_beta", "0",
        "--team_bridge_type", "deterministic_expected",
        "--high_controller", $Arm,
        "--r30_pair_gate",
        "--device", "cuda",
        "--resume_from", $SourceCheckpoint,
        "--log_dir", $LogDir
    )
}

try {
    if (Test-Path -LiteralPath $RunRoot) {
        throw "RunRoot already exists: $RunRoot"
    }
    if (-not (Test-Path -LiteralPath $SourceCheckpoint)) {
        throw "Source checkpoint is missing: $SourceCheckpoint"
    }
    New-Item -ItemType Directory -Path $RunRoot | Out-Null
    Write-Status "running" "training"

    $workers = @()
    foreach ($arm in $Arms) {
        $logDir = Join-Path $RunRoot "runs\$arm\seed$Seed"
        $workers += Start-Worker `
            -Id $arm `
            -Arguments (Training-Arguments $arm $logDir) `
            -LogRoot $logDir
    }
    Write-Status "running" "training" @(
        "legacy_pid=$($workers[0].Process.Id)",
        "r30_pid=$($workers[1].Process.Id)"
    )
    Wait-Workers $workers

    Write-Status "running" "pair_analysis"
    & $PythonBin $PairAnalyzer --run-root $RunRoot --seed $Seed
    if ($LASTEXITCODE -ne 0) {
        throw "R30 pair analysis failed with exit code $LASTEXITCODE"
    }
    $resultPath = Join-Path $RunRoot "result\r30_fixed_clock_pair.json"
    $result = Get-Content -Raw $resultPath | ConvertFrom-Json
    Write-Status "completed" "result" @(
        "result_status=$($result.status)",
        "result_json=$resultPath"
    )
    Write-Output "RUN_ROOT=$RunRoot"
    Write-Output "RESULT_STATUS=$($result.status)"
}
catch {
    $message = [string]$_.Exception.Message
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status "failed" "runner" @("error=$message")
    }
    throw
}
