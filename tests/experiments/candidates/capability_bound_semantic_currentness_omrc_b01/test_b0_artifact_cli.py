from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b0
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.telemetry import (
    ResourceCaps,
    TelemetryError,
)
from scripts import run_cbsc_omrc_b01 as cli


def test_b0_plan_freezes_seed_split_updates_and_has_no_science_branch() -> None:
    plan = b0.B0Plan()
    assert plan.seed == 21001
    assert plan.arms == b0.ARMS and len(plan.arms) == 4
    assert plan.train_episode_ids == tuple(range(8))
    assert plan.eval_stochastic_ids == (0, 1, 2, 3)
    assert plan.eval_motif_ids == (0, 12, 20, 28)
    assert plan.rollout_updates == 1 and plan.optimizer_steps_per_arm == 16
    assert plan.scientific_branch is None


def test_formal_run_has_no_engine_preflight_monitor_source_or_root_injection() -> None:
    assert tuple(inspect.signature(b0.run_b0).parameters) == (
        "final_path", "implementation_commit", "run_name",
    )
    with pytest.raises(TypeError):
        b0.run_b0(  # type: ignore[call-arg]
            engine=object(), final_path=Path("unused"), implementation_commit="a" * 40
        )


def test_canonical_source_surface_includes_worker_cli_and_shared_preflight() -> None:
    surface = set(b0.CANONICAL_SOURCE_SURFACE)
    assert "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/worker.py" in surface
    assert "scripts/run_cbsc_omrc_b01.py" in surface
    assert "scripts/hmasd_resource_preflight.py" in surface
    identity = b0._canonical_engine_identity()
    assert identity["module"] == b0.CANONICAL_ENGINE_MODULE
    assert identity["factory"] == "b0_engine"
    assert identity["type"] == "LiteralB0Engine"
    assert identity["factory_file"] == identity["type_file"]


def _bound_admission(attempt: str, arm: str, commit: str) -> dict:
    executable = Path(sys.executable).resolve()
    bound = Path("C:/opaque/inside-attempt/admission.json")
    raw = bound.with_name(".admission.json.raw-fixture.json")
    return {
        "schema": b0.BOUND_ADMISSION_SCHEMA,
        "attempt_id": attempt,
        "arm": arm,
        "implementation_commit": commit,
        "source_conformance_sha256": "1" * 64,
        "bound_receipt_path": str(bound),
        "raw_output_path": str(raw),
        "python_executable": str(executable),
        "python_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "preflight_script": str(b0.CANONICAL_PREFLIGHT),
        "preflight_script_sha256": hashlib.sha256(b0.CANONICAL_PREFLIGHT.read_bytes()).hexdigest(),
        "exact_command": [str(executable), str(b0.CANONICAL_PREFLIGHT), "admit-memory", "--out", str(raw)],
        "raw_receipt_sha256": "2" * 64,
        "receipt": {
            "passed": True,
            "physical_floor_pass": True,
            "effective_floor_pass": True,
            "available_physical_bytes": 5 * 1024**3,
            "effective_available_bytes": 4 * 1024**3,
        },
    }


def test_bound_admission_locks_attempt_arm_command_python_script_and_commit() -> None:
    value = _bound_admission("attempt-1", b0.ARMS[0], "a" * 40)
    assert b0.validate_bound_admission(
        value, expected_attempt_id="attempt-1", expected_arm=b0.ARMS[0],
        expected_commit="a" * 40,
    )["receipt"]["passed"] is True
    for field, changed in (
        ("attempt_id", "attempt-2"), ("arm", b0.ARMS[1]),
        ("implementation_commit", "b" * 40), ("preflight_script_sha256", "3" * 64),
    ):
        tampered = dict(value); tampered[field] = changed
        with pytest.raises(b0.B0ContractError):
            b0.validate_bound_admission(
                tampered, expected_attempt_id="attempt-1", expected_arm=b0.ARMS[0],
                expected_commit="a" * 40,
            )


