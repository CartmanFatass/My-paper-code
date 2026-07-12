[CmdletBinding()]
param(
    [ValidateSet(
        "validate-local",
        "preflight",
        "sync-checkpoints",
        "sync-source",
        "dry-run",
        "prepare",
        "launch",
        "status",
        "watch",
        "wait",
        "collect",
        "all"
    )]
    [string]$Action = "prepare",
    [string]$GitBranch = "",
    [string]$GitRemoteName = "My-paper-code",
    [string]$GitRemoteUrl = "git@github.com:CartmanFatass/My-paper-code.git",
    [ValidateRange(1, 64)]
    [int]$MaxWorkers = 64,
    [switch]$ConcurrencyValidated,
    [string]$LaunchAuthorization = "",
    [ValidateRange(5, 3600)]
    [int]$PollSeconds = 60,
    [ValidateRange(1, 1200)]
    [int]$MaxWaitHours = 1000,
    [switch]$AllowPartialCollect,
    [string]$DownloadRoot = "dist/remote_results",
    [string]$RemoteBase = "/root/autodl-tmp/HMASD/r27_g2_remote",
    [string]$RemoteRepoRoot = "/root/autodl-tmp/HMASD/source",
    [string]$RemoteCheckpointRoot = "/root/autodl-tmp/HMASD/checkpoint_dist",
    [string]$LegacyRemoteCheckpointRoot = "/root/HMASD/dist",
    [ValidateRange(1, 49)]
    [int]$MinimumDataDiskFreeGiB = 20,
    [string]$RemotePython = "/root/miniconda3/bin/python3"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExperimentId = "EXP-20260712-r27-g2-forced-z-trajectory-effect"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SshConfig = Join-Path $PSScriptRoot "hmasd_autodl_ssh_config"
$Remote = "hmasd-autodl"
$script:ResolvedGitBranch = ""
$script:ResolvedGitRemoteUrl = ""
$script:WorktreeDirty = $true

function Assert-SafeRemotePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ($Path -notmatch '^/[A-Za-z0-9_./-]+$' -or $Path.Contains("..")) {
        throw "Unsafe remote path: $Path"
    }
}

function Assert-DataDiskRemotePath {
    param([Parameter(Mandatory = $true)][string]$Path)
    if ($Path -notmatch '^/root/autodl-tmp/HMASD(?:/|$)') {
        throw "R27-G2 source checkouts, checkpoints, logs, and results must stay on the data disk: $Path"
    }
}

function Assert-LocalPrerequisites {
    foreach ($command in ("git", "ssh", "scp")) {
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
            throw "Required command is unavailable: $command"
        }
    }
    if (-not (Test-Path -LiteralPath $SshConfig -PathType Leaf)) {
        throw "SSH config is missing: $SshConfig"
    }
    $privateKey = Join-Path $HOME ".ssh\imod_autodl"
    if (-not (Test-Path -LiteralPath $privateKey -PathType Leaf)) {
        throw "Dedicated AutoDL private key is missing: $privateKey"
    }
    Assert-SafeRemotePath $RemoteBase
    Assert-SafeRemotePath $RemoteRepoRoot
    Assert-SafeRemotePath $RemoteCheckpointRoot
    Assert-SafeRemotePath $LegacyRemoteCheckpointRoot
    Assert-SafeRemotePath $RemotePython
    Assert-DataDiskRemotePath $RemoteBase
    Assert-DataDiskRemotePath $RemoteRepoRoot
    Assert-DataDiskRemotePath $RemoteCheckpointRoot
}

