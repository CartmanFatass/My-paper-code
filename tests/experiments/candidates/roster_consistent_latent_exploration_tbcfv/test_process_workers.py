from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil

import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.process_workers import (
    CANONICAL_DURABLE_CEILING,
    CHECKPOINT_READ_CEILING,
    CHECKPOINT_WRITE_CEILING,
    CPU_HOURS_CEILING,
    FOUR_PROCESS_WALL_HOURS_CEILING,
    PRIVATE_SCRATCH_COMBINED_CEILING,
    PROCESS_GROUP_RSS_CEILING,
    ProcessWorkerError,
    canonical_json_bytes,
    make_process_resource_object,
    make_spawn_payload,
    make_worker_authorization,
    parent_install_test_packets,
    run_test_only_spawn_worker,
    run_production_block_worker,
    tree_size_bytes,
    validate_process_resource_object,
    validate_production_worker_packet,
    validate_parent_authorized_spawn_payload,
    validate_spawn_payload,
    validate_test_worker_packet,
    validate_worker_authorization,
    write_spawn_payload,
)


SOURCE = "1" * 64
NATIVE = "2" * 64
NATIVE_SOURCE = "3" * 64
BUILD = "4" * 64


def _resource(tmp_path: Path, label: str = "run") -> dict[str, object]:
    base = tmp_path / label
    return make_process_resource_object(
        canonical_result_root=base / "canonical",
        private_scratch_roots=[base / f"scratch_{index}" for index in range(4)],
        source_set_sha256=SOURCE,
        native_binding_sha256=NATIVE,
    )


def _payload(resource: dict[str, object], block_index: int) -> dict[str, object]:
    return make_spawn_payload(
        resource,
        block_index=block_index,
        block_root_digest=f"{block_index + 10:064x}",
        native_source_sha256=NATIVE_SOURCE,
        native_build_key=BUILD,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        test_only=True,
        test_steps=4,
    )


