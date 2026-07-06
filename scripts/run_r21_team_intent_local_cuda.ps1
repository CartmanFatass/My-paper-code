param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "r21_z_probe,r21_z_reward",
    [string]$Seeds = "1",
    [int]$TotalTimesteps = 960000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [int]$TeamIntentK = 48,
    [double]$TeamDiscCoef = 0.05,
    [switch]$ContinueOnError,
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
$logRoot = Join-Path "logs\ha_ctse_r21_team_intent_local_cuda" "run_$runStamp"
$requested = $Experiments.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$seedList = $Seeds.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }

if (-not $requested) {
    throw "No experiments requested. Use entfloor_control, r21_z_probe, or r21_z_reward."
}
if (-not $seedList) {
    throw "No seeds requested. Example: -Seeds `"1`" or -Seeds `"1,2`"."
}

$common = @(
    "-m", "ha_ctse_process.train",
    "--config", "ha_ctse_process.config",
    "--scenario", "energy",
    "--preset", "S7-S1",
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
    "--team_bridge_type", "stochastic",
    "--enable_situation_diagnostics",
    "--enable_prototype_response_skills",
    "--enable_high_omega_conditioning",
    "--enable_agent_prototype_relevance",
    "--enable_per_agent_kappa",
    "--enable_prototype_disc_probe",
    "--prototype_disc_condition", "kappa",
    "--enable_prototype_disc_reward",
    "--prototype_disc_reward_coef", "0.05",
    "--prototype_disc_clip", "2.0",
    "--prototype_disc_warmup_steps", "20000",
    "--reward_ratio_guard_mode", "kill",
    "--disable_process_reward",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe",
    "--disable_topology_role_probe",
    "--disable_transition_skill_discriminator"
)

function Invoke-R21Run {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Seed,
        [string[]]$ExtraArgs = @()
    )

    $logDir = Join-Path $logRoot ("seed$Seed\$Name")
    $command = @($Python) + $common + @("--seed", "$Seed") + $ExtraArgs + @("--log_dir", $logDir)
    $line = Format-CommandLine -Command $command

    Write-Host ""
    Write-Host "===== R21 team-intent local CUDA: $Name seed=$Seed ====="
    Write-Host "team_intent_k: $TeamIntentK"
    Write-Host "team_disc_coef: $TeamDiscCoef"
    Write-Host "guard_mode:    kill"
    Write-Host $line

    if ($DryRun) {
        return
    }

    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    $cmdFile = Join-Path $logDir "command.txt"
    $line | Set-Content -Path $cmdFile -Encoding UTF8
    $batchFile = Join-Path $logDir "run_command.cmd"
    $outputFile = Join-Path $logDir "runner_output.log"
    $statusFile = Join-Path $logDir "runner_status.txt"

    @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "output_file=$outputFile"
        "command_file=$cmdFile"
        "batch_file=$batchFile"
    ) | Set-Content -Path $statusFile -Encoding UTF8

    $exitCode = 1
    $oldErrorActionPreference = $ErrorActionPreference
    $hasNativePreference = Test-Path Variable:\PSNativeCommandUseErrorActionPreference
    if ($hasNativePreference) {
        $oldNativePreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    try {
        @(
            "@echo off",
            "cd /d `"$((Get-Location).Path)`"",
            "$line > `"$outputFile`" 2>&1",
            "exit /b %ERRORLEVEL%"
        ) | Set-Content -Path $batchFile -Encoding ASCII
        $ErrorActionPreference = "Continue"
        & $env:ComSpec /d /c $batchFile
        $exitCode = $LASTEXITCODE
    } catch {
        $_ | Out-File -FilePath $outputFile -Append -Encoding UTF8
        $exitCode = 1
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
        if ($hasNativePreference) {
            $PSNativeCommandUseErrorActionPreference = $oldNativePreference
        }
    }

    @(
        "finished=$(Get-Date -Format o)"
        "state=finished"
        "exit_code=$exitCode"
        "output_file=$outputFile"
        "command_file=$cmdFile"
        "batch_file=$batchFile"
    ) | Set-Content -Path $statusFile -Encoding UTF8

    if ($exitCode -ne 0) {
        $message = "Experiment $Name seed=$Seed failed with exit code $exitCode; see $outputFile"
        if ($ContinueOnError) {
            Write-Warning $message
        } else {
            throw $message
        }
    }
}

Write-Host "R21 team-intent local CUDA runner"
Write-Host "  experiments:     $($requested -join ',')"
Write-Host "  seeds:           $($seedList -join ',')"
Write-Host "  python:          $Python"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  device:          $Device"
Write-Host "  team_intent_k:   $TeamIntentK"
Write-Host "  team_disc_coef:  $TeamDiscCoef"
Write-Host "  continue_error:  $ContinueOnError"
Write-Host "  log_root:        $logRoot"
Write-Host "  dry_run:         $DryRun"
Write-Host "  primary read:    z_usage_entropy + z_dwell + z_boundary_trunc_rate + z_assignment_itv + team_disc_*"
Write-Host "  base:            coef005 prototype reward; duration floor disabled"

foreach ($seed in $seedList) {
    foreach ($exp in $requested) {
        switch ($exp) {
            "entfloor_control" {
                Invoke-R21Run "entfloor_control" $seed @()
            }
            "r21_z_probe" {
                Invoke-R21Run "r21_z_probe" $seed @(
                    "--enable_team_intent",
                    "--enable_team_disc_probe",
                    "--team_intent_k", "$TeamIntentK"
                )
            }
            "r21_z_reward" {
                Invoke-R21Run "r21_z_reward" $seed @(
                    "--enable_team_intent",
                    "--enable_team_disc_reward",
                    "--team_intent_k", "$TeamIntentK",
                    "--team_disc_coef", "$TeamDiscCoef",
                    "--team_disc_clip", "2.0",
                    "--team_disc_warmup_steps", "20000"
                )
            }
            default {
                throw "Unknown experiment '$exp'. Use entfloor_control, r21_z_probe, or r21_z_reward."
            }
        }
    }
}
