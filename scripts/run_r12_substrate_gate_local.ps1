param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$CheckpointDir = "logs\ha_ctse_process_s7s1_short_reward_pure_32env_seed1_1280k",
    [string]$LogDir = "logs\r12_substrate_gate_local",
    [string]$Updates = "20,40,60,final",
    [int]$EvalEpisodes = 4,
    [int]$EvalMaxSteps = 500,
    [int]$DumpInterval = 10,
    [string]$Device = "cpu",
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

$reportPath = Join-Path $LogDir "substrate_gate_report.json"

$exportCommand = @(
    $Python,
    "-m", "ha_ctse_process.export_substrate_gate",
    "--checkpoint_dir", $CheckpointDir,
    "--log_dir", $LogDir,
    "--config", "ha_ctse_process.config",
    "--scenario", "energy",
    "--preset", "S7-S1",
    "--seed", "1",
    "--n_agents", "6",
    "--skill_interval", "10",
    "--updates", $Updates,
    "--eval_episodes", "$EvalEpisodes",
    "--eval_max_steps", "$EvalMaxSteps",
    "--dump_interval", "$DumpInterval",
    "--device", $Device,
    "--require_role_label_variance",
    "--overwrite"
)

$analyzeCommand = @(
    $Python,
    "scripts/analyze_r12_substrate_gate.py",
    "--dump_dir", $LogDir,
    "--output", $reportPath,
    "--require_role_label_variance"
)

$commands = @($exportCommand, $analyzeCommand)

Write-Host "R12 substrate gate local runner"
Write-Host "  python:         $Python"
Write-Host "  checkpoint_dir: $CheckpointDir"
Write-Host "  log_dir:        $LogDir"
Write-Host "  updates:        $Updates"
Write-Host "  eval_episodes:  $EvalEpisodes"
Write-Host "  eval_max_steps: $EvalMaxSteps"
Write-Host "  dump_interval:  $DumpInterval"
Write-Host "  device:         $Device"
Write-Host "  dry_run:        $DryRun"

foreach ($command in $commands) {
    Write-Host ""
    Write-Host (Format-CommandLine -Command $command)

    if (-not $DryRun) {
        & $command[0] @($command[1..($command.Count - 1)])
        if ($LASTEXITCODE -ne 0) {
            $exitCode = $LASTEXITCODE
            Write-Error "Command failed with exit code $exitCode`: $(Format-CommandLine -Command $command)" -ErrorAction Continue
            exit $exitCode
        }
    }
}
