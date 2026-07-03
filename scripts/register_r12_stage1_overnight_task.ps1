param(
    [string]$TaskName = "HA-CTSE R12 Stage1 Overnight",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "diag_only,oracle_change",
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [int]$PollSeconds = 300,
    [int]$MaxWaitHours = 18,
    [switch]$NoStart,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path -Path (Join-Path $PSScriptRoot "..")).Path
$wrapper = Join-Path $root "scripts\run_r12_stage1_after_current.ps1"
if (-not (Test-Path -Path $wrapper)) {
    throw "Missing wrapper script: $wrapper"
}

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$wrapper`"",
    "-Python", "`"$Python`"",
    "-Experiments", "`"$Experiments`"",
    "-TotalTimesteps", "$TotalTimesteps",
    "-NumEnvs", "$NumEnvs",
    "-Device", "`"$Device`"",
    "-PollSeconds", "$PollSeconds",
    "-MaxWaitHours", "$MaxWaitHours"
)

if ($DryRun) {
    $argList += "-DryRun"
}

$argumentString = $argList -join " "
$timeLimitHours = [Math]::Max($MaxWaitHours + 12, 24)

Write-Host "Task name: $TaskName"
Write-Host "Working directory: $root"
Write-Host "Action: powershell.exe $argumentString"
Write-Host "Execution time limit hours: $timeLimitHours"

if ($DryRun) {
    Write-Host "DryRun requested; not registering or starting scheduled task."
    exit 0
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argumentString -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours $timeLimitHours)

Write-Host "Registering scheduled task: $TaskName"

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Wait for current HA-CTSE training, then run R12 Stage 1 sequential CUDA experiments." `
    -Force | Out-Null

if ($NoStart) {
    Write-Host "Registered but did not start scheduled task because -NoStart was provided."
} else {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Started scheduled task: $TaskName"
}

Write-Host "Final scheduled task state:"
Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State