function Resolve-GitSource {
    if (-not [string]::IsNullOrWhiteSpace($script:ResolvedGitBranch)) {
        return
    }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
        throw "HMASD source must be managed by Git: $RepoRoot"
    }
    $branch = $GitBranch
    if ([string]::IsNullOrWhiteSpace($branch)) {
        $branch = ((& git -C $RepoRoot branch --show-current) | Select-Object -First 1).Trim()
    }
    if (
        [string]::IsNullOrWhiteSpace($branch) -or
        $branch -notmatch '^[A-Za-z0-9._/-]+$' -or
        $branch.StartsWith("-") -or
        $branch.Contains("..")
    ) {
        throw "A safe named Git branch is required for R27-G2 remote source"
    }
    $remoteUrl = $GitRemoteUrl
    if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
        $remoteUrl = ((& git -C $RepoRoot remote get-url $GitRemoteName) | Select-Object -First 1).Trim()
    }
    if (
        [string]::IsNullOrWhiteSpace($remoteUrl) -or
        $remoteUrl -match '[\s''"]'
    ) {
        throw "A nonempty Git remote URL without whitespace or quotes is required"
    }
    $scopeStatus = @(& git -C $RepoRoot status --porcelain --untracked-files=normal)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect the Git-managed HMASD worktree"
    }
    $script:ResolvedGitBranch = $branch
    $script:ResolvedGitRemoteUrl = $remoteUrl
    $script:WorktreeDirty = [bool]($scopeStatus.Count -gt 0)
}

function Invoke-Remote {
    param([Parameter(Mandatory = $true)][string]$Command)
    $output = & ssh -F $SshConfig $Remote $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed with exit code ${LASTEXITCODE}: $Command"
    }
    return $output
}

function Invoke-RemotePreflight {
    Assert-LocalPrerequisites
    $checkpointRelativeDir = "logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"
    $checkpointDir = "$RemoteCheckpointRoot/$checkpointRelativeDir"
    $legacyCheckpointDir = "$LegacyRemoteCheckpointRoot/$checkpointRelativeDir"
    $minimumFreeKiB = [int64]$MinimumDataDiskFreeGiB * 1024 * 1024
    $command = @"
set -euo pipefail
command -v git >/dev/null
command -v tar >/dev/null
command -v screen >/dev/null
command -v df >/dev/null
test -d '/root/autodl-tmp'
root_device=`$(df -P /root | awk 'NR==2 {print `$1}')
data_device=`$(df -P /root/autodl-tmp | awk 'NR==2 {print `$1}')
test -n "`$root_device"
test -n "`$data_device"
if [ "`$root_device" = "`$data_device" ]; then
  echo '/root/autodl-tmp is not a separate data filesystem.' >&2
  exit 2
fi
data_free_kib=`$(df -Pk /root/autodl-tmp | awk 'NR==2 {print `$4}')
if [ "`$data_free_kib" -lt '$minimumFreeKiB' ]; then
  echo "Data disk has only `$data_free_kib KiB free; need at least $minimumFreeKiB KiB." >&2
  exit 2
fi
test -x '$RemotePython'
'$RemotePython' -c 'import torch; raise SystemExit(0 if torch.cuda.is_available() else 2)'
verify_checkpoint() {
  target="`$1"
  legacy="`$2"
  if [ -s "`$target" ]; then
    candidate="`$target"
  else
    candidate="`$legacy"
  fi
  test -s "`$candidate"
  printf 'checkpoint_ready=%s\n' "`$candidate"
}
verify_checkpoint \
  '$checkpointDir/standalone_process_core_update_25.pt' \
  '$legacyCheckpointDir/standalone_process_core_update_25.pt'
verify_checkpoint \
  '$checkpointDir/standalone_process_core_update_30.pt' \
  '$legacyCheckpointDir/standalone_process_core_update_30.pt'
verify_checkpoint \
  '$checkpointDir/standalone_process_core_final.pt' \
  '$legacyCheckpointDir/standalone_process_core_final.pt'
printf 'root_device=%s\ndata_device=%s\ndata_free_kib=%s\nscreen=%s\n' \
  "`$root_device" "`$data_device" "`$data_free_kib" "`$(command -v screen)"
