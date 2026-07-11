<#
Sequential local-CUDA runner for the frozen R27-G1 low-actor capacity autopsy.

Use -DryRun to inspect the exact three-checkpoint identity without creating
output or requiring the checkpoints to exist.
#>
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [string]$Device = "cuda",
    [int]$NResets = 64,
    [switch]$DryRun,
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

function Write-RunnerStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string[]]$Lines
    )
    $Lines | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Invoke-PythonPhase {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$LogPath
    )
    $previousErrorActionPreference = $ErrorActionPreference
    $exitCode = 1
    try {
        $ErrorActionPreference = "Continue"
        & $Python @Arguments 2>&1 | Tee-Object -FilePath $LogPath | Out-Host
        $exitCode = $LASTEXITCODE
    } catch {
        $_ | Out-File -LiteralPath $LogPath -Append -Encoding UTF8
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    return $exitCode
}

if ($Device -cnotmatch '^cuda(?::\d+)?$') {
    throw "R27-G1 capacity autopsy requires -Device cuda; CPU fallback is forbidden."
}
if ($NResets -ne 64) {
    throw "R27-G1 scientific contract requires -NResets 64."
}
if (-not (Test-Path -LiteralPath "scripts\audit_r27_low_actor_capacity.py" -PathType Leaf)) {
    throw "Run this script from the HMASD repository root."
}
if ([string]::IsNullOrWhiteSpace($RunRoot)) {
    $RunRoot = "logs/r27_g1_capacity_autopsy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
}

$arms = @(
    @{
        Name = "arm0_update25"
        Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt"
        Update = 25
    },
    @{
        Name = "arm0_update30"
        Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt"
        Update = 30
    },
    @{
        Name = "arm0_final"
        Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt"
        Update = 32
    }
)

if (-not $DryRun) {
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Python executable not found: $Python"
    }
    $missingCheckpoints = @(
        $arms |
            Where-Object { -not (Test-Path -LiteralPath $_.Checkpoint -PathType Leaf) } |
            ForEach-Object { $_.Checkpoint }
    )
    if ($missingCheckpoints.Count -gt 0) {
        $message = "Required checkpoints not found:" + [Environment]::NewLine
        $message += $missingCheckpoints -join [Environment]::NewLine
        throw $message
    }
}

Write-Host "R27-G1 low-actor capacity autopsy runner"
Write-Host "  python:             $Python"
Write-Host "  run_root:           $RunRoot"
Write-Host "  device:             $Device"
Write-Host "  n_resets:           $NResets"
Write-Host "  dry_run:            $DryRun"
Write-Host "  continue_on_error:  $ContinueOnError"

$batchStatusPath = Join-Path $RunRoot "batch_status.txt"
$failures = [System.Collections.Generic.List[string]]::new()
$results = [System.Collections.Generic.List[string]]::new()
$successfulArms = [System.Collections.Generic.List[string]]::new()

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
    Write-RunnerStatus -Path $batchStatusPath -Lines @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "phase=collect-static"
        "device=$Device"
        "n_resets=$NResets"
        "arm_count=$($arms.Count)"
    )
}

foreach ($arm in $arms) {
    $armRoot = Join-Path $RunRoot $arm.Name
    $commandPath = Join-Path $armRoot "command.txt"
    $runnerStatusPath = Join-Path $armRoot "runner_status.txt"
    $phaseLogPath = Join-Path $armRoot "collector_static_output.log"
    $arguments = @(
        "scripts/audit_r27_low_actor_capacity.py",
        "collect-static",
        "--checkpoint", $arm.Checkpoint,
        "--output-dir", $armRoot,
        "--checkpoint-id", $arm.Name,
        "--checkpoint-update", "$($arm.Update)",
        "--device", $Device,
        "--n-resets", "$NResets"
    )
    $command = Format-CommandLine -Command (@($Python) + $arguments)

    Write-Host ""
    Write-Host "PHASE collect-static $($arm.Name)"
    Write-Host "  checkpoint:       $($arm.Checkpoint)"
    Write-Host "  command.txt:      $commandPath"
    Write-Host "  runner_status:    $runnerStatusPath"
    Write-Host "  output_log:       $phaseLogPath"
    Write-Host "COMMAND: $command"
    if ($DryRun) {
        continue
    }

    New-Item -ItemType Directory -Force -Path $armRoot | Out-Null
    $command | Set-Content -LiteralPath $commandPath -Encoding UTF8
    Write-RunnerStatus -Path $runnerStatusPath -Lines @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "phase=collect-static"
        "arm=$($arm.Name)"
    )
    Write-RunnerStatus -Path $batchStatusPath -Lines @(
        "updated=$(Get-Date -Format o)"
        "state=running"
        "phase=collect-static"
        "current_arm=$($arm.Name)"
        $results
    )

    $exitCode = Invoke-PythonPhase -Arguments $arguments -LogPath $phaseLogPath
    $failure = $null
    if ($exitCode -ne 0) {
        $failure = "collect-static failed with exit code $exitCode"
    } elseif (-not (Test-Path -LiteralPath (Join-Path $armRoot "collector_manifest.json") -PathType Leaf)) {
        $failure = "collector_manifest.json is missing"
    } elseif (-not (Test-Path -LiteralPath (Join-Path $armRoot "static_capacity.json") -PathType Leaf)) {
        $failure = "static_capacity.json is missing"
    }

    if ($null -eq $failure) {
        Write-RunnerStatus -Path $runnerStatusPath -Lines @(
            "finished=$(Get-Date -Format o)"
            "state=succeeded"
            "phase=collect-static"
            "arm=$($arm.Name)"
        )
        $successfulArms.Add($arm.Name)
        $results.Add("$($arm.Name)=succeeded")
        continue
    }

    Write-RunnerStatus -Path $runnerStatusPath -Lines @(
        "finished=$(Get-Date -Format o)"
        "state=failed"
        "phase=collect-static"
        "arm=$($arm.Name)"
        "error=$failure"
    )
    $failures.Add($arm.Name)
    $results.Add("$($arm.Name)=failed: $failure")
    Write-Warning "Arm '$($arm.Name)' failed: $failure"
    if (-not $ContinueOnError) {
        break
    }
}

