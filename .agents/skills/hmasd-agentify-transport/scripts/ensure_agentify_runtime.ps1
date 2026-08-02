[CmdletBinding()]
param(
    [string]$AgentifySource = 'C:\Projects\agentify-desktop',
    [string]$NpmExecutable = 'npm.cmd',
    [string]$ServiceProcessName = 'electron',
    [string]$BrowserProcessName = 'chrome',
    [ValidateRange(1, 30)][int]$TimeoutSeconds = 15,
    [switch]$ProbeOnly
)

$ErrorActionPreference = 'Stop'

function Get-NamedProcesses([string]$Name) {
    @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
}

$serviceProcesses = Get-NamedProcesses $ServiceProcessName
$browserProcesses = Get-NamedProcesses $BrowserProcessName
$launched = $false

if ($serviceProcesses.Count -eq 0 -or $browserProcesses.Count -eq 0) {
    if ($ProbeOnly) {
        throw "Agentify runtime is not running: service=$ServiceProcessName browser=$BrowserProcessName"
    }
    if ($serviceProcesses.Count -eq 0 -and $browserProcesses.Count -gt 0) {
        throw 'Chrome is running without Agentify Desktop; close Chrome before starting the existing-profile service'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $AgentifySource 'package.json') -PathType Leaf)) {
        throw "Agentify source is missing: $AgentifySource"
    }
    $env:AGENTIFY_DESKTOP_CHROME_PROFILE_MODE = 'existing'
    $env:AGENTIFY_DESKTOP_SHOW_TABS = 'true'
    Start-Process -FilePath $NpmExecutable -ArgumentList @('run', 'start') `
        -WorkingDirectory $AgentifySource -WindowStyle Hidden
    $launched = $true
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 250
        $serviceProcesses = Get-NamedProcesses $ServiceProcessName
        $browserProcesses = Get-NamedProcesses $BrowserProcessName
    } while (($serviceProcesses.Count -eq 0 -or $browserProcesses.Count -eq 0) -and [DateTime]::UtcNow -lt $deadline)
}

if ($serviceProcesses.Count -eq 0 -or $browserProcesses.Count -eq 0) {
    throw "Agentify Desktop and Chrome were not both running within $TimeoutSeconds seconds"
}

Start-Sleep -Milliseconds 500
$serviceProcesses = Get-NamedProcesses $ServiceProcessName
$browserProcesses = Get-NamedProcesses $BrowserProcessName
if ($serviceProcesses.Count -eq 0 -or $browserProcesses.Count -eq 0) {
    throw 'Agentify Desktop or Chrome exited before the stable runtime check'
}

$receipt = [ordered]@{
    status = 'AGENTIFY_RUNTIME_READY'
    launched = $launched
    service_process_ids = @($serviceProcesses | ForEach-Object { $_.Id })
    browser_process_ids = @($browserProcesses | ForEach-Object { $_.Id })
    agentify_source = $AgentifySource
}
$receipt | ConvertTo-Json -Compress
