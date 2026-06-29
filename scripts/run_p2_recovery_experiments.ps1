# P2-lite: recovery-window contribution credit runner (PowerShell).
#
# Staged per the P2-lite gate (memory/ALGORITHM_PRINCIPLES.md ->
# "P2-lite: Recovery-Window Contribution Credit"):
#   1. p2_recovery_precheck  -> compute-on / reward-OFF.  MANDATORY FIRST.
#        Verify Pre-check 2 before enabling any reward:
#          delta_phi_soft_nonzero_rate_when_full_disconnect > 0
#          delta_phi_soft_nonzero_rate_when_near_disconnect  > 0
#          p2_corr_phi_recovery_event                        > 0
#   2. p2_recovery_h0  -> high_team signed shaping reward (first mainline reward).
#   3. p2_recovery_h1  -> high_per_agent signed shaping reward.
#   4. p2_recovery_l1  -> low_only positive-only ablation.
#
# All runs use a SHORT-duration reward-pure base (P0.3 decision); everything else
# intrinsic stays OFF so P2 is the only moving variable.
param(
    [string]$PythonExe = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [ValidateSet(
        "all",
        "p2_recovery_precheck",
        "p2_recovery_h0",
        "p2_recovery_h1",
        "p2_recovery_l1"
    )]
    [string[]]$Experiment = @("p2_recovery_precheck"),
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
    [string]$SkillLifetimeCandidates = "1,2,3",
    [double]$SmdpBootstrapCoef = 0.25,
    [double]$P2RewardCoef = 0.05,
    [double]$P2RewardClip = 0.5,
    [string]$LogRoot = "logs",
    [ValidateSet("cpu", "cuda")]
    [string]$Device = "cpu",
    [switch]$SkipGate,
    [string]$GateCsv = "",
    [double]$GateMinDeltaPhi = 0.0,
    [double]$GateMinCorr = 0.0,
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
        [string[]]$ExtraArgs
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
        "--skill_lifetime_candidates", $SkillLifetimeCandidates,
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
    Write-Host "===== P2-lite experiment: $Name seed=$Seed ====="
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

$script:GateDone = $false
# Evaluate the Pre-check 2 gate once, lazily, right before the first reward variant.
# In `all` mode this runs AFTER the precheck has produced its CSV; in a reward-only
# invocation it gates on a pre-existing precheck CSV.
function Assert-PrecheckGate {
    if ($SkipGate -or $script:GateDone) { return }
    $script:GateDone = $true
    if ($DryRun) {
        Write-Host "[p2-gate] dry-run: skipping gate evaluation"
        return
    }
    $gateScript = Join-Path $PSScriptRoot "p2_gate_check.py"
    $gateArgs = @(
        $gateScript,
        "--log-root", $LogRoot,
        "--min-delta-phi", "$GateMinDeltaPhi",
        "--min-corr", "$GateMinCorr"
    )
    if ($GateCsv) { $gateArgs += @("--gate-csv", $GateCsv) }
    Write-Host ""
    Write-Host "----- P2 Pre-check 2 gate (reward variants require a positive precheck) -----"
    & $PythonExe @gateArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Aborting reward variants: precheck gate not satisfied (exit $LASTEXITCODE). Pass -SkipGate to override."
    }
}

if ($Experiment -contains "all") {
    $Experiment = @("p2_recovery_precheck", "p2_recovery_h0", "p2_recovery_h1", "p2_recovery_l1")
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

# Short-duration reward-pure base: everything intrinsic OFF except the P2 path.
$rewardPureBase = @(
    "--process_reward_injection", "none",
    "--process_reward_coef", "0.0",
    "--process_contrast_coef", "0.0",
    "--process_outcome_coef", "0.0",
    "--process_prior_coef", "0.0",
    "--process_shortcut_coef", "0.0",
    "--context_shortcut_coef", "0.0",
    "--process_shortcut_margin_coef", "0.0",
    "--disable_process_posterior_mi",
    "--disable_outcome_residual_probe",
    "--disable_process_reward",
    "--disable_transition_skill_discriminator",
    "--disable_topology_role_probe"
)

foreach ($item in $Experiment) {
    foreach ($Seed in $SeedList) {
        switch ($item) {
            "p2_recovery_precheck" {
                # Compute-on / reward-OFF.  MANDATORY first run (validates Pre-check 2).
                Invoke-HaCtseRun `
                    -Name ("s7s1_p2_recovery_precheck_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @($rewardPureBase + @("--enable_p2_recovery_compute"))
            }
            "p2_recovery_h0" {
                # High-level shared signed Phi_total reward (first mainline reward run).
                Assert-PrecheckGate
                Invoke-HaCtseRun `
                    -Name ("s7s1_p2_recovery_h0_high_team_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $rewardPureBase +
                        @(
                            "--enable_p2_recovery_reward",
                            "--p2_recovery_reward_level", "high_team",
                            "--p2_recovery_reward_coef", "$P2RewardCoef",
                            "--p2_recovery_reward_clip", "$P2RewardClip"
                        )
                    )
            }
            "p2_recovery_h1" {
                # Per-agent signed phi_i high-level credit.
                Assert-PrecheckGate
                Invoke-HaCtseRun `
                    -Name ("s7s1_p2_recovery_h1_per_agent_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $rewardPureBase +
                        @(
                            "--enable_p2_recovery_reward",
                            "--p2_recovery_reward_level", "high_per_agent",
                            "--p2_recovery_reward_coef", "$P2RewardCoef",
                            "--p2_recovery_reward_clip", "$P2RewardClip"
                        )
                    )
            }
            "p2_recovery_l1" {
                # Low-level positive-only ablation (NOT the mainline conclusion).
                Assert-PrecheckGate
                Invoke-HaCtseRun `
                    -Name ("s7s1_p2_recovery_l1_low_only_{0}env" -f $NumEnvs) `
                    -Seed $Seed `
                    -ExtraArgs @(
                        $rewardPureBase +
                        @(
                            "--enable_p2_recovery_reward",
                            "--p2_recovery_reward_level", "low_only",
                            "--p2_recovery_reward_coef", "$P2RewardCoef",
                            "--p2_recovery_reward_clip", "$P2RewardClip"
                        )
                    )
            }
        }
    }
}
