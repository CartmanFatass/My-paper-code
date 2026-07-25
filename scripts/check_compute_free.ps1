# Compute availability gate.
#
# Standing authorization covers compute; this decides *when*, not *whether*.
# Prints COMPUTE_FREE or COMPUTE_BUSY plus the numbers behind the verdict.
#
# Busy is not a blocker. Busy means wait an hour and re-check.

[CmdletBinding()]
param(
    [double] $CpuCeilingPct = 60.0,
    [int]    $Samples = 3
)
$ErrorActionPreference = 'Stop'

$cpu = ((Get-Counter '\Processor(_Total)\% Processor Time' `
        -SampleInterval 1 -MaxSamples $Samples).CounterSamples |
        Measure-Object CookedValue -Average).Average

# A python process burning real CPU time is a training run, ours or another
# line's. Short-lived helpers sit near zero and are ignored.
$heavy = @(Get-Process -Name python -ErrorAction SilentlyContinue |
           Where-Object { $_.CPU -gt 60 })

$cores = [Environment]::ProcessorCount
$free  = ($cpu -lt $CpuCeilingPct) -and ($heavy.Count -eq 0)

[pscustomobject]@{
    verdict        = if ($free) { 'COMPUTE_FREE' } else { 'COMPUTE_BUSY' }
    cpu_avg_pct    = [math]::Round($cpu, 1)
    cpu_ceiling    = $CpuCeilingPct
    heavy_python   = $heavy.Count
    heavy_pids     = ($heavy | ForEach-Object { $_.Id }) -join ','
    cores          = $cores
} | Format-List | Out-String | Write-Output

if ($free) { Write-Output 'COMPUTE_FREE' } else { Write-Output 'COMPUTE_BUSY' }
