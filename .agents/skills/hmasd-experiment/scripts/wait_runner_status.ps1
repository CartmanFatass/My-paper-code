[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RunPath,

    [string]$StatusPath = "runner_status.txt"
)

$ErrorActionPreference = "Stop"

$run = (Resolve-Path -LiteralPath $RunPath).Path
$status = if ([IO.Path]::IsPathRooted($StatusPath)) {
    [IO.Path]::GetFullPath($StatusPath)
} else {
    [IO.Path]::GetFullPath((Join-Path $run $StatusPath))
}

if (-not $status.StartsWith($run + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Status path escapes run root: $status"
}

function Read-Status {
    if (-not (Test-Path -LiteralPath $status -PathType Leaf)) {
        return $null
    }

    $values = [ordered]@{}
    foreach ($line in Get-Content -LiteralPath $status) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        $pair = $line.Split("=", 2)
        if ($pair.Count -ne 2 -or [string]::IsNullOrWhiteSpace($pair[0])) {
            return $null
        }
        $values[$pair[0].Trim()] = $pair[1].Trim()
    }

    if (-not $values.Contains("state")) {
        return $null
    }
    if ($values.state -notin @("complete", "completed", "failed")) {
        return $null
    }
    foreach ($required in @("updated", "phase")) {
        if (-not $values.Contains($required) -or [string]::IsNullOrWhiteSpace([string]$values[$required])) {
            throw "Terminal status is missing $required"
        }
    }

    if ($values.Contains("run_root")) {
        $reportedRun = [IO.Path]::GetFullPath([string]$values.run_root)
        if (-not [string]::Equals($reportedRun, $run, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Terminal status run_root does not match the frozen run root"
        }
    }
    if ($values.Contains("run_id") -and
        [string]$values.run_id -ne (Split-Path -Leaf $run)) {
        throw "Terminal status run_id does not match the frozen run root"
    }

    $payload = $null
    $payloadKeys = if ($values.state -in @("complete", "completed")) { @("result_path") } else { @("error_path") }
    foreach ($key in $payloadKeys) {
        if ($values.Contains($key) -and -not [string]::IsNullOrWhiteSpace([string]$values[$key])) {
            $candidate = [IO.Path]::GetFullPath([string]$values[$key])
            if (-not $candidate.StartsWith($run + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Terminal payload path escapes run root: $candidate"
            }
            $payload = $candidate
            break
        }
    }

    return [pscustomobject]@{
        run = Split-Path -Leaf $run
        state = [string]$values.state
        phase = [string]$values.phase
        updated = [string]$values.updated
        status = $status
        payload = $payload
        error = if ($values.Contains("error")) { [string]$values.error } else { $null }
    }
}

$watcher = [IO.FileSystemWatcher]::new((Split-Path -Parent $status), (Split-Path -Leaf $status))
$watcher.NotifyFilter = [IO.NotifyFilters]::FileName -bor [IO.NotifyFilters]::LastWrite -bor [IO.NotifyFilters]::Size
$watcher.EnableRaisingEvents = $true
$sourceIds = @(
    "hmasd-status-created-$PID",
    "hmasd-status-changed-$PID",
    "hmasd-status-renamed-$PID"
)

$subscriptions = @()
$subscriptions += Register-ObjectEvent -InputObject $watcher -EventName Created -SourceIdentifier $sourceIds[0]
$subscriptions += Register-ObjectEvent -InputObject $watcher -EventName Changed -SourceIdentifier $sourceIds[1]
$subscriptions += Register-ObjectEvent -InputObject $watcher -EventName Renamed -SourceIdentifier $sourceIds[2]

try {
    while ($true) {
        $terminal = Read-Status
        if ($null -ne $terminal) {
            $terminal | ConvertTo-Json -Compress
            break
        }
        $event = Wait-Event
        if ($null -ne $event) {
            Remove-Event -EventIdentifier $event.EventIdentifier -ErrorAction SilentlyContinue
        }
    }
} finally {
    foreach ($subscription in $subscriptions) {
        Unregister-Event -SubscriptionId $subscription.Id -ErrorAction SilentlyContinue
    }
    $watcher.Dispose()
}
