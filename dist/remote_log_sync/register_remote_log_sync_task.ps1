param(
    [string]$Config = (Join-Path $PSScriptRoot "remote_log_sync.config.json"),
    [string]$TaskName = "HA-CTSE Remote Log Sync",
    [switch]$RunNow,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Format-CommandLine {
    param([Parameter(Mandatory = $true)][string[]]$Command)

    return (($Command | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }) -join " ")
}

function Get-PropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        [object]$Default = $null
    )

    if ($null -eq $Object) { return $Default }
    $prop = $Object.PSObject.Properties | Where-Object { $_.Name -eq $Name } | Select-Object -First 1
    if ($null -eq $prop -or $null -eq $prop.Value) { return $Default }
    return $prop.Value
}

function Resolve-WorkspacePath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $Path))
}

function Get-RemoteLogRootLeaf {
    param([Parameter(Mandatory = $true)][string]$RemoteLogRoot)

    $trimmed = $RemoteLogRoot.Trim().TrimEnd("/", "\")
    if (-not $trimmed) {
        throw "remoteLogRoot cannot be empty."
    }
    $parts = $trimmed -split '[\\/]+' | Where-Object { $_ }
    if ($parts.Count -eq 0) {
        throw "Cannot derive local directory from remoteLogRoot: $RemoteLogRoot"
    }
    $leaf = [string]$parts[-1]
    $invalid = [System.IO.Path]::GetInvalidFileNameChars()
    foreach ($char in $invalid) {
        $leaf = $leaf.Replace([string]$char, "_")
    }
    $leaf = $leaf.Trim()
    if (-not $leaf) {
        throw "Cannot derive safe local directory from remoteLogRoot: $RemoteLogRoot"
    }
    return $leaf
}

function Resolve-LocalLogRoot {
    param(
        [Parameter(Mandatory = $true)][string]$LocalLogRootRaw,
        [Parameter(Mandatory = $true)][string]$RemoteLogRoot,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )

    $raw = $LocalLogRootRaw.Trim()
    if (-not $raw -or $raw -ieq "auto") {
        $leaf = Get-RemoteLogRootLeaf -RemoteLogRoot $RemoteLogRoot
        return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot (Join-Path "synced" $leaf)))
    }
    return Resolve-WorkspacePath -Path $raw -RepoRoot $RepoRoot
}

$configPath = Resolve-Path -Path $Config
$configObject = Get-Content -LiteralPath $configPath.Path -Raw -Encoding UTF8 | ConvertFrom-Json
$repoRoot = (Resolve-Path -Path (Join-Path $PSScriptRoot "..\..")).Path
$syncPath = Resolve-Path -Path (Join-Path $PSScriptRoot "sync_remote_logs_ssh.ps1")

$intervalMinutes = [int](Get-PropertyValue -Object $configObject -Name "intervalMinutes" -Default 30)
if ($intervalMinutes -lt 1 -or $intervalMinutes -gt 1439) {
    throw "intervalMinutes must be in [1, 1439]."
}

$remote = [string](Get-PropertyValue -Object $configObject -Name "remote" -Default "")
$remoteLogRoot = [string](Get-PropertyValue -Object $configObject -Name "remoteLogRoot" -Default "")
$localLogRootRaw = [string](Get-PropertyValue -Object $configObject -Name "localLogRoot" -Default "auto")
$localLogRoot = Resolve-LocalLogRoot -LocalLogRootRaw $localLogRootRaw -RemoteLogRoot $remoteLogRoot -RepoRoot $repoRoot

$syncArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $syncPath.Path,
    "-Config", $configPath.Path
)

$taskRun = Format-CommandLine -Command (@("powershell.exe") + $syncArgs)
$startTime = (Get-Date).AddMinutes(2).ToString("HH:mm")
$schtasksCommand = @(
    "schtasks.exe",
    "/Create",
    "/TN", $TaskName,
    "/SC", "MINUTE",
    "/MO", "$intervalMinutes",
    "/ST", $startTime,
    "/TR", $taskRun,
    "/F"
)

Write-Host "Registering remote log sync scheduled task:"
Write-Host "  name:      $TaskName"
Write-Host "  config:    $($configPath.Path)"
Write-Host "  remote:    $remote"
Write-Host "  remote_log_root: $remoteLogRoot"
Write-Host "  interval:  every $intervalMinutes minutes"
Write-Host "  start:     $startTime"
Write-Host "  command:   $taskRun"
Write-Host "  output:    $localLogRoot"
Write-Host "  schtasks:  $(Format-CommandLine -Command $schtasksCommand)"

if ($DryRun) {
    Write-Host "DryRun requested; not registering scheduled task."
    exit 0
}

New-Item -ItemType Directory -Path $localLogRoot -Force | Out-Null
& schtasks.exe /Create /TN $TaskName /SC MINUTE /MO $intervalMinutes /ST $startTime /TR $taskRun /F

if ($RunNow) {
    & schtasks.exe /Run /TN $TaskName
}

Write-Host ""
Write-Host "Task registered. Manual sync command:"
Write-Host "  $taskRun"
Write-Host ""
Write-Host "Delete task command:"
Write-Host "  schtasks.exe /Delete /TN `"$TaskName`" /F"
