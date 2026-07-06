param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$SourceRun = "logs\ha_ctse_r16_a2r_overnight_local_cuda\run_20260704_142053\seed1\a2r_roster_reward_coef01",
    [string]$LogRoot = "logs\ha_ctse_r16_5_p2_eval_modes\run_20260704_142053",
    [int]$Seed = 1,
    [int]$EvalEpisodes = 20,
    [string]$Device = "cuda",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

$checks = @(
    @{ Update = "update_60"; Checkpoint = "standalone_process_core_update_60.pt" },
    @{ Update = "update_120"; Checkpoint = "standalone_process_core_update_120.pt" }
)
$modes = @("deterministic", "stochastic")

foreach ($check in $checks) {
    $checkpoint = Join-Path $SourceRun $check.Checkpoint
    if (-not (Test-Path $checkpoint)) {
        throw "Missing checkpoint: $checkpoint"
    }
    foreach ($mode in $modes) {
        $logDir = Join-Path $LogRoot (Join-Path $check.Update $mode)
        $command = @(
            $Python,
            "-m", "ha_ctse_process.train",
            "--config", "ha_ctse_process.config",
            "--mode", "eval",
            "--scenario", "energy",
            "--preset", "S7-S1",
            "--seed", "$Seed",
            "--n_agents", "6",
            "--skill_interval", "10",
            "--eval_episodes", "$EvalEpisodes",
            "--eval_action_mode", $mode,
            "--device", $Device,
            "--resume_from", $checkpoint,
            "--log_dir", $logDir
        )
        $line = (($command | ForEach-Object {
            if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
        }) -join " ")
        Write-Host ""
        Write-Host "===== R16.5 P2 eval: $($check.Update) $mode ====="
        Write-Host $line
        if ($DryRun) {
            continue
        }
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        $line | Set-Content -Path (Join-Path $logDir "command.txt") -Encoding UTF8
        & $Python @($command | Select-Object -Skip 1)
        if ($LASTEXITCODE -ne 0) {
            throw "Eval failed for $($check.Update) $mode with exit code $LASTEXITCODE"
        }
    }
}