def test_parent_supervision_terminates_child_on_live_wall_cap(tmp_path) -> None:
    result = tmp_path / "result.json"
    with pytest.raises(TelemetryError, match="live resource cap exceeded: wall_seconds"):
        b0.supervise_child(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            scratch_root=tmp_path / "scratch", durable_root=tmp_path,
            result_path=result, stdout_path=tmp_path / "stdout.log",
            stderr_path=tmp_path / "stderr.log",
            caps=ResourceCaps(wall_seconds=0.15), interval_seconds=0.02,
        )
    assert not result.exists()
    incident = json.loads(
        (tmp_path / "supervisor-incident.json").read_text(encoding="utf-8")
    )
    assert incident["reason"] == "LIVE_RESOURCE_CAP_TERMINATION"
    assert incident["cap_failures"] == ["wall_seconds"]
    assert incident["process_tree_peak_rss_bytes"] > 0


def test_parent_supervision_reads_create_only_worker_result_and_measures_child(tmp_path) -> None:
    result = tmp_path / "result.json"
    stage = {"stage": "fixture", "wall_seconds": 0.2, "cpu_seconds": 0.1,
             "transitions": 2432, "transitions_per_second": 12160.0}
    payload = {"stage_measurements": [stage], "test_only": True}
    code = (
        "import json,time,pathlib\nend=time.perf_counter()+0.35\nx=0\n"
        "while time.perf_counter()<end: x+=1\n"
        f"pathlib.Path({str(result)!r}).write_text(json.dumps({payload!r}))"
    )
    raw, telemetry = b0.supervise_child(
        [sys.executable, "-c", code], scratch_root=tmp_path / "scratch",
        durable_root=tmp_path, result_path=result, stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log", interval_seconds=0.02,
    )
    assert raw["test_only"] is True
    assert telemetry["process_tree_peak_rss_bytes"] > 0
    assert telemetry["end_to_end_cpu_seconds"] > 0
    assert telemetry["sample_count"] >= 2


def test_independent_audit_refuses_engine_claims_without_raw_action_evidence(tmp_path) -> None:
    raw = {
        "arm": b0.ARMS[0],
        "audits": {name: True for name in b0.REQUIRED_AUDITS},
        "digests": {name: "0" * 64 for name in (*b0.COMMON_DIGESTS, "adapter_law", "checkpoint_bytes", "adapter_work")},
        "records": {"evaluation_actions": [["SERVE"] * 24 for _ in range(8)]},
    }
    with pytest.raises(b0.B0ContractError, match="identity|training_actions"):
        b0.recompute_arm_evidence(raw, expected_arm=b0.ARMS[0], arm_root=tmp_path)


def test_cli_uses_only_canonical_engine_and_preflight_options(capsys) -> None:
    assert cli.main(["readiness"]) == 4
    document = json.loads(capsys.readouterr().out)
    assert document["engine_bound"] is True
    assert document["engine_contract"] == "CANONICAL_FIXED_FACTORY_ONLY"
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["readiness", "--engine", "evil:factory"])
    with pytest.raises(SystemExit):
        cli._parser().parse_args([
            "run-b0", "--output", "x", "--implementation-commit", "a" * 40,
            "--preflight-script", "evil.py",
        ])


def test_formal_run_blocks_uncommitted_surface_before_admission_or_output() -> None:
    destination = b0.CONFINED_ROOT / "test-only-must-not-appear"
    assert not destination.exists()
    with pytest.raises(b0.B0ContractError, match="BLOCKED_UNCOMMITTED"):
        b0.run_b0(final_path=destination, implementation_commit="e" * 40)
    assert not destination.exists()


def test_direct_script_launcher_resolves_repository_imports() -> None:
    script = Path(__file__).resolve().parents[4] / "scripts" / "run_cbsc_omrc_b01.py"
    completed = subprocess.run(
        [sys.executable, str(script), "readiness"], cwd=script.parent.parent,
        capture_output=True, text=True, shell=False, timeout=60,
    )
    assert completed.returncode == 4
    document = json.loads(completed.stdout)
    assert document["engine_bound"] is True
    assert document["run_b0_authorized"] is False
