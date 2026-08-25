from __future__ import annotations

from dataclasses import replace
import json
import inspect
import subprocess
from types import SimpleNamespace

import numpy as np

import pytest

from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary import (
    EXPECTED_ARM_INDEPENDENT_ORIGINS_PANEL,
    EXPECTED_COMBINED_SOURCE_SHA256,
    EXPECTED_NATIVE_ARTIFACT_SHA256,
    EXPECTED_NATIVE_SOURCE_SHA256,
    EXPECTED_RUNNER_SHA256,
    BlindedSeedFrontier,
    EmpiricalCoordinateAdapter,
    ProductionLifecycleStore,
    ProductionBoundaryError,
    IntegrityError,
    LeaseValidationError,
    canonical_sha256,
    current_exact_source_binding,
    exact_future_launch_contract,
    initialize_one_worker_parameters,
    run_sealed_test_preflight,
    validate_production_preflight_artifact,
    validate_root_lease,
)


def test_exact_width32_source_abi_binding_and_drift_rejection(monkeypatch) -> None:
    binding = current_exact_source_binding(load_native=True)
    assert binding.combined_source_sha256 == EXPECTED_COMBINED_SOURCE_SHA256
    assert binding.runner_sha256 == EXPECTED_RUNNER_SHA256
    assert binding.native_source_sha256 == EXPECTED_NATIVE_SOURCE_SHA256
    assert binding.native_artifact_sha256 == EXPECTED_NATIVE_ARTIFACT_SHA256
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    monkeypatch.setattr(boundary, "EXPECTED_RUNNER_SHA256", "0" * 64)
    with pytest.raises(IntegrityError, match="runner source identity drifted"):
        current_exact_source_binding(load_native=False)


def test_lease_and_initializer_fail_closed_before_master_coordinate_or_model(tmp_path) -> None:
    absent = tmp_path / "no-lease.json"
    with pytest.raises(FileNotFoundError):
        validate_root_lease(absent, load_native=False)
    noncanonical = tmp_path / "fake-lease.json"
    noncanonical.write_text("{}\n", encoding="ascii")
    with pytest.raises(LeaseValidationError, match="canonical"):
        validate_root_lease(noncanonical, load_native=False)
    with pytest.raises((TypeError, AttributeError)):
        initialize_one_worker_parameters(None, None, None, seed_block_index=0)  # type: ignore[arg-type]
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    assert "master_commitment_sha256" not in boundary._LEASE_FIELDS
    assert {"master_source", "master_record_relative_path"} <= boundary._LEASE_FIELDS
    assert {
        "projected_wall_seconds", "production_preflight_sha256",
        "production_preflight_artifact_path", "production_preflight_artifact_file_sha256",
    } <= boundary._LEASE_FIELDS
    assert not any(path.name.endswith((".pt", ".json")) for path in tmp_path.iterdir() if path != noncanonical)


def test_blinded_atomic_frontier_resume_and_no_partial_evaluability() -> None:
    first = BlindedSeedFrontier(0, 0, 0, 0, canonical_sha256([]), "1" * 64, "2" * 64)
    second = BlindedSeedFrontier(0, 1, 1, 384, canonical_sha256(["origin"]), "1" * 64, "2" * 64)
    second.require_successor_of(first)
    assert first.evaluable is False and second.evaluable is False
    with pytest.raises(IntegrityError, match="atomic update boundary"):
        BlindedSeedFrontier(0, 1, 1, 383, canonical_sha256([]), "1" * 64, "2" * 64)
    with pytest.raises(IntegrityError, match="resume successor"):
        replace(second, generation=2).require_successor_of(first)


def test_sealed_preflight_validates_coordinates_atomic_resume_storage_and_leaves_zero_artifacts(tmp_path) -> None:
    before = tuple(tmp_path.iterdir())
    report = run_sealed_test_preflight(tmp_path)
    assert report.coordinate_count == EXPECTED_ARM_INDEPENDENT_ORIGINS_PANEL
    assert report.seed_block_count == 24
    assert report.arm_independent
    assert report.atomic_resume_validated
    assert report.write_once_conflict_validated
    assert report.retained_probe_bytes > 0
    assert report.resume_generation_bytes > 0
    assert report.update512_checkpoint_bytes > 0
    assert report.projected_complete_retained_bytes > (
        24 * (report.resume_generation_bytes + report.update512_checkpoint_bytes)
    )
    assert report.lifecycle_io_wall_seconds >= 0.0
    assert report.lifecycle_io_cpu_seconds >= 0.0
    assert report.projected_complete_retained_bytes <= report.retained_storage_ceiling_bytes
    assert report.retained_storage_ceiling_bytes == 8_589_934_592
    assert report.storage_headroom_valid
    assert report.available_storage_bytes > 0
    assert report.empirical_objects_created == 0
    assert report.probe_cleanup_complete
    assert tuple(tmp_path.iterdir()) == before


