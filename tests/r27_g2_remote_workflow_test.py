from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "scripts" / "remote" / "run_hmasd_r27_g2.ps1"
SSH_CONFIG = ROOT / "scripts" / "remote" / "hmasd_autodl_ssh_config"
MANIFEST = ROOT / "scripts" / "r27_g2_runtime_package_manifest.txt"
WATCHER = ROOT / "scripts" / "remote" / "watch_r27_g2_status.sh"
PACKAGER = ROOT / "scripts" / "package_r27_g2_runtime.ps1"
EXPERIMENT_ID = "EXP-20260712-r27-g2-forced-z-trajectory-effect"


def find_pwsh() -> str:
    candidates = [
        shutil.which("pwsh"),
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        shutil.which("powershell"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("PowerShell is required for the remote workflow parser test")


def find_bash() -> str:
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("Git Bash is required for the remote watcher syntax test")


def find_windows_powershell() -> str:
    candidate = Path(os.environ.get("WINDIR", r"C:\Windows")) / (
        r"System32\WindowsPowerShell\v1.0\powershell.exe"
    )
    if candidate.is_file():
        return str(candidate)
    pytest.skip("Windows PowerShell 5.1 is required for native argv regression")


def write_mock_remote_harness(path: Path) -> None:
    path.write_text(
        r'''$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-MockRecord {
    param(
        [Parameter(Mandatory = $true)][string]$Tool,
        [Parameter(Mandatory = $true)][object[]]$Arguments
    )
    $values = @($Arguments | ForEach-Object { [string]$_ })
    $command = if ($values.Count -gt 0) { $values[-1] } else { "" }
    $record = [ordered]@{
        tool = $Tool
        arguments = $values
        command = $command
    }
    $json = $record | ConvertTo-Json -Compress -Depth 4
    [System.IO.File]::AppendAllText(
        $env:R27_MOCK_LOG,
        $json + "`n",
        [System.Text.UTF8Encoding]::new($false)
    )
}

function global:ssh {
    Write-MockRecord -Tool "ssh" -Arguments @($args)
    $global:LASTEXITCODE = 0
    if ($env:R27_MOCK_ACTION -eq "collect") {
        Write-Output "archive=/root/autodl-tmp/HMASD/r27_g2_remote/results/r27_fixture.tar.gz"
        Write-Output "collection_mode=complete"
    }
    elseif (
        $env:R27_MOCK_ACTION -eq "launch" -and
        ([string]$args[-1]).Contains("verify_checkpoint()")
    ) {
        Write-Output "checkpoint_ready=update25.pt"
        Write-Output "checkpoint_ready=update30.pt"
        Write-Output "checkpoint_ready=final.pt"
    }
}

function global:git {
    $global:LASTEXITCODE = 0
    $values = @($args | ForEach-Object { [string]$_ })
    $joined = $values -join " "
    if ($joined.Contains(" status --porcelain") -and $env:R27_MOCK_DIRTY -eq "1") {
        Write-Output " M scripts/run_r27_g2_forced_trajectory_effect_cloud_64env.sh"
    }
}

function global:scp {
    Write-MockRecord -Tool "scp" -Arguments @($args)
    $global:LASTEXITCODE = 0
    if ($env:R27_MOCK_ACTION -eq "collect") {
        $destination = [string]$args[-1]
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        $archive = Join-Path $destination "r27_fixture.tar.gz"
        $fixture = Join-Path $destination "archive_fixture"
        $runDir = Join-Path $fixture "runs/r27_fixture"
        $resultDir = Join-Path $fixture "results"
        $controllerDir = Join-Path $fixture "controller"
        New-Item -ItemType Directory -Path $runDir, $resultDir, $controllerDir -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $runDir "batch_status.txt") -Value "state=succeeded"
        Set-Content -LiteralPath (Join-Path $resultDir "r27_fixture.collection.env") -Value "collection_mode=complete"
        Set-Content -LiteralPath (Join-Path $controllerDir "current_source.env") -Value "repo_dir='/root/autodl-tmp/HMASD/source'"
        & tar -czf $archive -C $fixture .
        if ($LASTEXITCODE -ne 0) { throw "Unable to create fixture archive" }
    }
}

if ($env:R27_MOCK_ACTION -eq "launch") {
    & $env:R27_WORKFLOW `
        -Action launch `
        -GitBranch aggressive `
        -GitRemoteUrl https://example.invalid/hmasd.git `
        -MaxWorkers 2 `
        -ConcurrencyValidated `
        -LaunchAuthorization $env:R27_LAUNCH_AUTHORIZATION
}
elseif ($env:R27_MOCK_ACTION -eq "collect") {
    & $env:R27_WORKFLOW `
        -Action collect `
        -DownloadRoot $env:R27_DOWNLOAD_ROOT
}
else {
    throw "Unsupported mock action: $env:R27_MOCK_ACTION"
}
''',
        encoding="utf-8",
    )


def run_mock_remote_action(
    *,
    harness: Path,
    log_path: Path,
    home: Path,
    action: str,
    dirty: bool = False,
    authorization: str = "",
    download_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    (home / ".ssh").mkdir(parents=True, exist_ok=True)
    (home / ".ssh" / "imod_autodl").write_text("mock key\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "R27_WORKFLOW": str(WORKFLOW),
            "R27_MOCK_ACTION": action,
            "R27_MOCK_LOG": str(log_path),
            "R27_MOCK_DIRTY": "1" if dirty else "0",
            "R27_LAUNCH_AUTHORIZATION": authorization,
            "R27_DOWNLOAD_ROOT": "" if download_root is None else str(download_root),
        }
    )
    return subprocess.run(
        [
            find_pwsh(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(harness),
        ],
        cwd=ROOT,
        env=env,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def read_mock_records(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def test_remote_workflow_is_valid_powershell() -> None:
    command = (
        "$tokens=$null; $errors=$null; "
        f"[void][System.Management.Automation.Language.Parser]::ParseFile('{WORKFLOW}',"
        "[ref]$tokens,[ref]$errors); "
        "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        [find_pwsh(), "-NoProfile", "-Command", command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_remote_workflow_rejects_retired_deploy_action() -> None:
    result = subprocess.run(
        [find_pwsh(), "-NoProfile", "-File", str(WORKFLOW), "-Action", "deploy"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "deploy" in (result.stdout + result.stderr)


def test_remote_ssh_config_reuses_existing_key_without_secret_material() -> None:
    source = SSH_CONFIG.read_text(encoding="utf-8")
    assert "Host hmasd-autodl" in source
    assert "HostName connect.nmb1.seetacloud.com" in source
    assert "Port 40791" in source
    assert "User root" in source
    assert "IdentityFile ~/.ssh/imod_autodl" in source
    assert "BatchMode yes" in source
    assert "BEGIN OPENSSH PRIVATE KEY" not in source
    assert "PasswordAuthentication yes" not in source


def test_remote_terminal_watcher_is_valid_read_only_shell() -> None:
    result = subprocess.run(
        [find_bash(), "-n", str(WATCHER)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    source = WATCHER.read_text(encoding="utf-8")
    assert "--once" in source
    assert "nvidia-smi" in source
    assert "scientific_status" in source
    assert "classification" in source
    assert "runner_status.txt / batch_status.txt (read-only view)" in source
    assert not any(
        token in source for token in ("rm -", "mv ", "kill -TERM", "kill -KILL", "nohup")
    )


def test_remote_workflow_defaults_to_prepare_and_keeps_launch_gated() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert '[string]$Action = "prepare"' in source
    assert (
        '[string]$GitRemoteUrl = "git@github.com:CartmanFatass/My-paper-code.git"'
        in source
    )
    assert "Launch requires -LaunchAuthorization" in source
    assert "clean Git-managed HMASD worktree" in source
    assert "MAX_WORKERS>1 requires -ConcurrencyValidated" in source
    assert "576-960 collector hours" in source
    assert "R27_G2_CONCURRENCY_VALIDATED" in source
    assert '/root/autodl-tmp/HMASD/r27_g2_remote' in source
    assert '/root/autodl-tmp/HMASD/source' in source
    assert '/root/autodl-tmp/HMASD/checkpoint_dist' in source
    assert "screen -DmS" in source
    assert "nohup" not in source
    assert '"watch" { Watch-RemoteStatus }' in source
    assert "git pull --ff-only" in source
    assert "git status --porcelain" in source
    assert "current_source.env" in source
    assert source.count("printf '%s\\n'") >= 3
    assert 'printf "repo_dir=' not in source
    assert 'printf "REPO_DIR=' not in source
    assert 'printf "collection_mode=' not in source
    assert "REPO_DIR" in source
    assert "GIT_BRANCH" in source
    assert "validate-run --run-root" in source
    assert '$stateLine -eq "state=succeeded" -and $aliveLine -eq "process_alive=0"' in source
    assert "tar -tzf" in source
    assert "imod_autodl" not in source.lower().replace(
        'join-path $home ".ssh\\imod_autodl"', ""
    )


def test_single_quoted_env_serialization_survives_windows_native_argv(
    tmp_path: Path,
) -> None:
    capture_script = tmp_path / "capture_argv.py"
    captured_command = tmp_path / "captured_remote_command.sh"
    harness = tmp_path / "marshal_remote_command.ps1"
    capture_script.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path(sys.argv[1]).write_bytes(sys.argv[2].encode('utf-8'))\n",
        encoding="utf-8",
    )
    harness.write_text(
        r'''$ErrorActionPreference = "Stop"
$command = @"
set -euo pipefail
REPO_DIR='/root/autodl-tmp/HMASD/source'
GIT_BRANCH='aggressive'
collection_mode='complete'
printf '%s\n' \
  'repo_dir=/root/autodl-tmp/HMASD/source' \
  'git_branch=aggressive'
printf '%s\n' \
  "REPO_DIR=`$REPO_DIR" \
  "GIT_BRANCH=`$GIT_BRANCH"
printf '%s\n' \
  "collection_mode=`$collection_mode"
"@
& $env:R27_NATIVE_PYTHON `
  $env:R27_CAPTURE_SCRIPT `
  $env:R27_CAPTURED_COMMAND `
  $command
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
''',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.update(
        {
            "R27_NATIVE_PYTHON": os.fspath(Path(sys.executable)),
            "R27_CAPTURE_SCRIPT": os.fspath(capture_script),
            "R27_CAPTURED_COMMAND": os.fspath(captured_command),
        }
    )
    marshalled = subprocess.run(
        [
            find_windows_powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(harness),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert marshalled.returncode == 0, marshalled.stdout + marshalled.stderr

    remote_command = captured_command.read_text(encoding="utf-8")
    assert remote_command.count("printf '%s\\n'") == 3
    executed = subprocess.run(
        [find_bash(), "-c", remote_command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert executed.returncode == 0, executed.stdout + executed.stderr
    assert executed.stdout.splitlines() == [
        "repo_dir=/root/autodl-tmp/HMASD/source",
        "git_branch=aggressive",
        "REPO_DIR=/root/autodl-tmp/HMASD/source",
        "GIT_BRANCH=aggressive",
        "collection_mode=complete",
    ]


def test_runtime_manifest_tracks_remote_workflow_without_private_key() -> None:
    source = MANIFEST.read_text(encoding="utf-8")
    assert "file scripts/remote/hmasd_autodl_ssh_config" in source
    assert "file scripts/remote/run_hmasd_r27_g2.ps1" in source
    assert "file scripts/remote/watch_r27_g2_status.sh" in source
    assert "file docs/operations/R27_G2_REMOTE_AUTOMATION_20260712.md" in source
    assert "file tests/r27_g2_remote_workflow_test.py" in source
    assert ".ssh/imod_autodl" not in source


def test_launch_gates_precede_remote_start_and_rechecks_git_source(
    tmp_path: Path,
) -> None:
    harness = tmp_path / "mock_remote_harness.ps1"
    write_mock_remote_harness(harness)

    wrong_auth_log = tmp_path / "wrong_auth.jsonl"
    wrong_auth = run_mock_remote_action(
        harness=harness,
        log_path=wrong_auth_log,
        home=tmp_path / "home_wrong_auth",
        action="launch",
        authorization="not-authorized",
    )
    assert wrong_auth.returncode != 0
    assert "Launch requires -LaunchAuthorization" in (
        wrong_auth.stdout + wrong_auth.stderr
    )
    assert read_mock_records(wrong_auth_log) == []

    dirty_scope_log = tmp_path / "dirty_scope.jsonl"
    dirty_scope = run_mock_remote_action(
        harness=harness,
        log_path=dirty_scope_log,
        home=tmp_path / "home_dirty_scope",
        action="launch",
        dirty=True,
        authorization=EXPERIMENT_ID,
    )
    assert dirty_scope.returncode != 0
    assert "clean Git-managed HMASD worktree" in (
        dirty_scope.stdout + dirty_scope.stderr
    )
    assert read_mock_records(dirty_scope_log) == []

    launch_log = tmp_path / "launch.jsonl"
    launched = run_mock_remote_action(
        harness=harness,
        log_path=launch_log,
        home=tmp_path / "home_launch",
        action="launch",
        authorization=EXPERIMENT_ID,
    )
    assert launched.returncode == 0, launched.stdout + launched.stderr
    records = read_mock_records(launch_log)
    assert [record["tool"] for record in records] == ["ssh", "ssh"]
    assert "checkpoint_ready=" in str(records[0]["command"])
    command = str(records[1]["command"])

    source_index = command.index("git branch --show-current")
    checkpoint_index = command.index(
        "standalone_process_core_update_25.pt"
    )
    launch_index = command.index("screen -DmS")
    assert source_index < checkpoint_index < launch_index
    assert "git status --porcelain" in command[source_index:checkpoint_index]
    assert "REPO_DIR" in command
    assert "GIT_BRANCH" in command


def test_collect_preserves_remote_relative_expansions_and_provenance(
    tmp_path: Path,
) -> None:
    harness = tmp_path / "mock_remote_harness.ps1"
    write_mock_remote_harness(harness)
    log_path = tmp_path / "collect.jsonl"
    result = run_mock_remote_action(
        harness=harness,
        log_path=log_path,
        home=tmp_path / "home_collect",
        action="collect",
        download_root=tmp_path / "downloads",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    records = read_mock_records(log_path)
    assert [record["tool"] for record in records] == ["ssh", "scp"]
    command = str(records[0]["command"])

    for token in (
        'run_rel="runs/$name"',
        'launcher_name=$(basename "$LAUNCHER_LOG")',
        'launcher_rel="controller/$launcher_name"',
        'launch_script_name=$(basename "$LAUNCH_SCRIPT")',
        'launch_script_rel="controller/$launch_script_name"',
        'test "$RUN_ROOT" = ',
        'test "$run_repo_dir" = ',
        'test "$LAUNCHER_LOG" = ',
        'test "$LAUNCH_SCRIPT" = ',
        "items=(",
        '"$run_rel"',
        "controller/current_run.env",
        "controller/current_source.env",
        '"$metadata_rel"',
        'items+=("$launch_script_rel")',
        'validate-run --run-root "$RUN_ROOT"',
    ):
        assert token in command


def test_packager_rejects_gitignored_non_test_payload_from_directory_manifest(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    payload = source_root / "payload"
    scripts = source_root / "scripts"
    payload.mkdir(parents=True)
    scripts.mkdir(parents=True)
    (payload / "tracked_payload.txt").write_text("tracked\n", encoding="utf-8")
    ignored_payload = payload / "ignored_payload.json"
    ignored_payload.write_text('{"ignored": true}\n', encoding="utf-8")
    (source_root / ".gitignore").write_text(
        "payload/ignored_payload.json\n", encoding="utf-8"
    )
    manifest = scripts / "r27_g2_runtime_package_manifest.txt"
    manifest.write_text("directory payload\n", encoding="utf-8")
    (source_root / ".git").mkdir()
    mock_bin = tmp_path / "mock_bin"
    mock_bin.mkdir()
    mock_git = mock_bin / "git"
    mock_git.write_text(
        "#!/bin/sh\nprintf '%s\\n' 'payload/tracked_payload.txt'\n",
        encoding="utf-8",
    )
    mock_git.chmod(0o755)
    (mock_bin / "git.cmd").write_text(
        "@echo off\r\necho payload/tracked_payload.txt\r\nexit /b 0\r\n",
        encoding="ascii",
    )
    output_root = tmp_path / "output"
    env = os.environ.copy()
    env["PATH"] = str(mock_bin) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [
            find_pwsh(),
            "-NoProfile",
            "-File",
            str(PACKAGER),
            "-SourceRoot",
            str(source_root),
            "-OutputRoot",
            str(output_root),
            "-BundleName",
            "r27_g2_runtime_ignored_payload",
            "-ManifestPath",
            str(manifest),
        ],
        cwd=ROOT,
        env=env,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "ignored or unaccounted source files" in output
    assert ignored_payload.name in output
    assert not output_root.exists()
