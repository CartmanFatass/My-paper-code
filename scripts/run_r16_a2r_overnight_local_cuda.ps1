param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "a2r_roster_reward,a2r_roster_coef005,a2_samecheck_reward,a1r_roster_probe",
    [string]$Seeds = "1",
    [int]$TotalTimesteps = 640000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
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
$logRoot = Join-Path "logs\ha_ctse_r16_a2r_overnight_local_cuda" "run_$runStamp"
$requested = $Experiments.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$seedList = $Seeds.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }

if (-not $requested) {
    throw "No experiments requested. Use a2r_roster_reward, a2r_roster_coef005, a2_samecheck_reward, or a1r_roster_probe."
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
    "--enable_situation_diagnostics",
    "--enable_prototype_response_skills",
    "--enable_high_omega_conditioning",
    "--enable_agent_prototype_relevance",
    "--enable_per_agent_kappa",
    "--enable_prototype_disc_probe",
    "--prototype_disc_condition", "kappa",
    "--disable_process_reward",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe",
    "--disable_topology_role_probe",
    "--disable_transition_skill_discriminator"
)

function Invoke-R16Run {
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
    Write-Host "===== R16 A2r overnight: $Name seed=$Seed ====="
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
        # Matplotlib and multiprocessing may emit harmless native stderr
        # warnings. Capture stdout/stderr inside cmd.exe so Windows
        # PowerShell 5.1 cannot wrap native stderr as NativeCommandError.
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

Write-Host "R16 A2r roster-docking overnight local CUDA runner"
Write-Host "  experiments:     $($requested -join ',')"
Write-Host "  seeds:           $($seedList -join ',')"
Write-Host "  python:          $Python"
Write-Host "  num_envs:        $NumEnvs"
Write-Host "  total_timesteps: $TotalTimesteps"
Write-Host "  device:          $Device"
Write-Host "  continue_error:  $ContinueOnError"
Write-Host "  log_root:        $logRoot"
Write-Host "  dry_run:         $DryRun"
Write-Host "  primary read:    roster_ar_kl_shuffled + selection_independence_deficit"

foreach ($seed in $seedList) {
    foreach ($exp in $requested) {
        switch ($exp) {
            "a2r_roster_reward" {
                Invoke-R16Run "a2r_roster_reward_coef01" $seed @(
                    "--ar_prefix_mode", "roster",
                    "--enable_prototype_disc_reward",
                    "--prototype_disc_reward_coef", "0.1",
                    "--prototype_disc_clip", "2.0",
                    "--prototype_disc_warmup_steps", "20000"
                )
            }
            "a2r_roster_coef005" {
                Invoke-R16Run "a2r_roster_reward_coef005" $seed @(
                    "--ar_prefix_mode", "roster",
                    "--enable_prototype_disc_reward",
                    "--prototype_disc_reward_coef", "0.05",
                    "--prototype_disc_clip", "2.0",
                    "--prototype_disc_warmup_steps", "20000"
                )
            }
            "a2_samecheck_reward" {
                Invoke-R16Run "a2_samecheck_reward_coef01" $seed @(
                    "--ar_prefix_mode", "same_check",
                    "--enable_prototype_disc_reward",
                    "--prototype_disc_reward_coef", "0.1",
                    "--prototype_disc_clip", "2.0",
                    "--prototype_disc_warmup_steps", "20000"
                )
            }
            "a1r_roster_probe" {
                Invoke-R16Run "a1r_roster_probe_reward_off" $seed @(
                    "--ar_prefix_mode", "roster"
                )
            }
            default {
                throw "Unknown experiment '$exp'. Use a2r_roster_reward, a2r_roster_coef005, a2_samecheck_reward, or a1r_roster_probe."
            }
        }
    }
}
