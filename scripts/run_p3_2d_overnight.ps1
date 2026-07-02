param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string[]]$Experiment = @("all"),
    [int]$Seed = 1,
    [int]$NumEnvs = 16,
    [int]$TotalTimesteps = 320000,
    [int]$EvalInterval = 160000,
    [int]$EvalEpisodes = 20,
    [int]$RolloutLength = 500,
    [int]$SkillInterval = 10,
    [string]$LogRoot = "logs\ha_ctse_process_p3_2d_overnight",
    [ValidateSet("cpu", "cuda")]
    [string]$Device = "cpu",
    [ValidateSet("sync", "subproc")]
    [string]$CollectorBackend = "subproc",
    [ValidateSet("spawn", "forkserver", "fork")]
    [string]$CollectorStartMethod = "spawn",
    [switch]$DryRun,
    [switch]$ContinueOnError
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Join-ArgList {
    param([string[]]$Items)
    return ($Items | ForEach-Object {
        if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
    }) -join " "
}

if ($Experiment -contains "all") {
    $Experiment = @(
        "p3_2d_main",
        "p3_2d_dense_short",
        "p3_2d_mixed_lifetime",
        "p3_2d_no_group_balance"
    )
}

$validExperiments = @(
    "p3_2d_main",
    "p3_2d_dense_short",
    "p3_2d_mixed_lifetime",
    "p3_2d_no_group_balance"
)

foreach ($exp in $Experiment) {
    if ($validExperiments -notcontains $exp) {
        throw "Unknown experiment '$exp'. Valid: all,$($validExperiments -join ',')"
    }
}

$rewardOffBase = @(
    "--disable_process_posterior_mi",
    "--disable_process_reward",
    "--disable_transition_skill_discriminator",
    "--disable_topology_role_probe",
    "--process_reward_injection", "none",
    "--process_reward_coef", "0.0",
    "--process_contrast_coef", "0.0",
    "--process_outcome_coef", "0.0",
    "--process_prior_coef", "0.0",
    "--process_shortcut_coef", "0.0",
    "--context_shortcut_coef", "0.0",
    "--process_shortcut_margin_coef", "0.0"
)

function Invoke-P3Run {
    param(
        [string]$Name,
        [string]$Candidates,
        [string]$Horizons,
        [int]$Stride,
        [string[]]$ExtraArgs = @()
    )

    $stepsK = [int]($TotalTimesteps / 1000)
    $logDir = Join-Path $LogRoot ("ha_ctse_process_s7s1_{0}_{1}env_seed{2}_{3}k" -f $Name, $NumEnvs, $Seed, $stepsK)
    $args = @(
        "-m", "ha_ctse_process.train",
        "--config", "ha_ctse_process.config",
        "--scenario", "energy",
        "--preset", "S7-S1",
        "--seed", "$Seed",
        "--n_agents", "6",
        "--collector_backend", "$CollectorBackend",
        "--collector_start_method", "$CollectorStartMethod",
        "--num_envs", "$NumEnvs",
        "--rollout_length", "$RolloutLength",
        "--skill_interval", "$SkillInterval",
        "--skill_lifetime_candidates", "$Candidates",
        "--total_timesteps", "$TotalTimesteps",
        "--eval_interval", "$EvalInterval",
        "--eval_episodes", "$EvalEpisodes",
        "--save_interval", "20",
        "--checkpoint_keep_last", "4",
        "--plot_interval", "10",
        "--low_clip_epsilon", "0.1",
        "--smdp_bootstrap_coef", "0.25",
        "--device", "$Device",
        "--log_dir", "$logDir",
        "--enable_skill_effect_probe",
        "--enable_skill_effect_intervention_probe",
        "--skill_effect_horizons", "$Horizons",
        "--skill_effect_stride", "$Stride",
        "--skill_effect_max_windows", "8192",
        "--skill_effect_intervention_max_samples", "512"
    ) + $rewardOffBase + $ExtraArgs

    Write-Host ""
    Write-Host "===== HA-CTSE P3-2d overnight: $Name ====="
    Write-Host "  candidates: $Candidates"
    Write-Host "  horizons:   $Horizons"
    Write-Host "  stride:     $Stride"
    Write-Host "  log_dir:    $logDir"
    Write-Host ("& `"$Python`" " + (Join-ArgList $args))

    if ($DryRun) {
        return
    }

    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    & $Python @args
    if ($LASTEXITCODE -ne 0) {
        $message = "Experiment $Name failed with exit code $LASTEXITCODE"
        if ($ContinueOnError) {
            Write-Warning $message
        } else {
            throw $message
        }
    }
}

Write-Host "HA-CTSE P3-2d overnight reward-off suite"
Write-Host "  experiments:     $($Experiment -join ',')"
Write-Host "  seed:            $Seed"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  eval_interval:   $EvalInterval"
Write-Host "  eval_episodes:   $EvalEpisodes"
Write-Host "  log_root:        $LogRoot"
Write-Host "  device:          $Device"
Write-Host "  collector:       $CollectorBackend/$CollectorStartMethod"
Write-Host "  dry_run:         $DryRun"
Write-Host "  reward:          OFF; P3-4 remains blocked"

foreach ($exp in $Experiment) {
    switch ($exp) {
        "p3_2d_main" {
            Invoke-P3Run `
                -Name "p3_2d_observed_main" `
                -Candidates "1,2,3" `
                -Horizons "3,5,10,20" `
                -Stride 3
        }
        "p3_2d_dense_short" {
            Invoke-P3Run `
                -Name "p3_2d_dense_short_h1_3_5_10" `
                -Candidates "1,2,3" `
                -Horizons "1,3,5,10" `
                -Stride 1
        }
        "p3_2d_mixed_lifetime" {
            Invoke-P3Run `
                -Name "p3_2d_mixed_lifetime_1_2_4_8" `
                -Candidates "1,2,4,8" `
                -Horizons "3,5,10,20" `
                -Stride 3
        }
        "p3_2d_no_group_balance" {
            Invoke-P3Run `
                -Name "p3_2d_no_group_balance" `
                -Candidates "1,2,3" `
                -Horizons "3,5,10,20" `
                -Stride 3 `
                -ExtraArgs @("--disable_skill_effect_group_balanced_loss")
        }
    }
}

if (-not $DryRun) {
    Write-Host ""
    Write-Host "===== P3-2d overnight suite finished ====="
    Write-Host "Read logs under: $LogRoot"
    Write-Host "Primary gate metrics:"
    Write-Host "  effect_gain_group_balanced_mean"
    Write-Host "  effect_gain_nonmotion"
    Write-Host "  effect_gain_positive_frac"
    Write-Host "  effect_gain_minus_duration_baseline"
    Write-Host "  effect_gain_minus_reward_baseline"
    Write-Host "  effect_observed_target_skill_l2_mean"
    Write-Host "  effect_observed_target_skill_l2_nonmotion"
    Write-Host "  effect_observed_action_target_corr"
    Write-Host "  effect_reward_low_mean and effect_reward_applied_steps must stay zero"
}
