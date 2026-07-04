param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "control_legacy4,s1_probe",
    [int]$Seed = 1,
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [switch]$DryRun
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

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logRoot = Join-Path "logs\ha_ctse_r15_stage1_local_cuda" "run_$runStamp"
$common = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config",
    "--scenario", "energy",
    "--preset", "S7-S1",
    "--seed", "$Seed",
    "--n_agents", "6",
    "--collector_backend", "subproc",
    "--collector_start_method", "spawn",
    "--num_envs", "$NumEnvs",
    "--rollout_length", "500",
    "--skill_interval", "10",
    "--skill_lifetime_candidates", "3,7,13,24",
    "--total_timesteps", "$TotalTimesteps",
    "--eval_interval", "160000",
    "--eval_episodes", "20",
    "--save_interval", "20",
    "--checkpoint_keep_last", "4",
    "--plot_interval", "10",
    "--low_clip_epsilon", "0.1",
    "--smdp_bootstrap_coef", "0.25",
    "--device", $Device,
    "--opt_num_prototypes", "4",
    "--prototype_skill_extra_codes", "0",
    "--enable_situation_diagnostics",
    "--disable_process_reward",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe",
    "--disable_topology_role_probe",
    "--disable_transition_skill_discriminator"
)

function Invoke-R15Stage1Run {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [string[]]$ExtraArgs = @()
    )

    $logDir = Join-Path $logRoot $Name
    $command = @($Python) + $common + $ExtraArgs + @("--log_dir", $logDir)

    Write-Host ""
    Write-Host "===== R15 Stage 1 steering objective: $Name ====="
    Write-Host (Format-CommandLine -Command $command)

    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        & $command[0] @($command[1..($command.Count - 1)])
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
}

$requested = $Experiments.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if (-not $requested) {
    throw "No experiments requested. Use control_legacy4, s1_probe, s1_reward, or r15_p1_ablation."
}

Write-Host "R15 Stage 1 steering-objective local CUDA runner"
Write-Host "  experiments:     $($requested -join ',')"
Write-Host "  python:          $Python"
Write-Host "  seed:            $Seed"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  device:          $Device"
Write-Host "  log_root:        $logRoot"
Write-Host "  dry_run:         $DryRun"
Write-Host "  default path:    A0+A1 only; reward/fallback arms require explicit names"

foreach ($exp in $requested) {
    switch ($exp) {
        "control_legacy4" {
            Invoke-R15Stage1Run "control_legacy4_reward_pure" @(
                "--legacy_n_skills", "4"
            )
        }
        "s1_probe" {
            Invoke-R15Stage1Run "s1_probe_ar_null_reward_off" @(
                "--enable_prototype_response_skills",
                "--enable_high_omega_conditioning",
                "--enable_agent_prototype_relevance",
                "--enable_per_agent_kappa",
                "--enable_prototype_disc_probe",
                "--prototype_disc_condition", "kappa"
            )
        }
        "s1_reward" {
            Invoke-R15Stage1Run "s1_reward_ar_null_coef01" @(
                "--enable_prototype_response_skills",
                "--enable_high_omega_conditioning",
                "--enable_agent_prototype_relevance",
                "--enable_per_agent_kappa",
                "--enable_prototype_disc_probe",
                "--enable_prototype_disc_reward",
                "--prototype_disc_condition", "kappa",
                "--prototype_disc_reward_coef", "0.1",
                "--prototype_disc_clip", "2.0",
                "--prototype_disc_warmup_steps", "20000"
            )
        }
        "r15_p1_ablation" {
            Invoke-R15Stage1Run "r15_p1_parallel_learned_prior_coef01" @(
                "--enable_prototype_response_skills",
                "--parallel_selection",
                "--prototype_disc_use_learned_prior",
                "--enable_high_omega_conditioning",
                "--enable_agent_prototype_relevance",
                "--enable_per_agent_kappa",
                "--enable_prototype_disc_probe",
                "--enable_prototype_disc_reward",
                "--prototype_disc_condition", "kappa",
                "--prototype_disc_reward_coef", "0.1",
                "--prototype_disc_clip", "2.0",
                "--prototype_disc_warmup_steps", "20000"
            )
        }
        default {
            throw "Unknown experiment '$exp'. Use control_legacy4, s1_probe, s1_reward, or r15_p1_ablation."
        }
    }
}
