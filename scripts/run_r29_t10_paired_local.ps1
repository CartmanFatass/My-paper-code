param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$Seed = 29031
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$SourceCheckpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_final.pt"
$PairAnalyzer = Join-Path $PSScriptRoot "analyze_r29_t10_pair.py"
$Collector = Join-Path $PSScriptRoot "collect_r26_g1_windows.py"
$R26Analyzer = Join-Path $PSScriptRoot "analyze_r26_g1_behavior.py"
$ReviewDir = Join-Path $RepoDir "docs\external-review\gpt5_6_pro\20260714_r29_t10_result"
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir ("logs\r29_t10_paired_320k_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
$StatusPath = Join-Path $RunRoot "runner_status.txt"
$Arms = @("probe_only", "real_reward")
$env:CUBLAS_WORKSPACE_CONFIG = ":4096:8"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"

function Write-Status([string]$State, [string]$Phase, [string[]]$Details = @()) {
    $lines = @(
        "updated=$([DateTimeOffset]::Now.ToString('o'))",
        "state=$State",
        "phase=$Phase",
        "experiment=EXP-20260714-r29-t10-paired-320k",
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

function Wait-Workers([object[]]$Workers, [string]$Phase) {
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
            throw "$Phase worker failure: $($failed -join ', ')"
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
        "--rollout_length", "500",
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
        "--reward_ratio_guard_mode", "kill",
        "--device", "cuda",
        "--resume_from", $SourceCheckpoint,
        "--r29_action_info_mode", $Arm,
        "--r29_action_info_coef", "0.05",
        "--r29_action_info_clip", "0.05",
        "--log_dir", $LogDir
    )
}

function Collector-Arguments([string]$Arm, [string]$Checkpoint, [string]$OutputDir) {
    return @(
        $Collector,
        "--checkpoint", $Checkpoint,
        "--output_dir", $OutputDir,
        "--config", "ha_ctse_process.config",
        "--scenario", "energy",
        "--preset", "S7-S1",
        "--seed", [string]$Seed,
        "--n_agents", "6",
        "--device", "cuda",
        "--skill_interval", "10",
        "--n_resets", "64",
        "--episode_max_steps", "500",
        "--checkpoint_id", "r29_t10_${Arm}_seed${Seed}_final",
        "--checkpoint_update", "72"
    )
}

function R26-Arguments([string]$InputDir, [string]$OutputDir) {
    return @(
        $R26Analyzer,
        "--input_dir", $InputDir,
        "--output_dir", $OutputDir,
        "--num_skills", "4",
        "--device", "cuda"
    )
}

function Copy-PackageFile([string]$Source, [string]$RelativeDestination, [string]$Staging) {
    $destination = Join-Path $Staging $RelativeDestination
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $destination
}

try {
    if (Test-Path -LiteralPath $RunRoot) {
        throw "RunRoot already exists: $RunRoot"
    }
    if (Test-Path -LiteralPath $ReviewDir) {
        throw "Review output already exists: $ReviewDir"
    }
    New-Item -ItemType Directory -Path $RunRoot | Out-Null
    Write-Status "running" "training"

    $trainingWorkers = @()
    foreach ($arm in $Arms) {
        $logDir = Join-Path $RunRoot "runs\$arm\seed$Seed"
        $trainingWorkers += Start-Worker `
            -Id "train:$arm" `
            -Arguments (Training-Arguments $arm $logDir) `
            -LogRoot $logDir
    }
    Write-Status "running" "training" @(
        "probe_pid=$($trainingWorkers[0].Process.Id)",
        "real_pid=$($trainingWorkers[1].Process.Id)"
    )
    Wait-Workers $trainingWorkers "training"

    Write-Status "running" "r26_collection"
    $collectorWorkers = @()
    foreach ($arm in $Arms) {
        $armRoot = Join-Path $RunRoot "runs\$arm\seed$Seed"
        $checkpoint = Join-Path $armRoot "standalone_process_core_final.pt"
        $evidenceRoot = Join-Path $RunRoot "evidence\$arm"
        $windowsDir = Join-Path $evidenceRoot "windows"
        $collectorWorkers += Start-Worker `
            -Id "collect:$arm" `
            -Arguments (Collector-Arguments $arm $checkpoint $windowsDir) `
            -LogRoot $evidenceRoot
    }
    Wait-Workers $collectorWorkers "R26 collection"

    Write-Status "running" "r26_analysis"
    $analysisWorkers = @()
    foreach ($arm in $Arms) {
        $evidenceRoot = Join-Path $RunRoot "evidence\$arm"
        $analysisDir = Join-Path $evidenceRoot "analysis"
        $analysisWorkers += Start-Worker `
            -Id "analyze:$arm" `
            -Arguments (R26-Arguments (Join-Path $evidenceRoot "windows") $analysisDir) `
            -LogRoot $analysisDir
    }
    Wait-Workers $analysisWorkers "R26 analysis"

    Write-Status "running" "pair_analysis"
    & $PythonBin $PairAnalyzer --run-root $RunRoot --seed $Seed
    if ($LASTEXITCODE -ne 0) {
        throw "R29-T10 pair analysis failed with exit code $LASTEXITCODE"
    }

    Write-Status "running" "review_package"
    $staging = Join-Path $RunRoot "review_package"
    New-Item -ItemType Directory -Path $staging | Out-Null
    Copy-PackageFile (Join-Path $RunRoot "result\GPT5_6_PRO_QUESTION.md") "GPT5_6_PRO_QUESTION.md" $staging
    Copy-PackageFile (Join-Path $RunRoot "result\r29_t10_pair.json") "results\r29_t10_pair.json" $staging
    Copy-PackageFile (Join-Path $RunRoot "result\r29_t10_pair.md") "results\r29_t10_pair.md" $staging
    Copy-PackageFile (Join-Path $RepoDir "memory\ALGORITHM_PRINCIPLES.md") "project\ALGORITHM_PRINCIPLES.md" $staging
    Copy-PackageFile (Join-Path $RepoDir "memory\CURRENT_WORK.md") "project\CURRENT_WORK.md" $staging
    Copy-PackageFile (Join-Path $RepoDir "memory\ExpRecord.md") "project\ExpRecord.md" $staging
    Copy-PackageFile (Join-Path $RepoDir "ha_ctse_process\r29_action_information.py") "code\r29_action_information.py" $staging
    Copy-PackageFile (Join-Path $RepoDir "ha_ctse_process\r29_action_information_reward.py") "code\r29_action_information_reward.py" $staging
    $priorReview = Join-Path $RepoDir "docs\external-review\gpt5_6_pro\20260713_r29_action_information"
    Copy-PackageFile (Join-Path $priorReview "RESEARCH_BACKGROUND.md") "prior_review\RESEARCH_BACKGROUND.md" $staging
    Copy-PackageFile (Join-Path $priorReview "RESPONSE_RAW.md") "prior_review\RESPONSE_RAW.md" $staging
    Copy-PackageFile (Join-Path $priorReview "DISPOSITION.md") "prior_review\DISPOSITION.md" $staging
    foreach ($arm in $Arms) {
        $armRoot = Join-Path $RunRoot "runs\$arm\seed$Seed"
        Copy-PackageFile (Join-Path $armRoot "metrics\train_updates.csv") "results\$arm\train_updates.csv" $staging
        Copy-PackageFile (Join-Path $armRoot "metrics\eval_episodes.csv") "results\$arm\eval_episodes.csv" $staging
        Copy-PackageFile (Join-Path $armRoot "metadata\run_manifest.json") "results\$arm\run_manifest.json" $staging
        $analysisRoot = Join-Path $RunRoot "evidence\$arm\analysis"
        Copy-PackageFile (Join-Path $analysisRoot "r26_g1_behavior.json") "results\$arm\r26_g1_behavior.json" $staging
        Copy-PackageFile (Join-Path $analysisRoot "r26_g1_behavior.md") "results\$arm\r26_g1_behavior.md" $staging
    }
    New-Item -ItemType Directory -Path $ReviewDir | Out-Null
    Copy-Item -LiteralPath (Join-Path $RunRoot "result\GPT5_6_PRO_QUESTION.md") -Destination $ReviewDir
    Copy-Item -LiteralPath (Join-Path $RunRoot "result\r29_t10_pair.json") -Destination $ReviewDir
    Copy-Item -LiteralPath (Join-Path $RunRoot "result\r29_t10_pair.md") -Destination $ReviewDir
    $zipPath = Join-Path $ReviewDir "HMASD_R29_T10_RESULT_20260714.zip"
    Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Status "succeeded" "complete" @(
        "result_json=$(Join-Path $RunRoot 'result\r29_t10_pair.json')",
        "review_question=$(Join-Path $ReviewDir 'GPT5_6_PRO_QUESTION.md')",
        "review_zip=$zipPath"
    )
}
catch {
    if (-not (Test-Path -LiteralPath $RunRoot)) {
        New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null
    }
    Write-Status "failed" "operational_failure" @("error=$($_.Exception.Message)")
    throw
}
