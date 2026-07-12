[CmdletBinding()]
param(
    [ValidateSet("validate-local", "dry-run", "launch", "status", "watch")]
    [string]$Action = "dry-run",
    [string]$GitBranch = "",
    [string]$GitRemoteName = "My-paper-code",
    [string]$LaunchAuthorization = "",
    [ValidateRange(5, 3600)]
    [int]$PollSeconds = 60,
    [string]$RemoteBase = "/root/autodl-tmp/HMASD/r27_g2_remote",
    [string]$RemoteRepoRoot = "/root/autodl-tmp/HMASD/source",
    [string]$RemoteCheckpointRoot = "/root/autodl-tmp/HMASD/checkpoint_dist",
    [string]$RemotePython = "/root/miniconda3/bin/python3"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Authorization = "EXP-20260712-r27-g2-overnight-authorized"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SshConfig = Join-Path $PSScriptRoot "hmasd_autodl_ssh_config"
$Remote = "hmasd-autodl"
$script:ResolvedBranch = ""
$script:ResolvedCommit = ""

function Assert-SafeRemotePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ($Path -notmatch '^/root/autodl-tmp/HMASD(?:/[A-Za-z0-9_.-]+)*$' -or $Path.Contains("..")) {
        throw "Remote runtime path must be a safe HMASD data-disk path: $Path"
    }
}

function Assert-Tools {
    foreach ($name in @("git", "ssh", "scp")) {
        if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
            throw "Required command is unavailable: $name"
        }
    }
    if (-not (Test-Path -LiteralPath $SshConfig -PathType Leaf)) {
        throw "SSH config is missing: $SshConfig"
    }
    foreach ($path in @($RemoteBase, $RemoteRepoRoot, $RemoteCheckpointRoot)) {
        Assert-SafeRemotePath $path
    }
    if ($RemotePython -notmatch '^/[A-Za-z0-9_./-]+$' -or $RemotePython.Contains("..")) {
        throw "Unsafe remote Python path: $RemotePython"
    }
}

function Resolve-SynchronizedGitSource {
    if ($script:ResolvedCommit) { return }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
        throw "HMASD source must be Git-managed"
    }
    $branch = $GitBranch
    if (-not $branch) {
        $branch = ((& git -C $RepoRoot branch --show-current) | Select-Object -First 1).Trim()
    }
    if (-not $branch -or $branch -notmatch '^[A-Za-z0-9._/-]+$' -or $branch.Contains("..")) {
        throw "A safe named Git branch is required"
    }
    $dirty = @(& git -C $RepoRoot status --porcelain --untracked-files=normal)
    if ($LASTEXITCODE -ne 0) { throw "Unable to inspect the HMASD worktree" }
    if ($dirty.Count -gt 0) { throw "Overnight launch requires a clean Git worktree" }
    & git -C $RepoRoot fetch --quiet $GitRemoteName $branch
    if ($LASTEXITCODE -ne 0) { throw "Unable to fetch $GitRemoteName/$branch" }
    $localCommit = ((& git -C $RepoRoot rev-parse HEAD) | Select-Object -First 1).Trim()
    $remoteCommit = ((& git -C $RepoRoot rev-parse FETCH_HEAD) | Select-Object -First 1).Trim()
    if ($LASTEXITCODE -ne 0 -or $localCommit -notmatch '^[0-9a-f]{40}$') {
        throw "Unable to resolve the local Git commit"
    }
    if ($localCommit -ne $remoteCommit) {
        throw "Local HEAD is not synchronized with $GitRemoteName/$branch"
    }
    $script:ResolvedBranch = $branch
    $script:ResolvedCommit = $localCommit
}

function Invoke-Remote {
    param([Parameter(Mandatory = $true)][string]$Command)
    $output = & ssh -F $SshConfig $Remote $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed with exit code ${LASTEXITCODE}"
    }
    return @($output)
}

