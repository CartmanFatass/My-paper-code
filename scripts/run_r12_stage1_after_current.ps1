param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "diag_only,oracle_change",
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [int]$PollSeconds = 300,
    [int]$MaxWaitHours = 18,
    [string]$AutomationLogDir = "logs\ha_ctse_r12_stage1_overnight_auto\_automation",
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

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

New-Item -ItemType Directory -Path $AutomationLogDir -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $AutomationLogDir "r12_stage1_after_current_$stamp.log"

function Write-AutoLog {
    param([string]$Message)

    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

function Get-ActiveHaCtseTrainProcesses {
    $self = $PID
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -ne $self -and
            $_.CommandLine -and
            $_.CommandLine -like "*ha_ctse_process.train*" -and
            $_.CommandLine -notlike "*-DryRun*"
        } |
        Select-Object ProcessId, ParentProcessId, Name, CommandLine
}

Write-AutoLog "R12 Stage 1 overnight wait-and-run starting."
Write-AutoLog "experiments=$Experiments total_timesteps=$TotalTimesteps num_envs=$NumEnvs device=$Device poll_seconds=$PollSeconds max_wait_hours=$MaxWaitHours dry_run=$DryRun"

$deadline = (Get-Date).AddHours([Math]::Max($MaxWaitHours, 1))
while ($true) {
    $active = @(Get-ActiveHaCtseTrainProcesses)
    if ((Get-Date) -ge $deadline) {
        Write-AutoLog "Max wait time exceeded while waiting for current HA-CTSE training to finish. Not launching R12 Stage 1 runner."
        throw "Max wait time exceeded while waiting for current HA-CTSE training to finish."
    }

    if ($active.Count -eq 0) {
        Write-AutoLog "No active ha_ctse_process.train process found. Proceeding to R12 Stage 1 runner."
        break
    }

    Write-AutoLog ("Waiting for {0} active training process(es): {1}" -f $active.Count, (($active | ForEach-Object { $_.ProcessId }) -join ","))
    Start-Sleep -Seconds ([Math]::Max($PollSeconds, 30))
}

$runner = ".\scripts\run_r12_stage1_local_cuda.ps1"
if (-not (Test-Path $runner)) {
    throw "Missing runner script: $runner"
}

$runnerArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $runner,
    "-Python", $Python,
    "-Experiments", $Experiments,
    "-TotalTimesteps", "$TotalTimesteps",
    "-NumEnvs", "$NumEnvs",
    "-Device", $Device
)

if ($DryRun) {
    $runnerArgs += "-DryRun"
}

Write-AutoLog ("Launching: {0}" -f (Format-CommandLine -Command (@("powershell.exe") + $runnerArgs)))
& powershell.exe @runnerArgs
$exitCode = $LASTEXITCODE
Write-AutoLog "R12 Stage 1 runner exited with code $exitCode"
exit $exitCode
