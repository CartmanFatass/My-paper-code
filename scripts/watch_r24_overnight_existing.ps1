param(
    [string]$RunRoot = "logs_r24_overnight_existing_local_cuda",
    [string]$OutputRoot = "",
    [int]$IntervalMinutes = 30,
    [int]$StaleMinutes = 120,
    [switch]$Once,
    [switch]$ExitWhenFinished,
    [switch]$CodexOnAlert,
    [string]$CodexCli = "codex",
    [int]$CodexCooldownMinutes = 60,
    [int]$MaxCodexCalls = 2,
    [switch]$AutoRunRecovery
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

function Resolve-R24RunDir {
    param([string]$Root)
    if (-not (Test-Path $Root)) {
        return $null
    }
    $rootItem = Get-Item -LiteralPath $Root -ErrorAction SilentlyContinue
    if ($null -eq $rootItem -or -not $rootItem.PSIsContainer) {
        return $null
    }
    $armDirs = @(Get-ChildItem -LiteralPath $rootItem.FullName -Directory -Filter "arm*" -ErrorAction SilentlyContinue)
    if ($armDirs.Count -gt 0) {
        return $rootItem.FullName
    }
    $runs = @(Get-ChildItem -LiteralPath $rootItem.FullName -Directory -Filter "run_*" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending)
    if ($runs.Count -gt 0) {
        return $runs[0].FullName
    }
    return $rootItem.FullName
}

function Read-KeyValueFile {
    param([string]$Path)
    $map = @{}
    if (-not $Path -or -not (Test-Path $Path)) {
        return $map
    }
    foreach ($line in @(Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
        if ($line -match "^\s*([^=]+)=(.*)$") {
            $map[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    return $map
}

function Get-R24Processes {
    $patterns = @(
        "run_r24_overnight_existing_local_cuda",
        "run_r24_qd_probe_local_cuda",
        "run_r24_behavior_audit_local_cuda",
        "r24_forced_behavior_audit",
        "ha_ctse_process.train"
    )
    try {
        return @(Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object {
                $cmd = $_.CommandLine
                if (-not $cmd) { return $false }
                if ($cmd -like "*watch_r24_overnight_existing.ps1*") { return $false }
                foreach ($pattern in $patterns) {
                    if ($cmd -like "*$pattern*") { return $true }
                }
                return $false
            } |
            Select-Object ProcessId, ParentProcessId, Name, CommandLine)
    } catch {
        return @(Get-Process -Name python,powershell,pwsh -ErrorAction SilentlyContinue |
            Select-Object @{n="ProcessId";e={$_.Id}}, @{n="ParentProcessId";e={$null}}, @{n="Name";e={$_.ProcessName}}, @{n="CommandLine";e={"<command line unavailable>"}})
    }
}

function Get-GpuSummary {
    $nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $nvsmi) {
        return @{
            Summary = "nvidia-smi_not_found"
            Compute = ""
        }
    }
    $summary = (& nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>$null) -join "; "
    $compute = (@(& nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits 2>$null)) -join "; "
    return @{
        Summary = $summary
        Compute = $compute
    }
}

function Get-ErrorMarkers {
    param([string]$RunDir)
    if (-not $RunDir -or -not (Test-Path $RunDir)) {
        return @()
    }
    $pattern = "Traceback|RuntimeError|BrokenPipe|CUDA out of memory|out of memory|OOM|NaN|KeyboardInterrupt|ERROR|failed with exit code"
    $wantedNames = @("runner_output.log", "standalone_train.log")
    $files = @(Get-ChildItem -LiteralPath $RunDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $wantedNames -contains $_.Name })
    $hits = New-Object System.Collections.Generic.List[string]
    foreach ($file in $files) {
        $matches = @(Select-String -LiteralPath $file.FullName -Pattern $pattern -CaseSensitive:$false -ErrorAction SilentlyContinue |
            Select-Object -Last 3)
        foreach ($match in $matches) {
            $rel = $file.FullName
            if ($RunDir -and $rel.StartsWith($RunDir)) {
                $rel = $rel.Substring($RunDir.Length).TrimStart("\")
            }
            $hits.Add(("{0}: {1}" -f $rel, $match.Line.Trim()))
        }
    }
    return @($hits | Select-Object -Last 10)
}

function Get-LatestEvidenceFile {
    param([string]$RunDir)
    if (-not $RunDir -or -not (Test-Path $RunDir)) {
        return $null
    }
    $wantedNames = @(
        "runner_status.txt",
        "runner_output.log",
        "standalone_train.log",
        "train_updates.csv",
        "eval_episodes.csv",
        "r24_behavior_audit.csv"
    )
    $files = @(Get-ChildItem -LiteralPath $RunDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $wantedNames -contains $_.Name } |
        Sort-Object LastWriteTime -Descending)
    if ($files.Count -gt 0) {
        return $files[0]
    }
    return $null
}

function Get-LatestMetricLine {
    param([string]$RunDir)
    if (-not $RunDir -or -not (Test-Path $RunDir)) {
        return ""
    }
    $train = @(Get-ChildItem -LiteralPath $RunDir -Recurse -File -Filter "train_updates.csv" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1)
    if ($train.Count -gt 0) {
        $tail = @(Get-Content -LiteralPath $train[0].FullName -Tail 1 -ErrorAction SilentlyContinue)
        if ($tail.Count -gt 0) {
            return "train_updates_tail=$($tail[-1])"
        }
    }
    $audit = @(Get-ChildItem -LiteralPath $RunDir -Recurse -File -Filter "r24_behavior_audit.csv" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1)
    if ($audit.Count -gt 0) {
        $tail = @(Get-Content -LiteralPath $audit[0].FullName -Tail 1 -ErrorAction SilentlyContinue)
        if ($tail.Count -gt 0) {
            return "audit_tail=$($tail[-1])"
        }
    }
    return ""
}

function Get-ArmStatuses {
    param([string]$RunDir)
    if (-not $RunDir -or -not (Test-Path $RunDir)) {
        return @()
    }
    $armDirs = @(Get-ChildItem -LiteralPath $RunDir -Directory -Filter "arm*" -ErrorAction SilentlyContinue |
        Sort-Object Name)
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($arm in $armDirs) {
        $statusPath = Join-Path $arm.FullName "runner_status.txt"
        $status = Read-KeyValueFile -Path $statusPath
        $state = if ($status.ContainsKey("state")) { $status["state"] } else { "missing" }
        $exitCode = if ($status.ContainsKey("exit_code")) { $status["exit_code"] } else { "" }
        $items.Add([pscustomobject]@{
            Arm = $arm.Name
            State = $state
            ExitCode = $exitCode
            StatusPath = $statusPath
        })
    }
    return @($items.ToArray())
}

function Format-ArmSummary {
    param([object[]]$Arms)
    if (-not $Arms -or $Arms.Count -eq 0) {
        return "arms=none"
    }
    return (($Arms | ForEach-Object {
        if ($_.ExitCode -ne "") {
            "$($_.Arm):$($_.State)/$($_.ExitCode)"
        } else {
            "$($_.Arm):$($_.State)"
        }
    }) -join ",")
}

$initialRunDir = Resolve-R24RunDir -Root $RunRoot
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    if ($initialRunDir) {
        $OutputRoot = Join-Path $initialRunDir "_watch"
    } else {
        $OutputRoot = Join-Path $RunRoot "_watch"
    }
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$statusLog = Join-Path $OutputRoot "watch_status.log"
$alertLog = Join-Path $OutputRoot "watch_alert.txt"
$stateFile = Join-Path $OutputRoot "watch_state.json"
$codexTriggerStateFile = Join-Path $OutputRoot "codex_recovery_trigger_state.json"

function Write-WatchLine {
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

function Invoke-CodexRecoveryHandler {
    param(
        [string]$IssueKey
    )
    if (-not $CodexOnAlert) {
        return
    }

    $now = Get-Date
    $state = [ordered]@{
        call_count = 0
        last_issue_key = ""
        last_invoked = $null
    }
    if (Test-Path $codexTriggerStateFile) {
        try {
            $loaded = Get-Content -LiteralPath $codexTriggerStateFile -Raw | ConvertFrom-Json
            $state.call_count = [int]$loaded.call_count
            $state.last_issue_key = [string]$loaded.last_issue_key
            $state.last_invoked = $loaded.last_invoked
        } catch {
            Write-WatchLine "WARN could_not_read_codex_trigger_state=$codexTriggerStateFile"
        }
    }

    if ($state.call_count -ge $MaxCodexCalls) {
        Write-WatchLine "codex_recovery_skip reason=max_calls_reached count=$($state.call_count) max=$MaxCodexCalls" -Alert
        return
    }

    if ($state.last_issue_key -eq $IssueKey -and $state.last_invoked) {
        try {
            $last = [datetime]$state.last_invoked
            $age = ($now - $last).TotalMinutes
            if ($age -lt $CodexCooldownMinutes) {
                Write-WatchLine ("codex_recovery_skip reason=cooldown age_min={0:N1} cooldown_min={1}" -f $age, $CodexCooldownMinutes) -Alert
                return
            }
        } catch {
            # Ignore parse failures and allow one recovery attempt.
        }
    }

    if (-not (Test-Path "scripts\codex_r24_alert_handler.ps1")) {
        Write-WatchLine "codex_recovery_skip reason=handler_missing path=scripts\\codex_r24_alert_handler.ps1" -Alert
        return
    }

    $state.call_count = $state.call_count + 1
    $state.last_issue_key = $IssueKey
    $state.last_invoked = $now.ToString("o")
    $state | ConvertTo-Json -Depth 4 | Set-Content -Path $codexTriggerStateFile -Encoding UTF8

    Write-WatchLine "codex_recovery_start call=$($state.call_count) max=$MaxCodexCalls auto_run=$AutoRunRecovery" -Alert

    $args = @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ".\scripts\codex_r24_alert_handler.ps1",
        "-RunRoot",
        $RunRoot,
        "-WatchOutputRoot",
        $OutputRoot,
        "-CodexCli",
        $CodexCli
    )
    if ($AutoRunRecovery) {
        $args += "-AutoRunRecovery"
    }

    try {
        & powershell.exe @args
        $exitCode = $LASTEXITCODE
        Write-WatchLine "codex_recovery_finished exit_code=$exitCode" -Alert
    } catch {
        Write-WatchLine "codex_recovery_failed error=$($_.Exception.Message)" -Alert
    }
}

function Invoke-WatchCheck {
    $now = Get-Date
    $runDir = Resolve-R24RunDir -Root $RunRoot
    $processes = @(Get-R24Processes)
    $gpu = Get-GpuSummary
    $arms = @(Get-ArmStatuses -RunDir $runDir)
    $latest = Get-LatestEvidenceFile -RunDir $runDir
    $markers = @(Get-ErrorMarkers -RunDir $runDir)
    $metricLine = Get-LatestMetricLine -RunDir $runDir

    $issues = New-Object System.Collections.Generic.List[string]
    $latestPath = ""
    $latestAge = $null
    if ($null -eq $runDir) {
        $issues.Add("run_dir_missing")
    }
    if ($null -eq $latest) {
        $issues.Add("evidence_file_missing")
    } else {
        $latestPath = $latest.FullName
        $latestAge = ($now - $latest.LastWriteTime).TotalMinutes
        if ($latestAge -gt $StaleMinutes -and $processes.Count -gt 0) {
            $issues.Add(("evidence_stale_{0:N1}min" -f $latestAge))
        }
    }
    foreach ($arm in $arms) {
        if ($arm.State -eq "finished" -and $arm.ExitCode -ne "" -and $arm.ExitCode -ne "0") {
            $issues.Add("arm_failed_$($arm.Arm)_exit_$($arm.ExitCode)")
        }
    }
    $runningArms = @($arms | Where-Object { $_.State -eq "running" })
    if ($runningArms.Count -gt 0 -and $processes.Count -eq 0) {
        $issues.Add("running_arm_but_process_missing")
    }
    if ($markers.Count -gt 0) {
        $issues.Add("error_marker_found")
    }

    $allFinished = ($arms.Count -gt 0 -and (@($arms | Where-Object { $_.State -ne "finished" }).Count -eq 0))
    $record = [ordered]@{
        time = $now.ToString("o")
        ok = ($issues.Count -eq 0)
        done = $allFinished
        issues = @($issues)
        run_dir = $runDir
        process_count = $processes.Count
        process_ids = @($processes | ForEach-Object { $_.ProcessId })
        latest_evidence = $latestPath
        latest_evidence_age_min = if ($null -eq $latestAge) { $null } else { [Math]::Round($latestAge, 2) }
        arms = @($arms)
        gpu_summary = $gpu.Summary
        gpu_compute = $gpu.Compute
        metric_line = $metricLine
        markers = @($markers)
    }
    $record | ConvertTo-Json -Depth 5 | Set-Content -Path $stateFile -Encoding UTF8

    $armSummary = Format-ArmSummary -Arms $arms
    $pidSummary = (($record.process_ids | Select-Object -First 8) -join ",")
    if ($allFinished -and $issues.Count -eq 0) {
        Write-WatchLine ("DONE {0} processes={1} latest_age_min={2} gpu=({3})" -f $armSummary, $pidSummary, $record.latest_evidence_age_min, $gpu.Summary)
    } elseif ($issues.Count -eq 0) {
        Write-WatchLine ("OK {0} processes={1} latest_age_min={2} gpu=({3}) metric='{4}'" -f $armSummary, $pidSummary, $record.latest_evidence_age_min, $gpu.Summary, $metricLine)
    } else {
        Write-WatchLine ("ALERT issues={0} {1} processes={2} latest_age_min={3} latest={4} gpu=({5})" -f ($issues -join ","), $armSummary, $pidSummary, $record.latest_evidence_age_min, $latestPath, $gpu.Summary) -Alert
        if ($markers.Count -gt 0) {
            Write-WatchLine ("ALERT markers: {0}" -f (($markers | Select-Object -First 3) -join " || ")) -Alert
        }
        $issueKey = (($issues -join "|") + "|" + (($markers | Select-Object -First 5) -join "|"))
        Invoke-CodexRecoveryHandler -IssueKey $issueKey
    }
    return $allFinished
}

Write-WatchLine "watch_start interval_minutes=$IntervalMinutes stale_minutes=$StaleMinutes run_root=$RunRoot once=$Once exit_when_finished=$ExitWhenFinished codex_on_alert=$CodexOnAlert auto_run_recovery=$AutoRunRecovery"

do {
    $done = Invoke-WatchCheck
    if ($Once) {
        break
    }
    if ($ExitWhenFinished -and $done) {
        break
    }
    Start-Sleep -Seconds ([Math]::Max(60, $IntervalMinutes * 60))
} while ($true)