"@
    $lines = @(Invoke-Remote $command)
    $readyCheckpoints = @($lines | Where-Object { $_ -match '^checkpoint_ready=' })
    if ($readyCheckpoints.Count -ne 3) {
        throw "Remote checkpoint preflight found $($readyCheckpoints.Count) nonempty checkpoints, expected 3"
    }
    Write-Host "Remote preflight passed: separate data disk, >=${MinimumDataDiskFreeGiB} GiB free, screen, CUDA Python, tools, and 3 nonempty checkpoints."
}

function Sync-RemoteCheckpoints {
    Assert-LocalPrerequisites
    $checkpointRelativeDir = "logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1"
    $checkpointDir = "$RemoteCheckpointRoot/$checkpointRelativeDir"
    $legacyCheckpointDir = "$LegacyRemoteCheckpointRoot/$checkpointRelativeDir"
    $command = @"
set -euo pipefail
mkdir -p '$checkpointDir'
stage_checkpoint() {
  source_path="`$1"
  target_path="`$2"
  if [ -s "`$target_path" ]; then
    printf 'checkpoint_cached=%s\n' "`$target_path"
    return 0
  fi
  test -s "`$source_path"
  temp_path="`$target_path.tmp.`$`$"
  trap 'rm -f "`$temp_path"' RETURN
  cp "`$source_path" "`$temp_path"
  test -s "`$temp_path"
  mv "`$temp_path" "`$target_path"
  trap - RETURN
  printf 'checkpoint_staged=%s\n' "`$target_path"
}
stage_checkpoint \
  '$legacyCheckpointDir/standalone_process_core_update_25.pt' \
  '$checkpointDir/standalone_process_core_update_25.pt'
stage_checkpoint \
  '$legacyCheckpointDir/standalone_process_core_update_30.pt' \
  '$checkpointDir/standalone_process_core_update_30.pt'
stage_checkpoint \
  '$legacyCheckpointDir/standalone_process_core_final.pt' \
  '$checkpointDir/standalone_process_core_final.pt'
"@
    Invoke-Remote $command
    Write-Host "Registered R27-G2 checkpoint files are present and nonempty on the data disk; model metadata is checked by the collector when loaded."
}

function Sync-RemoteSource {
    Assert-LocalPrerequisites
    Resolve-GitSource
    if ($script:WorktreeDirty) {
        throw "Remote source sync requires a clean Git-managed HMASD worktree"
    }
    $command = @"
set -euo pipefail
mkdir -p '$RemoteBase/controller' '$RemoteBase/results' '$RemoteBase/runs'
if [ -f '$RemoteBase/controller/current_run.env' ]; then
  . '$RemoteBase/controller/current_run.env'
  if screen -ls 2>/dev/null | grep -Eq "[.]`$SCREEN_SESSION[[:space:]]"; then
    echo 'Refusing to update the Git source while the registered R27-G2 run is active.' >&2
    exit 3
  fi
fi
if [ -d '$RemoteRepoRoot/.git' ]; then
  cd '$RemoteRepoRoot'
  test -z "`$(git status --porcelain --untracked-files=normal)"
  git fetch origin '$script:ResolvedGitBranch'
  git checkout '$script:ResolvedGitBranch'
  git pull --ff-only origin '$script:ResolvedGitBranch'
else
  if [ -e '$RemoteRepoRoot' ] && [ -n "`$(ls -A '$RemoteRepoRoot' 2>/dev/null)" ]; then
    echo 'Remote source path exists but is not an empty Git worktree.' >&2
    exit 3
  fi
  mkdir -p "`$(dirname '$RemoteRepoRoot')"
  git clone --branch '$script:ResolvedGitBranch' --single-branch \
    '$script:ResolvedGitRemoteUrl' '$RemoteRepoRoot'
fi
cd '$RemoteRepoRoot'
test "`$(git branch --show-current)" = '$script:ResolvedGitBranch'
test -z "`$(git status --porcelain --untracked-files=normal)"
test -f scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh
test -f scripts/audit_r27_forced_trajectory_effect.py
test -f ha_ctse_process/r27_g2_collector.py
printf '%s\n' \
  'repo_dir=$RemoteRepoRoot' \
  'git_branch=$script:ResolvedGitBranch' \
  > '$RemoteBase/controller/current_source.env'
"@
    Invoke-Remote $command | Out-Null
    Write-Host "Remote Git source is on branch $script:ResolvedGitBranch, fast-forward updated, and clean."
    Write-Host "Remote source: $RemoteRepoRoot"
}

