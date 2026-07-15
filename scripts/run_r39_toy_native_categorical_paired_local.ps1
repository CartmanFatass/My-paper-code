param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 39041,
    [int]$TotalTimesteps = 12800,
    [int]$NumEnvs = 16,
    [int]$RolloutLength = 40,
    [int]$EvalEpisodes = 32,
    [string]$Device = "cuda",
    [string]$ExperimentId = "EXP-20260715-r39-toy-native-categorical",
    [string]$AdaptiveConfig = "ha_ctse_process.config_r39_toy_native_categorical",
    [string]$ControlConfig = "ha_ctse_process.config_r39_toy_shared_refresh",
    [string]$RunLabel = "r39_toy_native_categorical_12k8",
    [string]$ResultName = "r39_toy_native_categorical.json",
    [switch]$FixedPrimitives,
    [switch]$DirectStateContext,
    [switch]$HighExposurePair,
    [switch]$BlockCreditPair
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$Analyzer = Join-Path $PSScriptRoot "analyze_r39_toy_native_categorical.py"
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellBin = (Get-Process -Id $PID).Path
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir (
        "logs\$RunLabel`_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    )
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$ExpectedUpdates = [int]($TotalTimesteps / ($NumEnvs * $RolloutLength))
$GitCommit = (& git -C $RepoDir rev-parse HEAD).Trim()
if ($HighExposurePair -and $BlockCreditPair) {
    throw "HighExposurePair and BlockCreditPair are mutually exclusive"
}
if ($HighExposurePair) {
    $Arms = @(
        [pscustomobject]@{
            Id = "high_epoch1"
            Config = $AdaptiveConfig
        },
        [pscustomobject]@{
            Id = "high_epoch3"
            Config = $ControlConfig
        }
    )
}
elseif ($BlockCreditPair) {
    $Arms = @(
        [pscustomobject]@{
            Id = "smdp_gae"
            Config = $AdaptiveConfig
        },
        [pscustomobject]@{
            Id = "block_return"
            Config = $ControlConfig
        }
    )
}
else {
    $Arms = @(
        [pscustomobject]@{
            Id = "adaptive_retention"
            Config = $AdaptiveConfig
        },
        [pscustomobject]@{
            Id = "force_refresh"
            Config = $ControlConfig
        }
    )
}

$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

function Write-Status([string]$State, [string]$Phase, [string[]]$Details = @()) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=$ExperimentId",
        "git_commit=$GitCommit",
        "seed=$Seed",
        "run_root=$RunRoot",
        "arms=$((@($Arms | ForEach-Object { $_.Id })) -join ',')",
        "scenario=two_timescale_role_free_actions",
        "device=$Device",
        "num_envs_per_arm=$NumEnvs",
        "total_timesteps_per_arm=$TotalTimesteps",
        "rollout_length=$RolloutLength",
        "expected_outer_updates=$ExpectedUpdates",
        "high_exposure_pair=$([bool]$HighExposurePair)",
        "block_credit_pair=$([bool]$BlockCreditPair)",
        "skill_interval=5",
        "eval_episodes=$EvalEpisodes",
        "eval_action_mode=stochastic",
        "eval_max_steps=40"
    ) + $Details
    [System.IO.File]::WriteAllLines($StatusPath, $lines)
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
    $analyzerArgs = @(
        $Analyzer,
        "--run-root", $RunRoot,
        "--seed", [string]$Seed,
        "--total-timesteps", [string]$TotalTimesteps,
        "--expected-updates", [string]$ExpectedUpdates,
        "--eval-episodes", [string]$EvalEpisodes,
        "--experiment-id", $ExperimentId,
        "--adaptive-config", $AdaptiveConfig,
        "--control-config", $ControlConfig,
        "--result-name", $ResultName
    )
    if ($FixedPrimitives) {
        $analyzerArgs += "--fixed-primitives"
    }
    if ($DirectStateContext) {
        $analyzerArgs += "--direct-state-context"
    }
    if ($HighExposurePair) {
        $analyzerArgs += "--high-exposure-pair"
    }
    if ($BlockCreditPair) {
        $analyzerArgs += "--block-credit-pair"
    }
    & $PythonBin @analyzerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "R39 toy pair analysis failed with exit code $LASTEXITCODE"
    }
    $resultPath = Join-Path $RunRoot "result\$ResultName"
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
