from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "scripts" / "r27_g2_pilot_summary.py"
PREFIX_STEPS = (50, 150, 250, 50, 150, 250, 50, 150)


def write_fake_audit(path: Path) -> None:
    path.write_text(
        "from __future__ import annotations\n"
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p=argparse.ArgumentParser(); p.add_argument('command'); "
        "p.add_argument('--manifest'); p.add_argument('--checkpoint-id'); "
        "p.add_argument('--reset-id'); a=p.parse_args()\n"
        "m=json.loads(Path(a.manifest).read_text(encoding='utf-8'))\n"
        "print(json.dumps({'valid': True, 'scientific_status': m['status'], "
        "'checkpoint_id': a.checkpoint_id, 'reset_id': int(a.reset_id)}))\n",
        encoding="utf-8",
    )


def write_fixture(run_root: Path, statuses: dict[int, str] | None = None) -> None:
    statuses = statuses or {}
    run_root.mkdir(parents=True, exist_ok=True)
    pilot_contract = {
        "experiment_id": "EXP-20260712-r27-g2-forced-z-trajectory-effect",
        "run_kind": "wiring_pilot",
        "scientific_status": "NOT_EVALUATED",
        "eligible_for_scientific_gate": False,
        "checkpoint_ids": ["arm0_final"],
        "checkpoint_update": 32,
        "reset_ids": list(range(8)),
        "reset_seeds": list(range(1, 9)),
        "prefix_policy_seeds": list(range(27100, 27108)),
        "prefix_steps": list(PREFIX_STEPS),
        "branches_per_reset": 55,
        "branch_steps": 50,
        "environment_steps": 83600,
    }
    (run_root / "pilot_contract.json").write_text(
        json.dumps(pilot_contract), encoding="utf-8"
    )
    for reset_id, prefix_steps in enumerate(PREFIX_STEPS):
        output_dir = run_root / "arm0_final" / "resets" / f"reset_{reset_id:02d}"
        output_dir.mkdir(parents=True)
        status = statuses.get(reset_id, "OK")
        (output_dir / "runner_status.txt").write_text(
            f"state=succeeded\nscientific_status={status}\n",
            encoding="utf-8",
        )
        artifact_name = f"reset_{reset_id:04d}.npz"
        (output_dir / artifact_name).write_bytes(b"pilot fixture")
        environment_steps = prefix_steps + 55 * (prefix_steps + 50)
        manifest = {
            "experiment_id": "EXP-20260712-r27-g2-forced-z-trajectory-effect",
            "status": status,
            "invalid_reasons": ["fixture invalid"] if status == "INVALID" else [],
            "excluded_reason": "fixture exclusion" if status == "EXCLUDED" else None,
            "reset_id": reset_id,
            "reset_seed": reset_id + 1,
            "prefix_policy_seed": 27100 + reset_id,
            "prefix_steps": prefix_steps,
            "checkpoint_id": "arm0_final",
            "checkpoint_update": 32,
            "checkpoint_path": "/data/standalone_process_core_final.pt",
            "checkpoint_file_nonempty": True,
            "device": "cuda",
            "branch_count": 55,
            "branch_steps": 50,
            "environment_steps": environment_steps,
            "calibration_complete": True,
            "module_state_equal": True,
            "value_norm_state_equal": True,
            "loaded_value_norm_equal": True,
            "reference_act_low_parity_complete": status == "OK",
            "reference_act_low_parity_max_abs_error": 0.0,
            "artifact": artifact_name,
        }
        (output_dir / "reset_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )


def run_summary(run_root: Path, audit_script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SUMMARY),
            "--run-root",
            str(run_root),
            "--audit-script",
            str(audit_script),
            "--python-bin",
            sys.executable,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_summary_writes_exact_quarantined_wiring_pass_contract(tmp_path: Path) -> None:
    run_root = tmp_path / "pilot"
    audit_script = tmp_path / "fake_audit.py"
    write_fake_audit(audit_script)
    write_fixture(run_root)

    result = run_summary(run_root, audit_script)

    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((run_root / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["state"] == "WIRING_PASS"
    assert summary["scientific_status"] == "NOT_EVALUATED"
    assert summary["eligible_for_scientific_gate"] is False
    assert summary["checkpoint_id"] == "arm0_final"
    assert summary["reset_ids"] == list(range(8))
    assert summary["prefix_steps"] == list(PREFIX_STEPS)
    assert summary["validated_resets"] == 8
    assert summary["environment_steps_observed"] == 83600
    assert summary["gate_a"] == summary["gate_b"] == summary["gate_c"] == "NOT_RUN"
    status = (run_root / "pilot_status.txt").read_text(encoding="utf-8")
    assert "state=WIRING_PASS\n" in status
    assert "scientific_status=NOT_EVALUATED\n" in status
    assert "eligible_for_scientific_gate=false\n" in status
    assert "environment_steps=83600\n" in status


@pytest.mark.parametrize(
    ("status", "expected_state", "expected_exit"),
    [
        ("EXCLUDED", "INCOMPLETE", 3),
        ("INVALID", "INVALID", 4),
    ],
)
def test_summary_fail_closed_nonpass_states(
    tmp_path: Path, status: str, expected_state: str, expected_exit: int
) -> None:
    run_root = tmp_path / "pilot"
    audit_script = tmp_path / "fake_audit.py"
    write_fake_audit(audit_script)
    write_fixture(run_root, {3: status})

    result = run_summary(run_root, audit_script)

    assert result.returncode == expected_exit
    summary = json.loads((run_root / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["state"] == expected_state
    assert summary["scientific_status"] == "NOT_EVALUATED"
    assert summary["eligible_for_scientific_gate"] is False
    assert f"state={expected_state}\n" in (
        run_root / "pilot_status.txt"
    ).read_text(encoding="utf-8")


def test_summary_classifies_failed_worker_as_crash(tmp_path: Path) -> None:
    run_root = tmp_path / "pilot"
    audit_script = tmp_path / "fake_audit.py"
    write_fake_audit(audit_script)
    write_fixture(run_root)
    failed = run_root / "arm0_final" / "resets" / "reset_05" / "runner_status.txt"
    failed.write_text(
        "state=failed\nreason=collect_command_failed\n", encoding="utf-8"
    )

    result = run_summary(run_root, audit_script)

    assert result.returncode == 5
    summary = json.loads((run_root / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["state"] == "crash"
    assert "state=crash\n" in (run_root / "pilot_status.txt").read_text(
        encoding="utf-8"
    )


def test_summary_classifies_output_validation_failure_as_invalid(tmp_path: Path) -> None:
    run_root = tmp_path / "pilot"
    audit_script = tmp_path / "fake_audit.py"
    write_fake_audit(audit_script)
    write_fixture(run_root)
    failed = run_root / "arm0_final" / "resets" / "reset_02" / "runner_status.txt"
    failed.write_text(
        "state=failed\nreason=output_validation_failed\n", encoding="utf-8"
    )

    result = run_summary(run_root, audit_script)

    assert result.returncode == 4
    summary = json.loads((run_root / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["state"] == "INVALID"


def test_summary_rejects_extra_reset_inventory(tmp_path: Path) -> None:
    run_root = tmp_path / "pilot"
    audit_script = tmp_path / "fake_audit.py"
    write_fake_audit(audit_script)
    write_fixture(run_root)
    extra = run_root / "arm0_final" / "resets" / "reset_08"
    extra.mkdir(parents=True)
    (extra / "reset_manifest.json").write_text("{}", encoding="utf-8")

    result = run_summary(run_root, audit_script)

    assert result.returncode == 4
    summary = json.loads((run_root / "pilot_summary.json").read_text(encoding="utf-8"))
    assert summary["state"] == "INVALID"
    assert any("inventory" in issue for issue in summary["issues"])
