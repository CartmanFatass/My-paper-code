param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "diag_only,oracle_change",
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
$logRoot = Join-Path "logs\ha_ctse_r12_stage1_local_cuda" "run_$runStamp"
$common = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config",
    "--scenario", "energy",
    "--preset", "S7-S1",
    "--seed", "1",
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
    "--enable_situation_diagnostics"
)

function Invoke-R12Stage1Run {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [string[]]$ExtraArgs = @()
    )

    $logDir = Join-Path $logRoot $Name
    $command = @($Python) + $common + $ExtraArgs + @("--log_dir", $logDir)

    Write-Host ""
    Write-Host "===== R12 Stage 1 situation hazard: $Name ====="
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
    throw "No experiments requested. Use diag_only, oracle_change, oracle_conservative, oracle_strict, or learned_beta_small."
}

Write-Host "R12 Stage 1 situation hazard local CUDA runner"
Write-Host "  experiments:     $($requested -join ',')"
Write-Host "  python:          $Python"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  device:          $Device"
Write-Host "  log_root:        $logRoot"
Write-Host "  dry_run:         $DryRun"
Write-Host "  reward path:     external task reward only; no SEF/DADS reward"

foreach ($exp in $requested) {
    switch ($exp) {
        "diag_only" {
            Invoke-R12Stage1Run "diag_only_reward_pure"
        }
        "oracle_change" {
            Invoke-R12Stage1Run "oracle_change_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "oracle_change",
                "--situation_hazard_min_age", "10"
            )
        }
        "oracle_conservative" {
            Invoke-R12Stage1Run "oracle_conservative_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "oracle_change",
                "--situation_hazard_min_age", "30",
                "--enable_situation_hazard_conservative_guard",
                "--situation_hazard_min_dwell_checks", "3",
                "--situation_hazard_confirm_changes", "2",
                "--situation_hazard_max_force_rate", "0.03",
                "--situation_hazard_rate_window", "256"
            )
        }
        "oracle_strict" {
            Invoke-R12Stage1Run "oracle_strict_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "oracle_change",
                "--situation_hazard_min_age", "50",
                "--enable_situation_hazard_conservative_guard",
                "--situation_hazard_min_dwell_checks", "5",
                "--situation_hazard_confirm_changes", "3",
                "--situation_hazard_max_force_rate", "0.015",
                "--situation_hazard_rate_window", "256"
            )
        }
        "learned_beta_small" {
            # Exploratory only: current code samples learned_beta at inference
            # time, but does not yet train a hazard policy update path.
            Invoke-R12Stage1Run "learned_beta_small_reward_pure" @(
                "--enable_situation_hazard_control",
                "--situation_hazard_mode", "learned_beta",
                "--situation_hazard_min_age", "10",
                "--situation_hazard_entropy_coef", "0.005",
                "--situation_hazard_reward_coef", "0.0"
            )
        }
        default {
            throw "Unknown experiment '$exp'. Use diag_only, oracle_change, oracle_conservative, oracle_strict, learned_beta_small."
        }
    }
}
