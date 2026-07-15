<#
HA-CTSE R23-next mechanism matrix local runner (Windows / CUDA mirror of the cloud .sh).

Four arms (see docs/research/designs/R23_ACTIONABLE_TEAM_INTENT.md section 11):
  arm0_arch_only : Z residual capacity path only (known-pass control).
  arm1_qA_probe  : + q_A residual actionability PROBE (reward off).
  arm2_qA_reward : + small q_A residual REWARD (high-level only, gated on residual_gain>0).
  arm3_qD_audit  : reward-off q_D effect-target/timescale audit
                   {s_next,joint_action,joint_effect,delta_omega} x H{10,20,50}.
q_D reward is OFF everywhere. 320k mechanism read, NOT 960k parity.

Usage:
  powershell -File scripts/run_r23_next_mechanism_matrix_local_cuda.ps1 -DryRun
  powershell -File scripts/run_r23_next_mechanism_matrix_local_cuda.ps1 -Experiments arm1_qA_probe -Seeds 1
#>
param(
  [string]$Experiments = "arm0_arch_only,arm1_qA_probe,arm2_qA_reward,arm3_qD_audit",
  [string]$Seeds = "1",
  [int]$TotalTimesteps = 320000,
  [int]$NumEnvs = 8,
  [string]$Device = "cuda",
  [string]$LogRoot = "logs_r23_next_mechanism_matrix_local",
  [string]$Python = "python",
  [double]$ZGain = 0.5,
  [int]$TeamIntentK = 8,
  [string]$Durations = "1,2,3,4",
  [double]$QaCoef = 0.02,
  [double]$QaClip = 1.0,
  [int]$QaWarmup = 20000,
  [string]$QdAuditTargets = "s_next,joint_action,joint_effect,delta_omega",
  [string]$QdAuditHorizons = "10,20,50",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Test-Path "ha_ctse_process/train.py")) {
  Write-Error "Run from the HMASD repo root (scripts/ under the repo root)."
  exit 2
}

$common = @(
  "-m", "ha_ctse_process.train",
  "--config", "ha_ctse_process.config",
  "--scenario", "energy", "--preset", "S7-S1", "--n_agents", "6",
  "--collector_backend", "subproc", "--collector_start_method", "spawn",
  "--num_envs", "$NumEnvs", "--rollout_length", "500", "--skill_interval", "10",
  "--skill_lifetime_candidates", "$Durations",
  "--total_timesteps", "$TotalTimesteps",
  "--eval_interval", "160000", "--eval_episodes", "20",
  "--save_interval", "20", "--checkpoint_keep_last", "4", "--plot_interval", "10",
  "--low_clip_epsilon", "0.1", "--smdp_bootstrap_coef", "0.25", "--device", "$Device",
  "--opt_num_prototypes", "4", "--prototype_skill_extra_codes", "0",
  "--team_bridge_type", "stochastic", "--enable_situation_diagnostics",
  "--enable_prototype_response_skills", "--enable_high_omega_conditioning",
  "--enable_agent_prototype_relevance", "--enable_per_agent_kappa",
  "--enable_prototype_disc_probe", "--prototype_disc_condition", "kappa",
  "--enable_prototype_disc_reward", "--prototype_disc_reward_coef", "0.05",
  "--prototype_disc_clip", "2.0", "--prototype_disc_warmup_steps", "20000",
  "--reward_ratio_guard_mode", "kill",
  "--disable_process_reward", "--disable_process_posterior_mi",
  "--disable_outcome_residual_probe", "--disable_topology_role_probe",
  "--disable_transition_skill_discriminator"
)

function Get-ArmArgs([string]$exp) {
  $base = @(
    "--enable_team_intent", "--enable_team_disc_probe",
    "--team_intent_k", "$TeamIntentK",
    "--z_assignment_residual_gain", "$ZGain"
  )
  switch ($exp) {
    "arm0_arch_only" { return @{ name = "arm0_arch_only"; args = $base } }
    "arm1_qA_probe"  { return @{ name = "arm1_qA_probe"; args = $base + @("--enable_assignment_actionability_probe") } }
    "arm2_qA_reward" {
      $n = "arm2_qA_reward_coef" + ("$QaCoef" -replace '\.', '')
      return @{ name = $n; args = $base + @(
        "--enable_assignment_actionability_reward",
        "--assignment_actionability_coef", "$QaCoef",
        "--assignment_actionability_clip", "$QaClip",
        "--assignment_actionability_warmup_steps", "$QaWarmup") }
    }
    "arm3_qD_audit" {
      return @{ name = "arm3_qD_audit"; args = $base + @(
        "--enable_team_effect_target_audit",
        "--team_effect_audit_targets", "$QdAuditTargets",
        "--team_effect_audit_horizons", "$QdAuditHorizons") }
    }
    default { throw "Unknown experiment '$exp'." }
  }
}

$expList = $Experiments.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$seedList = $Seeds.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }

Write-Host "R23-next mechanism matrix (local): experiments=$Experiments seeds=$Seeds num_envs=$NumEnvs total=$TotalTimesteps device=$Device dry_run=$DryRun"

foreach ($seed in $seedList) {
  foreach ($exp in $expList) {
    $arm = Get-ArmArgs $exp
    $logDir = Join-Path $LogRoot "seed$seed/$($arm.name)"
    $cmd = $common + @("--seed", "$seed") + $arm.args + @("--log_dir", $logDir)
    Write-Host "`n===== R23-next matrix: $($arm.name) seed=$seed ====="
    Write-Host "$Python $($cmd -join ' ')"
    if (-not $DryRun) {
      New-Item -ItemType Directory -Force -Path $logDir | Out-Null
      & $Python @cmd
      if ($LASTEXITCODE -ne 0) { Write-Error "Arm $($arm.name) seed=$seed failed ($LASTEXITCODE)"; exit $LASTEXITCODE }
    }
  }
}
