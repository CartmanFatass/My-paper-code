from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest


CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import g_init_r01_coordinate_certificate as certificate_spec  # noqa: E402
import g_init_r01_experiment as experiment  # noqa: E402
import g_init_r01_native_backend as native_backend  # noqa: E402
import g_init_r01_resume as resume  # noqa: E402
import g_init_r01_rss_successor as successor  # noqa: E402
import run_g_init_r01_resume as original_runner  # noqa: E402
import run_g_init_r01_rss_successor as successor_runner  # noqa: E402


NOW = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _stored_manifest_with_external_shared_drift() -> dict[str, str]:
    manifest: dict[str, str] = {}
    for suffix in successor._DIRECTION_PROTECTED_SUFFIXES:
        path = successor.ROOT / suffix
        manifest[str(path.resolve())] = successor._sha(path)
    shared = successor.ROOT / successor._SHARED_REGISTRY_SUFFIX
    manifest[str(shared.resolve())] = "0" * 64
    return manifest


def _fixture(tmp_path: Path) -> dict[str, object]:
    certificate = tmp_path / "TEST" / "original_certificate.json"
    predecessor = tmp_path / "TEST" / "expired_predecessor_lease.json"
    backend = tmp_path / "TEST" / "backend_acceptance.json"
    frontier = tmp_path / "TEST" / "frontier"
    manifest = frontier / "manifest.json"
    result_root = tmp_path / "TEST" / "result"
    result = result_root / certificate_spec.RESULT_NAME
    acceptance = tmp_path / "TEST" / "successor_acceptance.json"
    lease = tmp_path / "TEST" / "successor_lease.json"
    _write(certificate, {"synthetic_test_certificate": True, "no_coordinate_field": True})
    _write(predecessor, {"expired_at": "2000-01-01T00:00:00Z", "immutable_parent_only": True})
    _write(manifest, {"synthetic_zero_commit_frontier": True})
    observed = native_backend.production_preflight(batch_width=32)
    _write(backend, {
        "native_artifact": observed["local"],
        "shared_functional_acceptance": observed["shared"],
    })
    stored_manifest = _stored_manifest_with_external_shared_drift()
    packet = successor.build_successor_acceptance(
        output=acceptance, original_certificate=certificate, predecessor_lease=predecessor,
        backend_acceptance=backend, frontier_manifest=manifest, result_path=result,
        original_source_manifest=stored_manifest, test_only=True,
    )
    command = successor.successor_command(
        certificate=certificate, frontier=frontier, result_root=result_root,
        successor_acceptance=acceptance, successor_lease=lease,
    )
    lease_packet = {
        "schema": successor.SUCCESSOR_LEASE_SCHEMA, "lease_id": successor.SUCCESSOR_LEASE_ID,
        "direction_id": certificate_spec.DIRECTION_ID, "stage_id": certificate_spec.STAGE_ID,
        "exact_object_revision": certificate_spec.OBJECT_REVISION,
        "production_authorized": True, "issued_at": "2026-08-21T11:00:00Z",
        "not_after": "2026-08-21T18:00:00Z", "resources": successor.SUCCESSOR_RESOURCES,
        "certificate": str(certificate.resolve()), "frontier": str(frontier.resolve()),
        "result_root": str(result_root.resolve()), "result": str(result.resolve()), "command": command,
        "successor_acceptance": {"path": str(acceptance.resolve()), "sha256": successor._sha(acceptance)},
        "immutable_lineage": {
            "original_certificate": packet["parents"]["original_certificate"],
            "predecessor_lease": {
                "path": packet["parents"]["predecessor_lease"]["path"],
                "sha256": packet["parents"]["predecessor_lease"]["sha256"],
            },
        },
    }
    _write(lease, lease_packet)
    return {
        "certificate": certificate, "predecessor": predecessor, "backend": backend,
        "frontier": frontier, "manifest": manifest, "result_root": result_root,
        "result": result, "acceptance": acceptance, "lease": lease,
        "acceptance_packet": packet, "lease_packet": lease_packet,
    }