def _run_spawn_set(
    tmp_path: Path, workers: int
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    resource = _resource(tmp_path, f"w{workers}")
    payloads = [_payload(resource, block_index) for block_index in range(4)]
    authorizations = [
        make_worker_authorization(resource, payload) for payload in payloads
    ]
    payload_paths: list[Path] = []
    for block_index, payload in enumerate(payloads):
        path = tmp_path / f"payload_w{workers}_{block_index}.json"
        write_spawn_payload(path, payload)
        payload_paths.append(path)
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as pool:
        rows = list(
            pool.map(
                run_test_only_spawn_worker,
                map(str, payload_paths),
                authorizations,
            )
        )
    return resource, payloads, rows


def test_exact_resource_schema_and_all_authorized_ceilings(tmp_path: Path) -> None:
    resource = _resource(tmp_path)
    assert validate_process_resource_object(resource) == resource
    assert resource["limits"] == {
        "projected_complete_panel_cpu_hours_upper": CPU_HOURS_CEILING,
        "projected_four_process_wall_hours_upper": FOUR_PROCESS_WALL_HOURS_CEILING,
        "max_workers": 4,
        "spawn_processes": True,
        "one_thread_per_worker": True,
        "process_group_rss_bytes_upper": PROCESS_GROUP_RSS_CEILING,
        "private_scratch_combined_bytes_upper": PRIVATE_SCRATCH_COMBINED_CEILING,
        "canonical_durable_bytes_upper": CANONICAL_DURABLE_CEILING,
        "ordinary_checkpoint_read_bytes_upper": CHECKPOINT_READ_CEILING,
        "ordinary_checkpoint_write_bytes_upper": CHECKPOINT_WRITE_CEILING,
    }
    assert resource["production_activity_authorized"] is False
    assert resource["lease_scope"] == "FUTURE_ROOT_LEASE_REQUIRED"
    assert list(resource["paths"]) == [
        f"lease_scoped_worker_private_scratch_root_{index:02d}"
        for index in range(4)
    ]
    assert len(resource["private_root_digests"]) == 4
    assert len(set(resource["private_root_digests"])) == 4


def test_resource_rejects_overlap_duplicate_and_limit_drift(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical"
    with pytest.raises(ProcessWorkerError, match="overlaps"):
        make_process_resource_object(
            canonical_result_root=canonical,
            private_scratch_roots=[canonical / "worker0", *(tmp_path / f"s{i}" for i in range(1, 4))],
            source_set_sha256=SOURCE,
            native_binding_sha256=NATIVE,
        )
    duplicate = [tmp_path / "same", tmp_path / "same", tmp_path / "s2", tmp_path / "s3"]
    with pytest.raises(ProcessWorkerError, match="distinct"):
        make_process_resource_object(
            canonical_result_root=canonical,
            private_scratch_roots=duplicate,
            source_set_sha256=SOURCE,
            native_binding_sha256=NATIVE,
        )
    resource = _resource(tmp_path, "drift")
    tampered = json.loads(json.dumps(resource))
    tampered["limits"]["max_workers"] = 8
    with pytest.raises(ProcessWorkerError, match="digest"):
        validate_process_resource_object(tampered)


def test_spawn_payload_has_one_block_and_no_canonical_paths(tmp_path: Path) -> None:
    resource = _resource(tmp_path)
    payload = _payload(resource, 7)
    authorization = make_worker_authorization(resource, payload)
    assert validate_spawn_payload(payload) == payload
    serialized = canonical_json_bytes(payload).decode("ascii")
    assert str(resource["canonical_result_root"]) not in serialized
    assert "frontier" not in serialized.lower()
    assert "result_root" not in serialized.lower()
    assert payload["block_index"] == 7
    assert payload["private_scratch_slot"] == 3
    assert payload["canonical_paths_present"] is False
    child_bytes = canonical_json_bytes(authorization)
    assert str(resource["canonical_result_root"]).encode("utf-8") not in child_bytes
    selected = str(payload["private_scratch_root"])
    for root in resource["paths"].values():
        if str(root) != selected:
            assert str(root).encode("utf-8") not in child_bytes


def test_parent_authorized_resource_rejects_scratch_and_canonical_substitution(
    tmp_path: Path,
) -> None:
    resource = _resource(tmp_path, "authorized")
    payload = _payload(resource, 0)
    tampered = json.loads(json.dumps(payload))
    substituted = str(resource["canonical_result_root"])
    tampered["private_scratch_root"] = substituted
    tampered["private_scratch_root_sha256"] = hashlib.sha256(
        substituted.encode("utf-8")
    ).hexdigest()
    body = {key: value for key, value in tampered.items() if key != "payload_sha256"}
    tampered["payload_sha256"] = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    with pytest.raises(ProcessWorkerError, match="parent-authorized"):
        validate_parent_authorized_spawn_payload(tampered, resource)
    authorization = make_worker_authorization(resource, payload)
    damaged_authorization = json.loads(json.dumps(authorization))
    damaged_authorization["private_scratch_root"] = substituted
    damaged_authorization["private_scratch_root_sha256"] = hashlib.sha256(
        substituted.encode("utf-8")
    ).hexdigest()
    auth_body = {
        key: value
        for key, value in damaged_authorization.items()
        if key != "authorization_sha256"
    }
    damaged_authorization["authorization_sha256"] = hashlib.sha256(
        canonical_json_bytes(auth_body)
    ).hexdigest()
    with pytest.raises(ProcessWorkerError, match="exact one-block"):
        validate_worker_authorization(damaged_authorization, payload)


def test_create_only_payload_publish_never_replaces_existing_bytes(tmp_path: Path) -> None:
    resource = _resource(tmp_path, "exclusive")
    payload = _payload(resource, 0)
    target = write_spawn_payload(tmp_path / "payload.json", payload)
    before = target.read_bytes()
    with pytest.raises(ProcessWorkerError, match="create-only"):
        write_spawn_payload(target, payload)
    assert target.read_bytes() == before


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_spawned_1_2_4_processes_are_packet_equivalent(tmp_path: Path, workers: int) -> None:
    resource, payloads, rows = _run_spawn_set(tmp_path, workers)
    assert [row["block_index"] for row in rows] == [0, 1, 2, 3]
    observed = [
        validate_test_worker_packet(
            row["packet_path"], payload, authorized_resource=resource
        )
        for row, payload in zip(rows, payloads)
    ]
    assert [row["block_index"] for row in observed] == [0, 1, 2, 3]
    assert all(row["one_thread"] is True for row in observed)
    assert all(row["test_only"] is True and row["result_blind"] is True for row in observed)


def test_private_failure_is_atomic_and_exact_same_scratch_resumes(tmp_path: Path) -> None:
    resource = _resource(tmp_path, "failure")
    payload = _payload(resource, 3)
    authorization = make_worker_authorization(resource, payload)
    payload_path = write_spawn_payload(tmp_path / "failure_payload.json", payload)
    canonical = Path(str(resource["canonical_result_root"]))
    with ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn")) as pool:
        future = pool.submit(
            run_test_only_spawn_worker,
            str(payload_path),
            authorization,
            inject_failure_after_step=2,
        )
        with pytest.raises(ProcessWorkerError, match="injected"):
            future.result()
    checkpoint = Path(str(payload["private_scratch_root"])) / "block_03" / "checkpoint.json"
    assert checkpoint.is_file()
    assert not (checkpoint.parent / "complete_packet").exists()
    assert not canonical.exists()
    with ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn")) as pool:
        resumed = pool.submit(
            run_test_only_spawn_worker, str(payload_path), authorization
        ).result()
    accepted = validate_test_worker_packet(
        resumed["packet_path"], payload, authorized_resource=resource
    )
    assert accepted["steps_completed"] == 4
    assert not canonical.exists()


@pytest.mark.parametrize(
    ("field", "replacement", "match"),
    [
        ("source_set_sha256", "f" * 64, "source"),
        ("block_index", 9, "block"),
        ("block_root_digest", "e" * 64, "block"),
        ("steps_completed", 3, "counts"),
    ],
)
def test_parent_rejects_wrong_source_block_digest_and_count(
    tmp_path: Path, field: str, replacement: object, match: str
) -> None:
    resource = _resource(tmp_path, field)
    payload = _payload(resource, 0)
    authorization = make_worker_authorization(resource, payload)
    payload_path = write_spawn_payload(tmp_path / f"{field}.payload.json", payload)
    row = run_test_only_spawn_worker(str(payload_path), authorization)
    packet = Path(str(row["packet_path"]))
    damaged = tmp_path / f"damaged_{field}"
    shutil.copytree(packet, damaged)
    manifest_path = damaged / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    manifest[field] = replacement
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    with pytest.raises(ProcessWorkerError, match=match):
        validate_test_worker_packet(damaged, payload, authorized_resource=resource)


def test_parent_rejects_checkpoint_byte_digest_tamper(tmp_path: Path) -> None:
    resource = _resource(tmp_path, "checkpoint_digest")
    payload = _payload(resource, 0)
    authorization = make_worker_authorization(resource, payload)
    payload_path = write_spawn_payload(tmp_path / "checkpoint_digest.payload.json", payload)
    row = run_test_only_spawn_worker(str(payload_path), authorization)
    damaged = tmp_path / "damaged_checkpoint_digest"
    shutil.copytree(row["packet_path"], damaged)
    checkpoint_path = damaged / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="ascii"))
    checkpoint["rolling_sha256"] = "f" * 64
    checkpoint_path.write_bytes(canonical_json_bytes(checkpoint))
    manifest_path = damaged / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    manifest["checkpoint_sha256"] = hashlib.sha256(
        canonical_json_bytes(checkpoint)
    ).hexdigest()
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    with pytest.raises(ProcessWorkerError, match="final rolling"):
        validate_test_worker_packet(damaged, payload, authorized_resource=resource)


