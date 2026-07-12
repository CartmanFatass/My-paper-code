from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_r27_g1_capacity_autopsy_cloud_64env.sh"


def find_bash() -> str:
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise RuntimeError("Git Bash is required for the R27 cloud runner test")


def to_msys_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix().split(":", 1)[-1]
    return f"/{drive}{tail}"


def test_cloud_runner_dry_run_is_exact_64_env_3_plus_1_plus_1(tmp_path):
    run_root = tmp_path / "dry-run-output"
    env = os.environ.copy()
    env.update(
        {
            "PYTHON_BIN": "python",
            "DEVICE": "cuda",
            "NUM_ENVS": "64",
            "N_RESETS": "64",
            "RUN_ROOT": str(run_root),
            "CHECKPOINT_DIST_ROOT": str(tmp_path / "missing-dist"),
        }
    )

    result = subprocess.run(
        [find_bash(), "scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh", "--dry-run"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert output.count("PHASE collect-static") == 3
    assert output.count("PHASE synthetic") == 1
    assert output.count("PHASE aggregate") == 1
    assert output.count("scripts/audit_r27_low_actor_capacity.py collect-static") == 3
    assert "--device cuda" in output
    assert output.count("--num-envs 64") == 3
    assert output.count("--n-resets 64") == 3
    assert output.count("--collector-backend subproc") == 3
    assert output.count("--collector-start-method spawn") == 3
    assert not run_root.exists()


def test_cloud_runner_marks_failed_collect_arm_terminal(tmp_path):
    dist_root = tmp_path / "dist"
    checkpoint_dir = (
        dist_root
        / "logs_cloud_r25_qa_verification_1m"
        / "arm0_arch_only"
        / "seed1"
    )
    checkpoint_dir.mkdir(parents=True)
    for filename in (
        "standalone_process_core_update_25.pt",
        "standalone_process_core_update_30.pt",
        "standalone_process_core_final.pt",
    ):
        (checkpoint_dir / filename).write_bytes(b"fixture")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_sha = fake_bin / "sha256sum"
    fake_sha.write_text(
        """#!/usr/bin/env bash
case "$1" in
  *update_25.pt) hash=3f6404cd54e75f3f39af0cffb56c444dda78acd05993f1b6efd9cdc77ad9ca54 ;;
  *update_30.pt) hash=6553e97c032e54f0a19cf801e451298d6b56232720d82a8e26abbdb7171acabc ;;
  *final.pt) hash=eeaa4f7ec32314d47be818f20c76758c47a97b7881aa997511a2660bb5632c36 ;;
esac
printf '%s  %s\\n' "$hash" "$1"
""",
        encoding="utf-8",
    )
    fake_sha.chmod(0o755)
    run_root = tmp_path / "failed-run"
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{to_msys_path(fake_bin)}:/usr/bin:/bin",
            "SHA256_BIN": to_msys_path(fake_sha),
            "PYTHON_BIN": find_bash(),
            "DEVICE": "cuda",
            "NUM_ENVS": "64",
            "N_RESETS": "64",
            "RUN_ROOT": to_msys_path(run_root),
            "CHECKPOINT_DIST_ROOT": to_msys_path(dist_root),
        }
    )

    result = subprocess.run(
        [find_bash(), "scripts/run_r27_g1_capacity_autopsy_cloud_64env.sh"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert run_root.is_dir(), f"stdout={result.stdout}\nstderr={result.stderr}"
    arm_status = (run_root / "arm0_update25" / "runner_status.txt").read_text(
        encoding="utf-8"
    )
    assert "state=failed" in arm_status
    assert "phase=collect-static" in arm_status
