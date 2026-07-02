param(
    [string]$LogRoot = "logs\ha_ctse_process_g_info_local_cuda",
    [int]$Tail = 5,
    [string]$OutputDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Number {
    param(
        [object]$Row,
        [string]$Key
    )
    if ($null -eq $Row) { return 0.0 }
    $value = $Row.$Key
    if ($null -eq $value -or "$value" -eq "") { return 0.0 }
    $parsed = 0.0
    if ([double]::TryParse("$value", [ref]$parsed)) { return $parsed }
    return 0.0
}

function Get-Mean {
    param(
        [object[]]$Rows,
        [string]$Key
    )
    if ($Rows.Count -le 0) { return 0.0 }
    $sum = 0.0
    foreach ($row in $Rows) {
        $sum += Get-Number -Row $row -Key $Key
    }
    return $sum / [double]$Rows.Count
}

function Format-Value {
    param([double]$Value, [int]$Digits = 4)
    return $Value.ToString("F$Digits")
}

function Get-LatestEvalLine {
    param([string]$RunDir)
    $logPath = Join-Path $RunDir "standalone_train.log"
    if (-not (Test-Path $logPath)) { return "" }
    $line = Get-Content -Path $logPath -Tail 5000 -ErrorAction SilentlyContinue |
        Where-Object { $_ -match "standalone_eval\s+total_steps=" } |
        Select-Object -Last 1
    if ($null -eq $line) { return "" }
    return "$line"
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$stampFile = Get-Date -Format "yyyyMMdd_HHmmss"

$root = Resolve-Path -Path $LogRoot -ErrorAction SilentlyContinue
if ($null -eq $root) {
    if ([System.IO.Path]::IsPathRooted($LogRoot)) {
        $rootPath = $LogRoot
    } else {
        $rootPath = Join-Path (Get-Location).Path $LogRoot
    }
    if (-not $OutputDir) {
        $OutputDir = Join-Path $rootPath "_monitor"
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    $outPath = Join-Path $OutputDir "g_info_progress_$stampFile.txt"
    $latestPath = Join-Path $OutputDir "g_info_progress_latest.txt"
    $lines = @(
        "HA-CTSE G-info progress check",
        "timestamp=$timestamp",
        "log_root=$rootPath",
        "tail_updates=$Tail",
        "",
        "LogRoot not found yet. The monitor task is registered, but no run output has appeared."
    )
    $lines | Set-Content -Path $outPath -Encoding UTF8
    $lines | Set-Content -Path $latestPath -Encoding UTF8
    Write-Host ($lines -join [Environment]::NewLine)
    Write-Host ""
    Write-Host "Wrote monitor summary:"
    Write-Host "  $outPath"
    Write-Host "  $latestPath"
    exit 0
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $root.Path "_monitor"
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$outPath = Join-Path $OutputDir "g_info_progress_$stampFile.txt"
$latestPath = Join-Path $OutputDir "g_info_progress_latest.txt"

$metricKeys = @(
    "g_info_active",
    "g_info_objective_active",
    "g_info_loss",
    "g_info_skill_mi",
    "g_info_duration_mi",
    "g_info_total_mi",
    "g_itv_tv_skill",
    "g_itv_tv_duration",
    "g_joint_assignment_distance",
    "team_code_usage_entropy",
    "team_code_usage_max_frac",
    "team_code_skill_mi",
    "team_code_duration_mi",
    "team_code_edit_mi",
    "skill_usage_entropy",
    "duration_usage_entropy",
    "duration_usage_max_frac",
    "segment_length_mean",
    "env_reward_mean"
)

$csvPaths = Get-ChildItem -Path $root.Path -Filter train_updates.csv -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -like "*\metrics\train_updates.csv" } |
    Sort-Object FullName

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("HA-CTSE G-info progress check")
$lines.Add("timestamp=$timestamp")
$lines.Add("log_root=$($root.Path)")
$lines.Add("tail_updates=$Tail")
$lines.Add("")

if ($csvPaths.Count -eq 0) {
    $lines.Add("No metrics/train_updates.csv found yet.")
} else {
    foreach ($csv in $csvPaths) {
        $runDir = Split-Path -Parent (Split-Path -Parent $csv.FullName)
        $runName = Split-Path -Leaf $runDir
        $rows = @(Import-Csv -Path $csv.FullName)
        if ($rows.Count -eq 0) {
            $lines.Add("run=$runName rows=0")
            continue
        }
        $last = $rows[-1]
        $tailRows = @($rows | Select-Object -Last ([Math]::Max($Tail, 1)))
        $lines.Add("run=$runName")
        $lines.Add("  total_steps=$([int](Get-Number -Row $last -Key 'total_steps')) update=$([int](Get-Number -Row $last -Key 'update')) rows=$($rows.Count)")
        foreach ($key in $metricKeys) {
            $lastVal = Get-Number -Row $last -Key $key
            $tailVal = Get-Mean -Rows $tailRows -Key $key
            $lines.Add("  $key last=$(Format-Value $lastVal) tail_mean=$(Format-Value $tailVal)")
        }
        $evalLine = Get-LatestEvalLine -RunDir $runDir
        if ($evalLine) {
            $lines.Add("  latest_eval=$evalLine")
        } else {
            $lines.Add("  latest_eval=<none>")
        }
        $lines.Add("")
    }
}

$lines | Set-Content -Path $outPath -Encoding UTF8
$lines | Set-Content -Path $latestPath -Encoding UTF8

Write-Host ($lines -join [Environment]::NewLine)
Write-Host ""
Write-Host "Wrote monitor summary:"
Write-Host "  $outPath"
Write-Host "  $latestPath"
