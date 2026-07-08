param(
    [string]$LogRoot = "logs_r24_qd_probe_local_cuda",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [int]$TotalTimesteps = 160000,
    [int]$NumEnvs = 16,
    [int]$Seed = 1
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

$Device = "cuda"
$LogDir = Join-Path $LogRoot "seed$Seed"

$commonArgs = @(
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
    "--disable_transition_skill_discriminator",
    "--seed", "$Seed",
    "--enable_team_intent",
    "--z_assignment_residual_gain", "1.0",
    "--enable_assignment_actionability_probe",
    "--enable_assignment_actionability_reward",
    "--assignment_actionability_coef", "0.05",
    "--enable_team_conditioned_qd_probe",
    "--log_dir", $LogDir
)

Write-Host "===== R24 behavior-window two-stream q_d reward-off probe ====="
Write-Host "log_dir:  $LogDir"
Write-Host "seed:     $Seed"
Write-Host "timesteps:$TotalTimesteps"
Write-Host "num_envs: $NumEnvs"
Write-Host "device:   $Device"
Write-Host "probe:    q_full(z_i | action/effect window_i, Z, xi_context_i, c, omega) vs q_prior"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$command = @($Python) + $commonArgs
& $command[0] @($command[1..($command.Count - 1)])
