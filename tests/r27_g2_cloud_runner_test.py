from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_r27_g2_forced_trajectory_effect_cloud_64env.sh"


def find_bash() -> str:
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("Git Bash is required for the R27-G2 cloud runner test")


def to_msys_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix().split(":", 1)[-1]
    return f"/{drive}{tail}"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    path.chmod(0o755)


def test_cloud_runner_dry_run_has_exact_contract_and_writes_nothing(tmp_path):
    run_root = tmp_path / "must-not-exist"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "MAX_WORKERS": "11",
            "RUN_ROOT": to_msys_path(run_root),
            "CHECKPOINT_DIST_ROOT": to_msys_path(tmp_path / "missing-dist"),
        }
    )

    result = subprocess.run(
        [find_bash(), str(RUNNER), "--dry-run"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert output.count("PHASE collect-reset checkpoint=") == 3 * 64
    assert output.count("scripts/audit_r27_forced_trajectory_effect.py collect-reset") == 3 * 64
    assert output.count("--reset-id") == 3 * 64
    assert output.count("--device cuda") == 3 * 64
    assert output.count("PHASE aggregate") == 1
    assert "--checkpoint-ids arm0_update25 arm0_update30 arm0_final" in output
    assert "cublas_workspace_config: :4096:8" in output
    assert "reset_worker_limit:      11" in output
    assert "environments_per_worker: 1" in output
    assert "standalone_process_core_update_25.pt" in output
    assert "standalone_process_core_update_30.pt" in output
    assert "standalone_process_core_final.pt" in output
    assert "no directories, commands, logs, or statuses were written" in output
    assert not run_root.exists()


@pytest.mark.parametrize(
    ("environment_update", "expected_error"),
    [
        ({"DEVICE": "cpu"}, "requires DEVICE=cuda"),
        ({"DEVICE": "cuda:0"}, "requires DEVICE=cuda"),
        ({"MAX_WORKERS": "0"}, "MAX_WORKERS must be an integer from 1 through 64"),
        ({"MAX_WORKERS": "65"}, "MAX_WORKERS must be an integer from 1 through 64"),
    ],
)
def test_cloud_runner_rejects_contract_changes_without_writing(
    tmp_path, environment_update, expected_error
):
    run_root = tmp_path / "must-not-exist"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "MAX_WORKERS": "8",
            "RUN_ROOT": to_msys_path(run_root),
        }
    )
    env.update(environment_update)

    result = subprocess.run(
        [find_bash(), str(RUNNER), "--dry-run"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert expected_error in result.stderr
    assert not run_root.exists()


def test_cloud_runner_resumes_only_failed_reset_then_aggregates(tmp_path):
    fixture_root = tmp_path / "fixture-repo"
    scripts_dir = fixture_root / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy2(RUNNER, scripts_dir / RUNNER.name)
    (scripts_dir / "audit_r27_forced_trajectory_effect.py").write_text(
        "# fixture audit entry point\n", encoding="utf-8"
    )

    checkpoint_dir = (
        fixture_root
        / "dist"
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

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_python = fake_bin / "python"
    write_executable(
        fake_python,
        """#!/usr/bin/env bash
set -eu
printf '%s\n' "$*" >> "$FAKE_CALL_LOG"
if [[ "${1:-}" == "-c" ]]; then
  exit 0
fi
command="${2:-}"
if [[ "$command" == "collect-reset" ]]; then
  output_dir=""
  while (( $# )); do
    if [[ "$1" == "--output-dir" ]]; then output_dir="$2"; break; fi
    shift
  done
  mkdir -p "$output_dir"
  printf '{}\n' > "$output_dir/reset_manifest.json"
  exit 0
fi
if [[ "$command" == "validate-reset" ]]; then
  printf '{"scientific_status": "OK", "valid": true}\n'
  exit 0
fi
if [[ "$command" == "aggregate" ]]; then
  run_root=""
  while (( $# )); do
    if [[ "$1" == "--run-root" ]]; then run_root="$2"; break; fi
    shift
  done
  printf '{"status": "FAIL", "classification": "FAIL_BEHAVIOR_FAMILY"}\n' > "$run_root/r27_g2_forced_trajectory_effect.json"
  printf '# fixture\n' > "$run_root/r27_g2_forced_trajectory_effect.md"
  exit 0
fi
if [[ "$command" == "validate-aggregate" ]]; then
  run_root=""
  while (( $# )); do
    if [[ "$1" == "--run-root" ]]; then run_root="$2"; break; fi
    shift
  done
  [[ -s "$run_root/r27_g2_forced_trajectory_effect.json" ]]
  [[ -s "$run_root/r27_g2_forced_trajectory_effect.md" ]]
  printf '{"classification": "FAIL_BEHAVIOR_FAMILY", "scientific_status": "FAIL", "valid": true}\n'
  exit 0
fi
exit 0
""",
    )
    run_root = fixture_root / "logs" / "resume-fixture"
    checkpoint_ids = ("arm0_update25", "arm0_update30", "arm0_final")
    for checkpoint_id in checkpoint_ids:
        for reset_id in range(64):
            reset_root = run_root / checkpoint_id / "resets" / f"reset_{reset_id:02d}"
            reset_root.mkdir(parents=True, exist_ok=True)
            state = "succeeded"
            (reset_root / "runner_status.txt").write_text(
                f"state={state}\n", encoding="utf-8"
            )
            if (checkpoint_id, reset_id) != ("arm0_update25", 7):
                (reset_root / "reset_manifest.json").write_text(
                    "{}\n", encoding="utf-8"
                )

    (run_root / "aggregate_status.txt").write_text(
        "state=succeeded\n", encoding="utf-8"
    )
    (run_root / "r27_g2_forced_trajectory_effect.json").write_text(
        '{"classification": "STALE"}\n', encoding="utf-8"
    )
    (run_root / "r27_g2_forced_trajectory_effect.md").write_text(
        "# stale aggregate\n", encoding="utf-8"
    )

    call_log = tmp_path / "fake-calls.txt"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "MAX_WORKERS": "3",
            "PYTHON_BIN": to_msys_path(fake_python),
            "CHECKPOINT_DIST_ROOT": to_msys_path(fixture_root / "dist"),
            "RUN_ROOT": to_msys_path(run_root),
            "FAKE_CALL_LOG": to_msys_path(call_log),
            "R27_G2_CONCURRENCY_VALIDATED": "1",
        }
    )

    result = subprocess.run(
        [find_bash(), to_msys_path(scripts_dir / RUNNER.name)],
        cwd=fixture_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    calls = call_log.read_text(encoding="utf-8").splitlines()
    collect_calls = [line for line in calls if " collect-reset " in f" {line} "]
    aggregate_calls = [line for line in calls if " aggregate " in f" {line} "]
    assert len(collect_calls) == 1
    assert "--checkpoint-id arm0_update25" in collect_calls[0]
    assert "--reset-id 7" in collect_calls[0]
    assert len(aggregate_calls) == 1
    assert "STALE" not in (
        run_root / "r27_g2_forced_trajectory_effect.json"
    ).read_text(encoding="utf-8")
    resumed_status = (
        run_root / "arm0_update25" / "resets" / "reset_07" / "runner_status.txt"
    ).read_text(encoding="utf-8")
    assert "state=succeeded" in resumed_status
    assert "exit_code=0" in resumed_status
    batch_status = (run_root / "batch_status.txt").read_text(encoding="utf-8")
    assert "state=succeeded" in batch_status
    assert "expected_reset_shards=192" in batch_status
    assert "failed_reset_shards=0" in batch_status
    assert "aggregate_state=succeeded" in batch_status
    assert "scientific_status=FAIL" in batch_status
    assert "classification=FAIL_BEHAVIOR_FAMILY" in batch_status


def test_cloud_runner_contains_no_training_or_reward_switches():
    source = RUNNER.read_text(encoding="utf-8")
    assert "CUBLAS_WORKSPACE_CONFIG=:4096:8" in source
    assert "--device cuda" in source
    assert "--train" not in source
    assert "--reward" not in source
    assert "--device cpu" not in source
    assert "seq 0 63" in source
    assert 'MAX_WORKERS="${MAX_WORKERS:-1}"' in source
    assert 'CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"' in source
    assert 'R27_G2_CONCURRENCY_VALIDATED="${R27_G2_CONCURRENCY_VALIDATED:-0}"' in source
    assert "validate-reset" in source
    assert "validate-aggregate" in source
    assert "trap 'on_signal INT' INT" in source
    assert "stopping after the current worker batch" in source
    assert '"environments_per_worker=1"' in source
