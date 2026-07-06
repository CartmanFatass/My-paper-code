# R12 Stage 1 Overnight Auto Task Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows overnight automation task that waits for the currently running HA-CTSE training to finish, then sequentially launches the R12 Stage 1 local CUDA experiments.

**Architecture:** Add a wait-and-run PowerShell wrapper around the existing `scripts/run_r12_stage1_local_cuda.ps1`, then add a small Windows Task Scheduler registration script. The wrapper must not start a second training while the current `ha_ctse_process.train` process is still alive; it should log its own polling and launch decisions under a stable automation log directory.

**Tech Stack:** PowerShell 5/7 compatible scripts, Windows Task Scheduler, existing HA-CTSE Python training entrypoint.

**Execution status (2026-07-03 00:15):** Tasks 1-4 executed.  The Windows task
`HA-CTSE R12 Stage1 Overnight` was registered and started.  Validation found the
first launch reused a fixed log directory with stale rows/checkpoints, so the
contaminated run was stopped.  The runner now creates a fresh
`run_<timestamp>` root per invocation, and the task was relaunched cleanly under
`logs\ha_ctse_r12_stage1_local_cuda\run_20260703_001552`.

---

## Scope Boundary

This plan only creates automation around the already implemented R12 Stage 1 runner.

Allowed:

```text
wait for active ha_ctse_process.train processes
launch scripts/run_r12_stage1_local_cuda.ps1 sequentially
register/start a Windows scheduled task
write automation logs
update ExpRecord / ATTENTION_POINTER
```

Forbidden:

```text
changing HA-CTSE algorithm code
adding SEF/DADS reward
adding communication-specific reward
changing R12 Stage 1 experiment semantics
interpreting results before logs are read
```

## File Structure

- Create `scripts/run_r12_stage1_after_current.ps1`
  - Polls current Windows processes for existing `ha_ctse_process.train` runs.
  - Once none are present, invokes `scripts/run_r12_stage1_local_cuda.ps1`.
  - Supports dry-run mode, polling interval, max wait hours, and stable log output.
- Create `scripts/register_r12_stage1_overnight_task.ps1`
  - Registers a Windows scheduled task that runs the wait-and-run wrapper.
  - Starts the task immediately unless `-NoStart` is passed.
- Modify `memory/ExpRecord.md`
  - Append an automation note to `EXP-20260702-r12-stage1-situation-hazard`.
- Modify `memory/ATTENTION_POINTER.md`
  - Point current next action to the registered overnight automation task when it is created.

---

### Task 1: Add Wait-And-Run Overnight Wrapper

**Files:**
- Create: `scripts/run_r12_stage1_after_current.ps1`

- [ ] **Step 1: Create the wrapper script**

Create `scripts/run_r12_stage1_after_current.ps1`:

```powershell
param(
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "diag_only,oracle_change",
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [int]$PollSeconds = 300,
    [int]$MaxWaitHours = 18,
    [string]$AutomationLogDir = "logs\ha_ctse_r12_stage1_overnight_auto\_automation",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "ha_ctse_process\train.py")) {
    throw "Run this script from the HMASD repo root."
}

New-Item -ItemType Directory -Path $AutomationLogDir -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $AutomationLogDir "r12_stage1_after_current_$stamp.log"

function Write-AutoLog {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $logPath -Value $line -Encoding UTF8
}

function Get-ActiveHaCtseTrainProcesses {
    $self = $PID
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.ProcessId -ne $self -and
            $_.CommandLine -and
            $_.CommandLine -like "*ha_ctse_process.train*" -and
            $_.CommandLine -notlike "*-DryRun*"
        } |
        Select-Object ProcessId, ParentProcessId, Name, CommandLine
}

Write-AutoLog "R12 Stage 1 overnight wait-and-run starting."
Write-AutoLog "experiments=$Experiments total_timesteps=$TotalTimesteps num_envs=$NumEnvs device=$Device poll_seconds=$PollSeconds max_wait_hours=$MaxWaitHours dry_run=$DryRun"

$deadline = (Get-Date).AddHours([Math]::Max($MaxWaitHours, 1))
while ($true) {
    $active = @(Get-ActiveHaCtseTrainProcesses)
    if ($active.Count -eq 0) {
        Write-AutoLog "No active ha_ctse_process.train process found. Proceeding to R12 Stage 1 runner."
        break
    }

    Write-AutoLog ("Waiting for {0} active training process(es): {1}" -f $active.Count, (($active | ForEach-Object { $_.ProcessId }) -join ","))
    if ((Get-Date) -ge $deadline) {
        throw "Max wait time exceeded while waiting for current HA-CTSE training to finish."
    }
    Start-Sleep -Seconds ([Math]::Max($PollSeconds, 30))
}

$runner = ".\scripts\run_r12_stage1_local_cuda.ps1"
if (-not (Test-Path $runner)) {
    throw "Missing runner script: $runner"
}

$args = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $runner,
    "-Python", $Python,
    "-Experiments", $Experiments,
    "-TotalTimesteps", "$TotalTimesteps",
    "-NumEnvs", "$NumEnvs",
    "-Device", $Device
)

if ($DryRun) {
    $args += "-DryRun"
}

Write-AutoLog ("Launching: powershell.exe {0}" -f ($args -join " "))
& powershell.exe @args
$exitCode = $LASTEXITCODE
Write-AutoLog "R12 Stage 1 runner exited with code $exitCode"
exit $exitCode
```

