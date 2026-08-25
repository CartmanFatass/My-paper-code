from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "dist" / "remote_log_sync" / "remote_log_sync.config.json"
AUTO_LOCAL_ROOT = REPO_ROOT / "dist" / "remote_log_sync" / "synced" / "logs_cloud_p0_32env"


def _powershell() -> str:
    exe = shutil.which("pwsh") or shutil.which("powershell")
    if exe is None:
        raise AssertionError("PowerShell executable not found")
    return exe


def _run_ps(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    command = [
        _powershell(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REPO_ROOT / script),
        *args,
    ]
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_remote_log_sync_dry_run_reads_config_contract() -> None:
    result = _run_ps(
        "dist/remote_log_sync/sync_remote_logs_ssh.ps1",
        "-Config",
        str(CONFIG_PATH),
        "-DryRun",
    )

    assert result.returncode == 0, result.stderr
    assert "HA-CTSE remote log SSH sync" in result.stdout
    assert f"config={CONFIG_PATH}" in result.stdout
    assert "remote=ubuntu@example.com" in result.stdout
    assert "remote_log_root=/home/ubuntu/HMASD/logs_cloud_p0_32env" in result.stdout
    assert f"local_log_root={AUTO_LOCAL_ROOT}" in result.stdout
    assert "interval_minutes=30" in result.stdout
    assert "include_patterns=standalone_train.log,metrics/*.csv,_monitor/*.txt" in result.stdout
    assert "ssh list command:" in result.stdout
    assert "DryRun requested; not connecting to remote host." in result.stdout


def test_remote_log_sync_task_dry_run_uses_configured_30_minute_schedule() -> None:
    result = _run_ps(
        "dist/remote_log_sync/register_remote_log_sync_task.ps1",
        "-Config",
        str(CONFIG_PATH),
        "-TaskName",
        "HA-CTSE Remote Log Sync Test",
        "-DryRun",
    )

    assert result.returncode == 0, result.stderr
    assert "Registering remote log sync scheduled task:" in result.stdout
    assert f"config:    {CONFIG_PATH}" in result.stdout
    assert "remote:    ubuntu@example.com" in result.stdout
    assert f"output:    {AUTO_LOCAL_ROOT}" in result.stdout
    assert "interval:  every 30 minutes" in result.stdout
    assert "/SC MINUTE" in result.stdout
    assert "/MO 30" in result.stdout
    assert "sync_remote_logs_ssh.ps1" in result.stdout
    assert "remote_log_sync.config.json" in result.stdout
    assert "DryRun requested; not registering scheduled task." in result.stdout


def test_remote_log_sync_defaults_to_lightweight_configured_files() -> None:
    config = CONFIG_PATH.read_text(encoding="utf-8")
    script = (REPO_ROOT / "dist/remote_log_sync/sync_remote_logs_ssh.ps1").read_text(encoding="utf-8")

    assert '"intervalMinutes": 30' in config
    assert '"localLogRoot": "auto"' in config
    assert '"remote": "ubuntu@example.com"' in config
    assert '"remoteLogRoot": "/home/ubuntu/HMASD/logs_cloud_p0_32env"' in config
    assert '"standalone_train.log"' in config
    assert '"metrics/*.csv"' in config
    assert '"_monitor/*.txt"' in config
    assert '"includeCheckpoints": false' in config
    assert "includePatterns" in script
    assert "Get-RemoteLogRootLeaf" in script
    assert "files_copied=$copied" in script
    assert "_last_sync.txt" in script