function Invoke-RemoteDryRun {
    Resolve-GitSource
    $validated = if ($ConcurrencyValidated) { 1 } else { 0 }
    $command = @"
set -euo pipefail
cd '$RemoteRepoRoot'
test "`$(git branch --show-current)" = '$script:ResolvedGitBranch'
test -z "`$(git status --porcelain --untracked-files=normal)"
env \
  PYTHON_BIN='$RemotePython' \
  CHECKPOINT_DIST_ROOT='$RemoteCheckpointRoot' \
  RUN_ROOT='$RemoteBase/runs/dry_run_not_created' \
  MAX_WORKERS='$MaxWorkers' \
  R27_G2_CONCURRENCY_VALIDATED='$validated' \
  bash scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh --dry-run
"@
    Invoke-Remote $command
}

function Assert-LaunchAuthorization {
    Resolve-GitSource
    if ($LaunchAuthorization -ne $ExperimentId) {
        throw "Launch requires -LaunchAuthorization $ExperimentId"
    }
    if ($script:WorktreeDirty) {
        throw "Launch requires a clean Git-managed HMASD worktree"
    }
    if ($MaxWorkers -eq 1) {
        throw "Serial experiment launch is disabled; choose MAX_WORKERS from 2 through 64 and validate that parallel topology"
    }
    if (-not $ConcurrencyValidated) {
        throw "Parallel launch requires -ConcurrencyValidated after a separate safe GPU/process topology check"
    }
}

function Start-RemoteRun {
    Assert-LaunchAuthorization
    Invoke-RemotePreflight
    $runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $requestedRunRoot = "$RemoteBase/runs/r27_g2_forced_z_trajectory_effect_$runStamp"
    $validated = if ($ConcurrencyValidated) { 1 } else { 0 }
    $command = @"
set -euo pipefail
mkdir -p '$RemoteBase/controller' '$RemoteBase/runs'
state_file='$RemoteBase/controller/current_run.env'
if [ -f "`$state_file" ]; then
  . "`$state_file"
  test "`$REPO_DIR" = '$RemoteRepoRoot'
  test "`$GIT_BRANCH" = '$script:ResolvedGitBranch'
  test "`$RUN_MAX_WORKERS" = '$MaxWorkers'
  test "`$RUN_CONCURRENCY_VALIDATED" = '$validated'
else
  REPO_DIR='$RemoteRepoRoot'
  GIT_BRANCH='$script:ResolvedGitBranch'
  RUN_ROOT='$requestedRunRoot'
  LAUNCHER_LOG='$RemoteBase/controller/remote_launcher_$runStamp.log'
  SCREEN_SESSION='hmasd_r27_g2_$runStamp'
  LAUNCH_SCRIPT='$RemoteBase/controller/remote_launcher_$runStamp.sh'
  RUN_MAX_WORKERS='$MaxWorkers'
  RUN_CONCURRENCY_VALIDATED='$validated'
  printf '%s\n' \
    "REPO_DIR=`$REPO_DIR" \
    "GIT_BRANCH=`$GIT_BRANCH" \
    "RUN_ROOT=`$RUN_ROOT" \
    "LAUNCHER_LOG=`$LAUNCHER_LOG" \
    "SCREEN_SESSION=`$SCREEN_SESSION" \
    "LAUNCH_SCRIPT=`$LAUNCH_SCRIPT" \
    "RUN_MAX_WORKERS=`$RUN_MAX_WORKERS" \
    "RUN_CONCURRENCY_VALIDATED=`$RUN_CONCURRENCY_VALIDATED" \
    > "`$state_file"
fi
cd "`$REPO_DIR"
test "`$(git branch --show-current)" = '$script:ResolvedGitBranch'
test -z "`$(git status --porcelain --untracked-files=normal)"
test -s '$RemoteCheckpointRoot/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt'
test -s '$RemoteCheckpointRoot/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt'
test -s '$RemoteCheckpointRoot/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt'
if screen -ls 2>/dev/null | grep -Eq "[.]`$SCREEN_SESSION[[:space:]]"; then
  echo "ALREADY_RUNNING screen_session=`$SCREEN_SESSION"
else
  printf '#!/usr/bin/env bash\nset -euo pipefail\ncd %q\nexec env PYTHON_BIN=%q CHECKPOINT_DIST_ROOT=%q RUN_ROOT=%q MAX_WORKERS=%q CONTINUE_ON_ERROR=0 R27_G2_CONCURRENCY_VALIDATED=%q bash %q > %q 2>&1\n' \
    "`$REPO_DIR" '$RemotePython' '$RemoteCheckpointRoot' "`$RUN_ROOT" \
    '$MaxWorkers' '$validated' \
    'scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh' \
    "`$LAUNCHER_LOG" > "`$LAUNCH_SCRIPT"
  chmod 700 "`$LAUNCH_SCRIPT"
  screen -DmS "`$SCREEN_SESSION" bash "`$LAUNCH_SCRIPT"
  echo "LAUNCHED screen_session=`$SCREEN_SESSION run_root=`$RUN_ROOT"
fi
"@
    Invoke-Remote $command
}