function Get-LauncherText {
    param(
        [Parameter(Mandatory = $true)][string]$OrchestrationRoot,
        [Parameter(Mandatory = $true)][string]$GitBranchValue,
        [Parameter(Mandatory = $true)][string]$GitCommitValue
    )
    $template = @'
#!/usr/bin/env bash
set -uo pipefail

REPO_DIR=__REPO__
GIT_BRANCH=__BRANCH__
GIT_COMMIT=__COMMIT__
CHECKPOINT_ROOT=__CHECKPOINTS__
PYTHON_BIN=__PYTHON__
ORCH_ROOT=__ORCH_ROOT__
STATUS_ROOT="$ORCH_ROOT/status"
LOG_ROOT="$ORCH_ROOT/logs"
STATE_FILE="$STATUS_ROOT/orchestration_status.env"
SELECTED_WORKERS=none
EXPECTED_WALL_CLOCK=not_selected
CURRENT_PHASE=initializing
PROBE_RESIDENCY_SECONDS=300
PROBE_STARTUP_TIMEOUT_SECONDS=480
PROBE_SHUTDOWN_TIMEOUT_SECONDS=60
PROBE_MAX_WALL_SECONDS=900
PROBE_MIN_FREE_GPU_MIB=4096
PROBE_MIN_FREE_HOST_MIB=8192
PROBE_MIN_FREE_HOST_FRACTION=0.15
MIN_START_FREE_GPU_MIB=22000
mkdir -p "$STATUS_ROOT" "$LOG_ROOT" "$ORCH_ROOT/runs"
exec >>"$LOG_ROOT/orchestrator.log" 2>&1

write_overall() {
  local state="$1" phase="$2" exit_code="$3" message="$4"
  local tmp="$STATE_FILE.tmp.$$"
  printf '%s\n' \
    "state=$state" "phase=$phase" "exit_code=$exit_code" \
    "selected_workers=$SELECTED_WORKERS" \
    "expected_wall_clock=$EXPECTED_WALL_CLOCK" \
    "device=cloud_cuda" "message=$message" "updated_at=$(date -Is)" > "$tmp"
  mv "$tmp" "$STATE_FILE"
}

write_phase() {
  local phase="$1" state="$2" exit_code="$3" log_path="$4" run_root="$5"
  local target tmp
  target="$STATUS_ROOT/$phase.env"
  tmp="$target.tmp.$$"
  printf '%s\n' \
    "phase=$phase" "state=$state" "exit_code=$exit_code" \
    "log_path=$log_path" "run_root=$run_root" "updated_at=$(date -Is)" > "$tmp"
  mv "$tmp" "$target"
}

fail_chain() {
  local exit_code="$1" message="$2"
  write_overall failed "$CURRENT_PHASE" "$exit_code" "$message"
  echo "overnight_failed phase=$CURRENT_PHASE exit_code=$exit_code message=$message"
  exit "$exit_code"
}

assert_gpu_idle() {
  local compute_pids start_free_gpu_mib
  compute_pids="$(
    nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null |
      awk '$1 ~ /^[0-9]+$/ {print $1}'
  )"
  if [ -n "$compute_pids" ]; then
    echo "GPU occupied by compute PID(s): $(printf '%s' "$compute_pids" | paste -sd, -)" >&2
    return 46
  fi
  start_free_gpu_mib="$(
    nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null |
      awk 'NR==1 {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $0); print $0}'
  )"
  if ! [[ "$start_free_gpu_mib" =~ ^[0-9]+$ ]] || \
     [ "$start_free_gpu_mib" -lt "$MIN_START_FREE_GPU_MIB" ]; then
    echo "GPU start-free memory ${start_free_gpu_mib:-unknown} MiB is below ${MIN_START_FREE_GPU_MIB} MiB" >&2
    return 46
  fi
}

run_phase() {
  local phase="$1" run_root="$2"
  shift 2
  local log_path="$LOG_ROOT/$phase.log" rc
  CURRENT_PHASE="$phase"
  write_overall running "$phase" 0 phase_running
  write_phase "$phase" running 0 "$log_path" "$run_root"
  set +e
  "$@" > "$log_path" 2>&1
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    write_phase "$phase" failed "$rc" "$log_path" "$run_root"
    return "$rc"
  fi
  write_phase "$phase" succeeded 0 "$log_path" "$run_root"
  return 0
}

