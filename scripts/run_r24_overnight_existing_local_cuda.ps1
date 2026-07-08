param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "logs_r24_overnight_existing_local_cuda",
    [string]$Device = "cuda",
    [int]$NResets = 64,
    [int]$TotalTimesteps = 160000,
    [int]$NumEnvs = 16,
    [switch]$IncludeBehaviorWindowQdProbe,
    [switch]$IncludeLegacyQdProbe,
    [switch]$ContinueOnError
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

function Invoke-ArmRun {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArmName,
        [Parameter(Mandatory = $true)]
        [string[]]$Command
    )

    $logDir = Join-Path $runRoot $ArmName
    $line = Format-CommandLine -Command $Command
    Write-Host ""
    Write-Host "===== R24 overnight arm: $ArmName ====="
    Write-Host $line

    New-Item -ItemType Directory -Force -Path $logDir | Out-Null

    $cmdFile = Join-Path $logDir "command.txt"
    $outputFile = Join-Path $logDir "runner_output.log"
    $statusFile = Join-Path $logDir "runner_status.txt"
    $batchFile = Join-Path $logDir "run_command.cmd"

    $line | Set-Content -Path $cmdFile -Encoding UTF8

    @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "output_file=$outputFile"
        "command_file=$cmdFile"
        "batch_file=$batchFile"
        "arm=$ArmName"
    ) | Set-Content -Path $statusFile -Encoding UTF8

    @(
        "@echo off",
        "cd /d `"$((Get-Location).Path)`"",
        "$line > `"$outputFile`" 2>&1",
        "exit /b %ERRORLEVEL%"
    ) | Set-Content -Path $batchFile -Encoding ASCII

    $exitCode = 1
    try {
        & $env:ComSpec /d /c $batchFile
        $exitCode = $LASTEXITCODE
    } catch {
        $_ | Out-File -FilePath $outputFile -Append -Encoding UTF8
        $exitCode = 1
    }

    @(
        "finished=$(Get-Date -Format o)"
        "state=finished"
        "exit_code=$exitCode"
        "output_file=$outputFile"
        "command_file=$cmdFile"
        "batch_file=$batchFile"
        "arm=$ArmName"
    ) | Set-Content -Path $statusFile -Encoding UTF8

    if ($exitCode -ne 0) {
        $message = "Arm '$ArmName' failed with exit code $exitCode; see $outputFile"
        if ($ContinueOnError) {
            Write-Warning $message
        } else {
            throw $message
        }
    }
}

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

$existingQACheckpoint = "logs_r23_next_mechanism_matrix_local\\seed1\\arm2_qA_reward_coef002\\standalone_process_core_update_40.pt"
$existingNullArchNoQaCheckpoint = "logs_r23_next_mechanism_matrix_local\\seed1\\arm0_arch_only\\standalone_process_core_final.pt"
$existingNullQdProbeNoQaCheckpoint = "logs_r23_next_mechanism_matrix_local\\seed1\\arm3_qD_audit\\standalone_process_core_update_40.pt"

foreach ($path in @($existingQACheckpoint, $existingNullArchNoQaCheckpoint, $existingNullQdProbeNoQaCheckpoint)) {
    if (-not (Test-Path $path)) {
        throw "Required existing checkpoint not found: $path"
    }
}

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runRoot = Join-Path $RunRoot ("run_$runStamp")

$forcedAudits = @(
    "arm1_qA_checkpoint_forced_audit",
    "arm2_null_arch_no_qA_forced_audit",
    "arm3_null_qD_probe_no_qA_forced_audit"
)
$forcedAuditCheckpoints = @{
    "arm1_qA_checkpoint_forced_audit" = $existingQACheckpoint
    "arm2_null_arch_no_qA_forced_audit" = $existingNullArchNoQaCheckpoint
    "arm3_null_qD_probe_no_qA_forced_audit" = $existingNullQdProbeNoQaCheckpoint
}

Write-Host "R24 overnight local CUDA existing-checkpoint runner"
Write-Host "  python:         $Python"
Write-Host "  run_root:       $runRoot"
Write-Host "  device:         $Device"
Write-Host "  n_resets:       $NResets"
Write-Host "  num_envs:       $NumEnvs"
Write-Host "  qd_timesteps:   $TotalTimesteps"
Write-Host "  include_qd:     $($IncludeBehaviorWindowQdProbe -or $IncludeLegacyQdProbe)"
Write-Host "  continue_error: $ContinueOnError"

foreach ($audit in $forcedAudits) {
    $outDir = Join-Path $runRoot $audit
    $checkpoint = $forcedAuditCheckpoints[$audit]
    $command = @(
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "scripts\\run_r24_behavior_audit_local_cuda.ps1",
        "-Checkpoint",
        $checkpoint,
        "-OutDir",
        $outDir,
        "-Python",
        $Python,
        "-Device",
        $Device,
        "-NResets",
        "$NResets"
    )
    Invoke-ArmRun -ArmName $audit -Command $command
}

if ($IncludeBehaviorWindowQdProbe -or $IncludeLegacyQdProbe) {
    Write-Host ""
    Write-Host "Optional q_d probes: current reward-off behavior-window two-stream diagnostics."
    Write-Host "Note: these are still not reward gates until held-out/null/shortcut criteria are implemented and passed."

    Invoke-ArmRun -ArmName "arm4_behavior_window_qd_probe_seed1" -Command @(
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "scripts\\run_r24_qd_probe_local_cuda.ps1",
        "-LogRoot",
        (Join-Path $runRoot "arm4_behavior_window_qd_probe_seed1"),
        "-Python",
        $Python,
        "-TotalTimesteps",
        "$TotalTimesteps",
        "-NumEnvs",
        "$NumEnvs",
        "-Seed",
        "1"
    )

    Invoke-ArmRun -ArmName "arm5_behavior_window_qd_probe_seed2" -Command @(
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "scripts\\run_r24_qd_probe_local_cuda.ps1",
        "-LogRoot",
        (Join-Path $runRoot "arm5_behavior_window_qd_probe_seed2"),
        "-Python",
        $Python,
        "-TotalTimesteps",
        "$TotalTimesteps",
        "-NumEnvs",
        "$NumEnvs",
        "-Seed",
        "2"
    )
}
