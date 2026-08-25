from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))
import g_init_r01_resume as resume  # noqa: E402
import run_g_init_r01_resume as runner  # noqa: E402

def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value), encoding="utf-8")

def test_exact_plan_and_torn_packet_fence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(resume.experiment, "ALGORITHM_SEEDS", tuple(range(16)), raising=False)
    monkeypatch.setattr(resume.experiment, "ARMS", ("G", "ZERO"), raising=False)
    monkeypatch.setattr(resume.experiment, "CELL_FAMILIES", ("G", "ZERO", "UNIFORM", "ORACLE"), raising=False)
    monkeypatch.setattr(resume.experiment, "TRAINING_SCHEMA", "TRAIN", raising=False)
    monkeypatch.setattr(resume.experiment, "EVALUATION_SCHEMA", "EVAL", raising=False)
    monkeypatch.setattr(resume.experiment, "SCIENCE_REVISION", "TEST-R01", raising=False)
    assert len(resume.unit_plan()) == 352
    frontier = resume.Frontier(tmp_path / "frontier", tmp_path / "result", tmp_path / "TEST" / "fixture.json", 10, 1 << 30, 0)
    packet, commit = frontier.paths(("TRAIN", 0, "G", None)); _write(packet, {"schema": "TRAIN", "science_revision": "TEST-R01", "registered": True, "algorithm_seed": 0, "arm": "G", "binding_class": "PRODUCTION", "test_fixture": False})
    with pytest.raises(RuntimeError, match="torn"):
        frontier.committed(("TRAIN", 0, "G", None))
    _write(commit, {"schema": resume.FRONTIER_SCHEMA, "science_revision": "TEST-R01", "binding_class": "PRODUCTION", "test_fixture": False, "sha256": hashlib.sha256(packet.read_bytes()).hexdigest()})
    assert frontier.committed(("TRAIN", 0, "G", None)) is True
    packet_data = json.loads(packet.read_text(encoding="utf-8")); packet_data["test_fixture"] = True; _write(packet, packet_data)
    _write(commit, {"schema": resume.FRONTIER_SCHEMA, "science_revision": "TEST-R01", "binding_class": "PRODUCTION", "test_fixture": False, "sha256": hashlib.sha256(packet.read_bytes()).hexdigest()})
    with pytest.raises(RuntimeError, match="invalid"):
        frontier.committed(("TRAIN", 0, "G", None))

def test_production_consumer_rejects_test_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "TEST" / "RISP-G-INIT-REACH" / "CERTIFICATE-FIXTURE" / "V1" / "fixture.json"
    _write(fixture, {"certificate_schema": "RISP-G-INIT-REACH-TEST-CERTIFICATE-V1", "coordinate_schema": "RISP-G-INIT-REACH-TEST-CERTIFICATE-V1", "test_fixture_revision": "RISP-G-INIT-REACH-TEST-FIXTURE-20260821-01", "namespace": "TEST/RISP-G-INIT-REACH/CERTIFICATE-FIXTURE/V1", "fixture_root": "f" * 64})
    with pytest.raises(RuntimeError, match="TEST"):
        resume._certificate_binding(fixture)

def test_paired_initialization_ledger_is_counted_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resume.experiment, "ALGORITHM_SEEDS", (0,), raising=False)
    monkeypatch.setattr(resume.experiment, "ARMS", ("G", "ZERO"), raising=False)
    training = [
        {"algorithm_seed": 0, "arm": "G", "sampler_audit": {"calls": {"INIT_MODEL": 60, "ACTION": 2}}},
        {"algorithm_seed": 0, "arm": "ZERO", "sampler_audit": {"calls": {"INIT_MODEL": 60, "ACTION": 2}}},
    ]
    evaluation = [{"sampler_audit": {"calls": {"INIT_SECTOR": 3, "ACTION": 4}}}]
    assert resume._aggregate_ledger(training, evaluation) == {"ACTION": 8, "INIT_MODEL": 60, "INIT_SECTOR": 3}

def test_runner_uses_production_binder_seam_only_after_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    import g_init_r01_coordinate_certificate as certificates
    import g_init_r01_experiment as experiment
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(sys, "argv", [
        "runner", "--certificate", "C:/x/cert.json", "--frontier", "C:/x/frontier",
        "--result-root", "C:/x/result", "--workers", "2", "--cpu-cores", "2",
        "--slice-wall-seconds", "13800", "--per-worker-rss-limit-bytes", "1073741824",
        "--process-group-rss-limit-bytes", "1610612736",
    ])
    monkeypatch.setattr(certificates, "assert_production_paths", lambda *args: calls.append(("paths", args)))
    monkeypatch.setattr(resume, "_certificate_binding", lambda *args: calls.append(("certificate", args)) or {"coordinate_root": "a" * 64})
    monkeypatch.setattr(resume, "run_slice", lambda *args: calls.append(("slice", args)) or {"status": "TEST"})
    monkeypatch.setattr(experiment, "configure_production_coordinate_root", lambda root, *, validated_production_binding: calls.append(("binder", (root, validated_production_binding))) or root)
    assert runner.main() == 0
    assert calls[0][0] == "paths" and calls[1][0] == "certificate"
    assert calls[2] == ("binder", ("a" * 64, True))
    assert calls[3][0] == "slice"
    assert calls[3][1][-1] == 2


