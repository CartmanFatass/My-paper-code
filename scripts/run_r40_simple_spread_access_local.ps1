param(
    [string]$PythonExe = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [string]$Device = "cuda"
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellExe = (Get-Process -Id $PID).Path
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir (
        "logs\r40_simple_spread_access_200k_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    )
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$TrainRoot = Join-Path $RunRoot "runs\mappo\seed40041"
$ResultRoot = Join-Path $RunRoot "result"
$ResultPath = Join-Path $ResultRoot "r40_simple_spread_access.json"
$AnalyzerStdoutPath = Join-Path $ResultRoot "analyzer_stdout.log"
$AnalyzerStderrPath = Join-Path $ResultRoot "analyzer_stderr.log"
$GitCommit = (& git -C $RepoDir rev-parse HEAD).Trim()
$StatusOwned = $false

$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

$trainArgs = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config_r40_simple_spread",
    "--scenario", "simple_spread",
    "--seed", "40041",
    "--n_agents", "3",
    "--device", $Device,
    "--collector_backend", "subproc",
    "--collector_start_method", "spawn",
    "--num_envs", "16",
    "--rollout_length", "25",
    "--skill_interval", "25",
    "--total_timesteps", "200000",
    "--eval_interval", "200000",
    "--eval_episodes", "256",
    "--eval_action_mode", "stochastic",
    "--eval_max_steps", "25",
    "--eval_seed_blocks", "40042,40043,40044,40045",
    "--eval_episodes_per_seed", "64",
    "--save_interval", "0",
    "--checkpoint_keep_last", "1",
    "--plot_interval", "0",
    "--high_controller", "r30_fixed_clock_ar_edit",
    "--log_dir", $TrainRoot
)

$analyzerArgs = @(
    "-m", "scripts.analyze_r40_simple_spread_access",
    "--run-root", $RunRoot
)

function Write-Status(
    [string]$State,
    [string]$Phase,
    [string[]]$Details = @()
) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=EXP-20260715-r40-simple-spread-access",
        "git_commit=$GitCommit",
        "run_root=$RunRoot",
        "config=ha_ctse_process.config_r40_simple_spread",
        "scenario=simple_spread",
        "pettingzoo_version=1.24.3",
        "n_agents=3",
        "horizon=25",
        "local_ratio=0.0",
        "action_space=Discrete(5)",
        "seed=40041",
        "device=$Device",
        "train_root=$TrainRoot",
        "progress_source=$(Join-Path $TrainRoot 'metrics\train_updates.csv')",
        "collector_backend=subproc",
        "collector_start_method=spawn",
        "num_envs=16",
        "rollout_length=25",
        "total_timesteps=200000",
        "expected_outer_updates=500",
        "low_ppo_epochs=5",
        "low_sequence_length=25",
        "low_sequence_batch_size=64",
        "eval_action_mode=stochastic",
        "eval_seed_blocks=40042,40043,40044,40045",
        "eval_episodes_per_seed=64",
        "eval_episodes=256",
        "uniform_random_action_rng_seed=50041",
        "bootstrap_repetitions=10000",
        "bootstrap_seed=60041"
    ) + $Details
    [System.IO.File]::WriteAllLines($StatusPath, $lines)
}

function Invoke-PythonWorker(
    [string]$Id,
    [string]$LogRoot,
    [object[]]$Arguments,
    [string]$StdoutPath = "",
    [string]$StderrPath = ""
) {
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    if (-not $StdoutPath) {
        $StdoutPath = Join-Path $LogRoot "runner_stdout.log"
    }
    if (-not $StderrPath) {
        $StderrPath = Join-Path $LogRoot "runner_stderr.log"
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $LogRoot "command.txt"),
        "$PythonExe $($Arguments -join ' ')"
    )
    $exitCodePath = Join-Path $LogRoot "worker_exit_code.txt"
    $specPath = Join-Path $LogRoot "worker_spec.json"
    $spec = [ordered]@{
        python_bin = $PythonExe
        working_directory = $RepoDir
        stdout_path = $StdoutPath
        stderr_path = $StderrPath
        exit_code_path = $exitCodePath
        arguments = $Arguments
    }
    [System.IO.File]::WriteAllText(
        $specPath,
        ($spec | ConvertTo-Json -Depth 4),
        [System.Text.UTF8Encoding]::new($false)
    )
    $process = Start-Process `
        -FilePath $PowerShellExe `
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
        -Wait `
        -PassThru
    $wrapperExitCode = [int]$process.ExitCode
    $process.Dispose()
    if ($wrapperExitCode -ne 0) {
        throw "$Id worker wrapper failed with exit code $wrapperExitCode"
    }
    if (-not (Test-Path -LiteralPath $exitCodePath -PathType Leaf)) {
        throw "$Id worker did not write an exit code"
    }
    $workerExitCode = 0
    $rawExitCode = (Get-Content -Raw -LiteralPath $exitCodePath).Trim()
    if (-not [int]::TryParse($rawExitCode, [ref]$workerExitCode)) {
        throw "$Id worker wrote an invalid exit code: $rawExitCode"
    }
    if ($workerExitCode -ne 0) {
        throw "$Id worker failed with exit code $workerExitCode"
    }
}

try {
    if (Test-Path -LiteralPath $StatusPath) {
        throw "RunRoot already contains runner_status.txt: $RunRoot"
    }
    if ($Device -cne "cuda") {
        throw "R40 requires Device exactly 'cuda', got '$Device'"
    }
    $cudaProbeOutput = & $PythonExe -c (
        "import sys, torch; " +
        "available = torch.cuda.is_available(); " +
        "print(f'torch.cuda.is_available()={available}'); " +
        "sys.exit(0 if available == True else 1)"
    ) 2>&1
    if ($LASTEXITCODE -ne 0) {
        $cudaProbeText = ($cudaProbeOutput | Out-String).Trim()
        throw "R40 CUDA preflight failed: $cudaProbeText"
    }
    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
    $StatusOwned = $true

    Write-Status "running" "training"
    Invoke-PythonWorker "mappo" $TrainRoot $trainArgs

    Write-Status "running" "paired_random_and_analysis"
    New-Item -ItemType Directory -Path $ResultRoot -Force | Out-Null
    Invoke-PythonWorker "analyzer" $ResultRoot $analyzerArgs `
        $AnalyzerStdoutPath $AnalyzerStderrPath
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw "R40 analyzer did not produce $ResultPath"
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status "completed" "result" @(
        "result_status=$($result.status)",
        "implementation_valid=$($result.implementation_valid)",
        "m0_passed=$($result.gates.M0.passed)",
        "m1_passed=$($result.gates.M1.passed)",
        "m2_passed=$($result.gates.M2.passed)",
        "mappo_mean_return=$($result.gates.M1.mappo_mean_return)",
        "random_mean_return=$($result.gates.M1.random_mean_return)",
        "paired_lower_95=$($result.gates.M1.paired_difference_ci.lower_95)",
        "blocks_above_floor=$($result.gates.M2.blocks_above_floor)",
        "result_path=$ResultPath"
    )
}
catch {
    $message = [string]$_.Exception.Message
    $message = $message.Replace("`r", " ").Replace("`n", " ")
    if ($StatusOwned) {
        Write-Status "failed" "runner" @("error=$message")
    }
    throw
}
