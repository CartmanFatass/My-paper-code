param(
    [string]$PythonBin = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "",
    [int]$MaxWorkers = 4,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
$AuditScript = Join-Path $PSScriptRoot "audit_r28_support_transport.py"
$Checkpoint = Join-Path $RepoDir "dist\logs_cloud_r25_qa_verification_1m\arm0_arch_only\seed1\standalone_process_core_final.pt"
$Scorer = Join-Path $RepoDir "logs\r28_g0_action_process_target_20260713_175600\r28_g0_scorer_final.pt"
if (-not $RunRoot) {
    $RunRoot = Join-Path $RepoDir ("logs\r28_support_transport_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
}
if ($MaxWorkers -lt 1 -or $MaxWorkers -gt 6) {
    throw "MaxWorkers must be in 1..6 for the local 8 GB GPU."
}

function Get-CollectArgs([int]$ResetId, [string]$OutputDir) {
    return @(
        $AuditScript, "collect-reset",
        "--checkpoint", $Checkpoint,
        "--scorer", $Scorer,
        "--reset-id", [string]$ResetId,
        "--output-dir", $OutputDir,
        "--device", "cuda"
    )
}

if ($DryRun) {
    0..63 | ForEach-Object {
        $outputDir = Join-Path $RunRoot ("resets\reset_{0:D2}" -f $_)
        $command = @($PythonBin) + @(Get-CollectArgs $_ $outputDir)
        Write-Output ($command -join " ")
    }
    Write-Output "$PythonBin $AuditScript aggregate --run-root $RunRoot"
    return
}

foreach ($required in @($PythonBin, $AuditScript, $Checkpoint, $Scorer)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required file is missing: $required"
    }
}
if (Test-Path -LiteralPath $RunRoot) {
    throw "RunRoot already exists: $RunRoot"
}
& $PythonBin -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 2)"
if ($LASTEXITCODE -ne 0) {
    throw "CUDA is unavailable; CPU fallback is forbidden."
}

New-Item -ItemType Directory -Path (Join-Path $RunRoot "resets") | Out-Null
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

foreach ($resetId in 0..63) {
    while ($active.Count -ge $MaxWorkers) {
        Receive-Finished -WaitForOne
    }
    $outputDir = Join-Path $RunRoot ("resets\reset_{0:D2}" -f $resetId)
    New-Item -ItemType Directory -Path $outputDir | Out-Null
    $stdout = Join-Path $outputDir "runner_stdout.log"
    $stderr = Join-Path $outputDir "runner_stderr.log"
    $process = Start-Process `
        -FilePath $PythonBin `
        -ArgumentList (Get-CollectArgs $resetId $outputDir) `
        -WorkingDirectory $RepoDir `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -WindowStyle Hidden `
        -PassThru
    $active.Add([pscustomobject]@{ ResetId = $resetId; Process = $process })
}
while ($active.Count -gt 0) {
    Receive-Finished -WaitForOne
}
$failed = [System.Collections.Generic.List[string]]::new()
foreach ($resetId in 0..63) {
    $manifestPath = Join-Path $RunRoot ("resets\reset_{0:D2}\reset_manifest.json" -f $resetId)
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        $failed.Add("reset=$resetId manifest_missing")
        continue
    }
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ($manifest.experiment_id -ne "EXP-20260713-r28-forced-execution-support-transport" -or $manifest.reset_id -ne $resetId -or $manifest.status -ne "OK") {
            $failed.Add("reset=$resetId manifest_invalid")
        }
    }
    catch {
        $failed.Add("reset=$resetId manifest_parse")
    }
}
if ($failed.Count -gt 0) {
    throw "Reset workers failed: $($failed -join ', ')"
}

& $PythonBin $AuditScript aggregate --run-root $RunRoot
if ($LASTEXITCODE -ne 0) {
    throw "Transport aggregate failed."
}
Write-Output "RUN_ROOT=$RunRoot"
