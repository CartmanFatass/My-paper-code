param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 39041,
    [int]$TotalTimesteps = 12800,
    [int]$NumEnvs = 16,
    [int]$RolloutLength = 40,
    [int]$EvalEpisodes = 32,
    [string]$Device = "cuda"
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$Analyzer = Join-Path $PSScriptRoot "analyze_r39_toy_native_categorical.py"
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellBin = (Get-Process -Id $PID).Path
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir (
        "logs\r39_toy_native_categorical_12k8_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    )
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$ExpectedUpdates = [int]($TotalTimesteps / ($NumEnvs * $RolloutLength))
$GitCommit = (& git -C $RepoDir rev-parse HEAD).Trim()
$Arms = @(
    [pscustomobject]@{
        Id = "adaptive_retention"
        Config = "ha_ctse_process.config_r39_toy_native_categorical"
    },
    [pscustomobject]@{
        Id = "force_refresh"
        Config = "ha_ctse_process.config_r39_toy_shared_refresh"
    }
)

$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

function Write-Status([string]$State, [string]$Phase, [string[]]$Details = @()) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=EXP-20260715-r39-toy-native-categorical",
        "git_commit=$GitCommit",
        "seed=$Seed",
        "run_root=$RunRoot",
        "arms=adaptive_retention,force_refresh",
        "scenario=two_timescale_role_free_actions",
        "device=$Device",
        "num_envs_per_arm=$NumEnvs",
        "total_timesteps_per_arm=$TotalTimesteps",
        "rollout_length=$RolloutLength",
        "expected_outer_updates=$ExpectedUpdates",
        "skill_interval=5",
        "eval_episodes=$EvalEpisodes",
        "eval_action_mode=stochastic",
        "eval_max_steps=40"
    ) + $Details
    $temporary = "$StatusPath.tmp.$PID"
    [System.IO.File]::WriteAllLines($temporary, $lines)
    $lastError = $null
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        try {
            if ([System.IO.File]::Exists($StatusPath)) {
                [System.IO.File]::Replace($temporary, $StatusPath, $null)
            }
            else {
                [System.IO.File]::Move($temporary, $StatusPath)
            }
            return
        }
        catch {
            $lastError = $_.Exception
            Start-Sleep -Milliseconds 100
        }
    }
    throw "Could not replace runner status: $($lastError.Message)"
}

function Training-Arguments([string]$Config, [string]$LogDir) {
    return @(
        "-m", "ha_ctse_process.train",
        "--config", $Config,
        "--scenario", "two_timescale_role_free_actions",
        "--seed", [string]$Seed,
        "--n_agents", "2",
        "--collector_backend", "subproc",
        "--collector_start_method", "spawn",
        "--num_envs", [string]$NumEnvs,
        "--rollout_length", [string]$RolloutLength,
        "--skill_interval", "5",
        "--total_timesteps", [string]$TotalTimesteps,
        "--eval_interval", [string]$TotalTimesteps,
        "--eval_episodes", [string]$EvalEpisodes,
        "--eval_max_steps", "40",
        "--eval_action_mode", "stochastic",
        "--save_interval", "0",
        "--checkpoint_keep_last", "1",
        "--plot_interval", "0",
        "--high_controller", "r30_fixed_clock_ar_edit",
        "--device", $Device,
        "--log_dir", $LogDir
    )
}

