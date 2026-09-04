from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import pytest


CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import g_init_r01_rss_successor as successor  # noqa: E402
import run_g_init_r01_rss_current_authority_20260823_04 as current  # noqa: E402


NOW = datetime(2026, 8, 23, 15, 0, 0, tzinfo=timezone.utc)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _accepted(current_paths: dict[str, Path]) -> dict[str, object]:
    return {
        "direction_id": current.certificate_spec.DIRECTION_ID,
        "exact_object_revision": current.certificate_spec.OBJECT_REVISION,
        "technical_lineage_only": True,
        "science_revision_changed": False,
        "production_coordinate_serialized": False,
        "production_coordinate_read_by_successor": False,
        "parents": {
            "original_certificate": {
                "path": str(current_paths["certificate"].resolve()),
                "sha256": current.ORIGINAL_CERTIFICATE_SHA256,
            },
            "predecessor_lease": {
                "path": str(current_paths["original_predecessor"].resolve()),
                "sha256": current.ORIGINAL_PREDECESSOR_SHA256,
                "validity_reinterpreted": False,
            },
            "backend_acceptance": {
                "path": str(current_paths["backend"].resolve()),
                "sha256": current.BACKEND_ACCEPTANCE_SHA256,
            },
        },
        "whitelist": {
            "successor_resources": current.RESOURCES,
            "unchanged_unit_plan_sha256": current.UNIT_PLAN_SHA256,
            "unchanged_canonical_worker_payload_sha256": current.CANONICAL_WORKER_PAYLOAD_SHA256,
            "atomic_install_order": current.ATOMIC_INSTALL_ORDER,
            "rng_event_native_identity_unchanged": True,
            "unchanged_original_runner_core": True,
            "unchanged_worker_loop": True,
        },
    }


def _fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, object]:
    paths = {
        "lease": tmp_path / "lease_04.json",
        "direct_predecessor": tmp_path / "lease_03.json",
        "reacceptance": tmp_path / "source_reacceptance.json",
        "certificate": tmp_path / "certificate.json",
        "original_predecessor": tmp_path / "lease_01.json",
        "backend": tmp_path / "backend.json",
        "frontier": tmp_path / "frontier",
        "result_root": tmp_path / "result_root",
    }
    paths["manifest"] = paths["frontier"] / "manifest.json"
    paths["result"] = paths["result_root"] / current.certificate_spec.RESULT_NAME
    for key in ("direct_predecessor", "reacceptance", "certificate", "original_predecessor", "backend", "manifest"):
        _write(paths[key], {"fixture": key})
    for index in range(current.BLINDED_COMMIT_COUNT):
        commit = paths["frontier"] / f"unit_{index:03d}.commit.json"
        commit.write_bytes(b"payload-must-not-be-opened")

    monkeypatch.setattr(current, "CURRENT_LEASE_PATH", paths["lease"])
    monkeypatch.setattr(current, "DIRECT_PREDECESSOR_PATH", paths["direct_predecessor"])
    monkeypatch.setattr(current, "DIRECT_PREDECESSOR_SHA256", _digest(paths["direct_predecessor"]))
    monkeypatch.setattr(current, "SOURCE_REACCEPTANCE_PATH", paths["reacceptance"])
    monkeypatch.setattr(current, "SOURCE_REACCEPTANCE_SHA256", _digest(paths["reacceptance"]))
    monkeypatch.setattr(current, "ORIGINAL_CERTIFICATE_PATH", paths["certificate"])
    monkeypatch.setattr(current, "ORIGINAL_CERTIFICATE_SHA256", _digest(paths["certificate"]))
    monkeypatch.setattr(current, "ORIGINAL_PREDECESSOR_PATH", paths["original_predecessor"])
    monkeypatch.setattr(current, "ORIGINAL_PREDECESSOR_SHA256", _digest(paths["original_predecessor"]))
    monkeypatch.setattr(current, "BACKEND_ACCEPTANCE_PATH", paths["backend"])
    monkeypatch.setattr(current, "BACKEND_ACCEPTANCE_SHA256", _digest(paths["backend"]))
    monkeypatch.setattr(current, "FRONTIER_PATH", paths["frontier"])
    monkeypatch.setattr(current, "FRONTIER_MANIFEST_PATH", paths["manifest"])
    monkeypatch.setattr(current, "FRONTIER_MANIFEST_SHA256", _digest(paths["manifest"]))
    monkeypatch.setattr(current, "RESULT_ROOT", paths["result_root"])
    monkeypatch.setattr(current, "COMPLETE_RESULT_PATH", paths["result"])
    monkeypatch.setattr(current, "_current_accepted_view", lambda: _accepted(paths))

    lease = current._expected_lease()
    _write(paths["lease"], lease)
    monkeypatch.setattr(current, "CURRENT_LEASE_SHA256", _digest(paths["lease"]))
    return {"paths": paths, "lease": lease}


