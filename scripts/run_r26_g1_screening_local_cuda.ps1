<#
Sequential local-CUDA runner for the six frozen R26-G1a checkpoints.

Use -DryRun to inspect commands and artifact paths without creating output.
#>
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$RunRoot = "logs/r26_g1a_screening",
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

if ($Device -cne "cuda") {
    throw "R26-G1a screening requires -Device cuda; CPU fallback is forbidden."
}
if ($NResets -le 0) {
    throw "NResets must be greater than zero."
}
if (-not (Test-Path -LiteralPath "scripts\collect_r26_g1_windows.py" -PathType Leaf) -or
    -not (Test-Path -LiteralPath "scripts\analyze_r26_g1_behavior.py" -PathType Leaf)) {
    throw "Run this script from the HMASD repository root."
}

$arms = @(
    @{ Name = "arm0_update25"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt"; Update = 25; NumSkills = 4 },
    @{ Name = "arm0_update30"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt"; Update = 30; NumSkills = 4 },
    @{ Name = "arm0_final"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt"; Update = 32; NumSkills = 4 },
    @{ Name = "arm2_update25"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_update_25.pt"; Update = 25; NumSkills = 4 },
    @{ Name = "arm2_update30"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_update_30.pt"; Update = 30; NumSkills = 4 },
    @{ Name = "arm2_final"; Checkpoint = "dist/logs_cloud_r25_qa_verification_1m/arm2_qA_reward/seed1/standalone_process_core_final.pt"; Update = 32; NumSkills = 4 }
)

if (-not $DryRun) {
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Python executable not found: $Python"
    }
    $missingCheckpoints = @($arms | Where-Object {
        -not (Test-Path -LiteralPath $_.Checkpoint -PathType Leaf)
    } | ForEach-Object { $_.Checkpoint })
    if ($missingCheckpoints.Count -gt 0) {
        throw "Required checkpoints not found:`n$($missingCheckpoints -join "`n")"
    }
}

Write-Host "R26-G1a six-checkpoint screening runner"
Write-Host "  python:             $Python"
Write-Host "  run_root:           $RunRoot"
Write-Host "  device:             $Device"
Write-Host "  n_resets:           $NResets"
Write-Host "  dry_run:            $DryRun"
Write-Host "  continue_on_error:  $ContinueOnError"

$batchStatusPath = Join-Path $RunRoot "batch_status.txt"
Write-Host "  batch_status:       $batchStatusPath"
$batchFailures = [System.Collections.Generic.List[string]]::new()
$batchResults = [System.Collections.Generic.List[string]]::new()

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
    @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "device=$Device"
        "n_resets=$NResets"
        "arm_count=$($arms.Count)"
    ) | Set-Content -LiteralPath $batchStatusPath -Encoding UTF8
}

foreach ($arm in $arms) {
    $armRoot = Join-Path $RunRoot $arm.Name
    $commandPath = Join-Path $armRoot "command.txt"
    $runnerStatusPath = Join-Path $armRoot "runner_status.txt"
    $collectorLogPath = Join-Path $armRoot "collector_output.log"
    $analyzerLogPath = Join-Path $armRoot "analyzer_output.log"
    $windowsPath = Join-Path $armRoot "windows"
    $analysisPath = Join-Path $armRoot "analysis"
    $manifestPath = Join-Path $windowsPath "collector_manifest.json"

    $collectorArguments = @(
        "scripts/collect_r26_g1_windows.py",
        "--checkpoint", $arm.Checkpoint,
        "--output_dir", $windowsPath,
        "--device", $Device,
        "--n_resets", "$NResets",
        "--checkpoint_id", $arm.Name,
        "--checkpoint_update", "$($arm.Update)"
    )
    $analyzerArguments = @(
        "scripts/analyze_r26_g1_behavior.py",
        "--input_dir", $windowsPath,
        "--output_dir", $analysisPath,
        "--num_skills", "$($arm.NumSkills)",
        "--device", $Device
    )
    $collectorCommand = Format-CommandLine -Command (@($Python) + $collectorArguments)
    $analyzerCommand = Format-CommandLine -Command (@($Python) + $analyzerArguments)

    Write-Host ""
    Write-Host "===== $($arm.Name) ====="
    Write-Host "  command.txt:          $commandPath"
    Write-Host "  runner_status.txt:    $runnerStatusPath"
    Write-Host "  collector_output.log: $collectorLogPath"
    Write-Host "  analyzer_output.log:  $analyzerLogPath"
    Write-Host "  windows/:             $windowsPath"
    Write-Host "  analysis/:            $analysisPath"
    Write-Host "COLLECTOR COMMAND: $collectorCommand"
    Write-Host "ANALYZER COMMAND: $analyzerCommand"

    if ($DryRun) {
        continue
    }

    New-Item -ItemType Directory -Force -Path $windowsPath, $analysisPath | Out-Null
    @(
        "collector=$collectorCommand"
        "analyzer=$analyzerCommand"
    ) | Set-Content -LiteralPath $commandPath -Encoding UTF8
    Write-RunnerStatus -Path $runnerStatusPath -Lines @(
        "started=$(Get-Date -Format o)"
        "state=running"
        "phase=collector"
        "arm=$($arm.Name)"
    )

    $failure = $null
    $collectorExit = Invoke-PythonPhase -Arguments $collectorArguments -LogPath $collectorLogPath
    if ($collectorExit -ne 0) {
        $failure = "collector failed with exit code $collectorExit"
    }

    if ($null -eq $failure) {
        try {
            if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
                throw "collector manifest missing: $manifestPath"
            }
            $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
            if ($null -eq $manifest.checkpoint_metadata -or
                $manifest.checkpoint_metadata.PSObject.Properties.Name -notcontains "n_skills" -or
                $null -eq $manifest.checkpoint_metadata.n_skills) {
                throw "collector manifest is missing checkpoint_metadata.n_skills"
            }
            $rawManifestNumSkills = $manifest.checkpoint_metadata.n_skills
            $integralTypeCodes = @(
                [System.TypeCode]::SByte,
                [System.TypeCode]::Byte,
                [System.TypeCode]::Int16,
                [System.TypeCode]::UInt16,
                [System.TypeCode]::Int32,
                [System.TypeCode]::UInt32,
                [System.TypeCode]::Int64,
                [System.TypeCode]::UInt64
            )
            $manifestTypeCode = [System.Type]::GetTypeCode($rawManifestNumSkills.GetType())
            if ($integralTypeCodes -notcontains $manifestTypeCode) {
                throw "collector manifest checkpoint_metadata.n_skills must be an exact integer"
            }
            if ($rawManifestNumSkills -le 0) {
                throw "collector manifest checkpoint_metadata.n_skills must be positive"
            }
            if ([decimal]$rawManifestNumSkills -ne [decimal]$arm.NumSkills) {
                throw "collector manifest n_skills=$rawManifestNumSkills, expected $($arm.NumSkills)"
            }
            $manifestNumSkills = [int]$rawManifestNumSkills
            $analyzerArguments = @(
                "scripts/analyze_r26_g1_behavior.py",
                "--input_dir", $windowsPath,
                "--output_dir", $analysisPath,
                "--num_skills", "$manifestNumSkills",
                "--device", $Device
            )
            $analyzerCommand = Format-CommandLine -Command (@($Python) + $analyzerArguments)
            @(
                "collector=$collectorCommand"
                "analyzer=$analyzerCommand"
            ) | Set-Content -LiteralPath $commandPath -Encoding UTF8
        } catch {
            $failure = "manifest validation failed: $($_.Exception.Message)"
        }
    }

    if ($null -eq $failure) {
        Write-RunnerStatus -Path $runnerStatusPath -Lines @(
            "started=$(Get-Date -Format o)"
            "state=running"
            "phase=analyzer"
            "arm=$($arm.Name)"
            "manifest_num_skills=$manifestNumSkills"
        )
        $analyzerExit = Invoke-PythonPhase -Arguments $analyzerArguments -LogPath $analyzerLogPath
        if ($analyzerExit -ne 0) {
            $failure = "analyzer failed with exit code $analyzerExit"
        }
    }

    if ($null -eq $failure) {
        Write-RunnerStatus -Path $runnerStatusPath -Lines @(
            "finished=$(Get-Date -Format o)"
            "state=succeeded"
            "arm=$($arm.Name)"
            "manifest_num_skills=$manifestNumSkills"
        )
        $batchResults.Add("$($arm.Name)=succeeded")
        continue
    }

    Write-RunnerStatus -Path $runnerStatusPath -Lines @(
        "finished=$(Get-Date -Format o)"
        "state=failed"
        "arm=$($arm.Name)"
        "error=$failure"
    )
    $batchFailures.Add($arm.Name)
    $batchResults.Add("$($arm.Name)=failed: $failure")
    Write-Warning "Arm '$($arm.Name)' failed: $failure"
    if (-not $ContinueOnError) {
        break
    }
}

if (-not $DryRun) {
    @(
        "finished=$(Get-Date -Format o)"
        "state=$(if ($batchFailures.Count -eq 0) { 'succeeded' } else { 'failed' })"
        "failed_arms=$($batchFailures -join ',')"
        $batchResults
    ) | Set-Content -LiteralPath $batchStatusPath -Encoding UTF8
}

if ($batchFailures.Count -gt 0) {
    exit 1
}

Write-Host ""
Write-Host "R26-G1a screening runner completed successfully."
