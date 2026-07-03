param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "control,s1_probe,s1_reward",
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
$logRoot = Join-Path "logs\ha_ctse_r14_stage1_local_cuda" "run_$runStamp"
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
    "--enable_situation_diagnostics",
    "--disable_process_reward",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe",
    "--disable_topology_role_probe",
    "--disable_transition_skill_discriminator",
    "--enable_skill_effect_probe",
    "--enable_skill_effect_intervention_probe",
    "--skill_effect_intervention_max_samples", "512"
)

function Invoke-R14Stage1Run {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [string[]]$ExtraArgs = @()
    )

    $logDir = Join-Path $logRoot $Name
    $command = @($Python) + $common + $ExtraArgs + @("--log_dir", $logDir)

    Write-Host ""
    Write-Host "===== R14 Stage 1 prototype-response: $Name ====="
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
    throw "No experiments requested. Use control, s1_probe, or s1_reward."
}

Write-Host "R14 Stage 1 prototype-response local CUDA runner"
Write-Host "  experiments:     $($requested -join ',')"
Write-Host "  python:          $Python"
Write-Host "  seed:            $Seed"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  device:          $Device"
Write-Host "  log_root:        $logRoot"
Write-Host "  dry_run:         $DryRun"
Write-Host "  reward path:     external task reward only unless s1_reward is selected"

foreach ($exp in $requested) {
    switch ($exp) {
        "control" {
            Invoke-R14Stage1Run "control_reward_pure"
        }
        "s1_probe" {
            Invoke-R14Stage1Run "s1_probe_no_reward" @(
                "--enable_prototype_response_skills",
                "--enable_high_omega_conditioning",
                "--enable_agent_prototype_relevance",
                "--enable_per_agent_kappa",
                "--enable_prototype_disc_probe",
                "--prototype_disc_condition", "kappa"
            )
        }
        "s1_reward" {
            Invoke-R14Stage1Run "s1_reward_proto_disc_coef01" @(
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
        default {
            throw "Unknown experiment '$exp'. Use control, s1_probe, or s1_reward."
        }
    }
}
