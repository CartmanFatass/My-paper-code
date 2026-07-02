param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string[]]$Experiment = @(
        "k_full_sync",
        "k_fixed_d7",
        "k_decoupled_short",
        "k_decoupled_mixed",
        "p2_precheck",
        "p1_low_pos_probe"
    ),
    [int]$Seed = 1,
    [int]$NumEnvs = 4,
    [int]$TotalTimesteps = 160000,
    [int]$EvalInterval = 40000,
    [int]$EvalEpisodes = 8,
    [int]$RolloutLength = 250,
    [string]$LogRoot = "logs\local_s7s1_overnight",
    [string]$Device = "cpu",
    [ValidateSet("sync", "subproc")]
    [string]$CollectorBackend = "sync",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$runner = Join-Path $PSScriptRoot "run_s7s1_local_quick.ps1"
$summary = Join-Path $PSScriptRoot "summarize_ha_ctse_runs.py"

Write-Host "HA-CTSE local overnight validation"
Write-Host "  purpose: reward-pure K gate + P2 compute precheck + weak P1 probe"
Write-Host "  log_root: $LogRoot"
Write-Host "  collector: $CollectorBackend"
Write-Host "  experiments: $($Experiment -join ',')"

$runnerArgs = @{
    Python = $Python
    Experiment = $Experiment
    Seed = $Seed
    NumEnvs = $NumEnvs
    TotalTimesteps = $TotalTimesteps
    EvalInterval = $EvalInterval
    EvalEpisodes = $EvalEpisodes
    RolloutLength = $RolloutLength
    LogRoot = $LogRoot
    Device = $Device
    CollectorBackend = $CollectorBackend
}

if ($DryRun) {
    $runnerArgs["DryRun"] = $true
}

& $runner @runnerArgs

if (-not $DryRun) {
    Write-Host ""
    Write-Host "===== HA-CTSE local overnight summary ====="
    & $Python $summary --log-root $LogRoot --tail 5
}