def test_parent_validates_all_before_exact_ordered_install(tmp_path: Path) -> None:
    resource, payloads, rows = _run_spawn_set(tmp_path, 4)
    bad = tmp_path / "bad_packet"
    shutil.copytree(rows[2]["packet_path"], bad)
    manifest_path = bad / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    manifest["steps_completed"] = 3
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    packets = [(row["packet_path"], payload) for row, payload in zip(rows, payloads)]
    packets[2] = (bad, payloads[2])
    canonical = Path(str(resource["canonical_result_root"]))
    substituted = tmp_path / "substituted_canonical"
    with pytest.raises(ProcessWorkerError, match="canonical root is not parent-authorized"):
        parent_install_test_packets(
            substituted,
            [(row["packet_path"], payload) for row, payload in zip(rows, payloads)],
            authorized_resource=resource,
        )
    assert not substituted.exists()
    with pytest.raises(ProcessWorkerError, match="counts"):
        parent_install_test_packets(
            canonical, tuple(reversed(packets)), authorized_resource=resource
        )
    assert not canonical.exists()

    report = parent_install_test_packets(
        canonical,
        tuple(reversed([(row["packet_path"], payload) for row, payload in zip(rows, payloads)])),
        authorized_resource=resource,
    )
    assert report["ordered_block_indices"] == [0, 1, 2, 3]
    assert report["parent_pid"] == os.getpid()
    assert all(row["installed_by_pid"] == os.getpid() for row in report["installed"])
    assert report["all_packets_validated_before_install"] is True
    assert report["failure_atomic_parent_tree_install"] is True
    assert (canonical / "block_00" / "manifest.json").is_file()
    assert (canonical / "block_00" / "checkpoint.json").is_file()