function Start-Worker([object]$Arm) {
    $logRoot = Join-Path $RunRoot "runs\$($Arm.Id)\seed$Seed"
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    $arguments = Training-Arguments $Arm.Config $logRoot
    [System.IO.File]::WriteAllText(
        (Join-Path $logRoot "command.txt"),
        "$PythonBin $($arguments -join ' ')"
    )
    $exitCodePath = Join-Path $logRoot "worker_exit_code.txt"
    $specPath = Join-Path $logRoot "worker_spec.json"
    $spec = [ordered]@{
        python_bin = $PythonBin
        working_directory = $RepoDir
        stdout_path = (Join-Path $logRoot "runner_stdout.log")
        stderr_path = (Join-Path $logRoot "runner_stderr.log")
        exit_code_path = $exitCodePath
        arguments = $arguments
    }
    [System.IO.File]::WriteAllText(
        $specPath,
        ($spec | ConvertTo-Json -Depth 4),
        [System.Text.UTF8Encoding]::new($false)
    )
    $process = Start-Process `
        -FilePath $PowerShellBin `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $WorkerWrapper,
            "-SpecPath", $specPath
        ) `
        -WorkingDirectory $RepoDir `
        -RedirectStandardOutput (Join-Path $logRoot "worker_wrapper_stdout.log") `
        -RedirectStandardError (Join-Path $logRoot "worker_wrapper_stderr.log") `
        -WindowStyle Hidden `
        -PassThru
    return [pscustomobject]@{
        Id = $Arm.Id
        Config = $Arm.Config
        Process = $process
        LogRoot = $logRoot
        ExitCodePath = $exitCodePath
        Completed = $false
    }
}

function Progress-Details([object[]]$Workers) {
    $details = @()
    foreach ($worker in $Workers) {
        $prefix = [string]$worker.Id
        $details += "${prefix}_pid=$($worker.Process.Id)"
        $details += "${prefix}_config=$($worker.Config)"
        $details += "${prefix}_log_root=$($worker.LogRoot)"
        $details += "${prefix}_worker_state=$(if ($worker.Process.HasExited) { 'exited' } else { 'running' })"
        $csvPath = Join-Path $worker.LogRoot "metrics\train_updates.csv"
        if (Test-Path -LiteralPath $csvPath) {
            try {
                $row = Import-Csv -LiteralPath $csvPath | Select-Object -Last 1
                if ($null -ne $row) {
                    $details += "${prefix}_update=$($row.update)"
                    $details += "${prefix}_total_steps=$($row.total_steps)"
                    $details += "${prefix}_full_sync_set_rate=$($row.r30_full_sync_set_rate)"
                    $details += "${prefix}_mixed_age_fraction=$($row.r30_mixed_age_fraction)"
                }
            }
            catch {
                $details += "${prefix}_progress_read=retry_next_poll"
            }
        }
    }
    return $details
}

function Wait-Workers([object[]]$Workers) {
    $failed = @()
    while ($true) {
        $running = 0
        foreach ($worker in $Workers) {
            if ($worker.Completed) {
                continue
            }
            if ($worker.Process.HasExited) {
                $worker.Process.WaitForExit()
                $exitCode = $null
                for ($attempt = 0; $attempt -lt 50; $attempt++) {
                    if (Test-Path -LiteralPath $worker.ExitCodePath) {
                        $raw = (Get-Content -Raw -LiteralPath $worker.ExitCodePath).Trim()
                        $parsed = 0
                        if ([int]::TryParse($raw, [ref]$parsed)) {
                            $exitCode = $parsed
                        }
                        break
                    }
                    Start-Sleep -Milliseconds 100
                }
                if ($null -eq $exitCode) {
                    $failed += "$($worker.Id):missing-exit-status"
                }
                elseif ($exitCode -ne 0) {
                    $failed += "$($worker.Id):$exitCode"
                }
                $worker.Completed = $true
            }
            else {
                $running += 1
            }
        }
        Write-Status "running" "training" (Progress-Details $Workers)
        if ($running -eq 0) {
            break
        }
        Start-Sleep -Seconds 15
    }
    foreach ($worker in $Workers) {
        $worker.Process.Dispose()
    }
    if ($failed.Count -gt 0) {
        throw "training worker failure: $($failed -join ', ')"
    }
}

try {
    if ($TotalTimesteps -le 0 -or $NumEnvs -le 0 -or $RolloutLength -le 0) {
        throw "timesteps, num_envs, and rollout_length must be positive"
    }
    if ($Device -cne "cuda") {
        throw "R39 toy gate requires Device exactly 'cuda', got '$Device'"
    }
    if ($TotalTimesteps % ($NumEnvs * $RolloutLength) -ne 0) {
        throw "total_timesteps must be divisible by num_envs * rollout_length"
    }
    if (Test-Path -LiteralPath $StatusPath) {
        throw "RunRoot already contains runner_status.txt: $RunRoot"
    }
    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
    Write-Status "running" "launching"
    $workers = @($Arms | ForEach-Object { Start-Worker $_ })
    Write-Status "running" "training" (Progress-Details $workers)
    Wait-Workers $workers

    Write-Status "running" "pair_analysis"
    & $PythonBin $Analyzer `
        --run-root $RunRoot `
        --seed $Seed `
        --total-timesteps $TotalTimesteps `
        --expected-updates $ExpectedUpdates `
        --eval-episodes $EvalEpisodes
    if ($LASTEXITCODE -ne 0) {
        throw "R39 toy pair analysis failed with exit code $LASTEXITCODE"
    }
    $resultPath = Join-Path $RunRoot "result\r39_toy_native_categorical.json"
    $result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
    Write-Status "completed" "result" @(
        "result_status=$($result.status)",
        "implementation_valid=$($result.implementation_valid)",
        "dense_access_passed=$($result.gates.M1_dense_access.passed)",
        "temporal_semantics_passed=$($result.gates.M2_temporal_semantics.passed)",
        "result_json=$resultPath"
    )
}
catch {
    $message = [string]$_.Exception.Message
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status "failed" "runner" @("error=$message")
    }
    throw
}
