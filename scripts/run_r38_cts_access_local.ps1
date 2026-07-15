param(
    [string]$PythonExe = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [string]$Device = "cuda"
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$Analyzer = Join-Path $PSScriptRoot "analyze_r38_cts_access.py"
$WorkerWrapper = Join-Path $PSScriptRoot "run_python_worker.ps1"
$PowerShellExe = (Get-Process -Id $PID).Path
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir (
        "logs\r38_cts_access_320k_" + (Get-Date -Format "yyyyMMdd_HHmmss")
    )
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$InitRoot = Join-Path $RunRoot "init\neutral_cts_seed39031"
$NeutralCheckpoint = Join-Path $InitRoot "standalone_process_core_final.pt"
$MappoRoot = Join-Path $RunRoot "runs\constant_code_mappo\seed39031"
$ResultPath = Join-Path $RunRoot "result\r38_cts_access.json"
$AnalyzerStdoutPath = Join-Path $RunRoot "result\analyzer_stdout.log"
$AnalyzerStderrPath = Join-Path $RunRoot "result\analyzer_stderr.log"
$GitCommit = (& git -C $RepoDir rev-parse HEAD).Trim()
$StatusOwned = $false

$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

$initArgs = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config_r38_two_timescale_sparse",
    "--scenario", "cooperative_two_timescale_sparse",
    "--seed", "39031",
    "--n_agents", "2",
    "--collector_backend", "sync",
    "--num_envs", "1",
    "--rollout_length", "200",
    "--skill_interval", "10",
    "--total_timesteps", "0",
    "--eval_interval", "0",
    "--eval_episodes", "1",
    "--eval_max_steps", "200",
    "--eval_action_mode", "stochastic",
    "--save_interval", "0",
    "--checkpoint_keep_last", "1",
    "--plot_interval", "0",
    "--high_controller", "r30_fixed_clock_ar_edit",
    "--device", $Device,
    "--log_dir", $InitRoot
)

$trainArgs = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config_r38_two_timescale_sparse",
    "--scenario", "cooperative_two_timescale_sparse",
    "--seed", "39031",
    "--n_agents", "2",
    "--device", $Device,
    "--collector_backend", "subproc",
    "--collector_start_method", "spawn",
    "--num_envs", "16",
    "--rollout_length", "200",
    "--skill_interval", "10",
    "--total_timesteps", "320000",
    "--eval_interval", "320000",
    "--eval_episodes", "256",
    "--eval_action_mode", "stochastic",
    "--eval_max_steps", "200",
    "--save_interval", "0",
    "--checkpoint_keep_last", "1",
    "--plot_interval", "0",
    "--high_controller", "r30_fixed_clock_ar_edit",
    "--resume_from", $NeutralCheckpoint,
    "--log_dir", $MappoRoot
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
        "experiment=EXP-20260715-r38-cts-access",
        "git_commit=$GitCommit",
        "run_root=$RunRoot",
        "config=ha_ctse_process.config_r38_two_timescale_sparse",
        "scenario=cooperative_two_timescale_sparse",
        "seed=39031",
        "device=$Device",
        "neutral_init_checkpoint=$NeutralCheckpoint",
        "mappo_root=$MappoRoot",
        "collector_backend=subproc",
        "collector_start_method=spawn",
        "num_envs=16",
        "rollout_length=200",
        "total_timesteps=320000",
        "expected_outer_updates=100",
        "eval_action_mode=stochastic",
        "eval_episodes=256",
        "eval_reset_seed_first=139031",
        "eval_reset_seed_last=139286",
        "uniform_random_action_rng_seed=49031",
        "bootstrap_repetitions=10000",
        "bootstrap_seed=59031"
    ) + $Details
    [System.IO.File]::WriteAllLines($StatusPath, $lines)
}

function Invoke-PythonWorker(
    [string]$Id,
    [string]$LogRoot,
    [object[]]$Arguments
) {
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    [System.IO.File]::WriteAllText(
        (Join-Path $LogRoot "command.txt"),
        "$PythonExe $($Arguments -join ' ')"
    )
    $exitCodePath = Join-Path $LogRoot "worker_exit_code.txt"
    $specPath = Join-Path $LogRoot "worker_spec.json"
    $spec = [ordered]@{
        python_bin = $PythonExe
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
    $rawExitCode = (Get-Content -Raw -LiteralPath $exitCodePath).Trim()
    $workerExitCode = 0
    if (-not [int]::TryParse($rawExitCode, [ref]$workerExitCode)) {
        throw "$Id worker wrote an invalid exit code: $rawExitCode"
    }
    if ($workerExitCode -ne 0) {
        throw "$Id worker failed with exit code $workerExitCode"
    }
}

function Remove-AnalyzerResult {
    if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
        Remove-Item -LiteralPath $ResultPath -Force
    }
}

