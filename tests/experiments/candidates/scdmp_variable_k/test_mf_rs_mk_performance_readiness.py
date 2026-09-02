from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    performance_readiness as readiness,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import contracts
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    source_identity as source_identity_module,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.runner import (
    RUN_CONFIRMATION, ResultExecutionDisabled, run_result,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import runner as runner_module
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.native_backend import (
    NativeBackendError,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.resources import (
    ResourceTelemetry,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.preflight import (
    PreflightError,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.active_gate import (
    ActiveInvocationGate,
)


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _synthetic_a(tmp_path: Path, monkeypatch):
    root = (tmp_path / "A-R2").resolve()
    root.mkdir()
    source = {"schema": "TEST_SOURCE", "owned_source_inventory": [], "native": "bound"}
    source_bytes = _canonical(source)
    monkeypatch.setattr(readiness, "compute_source_identity_bytes", lambda: source_bytes)
    (root / "source-identity.json").write_bytes(source_bytes)
    manifest = {
        "schema": readiness.ASSESS_SCHEMA,
        "assessment_id": readiness.ASSESS_ID,
        "resolved_assess_root": str(root),
        "resource_caps": {
            "peak_rss_bytes": 2 * 1024**3, "scratch_bytes": 256 * 1024**2,
            "durable_bytes": 256 * 1024**2, "wall_seconds": 1800.0,
        },
    }
    (root / "manifest.json").write_bytes(_canonical(manifest))
    projection = {
        "conservative_projected_total_seconds": 1200.0,
        "margin_to_1800_seconds": 600.0,
        "projected_work_seconds": 1140.0,
        "fixed_overhead_seconds": 60.0,
        "formula": "synthetic-test",
        "assumptions": ["test artifact"],
    }
    assessment = {
        "schema": readiness.ASSESS_SCHEMA,
        "assessment_id": readiness.ASSESS_ID,
        "status": "PERFORMANCE_OBSERVATION_COMPLETE",
        "performance_readiness": "REVIEW_REQUIRED",
        "projection": projection,
        "telemetry_file": "telemetry.json",
        "scientific_polarity": None,
        "ordered_branch": None,
    }
    measured = ResourceTelemetry(
        True, (), 5, 1024, 2048, 4096, 10.0, 5.0, 0.5, 1, 2,
        5 * 1024**3, 5 * 1024**3, 0,
    )
    accounting = {}
    for _ in range(12):
        assessment["final_tail_accounting"] = accounting
        telemetry = {
            "schema": "SCDMP_MF_RS_MK_B01_A_RESOURCE_V1",
            "telemetry": asdict(measured),
            "final_tail_accounting": accounting,
        }
        telemetry_bytes = _canonical(telemetry)
        assessment_bytes = _canonical(assessment)
        next_accounting = {
            "prepublication_durable_bytes": 1000,
            "telemetry_exact_bytes": len(telemetry_bytes),
            "assessment_exact_bytes": len(assessment_bytes),
            "exact_tail_bytes": len(telemetry_bytes) + len(assessment_bytes),
            "predicted_final_durable_bytes": 1000 + len(telemetry_bytes) + len(assessment_bytes),
            "durable_cap_bytes": 256 * 1024**2,
        }
        if next_accounting == accounting:
            break
        accounting = next_accounting
    (root / "telemetry.json").write_bytes(telemetry_bytes)
    (root / "assessment.json").write_bytes(assessment_bytes)
    inventory = []
    checkpoint_root = root / "technical-checkpoints"
    for seed in (1709, 2903):
        for coordinate in range(161):
            path = checkpoint_root / str(seed) / f"coordinate-{coordinate:03d}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_canonical({"seed": seed, "coordinate": coordinate}))
            inventory.append({
                "relative_path": path.relative_to(checkpoint_root).as_posix(),
                "direct_size_bytes": path.stat().st_size,
            })
    preview = {
        "schema": readiness.ASSESS_SCHEMA,
        "source_identity_file": "source-identity.json",
        "checkpoint_files": 322,
        "checkpoint_direct_bytes": sum(row["direct_size_bytes"] for row in inventory),
        "inventory": inventory,
        "scientific_polarity": None,
        "ordered_branch": None,
    }
    (root / "technical-publication-preview.json").write_bytes(_canonical(preview))
    review = {
        "schema": readiness.REVIEW_SCHEMA,
        "review_disposition": "CLEAN",
        "review_evidence_id": "review-test-001",
        "reviewer_identity": "cm-reviewer-test",
        "assessment_id": readiness.ASSESS_ID,
        "assessment_root": str(root),
        "scientific_polarity": None,
    }
    review_path = tmp_path / "review.json"
    review_path.write_bytes(_canonical(review))
    receipt = tmp_path / "performance-ready.json"
    readiness.create_performance_readiness_receipt(
        assessment_root=root, review_evidence=review_path, output=receipt,
    )
    return root, review_path, receipt, source_bytes


def _assert_active_gate_is_free(root: Path) -> None:
    """The launch now acquires and releases the active gate before admission.

    Before the section 11 recast the receipt refusal happened first, so no gate
    existed at all.  The gate coordinate is an OS byte-range lease whose file
    survives release, so the check is that nothing still holds it.
    """

    gate = ActiveInvocationGate(root, mode="RUN-01")
    gate.acquire()
    gate.release()


def test_missing_receipt_is_recorded_and_no_longer_refuses_the_launch(tmp_path) -> None:
    """Section 11 recast (2026-09-02, owner decision 1).

    Before the recast an absent `PERFORMANCE_READY` receipt raised
    `ResultExecutionDisabled` at `runner.py:606-611`.  Evidence spec §11.4 does
    not allow that capacity gate to hold a B launch, so the absence is now a
    recorded field and the launch continues to the mandatory resource
    admission, which remains a launch condition.
    """

    recorded = runner_module.performance_assessment_record(
        performance_readiness=None, performance_assessment=None,
    )
    assert recorded["gating"] is False
    assert recorded["readiness_receipt_status"] is None
    assert recorded["readiness_receipt_note"] == "not_supplied"

    calls = []
    root = tmp_path / contracts.ATTEMPT_ID
    # The admission is the next thing that runs, and it still refuses: the run
    # stops on the 4 GiB admission, not on the demoted receipt.
    with pytest.raises(PreflightError):
        run_result(
            result_root=root, admission_receipt=tmp_path / "admit.json",
            confirmation=RUN_CONFIRMATION, argv=("python", "runner.py", "--run-01"),
            cwd=tmp_path, command_runner=lambda *args, **kwargs: calls.append((args, kwargs)),
            performance_readiness=None,
        )
    assert len(calls) == 1
    assert not root.exists()
    _assert_active_gate_is_free(root)


def test_readiness_gate_source_is_inside_source_identity_and_byte_change_mismatches(monkeypatch) -> None:
    relative = (
        "experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/"
        "performance_readiness.py"
    )
    assert relative in source_identity_module.OWNED_PRODUCTION_PATHS
    persisted = _canonical({
        "schema": "TEST", "owned_source_inventory": [
            {"relative_path": relative, "byte_size": 10, "sha256": "a" * 64},
        ],
    })
    changed = json.loads(persisted)
    changed["owned_source_inventory"][0]["sha256"] = "b" * 64
    with pytest.raises(source_identity_module.SourceIdentityError, match="differs"):
        source_identity_module.validate_source_identity_bytes(persisted, _canonical(changed))


def test_cli_no_longer_refuses_a_missing_or_invalid_readiness_receipt(tmp_path) -> None:
    """Section 11 recast: the CLI records the receipt instead of refusing on it.

    Both invocations below still stop at exit 2, but on the canonical
    result-root name, which is not a demoted gate.  The pre-recast
    `parser.error("--run-01 requires --performance-readiness")` and the
    `invalid --performance-readiness` refusal are gone.
    """

    root = tmp_path / "cli-run"
    completed = subprocess.run([
        sys.executable, "scripts/run_scdmp_mf_rs_mk_b01.py", "--run-01",
        "--receipt", str(tmp_path / "admit.json"), "--result-root", str(root),
        "--confirm-run-id", RUN_CONFIRMATION,
    ], cwd=Path.cwd(), capture_output=True, text=True)
    assert completed.returncode == 2
    assert "--result-root name must be" in completed.stderr
    assert "requires --performance-readiness" not in completed.stderr
    assert completed.stdout == ""
    assert not root.exists()

    invalid = subprocess.run([
        sys.executable, "scripts/run_scdmp_mf_rs_mk_b01.py", "--run-01",
        "--receipt", str(tmp_path / "admit.json"), "--result-root", str(root),
        "--confirm-run-id", RUN_CONFIRMATION,
        "--performance-readiness", str(tmp_path / "missing-ready.json"),
    ], cwd=Path.cwd(), capture_output=True, text=True)
    assert invalid.returncode == 2
    assert "--result-root name must be" in invalid.stderr
    assert "invalid --performance-readiness" not in invalid.stderr
    assert invalid.stdout == ""
    assert not root.exists()


def test_cm_clean_review_produces_create_once_deep_valid_receipt(tmp_path, monkeypatch) -> None:
    root, _review, receipt, _source = _synthetic_a(tmp_path, monkeypatch)
    value = readiness.validate_performance_readiness_receipt(receipt)
    assert value["status"] == "PERFORMANCE_READY"
    assert value["assessment_root"] == str(root)
    assert value["review_binding"]["review_disposition"] == "CLEAN"
    with pytest.raises(readiness.PerformanceReadinessError, match="create-once"):
        readiness.create_performance_readiness_receipt(
            assessment_root=root, review_evidence=tmp_path / "review.json", output=receipt,
        )


def test_valid_receipt_reaches_only_the_later_admission_stub_boundary(tmp_path, monkeypatch) -> None:
    _root, _review, receipt, _source = _synthetic_a(tmp_path, monkeypatch)
    run_root = tmp_path / contracts.ATTEMPT_ID
    calls = []

    def refuse_admission(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("admission-stub-boundary")

    with pytest.raises(RuntimeError, match="admission-stub-boundary"):
        run_result(
            result_root=run_root, admission_receipt=tmp_path / "run-admit.json",
            confirmation=RUN_CONFIRMATION, argv=("python", "runner.py", "--run-01"),
            cwd=tmp_path, command_runner=refuse_admission,
            performance_readiness=receipt,
        )
    assert len(calls) == 1
    assert not run_root.exists()


@pytest.mark.parametrize("error", (RuntimeError("source-runtime"), NativeBackendError("native-runtime")))
def test_readiness_internal_exception_is_typed_and_now_recorded_not_refused(
    tmp_path, monkeypatch, error,
) -> None:
    """The receipt validator keeps its typed error; the runner records it.

    Section 11 recast (2026-09-02, owner decision 1): an invalid receipt was a
    `ResultExecutionDisabled` refusal at `runner.py:606-611`.  It is now a
    recorded `not_validated:<ExceptionType>` field and the launch continues to
    the resource admission.
    """

    _root, _review, receipt, _source = _synthetic_a(tmp_path, monkeypatch)
    monkeypatch.setattr(
        readiness, "compute_source_identity_bytes",
        lambda: (_ for _ in ()).throw(error),
    )
    with pytest.raises(readiness.PerformanceReadinessError):
        readiness.validate_performance_readiness_receipt(receipt)

    monkeypatch.setattr(
        runner_module, "validate_performance_readiness_receipt",
        lambda _path: (_ for _ in ()).throw(error),
    )
    recorded = runner_module.performance_assessment_record(
        performance_readiness=receipt, performance_assessment=None,
    )
    assert recorded["gating"] is False
    assert recorded["readiness_receipt_status"] is None
    assert recorded["readiness_receipt_note"] == f"not_validated:{type(error).__name__}"

    run_root = tmp_path / contracts.ATTEMPT_ID
    calls = []
    with pytest.raises(PreflightError):
        run_result(
            result_root=run_root, admission_receipt=tmp_path / "admit.json",
            confirmation=RUN_CONFIRMATION, argv=("python", "runner.py", "--run-01"),
            cwd=tmp_path, command_runner=lambda *args, **kwargs: calls.append((args, kwargs)),
            performance_readiness=receipt,
        )
    assert len(calls) == 1
    assert not run_root.exists()
    _assert_active_gate_is_free(run_root)


@pytest.mark.parametrize(
    "mutation", ("assessment", "telemetry", "inventory", "review", "source", "receipt_root"),
)
def test_gate_rejects_every_bound_artifact_or_identity_mismatch(tmp_path, monkeypatch, mutation) -> None:
    root, review, receipt, source_bytes = _synthetic_a(tmp_path, monkeypatch)
    if mutation == "assessment":
        path = root / "assessment.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "telemetry":
        path = root / "telemetry.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation == "inventory":
        path = root / "technical-checkpoints" / "1709" / "coordinate-000.json"
        direct = bytearray(path.read_bytes())
        direct[0] ^= 1
        path.write_bytes(direct)
    elif mutation == "review":
        review.write_bytes(review.read_bytes() + b" ")
    elif mutation == "source":
        monkeypatch.setattr(readiness, "compute_source_identity_bytes", lambda: source_bytes + b" ")
    else:
        value = json.loads(receipt.read_text(encoding="utf-8"))
        value["assessment_root"] = str(tmp_path / "wrong")
        receipt.write_bytes(_canonical(value))
    with pytest.raises(readiness.PerformanceReadinessError):
        readiness.validate_performance_readiness_receipt(receipt)


@pytest.mark.parametrize("disposition", ("REPAIR_REQUIRED", "REVIEW_REQUIRED"))
def test_nonclean_review_cannot_produce_ready_receipt(tmp_path, monkeypatch, disposition) -> None:
    root, review, receipt, _source = _synthetic_a(tmp_path, monkeypatch)
    receipt.unlink()
    value = json.loads(review.read_text(encoding="utf-8"))
    value["review_disposition"] = disposition
    review.write_bytes(_canonical(value))
    with pytest.raises(readiness.PerformanceReadinessError, match="CLEAN"):
        readiness.create_performance_readiness_receipt(
            assessment_root=root, review_evidence=review, output=receipt,
        )


@pytest.mark.parametrize("crafted", ("rss_overcap", "zero_work", "fatal_incident"))
def test_passed_true_cannot_hide_invalid_direct_telemetry(tmp_path, monkeypatch, crafted) -> None:
    root, review, receipt, _source = _synthetic_a(tmp_path, monkeypatch)
    receipt.unlink()
    path = root / "telemetry.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    measured = value["telemetry"]
    if crafted == "rss_overcap":
        measured["process_tree_peak_rss_bytes"] = 2 * 1024**3 + 1
    elif crafted == "zero_work":
        measured["wall_seconds"] = 0.0
    else:
        measured["measurement_incidents"] = [{
            "severity": "FATAL", "disposition": "MEASUREMENT_ABORTED",
            "exception_class": "PermissionError", "phase": "sample_now",
            "path_summary": "measurement-root", "errno": 13, "winerror": 5,
        }]
    path.write_bytes(_canonical(value))
    with pytest.raises(readiness.PerformanceReadinessError):
        readiness.create_performance_readiness_receipt(
            assessment_root=root, review_evidence=review, output=receipt,
        )


@pytest.mark.parametrize("crafted", ("enlarged_caps", "wrong_margin"))
def test_readiness_recomputes_exact_frozen_caps_and_projection_margin(
    tmp_path, monkeypatch, crafted,
) -> None:
    root, review, receipt, _source = _synthetic_a(tmp_path, monkeypatch)
    receipt.unlink()
    if crafted == "enlarged_caps":
        path = root / "manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["resource_caps"]["peak_rss_bytes"] *= 2
    else:
        path = root / "assessment.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["projection"]["margin_to_1800_seconds"] += 1.0
    path.write_bytes(_canonical(value))
    with pytest.raises(readiness.PerformanceReadinessError):
        readiness.create_performance_readiness_receipt(
            assessment_root=root, review_evidence=review, output=receipt,
        )