def test_evaluation_state_adapter_preserves_full_training_provenance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(resume.experiment, "ARMS", ("G", "ZERO"), raising=False)
    frontier = resume.Frontier(tmp_path / "frontier", tmp_path / "result", tmp_path / "certificate", 10, 1 << 30, 0)
    packets = {}
    for arm in ("G", "ZERO"):
        item = ("TRAIN", 7, arm, None)
        packet_path, _ = frontier.paths(item)
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        value = {"algorithm_seed": 7, "arm": arm, "binding_class": "PRODUCTION", "final_state": {"E": [[arm]]}}
        packet_path.write_text(json.dumps(value), encoding="utf-8")
        packets[arm] = value
    monkeypatch.setattr(frontier, "committed", lambda item: item[0] == "TRAIN" and item[1] == 7)
    assert resume._states(frontier, 7) == packets


def test_ordered_worker_batch_rejects_invalid_count_and_installs_nothing_on_failure() -> None:
    with pytest.raises(ValueError, match="worker_count"):
        resume.execute_test_units_ordered([{"binding_class": "TEST_ONLY"}], worker_count=0)
    installed: list[object] = []
    payload = {
        "binding_class": "TEST_ONLY", "root": "b" * 64,
        "item": ("INVALID", 1, "UNIFORM", 2), "episodes": 1,
    }
    with pytest.raises(RuntimeError, match="phase"):
        resume.execute_test_units_ordered([payload], worker_count=1, install=lambda *value: installed.append(value))
    assert installed == []