validate_probe() {
  local root="$1" workers="$2" status="$root/runner_status.txt" report="$root/topology_probe.json"
  test -f "$status" && test -f "$report" || return 31
  grep -Fxq 'state=succeeded' "$status" || return 31
  grep -Fxq 'probe_status=PASS' "$status" || return 31
  grep -Fxq "workers_requested=$workers" "$status" || return 31
  grep -Fxq "workers_passed=$workers" "$status" || return 31
  "$PYTHON_BIN" - "$report" "$workers" <<'PY' || return 31
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)
n = int(sys.argv[2])
required = {
    "status": "PASS", "operational_gate": "PASS", "scientific_evidence": False,
    "workers_requested": n, "workers_ready": n, "workers_resident": n,
    "workers_passed": n, "failure_class": "NONE", "resource_failure": False,
    "residency_seconds": 300.0, "startup_timeout_seconds": 480.0,
    "shutdown_timeout_seconds": 60.0, "max_wall_seconds": 900.0,
    "required_gpu_free_mib": 4096.0,
    "required_host_available_mib": 8192.0,
    "required_host_available_fraction": 0.15,
}
if any(report.get(key) != value for key, value in required.items()):
    raise SystemExit(31)
PY
}

run_probe() {
  local workers="$1" root="$2" rc
  assert_gpu_idle || return $?
  env PROBE_WORKERS="$workers" RUN_ROOT="$root" PYTHON_BIN="$PYTHON_BIN" \
    CHECKPOINT_DIST_ROOT="$CHECKPOINT_ROOT" \
    RESIDENCY_SECONDS="$PROBE_RESIDENCY_SECONDS" \
    STARTUP_TIMEOUT_SECONDS="$PROBE_STARTUP_TIMEOUT_SECONDS" \
    SHUTDOWN_TIMEOUT_SECONDS="$PROBE_SHUTDOWN_TIMEOUT_SECONDS" \
    MAX_WALL_SECONDS="$PROBE_MAX_WALL_SECONDS" \
    MIN_FREE_GPU_MIB="$PROBE_MIN_FREE_GPU_MIB" \
    MIN_FREE_HOST_MIB="$PROBE_MIN_FREE_HOST_MIB" \
    MIN_FREE_HOST_FRACTION="$PROBE_MIN_FREE_HOST_FRACTION" \
    MIN_START_FREE_GPU_MIB="$MIN_START_FREE_GPU_MIB" \
    bash scripts/run_r27_g2_topology_probe_cloud.sh
  rc=$?
  [ "$rc" -eq 0 ] || return "$rc"
  validate_probe "$root" "$workers"
}

probe_resource_failure() {
  local root="$1" status="$root/runner_status.txt" report="$root/topology_probe.json"
  test -f "$status" && test -f "$report" || return 1
  grep -Fxq 'state=failed' "$status" || return 1
  grep -Fxq 'probe_status=FAIL' "$status" || return 1
  grep -Fxq 'failure_class=RESOURCE_CAPACITY' "$status" || return 1
  "$PYTHON_BIN" - "$report" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)
ok = (report.get("status") == "FAIL" and
      report.get("failure_class") == "RESOURCE_CAPACITY" and
      report.get("resource_failure") is True)
raise SystemExit(0 if ok else 1)
PY
}

run_pilot() {
  local root="$1" status="$root/pilot_status.txt" summary="$root/pilot_summary.json" rc
  assert_gpu_idle || return $?
  env MAX_WORKERS=8 RUN_ROOT="$root" PYTHON_BIN="$PYTHON_BIN" \
    CHECKPOINT_DIST_ROOT="$CHECKPOINT_ROOT" R27_G2_CONCURRENCY_VALIDATED=1 \
    bash scripts/run_r27_g2_forced_trajectory_effect_pilot_cloud.sh
  rc=$?
  [ "$rc" -eq 0 ] || return "$rc"
  test -f "$status" && test -f "$summary" || return 32
  grep -Fxq 'state=WIRING_PASS' "$status" || return 32
  grep -Fxq 'scientific_status=NOT_EVALUATED' "$status" || return 32
  grep -Fxq 'eligible_for_scientific_gate=false' "$status" || return 32
  grep -Fxq 'expected_resets=8' "$status" || return 32
  grep -Fxq 'validated_resets=8' "$status" || return 32
  grep -Fxq 'environment_steps=83600' "$status" || return 32
  "$PYTHON_BIN" - "$summary" <<'PY' || return 32
import json, sys
with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)
if not isinstance(report, dict):
    raise SystemExit(32)
PY
}

