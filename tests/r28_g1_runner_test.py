from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_r28_g1_causal_skill_forcing_cloud.sh"


def _bash() -> str:
    for candidate in (
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("Git Bash is required for the R28-G1 runner test")


def _msys(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix().split(":", 1)[-1]
    return f"/{drive}{tail}"


def test_commands_mode_prints_exact_parallel_family_and_writes_nothing(tmp_path: Path):
    run_root = "/root/autodl-tmp/HMASD/logs/r28_g1_test_commands"
    env = os.environ.copy()
    env.update(
        {
            "REPO_DIR": _msys(ROOT),
            "DATA_ROOT": "/root/autodl-tmp/HMASD",
            "RUN_ROOT": run_root,
        }
    )
    result = subprocess.run(
        [_bash(), str(RUNNER), "commands"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    assert output.count("--r28_g1_arm") == 12
    assert output.count("--total_timesteps 1008000") == 3
    assert output.count("--total_timesteps 1160000") == 9
    assert output.count("--eval_action_mode deterministic") == 12
    assert output.count("scripts/collect_r26_g1_windows.py") == 9
    assert output.count("--r28_sidecar") == 9
    assert output.count("scripts/analyze_r26_g1_behavior.py") == 9
    assert output.count("scripts/analyze_r28_g1_family.py") == 1
    assert "--device cpu" not in output
    assert "No files, processes, topology checks, or experiments were started." in output
    assert not (tmp_path / "anything").exists()


def test_runner_is_data_disk_only_and_has_no_hash_layer() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert 'DATA_ROOT="${DATA_ROOT:-/root/autodl-tmp/HMASD}"' in source
    assert "RUN_ROOT must be a child of DATA_ROOT" in source
    assert "3 concurrent arms" in source
    assert "serial fallback is disabled" in source.lower()
    assert "sha256" not in source.lower()
    assert "checksum" not in source.lower()
    assert "state=waiting_for_launch_reinvoke" in source
    assert "topology_marker_existed" in source
    assert source.index("install_signal_traps\n    run_topology") > source.index(
        "require_topology_authorization\n    install_signal_traps"
    )
    assert "The first `all` invocation stops after a newly measured topology PASS" in source


@pytest.mark.parametrize(
    ("mode", "message"),
    (
        ("topology", "Topology execution requires R28_G1_TOPOLOGY_AUTHORIZATION"),
        ("run", "Experiment execution requires R28_G1_LAUNCH_AUTHORIZATION"),
    ),
)
def test_execution_modes_require_separate_authorization_before_writes(
    tmp_path: Path, mode: str, message: str
) -> None:
    data_root_path = tmp_path / "data"
    data_root = _msys(data_root_path)
    run_root = f"{data_root}/logs/r28_g1_unauthorized_test"
    env = os.environ.copy()
    env.update(
        {
            "REPO_DIR": _msys(ROOT),
            "DATA_ROOT": data_root,
            "RUN_ROOT": run_root,
        }
    )
    result = subprocess.run(
        [_bash(), str(RUNNER), mode],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert message in result.stderr
    assert not data_root_path.exists()
