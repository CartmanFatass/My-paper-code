from __future__ import annotations

import json

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import source_factored_test_fixture
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_contract import TestAuthority as R06TestAuthority
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_contract import (
    ClaimCoordinate,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_data_plane import (
    SourceFactoredDataPlaneError, TestOnlySourceFactoredDataPlane, validate_resource_observation,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_fork import (
    CausalReplayWorkShell, PolicyStateMode, ReplayRecord, SourceFactoredForkError,
    SourceFactoredForkPlan, TRANSACTION_TO_POLICY_STATE, fork_policy_state, future_address_equality,
)


def test_source_factored_policy_modes_checkpoint_addresses_and_replay_fence() -> None:
    hidden = np.arange(2 * 4 * 128, dtype=np.float64).reshape(2, 4, 128) / 2048
    retain = fork_policy_state(hidden, [0, 1], PolicyStateMode.RETAIN)
    copy = fork_policy_state(hidden, [0, 1], PolicyStateMode.COPY)
    shadow = fork_policy_state(hidden, [0, 1], PolicyStateMode.SHADOW)
    assert np.array_equal(retain, hidden)
    assert np.array_equal(copy[0, 2], hidden[0, 0])
    assert np.array_equal(shadow[0, 2], hidden[0, 3])
    bounded = hidden.copy(); bounded[0, 0, 0] = 1.5; bounded[0, 3, 0] = -1.5
    assert fork_policy_state(bounded, [0, 1], PolicyStateMode.COPY)[0, 2, 0] == 1.0
    assert fork_policy_state(bounded, [0, 1], PolicyStateMode.SHADOW)[0, 2, 0] == -1.0
    assert fork_policy_state(bounded.astype(np.float32), [0, 1], PolicyStateMode.COPY).dtype == np.float32
    addresses = tuple(f"tick/{i}" for i in range(100))
    bindings = SourceFactoredForkPlan(b"checkpoint", b"normalization", b"rng-frontier", addresses).branch_binding()
    assert tuple(TRANSACTION_TO_POLICY_STATE) == ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
    assert tuple(mode.value for mode in TRANSACTION_TO_POLICY_STATE.values()) == ("RETAIN", "COPY", "SHADOW")
    assert len({row["checkpoint_bytes"] for row in bindings.values()}) == 1
    assert future_address_equality({name: row["future_addresses"] for name, row in bindings.items()})
    prefix = (ReplayRecord(8, 0, "snapshot", b"x"), ReplayRecord(9, 0, "message", b"y"))
    replay = CausalReplayWorkShell(9, 10, prefix, prefix, 10)
    assert replay.ordered_work == ((8, 0, "snapshot", b"x"), (9, 0, "message", b"y"))
    with pytest.raises(SourceFactoredForkError, match="forbidden"):
        bad = (ReplayRecord(9, 0, "future_tape", b"x"),)
        CausalReplayWorkShell(9, 10, bad, bad, 10).validate()
    with pytest.raises(SourceFactoredForkError, match="captured"):
        CausalReplayWorkShell(9, 10, prefix, prefix[:-1], 10).validate()
    with pytest.raises(SourceFactoredForkError, match="coordinate"):
        bad = (ReplayRecord(-1, 0, "snapshot", b"x"),)
        CausalReplayWorkShell(9, 10, bad, bad, 10).validate()
    with pytest.raises(SourceFactoredForkError, match="captured"):
        CausalReplayWorkShell(9, 10, (), (), 10).validate()
    with pytest.raises(SourceFactoredForkError, match="completion"):
        CausalReplayWorkShell(9, 10, prefix, prefix, 11).validate()


def test_source_factored_create_only_resume_duplicate_and_firewall(tmp_path) -> None:
    plane = TestOnlySourceFactoredDataPlane(tmp_path)
    coordinate = ClaimCoordinate(0, "TARGET_VISUAL_MASK", "K8", 4, 0)
    resources = {"workers": 8, "cpu_cores": 8, "torch_threads": 1, "gpu": 0,
                 "cpu_hours": 40, "wall_hours": 10, "rss_gib": 6.61, "scratch_gib": 1.66,
                 "durable_gib": .83, "io_gib": 68.14}
    native, step_rows = source_factored_test_fixture(1, R06TestAuthority())
    _, _, native_metadata = native.clone_promotion_source_batches(step_rows)
    receipts = {name: rows[0] for name, rows in native_metadata["raw_receipts"].items()}
    arguments = dict(
        coordinate=coordinate, native_snapshot=native.snapshot_bytes(), rollout_welford=b"rollout",
        checkpoint=b"checkpoint", rng_frontier=b"rng",
        receipts=receipts, resource_observation=resources,
    )
    staging = plane._staging_root(coordinate); staging.parent.mkdir(parents=True, exist_ok=True)
    (staging.parent / f".{staging.name}.manifest.json.crashed.request-private").write_bytes(b'{"partial"')
    (staging.parent / f".{staging.name}.checkpoint.bin.crashed.request-private").write_bytes(b"check")
    with pytest.raises(SourceFactoredDataPlaneError, match="injected"):
        plane.create_generation(**arguments, _test_fail_after_staged_files=2)
    assert not plane._coordinate_root(coordinate).exists()
    with pytest.raises(SourceFactoredDataPlaneError, match="byte mismatch"):
        plane.create_generation(**dict(arguments, checkpoint=b"checkpoint-more"))
    manifest = plane.create_generation(**arguments)
    assert plane.resume_exact(coordinate) == manifest
    with pytest.raises(SourceFactoredDataPlaneError, match="cannot be forked again"):
        plane.create_generation(**arguments)
    with pytest.raises(SourceFactoredDataPlaneError, match="firewall"):
        plane.complete_result(coordinate)
    assert validate_resource_observation(resources)["io_gib"] == 68.14
    with pytest.raises(SourceFactoredDataPlaneError, match="not finite"):
        validate_resource_observation(dict(resources, io_gib=float("nan")))
    with pytest.raises(SourceFactoredDataPlaneError, match="type differs"):
        validate_resource_observation(dict(resources, workers=True))
    with pytest.raises(SourceFactoredDataPlaneError, match="type differs"):
        validate_resource_observation(dict(resources, io_gib="68.14"))
    manifest_path = plane._coordinate_root(coordinate) / "manifest.json"
    raw_manifest = manifest_path.read_bytes()
    extra_file = plane._coordinate_root(coordinate) / "complete_result"
    extra_file.write_bytes(b"forbidden")
    with pytest.raises(SourceFactoredDataPlaneError, match="file inventory"):
        plane.resume_exact(coordinate)
    extra_file.unlink()
    tampered = json.loads(raw_manifest); tampered["extra"] = False
    manifest_path.write_bytes((json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
    with pytest.raises(SourceFactoredDataPlaneError, match="direct binding differs"):
        plane.resume_exact(coordinate)
    manifest_path.write_bytes(raw_manifest)
    tampered = json.loads(raw_manifest); first_payload = next(iter(tampered["payload_hex"]))
    tampered["payload_hex"][first_payload] = tampered["payload_hex"][first_payload].upper()
    manifest_path.write_bytes((json.dumps(tampered, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))
    with pytest.raises(SourceFactoredDataPlaneError, match="lowercase"):
        plane.resume_exact(coordinate)
    manifest_path.write_bytes(json.dumps(json.loads(raw_manifest), indent=2).encode("ascii"))
    with pytest.raises(SourceFactoredDataPlaneError, match="canonical manifest"):
        plane.resume_exact(coordinate)
    duplicate = raw_manifest.replace(b"{", b'{"sealed":true,', 1)
    manifest_path.write_bytes(duplicate)
    with pytest.raises(SourceFactoredDataPlaneError, match="duplicate"):
        plane.resume_exact(coordinate)


def test_source_factored_staged_byte_mismatch_refuses_retry(tmp_path) -> None:
    plane = TestOnlySourceFactoredDataPlane(tmp_path)
    coordinate = ClaimCoordinate(1, "TARGET_VISUAL_MASK", "K8", 4, 0)
    native, step_rows = source_factored_test_fixture(1, R06TestAuthority())
    _, _, metadata = native.clone_promotion_source_batches(step_rows)
    resources = {"workers": 8, "cpu_cores": 8, "torch_threads": 1, "gpu": 0,
                 "cpu_hours": 40, "wall_hours": 10, "rss_gib": 6.61, "scratch_gib": 1.66,
                 "durable_gib": .83, "io_gib": 68.14}
    arguments = dict(
        coordinate=coordinate, native_snapshot=native.snapshot_bytes(), rollout_welford=b"rollout",
        checkpoint=b"checkpoint", rng_frontier=b"rng",
        receipts={name: rows[0] for name, rows in metadata["raw_receipts"].items()},
        resource_observation=resources,
    )
    with pytest.raises(SourceFactoredDataPlaneError, match="injected"):
        plane.create_generation(**arguments, _test_fail_after_staged_files=1)
    changed = dict(arguments, checkpoint=b"checkpoint-more")
    with pytest.raises(SourceFactoredDataPlaneError, match="byte mismatch"):
        plane.create_generation(**changed)
    (plane._staging_root(coordinate) / "native_snapshot.bin").write_bytes(b"mismatch")
    with pytest.raises(SourceFactoredDataPlaneError, match="byte mismatch"):
        plane.create_generation(**arguments)
