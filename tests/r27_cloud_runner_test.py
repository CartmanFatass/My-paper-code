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
