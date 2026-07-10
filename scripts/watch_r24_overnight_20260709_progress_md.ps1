param(
    [string]$Root = "logs\r24_overnight_20260709_audit_deconfound",
    [int]$IntervalSec = 600,
    [int]$TotalSteps = 320000
)

# Maintains $Root\PROGRESS.md with per-arm state for user checking.
# Detached, chat-silent. Exits after arm7 finishes (one final write).

$arms = @(
    "arm1_qA_checkpoint_forced_audit",
    "arm2_null_arch_no_qA_forced_audit",
    "arm3_null_qD_probe_no_qA_forced_audit",
    "arm4_training_arm0_seed1",
    "arm5_training_arm2_seed1",
    "arm6_training_arm0_seed2",
    "arm7_training_arm2_seed2"
)

function Get-ArmRow([string]$arm) {
    $dir = Join-Path $Root $arm
    $status = Join-Path $dir "runner_status.txt"
    if (-not (Test-Path $status)) { return "| $arm | not started | - | - | - | - |" }
    $lines = Get-Content $status -ErrorAction SilentlyContinue
    $state = ($lines | Where-Object { $_ -like "state=*" } | Select-Object -First 1) -replace "state=", ""
    $exit  = ($lines | Where-Object { $_ -like "exit_code=*" } | Select-Object -First 1) -replace "exit_code=", ""
    $upd = "-"; $steps = "-"; $pct = "-"; $ret = "-"
    $csv = Join-Path $dir "metrics\train_updates.csv"
    if (Test-Path $csv) {
        try {
            $header = (Get-Content $csv -TotalCount 1) -split ","
            $iu = [array]::IndexOf($header, "update")
            $is = [array]::IndexOf($header, "total_steps")
            $ir = [array]::IndexOf($header, "return_mean")
            $last = (Get-Content $csv -Tail 1) -split ","
            if ($iu -ge 0 -and $last.Count -gt $iu) { $upd = $last[$iu] }
            if ($is -ge 0 -and $last.Count -gt $is) {
                $steps = $last[$is]
                $pct = "{0:P0}" -f ([double]$steps / $TotalSteps)
            }
            if ($ir -ge 0 -and $last.Count -gt $ir) { $ret = "{0:N3}" -f [double]$last[$ir] }
        } catch { }
    }
    $exitTxt = if ($exit) { $exit } else { "-" }
    return "| $arm | $state | $exitTxt | $upd | $steps ($pct) | $ret |"
}

while ($true) {
    $md = @()
    $md += "# R24 Overnight Run Progress"
    $md += ""
    $md += "Updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (auto-refresh every $IntervalSec s)"
    $md += ""
    $md += "Note: return_mean is the noisy TRAINING metric, not deconfound evidence."
    $md += "The arm0-vs-arm2 comparison uses eval rows read at completion."
    $md += ""
    $md += "| Arm | State | Exit | Update | Steps (% of $TotalSteps) | return_mean |"
    $md += "| --- | --- | --- | --- | --- | --- |"
    foreach ($arm in $arms) { $md += Get-ArmRow $arm }
    $md += ""
    $md += "Matched pairs: arm4+arm5 = seed 1, arm6+arm7 = seed 2."
    $md += "Audit arms (1-3) are Phase A, already dispositioned."
    Set-Content -Path (Join-Path $Root "PROGRESS.md") -Value ($md -join "`n") -Encoding UTF8

    $a7 = Join-Path $Root "arm7_training_arm2_seed2\runner_status.txt"
    if ((Test-Path $a7) -and ((Get-Content $a7 -ErrorAction SilentlyContinue) -match "state=finished")) {
        Add-Content -Path (Join-Path $Root "PROGRESS.md") -Value "`nRUN COMPLETE - progress watcher exited."
        break
    }
    Start-Sleep -Seconds $IntervalSec
}