run_decision() {
  local root="$1" workers="$2" rc
  assert_gpu_idle || return $?
  env MAX_WORKERS="$workers" RUN_ROOT="$root" PYTHON_BIN="$PYTHON_BIN" \
    CHECKPOINT_DIST_ROOT="$CHECKPOINT_ROOT" CONTINUE_ON_ERROR=0 \
    R27_G2_CONCURRENCY_VALIDATED=1 \
    bash scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh
  rc=$?
  [ "$rc" -eq 0 ] || return "$rc"
  test -f "$root/batch_status.txt" || return 33
  grep -Fxq 'state=succeeded' "$root/batch_status.txt" || return 33
  "$PYTHON_BIN" scripts/audit_r27_forced_trajectory_effect.py validate-run --run-root "$root"
}

cd "$REPO_DIR" || fail_chain 20 repo_missing
[ "$(git branch --show-current)" = "$GIT_BRANCH" ] || fail_chain 20 branch_mismatch
[ "$(git rev-parse HEAD)" = "$GIT_COMMIT" ] || fail_chain 20 commit_mismatch
if git status --porcelain --untracked-files=normal | grep -q .; then
  fail_chain 20 remote_worktree_dirty
fi

PROBE8_ROOT="$ORCH_ROOT/runs/probe8"
PILOT_ROOT="$ORCH_ROOT/runs/pilot"
PROBE64_ROOT="$ORCH_ROOT/runs/probe64"
PROBE32_ROOT="$ORCH_ROOT/runs/probe32"
DECISION_ROOT="$ORCH_ROOT/runs/decision_grade"

write_overall running initializing 0 chain_started
if ! run_phase topology_probe_8 "$PROBE8_ROOT" run_probe 8 "$PROBE8_ROOT"; then
  fail_chain 41 probe8_failed
fi
if ! run_phase wiring_pilot_8 "$PILOT_ROOT" run_pilot "$PILOT_ROOT"; then
  fail_chain 42 pilot_not_wiring_pass
fi

if run_phase topology_probe_64 "$PROBE64_ROOT" run_probe 64 "$PROBE64_ROOT"; then
  SELECTED_WORKERS=64
  EXPECTED_WALL_CLOCK=12-20h
else
  if ! probe_resource_failure "$PROBE64_ROOT"; then
    fail_chain 43 probe64_execution_failure
  fi
  if ! run_phase topology_probe_32 "$PROBE32_ROOT" run_probe 32 "$PROBE32_ROOT"; then
    fail_chain 44 probe32_failed_no_lower_fallback
  fi
  SELECTED_WORKERS=32
  EXPECTED_WALL_CLOCK=24-40h
fi
printf '%s\n' "selected_workers=$SELECTED_WORKERS" \
  "expected_wall_clock=$EXPECTED_WALL_CLOCK" > "$STATUS_ROOT/selection.env"

if ! run_phase decision_grade "$DECISION_ROOT" run_decision "$DECISION_ROOT" "$SELECTED_WORKERS"; then
  fail_chain 45 decision_grade_failed
fi
CURRENT_PHASE=complete
write_overall succeeded complete 0 chain_complete
echo "overnight_succeeded selected_workers=$SELECTED_WORKERS run_root=$DECISION_ROOT"
'@
    return $template.Replace("__REPO__", $RemoteRepoRoot).
        Replace("__BRANCH__", $GitBranchValue).
        Replace("__COMMIT__", $GitCommitValue).
        Replace("__CHECKPOINTS__", $RemoteCheckpointRoot).
        Replace("__PYTHON__", $RemotePython).
        Replace("__ORCH_ROOT__", $OrchestrationRoot)
}

function Show-DryRun {
    Resolve-SynchronizedGitSource
    Write-Host "DRY_RUN=1; no SSH, screen, run directory, or experiment was started."
    Write-Host "git_branch=$script:ResolvedBranch git_commit=$script:ResolvedCommit device=cloud_cuda"
    Write-Host "phase_order=probe8 -> pilot8(WIRING_PASS) -> probe64 -> [RESOURCE_CAPACITY only: probe32] -> decision_grade"
    Write-Host "probe8=5-15m; pilot8=3-5h/83600_steps; probe64=7-15m"
    Write-Host "decision_phase64=12-20h; full_chain64=15-26h"
    Write-Host "decision_phase32=24-40h; full_chain32=28-46h"
    Write-Host "serial_fallback=forbidden; workers_below_32=forbidden"
    Write-Host "PROBE_WORKERS=8 ... bash scripts/run_r27_g2_topology_probe_cloud.sh --dry-run"
    Write-Host "MAX_WORKERS=8 R27_G2_CONCURRENCY_VALIDATED=1 ... bash scripts/run_r27_g2_forced_trajectory_effect_pilot_cloud.sh --dry-run"
    Write-Host "PROBE_WORKERS=64 ... bash scripts/run_r27_g2_topology_probe_cloud.sh --dry-run"
    Write-Host "PROBE_WORKERS=32 ... bash scripts/run_r27_g2_topology_probe_cloud.sh --dry-run"
    Write-Host "MAX_WORKERS=<64-or-32> R27_G2_CONCURRENCY_VALIDATED=1 ... bash scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh --dry-run"
}

