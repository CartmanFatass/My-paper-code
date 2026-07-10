<#
R24 overnight local CUDA resume runner (arms 5-7 only)
EXP-20260709-local-overnight-audit-power-r23-deconfound

Resume after interruption at ~16:20: arms 1-4 complete, arm5-7 resume.
Arm5 was killed ~10 min in; arms 6-7 never started.

Usage:
  powershell -NoProfile -File scripts/run_r24_overnight_20260709_resume_arm5_local_cuda.ps1
  powershell -NoProfile -File scripts/run_r24_overnight_20260709_resume_arm5_local_cuda.ps1 -ContinueOnError
#>
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "logs/r24_overnight_20260709_audit_deconfound",
    [string]$Device = "cuda",
    [int]$TrainTotalTimesteps = 320000,
    [int]$TrainNumEnvs = 16,
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"

function Format-CommandLine {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Command
    )

    return (($Command | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }) -join " ")
}

function Invoke-ArmRun {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArmName,
        [Parameter(Mandatory = $true)]
        [string[]]$Command
    )

    $logDir = Join-Path $runRoot $ArmName
    $line = Format-CommandLine -Command $Command
    Write-Host ""
    Write-Host "===== R24 overnight resume arm: $ArmName ====="
    Write-Host $line

    New-Item -ItemType Directory -Force -Path $logDir | Out-Null

    $cmdFile = Join-Path $logDir "command.txt"
    $outputFile = Join-Path $logDir "runner_output.log"
    $statusFile = Join-Path $logDir "runner_status.txt"
    $batchFile = Join-Path $logDir "run_command.cmd"

    $line | Set-Content -Path $cmdFile -Encoding UTF8

    @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "output_file=$outputFile"
        "command_file=$cmdFile"
        "batch_file=$batchFile"
        "arm=$ArmName"
    ) | Set-Content -Path $statusFile -Encoding UTF8

    @(
        "@echo off",
        "cd /d `"$((Get-Location).Path)`"",
        "$line > `"$outputFile`" 2>&1",
        "exit /b %ERRORLEVEL%"
    ) | Set-Content -Path $batchFile -Encoding ASCII

    $exitCode = 1
    try {
        & $env:ComSpec /d /c $batchFile
        $exitCode = $LASTEXITCODE
    } catch {
        $_ | Out-File -FilePath $outputFile -Append -Encoding UTF8
        $exitCode = 1
    }

    @(
        "finished=$(Get-Date -Format o)"
        "state=finished"
        "exit_code=$exitCode"
        "output_file=$outputFile"
        "command_file=$cmdFile"
        "batch_file=$batchFile"
        "arm=$ArmName"
    ) | Set-Content -Path $statusFile -Encoding UTF8

    if ($exitCode -ne 0) {
        $message = "Arm '$ArmName' failed with exit code $exitCode; see $outputFile"
        if ($ContinueOnError) {
            Write-Warning $message
        } else {
            throw $message
        }
    }
}

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

$runRoot = $RunRoot

Write-Host "R24 overnight resume (local CUDA): arms 5-7"
Write-Host "  python:              $Python"
Write-Host "  run_root:            $runRoot"
Write-Host "  device:              $Device"
Write-Host "  train_timesteps:     $TrainTotalTimesteps"
Write-Host "  train_num_envs:      $TrainNumEnvs"
Write-Host "  continue_on_error:   $ContinueOnError"
Write-Host ""

$commonTrainArgs = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config",
    "--scenario", "energy", "--preset", "S7-S1", "--n_agents", "6",
    "--collector_backend", "subproc", "--collector_start_method", "spawn",
    "--num_envs", "$TrainNumEnvs", "--rollout_length", "500", "--skill_interval", "10",
    "--skill_lifetime_candidates", "1,2,3,4",
    "--total_timesteps", "$TrainTotalTimesteps",
    "--eval_interval", "160000", "--eval_episodes", "20",
    "--save_interval", "20", "--checkpoint_keep_last", "4", "--plot_interval", "10",
    "--low_clip_epsilon", "0.1", "--smdp_bootstrap_coef", "0.25", "--device", "$Device",
    "--opt_num_prototypes", "4", "--prototype_skill_extra_codes", "0",
    "--team_bridge_type", "stochastic", "--enable_situation_diagnostics",
    "--enable_prototype_response_skills", "--enable_high_omega_conditioning",
    "--enable_agent_prototype_relevance", "--enable_per_agent_kappa",
    "--enable_prototype_disc_probe", "--prototype_disc_condition", "kappa",
    "--enable_prototype_disc_reward", "--prototype_disc_reward_coef", "0.05",
    "--prototype_disc_clip", "2.0", "--prototype_disc_warmup_steps", "20000",
    "--reward_ratio_guard_mode", "kill",
    "--disable_process_reward", "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe", "--disable_topology_role_probe",
    "--disable_transition_skill_discriminator",
    "--enable_team_intent", "--enable_team_disc_probe",
    "--team_intent_k", "8",
    "--z_assignment_residual_gain", "0.5"
)

$baseTrainArgs = $commonTrainArgs

# Pair-complete-first order resume: arm5, arm6, arm7

# arm5_training_arm2_seed1 (with q_A flags)
$arm5Args = $baseTrainArgs + @(
    "--enable_assignment_actionability_reward",
    "--assignment_actionability_coef", "0.02",
    "--assignment_actionability_clip", "1.0",
    "--assignment_actionability_warmup_steps", "20000",
    "--seed", "1",
    "--log_dir", (Join-Path $runRoot "arm5_training_arm2_seed1")
)
$command = @($Python) + $arm5Args
Invoke-ArmRun -ArmName "arm5_training_arm2_seed1" -Command $command

# arm6_training_arm0_seed2 (no q_A flags)
$arm6Args = $baseTrainArgs + @(
    "--seed", "2",
    "--log_dir", (Join-Path $runRoot "arm6_training_arm0_seed2")
)
$command = @($Python) + $arm6Args
Invoke-ArmRun -ArmName "arm6_training_arm0_seed2" -Command $command

# arm7_training_arm2_seed2 (with q_A flags)
$arm7Args = $baseTrainArgs + @(
    "--enable_assignment_actionability_reward",
    "--assignment_actionability_coef", "0.02",
    "--assignment_actionability_clip", "1.0",
    "--assignment_actionability_warmup_steps", "20000",
    "--seed", "2",
    "--log_dir", (Join-Path $runRoot "arm7_training_arm2_seed2")
)
$command = @($Python) + $arm7Args
Invoke-ArmRun -ArmName "arm7_training_arm2_seed2" -Command $command

Write-Host ""
Write-Host "R24 overnight resume: arms 5-7 completed or failed."
