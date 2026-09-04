param(
    [string]$Python = "python",
    [string[]]$Experiment = @("all"),
    [int[]]$Seeds = @(1),
    [int]$NumEnvs = 16,
    [int]$TotalTimesteps = 320000,
    [int]$EvalInterval = 160000,
    [int]$EvalEpisodes = 20,
    [int]$RolloutLength = 500,
    [int]$SkillInterval = 10,
    [string]$Candidates = "3,7,13,24",
    [string]$LogRoot = "logs\ha_ctse_process_g_info_local_cuda",
    [ValidateSet("cpu", "cuda")]
    [string]$Device = "cuda",
    [ValidateSet("sync", "subproc")]
    [string]$CollectorBackend = "subproc",
    [ValidateSet("spawn", "forkserver", "fork")]
    [string]$CollectorStartMethod = "spawn",
    [double]$GInfoCoefSkill = 0.01,
    [double]$GInfoCoefDuration = 0.01,
    [int]$GInfoWarmupSteps = 80000,
    [int]$GInfoAnnealSteps = 0,
    [int]$GInfoMaxSegments = 256,
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

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

if ($Experiment -contains "all") {
    $Experiment = @(
        "diag",
        "obj_skill_duration"
    )
}

$validExperiments = @(
    "diag",
    "obj_skill_duration",
    "obj_skill_only",
    "obj_duration_only"
)

foreach ($exp in $Experiment) {
    if ($validExperiments -notcontains $exp) {
        throw "Unknown experiment '$exp'. Valid: all,$($validExperiments -join ',')"
    }
}

$rewardPureBase = @(
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

function Invoke-GInfoRun {
    param(
        [string]$Name,
        [int]$Seed,
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
        "--g_info_max_segments", "$GInfoMaxSegments",
        "--log_dir", "$logDir"
    ) + $rewardPureBase + $ExtraArgs

    Write-Host ""
    Write-Host "===== HA-CTSE Round10 G-info local CUDA: $Name seed=$Seed ====="
    Write-Host "  candidates:      $Candidates"
    Write-Host "  num_envs:        $NumEnvs"
    Write-Host "  total_timesteps: $TotalTimesteps"
    Write-Host "  device:          $Device"
    Write-Host "  log_dir:         $logDir"
    Write-Host ("& `"$Python`" " + (Join-ArgList $args))

    if ($DryRun) {
        return
    }

    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    & $Python @args
    if ($LASTEXITCODE -ne 0) {
        $message = "Experiment $Name seed=$Seed failed with exit code $LASTEXITCODE"
        if ($ContinueOnError) {
            Write-Warning $message
        } else {
            throw $message
        }
    }
}

Write-Host "HA-CTSE Round10 G-info objective local CUDA suite"
Write-Host "  experiments:       $($Experiment -join ',')"
Write-Host "  seeds:             $($Seeds -join ',')"
Write-Host "  num_envs:          $NumEnvs"
Write-Host "  total_timesteps:   $TotalTimesteps"
Write-Host "  eval_interval:     $EvalInterval"
Write-Host "  eval_episodes:     $EvalEpisodes"
Write-Host "  candidates:        $Candidates"
Write-Host "  log_root:          $LogRoot"
Write-Host "  device:            $Device"
Write-Host "  collector:         $CollectorBackend/$CollectorStartMethod"
Write-Host "  g_info_coef_skill: $GInfoCoefSkill"
Write-Host "  g_info_coef_dur:   $GInfoCoefDuration"
Write-Host "  g_info_warmup:     $GInfoWarmupSteps"
Write-Host "  dry_run:           $DryRun"
Write-Host "  reward:            OFF; this is a g-liveness probe, not a comm-shaping run"

foreach ($seed in $Seeds) {
    foreach ($exp in $Experiment) {
        switch ($exp) {
            "diag" {
                Invoke-GInfoRun `
                    -Name "g_info_diag" `
                    -Seed $seed
            }
            "obj_skill_duration" {
                Invoke-GInfoRun `
                    -Name "g_info_obj_skill_duration" `
                    -Seed $seed `
                    -ExtraArgs @(
                        "--enable_g_info_objective",
                        "--g_info_coef_skill", "$GInfoCoefSkill",
                        "--g_info_coef_duration", "$GInfoCoefDuration",
                        "--g_info_warmup_steps", "$GInfoWarmupSteps",
                        "--g_info_anneal_steps", "$GInfoAnnealSteps"
                    )
            }
            "obj_skill_only" {
                Invoke-GInfoRun `
                    -Name "g_info_obj_skill_only" `
                    -Seed $seed `
                    -ExtraArgs @(
                        "--enable_g_info_objective",
                        "--g_info_coef_skill", "$GInfoCoefSkill",
                        "--g_info_coef_duration", "0.0",
                        "--g_info_warmup_steps", "$GInfoWarmupSteps",
                        "--g_info_anneal_steps", "$GInfoAnnealSteps"
                    )
            }
            "obj_duration_only" {
                Invoke-GInfoRun `
                    -Name "g_info_obj_duration_only" `
                    -Seed $seed `
                    -ExtraArgs @(
                        "--enable_g_info_objective",
                        "--g_info_coef_skill", "0.0",
                        "--g_info_coef_duration", "$GInfoCoefDuration",
                        "--g_info_warmup_steps", "$GInfoWarmupSteps",
                        "--g_info_anneal_steps", "$GInfoAnnealSteps"
                    )
            }
        }
    }
}

if (-not $DryRun) {
    Write-Host ""
    Write-Host "===== G-info local CUDA suite finished ====="
    Write-Host "Read logs under: $LogRoot"
    Write-Host "Primary gate metrics:"
    Write-Host "  g_info_skill_mi, g_info_duration_mi, g_info_total_mi"
    Write-Host "  g_itv_tv_skill, g_itv_tv_duration, g_joint_assignment_distance"
    Write-Host "  team_code_usage_entropy, team_code_usage_max_frac"
    Write-Host "  team_code_skill_mi, team_code_duration_mi, team_code_edit_mi"
    Write-Host "  skill_usage_entropy, duration_usage_entropy, segment_length_mean"
    Write-Host "  coverage_eq1_step_fraction, zero_throughput_step_fraction"
}