def test_exact_future_launch_contract_is_one_worker_full_panel_and_lease_first() -> None:
    contract = exact_future_launch_contract()
    assert contract["width"] == 32
    assert contract["outer_workers"] == 1
    assert contract["native_threads"] == 1
    assert contract["panel_seed_blocks"] == 24
    assert contract["sole_checkpoint_update"] == 512
    assert contract["partial_evaluable"] is False
    assert contract["lease_required_before"] == (
        "master", "coordinates", "parameters", "frontier", "checkpoint", "result"
    )
    assert contract["native_environment_rollout_fallback"] is None
    assert contract["production_launch_command"].endswith("--lease <EXACT_ROOT_LEASE_JSON>")
    assert contract["production_launch_status"] == "IMPLEMENTED_REQUIRES_ROOT_LEASE_AND_CM_ACCEPTANCE"


def test_potential_coordinate_api_is_arm_independent_and_covers_task_action_domains() -> None:
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    parameters = inspect.signature(boundary.EmpiricalCoordinateAdapter.potential).parameters
    assert "arm" not in parameters and "outcome" not in parameters and "branch" not in parameters
    source = inspect.getsource(boundary.EmpiricalCoordinateAdapter.potential)
    for kind in (
        "event_time",
        "detection_uniform",
        "uplink_uniform",
        "base_uniform",
        "action_uniform",
    ):
        assert kind in source
    origin_source = inspect.getsource(boundary.EmpiricalCoordinateAdapter.origin)
    assert '"kind": "base_slot"' in origin_source
    assert '"side": side, "kind": "local_index"' in origin_source


def test_scalar_and_batched_test_only_potential_coordinates_are_exactly_equal() -> None:
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    adapter = boundary.EmpiricalCoordinateAdapter.__new__(boundary.EmpiricalCoordinateAdapter)
    adapter._master = SimpleNamespace(_secret=b"TEST_ONLY_SCALAR_BATCH_COORDS!!"[:32])
    adapter.namespace = "TEST_ONLY|SGSP-RSCF-SCALAR-BATCH"
    scalar = adapter.potential(
        seed_block_index=0,
        phase="TRAINING",
        roster_size=9,
        update_index=7,
        episode_index=3,
        random_variable_kind="action_uniform",
        slot=4,
        sender=5,
    )
    batched = adapter.uniform_grid(
        seed_block_index=0,
        phase="TRAINING",
        roster_size=9,
        update_index=7,
        random_variable_kind="action_uniform",
        episode_indices=np.asarray([[[3]]], dtype=np.uint64),
        slot_indices=np.asarray([[[4]]], dtype=np.uint64),
        sender_indices=np.asarray([[[5]]], dtype=np.uint64),
        receiver_indices=np.asarray([[[0]]], dtype=np.uint64),
    )
    assert batched.shape == (1, 1, 1)
    assert scalar.uniform_01 == float(batched[0, 0, 0])


def test_exact_coordinate_adapter_factory_is_test_only_and_production_inadmissible() -> None:
    adapter = EmpiricalCoordinateAdapter.for_sealed_test_preflight(
        namespace="TEST_ONLY|EXACT-ADAPTER-PROBE",
        secret=b"TEST_ONLY|RSCF_COORDINATE_KEY_00",
    )
    assert type(adapter) is EmpiricalCoordinateAdapter
    assert adapter._test_only is True
    assert adapter.namespace == "TEST_ONLY|EXACT-ADAPTER-PROBE"
    assert adapter.origin(
        seed_block_index=0, update_index=0, roster_size=9,
        pair_index=0, side=0, role_index=0,
    ).seed_block_index == 0
    production_lease = SimpleNamespace(lease_lineage_id="PRODUCTION_LINEAGE")
    production_master = SimpleNamespace(lease_lineage_id="PRODUCTION_LINEAGE")
    with pytest.raises(ProductionBoundaryError, match="coordinate plan was not bound"):
        initialize_one_worker_parameters(
            production_lease, production_master, adapter, seed_block_index=0
        )


