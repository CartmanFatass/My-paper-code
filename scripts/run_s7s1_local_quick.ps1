param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string[]]$Experiment = @(
        "smoke",
        "k_full_sync",
        "k_fixed_d7",
        "k_decoupled_short",
        "k_decoupled_mixed",
        "p2_precheck"
    ),
    [int]$Seed = 1,
    [int]$NumEnvs = 4,
    [int]$TotalTimesteps = 64000,
    [int]$EvalInterval = 32000,
    [int]$EvalEpisodes = 5,
    [int]$RolloutLength = 250,
    [string]$LogRoot = "logs\local_s7s1_quick",
    [string]$Device = "cpu",
    [ValidateSet("sync", "subproc")]
    [string]$CollectorBackend = "sync",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ($Experiment -contains "all") {
    $Experiment = @(
        "smoke",
        "k_full_sync",
        "k_fixed_d7",
        "k_decoupled_short",
        "k_decoupled_mixed",
        "p2_precheck",
        "p1_low_pos_probe"
    )
}

$processOff = @(
    "--process_reward_injection", "none",
    "--process_reward_coef", "0.0",
    "--process_contrast_coef", "0.0",
    "--process_outcome_coef", "0.0",
    "--process_prior_coef", "0.0",
    "--process_shortcut_coef", "0.0",
    "--context_shortcut_coef", "0.0",
    "--process_shortcut_margin_coef", "0.0",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe",
    "--disable_process_reward",
    "--disable_transition_skill_discriminator",
    "--disable_topology_role_probe"
)

function Invoke-HaCtseRun {
    param(
        [string]$Name,
        [string]$Candidates,
        [string[]]$ExtraArgs = @(),
        [int]$Steps = $TotalTimesteps,
        [int]$Envs = $NumEnvs,
        [int]$Rollout = $RolloutLength,
        [int]$EvalEvery = $EvalInterval,
        [int]$Episodes = $EvalEpisodes
    )

    $stepsK = [int]($Steps / 1000)
    $logDir = Join-Path $LogRoot ("ha_ctse_process_{0}_{1}env_seed{2}_{3}k" -f $Name, $Envs, $Seed, $stepsK)
    $args = @(
        "-m", "ha_ctse_process.train",
        "--config", "ha_ctse_process.config",
        "--scenario", "energy",
        "--preset", "S7-S1",
        "--seed", "$Seed",
        "--n_agents", "6",
        "--collector_backend", "$CollectorBackend",
        "--collector_start_method", "spawn",
        "--num_envs", "$Envs",
        "--rollout_length", "$Rollout",
        "--skill_interval", "10",
        "--skill_lifetime_candidates", "$Candidates",
        "--total_timesteps", "$Steps",
        "--eval_interval", "$EvalEvery",
        "--eval_episodes", "$Episodes",
        "--save_interval", "10",
        "--checkpoint_keep_last", "2",
        "--plot_interval", "0",
        "--low_clip_epsilon", "0.1",
        "--smdp_bootstrap_coef", "0.25",
        "--device", "$Device",
        "--log_dir", "$logDir"
    ) + $processOff + $ExtraArgs

    Write-Host ""
    Write-Host "===== HA-CTSE local quick: $Name candidates=$Candidates steps=$Steps envs=$Envs ====="
    Write-Host ("& `"$Python`" " + ($args -join " "))
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        & $Python @args
    }
}

Write-Host "HA-CTSE local quick suite"
Write-Host "  experiments:     $($Experiment -join ',')"
Write-Host "  seed:            $Seed"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  eval_interval:   $EvalInterval"
Write-Host "  log_root:        $LogRoot"
Write-Host "  device:          $Device"
Write-Host "  collector:       $CollectorBackend"
Write-Host "  dry_run:         $DryRun"

foreach ($exp in $Experiment) {
    switch ($exp) {
        "smoke" {
            Invoke-HaCtseRun `
                -Name "smoke_lifetime_diag" `
                -Candidates "1,2" `
                -Steps 1024 `
                -Envs 2 `
                -Rollout 64 `
                -EvalEvery 0 `
                -Episodes 1
        }
        "k_full_sync" {
            Invoke-HaCtseRun -Name "k_full_sync_1_reward_pure" -Candidates "1"
        }
        "k_fixed_d7" {
            Invoke-HaCtseRun -Name "k_fixed_d7_reward_pure" -Candidates "7"
        }
        "k_decoupled_short" {
            Invoke-HaCtseRun -Name "k_decoupled_short_1_2_3_reward_pure" -Candidates "1,2,3"
        }
        "k_decoupled_mixed" {
            Invoke-HaCtseRun -Name "k_decoupled_mixed_1_2_4_8_reward_pure" -Candidates "1,2,4,8"
        }
        "p2_precheck" {
            Invoke-HaCtseRun `
                -Name "p2_precheck_reward_off" `
                -Candidates "1,2,3" `
                -ExtraArgs @("--enable_p2_recovery_compute")
        }
        "p1_low_pos_probe" {
            Invoke-HaCtseRun `
                -Name "p1_low_pos_probe" `
                -Candidates "1,2,3" `
                -ExtraArgs @(
                    "--enable_topology_potential_shaping",
                    "--topology_potential_injection", "low_only",
                    "--topology_potential_coef", "1.0",
                    "--topology_potential_clip", "0.05",
                    "--topology_potential_discount_mode", "delta",
                    "--topology_potential_positive_only",
                    "--topology_potential_warmup_steps", "0"
                )
        }
        default {
            throw "Unknown experiment: $exp"
        }
    }
}
