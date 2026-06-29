param(
    [string]$PythonExe = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [ValidateSet(
        "all",
        "base_reward_pure",
        "duration_short_reward_pure",
        "fixed_duration_reward_pure",
        "low_actor_g_reward_pure",
        "topology_role_probe",
        "topology_role_low_reward",
        "topology_potential_low_reward",
        "transition_semantic_low_reward",
        "topology_role_transition_combo"
    )]
    [string[]]$Experiment = @("base_reward_pure", "topology_role_probe", "topology_role_low_reward", "transition_semantic_low_reward"),
    [int]$TotalTimesteps = 320000,
    [int]$EvalInterval = 80000,
    [int]$EvalEpisodes = 20,
    [int]$NumEnvs = 8,
    [int]$RolloutLength = 500,
    [int]$SkillInterval = 10,
    [int]$NAgents = 6,
    [string]$Seeds = "1",
    [string]$Preset = "S7-S1",
    [string]$Scenario = "energy",
    [string]$CollectorBackend = "subproc",
    [string]$CollectorStartMethod = "spawn",
    [string]$SkillLifetimeCandidates = "3,7,13,24",
    [double]$SmdpBootstrapCoef = 0.25,
    [string]$LogRoot = "logs",
    [ValidateSet("cpu", "cuda")]
    [string]$Device = "cpu",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Join-ArgList {
    param([string[]]$Items)
    return ($Items | ForEach-Object {
        if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
    }) -join " "
}

function Invoke-HaCtseRun {
    param(
        [string]$Name,
        [int]$Seed,
        [string[]]$ExtraArgs,
        [string]$RunSkillLifetimeCandidates = $SkillLifetimeCandidates
    )

    $logDir = Join-Path $LogRoot ("ha_ctse_process_{0}_seed{1}_{2}k" -f $Name, $Seed, [int]($TotalTimesteps / 1000))
    $common = @(
        "-m", "ha_ctse_process.train",
        "--config", "ha_ctse_process.config",
        "--scenario", $Scenario,
        "--preset", $Preset,
        "--seed", "$Seed",
        "--n_agents", "$NAgents",
        "--collector_backend", $CollectorBackend,
        "--collector_start_method", $CollectorStartMethod,
        "--num_envs", "$NumEnvs",
        "--rollout_length", "$RolloutLength",
        "--skill_interval", "$SkillInterval",
        "--skill_lifetime_candidates", $RunSkillLifetimeCandidates,
        "--total_timesteps", "$TotalTimesteps",
        "--eval_interval", "$EvalInterval",
        "--eval_episodes", "$EvalEpisodes",
        "--save_interval", "20",
        "--checkpoint_keep_last", "4",
        "--plot_interval", "10",
        "--low_clip_epsilon", "0.1",
        "--smdp_bootstrap_coef", "$SmdpBootstrapCoef",
        "--device", $Device,
        "--log_dir", $logDir
    )

    $cmdArgs = @($common + $ExtraArgs)
    Write-Host ""
    Write-Host "===== HA-CTSE experiment: $Name seed=$Seed ====="
    Write-Host "& `"$PythonExe`" $(Join-ArgList $cmdArgs)"
    if ($DryRun) {
        return
    }
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    & $PythonExe @cmdArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Experiment $Name failed with exit code $LASTEXITCODE"
    }
}

if ($Experiment -contains "all") {
    $Experiment = @(
        "base_reward_pure",
        "duration_short_reward_pure",
        "fixed_duration_reward_pure",
        "low_actor_g_reward_pure",
        "topology_role_probe",
        "topology_role_low_reward",
        "topology_potential_low_reward",
        "transition_semantic_low_reward",
        "topology_role_transition_combo"
    )
}

$SeedList = @()
foreach ($chunk in ($Seeds -split ",")) {
    $trimmed = $chunk.Trim()
    if ($trimmed.Length -gt 0) {
        $SeedList += [int]$trimmed
    }
}
if ($SeedList.Count -eq 0) {
    throw "At least one seed is required"
}

$isolatedProcessOff = @(
    "--process_reward_injection", "none",
    "--process_reward_coef", "0.0",
    "--process_contrast_coef", "0.0",
    "--process_outcome_coef", "0.0",
    "--process_prior_coef", "0.0",
    "--process_shortcut_coef", "0.0",
    "--context_shortcut_coef", "0.0",
    "--process_shortcut_margin_coef", "0.0",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe"
)

foreach ($item in $Experiment) {
    foreach ($Seed in $SeedList) {
        switch ($item) {
            "base_reward_pure" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_base_reward_pure_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_process_reward",
                            "--disable_transition_skill_discriminator",
                            "--disable_topology_role_probe"
                        )
                    )
            }
            "duration_short_reward_pure" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_duration_short_reward_pure_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -RunSkillLifetimeCandidates "1,2,3" `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_process_reward",
                            "--disable_transition_skill_discriminator",
                            "--disable_topology_role_probe"
                        )
                    )
            }
            "fixed_duration_reward_pure" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_fixed_duration7_reward_pure_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -RunSkillLifetimeCandidates "7" `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_process_reward",
                            "--disable_transition_skill_discriminator",
                            "--disable_topology_role_probe"
                        )
                    )
            }
            "low_actor_g_reward_pure" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_low_actor_g_reward_pure_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--enable_low_actor_team_code",
                            "--disable_process_reward",
                            "--disable_transition_skill_discriminator",
                            "--disable_topology_role_probe"
                        )
                    )
            }
            "topology_role_probe" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_topology_role_probe_no_reward_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_process_reward",
                            "--disable_transition_skill_discriminator",
                            "--topology_role_coef", "1.0",
                            "--topology_role_injection", "none",
                            "--topology_role_reward_coef", "0.0"
                        )
                    )
            }
            "topology_role_low_reward" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_topology_role_low_reward_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_transition_skill_discriminator",
                            "--topology_role_coef", "1.0",
                            "--topology_role_injection", "low_only",
                            "--topology_role_reward_coef", "0.02",
                            "--topology_role_reward_clip", "0.03"
                        )
                    )
            }
            "topology_potential_low_reward" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_topology_potential_short_low_reward_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -RunSkillLifetimeCandidates "1,2,3" `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_transition_skill_discriminator",
                            "--disable_topology_role_probe",
                            "--enable_topology_potential_shaping",
                            "--topology_potential_injection", "low_only",
                            "--topology_potential_coef", "0.05",
                            "--topology_potential_clip", "0.08",
                            "--topology_potential_discount_mode", "delta",
                            "--topology_potential_warmup_steps", "0"
                        )
                    )
            }
            "transition_semantic_low_reward" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_transition_semantic_low_reward_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--disable_topology_role_probe",
                            "--transition_skill_coef", "0.5",
                            "--transition_skill_prior_coef", "0.25",
                            "--transition_context_shortcut_coef", "0.25",
                            "--transition_skill_reward_coef", "0.02",
                            "--transition_skill_reward_clip", "0.05",
                            "--transition_skill_reward_warmup_steps", "80000"
                        )
                    )
            }
            "topology_role_transition_combo" {
                Invoke-HaCtseRun `
                    -Name ("s7s1_topology_role_transition_combo_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $isolatedProcessOff +
                        @(
                            "--topology_role_coef", "1.0",
                            "--topology_role_injection", "low_only",
                            "--topology_role_reward_coef", "0.02",
                            "--topology_role_reward_clip", "0.03",
                            "--transition_skill_coef", "0.5",
                            "--transition_skill_prior_coef", "0.25",
                            "--transition_context_shortcut_coef", "0.25",
                            "--transition_skill_reward_coef", "0.01",
                            "--transition_skill_reward_clip", "0.03",
                            "--transition_skill_reward_warmup_steps", "80000"
                        )
                    )
            }
        }
    }
}