def test_windows_dpapi_seals_test_only_master_bytes_without_plaintext_or_fallback() -> None:
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    plaintext = b"TEST_ONLY_MASTER_BYTES_32_LONG!!"[:32]
    entropy = b"TEST_ONLY|SGSP_RSCF_R01|DPAPI"
    ciphertext = boundary._dpapi_protect(plaintext, entropy)
    assert ciphertext != plaintext
    assert plaintext not in ciphertext
    assert boundary._dpapi_unprotect(ciphertext, entropy) == plaintext
    with pytest.raises(OSError):
        boundary._dpapi_unprotect(ciphertext, entropy + b"-WRONG")


def test_generation_scoped_resume_and_checkpoint_ignore_uncommitted_crash_orphans(tmp_path) -> None:
    lease = SimpleNamespace(
        lease_lineage_id="TEST_ONLY_LINEAGE",
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest="b" * 64),
    )
    coordinates = SimpleNamespace(
        _lease_lineage_id="TEST_ONLY_LINEAGE",
        manifest_sha256="a" * 64,
    )
    store = ProductionLifecycleStore(lease, coordinates)  # type: ignore[arg-type]
    orphan_dir = tmp_path / "resume" / "SB00"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "g000001-ORPHAN.pt").write_bytes(b"TEST_ONLY_ORPHAN")
    assert store.latest_resume_frontier(0) is None

    frontier = BlindedSeedFrontier(
        0, 1, 1, 384, canonical_sha256(["TEST_ONLY_ORIGIN"]), "a" * 64, "b" * 64
    )
    store.write_frontier(frontier)
    state = b"TEST_ONLY_FULL_SHAPED_STATE"
    store.write_resume_state(0, 1, state, frontier)
    assert store.latest_resume_frontier(0) == frontier
    assert store.read_resume_state(0, frontier) == state
    assert not (tmp_path / "resume" / "SB00.pt").exists()
    assert not (tmp_path / "resume" / "SB00.json").exists()
    second = BlindedSeedFrontier(
        0, 2, 2, 768, canonical_sha256(["TEST_ONLY_ORIGIN_2"]), "a" * 64, "b" * 64
    )
    third = BlindedSeedFrontier(
        0, 3, 3, 1152, canonical_sha256(["TEST_ONLY_ORIGIN_3"]), "a" * 64, "b" * 64
    )
    store.write_frontier(second)
    store.write_resume_state(0, 2, b"TEST_ONLY_STATE_2", second)
    store.write_frontier(third)
    store.write_resume_state(0, 3, b"TEST_ONLY_STATE_3", third)
    assert store.latest_resume_frontier(0) == third
    assert not (tmp_path / "resume" / "SB00" / "g000001.commit").exists()

    complete = BlindedSeedFrontier(
        0, 512, 512, 196_608, canonical_sha256(["TEST_ONLY_COMPLETE"]), "a" * 64, "b" * 64
    )
    store.write_frontier(complete)
    checkpoint_orphan = tmp_path / "checkpoint" / "SB00" / "ORPHAN.pt"
    checkpoint_orphan.parent.mkdir(parents=True)
    checkpoint_orphan.write_bytes(b"TEST_ONLY_CHECKPOINT_ORPHAN")
    with pytest.raises((FileNotFoundError, IntegrityError)):
        store.read_update512_checkpoint_ref(0)
    reference = store.install_update512_checkpoint(0, b"TEST_ONLY_UPDATE512_STATE", complete)
    assert store.read_update512_checkpoint_ref(0) == reference
    assert (tmp_path / "checkpoint" / "SB00" / "COMMITTED.json").is_file()


def test_test_only_successor_lease_preserves_dpapi_master_lineage_without_plaintext(tmp_path) -> None:
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    common = dict(
        lease_lineage_id="TEST_ONLY_SUCCESSOR_LINEAGE",
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest="c" * 64),
        lease_payload={"master_record_relative_path": "control/master.json"},
    )
    first_lease = SimpleNamespace(**common, lease_payload_sha256="1" * 64)
    successor_lease = SimpleNamespace(**common, lease_payload_sha256="2" * 64)
    first = boundary.mint_or_resume_empirical_master(first_lease)
    successor = boundary.mint_or_resume_empirical_master(successor_lease)
    assert first.commitment_sha256 == successor.commitment_sha256
    assert first.current_lease_payload_sha256 != successor.current_lease_payload_sha256
    record_bytes = (tmp_path / "control" / "master.json").read_bytes()
    assert b"secret_hex" not in record_bytes
    assert first._secret not in record_bytes
    assert b"ciphertext_b64" in record_bytes