def _rewrite_current_lease(monkeypatch: pytest.MonkeyPatch, fixture: dict[str, object], lease: dict[str, object]) -> None:
    path = fixture["paths"]["lease"]
    _write(path, lease)
    monkeypatch.setattr(current, "CURRENT_LEASE_SHA256", _digest(path))


def test_exact_binding_is_result_blind_and_exposes_operator_only_argv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = _fixture(monkeypatch, tmp_path)
    reads: list[Path] = []
    original_read = current._read_bytes

    def observed_read(path: Path, label: str) -> bytes:
        reads.append(path)
        return original_read(path, label)

    monkeypatch.setattr(current, "_read_bytes", observed_read)
    binding = current.validate_current_authority_binding(now=NOW)
    assert binding["lease_id"] == current.CURRENT_LEASE_ID
    assert binding["blinded_frontier"] == "26/352"
    assert binding["complete_result_absent"] is True
    assert binding["result_blind"] is True
    assert binding["operator_argv"] == (current.INTERPRETER, str(current.WRAPPER_PATH.resolve()))
    assert all(not str(path).endswith(".commit.json") for path in reads)
    assert fixture["paths"]["result"] not in reads


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"lease_id": current.CONSUMED_SUCCESSOR_ID}, "lease fields"),
        ({"resources": {**current.RESOURCES, "cpu_workers": 3}}, "lease fields"),
        ({"predecessor_lease": {"path": "wrong", "sha256": "0" * 64}}, "lease fields"),
        ({"command": "wrong"}, "lease fields"),
    ],
)
def test_binding_rejects_identity_resource_lineage_and_command_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    change: dict[str, object],
    message: str,
) -> None:
    fixture = _fixture(monkeypatch, tmp_path)
    _rewrite_current_lease(monkeypatch, fixture, {**fixture["lease"], **change})
    with pytest.raises(current.CurrentAuthorityValidationError, match=message):
        current.validate_current_authority_binding(now=NOW)


def test_binding_rejects_short_window_frontier_count_and_complete_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = _fixture(monkeypatch, tmp_path)
    with pytest.raises(current.CurrentAuthorityValidationError, match="complete slice"):
        current.validate_current_authority_binding(
            now=datetime(2026, 8, 24, 11, 0, 0, tzinfo=timezone.utc)
        )

    commit = fixture["paths"]["frontier"] / "unit_000.commit.json"
    commit.unlink()
    with pytest.raises(current.CurrentAuthorityValidationError, match="26/352"):
        current.validate_current_authority_binding(now=NOW)

    commit.write_bytes(b"still-not-opened")
    _write(fixture["paths"]["result"], {"forbidden": "complete"})
    with pytest.raises(current.CurrentAuthorityValidationError, match="complete result"):
        current.validate_current_authority_binding(now=NOW)


def test_operator_adapter_binds_fresh_id_and_path_then_restores_without_launch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = _fixture(monkeypatch, tmp_path)
    accepted = _accepted(fixture["paths"])
    monkeypatch.setattr(current, "validate_current_authority_binding", lambda: {})
    monkeypatch.setattr(current, "_current_accepted_view", lambda: accepted)
    captured: dict[str, object] = {}

    def no_launch(**kwargs: object) -> int:
        captured.update(kwargs)
        captured["lease_id"] = successor.SUCCESSOR_LEASE_ID
        captured["lease_path"] = successor.SUCCESSOR_LEASE
        captured["acceptance_path"] = successor.SUCCESSOR_ACCEPTANCE
        captured["accepted_view"] = successor.validate_successor_acceptance(current.SOURCE_REACCEPTANCE_PATH)
        return 17

    monkeypatch.setattr(successor, "invoke_unchanged_runner", no_launch)
    old = (
        successor.SUCCESSOR_LEASE_ID,
        successor.SUCCESSOR_LEASE,
        successor.SUCCESSOR_ACCEPTANCE,
        successor.validate_successor_acceptance,
    )
    assert current.invoke_operator_owned_slice() == 17
    assert captured["lease_id"] == current.CURRENT_LEASE_ID
    assert captured["lease_path"] == current.CURRENT_LEASE_PATH.resolve()
    assert captured["acceptance_path"] == current.SOURCE_REACCEPTANCE_PATH.resolve()
    assert captured["accepted_view"] is accepted
    assert (
        successor.SUCCESSOR_LEASE_ID,
        successor.SUCCESSOR_LEASE,
        successor.SUCCESSOR_ACCEPTANCE,
        successor.validate_successor_acceptance,
    ) == old
