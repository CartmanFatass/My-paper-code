param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 30031,
    [int]$TotalTimesteps = 64000,
    [int]$NumEnvs = 16,
    [int]$RolloutLength = 80,
    [int]$EvalEpisodes = 40
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$Analyzer = Join-Path $PSScriptRoot "analyze_r30_alice_bob_pair.py"
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellBin = (Get-Process -Id $PID).Path
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir (
        "logs\r30_alice_bob_paired_64k_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    )
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$ExpectedUpdates = [int]($TotalTimesteps / ($NumEnvs * $RolloutLength))
$GitCommit = (& git -C $RepoDir rev-parse HEAD).Trim()
$Arms = @(
    [pscustomobject]@{
        Id = "adaptive_keep_set"
        Config = "ha_ctse_process.config_alice_bob_asymmetric"
    },
    [pscustomobject]@{
        Id = "shared_k_refresh"
        Config = "ha_ctse_process.config_alice_bob_shared_k"
    }
)
$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

function Write-Status([string]$State, [string]$Phase, [string[]]$Details = @()) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=EXP-20260714-r30-alice-bob-paired-64k",
        "git_commit=$GitCommit",
        "seed=$Seed",
        "run_root=$RunRoot",
        "arms=adaptive_keep_set,shared_k_refresh",
        "device=cuda",
        "num_envs_per_arm=$NumEnvs",
        "total_timesteps_per_arm=$TotalTimesteps",
        "rollout_length=$RolloutLength",
        "expected_updates=$ExpectedUpdates",
        "skill_interval=10",
        "eval_episodes=$EvalEpisodes",
        "eval_max_steps=80"
    ) + $Details
    $temporary = "$StatusPath.tmp.$PID"
    [System.IO.File]::WriteAllLines($temporary, $lines)
    [System.IO.File]::Move($temporary, $StatusPath, $true)
}

function Training-Arguments([string]$Config, [string]$LogDir) {
    return @(
        "-m", "ha_ctse_process.train",
        "--config", $Config,
        "--scenario", "alice_bob_asymmetric_cycles",
        "--seed", [string]$Seed,
        "--n_agents", "2",
        "--collector_backend", "subproc",
        "--collector_start_method", "spawn",
        "--num_envs", [string]$NumEnvs,
        "--rollout_length", [string]$RolloutLength,
        "--skill_interval", "10",
        "--total_timesteps", [string]$TotalTimesteps,
        "--eval_interval", [string]$TotalTimesteps,
        "--eval_episodes", [string]$EvalEpisodes,
        "--eval_max_steps", "80",
        "--eval_action_mode", "deterministic",
        "--save_interval", "0",
        "--checkpoint_keep_last", "1",
        "--plot_interval", "0",
        "--high_controller", "r30_fixed_clock_ar_edit",
        "--device", "cuda",
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
                    $details += "${prefix}_cycle_match=$($row.alice_bob_r30_observed_cycle_action_match_rate)"
                    $details += "${prefix}_transition_residual_mi=$($row.transition_skill_residual_mi_mean)"
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
        --eval-episodes $EvalEpisodes `
        --n-agents 2
    if ($LASTEXITCODE -ne 0) {
        throw "Alice--Bob pair analysis failed with exit code $LASTEXITCODE"
    }
    $resultPath = Join-Path $RunRoot "result\alice_bob_pair.json"
    $result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
    Write-Status "completed" "result" @(
        "result_status=$($result.status)",
        "implementation_valid=$($result.implementation_valid)",
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
