<#
.SYNOPSIS
  Local (Windows/CUDA) runner for HA-CTSE R23 "Actionable Team Intent".
  Small-scale mirror of scripts/run_r23_actionable_team_intent_cloud_64env.sh for
  local sanity/smoke before the cloud overnight run.

  Arms (actionability-first; see docs/research/designs/R23_ACTIONABLE_TEAM_INTENT.md):
    r23_arch_only : R23-0 residual capacity path only (no objective, no q_D reward).
    r23_1_action  : + g-info actionability objective I(Z;skill). q_D probe, no reward.
    r23_3_reward  : + q_D reward HARD-GATED behind the forced-Z KL floor.

  Choice-1 timing: K_team=8, durations {1,2,3,4}.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass `
    -File .\scripts\run_r23_actionable_team_intent_local_cuda.ps1 `
    -Experiments r23_arch_only,r23_1_action,r23_3_reward -DryRun
#>
param(
  [string[]] $Experiments = @('r23_arch_only', 'r23_1_action', 'r23_3_reward'),
  [string]   $Seeds = '1',
  [int]      $TotalTimesteps = 160000,
  [int]      $NumEnvs = 16,
  [string]   $Device = 'cuda',
  [string]   $LogRoot = 'logs\ha_ctse_r23_actionable_local_cuda',
  [double]   $ZGain = 0.5,
  [int]      $TeamIntentK = 8,
  [string]   $Durations = '1,2,3,4',
  [double]   $GInfoCoef = 0.02,
  [int]      $GInfoWarmup = 20000,
  [double]   $ActionabilityFloor = 0.05,
  [double]   $TeamDiscCoef = 0.05,
  [int]      $TeamDiscWarmup = 20000,
  [switch]   $DryRun
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Test-Path 'ha_ctse_process\train.py')) {
  throw 'Run from the HMASD repo root (scripts/ must be under the repo root).'
}
$python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

$common = @(
  '-m', 'ha_ctse_process.train',
  '--config', 'ha_ctse_process.config', '--scenario', 'energy', '--preset', 'S7-S1', '--n_agents', '6',
  '--collector_backend', 'subproc', '--collector_start_method', 'spawn', '--num_envs', "$NumEnvs",
  '--rollout_length', '500', '--skill_interval', '10', '--skill_lifetime_candidates', "$Durations",
  '--total_timesteps', "$TotalTimesteps", '--eval_interval', '80000', '--eval_episodes', '10',
  '--save_interval', '20', '--checkpoint_keep_last', '4', '--plot_interval', '10',
  '--low_clip_epsilon', '0.1', '--smdp_bootstrap_coef', '0.25', '--device', "$Device",
  '--opt_num_prototypes', '4', '--prototype_skill_extra_codes', '0', '--team_bridge_type', 'stochastic',
  '--enable_situation_diagnostics', '--enable_prototype_response_skills', '--enable_high_omega_conditioning',
  '--enable_agent_prototype_relevance', '--enable_per_agent_kappa', '--enable_prototype_disc_probe',
  '--prototype_disc_condition', 'kappa', '--enable_prototype_disc_reward', '--prototype_disc_reward_coef', '0.05',
  '--prototype_disc_clip', '2.0', '--prototype_disc_warmup_steps', '20000', '--reward_ratio_guard_mode', 'kill',
  '--disable_process_reward', '--disable_process_posterior_mi', '--disable_outcome_residual_probe',
  '--disable_topology_role_probe', '--disable_transition_skill_discriminator'
)

function Get-ArmArgs([string] $exp) {
  switch ($exp) {
    'r23_arch_only' {
      return @{ Name = 'r23_arch_only'; Args = @(
        '--enable_team_intent', '--enable_team_disc_probe', '--team_intent_k', "$TeamIntentK",
        '--z_assignment_residual_gain', "$ZGain") }
    }
    'r23_1_action' {
      return @{ Name = 'r23_1_action'; Args = @(
        '--enable_team_intent', '--enable_team_disc_probe', '--team_intent_k', "$TeamIntentK",
        '--z_assignment_residual_gain', "$ZGain",
        '--enable_g_info_objective', '--g_info_coef_skill', "$GInfoCoef", '--g_info_warmup_steps', "$GInfoWarmup") }
    }
    'r23_3_reward' {
      $floorTag = ("$ActionabilityFloor" -replace '\.', '')
      return @{ Name = "r23_3_reward_floor$floorTag"; Args = @(
        '--enable_team_intent', '--enable_team_disc_reward', '--team_intent_k', "$TeamIntentK",
        '--z_assignment_residual_gain', "$ZGain",
        '--enable_g_info_objective', '--g_info_coef_skill', "$GInfoCoef", '--g_info_warmup_steps', "$GInfoWarmup",
        '--team_disc_coef', "$TeamDiscCoef", '--team_disc_clip', '2.0', '--team_disc_warmup_steps', "$TeamDiscWarmup",
        '--team_disc_actionability_floor', "$ActionabilityFloor") }
    }
    default { throw "Unknown experiment '$exp'. Use r23_arch_only, r23_1_action, or r23_3_reward." }
  }
}

Write-Host "HA-CTSE R23 local runner  experiments=$($Experiments -join ',')  seeds=$Seeds  num_envs=$NumEnvs  device=$Device  z_gain=$ZGain  K=$TeamIntentK  durations=$Durations  floor=$ActionabilityFloor  dry_run=$($DryRun.IsPresent)"

foreach ($seed in ($Seeds -split ',')) {
  $seed = $seed.Trim(); if (-not $seed) { continue }
  foreach ($exp in $Experiments) {
    $exp = $exp.Trim(); if (-not $exp) { continue }
    $arm = Get-ArmArgs $exp
    $name = $arm.Name; $extra = $arm.Args
    $logDir = Join-Path $LogRoot "seed$seed\$name"
    $cmd = @($common) + @('--seed', "$seed") + $extra + @('--log_dir', $logDir)
    Write-Host "`n===== R23 local: $name seed=$seed ====="
    Write-Host "$python $($cmd -join ' ')"
    if ($DryRun) { continue }
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    & $python @cmd
    if ($LASTEXITCODE -ne 0) { throw "Experiment $name seed=$seed failed (exit $LASTEXITCODE)." }
  }
}
