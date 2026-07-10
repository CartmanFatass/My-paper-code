<#
R24 overnight local CUDA audit + deconfound runner
EXP-20260709-local-overnight-audit-power-r23-deconfound

Phase A: R24 forced-audit power upgrade on three existing checkpoints (NResets 64)
Phase B: R23 arm0-vs-arm2 matched-env deconfound at 2 seeds x 160k, 16 envs

Usage:
  powershell -NoProfile -File scripts/run_r24_overnight_20260709_audit_deconfound_local_cuda.ps1 -DryRun
  powershell -NoProfile -File scripts/run_r24_overnight_20260709_audit_deconfound_local_cuda.ps1
#>
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "logs/r24_overnight_20260709_audit_deconfound",
    [string]$Device = "cuda",
    [int]$AuditNResets = 64,
    [int]$TrainTotalTimesteps = 320000,
    [int]$TrainNumEnvs = 16,
    [switch]$DryRun,
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
    Write-Host "===== R24 overnight arm: $ArmName ====="
    Write-Host $line

    if ($DryRun) {
        return
    }

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

# Verify checkpoints exist
$existingQACheckpoint = "logs_r23_next_mechanism_matrix_local\seed1\arm2_qA_reward_coef002\standalone_process_core_update_40.pt"
$existingNullArchCheckpoint = "logs_r23_next_mechanism_matrix_local\seed1\arm0_arch_only\standalone_process_core_final.pt"
$existingNullQdCheckpoint = "logs_r23_next_mechanism_matrix_local\seed1\arm3_qD_audit\standalone_process_core_update_40.pt"

foreach ($path in @($existingQACheckpoint, $existingNullArchCheckpoint, $existingNullQdCheckpoint)) {
    if (-not (Test-Path $path)) {
        throw "Required existing checkpoint not found: $path"
    }
}

$runRoot = $RunRoot
$auditHorizons = "10,20,50,100"

Write-Host "R24 overnight audit + deconfound (local CUDA)"
Write-Host "  python:              $Python"
Write-Host "  run_root:            $runRoot"
Write-Host "  device:              $Device"
Write-Host "  audit_n_resets:      $AuditNResets"
Write-Host "  train_timesteps:     $TrainTotalTimesteps"
Write-Host "  train_num_envs:      $TrainNumEnvs"
Write-Host "  audit_horizons:      $auditHorizons"
Write-Host "  dry_run:             $DryRun"
Write-Host ""

# Phase A: Three forced-audit arms
Write-Host "Phase A: Forced-behavior audit arms (NResets=$AuditNResets)"
Write-Host ""

$auditArms = @(
    @{ name = "arm1_qA_checkpoint_forced_audit"; checkpoint = $existingQACheckpoint }
    @{ name = "arm2_null_arch_no_qA_forced_audit"; checkpoint = $existingNullArchCheckpoint }
    @{ name = "arm3_null_qD_probe_no_qA_forced_audit"; checkpoint = $existingNullQdCheckpoint }
)

foreach ($arm in $auditArms) {
    $outDir = Join-Path $runRoot $arm.name
    $command = @(
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "scripts\run_r24_behavior_audit_local_cuda.ps1",
        "-Checkpoint",
        $arm.checkpoint,
        "-OutDir",
        $outDir,
        "-Python",
        $Python,
        "-Device",
        $Device,
        "-NResets",
        "$AuditNResets"
    )
    Invoke-ArmRun -ArmName $arm.name -Command $command
}

# Phase B: Four training arms (arm0_arch_only and arm2_qA_reward at seeds 1,2)
# Order: pair-complete-first (arm0_seed1, arm2_seed1, arm0_seed2, arm2_seed2)
Write-Host ""
Write-Host "Phase B: Training deconfound arms (timesteps=$TrainTotalTimesteps num_envs=$TrainNumEnvs)"
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

# Pair-complete-first order: arm0_seed1, arm2_seed1, arm0_seed2, arm2_seed2

# arm0_arch_only seed 1
$arm0Seed1Args = $baseTrainArgs + @(
    "--seed", "1",
    "--log_dir", (Join-Path $runRoot "arm4_training_arm0_seed1")
)
$command = @($Python) + $arm0Seed1Args
Invoke-ArmRun -ArmName "arm4_training_arm0_seed1" -Command $command

# arm2_qA_reward seed 1 (with q_A flags)
$arm2Seed1Args = $baseTrainArgs + @(
    "--enable_assignment_actionability_reward",
    "--assignment_actionability_coef", "0.02",
    "--assignment_actionability_clip", "1.0",
    "--assignment_actionability_warmup_steps", "20000",
    "--seed", "1",
    "--log_dir", (Join-Path $runRoot "arm5_training_arm2_seed1")
)
$command = @($Python) + $arm2Seed1Args
Invoke-ArmRun -ArmName "arm5_training_arm2_seed1" -Command $command

# arm0_arch_only seed 2
$arm0Seed2Args = $baseTrainArgs + @(
    "--seed", "2",
    "--log_dir", (Join-Path $runRoot "arm6_training_arm0_seed2")
)
$command = @($Python) + $arm0Seed2Args
Invoke-ArmRun -ArmName "arm6_training_arm0_seed2" -Command $command

# arm2_qA_reward seed 2 (with q_A flags)
$arm2Seed2Args = $baseTrainArgs + @(
    "--enable_assignment_actionability_reward",
    "--assignment_actionability_coef", "0.02",
    "--assignment_actionability_clip", "1.0",
    "--assignment_actionability_warmup_steps", "20000",
    "--seed", "2",
    "--log_dir", (Join-Path $runRoot "arm7_training_arm2_seed2")
)
$command = @($Python) + $arm2Seed2Args
Invoke-ArmRun -ArmName "arm7_training_arm2_seed2" -Command $command

Write-Host ""
Write-Host "R24 overnight audit + deconfound: all arms completed or dry-run successful."
