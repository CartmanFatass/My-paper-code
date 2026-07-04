param(
    [string]$TrainingLogRoot = "logs\ha_ctse_r16_a2r_overnight_local_cuda",
    [string]$OutputRoot = "logs\training_monitor",
    [int]$IntervalMinutes = 60,
    [int]$StaleMinutes = 60,
    [string]$ProcessPattern = "ha_ctse_process.train",
    [switch]$Once
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$statusLog = Join-Path $OutputRoot "monitor_status.log"
$alertLog = Join-Path $OutputRoot "monitor_alert.txt"
$stateFile = Join-Path $OutputRoot "monitor_state.json"

function Write-MonitorLine {
    param(
        [string]$Message,
        [switch]$Alert
    )
    $line = "$(Get-Date -Format o) $Message"
    Add-Content -Path $statusLog -Value $line -Encoding UTF8
    if ($Alert) {
        Add-Content -Path $alertLog -Value $line -Encoding UTF8
    }
    Write-Host $line
}

function Get-TrainingProcesses {
    try {
        return @(Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object {
                $_.CommandLine -and
                $_.CommandLine -like "*$ProcessPattern*" -and
                $_.CommandLine -notlike "*watch_overnight_training.ps1*"
            } |
            Select-Object ProcessId, ParentProcessId, Name, CommandLine)
    } catch {
        # Some shells cannot query Win32_Process command lines. Fall back to
        # python processes; the log freshness and GPU PID cross-check below
        # disambiguate whether training is still alive.
        return @(Get-Process -Name python -ErrorAction SilentlyContinue |
            Select-Object @{n="ProcessId";e={$_.Id}}, @{n="ParentProcessId";e={$null}}, @{n="Name";e={$_.ProcessName}}, @{n="CommandLine";e={"<command line unavailable>"}})
    }
}

function Get-LatestTrainingLog {
    if (-not (Test-Path $TrainingLogRoot)) {
        return $null
    }
    Get-ChildItem -Path $TrainingLogRoot -Recurse -Filter "standalone_train.log" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function Get-LogMarkers {
    param([string]$Path)
    if (-not $Path -or -not (Test-Path $Path)) {
        return @()
    }
    $pattern = "Traceback|RuntimeError|BrokenPipe|CUDA out of memory|out of memory|OOM|NaN|KeyboardInterrupt|ERROR"
    @(Select-String -Path $Path -Pattern $pattern -CaseSensitive:$false -ErrorAction SilentlyContinue |
        Select-Object -Last 8 |
        ForEach-Object { $_.Line.Trim() })
}

function Get-LastUpdateLine {
    param([string]$Path)
    if (-not $Path -or -not (Test-Path $Path)) {
        return ""
    }
    $tail = Get-Content -Path $Path -Tail 80 -ErrorAction SilentlyContinue
    $updates = @($tail | Where-Object { $_ -match "^standalone_update update=" })
    if ($updates.Count -gt 0) {
        return $updates[-1]
    }
    $evals = @($tail | Where-Object { $_ -match "^standalone_eval " })
    if ($evals.Count -gt 0) {
        return $evals[-1]
    }
    return ""
}

function Get-StatusSummary {
    param([string]$Line)
    if (-not $Line) {
        return ""
    }
    if ($Line -match "^standalone_update update=(\d+) total_steps=(\d+).*?env_reward_mean=([^\s]+)") {
        return "update=$($Matches[1]) steps=$($Matches[2]) env_reward_mean=$($Matches[3])"
    }
    if ($Line -match "^standalone_eval total_steps=(\d+).*?reward_mean=([^\s]+).*?coverage=([^\s]+).*?zero_throughput_ep_frac=([^\s]+)") {
        return "eval_steps=$($Matches[1]) reward_mean=$($Matches[2]) coverage=$($Matches[3]) zero_thr_ep=$($Matches[4])"
    }
    if ($Line.Length -gt 180) {
        return $Line.Substring(0, 180)
    }
    return $Line
}

function Get-GpuStatus {
    $nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $nvsmi) {
        return @{
            Available = $false
            Summary = "nvidia-smi_not_found"
            PythonOnGpu = $false
        }
    }

    $summary = (& nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null) -join "; "
    $computeLines = @(& nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits 2>$null)
    $compute = $computeLines -join "`n"
    $gpuPids = @($computeLines | ForEach-Object {
        if ($_ -match "^\s*(\d+)\s*,") {
            [int]$Matches[1]
        }
    })
    $pythonOnGpu = $compute -match "python(\.exe)?"
    return @{
        Available = $true
        Summary = $summary
        Compute = $compute
        GpuPids = $gpuPids
        PythonOnGpu = $pythonOnGpu
    }
}

function Invoke-Check {
    $now = Get-Date
    $processes = @(Get-TrainingProcesses)
    $latestLog = Get-LatestTrainingLog
    $gpu = Get-GpuStatus
    $processIds = @($processes | ForEach-Object { [int]$_.ProcessId })
    $gpuPids = @($gpu.GpuPids)
    $gpuHasTrainingPid = @($gpuPids | Where-Object { $processIds -contains $_ }).Count -gt 0
    $pythonOnGpu = [bool]($gpu.PythonOnGpu -or $gpuHasTrainingPid)

    $issues = New-Object System.Collections.Generic.List[string]
    if ($processes.Count -eq 0) {
        $issues.Add("training_process_missing")
    }

    $logPath = ""
    $logAgeMinutes = $null
    $lastLine = ""
    $markers = @()
    if ($null -eq $latestLog) {
        $issues.Add("standalone_train_log_missing")
    } else {
        $logPath = $latestLog.FullName
        $logAgeMinutes = ($now - $latestLog.LastWriteTime).TotalMinutes
        if ($logAgeMinutes -gt $StaleMinutes) {
            $issues.Add(("log_stale_{0:N1}min" -f $logAgeMinutes))
        }
        $markers = @(Get-LogMarkers -Path $logPath)
        if ($markers.Count -gt 0) {
            $issues.Add("exception_marker_in_log")
        }
        $lastLine = Get-LastUpdateLine -Path $logPath
    }

    if (-not $gpu.Available) {
        $issues.Add("gpu_status_unavailable")
    } elseif (-not $pythonOnGpu) {
        $issues.Add("python_not_visible_on_gpu")
    }

    $record = [ordered]@{
        time = $now.ToString("o")
        ok = ($issues.Count -eq 0)
        issues = @($issues)
        process_count = $processes.Count
        process_ids = @($processIds)
        active_log = $logPath
        log_age_minutes = if ($null -eq $logAgeMinutes) { $null } else { [Math]::Round($logAgeMinutes, 2) }
        last_status_line = $lastLine
        gpu_summary = $gpu.Summary
        python_on_gpu = $pythonOnGpu
        gpu_pids = @($gpuPids)
        markers = @($markers)
    }
    $record | ConvertTo-Json -Depth 4 | Set-Content -Path $stateFile -Encoding UTF8
    $statusSummary = Get-StatusSummary -Line $lastLine

    if ($issues.Count -eq 0) {
        Write-MonitorLine ("OK process_ids={0} log_age_min={1:N1} gpu=({2}) status='{3}'" -f (($processIds | Select-Object -First 8) -join ","), $logAgeMinutes, $gpu.Summary, $statusSummary)
    } else {
        Write-MonitorLine ("ALERT issues={0} process_ids={1} gpu_pids={2} log_age_min={3} gpu=({4}) log={5}" -f ($issues -join ","), (($processIds | Select-Object -First 8) -join ","), ($gpuPids -join ","), $record.log_age_minutes, $gpu.Summary, $logPath) -Alert
        if ($markers.Count -gt 0) {
            Write-MonitorLine ("ALERT markers: {0}" -f (($markers | Select-Object -First 3) -join " || ")) -Alert
        }
    }
}

Write-MonitorLine "monitor_start interval_minutes=$IntervalMinutes stale_minutes=$StaleMinutes log_root=$TrainingLogRoot once=$Once"

do {
    Invoke-Check
    if ($Once) {
        break
    }
    Start-Sleep -Seconds ([Math]::Max(60, $IntervalMinutes * 60))
} while ($true)