def test_test_lifecycle_storage_is_bounded_and_worker_roots_disjoint(tmp_path: Path) -> None:
    resource, payloads, rows = _run_spawn_set(tmp_path, 4)
    roots = {Path(str(payload["private_scratch_root"])).resolve() for payload in payloads}
    assert len(roots) == 4
    total_private = sum(tree_size_bytes(root) for root in roots)
    assert total_private == sum(int(row["private_bytes"]) for row in rows)
    assert total_private < PRIVATE_SCRATCH_COMBINED_CEILING
    canonical = Path(str(resource["canonical_result_root"]))
    parent_install_test_packets(
        canonical,
        [(row["packet_path"], payload) for row, payload in zip(rows, payloads)],
        authorized_resource=resource,
    )
    assert tree_size_bytes(canonical) < CANONICAL_DURABLE_CEILING


def _production_context(payload: dict[str, object]) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": "RCLE_TBCFV_R04_CLOSED_ONE_BLOCK_PRODUCTION_CONTEXT_V1",
        "block_index": payload["block_index"],
        "identity": "RCLE-TBCFV-R04-FULL-PANEL-20260821-01",
        "coordinate_binding_sha256": "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915",
        "master_digest": "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2",
        "block_root_digest": payload["block_root_digest"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "native_source_sha256": payload["native_source_sha256"],
        "native_build_key": payload["native_build_key"],
        "native_artifact_sha256": "5" * 64,
        "empirical_bindings": {
            "source_manifest_sha256": payload["source_set_sha256"],
            "config_sha256": "6" * 64,
            "native_binding_sha256": payload["native_binding_sha256"],
            "coordinate_digest": "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915",
            "master_digest": "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2",
            "origin_lease_id": "ORIGIN-LEASE",
            "lease_id": "ORIGIN-LEASE",
            "lease_binding_sha256": "7" * 64,
        },
        "origin_lease_id": "ORIGIN-LEASE",
        "stage_binding_sha256": "7" * 64,
        "accepted_binding_sha256": "8" * 64,
        "preactivity_certificate_sha256": "9" * 64,
        "coordinate_proposal_sha256": "a" * 64,
        "lease_document_sha256": "b" * 64,
        "lease_validated_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "one_thread": True,
        "gpu_count": 0,
        "canonical_paths_present": False,
        "result_blind": True,
        "protocol_canary": False,
        "protocol_canary_failure_once": False,
    }
    return {
        **body,
        "context_sha256": hashlib.sha256(canonical_json_bytes(body)).hexdigest(),
    }


def test_production_worker_uses_private_frontier_and_emits_complete_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_runner as runner

    resource = _resource(tmp_path, "production")
    payload = make_spawn_payload(
        resource,
        block_index=0,
        block_root_digest="c" * 64,
        native_source_sha256=NATIVE_SOURCE,
        native_build_key=BUILD,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        test_only=False,
        test_steps=1,
    )
    context = _production_context(payload)
    authorization = make_worker_authorization(
        resource, payload, production_context=context
    )
    child_bytes = canonical_json_bytes(authorization)
    assert str(resource["canonical_result_root"]).encode("utf-8") not in child_bytes
    selected = str(payload["private_scratch_root"])
    for root in resource["paths"].values():
        if str(root) != selected:
            assert str(root).encode("utf-8") not in child_bytes

    def complete_synthetic_block(frontier, _authority, block_index, *, now):
        del now
        runtime = runner._new_block_runtime(runner.SyntheticTestRNG())
        runtime.phase = "BLOCK_COMPLETE"
        runtime.updates = {arm: 800 for arm in runner.LEARNED_PACKAGES}
        runtime.learned_completed = {
            arm: {cell: 2_048 for cell in runner.HELDOUT_CELLS}
            for arm in runner.LEARNED_PACKAGES
        }
        runtime.scripted_completed = {
            package: {cell: 2_048 for cell in runner.HELDOUT_CELLS}
            for package in runner.SCRIPTED_PACKAGES
        }
        for family in runtime.aggregates.values():
            for owner in family.values():
                for cell in owner.values():
                    cell["episodes"] = 2_048
        runtime.counts = dict(runner.BLOCK_COUNTS)
        runner._persist_runtime(frontier, block_index, runtime)
        return frontier.seal_block(block_index, owner_token=runner.OWNER_TOKEN)

    monkeypatch.setattr(runner, "execute_run_block", complete_synthetic_block)
    payload_path = write_spawn_payload(tmp_path / "production_payload.json", payload)
    row = run_production_block_worker(str(payload_path), authorization)
    assert int(row["process_lifetime_peak_rss_bytes"]) > 0
    manifest = validate_production_worker_packet(
        row["packet_path"], payload, worker_authorization=authorization
    )
    assert manifest["block_index"] == 0
    assert manifest["test_only"] is False
    assert manifest["counts"] == runner.BLOCK_COUNTS
    assert not Path(str(resource["canonical_result_root"])).exists()


