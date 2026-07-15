param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 38031,
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [int]$RolloutLength = 80,
    [int]$EvalEpisodes = 64
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$Analyzer = Join-Path $PSScriptRoot "analyze_r37_actor_visible_identity_access.py"
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellBin = (Get-Process -Id $PID).Path
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir (
        "logs\r37_actor_visible_identity_access_320k_" +
        (Get-Date -Format "yyyyMMdd_HHmmss")
    )
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$MaskedConfig = "ha_ctse_process.config_alice_bob_identity_masked"
$VisibleConfig = "ha_ctse_process.config_alice_bob_identity_visible"
$InitLogRoot = Join-Path $RunRoot "init\neutral_identity_masked_seed$Seed"
$InitCheckpoint = Join-Path $InitLogRoot "standalone_process_core_final.pt"
$ExpectedUpdates = [int]($TotalTimesteps / ($NumEnvs * $RolloutLength))
$GitCommit = (& git -C $RepoDir rev-parse HEAD).Trim()
$Arms = @(
    [pscustomobject]@{ Id = "identity_visible"; Config = $VisibleConfig },
    [pscustomobject]@{ Id = "identity_masked"; Config = $MaskedConfig }
)
$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

function Write-Status(
    [string]$State,
    [string]$Phase,
    [string[]]$Details = @()
) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=EXP-20260715-r37-actor-visible-identity-access",
        "git_commit=$GitCommit",
        "seed=$Seed",
        "run_root=$RunRoot",
        "arms=identity_visible,identity_masked",
        "identity_visible_config=$VisibleConfig",
        "identity_masked_config=$MaskedConfig",
        "common_init_config=$MaskedConfig",
        "common_init_steps=0",
        "common_init_checkpoint=$InitCheckpoint",
        "actor_obs_dim=16",
        "critic_state_dim=19",
        "device=cuda",
        "collector_backend=subproc",
        "collector_start_method=spawn",
        "num_envs_per_arm=$NumEnvs",
        "total_timesteps_per_arm=$TotalTimesteps",
        "rollout_length=$RolloutLength",
        "expected_low_updates=$ExpectedUpdates",
        "low_ppo_epochs=5",
        "low_sequence_length=10",
        "low_sequence_batch_size=64",
        "eval_action_mode=stochastic",
        "eval_episodes=$EvalEpisodes",
        "eval_max_steps=80",
        "bootstrap_repetitions=10000",
        "bootstrap_seed=40038031"
    ) + $Details
    [System.IO.File]::WriteAllLines($StatusPath, $lines)
}

function Init-Arguments() {
    return @(
        "-m", "ha_ctse_process.train",
        "--config", $MaskedConfig,
        "--scenario", "alice_bob_asymmetric_cycles",
        "--seed", [string]$Seed,
        "--n_agents", "2",
        "--collector_backend", "sync",
        "--num_envs", "1",
        "--rollout_length", [string]$RolloutLength,
        "--skill_interval", "10",
        "--total_timesteps", "0",
        "--eval_interval", "0",
        "--eval_episodes", "1",
        "--eval_max_steps", "80",
        "--eval_action_mode", "stochastic",
        "--save_interval", "0",
        "--checkpoint_keep_last", "1",
        "--plot_interval", "0",
        "--high_controller", "r30_fixed_clock_ar_edit",
        "--device", "cuda",
        "--log_dir", $InitLogRoot
    )
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
        "--eval_action_mode", "stochastic",
        "--save_interval", "0",
        "--checkpoint_keep_last", "1",
        "--plot_interval", "0",
        "--high_controller", "r30_fixed_clock_ar_edit",
        "--device", "cuda",
        "--resume_from", $InitCheckpoint,
        "--log_dir", $LogDir
    )
}