- [ ] **Step 2: Dry-run the wrapper**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\run_r12_stage1_after_current.ps1 `
  -Experiments diag_only `
  -TotalTimesteps 32000 `
  -NumEnvs 4 `
  -PollSeconds 30 `
  -MaxWaitHours 1 `
  -DryRun
```

Expected:

```text
If current training exists:
  prints waiting lines and does not launch until the process ends or max wait triggers.

If no current training exists:
  prints one dry-run command for diag_only and exits 0.
```

Do not run a non-dry-run wrapper until the scheduled-task script is reviewed.

---

### Task 2: Add Scheduled Task Registration Script

**Files:**
- Create: `scripts/register_r12_stage1_overnight_task.ps1`

- [ ] **Step 1: Create the registration script**

Create `scripts/register_r12_stage1_overnight_task.ps1`:

```powershell
param(
    [string]$TaskName = "HA-CTSE R12 Stage1 Overnight",
    [string]$Python = "C:\Users\wu\.conda\envs\SB3\python.exe",
    [string]$Experiments = "diag_only,oracle_change",
    [int]$TotalTimesteps = 320000,
    [int]$NumEnvs = 16,
    [string]$Device = "cuda",
    [int]$PollSeconds = 300,
    [int]$MaxWaitHours = 18,
    [switch]$NoStart,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path ".").Path
$wrapper = Join-Path $root "scripts\run_r12_stage1_after_current.ps1"
if (-not (Test-Path $wrapper)) {
    throw "Missing wrapper script: $wrapper"
}

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$wrapper`"",
    "-Python", "`"$Python`"",
    "-Experiments", "`"$Experiments`"",
    "-TotalTimesteps", "$TotalTimesteps",
    "-NumEnvs", "$NumEnvs",
    "-Device", "`"$Device`"",
    "-PollSeconds", "$PollSeconds",
    "-MaxWaitHours", "$MaxWaitHours"
)

if ($DryRun) {
    $argList += "-DryRun"
}

$argumentString = $argList -join " "
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argumentString -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours ([Math]::Max($MaxWaitHours + 12, 24)))

Write-Host "Registering scheduled task: $TaskName"
Write-Host "Working directory: $root"
Write-Host "Action: powershell.exe $argumentString"

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Wait for current HA-CTSE training, then run R12 Stage 1 sequential CUDA experiments." `
    -Force | Out-Null

if (-not $NoStart) {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Started scheduled task: $TaskName"
} else {
    Write-Host "Registered but did not start scheduled task because -NoStart was provided."
}

Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State
```

- [ ] **Step 2: Register a dry-run task first**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\register_r12_stage1_overnight_task.ps1 `
  -TaskName "HA-CTSE R12 Stage1 Overnight DryRun" `
  -Experiments diag_only `
  -TotalTimesteps 32000 `
  -NumEnvs 4 `
  -PollSeconds 30 `
  -MaxWaitHours 1 `
  -DryRun
```

Expected:

```text
Scheduled task is registered and started.
It creates a log under logs\ha_ctse_r12_stage1_overnight_auto\_automation.
If no current training exists, the dry-run wrapper prints a command and exits.
```

- [ ] **Step 3: Remove the dry-run task after validation**

Run:

```powershell
Unregister-ScheduledTask -TaskName "HA-CTSE R12 Stage1 Overnight DryRun" -Confirm:$false
```

Expected:

```text
No output or successful removal.
```

---

### Task 3: Register the Real Overnight Task

**Files:**
- Uses: `scripts/register_r12_stage1_overnight_task.ps1`

- [ ] **Step 1: Register and start the real task**

Run from the repo root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\register_r12_stage1_overnight_task.ps1 `
  -TaskName "HA-CTSE R12 Stage1 Overnight" `
  -Experiments diag_only,oracle_change `
  -TotalTimesteps 320000 `
  -NumEnvs 16 `
  -Device cuda `
  -PollSeconds 300 `
  -MaxWaitHours 18