function Get-RemoteStatus {
    Assert-LocalPrerequisites
    $command = @"
set -euo pipefail
state_file='$RemoteBase/controller/current_run.env'
if [ ! -f "`$state_file" ]; then
  echo 'state=not_started'
  echo 'process_alive=0'
  exit 0
fi
. "`$state_file"
echo "run_root=`$RUN_ROOT"
echo "repo_dir=`$REPO_DIR"
if [ -f "`$RUN_ROOT/batch_status.txt" ]; then
  cat "`$RUN_ROOT/batch_status.txt"
else
  echo 'state=not_started'
fi
if screen -ls 2>/dev/null | grep -Eq "[.]`$SCREEN_SESSION[[:space:]]"; then
  echo 'process_alive=1'
  echo "screen_session=`$SCREEN_SESSION"
else
  echo 'process_alive=0'
  echo "screen_session=`$SCREEN_SESSION"
fi
if [ -f "`$LAUNCHER_LOG" ]; then
  echo '--- launcher tail ---'
  tail -n 20 "`$LAUNCHER_LOG"
fi
"@
    return @(Invoke-Remote $command)
}

function Watch-RemoteStatus {
    Assert-LocalPrerequisites
    $command = @"
set -euo pipefail
if [ -f '$RemoteBase/controller/current_run.env' ]; then
  . '$RemoteBase/controller/current_run.env'
elif [ -f '$RemoteBase/controller/current_source.env' ]; then
  . '$RemoteBase/controller/current_source.env'
  REPO_DIR="`$repo_dir"
else
  echo 'No R27-G2 Git source is registered.' >&2
  exit 2
fi
exec env CONTROLLER_ROOT='$RemoteBase/controller' \
  bash "`$REPO_DIR/scripts/remote/watch_r27_g2_status.sh"
"@
    & ssh -t -F $SshConfig $Remote $command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote terminal dashboard exited with code $LASTEXITCODE"
    }
}

function Invoke-RemoteRunValidation {
    Assert-LocalPrerequisites
    $command = @"
set -euo pipefail
. '$RemoteBase/controller/current_run.env'
if screen -ls 2>/dev/null | grep -Eq "[.]`$SCREEN_SESSION[[:space:]]"; then
  echo 'Refusing final evidence validation while the R27-G2 screen session is alive.' >&2
  exit 3
fi
run_repo_dir="`$REPO_DIR"
run_git_branch="`$GIT_BRANCH"
cd "`$run_repo_dir"
test "`$(git branch --show-current)" = "`$run_git_branch"
test -z "`$(git status --porcelain --untracked-files=normal)"
'$RemotePython' scripts/audit_r27_forced_trajectory_effect.py \
  validate-run --run-root "`$RUN_ROOT"
"@
    $output = @(Invoke-Remote $command)
    Write-Host "Remote complete-run evidence passed 192 reset validations plus aggregate validation."
    return $output
}

