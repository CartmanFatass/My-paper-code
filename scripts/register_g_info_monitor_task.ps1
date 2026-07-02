param(
    [string]$TaskName = "HA-CTSE GInfo Progress Check",
    [int]$IntervalHours = 8,
    [string]$LogRoot = "logs\ha_ctse_process_g_info_local_cuda",
    [string]$CheckScript = "scripts\check_g_info_progress.ps1",
    [switch]$RunNow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($IntervalHours -lt 1 -or $IntervalHours -gt 23) {
    throw "IntervalHours must be in [1, 23] for schtasks hourly mode."
}

$repoRoot = Resolve-Path -Path (Join-Path $PSScriptRoot "..")

if ([System.IO.Path]::IsPathRooted($CheckScript)) {
    $checkPath = Resolve-Path -Path $CheckScript
} else {
    $checkPath = Resolve-Path -Path (Join-Path $repoRoot.Path $CheckScript)
}

if ([System.IO.Path]::IsPathRooted($LogRoot)) {
    $logRootPath = $LogRoot
} else {
    $logRootPath = Join-Path $repoRoot.Path $LogRoot
}

New-Item -ItemType Directory -Path $logRootPath -Force | Out-Null

$startTime = (Get-Date).AddMinutes(2).ToString("HH:mm")
$taskRun = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$($checkPath.Path)`" -LogRoot `"$logRootPath`""

Write-Host "Registering scheduled task:"
Write-Host "  name:      $TaskName"
Write-Host "  interval:  every $IntervalHours hours"
Write-Host "  start:     $startTime"
Write-Host "  command:   $taskRun"
Write-Host "  output:    $(Join-Path $logRootPath '_monitor')"

& schtasks.exe /Create /TN $TaskName /SC HOURLY /MO $IntervalHours /ST $startTime /TR $taskRun /F

if ($RunNow) {
    & schtasks.exe /Run /TN $TaskName
}

Write-Host ""
Write-Host "Task registered. Manual check command:"
Write-Host "  powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$($checkPath.Path)`" -LogRoot `"$logRootPath`""
Write-Host ""
Write-Host "Delete task command:"
Write-Host "  schtasks.exe /Delete /TN `"$TaskName`" /F"
