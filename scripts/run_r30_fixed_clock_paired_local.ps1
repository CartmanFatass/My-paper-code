param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 30031,
    [switch]$RetryR30Only,
    [string]$RetryTag = "retry1"
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$SourceCheckpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_final.pt"
$PairAnalyzer = Join-Path $PSScriptRoot "analyze_r30_fixed_clock_pair.py"
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellBin = (Get-Process -Id $PID).Path
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
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $WorkerWrapper,
            "-SpecPath", $specPath
        ) `
        -WorkingDirectory $RepoDir `
        -RedirectStandardOutput (Join-Path $LogRoot "worker_wrapper_stdout.log") `
        -RedirectStandardError (Join-Path $LogRoot "worker_wrapper_stderr.log") `
        -WindowStyle Hidden `
        -PassThru
    return [pscustomobject]@{
        Id = $Id
        Process = $process
        ExitCodePath = $exitCodePath
        Completed = $false
    }
}

function Wait-Workers([object[]]$Workers) {
    $failed = @()
    while ($true) {
        $running = @()
        foreach ($worker in $Workers) {
            if ($worker.Completed) {
                continue
            }
            if ($worker.Process.HasExited) {
                $worker.Process.WaitForExit()
                $exitCode = $null
                for ($attempt = 0; $attempt -lt 50; $attempt++) {
                    if (Test-Path -LiteralPath $worker.ExitCodePath) {
                        $rawExitCode = (
                            Get-Content -Raw -LiteralPath $worker.ExitCodePath
                        ).Trim()
                        $parsedExitCode = 0
                        if ([int]::TryParse($rawExitCode, [ref]$parsedExitCode)) {
                            $exitCode = $parsedExitCode
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
                $running += $worker
            }
        }
        if ($running.Count -eq 0) {
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

function Analyze-Pair([string]$R30ArmRoot = "") {
    Write-Status "running" "pair_analysis"
    $arguments = @("--run-root", $RunRoot, "--seed", [string]$Seed)
    if ($R30ArmRoot) {
        $arguments += @("--r30-arm-root", $R30ArmRoot)
    }
    & $PythonBin $PairAnalyzer @arguments
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
    if (-not (Test-Path -LiteralPath $SourceCheckpoint)) {
        throw "Source checkpoint is missing: $SourceCheckpoint"
    }
    if ($RetryR30Only) {
        if (-not (Test-Path -LiteralPath $RunRoot)) {
            throw "Retry RunRoot is missing: $RunRoot"
        }
        $legacyRoot = Join-Path $RunRoot "runs\legacy_duration\seed$Seed"
        $legacyCheckpoint = Join-Path $legacyRoot "standalone_process_core_final.pt"
        if (-not (Test-Path -LiteralPath $legacyCheckpoint)) {
            throw "Completed legacy arm is missing: $legacyCheckpoint"
        }
        $retryRoot = Join-Path $RunRoot "runs\r30_fixed_clock_ar_edit_$RetryTag\seed$Seed"
        if (Test-Path -LiteralPath $retryRoot) {
            throw "R30 retry root already exists: $retryRoot"
        }
        Write-Status "running" "r30_retry_training" @(
            "retry_tag=$RetryTag",
            "r30_log_root=$retryRoot"
        )
        $worker = Start-Worker `
            -Id "r30_fixed_clock_ar_edit_$RetryTag" `
            -Arguments (Training-Arguments "r30_fixed_clock_ar_edit" $retryRoot) `
            -LogRoot $retryRoot
        Write-Status "running" "r30_retry_training" @(
            "retry_tag=$RetryTag",
            "r30_pid=$($worker.Process.Id)",
            "r30_log_root=$retryRoot"
        )
        Wait-Workers @($worker)
        Analyze-Pair -R30ArmRoot $retryRoot
        return
    }
    if (Test-Path -LiteralPath $RunRoot) {
        throw "RunRoot already exists: $RunRoot"
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
    Analyze-Pair
}
catch {
    $message = [string]$_.Exception.Message
    if (Test-Path -LiteralPath $RunRoot) {
        Write-Status "failed" "runner" @("error=$message")
    }
    throw
}