function Wait-RemoteRun {
    $deadline = (Get-Date).AddHours($MaxWaitHours)
    while ((Get-Date) -lt $deadline) {
        $status = @(Get-RemoteStatus)
        $status | ForEach-Object { Write-Host $_ }
        $stateLine = $status | Where-Object { $_ -match '^state=' } | Select-Object -Last 1
        $aliveLine = $status | Where-Object { $_ -match '^process_alive=' } | Select-Object -Last 1
        $hasRunPointer = [bool]($status | Where-Object { $_ -match '^run_root=' })
        if ($stateLine -eq "state=succeeded" -and $aliveLine -eq "process_alive=0") {
            Invoke-RemoteRunValidation | ForEach-Object { Write-Host $_ }
            return
        }
        if ($stateLine -in @("state=failed", "state=interrupted", "state=crashed")) {
            throw "Remote R27-G2 runner reached terminal operational state: $stateLine"
        }
        if (
            $aliveLine -eq "process_alive=0" -and
            ($stateLine -ne "state=not_started" -or $hasRunPointer)
        ) {
            throw "Remote R27-G2 process stopped without a terminal batch status"
        }
        Start-Sleep -Seconds $PollSeconds
    }
    throw "Timed out after $MaxWaitHours hours waiting for remote R27-G2"
}

function Copy-RemoteResults {
    Assert-LocalPrerequisites
    $allowPartial = if ($AllowPartialCollect) { 1 } else { 0 }
    $command = @"
set -euo pipefail
. '$RemoteBase/controller/current_run.env'
test -d "`$RUN_ROOT"
if screen -ls 2>/dev/null | grep -Eq "[.]`$SCREEN_SESSION[[:space:]]"; then
  echo 'Refusing to archive a running R27-G2 process.' >&2
  exit 3
fi
batch_state=`$(sed -n 's/^state=//p' "`$RUN_ROOT/batch_status.txt" 2>/dev/null | tail -n 1)
run_repo_dir="`$REPO_DIR"
run_git_branch="`$GIT_BRANCH"
cd "`$run_repo_dir"
test "`$(git branch --show-current)" = "`$run_git_branch"
test -z "`$(git status --porcelain --untracked-files=normal)"
case "`$batch_state" in
  succeeded)
    '$RemotePython' scripts/audit_r27_forced_trajectory_effect.py \
      validate-run --run-root "`$RUN_ROOT" >/dev/null
    collection_mode=complete
    ;;
  failed|interrupted|crashed)
    if [ '$allowPartial' != '1' ]; then
      echo "Run is `$batch_state; pass -AllowPartialCollect to preserve failure evidence." >&2
      exit 3
    fi
    collection_mode=partial
    ;;
  *) echo "Run has no terminal batch status: `$batch_state" >&2; exit 3 ;;
esac
name=`$(basename "`$RUN_ROOT")
archive='$RemoteBase/results/'"`$name"'.tar.gz'
run_rel="runs/`$name"
launcher_name=`$(basename "`$LAUNCHER_LOG")
launcher_rel="controller/`$launcher_name"
launch_script_name=`$(basename "`$LAUNCH_SCRIPT")
launch_script_rel="controller/`$launch_script_name"
test "`$RUN_ROOT" = '$RemoteBase/'"`$run_rel"
test "`$run_repo_dir" = '$RemoteRepoRoot'
test "`$LAUNCHER_LOG" = '$RemoteBase/'"`$launcher_rel"
test "`$LAUNCH_SCRIPT" = '$RemoteBase/'"`$launch_script_rel"
metadata_rel="results/`$name.collection.env"
printf '%s\n' \
  "collection_mode=`$collection_mode" \
  "batch_state=`$batch_state" \
  "repo_dir=`$run_repo_dir" \
  "git_branch=`$run_git_branch" \
  "run_root=`$RUN_ROOT" \
  "screen_session=`$SCREEN_SESSION" \
  "launch_script=`$LAUNCH_SCRIPT" \
  > '$RemoteBase/'"`$metadata_rel"
