from __future__ import annotations

import sys
from pathlib import Path

import pytest
import json
from datetime import datetime, timezone

CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))
import g_init_r01_coordinate_certificate as certificate  # noqa: E402

def test_certificate_is_no_overwrite_and_binds_exact_test_paths(tmp_path: Path) -> None:
    output = tmp_path / "TEST" / "RISP-G-INIT-REACH" / "CERTIFICATE-FIXTURE" / "V1" / "certificate.json"
    packet = certificate.build_test_fixture(output)
    assert packet["certificate_schema"] == certificate.TEST_SCHEMA
    assert packet["coordinate_schema"] == certificate.TEST_SCHEMA
    assert packet["namespace"] == certificate.TEST_NAMESPACE
    assert packet["fixture_root"] == "f" * 64
    assert "science_revision" not in packet
    assert "coordinate_root" not in packet
    assert "coordinate_binding_activity_started" not in packet
    with pytest.raises(FileExistsError):
        certificate.build_test_fixture(output)

def test_production_builder_rejects_test_provenance_before_root_generation(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="TEST"):
        certificate.build_production_certificate(
            output=tmp_path / "TEST" / "certificate.json", frontier=tmp_path / "TEST" / "frontier",
            result_root=tmp_path / "TEST" / "result", backend_binding=tmp_path / "backend", lease_binding=tmp_path / "lease",
        )

def test_unregistered_backend_interface_cannot_be_satisfied_by_arbitrary_json(tmp_path: Path) -> None:
    backend = tmp_path / "backend.json"
    backend.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="frozen R01 interface"):
        certificate.validate_backend_binding(backend)
    assert certificate.BACKEND_BINDING_INTERFACE["schema"].endswith("V1")
    assert certificate.BACKEND_BINDING_INTERFACE["component"] == "risp.g_init_reach.r01.full_host"


def _accepted_backend() -> dict:
    digest = "1" * 64
    native = {
        "schema": "RISP-G-INIT-REACH-R01-NATIVE-ARTIFACT-IDENTITY-V1",
        "abi_version": 1, "build_key": digest, "artifact_sha256": digest,
        "source_sha256": digest, "python_fallback": False,
        "runtime_abi": {"struct_sizes": {"reset_input": 160, "step_input": 64, "extended_step_input": 288, "transition_output": 104}},
    }
    shared = {
        "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
        "component": certificate.CANONICAL_COMPONENT, "backend": "cpp", "batch_width": 32,
        "full_reset_step_cpp": True, "python_fallback": False,
        "native": {"artifact_sha256": digest},
    }
    return {
        "schema": certificate.BACKEND_BINDING_INTERFACE["schema"],
        "direction_id": "renewal_indexed_score_plasticity",
        "exact_object_revision": "RISP-G-INIT-REACH-R01-FULL-PANEL / RISP-G-INIT-REACH-SCIENCE-20260821-01",
        "component": certificate.CANONICAL_COMPONENT, "accepted_full_host_cpp": True,
        "native_artifact": native, "shared_functional_acceptance": shared,
        "efficiency_review": {
            "schema": certificate.BACKEND_BINDING_INTERFACE["efficiency_schema"],
            "status": "COMPLETE", "lease_ready": True,
            "projected_complete_cpu_hours": 30.0, "projected_complete_wall_seconds": 73745.0,
            "representative_workers": {
                "schema": certificate.BACKEND_BINDING_INTERFACE["representative_schema"],
                "worker_count": 2, "exact_semantic_hashes": True,
                "per_worker_peak_rss_bytes": 500000000,
                "process_group_ram_bytes": 1203560448,
                "training_semantic_hashes": [str(index) * 64 for index in range(1, 5)],
                "evaluation_semantic_hashes": [str(index) * 64 for index in range(5, 9)],
            },
        },
        "source_hashes": certificate.source_manifest(), "test_hashes": certificate.test_manifest(),
        "rollback_nodes": certificate.BACKEND_BINDING_INTERFACE["rollback_nodes"],
    }


def test_backend_and_lease_binding_require_exact_expanded_ceiling(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    backend = tmp_path / "backend.json"
    backend.write_text(json.dumps(_accepted_backend()), encoding="utf-8")
    assert certificate.validate_backend_binding(backend)["component"] == certificate.CANONICAL_COMPONENT
    acceptance = tmp_path / "backend_acceptance.json"; acceptance.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(certificate, "BACKEND_ACCEPTANCE", acceptance)
    now = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    lease = {
        "schema": certificate.LEASE_BINDING_INTERFACE["schema"],
        "lease_id": certificate.LEASE_ID, "direction_id": certificate.DIRECTION_ID,
        "stage_id": certificate.STAGE_ID, "exact_object_revision": certificate.OBJECT_REVISION,
        "production_authorized": True, "issued_at": "2026-08-21T11:00:00Z",
        "not_after": "2026-08-21T18:00:00Z",
        "backend_acceptance": {"path": str(acceptance), "sha256": certificate._sha(acceptance)},
        "certificate": str(certificate.PRODUCTION_CERTIFICATE), "frontier": str(certificate.PRODUCTION_FRONTIER),
        "result_root": str(certificate.PRODUCTION_RESULT_ROOT),
        "result": str(certificate.PRODUCTION_RESULT_ROOT / certificate.RESULT_NAME),
        "command": certificate.production_command(), "resources": certificate.LEASE_BINDING_INTERFACE["resources"],
    }
    lease_path = tmp_path / "lease.json"; lease_path.write_text(json.dumps(lease), encoding="utf-8")
    assert certificate.validate_lease_binding(lease_path, now=now)["resources"]["cpu_workers"] == 2
    lease["resources"] = {**lease["resources"], "cpu_workers": 3}
    lease_path.write_text(json.dumps(lease), encoding="utf-8")
    with pytest.raises(RuntimeError, match="lease binding"):
        certificate.validate_lease_binding(lease_path, now=now)


def test_lease_rejects_future_expired_and_short_windows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    acceptance = tmp_path / "acceptance.json"; acceptance.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(certificate, "BACKEND_ACCEPTANCE", acceptance)
    now = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    base = {
        "schema": certificate.LEASE_BINDING_INTERFACE["schema"], "lease_id": certificate.LEASE_ID,
        "direction_id": certificate.DIRECTION_ID, "stage_id": certificate.STAGE_ID,
        "exact_object_revision": certificate.OBJECT_REVISION, "production_authorized": True,
        "backend_acceptance": {"path": str(acceptance), "sha256": certificate._sha(acceptance)},
        "certificate": str(certificate.PRODUCTION_CERTIFICATE), "frontier": str(certificate.PRODUCTION_FRONTIER),
        "result_root": str(certificate.PRODUCTION_RESULT_ROOT), "result": str(certificate.PRODUCTION_RESULT_ROOT / certificate.RESULT_NAME),
        "command": certificate.production_command(), "resources": certificate.LEASE_BINDING_INTERFACE["resources"],
    }
    lease = tmp_path / "lease.json"
    for issued, expires, message in (
        ("2026-08-21T13:00:00Z", "2026-08-21T20:00:00Z", "future-issued"),
        ("2026-08-21T08:00:00Z", "2026-08-21T12:00:00Z", "expired"),
        ("2026-08-21T08:00:00Z", "2026-08-21T15:00:00Z", "complete slice"),
    ):
        lease.write_text(json.dumps({**base, "issued_at": issued, "not_after": expires}), encoding="utf-8")
        with pytest.raises(RuntimeError, match=message):
            certificate.validate_lease_binding(lease, now=now)
