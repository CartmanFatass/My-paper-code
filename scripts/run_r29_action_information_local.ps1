param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$MaxWorkers = 3,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$AuditScript = Join-Path $PSScriptRoot "audit_r29_action_information.py"
$SnapshotRoot = Join-Path $RepoDir "dist\r27_g1_capacity_autopsy_cloud64_20260712_151313_extracted\logs\r27_g1_capacity_autopsy_cloud64_20260712_151313"
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir ("logs\r29_action_information_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
if ($MaxWorkers -lt 1 -or $MaxWorkers -gt 3) {
    throw "MaxWorkers must be in 1..3."
}

$Sources = @(
    [pscustomobject]@{
        Id = "arm0_update25"
        Update = 25
        Checkpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_update_25.pt"
    },
    [pscustomobject]@{
        Id = "arm0_update30"
        Update = 30
        Checkpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_update_30.pt"
    },
    [pscustomobject]@{
        Id = "arm0_final"
        Update = 32
        Checkpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_final.pt"
    }
)

function Get-CheckpointArgs([object]$Source) {
    return @(
        $AuditScript, "checkpoint",
        "--checkpoint", $Source.Checkpoint,
        "--checkpoint-id", $Source.Id,
        "--checkpoint-update", [string]$Source.Update,
        "--snapshot-dir", (Join-Path $SnapshotRoot "$($Source.Id)\capacity_snapshots"),
        "--output-dir", (Join-Path $RunRoot $Source.Id),
        "--device", "cuda"
    )
}

if ($DryRun) {
    foreach ($source in $Sources) {
        $command = @($PythonBin) + @(Get-CheckpointArgs $source)
        Write-Output ($command -join " ")
    }
    Write-Output "$PythonBin $AuditScript aggregate --run-root $RunRoot"
    return
}

foreach ($required in @($PythonBin, $AuditScript)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file is missing: $required"
    }
}
foreach ($source in $Sources) {
    $snapshotDir = Join-Path $SnapshotRoot "$($source.Id)\capacity_snapshots"
    if (-not (Test-Path -LiteralPath $source.Checkpoint -PathType Leaf)) {
        throw "Checkpoint is missing: $($source.Checkpoint)"
    }
    if (-not (Test-Path -LiteralPath $snapshotDir -PathType Container)) {
        throw "Snapshot directory is missing: $snapshotDir"
    }
}
if (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists: $RunRoot"
}
& $PythonBin -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 2)"
if ($LASTEXITCODE -ne 0) {
    throw "CUDA is unavailable; CPU fallback is forbidden."
}

New-Item -ItemType Directory -Path $RunRoot | Out-Null
$active = [System.Collections.Generic.List[object]]::new()

function Receive-Finished([switch]$WaitForOne) {
    do {
        $finished = @($active | Where-Object { $_.Process.HasExited })
        if ($finished.Count -eq 0 -and $WaitForOne) {
            Start-Sleep -Milliseconds 250
        }
    } while ($finished.Count -eq 0 -and $WaitForOne)
    foreach ($job in $finished) {
        $job.Process.WaitForExit()
        [void]$active.Remove($job)
        $job.Process.Dispose()
    }
}

foreach ($source in $Sources) {
    while ($active.Count -ge $MaxWorkers) {
        Receive-Finished -WaitForOne
    }
    $outputDir = Join-Path $RunRoot $source.Id
    New-Item -ItemType Directory -Path $outputDir | Out-Null
    $process = Start-Process `
        -FilePath $PythonBin `
        -ArgumentList (Get-CheckpointArgs $source) `
        -WorkingDirectory $RepoDir `
        -RedirectStandardOutput (Join-Path $outputDir "runner_stdout.log") `
        -RedirectStandardError (Join-Path $outputDir "runner_stderr.log") `
        -WindowStyle Hidden `
        -PassThru
    $active.Add([pscustomobject]@{ Id = $source.Id; Process = $process })
}
while ($active.Count -gt 0) {
    Receive-Finished -WaitForOne
}
$failed = [System.Collections.Generic.List[string]]::new()
foreach ($source in $Sources) {
    $reportPath = Join-Path $RunRoot "$($source.Id)\r29_action_information.json"
    if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
        $failed.Add("checkpoint=$($source.Id) report_missing")
        continue
    }
    try {
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        if ($report.experiment_id -ne "EXP-20260713-r29-g0-counterfactual-action-information" -or $report.checkpoint_id -ne $source.Id) {
            $failed.Add("checkpoint=$($source.Id) report_identity")
        }
    }
    catch {
        $failed.Add("checkpoint=$($source.Id) report_parse")
    }
}
if ($failed.Count -gt 0) {
    throw "Checkpoint workers failed: $($failed -join ', ')"
}

& $PythonBin $AuditScript aggregate --run-root $RunRoot
if ($LASTEXITCODE -ne 0) {
    throw "R29 aggregate failed."
}
Write-Output "RUN_ROOT=$RunRoot"