function Start-PythonWorker(
    [string]$Id,
    [string]$Config,
    [string]$LogRoot,
    [object[]]$Arguments
) {
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    [System.IO.File]::WriteAllText(
        (Join-Path $LogRoot "command.txt"),
        "$PythonBin $($Arguments -join ' ')"
    )
    $exitCodePath = Join-Path $LogRoot "worker_exit_code.txt"
    $specPath = Join-Path $LogRoot "worker_spec.json"
    $spec = [ordered]@{
        python_bin = $PythonBin
        working_directory = $RepoDir
        stdout_path = (Join-Path $LogRoot "runner_stdout.log")
        stderr_path = (Join-Path $LogRoot "runner_stderr.log")
        exit_code_path = $exitCodePath
        arguments = $Arguments
    }
    [System.IO.File]::WriteAllText(
        $specPath,
        ($spec | ConvertTo-Json -Depth 4),
        [System.Text.UTF8Encoding]::new($false)
    )
    $process = Start-Process `
        -FilePath $PowerShellBin `
        -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $WorkerWrapper,
            "-SpecPath", $specPath
        ) `
        -WorkingDirectory $RepoDir `
        -RedirectStandardOutput (Join-Path $LogRoot "worker_wrapper_stdout.log") `
        -RedirectStandardError (Join-Path $LogRoot "worker_wrapper_stderr.log") `
        -WindowStyle Hidden `
        -PassThru
    return [pscustomobject]@{
        Id = $Id
        Config = $Config
        Process = $process
        LogRoot = $LogRoot
        ExitCodePath = $exitCodePath
        Completed = $false
    }
}

function Start-ArmWorker([object]$Arm) {
    $logRoot = Join-Path $RunRoot "runs\$($Arm.Id)\seed$Seed"
    return Start-PythonWorker `
        -Id $Arm.Id `
        -Config $Arm.Config `
        -LogRoot $logRoot `
        -Arguments (Training-Arguments $Arm.Config $logRoot)
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
                    $details += "${prefix}_env_reward_mean=$($row.env_reward_mean)"
                    $details += "${prefix}_identity_audit_rows=$($row.r37_identity_audit_rows)"
                    $details += "${prefix}_identity_slot_error=$($row.r37_identity_slot_max_abs_error)"
                    $details += "${prefix}_critic_identity_error=$($row.r37_critic_identity_max_abs_error)"
                    $details += "${prefix}_low_policy_loss=$($row.low_policy_loss)"
                }
            }
            catch {
                $details += "${prefix}_progress_read=retry_next_poll"
            }
        }
    }
    return $details
}

function Wait-Workers([object[]]$Workers, [string]$Phase) {
    $failed = @()
    while ($true) {
        $running = 0
        foreach ($worker in $Workers) {
            if ($worker.Completed) { continue }
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
        Write-Status "running" $Phase (Progress-Details $Workers)
        if ($running -eq 0) { break }
        Start-Sleep -Seconds 15
    }
    foreach ($worker in $Workers) { $worker.Process.Dispose() }
    if ($failed.Count -gt 0) {
        throw "$Phase worker failure: $($failed -join ', ')"
    }
}

try {
    if ($Seed -ne 38031) { throw "R37 fixes seed at 38031" }
    if ($TotalTimesteps -ne 320000) {
        throw "R37 fixes total_timesteps at 320000 per arm"
    }
    if ($NumEnvs -ne 16 -or $RolloutLength -ne 80) {
        throw "R37 requires 16 environments per arm and rollout_length=80"
    }
    if ($EvalEpisodes -ne 64) {
        throw "R37 fixes stochastic final evaluation at 64 episodes"
    }
    if ($ExpectedUpdates -ne 250) {
        throw "R37 requires exactly 250 low updates"
    }
    if (Test-Path -LiteralPath $StatusPath) {
        throw "RunRoot already contains runner_status.txt: $RunRoot"
    }
    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null

    Write-Status "running" "neutral_init"
    $initWorker = Start-PythonWorker `
        -Id "neutral_init" `
        -Config $MaskedConfig `
        -LogRoot $InitLogRoot `
        -Arguments (Init-Arguments)
    Wait-Workers @($initWorker) "neutral_init"
    if (-not (Test-Path -LiteralPath $InitCheckpoint -PathType Leaf)) {
        throw "neutral 0-step init did not produce checkpoint: $InitCheckpoint"
    }

    Write-Status "running" "launching_pair" @("common_init_ready=true")
    $workers = @($Arms | ForEach-Object { Start-ArmWorker $_ })
    Write-Status "running" "training" (Progress-Details $workers)
    Wait-Workers $workers "training"

    Write-Status "running" "pair_analysis"
    & $PythonBin $Analyzer `
        --run-root $RunRoot `
        --init-checkpoint $InitCheckpoint `
        --seed $Seed `
        --total-timesteps $TotalTimesteps `
        --expected-updates $ExpectedUpdates `
        --eval-episodes $EvalEpisodes `
        --bootstrap-repetitions 10000 `
        --bootstrap-seed 40038031
    if ($LASTEXITCODE -ne 0) {
        throw "R37 pair analysis failed with exit code $LASTEXITCODE"
    }
    $resultPath = Join-Path $RunRoot "result\r37_actor_visible_identity_access.json"
    $result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
    Write-Status "completed" "result" @(
        "result_status=$($result.status)",
        "implementation_valid=$($result.implementation_valid)",
        "m1_access_passed=$($result.gates.m1_access.passed)",
        "m2_sparse_task_evidence_passed=$($result.gates.m2_sparse_task_evidence.passed)",
        "m3_stability_passed=$($result.gates.m3_stability.passed)",
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