def test_production_worker_payload_has_no_frontier_paths_and_preserves_dependencies(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frontier = resume.Frontier(
        tmp_path / "frontier", tmp_path / "result", tmp_path / "certificate",
        13800, 1073741824, 10.0, 2, 1610612736,
    )
    training = ("TRAIN", 3, "G", None)
    train_payload = resume._production_worker_payload(frontier, {"coordinate_root": "1" * 64}, training, 99.0)
    assert train_payload == {
        "binding_class": "PRODUCTION", "validated_production_binding": True,
        "root": "1" * 64, "item": training, "deadline_monotonic": 99.0,
        "per_worker_rss_limit_bytes": 1073741824,
    }
    monkeypatch.setattr(resume, "_states", lambda _frontier, seed: {"G": {"algorithm_seed": seed}})
    evaluation = ("EVAL", 3, "G-INTACT", 2)
    eval_payload = resume._production_worker_payload(frontier, {"coordinate_root": "1" * 64}, evaluation, 99.0)
    assert eval_payload["checkpoint_states"] == {"G": {"algorithm_seed": 3}}
    assert not {"frontier", "frontier_root", "result_root", "packet_path", "commit_path"}.intersection(eval_payload)


def test_parent_validates_production_worker_semantic_hash_and_identity() -> None:
    payload = {
        "binding_class": "PRODUCTION", "item": ("TRAIN", 5, "G-START/ZERO-CENTER", None),
    }
    packet = {
        "schema": resume.experiment.TRAINING_SCHEMA,
        "science_revision": resume.experiment.SCIENCE_REVISION,
        "binding_class": "PRODUCTION", "test_fixture": False, "registered": True,
        "algorithm_seed": 5, "arm": "G-START/ZERO-CENTER", "elapsed_seconds": 1.25,
    }
    result = {"item": payload["item"], "packet": packet, "semantic_sha256": resume._semantic_packet_sha256(packet)}
    resume._validate_worker_result(payload, result)
    result["semantic_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="hash or identity"):
        resume._validate_worker_result(payload, result)


def test_next_atomic_batch_is_plan_ordered_and_training_first(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frontier = resume.Frontier(tmp_path / "f", tmp_path / "r", tmp_path / "c", 13800, 1073741824, 0.0, 2, 1610612736)
    plan = (
        ("TRAIN", 0, "G", None), ("TRAIN", 0, "ZERO", None),
        ("EVAL", 0, "G", 0), ("EVAL", 0, "G", 1),
    )
    committed: set[tuple[str, int, str, int | None]] = set()
    monkeypatch.setattr(frontier, "committed", lambda item: item in committed)
    assert resume._next_atomic_batch(frontier, plan) == plan[:2]
    committed.update(plan[:2])
    assert resume._next_atomic_batch(frontier, plan) == plan[2:]


def test_mocked_production_worker_preflights_binds_and_emits_no_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(resume.native_backend, "production_preflight", lambda **_kwargs: calls.append("preflight") or {})
    monkeypatch.setattr(resume.experiment, "coordinate_root", lambda: None)
    monkeypatch.setattr(resume.experiment, "fixture_root", lambda: None)
    monkeypatch.setattr(
        resume.experiment, "configure_production_coordinate_root",
        lambda _root, *, validated_production_binding: calls.append(f"bind:{validated_production_binding}"),
    )
    packet = {
        "schema": resume.experiment.TRAINING_SCHEMA,
        "science_revision": resume.experiment.SCIENCE_REVISION,
        "binding_class": "PRODUCTION", "test_fixture": False, "registered": True,
        "algorithm_seed": 4, "arm": "G-START/ZERO-CENTER",
    }
    monkeypatch.setattr(
        resume.experiment, "run_training_unit",
        lambda *_args, **_kwargs: calls.append("train") or packet,
    )
    monkeypatch.setattr(resume, "_peak_rss_bytes", lambda: 1000)
    payload = {
        "binding_class": "PRODUCTION", "validated_production_binding": True,
        "root": "2" * 64, "item": ("TRAIN", 4, "G-START/ZERO-CENTER", None),
        "deadline_monotonic": resume.time.monotonic() + 60,
        "per_worker_rss_limit_bytes": 1073741824,
    }
    result = resume._isolated_unit_worker(payload)
    assert calls[:3] == ["preflight", "bind:True", "train"]
    assert result["packet"] == packet


def test_mocked_expired_production_worker_does_not_start_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(resume.native_backend, "production_preflight", lambda **_kwargs: {})
    monkeypatch.setattr(resume.experiment, "coordinate_root", lambda: "3" * 64)
    monkeypatch.setattr(resume.experiment, "fixture_root", lambda: None)
    monkeypatch.setattr(resume, "_peak_rss_bytes", lambda: 1000)
    monkeypatch.setattr(
        resume.experiment, "run_training_unit",
        lambda *_args, **_kwargs: pytest.fail("expired worker reached stochastic unit"),
    )
    payload = {
        "binding_class": "PRODUCTION", "validated_production_binding": True,
        "root": "3" * 64, "item": ("TRAIN", 4, "G-START/ZERO-CENTER", None),
        "deadline_monotonic": resume.time.monotonic() - 1,
        "per_worker_rss_limit_bytes": 1073741824,
    }
    with pytest.raises(resume.SliceExpired, match="reserve"):
        resume._isolated_unit_worker(payload)


def test_batch_and_prior_receipt_resource_accounting(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(resume, "_peak_rss_bytes", lambda: 200)
    results = [
        {"pid": 10, "peak_rss_bytes": 1000, "worker_cpu_seconds": 3.0, "worker_wall_seconds": 4.0},
        {"pid": 11, "peak_rss_bytes": 1100, "worker_cpu_seconds": 2.0, "worker_wall_seconds": 3.0},
    ]
    assert resume._batch_resource_accounting(results) == {
        "worker_cpu_seconds": 5.0, "worker_wall_seconds": 7.0,
        "parallel_batch_wall_seconds": 4.0, "worker_peak_rss_max_bytes": 1100,
        "process_group_rss_max_bytes": 2300,
    }
    frontier = resume.Frontier(tmp_path / "frontier", tmp_path / "result", tmp_path / "certificate", 13800, 1073741824, 0.0)
    cumulative = {
        "committed_batches": 3, "worker_cpu_seconds": 9.0, "worker_wall_seconds": 12.0,
        "parallel_batch_wall_seconds": 7.0, "parent_cpu_seconds": 1.0,
        "slice_elapsed_seconds": 20.0, "worker_peak_rss_max_bytes": 1100,
        "process_group_rss_max_bytes": 2300,
    }
    _write(frontier.receipts / "slice_0000.json", {"cumulative_resource_accounting": cumulative})
    assert all(resume._prior_resource_accounting(frontier)[key] == value for key, value in cumulative.items())


def test_slice_expiry_keeps_batch_uninstalled_and_writes_blinded_receipt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frontier = resume.Frontier(
        tmp_path / "frontier", tmp_path / "result", tmp_path / "certificate",
        13800, 1073741824, resume.time.monotonic(), 2, 1610612736,
    )
    frontier.receipts.mkdir(parents=True)
    plan = (("TRAIN", 0, "G", None), ("TRAIN", 0, "ZERO", None))
    monkeypatch.setattr(resume, "_initialize", lambda _frontier: {"coordinate_root": "4" * 64})
    monkeypatch.setattr(resume, "unit_plan", lambda: plan)
    monkeypatch.setattr(resume.experiment, "structural_certificate", lambda: {"passed": True})
    monkeypatch.setattr(frontier, "committed", lambda _item: False)
    monkeypatch.setattr(resume, "_production_worker_payload", lambda *_args: {"binding_class": "PRODUCTION"})
    installs: list[object] = []
    def expire(*_args: object, **kwargs: object) -> list[dict]:
        installs.append(kwargs.get("install"))
        raise resume.SliceExpired("slice reserve reached before atomic batch completion")
    monkeypatch.setattr(resume, "execute_units_ordered", expire)
    result = resume._run_slice_locked(frontier)
    receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8"))
    assert receipt["committed_atomic_units_before"] == receipt["committed_atomic_units_after"] == 0
    assert receipt["slice_resource_accounting"]["committed_batches"] == 0
    assert receipt["blinded_frontier_unchanged_on_uncommitted_batch"] is True
