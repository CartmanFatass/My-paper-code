from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "scripts" / "remote" / "run_hmasd_r27_g2_overnight.ps1"
AUTHORIZATION = "EXP-20260712-r27-g2-overnight-authorized"


def find_pwsh() -> str:
    for candidate in (
        shutil.which("pwsh"),
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        shutil.which("powershell"),
    ):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("PowerShell is required")


def find_bash() -> str:
    for candidate in (
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("Git Bash is required")


def write_harness(path: Path) -> None:
    path.write_text(
        r'''$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Record {
    param([string]$Tool, [object[]]$Arguments, [string]$Payload = "")
    $record = [ordered]@{
        tool = $Tool
        arguments = @($Arguments | ForEach-Object { [string]$_ })
        payload = $Payload
    }
    [System.IO.File]::AppendAllText(
        $env:R27_LOG,
        (($record | ConvertTo-Json -Compress -Depth 4) + "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )
}

function global:git {
    $global:LASTEXITCODE = 0
    $joined = (@($args | ForEach-Object { [string]$_ }) -join " ")
    if ($joined.Contains("branch --show-current")) { Write-Output "aggressive" }
    elseif ($joined.Contains("status --porcelain") -and $env:R27_DIRTY -eq "1") {
        Write-Output " M scripts/fixture.py"
    }
    elseif ($joined.Contains("rev-parse HEAD")) {
        Write-Output "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
    elseif ($joined.Contains("rev-parse FETCH_HEAD")) {
        if ($env:R27_SYNCED -eq "1") {
            Write-Output "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        } else {
            Write-Output "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        }
    }
}

function global:ssh {
    Write-Record -Tool "ssh" -Arguments @($args)
    $global:LASTEXITCODE = 0
    if ($env:R27_ACTION -eq "status") {
        Write-Output "state=running"
        Write-Output "phase=wiring_pilot_8"
        Write-Output "process_alive=1"
    }
}

function global:scp {
    $source = [string]$args[-2]
    $payload = if (Test-Path -LiteralPath $source) {
        [System.IO.File]::ReadAllText($source)
    } else { "" }
    Write-Record -Tool "scp" -Arguments @($args) -Payload $payload
    $global:LASTEXITCODE = 0
}

$common = @("-GitBranch", "aggressive")
switch ($env:R27_ACTION) {
    "dry-run" { & $env:R27_WORKFLOW -Action dry-run @common }
    "launch" {
        & $env:R27_WORKFLOW -Action launch @common `
            -LaunchAuthorization $env:R27_AUTHORIZATION
    }
    "status" { & $env:R27_WORKFLOW -Action status }
    default { throw "Unsupported action" }
}
''',
        encoding="utf-8",
    )


def run_harness(
    tmp_path: Path,
    *,
    action: str,
    authorization: str = "",
    dirty: bool = False,
    synced: bool = True,
) -> tuple[subprocess.CompletedProcess[str], list[dict[str, object]]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    harness = tmp_path / f"harness_{action}.ps1"
    log = tmp_path / f"log_{action}.jsonl"
    write_harness(harness)
    env = os.environ.copy()
    env.update(
        {
            "R27_WORKFLOW": str(WORKFLOW),
            "R27_ACTION": action,
            "R27_AUTHORIZATION": authorization,
            "R27_DIRTY": "1" if dirty else "0",
            "R27_SYNCED": "1" if synced else "0",
            "R27_LOG": str(log),
        }
    )
    result = subprocess.run(
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
    records = []
    if log.is_file():
        records = [
            json.loads(line)
            for line in log.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
    return result, records


def test_overnight_workflow_is_valid_powershell() -> None:
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


def test_chain_is_parallel_fail_closed_and_structured() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert '[string]$Action = "dry-run"' in source
    assert AUTHORIZATION in source
    assert "screen -DmS" in source
    assert "/root/autodl-tmp/HMASD" in source
    assert "current_overnight.env" in source
    assert "orchestration_status.env" in source
    assert "selected_workers=$SELECTED_WORKERS" in source
    assert "expected_wall_clock=$EXPECTED_WALL_CLOCK" in source
    assert "serial_fallback=forbidden" in source
    assert "workers_below_32=forbidden" in source
    assert "MAX_WORKERS=1" not in source
    assert "nohup" not in source
    assert '"watch"' in source


def test_dry_run_has_no_ssh_and_prints_full_branch(tmp_path: Path) -> None:
    result, records = run_harness(tmp_path, action="dry-run")
    assert result.returncode == 0, result.stdout + result.stderr
    assert records == []
    output = result.stdout + result.stderr
    assert "no SSH, screen, run directory, or experiment was started" in output
    assert "probe8 -> pilot8(WIRING_PASS) -> probe64" in output
    assert "RESOURCE_CAPACITY only: probe32" in output
    assert "decision_phase64=12-20h" in output
    assert "decision_phase32=24-40h" in output
    assert "full_chain64=15-26h" in output
    assert "full_chain32=28-46h" in output


def test_launch_gates_run_before_remote_access(tmp_path: Path) -> None:
    wrong, records = run_harness(
        tmp_path / "wrong", action="launch", authorization="wrong"
    )
    assert wrong.returncode != 0
    assert "Launch requires -LaunchAuthorization" in (wrong.stdout + wrong.stderr)
    assert records == []

    dirty, records = run_harness(
        tmp_path / "dirty",
        action="launch",
        authorization=AUTHORIZATION,
        dirty=True,
    )
    assert dirty.returncode != 0
    assert "clean Git worktree" in (dirty.stdout + dirty.stderr)
    assert records == []

    stale, records = run_harness(
        tmp_path / "stale",
        action="launch",
        authorization=AUTHORIZATION,
        synced=False,
    )
    assert stale.returncode != 0
    assert "not synchronized" in (stale.stdout + stale.stderr)
    assert records == []


def test_mock_launch_uploads_exact_fail_closed_chain_then_starts_screen(
    tmp_path: Path,
) -> None:
    result, records = run_harness(
        tmp_path, action="launch", authorization=AUTHORIZATION
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert [record["tool"] for record in records] == ["ssh", "scp", "ssh"]

    preflight = str(records[0]["arguments"][-1])
    assert "git pull --ff-only" in preflight
    assert "git rev-parse HEAD" in preflight
    assert "run_r27_g2_topology_probe_cloud.sh" in preflight
    assert "run_r27_g2_forced_trajectory_effect_pilot_cloud.sh" in preflight
    assert "standalone_process_core_final.pt" in preflight
    assert "hmasd_r27_g2_" in preflight
    assert "query-compute-apps=pid" in preflight
    assert 'test "$start_free_gpu_mib" -ge 22000' in preflight

    launcher = str(records[1]["payload"])
    launcher_path = tmp_path / "generated_overnight_controller.sh"
    launcher_path.write_text(launcher, encoding="utf-8", newline="\n")
    parsed = subprocess.run(
        [find_bash(), "-n", str(launcher_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stdout + parsed.stderr
    markers = [
        "run_phase topology_probe_8",
        "run_phase wiring_pilot_8",
        "run_phase topology_probe_64",
        "if ! probe_resource_failure",
        "run_phase topology_probe_32",
        "run_phase decision_grade",
    ]
    positions = [launcher.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "grep -Fxq 'state=WIRING_PASS'" in launcher
    assert 'report.get("failure_class") == "RESOURCE_CAPACITY"' in launcher
    assert "probe32_failed_no_lower_fallback" in launcher
    assert "SELECTED_WORKERS=64" in launcher
    assert "SELECTED_WORKERS=32" in launcher
    assert "EXPECTED_WALL_CLOCK=12-20h" in launcher
    assert "EXPECTED_WALL_CLOCK=24-40h" in launcher
    assert "R27_G2_CONCURRENCY_VALIDATED=1" in launcher
    assert "assert_gpu_idle" in launcher
    assert "PROBE_MIN_FREE_GPU_MIB=4096" in launcher
    assert "PROBE_MIN_FREE_HOST_MIB=8192" in launcher
    assert "validate-run --run-root" in launcher

    start = str(records[2]["arguments"][-1])
    assert "bash -n" in start
    assert "current_overnight.env" in start
    assert "overnight_launch.lock" in start
    assert "screen -DmS" in start


def test_status_is_read_only_and_reports_remote_state(tmp_path: Path) -> None:
    result, records = run_harness(tmp_path, action="status")
    assert result.returncode == 0, result.stdout + result.stderr
    assert [record["tool"] for record in records] == ["ssh"]
    output = result.stdout + result.stderr
    assert "state=running" in output
    assert "phase=wiring_pilot_8" in output
    command = str(records[0]["arguments"][-1])
    assert "tail -n 30" in command
    assert not any(token in command for token in ("rm -", "kill ", "screen -DmS"))