function Start-Overnight {
    if ($LaunchAuthorization -ne $Authorization) {
        throw "Launch requires -LaunchAuthorization $Authorization"
    }
    Assert-Tools
    Resolve-SynchronizedGitSource
    $checkpointDir = "$RemoteCheckpointRoot/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"
    $preflight = @"
set -euo pipefail
command -v git >/dev/null
command -v screen >/dev/null
command -v nvidia-smi >/dev/null
test -x '$RemotePython'
'$RemotePython' -c 'import torch; raise SystemExit(0 if torch.cuda.is_available() else 2)'
compute_pids=`$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | awk '`$1 ~ /^[0-9]+`$/ {print `$1}')
test -z "`$compute_pids"
start_free_gpu_mib=`$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1 {gsub(/^[[:space:]]+|[[:space:]]+`$/, "", `$0); print `$0}')
test -n "`$start_free_gpu_mib"
test "`$start_free_gpu_mib" -ge 22000
root_device=`$(df -P /root | awk 'NR==2 {print `$1}')
data_device=`$(df -P /root/autodl-tmp | awk 'NR==2 {print `$1}')
data_free_kib=`$(df -Pk /root/autodl-tmp | awk 'NR==2 {print `$4}')
test -n "`$root_device"
test -n "`$data_device"
test "`$root_device" != "`$data_device"
test "`$data_free_kib" -ge 20971520
test -d '$RemoteRepoRoot/.git'
cd '$RemoteRepoRoot'
if git status --porcelain --untracked-files=normal | grep -q .; then exit 21; fi
git fetch origin '$script:ResolvedBranch'
git checkout '$script:ResolvedBranch'
git pull --ff-only origin '$script:ResolvedBranch'
test "`$(git rev-parse HEAD)" = '$script:ResolvedCommit'
test -f scripts/run_r27_g2_topology_probe_cloud.sh
test -f scripts/run_r27_g2_forced_trajectory_effect_pilot_cloud.sh
test -f scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh
test -s '$checkpointDir/standalone_process_core_update_25.pt'
test -s '$checkpointDir/standalone_process_core_update_30.pt'
test -s '$checkpointDir/standalone_process_core_final.pt'
mkdir -p '$RemoteBase/controller' '$RemoteBase/runs'
if screen -ls 2>/dev/null | grep -Eq '[.]hmasd_r27_g2_'; then
  echo 'An R27-G2 screen session is already active.' >&2
  exit 22
fi
if [ -f '$RemoteBase/controller/current_overnight.env' ]; then
  echo 'A prior overnight pointer exists; refusing an implicit rerun.' >&2
  exit 22
fi
"@
    Invoke-Remote $preflight | ForEach-Object { Write-Host $_ }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $orchestrationRoot = "$RemoteBase/runs/r27_g2_overnight_$stamp"
    $remoteLauncher = "$RemoteBase/controller/r27_g2_overnight_$stamp.sh"
    $screenSession = "hmasd_r27_g2_overnight_$stamp"
    $launcher = Get-LauncherText -OrchestrationRoot $orchestrationRoot `
        -GitBranchValue $script:ResolvedBranch -GitCommitValue $script:ResolvedCommit
    $tempLauncher = Join-Path ([System.IO.Path]::GetTempPath()) "r27_g2_overnight_$stamp.sh"
    [System.IO.File]::WriteAllText(
        $tempLauncher,
        ($launcher -replace "`r`n", "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )
    try {
        & scp -F $SshConfig $tempLauncher "${Remote}:$remoteLauncher"
        if ($LASTEXITCODE -ne 0) { throw "Failed to upload the generated overnight controller" }
    }
    finally {
        Remove-Item -LiteralPath $tempLauncher -Force -ErrorAction SilentlyContinue
    }
    $statusFile = "$orchestrationRoot/status/orchestration_status.env"
    $orchestratorLog = "$orchestrationRoot/logs/orchestrator.log"
    $start = @"
set -euo pipefail
launch_lock='$RemoteBase/controller/overnight_launch.lock'
if ! mkdir "`$launch_lock" 2>/dev/null; then
  echo 'Another overnight launch transaction is active.' >&2
  exit 22