```

Expected:

```text
Task is registered and started.
The task waits while current HA-CTSE training is active.
After current training finishes, it runs diag_only then oracle_change sequentially.
```

- [ ] **Step 2: Check task state**

Run:

```powershell
Get-ScheduledTask -TaskName "HA-CTSE R12 Stage1 Overnight" | Format-List TaskName,State
```

Expected:

```text
State is Running or Ready.
```

- [ ] **Step 3: Check automation logs**

Run:

```powershell
Get-ChildItem logs\ha_ctse_r12_stage1_overnight_auto\_automation |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 3 Name,LastWriteTime,Length
```

Expected:

```text
At least one r12_stage1_after_current_*.log exists.
```

---

### Task 4: Update Experiment Record and Attention Pointer

**Files:**
- Modify: `memory/ExpRecord.md`
- Modify: `memory/ATTENTION_POINTER.md`

- [ ] **Step 1: Update ExpRecord status**

In `memory/ExpRecord.md`, under `EXP-20260702-r12-stage1-situation-hazard`, change:

```text
Result status: planned
```

to:

```text
Result status: queued via local Windows scheduled task
```

Add this to `Result summary`:

```text
Queued as Windows scheduled task `HA-CTSE R12 Stage1 Overnight`.  The task waits
for existing `ha_ctse_process.train` processes to exit, then runs
`diag_only,oracle_change` sequentially through
`scripts/run_r12_stage1_local_cuda.ps1` on CUDA with 16 envs / 320k steps.
Automation logs are under
`logs\ha_ctse_r12_stage1_overnight_auto\_automation`.
```

- [ ] **Step 2: Update attention pointer**

In `memory/ATTENTION_POINTER.md`, update the active next action line to:

```text
Active next action: monitor Windows scheduled task `HA-CTSE R12 Stage1 Overnight`
and then read `EXP-20260702-r12-stage1-situation-hazard` outputs after
`diag_only` and `oracle_change` complete.
```

Add a Last Update Note:

```text
2026-07-02 (R12 Stage 1 overnight automation queued): Added a wait-and-run
automation plan for the local CUDA Stage 1 read.  The task should wait for the
current training to finish, then run diag_only and oracle_change sequentially.
```

---

### Task 5: Validation and Handoff

**Files:**
- Uses scripts and memory files from Tasks 1-4.

- [ ] **Step 1: Syntax-check the PowerShell scripts**

Run:

```powershell
powershell.exe -NoProfile -Command "[System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\run_r12_stage1_after_current.ps1 -Raw), [ref]$null) | Out-Null; [System.Management.Automation.PSParser]::Tokenize((Get-Content .\scripts\register_r12_stage1_overnight_task.ps1 -Raw), [ref]$null) | Out-Null; 'ps_parse_ok'"
```

Expected:

```text
ps_parse_ok
```

- [ ] **Step 2: Confirm no algorithm files changed**

Run:

```powershell
git diff --name-only -- ha_ctse_process
```

Expected:

```text
No new algorithm-file names from this automation task.
```

- [ ] **Step 3: Report exact next morning readout paths**

Report these paths:

```text
Automation log:
  logs\ha_ctse_r12_stage1_overnight_auto\_automation

Training logs:
  logs\ha_ctse_r12_stage1_local_cuda\diag_only_reward_pure
  logs\ha_ctse_r12_stage1_local_cuda\oracle_change_reward_pure

Metrics to read:
  metrics\train_updates.csv
  eval\eval_summary.csv or eval checkpoint summaries if present
  standalone_train.log
```

---

## Self-Review

1. Spec coverage:
   - The plan creates an automatic task, not just a command.
   - It waits for the current training before launching new runs.
   - It launches R12 Stage 1 experiments sequentially.
   - It updates memory before interpretation.

2. Placeholder scan:
   - No `TODO`, `TBD`, or unspecified code paths remain in implementation steps.

3. Boundary check:
   - No HA-CTSE algorithm code is changed.
   - No reward path or communication-specific objective is added.
   - `learned_beta_small` remains out of the real overnight default because it is inference-only.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-02-r12-stage1-overnight-auto-task.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, then register the task.
2. **Inline Execution** - Execute these script/memory edits directly in this session.
