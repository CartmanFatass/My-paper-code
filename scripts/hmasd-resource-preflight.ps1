param(
    [Parameter(Mandatory=$true)][string] $AssignmentId,
    [Parameter(Mandatory=$true)][string] $RouteId,
    [Parameter(Mandatory=$true)][string] $Backend,
    [Parameter(Mandatory=$true)][int] $SelectedWorkerCount,
    [Parameter(Mandatory=$true)][string] $SelectionRationale,
    [Parameter(Mandatory=$true)][string] $CmOwner,
    [Parameter(Mandatory=$true)][string] $OutFile,
    [int] $ThreadsPerWorker = 1,
    [switch] $Parallel
)
$ErrorActionPreference = 'Stop'
if ($SelectedWorkerCount -le 0) { throw 'SelectedWorkerCount must be positive; the wrapper never invents a width.' }
$processors = @(Get-CimInstance Win32_Processor)
$os = Get-CimInstance Win32_OperatingSystem
$physical = [int](($processors | Measure-Object -Property NumberOfCores -Sum).Sum)
$logical = [int](($processors | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum)
$load = [double](($processors | Measure-Object -Property LoadPercentage -Average).Average)
$total = [math]::Round([double]$os.TotalVisibleMemorySize / 1MB, 4)
$available = [math]::Round([double]$os.FreePhysicalMemory / 1MB, 4)
$payload = [ordered]@{
    schema_version = 1; preflight_id = "resource_$([guid]::NewGuid().ToString('N'))"; assignment_id = $AssignmentId
    captured_at = [datetime]::UtcNow.ToString('o'); host_identity = $env:COMPUTERNAME; route_id = $RouteId; backend = $Backend
    cpu = [ordered]@{ physical_cores = $physical; logical_processors = $logical; load_percent = $load }
    memory = [ordered]@{ total_gib = $total; available_gib = $available }
    selection = [ordered]@{ selected_worker_count = $SelectedWorkerCount; threads_per_worker = $ThreadsPerWorker; parallel = [bool]$Parallel; selection_rationale = $SelectionRationale; cm_owner = $CmOwner }
}
$parent = Split-Path -Parent $OutFile; if ($parent) { New-Item -ItemType Directory -Force $parent | Out-Null }
$payload | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $OutFile
Write-Output ($payload | ConvertTo-Json -Depth 5)