$finalArm = $arms[-1]
$syntheticArguments = @(
    "scripts/audit_r27_low_actor_capacity.py",
    "synthetic",
    "--checkpoint", $finalArm.Checkpoint,
    "--snapshot-dir", (Join-Path (Join-Path $RunRoot $finalArm.Name) "capacity_snapshots"),
    "--output-dir", $RunRoot,
    "--device", $Device
)
$syntheticCommand = Format-CommandLine -Command (@($Python) + $syntheticArguments)
Write-Host ""
Write-Host "PHASE synthetic"
Write-Host "COMMAND: $syntheticCommand"

if (-not $DryRun -and $successfulArms.Count -eq $arms.Count) {
    $syntheticCommand | Set-Content -LiteralPath (Join-Path $RunRoot "synthetic_command.txt") -Encoding UTF8
    Write-RunnerStatus -Path $batchStatusPath -Lines @(
        "updated=$(Get-Date -Format o)"
        "state=running"
        "phase=synthetic"
        $results
    )
    $syntheticExit = Invoke-PythonPhase -Arguments $syntheticArguments -LogPath (Join-Path $RunRoot "synthetic_output.log")
    if ($syntheticExit -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $RunRoot "synthetic_control.json") -PathType Leaf)) {
        $failures.Add("synthetic")
        $results.Add("synthetic=failed: exit_code=$syntheticExit")
    } else {
        $results.Add("synthetic=succeeded")
    }
} elseif (-not $DryRun) {
    $failures.Add("synthetic")
    $results.Add("synthetic=skipped: not all collect-static phases succeeded")
}

$aggregateArguments = @(
    "scripts/audit_r27_low_actor_capacity.py",
    "aggregate",
    "--run-root", $RunRoot,
    "--checkpoint-ids", "arm0_update25", "arm0_update30", "arm0_final"
)
$aggregateCommand = Format-CommandLine -Command (@($Python) + $aggregateArguments)
Write-Host ""
Write-Host "PHASE aggregate"
Write-Host "COMMAND: $aggregateCommand"

if (-not $DryRun -and $failures.Count -eq 0) {
    $aggregateCommand | Set-Content -LiteralPath (Join-Path $RunRoot "aggregate_command.txt") -Encoding UTF8
    Write-RunnerStatus -Path $batchStatusPath -Lines @(
        "updated=$(Get-Date -Format o)"
        "state=running"
        "phase=aggregate"
        $results
    )
    $aggregateExit = Invoke-PythonPhase -Arguments $aggregateArguments -LogPath (Join-Path $RunRoot "aggregate_output.log")
    if ($aggregateExit -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $RunRoot "r27_capacity_autopsy.json") -PathType Leaf)) {
        $failures.Add("aggregate")
        $results.Add("aggregate=failed: exit_code=$aggregateExit")
    } else {
        $results.Add("aggregate=succeeded")
    }
} elseif (-not $DryRun) {
    $results.Add("aggregate=skipped: required phase failed")
}

if (-not $DryRun) {
    Write-RunnerStatus -Path $batchStatusPath -Lines @(
        "finished=$(Get-Date -Format o)"
        "state=$(if ($failures.Count -eq 0) { 'succeeded' } else { 'failed' })"
        "failed_phases=$($failures -join ',')"
        $results
    )
}

if ($failures.Count -gt 0) {
    exit 1
}

Write-Host ""
Write-Host "R27-G1 capacity autopsy runner completed successfully."