items=(
  "`$run_rel"
  'controller/current_run.env'
  'controller/current_source.env'
  "`$metadata_rel"
)
if [ -f "`$LAUNCHER_LOG" ]; then
  items+=("`$launcher_rel")
fi
if [ -f "`$LAUNCH_SCRIPT" ]; then
  items+=("`$launch_script_rel")
fi
tar -czf "`$archive" -C '$RemoteBase' "`${items[@]}"
tar -tzf "`$archive" >/dev/null
echo "archive=`$archive"
echo "collection_mode=`$collection_mode"
"@
    $output = @(Invoke-Remote $command)
    $archiveLine = $output | Where-Object { $_ -match '^archive=' } | Select-Object -Last 1
    if ($null -eq $archiveLine) {
        throw "Remote result archive path was not returned"
    }
    $remoteArchive = $archiveLine.Substring("archive=".Length)
    Assert-SafeRemotePath $remoteArchive
    $base = if ([System.IO.Path]::IsPathRooted($DownloadRoot)) {
        $DownloadRoot
    }
    else {
        Join-Path $RepoRoot $DownloadRoot
    }
    $destination = Join-Path $base (Get-Date -Format "r27_g2_yyyyMMdd_HHmmss")
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    & scp -F $SshConfig "${Remote}:$remoteArchive" $destination
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to download remote R27-G2 result archive"
    }
    $localArchive = Join-Path $destination ([System.IO.Path]::GetFileName($remoteArchive))
    if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
        throw "Local tar command is required to inspect the downloaded result archive"
    }
    $archiveEntries = @(& tar -tzf $localArchive)
    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded R27-G2 result archive is unreadable"
    }
    $requiredEntrySuffixes = @(
        "/batch_status.txt",
        ".collection.env",
        "/current_source.env"
    )
    foreach ($suffix in $requiredEntrySuffixes) {
        if (-not ($archiveEntries | Where-Object { $_.EndsWith($suffix) })) {
            throw "Downloaded R27-G2 result archive lacks required content ending in $suffix"
        }
    }
    Write-Host "Results downloaded and archive structure verified: $localArchive"
    return $localArchive
}

switch ($Action) {
    "validate-local" {
        Assert-LocalPrerequisites
        Resolve-GitSource
        Write-Host "Local workflow validation passed. worktree_dirty=$script:WorktreeDirty git_branch=$script:ResolvedGitBranch"
    }
    "preflight" { Invoke-RemotePreflight }
    "sync-checkpoints" {
        Invoke-RemotePreflight
        Sync-RemoteCheckpoints
    }
    "sync-source" { Sync-RemoteSource }
    "dry-run" { Invoke-RemoteDryRun }
    "prepare" {
        Resolve-GitSource
        if ($script:WorktreeDirty) {
            throw "Prepare requires a clean Git-managed HMASD worktree"
        }
        Invoke-RemotePreflight
        Sync-RemoteCheckpoints
        Sync-RemoteSource
        Invoke-RemoteDryRun
    }
    "launch" {
        throw "Legacy R27-G2 launch is disabled; use run_hmasd_r27_g2_overnight.ps1 so topology and pilot gates cannot be bypassed"
    }
    "status" { Get-RemoteStatus }
    "watch" { Watch-RemoteStatus }
    "wait" { Wait-RemoteRun }
    "collect" { Copy-RemoteResults | Out-Null }
    "all" {
        throw "Legacy R27-G2 all-in-one launch is disabled; use run_hmasd_r27_g2_overnight.ps1 so topology and pilot gates cannot be bypassed"
    }
}
