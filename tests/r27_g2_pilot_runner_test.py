from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_r27_g2_forced_trajectory_effect_pilot_cloud.sh"


def find_bash() -> str:
    for candidate in (
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    pytest.skip("Git Bash is unavailable")


def to_msys_path(path: Path) -> str:
    value = path.resolve().as_posix()
    if len(value) >= 3 and value[1:3] == ":/":
        return f"/{value[0].lower()}/{value[3:]}"
    return value


def test_pilot_dry_run_is_exact_eight_reset_final_checkpoint_matrix(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "must-not-exist"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "MAX_WORKERS": "8",
            "RUN_ROOT": to_msys_path(run_root),
            "CHECKPOINT_DIST_ROOT": to_msys_path(tmp_path / "missing"),
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

    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout
    assert output.count("PHASE pilot-collect-reset checkpoint=arm0_final") == 8
    assert output.count("audit_r27_forced_trajectory_effect.py collect-reset") == 8
    assert output.count("--checkpoint-id arm0_final") == 8
    assert output.count("--checkpoint-update 32") == 8
    assert output.count("--reset-id") == 8
    for reset_id in range(8):
        assert f"reset_id={reset_id}" in output
    assert "arm0_update25" not in output
    assert "arm0_update30" not in output
    assert " aggregate " not in f" {output} "
    assert "pilot-summary" in output
    assert "environment_steps:       83600" in output
    assert "expected_wall_clock:     3-5h rough queue estimate" in output
    assert "scientific_gate:         NOT_EVALUATED" in output
    assert not run_root.exists()


@pytest.mark.parametrize(
    ("updates", "error"),
    [
        ({"DEVICE": "cpu"}, "requires DEVICE=cuda"),
        ({"MAX_WORKERS": "0"}, "integer from 1 through 8"),
        ({"MAX_WORKERS": "9"}, "integer from 1 through 8"),
    ],
)
def test_pilot_dry_run_rejects_contract_changes_without_writing(
    tmp_path: Path, updates: dict[str, str], error: str
) -> None:
    run_root = tmp_path / "must-not-exist"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "MAX_WORKERS": "8",
            "RUN_ROOT": to_msys_path(run_root),
        }
    )
    env.update(updates)

    result = subprocess.run(
        [find_bash(), str(RUNNER), "--dry-run"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert error in result.stderr
    assert not run_root.exists()


@pytest.mark.parametrize(
    ("updates", "error"),
    [
        (
            {"MAX_WORKERS": "1", "R27_G2_CONCURRENCY_VALIDATED": "1"},
            "Serial R27-G2 pilot launch is disabled",
        ),
        (
            {"MAX_WORKERS": "8", "R27_G2_CONCURRENCY_VALIDATED": "0"},
            "requires R27_G2_CONCURRENCY_VALIDATED=1",
        ),
    ],
)
def test_pilot_launch_rejects_serial_or_unvalidated_before_writing(
    tmp_path: Path, updates: dict[str, str], error: str
) -> None:
    run_root = tmp_path / "must-not-exist"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "RUN_ROOT": to_msys_path(run_root),
        }
    )
    env.update(updates)

    result = subprocess.run(
        [find_bash(), str(RUNNER)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert error in result.stderr
    assert not run_root.exists()


def write_fake_python(path: Path) -> None:
    path.write_text(
        r'''#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$FAKE_CALL_LOG"
if [[ "$1" == "-c" ]]; then
  exit 0
fi
script="$1"
shift
if [[ "$script" == *"r27_g2_pilot_summary.py" ]]; then
  run_root=""
  while (( $# > 0 )); do
    if [[ "$1" == "--run-root" ]]; then run_root="$2"; shift 2; else shift; fi
  done
  printf '%s\n' \
    'state=WIRING_PASS' \
    'scientific_status=NOT_EVALUATED' \
    'eligible_for_scientific_gate=false' \
    'expected_resets=8' \
    'validated_resets=8' \
    'environment_steps=83600' \
    > "$run_root/pilot_status.txt"
  printf '%s\n' '{"state":"WIRING_PASS","scientific_status":"NOT_EVALUATED","eligible_for_scientific_gate":false}' > "$run_root/pilot_summary.json"
  exit 0
fi
command="$1"
shift
if [[ "$command" == "collect-reset" ]]; then
  output_dir=""
  reset_id=""
  while (( $# > 0 )); do
    case "$1" in
      --output-dir) output_dir="$2"; shift 2 ;;
      --reset-id) reset_id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  mkdir -p "$output_dir"
  printf 'fixture\n' > "$output_dir/reset_$(printf '%04d' "$reset_id").npz"
  printf '%s\n' '{"status":"OK"}' > "$output_dir/reset_manifest.json"
  exit 0
fi
if [[ "$command" == "validate-reset" ]]; then
  printf '%s\n' '{"valid": true, "scientific_status": "OK"}'
  exit 0
fi
exit 2
''',
        encoding="utf-8",
        newline="\n",
    )
    path.chmod(0o755)


def test_pilot_runner_writes_fail_closed_success_interface(tmp_path: Path) -> None:
    run_root = tmp_path / "pilot-run"
    checkpoint_root = tmp_path / "checkpoint-dist"
    checkpoint = (
        checkpoint_root
        / "logs_cloud_r25_qa_verification_1m"
        / "arm0_arch_only"
        / "seed1"
        / "standalone_process_core_final.pt"
    )
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"fixture checkpoint")
    fake_python = tmp_path / "fake_python.sh"
    write_fake_python(fake_python)
    call_log = tmp_path / "calls.log"
    env = os.environ.copy()
    env.update(
        {
            "DEVICE": "cuda",
            "MAX_WORKERS": "8",
            "R27_G2_CONCURRENCY_VALIDATED": "1",
            "RUN_ROOT": to_msys_path(run_root),
            "CHECKPOINT_DIST_ROOT": to_msys_path(checkpoint_root),
            "PYTHON_BIN": to_msys_path(fake_python),
            "FAKE_CALL_LOG": to_msys_path(call_log),
        }
    )

    result = subprocess.run(
        [find_bash(), str(RUNNER)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    calls = call_log.read_text(encoding="utf-8").splitlines()
    assert sum(" collect-reset " in f" {call} " for call in calls) == 8
    assert sum(" validate-reset " in f" {call} " for call in calls) == 8
    assert sum("r27_g2_pilot_summary.py" in call for call in calls) == 1
    status = (run_root / "pilot_status.txt").read_text(encoding="utf-8")
    assert "state=WIRING_PASS\n" in status
    assert "scientific_status=NOT_EVALUATED\n" in status
    assert "eligible_for_scientific_gate=false\n" in status
    batch = (run_root / "batch_status.txt").read_text(encoding="utf-8")
    assert "state=succeeded\n" in batch
    assert "pilot_state=WIRING_PASS\n" in batch
    assert "environment_steps=83600\n" in batch
    assert (run_root / "pilot_contract.json").is_file()
    assert (run_root / "pilot_summary.json").is_file()
    for reset_id in range(8):
        output_dir = run_root / "arm0_final" / "resets" / f"reset_{reset_id:02d}"
        assert (output_dir / "command.txt").is_file()
        assert (output_dir / "runner_output.log").is_file()
        assert (output_dir / "validation_output.log").is_file()