function Get-AnalyzerFailureText {
    if (Test-Path -LiteralPath $AnalyzerStderrPath -PathType Leaf) {
        $stderrText = (Get-Content -Raw -LiteralPath $AnalyzerStderrPath).Trim()
        if ($stderrText) {
            return $stderrText
        }
    }
    if (Test-Path -LiteralPath $AnalyzerStdoutPath -PathType Leaf) {
        $stdoutText = (Get-Content -Raw -LiteralPath $AnalyzerStdoutPath).Trim()
        if ($stdoutText) {
            return "stderr was empty; stdout: $stdoutText"
        }
    }
    return "analyzer stdout and stderr were empty"
}

try {
    if (Test-Path -LiteralPath $StatusPath) {
        throw "RunRoot already contains runner_status.txt: $RunRoot"
    }
    if ($Device -cne "cuda") {
        throw "R38 requires Device exactly 'cuda', got '$Device'"
    }
    $cudaProbeOutput = & $PythonExe -c (
        "import sys, torch; " +
        "available = torch.cuda.is_available(); " +
        "print(f'torch.cuda.is_available()={available}'); " +
        "sys.exit(0 if available == True else 1)"
    ) 2>&1
    $cudaProbeExitCode = $LASTEXITCODE
    if ($cudaProbeExitCode -ne 0) {
        $cudaProbeText = ($cudaProbeOutput | Out-String).Trim()
        throw (
            "R38 CUDA preflight failed for ${PythonExe}: " +
            "torch.cuda.is_available() != True " +
            "(exit_code=$cudaProbeExitCode; output=$cudaProbeText)"
        )
    }
    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
    $StatusOwned = $true
    Remove-AnalyzerResult

    Write-Status "running" "neutral_init"
    Invoke-PythonWorker "neutral_init" $InitRoot $initArgs
    if (-not (Test-Path -LiteralPath $NeutralCheckpoint -PathType Leaf)) {
        throw "neutral zero-step initialization did not produce $NeutralCheckpoint"
    }

    Write-Status "running" "training_mappo"
    Invoke-PythonWorker "constant_code_mappo" $MappoRoot $trainArgs

    Write-Status "running" "uniform_random_and_analysis"
    New-Item -ItemType Directory -Path (Split-Path -Parent $ResultPath) -Force |
        Out-Null
    try {
        & $PythonExe $Analyzer --run-root $RunRoot `
            1> $AnalyzerStdoutPath `
            2> $AnalyzerStderrPath
        $analyzerExitCode = $LASTEXITCODE
    }
    catch {
        $analyzerProcessError = [string]$_.Exception.Message
        $analyzerFailureText = Get-AnalyzerFailureText
        throw (
            "R38 analyzer process exception; " +
            "stdout_path=$AnalyzerStdoutPath; " +
            "stderr_path=$AnalyzerStderrPath; " +
            "error=$analyzerProcessError; " +
            "output=$analyzerFailureText"
        )
    }
    if ($analyzerExitCode -ne 0) {
        $analyzerFailureText = Get-AnalyzerFailureText
        throw (
            "R38 analyzer failed with exit code $analyzerExitCode; " +
            "stdout_path=$AnalyzerStdoutPath; " +
            "stderr_path=$AnalyzerStderrPath; " +
            "output=$analyzerFailureText"
        )
    }
    if (-not (Test-Path -LiteralPath $ResultPath -PathType Leaf)) {
        throw (
            "R38 analyzer did not produce $ResultPath; " +
            "stdout_path=$AnalyzerStdoutPath; " +
            "stderr_path=$AnalyzerStderrPath"
        )
    }
    $result = Get-Content -Raw -LiteralPath $ResultPath | ConvertFrom-Json
    Write-Status "completed" "result" @(
        "result_status=$($result.status)",
        "implementation_valid=$($result.implementation_valid)",
        "m0_passed=$($result.gates.M0.passed)",
        "m1_passed=$($result.gates.M1.passed)",
        "m2_passed=$($result.gates.M2.passed)",
        "result_path=$ResultPath",
        "analyzer_stdout_path=$AnalyzerStdoutPath",
        "analyzer_stderr_path=$AnalyzerStderrPath"
    )
}
catch {
    $message = [string]$_.Exception.Message
    $message = $message.Replace("`r", " ").Replace("`n", " ")
    if ($StatusOwned) {
        $failureDetails = @("error=$message")
        if (Test-Path -LiteralPath $AnalyzerStdoutPath -PathType Leaf) {
            $failureDetails += "analyzer_stdout_path=$AnalyzerStdoutPath"
        }
        if (Test-Path -LiteralPath $AnalyzerStderrPath -PathType Leaf) {
            $failureDetails += "analyzer_stderr_path=$AnalyzerStderrPath"
        }
        Remove-AnalyzerResult
        Write-Status "failed" "runner" $failureDetails
    }
    throw
}