def test_builder_and_validator_bind_exact_whitelist_without_coordinate(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    packet = successor.validate_successor_acceptance(fixture["acceptance"], test_only=True)
    assert packet["production_coordinate_serialized"] is False
    assert packet["production_coordinate_read_by_successor"] is False
    assert packet["whitelist"]["sole_resource_change"] == {
        "field": "process_group_rss_limit_bytes",
        "before": 1610612736, "after": 2684354560,
    }
    old = packet["whitelist"]["predecessor_resources"]
    new = packet["whitelist"]["successor_resources"]
    assert {key: value for key, value in old.items() if key != "process_group_rss_limit_bytes"} == {
        key: value for key, value in new.items() if key != "process_group_rss_limit_bytes"
    }
    lineage = packet["parents"]["shared_registry_lineage"]
    assert lineage["byte_identity_changed_outside_successor_scope"] is True
    assert lineage["accepted_only_by_original_component_semantic_identity"] is True
    with pytest.raises(FileExistsError):
        successor.build_successor_acceptance(
            output=fixture["acceptance"], original_certificate=fixture["certificate"],
            predecessor_lease=fixture["predecessor"], backend_acceptance=fixture["backend"],
            frontier_manifest=fixture["manifest"], result_path=fixture["result"],
            original_source_manifest=_stored_manifest_with_external_shared_drift(), test_only=True,
        )


def test_successor_lease_accepts_expired_predecessor_only_as_parent_and_current_window(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    lease = successor.validate_successor_lease(
        fixture["lease"], acceptance_path=fixture["acceptance"], certificate=fixture["certificate"],
        frontier=fixture["frontier"], result_root=fixture["result_root"], now=NOW, test_only=True,
    )
    assert lease["lease_id"] == successor.SUCCESSOR_LEASE_ID
    assert successor.PREDECESSOR_LEASE == Path("C:/Projects/HMASD/temp/leases/RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260821_01.json")
    assert successor.SUCCESSOR_LEASE == Path("C:/Projects/HMASD/temp/leases/RISP_G_INIT_REACH_R01_ROOT_EMPIRICAL_LEASE_20260821_02.json")
    assert json.loads(fixture["predecessor"].read_text(encoding="utf-8"))["expired_at"].startswith("2000")
    for resources, message in (
        ({**successor.SUCCESSOR_RESOURCES, "process_group_rss_limit_bytes": 1610612736}, "whitelist"),
        ({**successor.SUCCESSOR_RESOURCES, "cpu_workers": 3}, "whitelist"),
    ):
        changed = {**fixture["lease_packet"], "resources": resources}
        _write(fixture["lease"], changed)
        with pytest.raises(successor.SuccessorValidationError, match=message):
            successor.validate_successor_lease(
                fixture["lease"], acceptance_path=fixture["acceptance"], certificate=fixture["certificate"],
                frontier=fixture["frontier"], result_root=fixture["result_root"], now=NOW, test_only=True,
            )


def test_successor_lease_rejects_future_expired_short_hash_path_and_command(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    cases = (
        ({"issued_at": "2026-08-21T13:00:00Z"}, "future-issued"),
        ({"not_after": "2026-08-21T12:00:00Z"}, "expired"),
        ({"not_after": "2026-08-21T15:00:00Z"}, "complete slice"),
        ({"command": "wrong"}, "command or lineage"),
        ({"successor_acceptance": {"path": str(fixture["acceptance"]), "sha256": "0" * 64}}, "command or lineage"),
    )
    for change, message in cases:
        _write(fixture["lease"], {**fixture["lease_packet"], **change})
        with pytest.raises(successor.SuccessorValidationError, match=message):
            successor.validate_successor_lease(
                fixture["lease"], acceptance_path=fixture["acceptance"], certificate=fixture["certificate"],
                frontier=fixture["frontier"], result_root=fixture["result_root"], now=NOW, test_only=True,
            )


def test_acceptance_snapshot_allows_append_only_progress_but_rejects_manifest_result_and_parent_changes(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    successor.validate_successor_lease(
        fixture["lease"], acceptance_path=fixture["acceptance"], certificate=fixture["certificate"],
        frontier=fixture["frontier"], result_root=fixture["result_root"], now=NOW, test_only=True,
    )
    commit = fixture["frontier"] / "training_units" / "x.commit.json"
    _write(commit, {})
    assert successor.validate_successor_acceptance(fixture["acceptance"], test_only=True)["parents"]["zero_commit_frontier"]["commit_count"] == 0
    assert successor.validate_successor_lease(
        fixture["lease"], acceptance_path=fixture["acceptance"], certificate=fixture["certificate"],
        frontier=fixture["frontier"], result_root=fixture["result_root"], now=NOW, test_only=True,
    )["lease_id"] == successor.SUCCESSOR_LEASE_ID
    fixture["manifest"].write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(successor.SuccessorValidationError, match="manifest lineage"):
        successor.validate_successor_acceptance(fixture["acceptance"], test_only=True)
    _write(fixture["manifest"], {"synthetic_zero_commit_frontier": True})
    fixture["result"].parent.mkdir(parents=True, exist_ok=True)
    fixture["result"].write_text("{}", encoding="utf-8")
    with pytest.raises(successor.SuccessorValidationError, match="already-present complete result"):
        successor.validate_successor_acceptance(fixture["acceptance"], test_only=True)
    fixture["result"].unlink()
    fixture["predecessor"].write_text("changed", encoding="utf-8")
    with pytest.raises(successor.SuccessorValidationError, match="lineage or whitelist"):
        successor.validate_successor_acceptance(fixture["acceptance"], test_only=True)


def test_builder_rejects_protected_direction_source_and_native_semantic_mismatch(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    manifest = _stored_manifest_with_external_shared_drift()
    resume_path = str((successor.ROOT / "experiments/candidates/renewal_indexed_score_plasticity/g_init_r01_resume.py").resolve())
    manifest[resume_path] = "f" * 64
    with pytest.raises(successor.SuccessorValidationError, match="protected direction-local source"):
        successor.build_successor_acceptance(
            output=tmp_path / "TEST" / "bad_source_acceptance.json",
            original_certificate=fixture["certificate"], predecessor_lease=fixture["predecessor"],
            backend_acceptance=fixture["backend"], frontier_manifest=fixture["manifest"],
            result_path=fixture["result"], original_source_manifest=manifest, test_only=True,
        )
    backend = json.loads(fixture["backend"].read_text(encoding="utf-8"))
    backend["native_artifact"]["build_key"] = "e" * 64
    _write(fixture["backend"], backend)
    with pytest.raises(successor.SuccessorValidationError, match="native artifact/ABI"):
        successor.build_successor_acceptance(
            output=tmp_path / "TEST" / "bad_native_acceptance.json",
            original_certificate=fixture["certificate"], predecessor_lease=fixture["predecessor"],
            backend_acceptance=fixture["backend"], frontier_manifest=fixture["manifest"],
            result_path=fixture["result"], original_source_manifest=_stored_manifest_with_external_shared_drift(),
            test_only=True,
        )


def test_old_new_preexecution_plan_and_canonical_payload_bytes_are_identical(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan_before = resume.unit_plan()
    canonical_before = successor.canonical_worker_payload_bytes()
    frontier = resume.Frontier(tmp_path / "TEST" / "f", tmp_path / "TEST" / "r", tmp_path / "TEST" / "c", 13800, 1073741824, 0.0, 2, 1610612736)
    item = plan_before[0]
    payload_before = resume._production_worker_payload(frontier, {"coordinate_root": "a" * 64}, item, 123.0)
    original_group = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES
    try:
        certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = successor.SUCCESSOR_GROUP_RSS_BYTES
        payload_after = resume._production_worker_payload(frontier, {"coordinate_root": "a" * 64}, item, 123.0)
        assert resume.unit_plan() == plan_before
        assert successor.canonical_worker_payload_bytes() == canonical_before
        assert json.dumps(payload_after, sort_keys=True, separators=(",", ":")) == json.dumps(payload_before, sort_keys=True, separators=(",", ":"))
    finally:
        certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = original_group


def test_original_atomic_executor_installs_out_of_order_completions_in_plan_order(monkeypatch: pytest.MonkeyPatch) -> None:
    payloads = [
        {"binding_class": "TEST_ONLY", "root": "b" * 64, "item": ("TRAIN", 70, experiment.ARMS[0], None), "updates": 1, "episodes": 2},
        {"binding_class": "TEST_ONLY", "root": "b" * 64, "item": ("TRAIN", 71, experiment.ARMS[1], None), "updates": 1, "episodes": 2},
    ]
    class Future:
        def __init__(self, result: dict): self._result = result
        def result(self) -> dict: return self._result
    class Executor:
        def __init__(self, **_kwargs: object): self.futures: list[Future] = []
        def __enter__(self) -> "Executor": return self
        def __exit__(self, *_args: object) -> None: return None
        def submit(self, _fn: object, payload: dict) -> Future:
            phase, seed, arm, _ = payload["item"]
            packet = {
                "schema": experiment.TEST_TRAINING_SCHEMA,
                "science_revision": experiment.TEST_FIXTURE_REVISION,
                "binding_class": "TEST_ONLY", "test_fixture": True, "registered": False,
                "algorithm_seed": seed, "arm": arm,
            }
            result = {"item": payload["item"], "packet": packet, "semantic_sha256": resume._semantic_packet_sha256(packet), "pid": seed, "peak_rss_bytes": 1000}
            future = Future(result); self.futures.append(future); return future
    monkeypatch.setattr(resume, "ProcessPoolExecutor", Executor)
    monkeypatch.setattr(resume, "as_completed", lambda futures: list(reversed(tuple(futures))))
    monkeypatch.setattr(resume, "_peak_rss_bytes", lambda: 1000)
    installed: list[tuple] = []
    resume.execute_test_units_ordered(payloads, worker_count=2, install=lambda item, _packet: installed.append(item))
    assert installed == [tuple(payload["item"]) for payload in payloads]


def test_rng_address_event_token_census_and_native_identity_do_not_depend_on_group_ceiling() -> None:
    if experiment.fixture_root() is None and experiment.coordinate_root() is None:
        experiment.configure_test_fixture_root("9" * 64)
    assert experiment.coordinate_root() is None
    identity = experiment.event_identity(7, "TRAIN", 0, 2, 1, 3, "ACK")
    before = (identity, experiment._event_token(identity), experiment.bit_prefix(identity, 1024), experiment.expected_complete_ledger())
    old_group = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES
    try:
        certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = successor.SUCCESSOR_GROUP_RSS_BYTES
        same_identity = experiment.event_identity(7, "TRAIN", 0, 2, 1, 3, "ACK")
        after = (same_identity, experiment._event_token(same_identity), experiment.bit_prefix(same_identity, 1024), experiment.expected_complete_ledger())
        assert before == after
        preflight = native_backend.production_preflight(batch_width=32)
        assert preflight["shared"]["component"] == certificate_spec.CANONICAL_COMPONENT
        assert preflight["local"]["runtime_abi"]["struct_sizes"] == {"reset_input": 160, "step_input": 64, "extended_step_input": 288, "transition_output": 104}
    finally:
        certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES = old_group


def test_runtime_adapter_restores_every_override_after_exception(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    backend = tmp_path / "TEST" / "backend.json"; _write(backend, {})
    predecessor = tmp_path / "TEST" / "predecessor.json"; _write(predecessor, {})
    acceptance = {
        "parents": {
            "original_source_manifest": {"entries": {}},
            "predecessor_lease": {"path": str(predecessor), "sha256": successor._sha(predecessor)},
            "backend_acceptance": {"path": str(backend), "sha256": successor._sha(backend)},
        },
    }
    monkeypatch.setattr(successor, "validate_successor_acceptance", lambda *_args, **_kwargs: acceptance)
    monkeypatch.setattr(successor, "validate_successor_lease", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(original_runner, "main", lambda: (_ for _ in ()).throw(RuntimeError("synthetic runner exception")))
    old_group = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES
    old_interface = certificate_spec.LEASE_BINDING_INTERFACE
    old_source = certificate_spec.source_manifest
    old_backend = certificate_spec.validate_backend_binding
    old_lease = certificate_spec.validate_lease_binding
    old_binding = resume._certificate_binding
    old_argv = list(sys.argv)
    with pytest.raises(RuntimeError, match="synthetic runner"):
        successor.invoke_unchanged_runner(
            certificate=tmp_path / "TEST" / "certificate", frontier=tmp_path / "TEST" / "frontier",
            result_root=tmp_path / "TEST" / "result", successor_acceptance=tmp_path / "TEST" / "acceptance",
            successor_lease=tmp_path / "TEST" / "lease", now=NOW, test_only=True,
        )
    assert certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES == old_group
    assert certificate_spec.LEASE_BINDING_INTERFACE is old_interface
    assert certificate_spec.source_manifest is old_source
    assert certificate_spec.validate_backend_binding is old_backend
    assert certificate_spec.validate_lease_binding is old_lease
    assert resume._certificate_binding is old_binding
    assert sys.argv == old_argv


def test_wrapper_cli_is_exact_and_delegates_without_worker_launch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(successor, "invoke_unchanged_runner", lambda **kwargs: calls.append(kwargs) or 0)
    monkeypatch.setattr(sys, "argv", [
        "rss-wrapper", "--certificate", str(tmp_path / "c"), "--frontier", str(tmp_path / "f"),
        "--result-root", str(tmp_path / "r"), "--successor-acceptance", str(tmp_path / "a"),
        "--successor-lease", str(tmp_path / "l"), "--workers", "2", "--cpu-cores", "2",
        "--slice-wall-seconds", "13800", "--per-worker-rss-limit-bytes", "1073741824",
        "--process-group-rss-limit-bytes", "2684354560",
    ])
    assert successor_runner.main() == 0
    assert len(calls) == 1
    assert calls[0]["successor_lease"] == tmp_path / "l"


def test_exact_script_path_help_imports_without_pythonpath() -> None:
    import os
    import subprocess

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [certificate_spec.INTERPRETER, str(successor.SUCCESSOR_RUNNER), "--help"],
        cwd=successor.ROOT, env=environment, capture_output=True, text=True,
        check=False, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--successor-acceptance" in completed.stdout