def test_production_worker_failure_resumes_same_private_frontier_and_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import empirical_runner as runner

    resource = _resource(tmp_path, "production-resume")
    payload = make_spawn_payload(
        resource,
        block_index=0,
        block_root_digest="d" * 64,
        native_source_sha256=NATIVE_SOURCE,
        native_build_key=BUILD,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        test_only=False,
        test_steps=1,
    )
    context = _production_context(payload)
    authorization = make_worker_authorization(
        resource, payload, production_context=context
    )
    payload_path = write_spawn_payload(tmp_path / "production_resume_payload.json", payload)
    observed: dict[str, object] = {}

    def fail_after_private_generation(frontier, _authority, block_index, *, now):
        del now
        runtime = runner._new_block_runtime(runner.SyntheticTestRNG())
        runner._persist_runtime(frontier, block_index, runtime)
        raise RuntimeError("injected after private generation")

    monkeypatch.setattr(runner, "execute_run_block", fail_after_private_generation)
    with pytest.raises(RuntimeError, match="injected after private generation"):
        run_production_block_worker(str(payload_path), authorization)
    private_block_base = Path(str(payload["private_scratch_root"])) / "b00"
    generations_before = tuple(sorted((private_block_base / "f" / "blocks" / "block_00" / "resume").glob("generation_*.json")))
    assert len(generations_before) == 1
    assert not (private_block_base / "production_complete_packet").exists()
    assert not Path(str(resource["canonical_result_root"])).exists()

    def complete_after_resume(frontier, _authority, block_index, *, now):
        del now
        runtime = runner._restore_runtime(frontier, block_index)
        assert runtime is not None
        observed["resumed_phase"] = runtime.phase
        runtime.phase = "BLOCK_COMPLETE"
        runtime.updates = {arm: 800 for arm in runner.LEARNED_PACKAGES}
        runtime.learned_completed = {
            arm: {cell: 2_048 for cell in runner.HELDOUT_CELLS}
            for arm in runner.LEARNED_PACKAGES
        }
        runtime.scripted_completed = {
            package: {cell: 2_048 for cell in runner.HELDOUT_CELLS}
            for package in runner.SCRIPTED_PACKAGES
        }
        for family in runtime.aggregates.values():
            for owner in family.values():
                for cell in owner.values():
                    cell["episodes"] = 2_048
        runtime.counts = dict(runner.BLOCK_COUNTS)
        runner._persist_runtime(frontier, block_index, runtime)
        return frontier.seal_block(block_index, owner_token=runner.OWNER_TOKEN)

    monkeypatch.setattr(runner, "execute_run_block", complete_after_resume)
    row = run_production_block_worker(str(payload_path), authorization)
    assert int(row["process_lifetime_peak_rss_bytes"]) > 0
    manifest = validate_production_worker_packet(
        row["packet_path"], payload, worker_authorization=authorization
    )
    assert observed["resumed_phase"] == "TRAINING"
    assert manifest["payload_sha256"] == payload["payload_sha256"]
    assert manifest["counts"] == runner.BLOCK_COUNTS
    generations_after = tuple(sorted((private_block_base / "f" / "blocks" / "block_00" / "resume").glob("generation_*.json")))
    assert len(generations_after) == 2
    assert generations_before[0].read_bytes() == generations_after[0].read_bytes()
    assert not Path(str(resource["canonical_result_root"])).exists()