fi
trap 'rmdir "`$launch_lock" 2>/dev/null || true' EXIT
if [ -f '$RemoteBase/controller/current_overnight.env' ]; then
  echo 'A prior overnight pointer exists; refusing an implicit rerun.' >&2
  exit 22
fi
if screen -ls 2>/dev/null | grep -Eq '[.]hmasd_r27_g2_'; then
  echo 'An R27-G2 screen session is already active.' >&2
  exit 22
fi
chmod 700 '$remoteLauncher'
bash -n '$remoteLauncher'
printf '%s\n' \
  'ORCH_ROOT=$orchestrationRoot' \
  'STATUS_FILE=$statusFile' \
  'ORCHESTRATOR_LOG=$orchestratorLog' \
  'SCREEN_SESSION=$screenSession' \
  'GIT_BRANCH=$script:ResolvedBranch' \
  'GIT_COMMIT=$script:ResolvedCommit' \
  > '$RemoteBase/controller/current_overnight.env'
screen -DmS '$screenSession' bash '$remoteLauncher'
sleep 2
if screen -ls 2>/dev/null | grep -Eq '[.]$screenSession[[:space:]]'; then
  echo 'state=running'
  echo 'screen_session=$screenSession'
  echo 'orchestration_root=$orchestrationRoot'
elif grep -Eq '^state=(succeeded|failed)$' '$statusFile' 2>/dev/null; then
  cat '$statusFile'
else
  echo 'Overnight controller failed before recording terminal state.' >&2
  exit 23
fi
"@
    Invoke-Remote $start | ForEach-Object { Write-Host $_ }
    Write-Host "Expected cost: probe8 5-15m; pilot 3-5h; probe64 7-15m; decision phase 12-20h at 64 workers."
    Write-Host "Approximate full chain: 15-26h at 64; only a resource-capacity failure may select 32 (28-46h full chain)."
    Write-Host "There is no lower-worker, serial, CPU, or occupied-GPU fallback."
}

function Get-OvernightStatus {
    Assert-Tools
    $command = @"
set -euo pipefail
pointer='$RemoteBase/controller/current_overnight.env'
if [ ! -f "`$pointer" ]; then echo 'state=not_started'; echo 'process_alive=0'; exit 0; fi
. "`$pointer"
cat "`$STATUS_FILE" 2>/dev/null || echo 'state=initializing'
if [ -d "`$ORCH_ROOT/status" ]; then
  for status in "`$ORCH_ROOT"/status/*.env; do
    [ -f "`$status" ] || continue
    echo "--- `$(basename "`$status") ---"
    cat "`$status"
  done
fi
if screen -ls 2>/dev/null | grep -Eq "[.]`$SCREEN_SESSION[[:space:]]"; then
  echo 'process_alive=1'
else
  echo 'process_alive=0'
fi
if [ -f "`$ORCHESTRATOR_LOG" ]; then echo '--- orchestrator tail ---'; tail -n 30 "`$ORCHESTRATOR_LOG"; fi
"@
    return @(Invoke-Remote $command)
}

switch ($Action) {
    "validate-local" {
        Assert-Tools
        Resolve-SynchronizedGitSource
        Write-Host "Local validation passed: branch=$script:ResolvedBranch commit=$script:ResolvedCommit"
    }
    "dry-run" { Show-DryRun }
    "launch" { Start-Overnight }
    "status" { Get-OvernightStatus }
    "watch" {
        while ($true) {
            $lines = @(Get-OvernightStatus)
            Clear-Host
            $lines | ForEach-Object { Write-Host $_ }
            $state = $lines | Where-Object { $_ -match '^state=' } | Select-Object -First 1
            $alive = $lines | Where-Object { $_ -match '^process_alive=' } | Select-Object -Last 1
            if ($state -in @("state=succeeded", "state=failed") -and $alive -eq "process_alive=0") { break }
            Start-Sleep -Seconds $PollSeconds
        }
    }
}