def test_authenticated_test_only_seed_result_rejects_ciphertext_tamper(tmp_path) -> None:
    import experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary as boundary
    from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.analysis import QUANTITY_NAMES
    fake_lease = SimpleNamespace(
        lease_lineage_id="TEST_ONLY_AUTH_LINEAGE",
        lease_payload_sha256="d" * 64,
        retained_root=tmp_path,
        source_binding=SimpleNamespace(digest="e" * 64),
    )
    coordinates = SimpleNamespace(
        _lease_lineage_id="TEST_ONLY_AUTH_LINEAGE",
        manifest_sha256="f" * 64,
    )
    master = boundary.BoundEmpiricalMaster(fake_lease, b"TEST_ONLY_AUTH_MASTER_32_BYTES!!"[:32])
    store = ProductionLifecycleStore(fake_lease, coordinates)  # type: ignore[arg-type]
    payload = {
        "schema": "TEST_ONLY_SEED_RESULT_V1",
        "seed_block_index": 0,
        "quantity_vector": {"values": {name: 0.0 for name in QUANTITY_NAMES}},
    }
    reference = store.install_sealed_seed_result(0, payload, master)
    assert store.read_sealed_seed_result_ref(0, master) == reference
    assert store.read_sealed_seed_result(reference, master) == payload
    ciphertext_path = tmp_path / "sealed" / "SB00.bin"
    ciphertext = bytearray(ciphertext_path.read_bytes())
    ciphertext[0] ^= 0x01
    ciphertext_path.write_bytes(ciphertext)
    with pytest.raises(IntegrityError, match="ciphertext changed"):
        store.read_sealed_seed_result_ref(0, master)


def test_preflight_cli_is_executable_leaves_no_empirical_artifact_and_rejects_evidence_tamper(tmp_path) -> None:
    artifact_path = tmp_path.parent / f"{tmp_path.name}-extended-preflight.json"
    completed = subprocess.run(
        [
            "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
            "-m",
            "experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher",
            "--preflight-only",
            "--preflight-root",
            str(tmp_path),
            "--preflight-artifact",
            str(artifact_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"empirical_objects_created":0' in completed.stdout
    assert '"service_graph":["lease_validated","master_created","coordinates_bound","parameters_initialized","lifecycle_bound","engine_bound"]' in completed.stdout
    assert '"test_only_exact_coordinate_tape_wall_seconds":' in completed.stdout
    assert '"test_only_production_update_wall_seconds":' in completed.stdout
    assert '"test_only_production_evaluation_cell_wall_seconds":' in completed.stdout
    assert '"production_projected_wall_seconds":' in completed.stdout
    assert '"production_preflight_sha256":' in completed.stdout
    output = json.loads(completed.stdout)
    assert output["exact_coordinate_adapter_class"].endswith(
        "production_boundary.EmpiricalCoordinateAdapter"
    )
    assert output["exact_coordinate_adapter_test_only"] is True
    assert output["test_only_evaluation_orchestration_overhead_seconds"] == output[
        "test_only_production_evaluation_cell_wall_seconds"
    ]
    assert output["production_preflight_artifact_path"] == str(artifact_path.resolve())
    binding = current_exact_source_binding(load_native=False)
    validated = validate_production_preflight_artifact(
        artifact_path,
        artifact_file_sha256=output["production_preflight_artifact_file_sha256"],
        production_preflight_sha256=output["production_preflight_sha256"],
        projected_wall_seconds=output["production_projected_wall_seconds"],
        source_binding=binding,
        require_exact_retained_path=False,
    )
    assert validated["source_binding_sha256"] == binding.digest
    artifact_bytes = bytearray(artifact_path.read_bytes())
    artifact_bytes[-2] ^= 0x01
    artifact_path.write_bytes(artifact_bytes)
    with pytest.raises(LeaseValidationError, match="file digest mismatch"):
        validate_production_preflight_artifact(
            artifact_path,
            artifact_file_sha256=output["production_preflight_artifact_file_sha256"],
            production_preflight_sha256=output["production_preflight_sha256"],
            projected_wall_seconds=output["production_projected_wall_seconds"],
            source_binding=binding,
            require_exact_retained_path=False,
        )
    assert tuple(tmp_path.iterdir()) == ()


def test_production_cli_invalid_lease_fails_before_any_empirical_artifact(tmp_path) -> None:
    missing = tmp_path / "missing-root-lease.json"
    completed = subprocess.run(
        [
            "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
            "-m",
            "experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_launcher",
            "--lease",
            str(missing),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert tuple(tmp_path.iterdir()) == ()
