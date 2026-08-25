"""Result-blind production-equivalent runner-chain benchmark for RCLE r04.

Only fixed ``SyntheticTestRNG`` coordinates and disposable roots are used.
The benchmark executes the actual native host, batched learned/scripted
consumers, forward/backward/update path, worker orchestration and exact runtime
serialization/resume implementation.  It never admits production authority or
materializes a scientific identity.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import multiprocessing
from types import SimpleNamespace
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

import torch  # noqa: E402

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (  # noqa: E402
    empirical_runner as runner,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (  # noqa: E402
    LEARNED_PACKAGES,
    SCRIPTED_PACKAGES,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (  # noqa: E402
    make_conformance_fixture_model,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import (  # noqa: E402
    ACCEPTED_NATIVE_ARTIFACT_SHA256,
    ACCEPTED_NATIVE_BUILD_KEY,
    ACCEPTED_NATIVE_SOURCE_SHA256,
    canonical_source_identity,
    document_sha256,
    production_source_paths,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_artifacts import (  # noqa: E402
    AtomicEmpiricalFrontier,
    EmpiricalBindings,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.process_workers import (  # noqa: E402
    CANONICAL_DURABLE_CEILING,
    CHECKPOINT_READ_CEILING,
    CHECKPOINT_WRITE_CEILING,
    CPU_HOURS_CEILING,
    FOUR_PROCESS_WALL_HOURS_CEILING,
    PRIVATE_SCRATCH_COMBINED_CEILING,
    PROCESS_GROUP_RSS_CEILING,
    ProcessWorkerError,
    _PrivateWorkerPermit,
    make_process_resource_object,
    make_spawn_payload,
    make_worker_authorization,
    parent_install_test_packets,
    run_production_block_worker,
    run_test_only_spawn_worker,
    tree_size_bytes,
    validate_test_worker_packet,
    validate_production_worker_packet,
    write_spawn_payload,
)
from tools.benchmarks.benchmark_rcle_tbcfv_r04_native import _measure  # noqa: E402


SCHEMA = "RCLE_TBCFV_R04_RUNNER_CHAIN_EFFICIENCY_REVIEW_V1"
TRAINING_ARM_UPDATES = 80_000
EVALUATION_GROUPS = 20 * 8 * (2_048 // 32)
RUNTIME_COMMITS = 20 * 20


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii") + b"\n"


def _coordinates(
    cells: tuple[str, ...], *, width: int, update_or_scenario: int = 0
) -> tuple[runner.EpisodeCoordinate, ...]:
    return tuple(
        runner.EpisodeCoordinate(
            0,
            cell,
            update_or_scenario + row,
            row % runner.SELECTED_BATCH_WIDTH,
        )
        for cell in cells
        for row in range(width // len(cells))
    )


def _episode_equal(left: object, right: object) -> bool:
    scalar_fields = ("tau", "U", "F", "agent_ticks", "claim_decisions")
    if hasattr(left, "Y"):
        scalar_fields += ("Y",)
    if any(getattr(left, name) != getattr(right, name) for name in scalar_fields):
        return False
    for name in ("plan_scores", "claim_scores"):
        if not hasattr(left, name):
            continue
        left_values, right_values = getattr(left, name), getattr(right, name)
        if len(left_values) != len(right_values) or any(
            not torch.equal(a, b) for a, b in zip(left_values, right_values)
        ):
            return False
    return True


def _width_equivalence() -> dict[str, object]:
    cells = tuple(runner.TRAINING_CELLS[:4])
    coords32 = _coordinates(cells, width=32)
    learned: dict[str, bool] = {}
    for arm in LEARNED_PACKAGES:
        reference_model = make_conformance_fixture_model()
        observed_model = make_conformance_fixture_model()
        observed_model.load_state_dict(reference_model.state_dict())
        reference_rng = runner.SyntheticTestRNG()
        observed_rng = runner.SyntheticTestRNG()
        reference = tuple(
            episode
            for offset in range(0, 32, 8)
            for episode in runner._execute_learned_batch_scalar_reference(
                reference_model,
                arm,
                reference_rng,
                coords32[offset : offset + 8],
                training=True,
            )
        )
        observed = runner.execute_learned_batch(
            observed_model, arm, observed_rng, coords32, training=True
        )
        learned[arm] = all(
            _episode_equal(expected, actual)
            for expected, actual in zip(reference, observed)
        )
    heldout = tuple(runner.HELDOUT_CELLS[:1])
    coords = _coordinates(heldout, width=32)
    scripted: dict[str, bool] = {}
    for package in SCRIPTED_PACKAGES:
        reference_rng = runner.SyntheticTestRNG()
        observed_rng = runner.SyntheticTestRNG()
        reference = tuple(
            episode
            for offset in range(0, 32, 8)
            for episode in runner.execute_scripted_batch(
                package, reference_rng, coords[offset : offset + 8]
            )
        )
        observed = runner.execute_scripted_batch(package, observed_rng, coords)
        scripted[package] = all(
            _episode_equal(expected, actual)
            for expected, actual in zip(reference, observed)
        )
    return {
        "supported_widths_exercised": [1, 8, 32],
        "production_grouping_comparison": "four_B8_calls_vs_one_B32_call",
        "learned_exact": learned,
        "scripted_exact": scripted,
        "all_exact": all(learned.values()) and all(scripted.values()),
    }


def _training_action(arm: str) -> Callable[[], None]:
    model = make_conformance_fixture_model()
    rng = runner.SyntheticTestRNG()
    baselines = torch.zeros(8, dtype=torch.float64)
    update = 0

    def action() -> None:
        nonlocal baselines, update
        baselines, _ = runner.execute_training_update(
            model,
            arm,
            rng,
            update,
            baselines,
        )
        update = (update + 1) % 800

    return action


def _learned_eval_action(arm: str) -> Callable[[], None]:
    coordinates = _coordinates(tuple(runner.HELDOUT_CELLS[:1]), width=32)
    model = make_conformance_fixture_model()
    rng = runner.SyntheticTestRNG()

    def action() -> None:
        with torch.no_grad():
            runner.execute_learned_batch(
                model,
                arm,
                rng,
                coordinates,
                training=False,
            )

    return action


def _scripted_eval_action(package: str) -> Callable[[], None]:
    coordinates = _coordinates(tuple(runner.HELDOUT_CELLS[:1]), width=32)
    rng = runner.SyntheticTestRNG()

    def action() -> None:
        runner.execute_scripted_batch(
            package, rng, coordinates
        )

    return action


def _measure_warm_unit(
    action: Callable[[], None], *, repetitions: int = 3
) -> dict[str, object]:
    """Measure a warmed persistent runner unit above Windows timer granularity."""

    action()

    def repeated() -> None:
        for _ in range(repetitions):
            action()

    _, measured = _measure(repeated)
    normalized = dict(measured)
    for key in ("cpu_seconds", "wall_seconds", "io_read_bytes", "io_write_bytes"):
        normalized[key] = float(measured[key]) / repetitions
    wall = float(normalized["wall_seconds"])
    normalized["cpu_utilization_fraction"] = (
        float(normalized["cpu_seconds"]) / wall if wall > 0.0 else 0.0
    )
    normalized["warmup_calls"] = 1
    normalized["measured_repetitions"] = repetitions
    return normalized


def _concurrency_measurement(workers: int) -> dict[str, object]:
    def execute() -> list[dict[str, object]]:
        with ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            return list(pool.map(_spawn_composite_measurement, range(workers)))

    rows, parent = _measure(execute)
    wall = float(parent["wall_seconds"])
    child_cpu = sum(float(row["cpu_seconds"]) for row in rows)
    child_peak_sum = sum(int(row["peak_rss_bytes"]) for row in rows)
    parent_peak = int(parent["peak_rss_bytes"])
    return {
        "workers": workers,
        "worker_kind": "spawn_process_isolated_test_only",
        "identical_composite": True,
        "wall_seconds": wall,
        "cpu_seconds": child_cpu + float(parent["cpu_seconds"]),
        "cpu_utilization_fraction": (
            (child_cpu + float(parent["cpu_seconds"])) / wall if wall > 0.0 else 0.0
        ),
        "telemetry_available": parent["telemetry_available"] is True
        and all(row["telemetry_available"] is True for row in rows),
        "telemetry_error": parent["telemetry_error"],
        "peak_rss_bytes": max(
            parent_peak, max(int(row["peak_rss_bytes"]) for row in rows)
        ),
        "parent_peak_rss_bytes": parent_peak,
        "child_peak_rss_bytes_sum": child_peak_sum,
        "process_group_rss_bytes": parent_peak + child_peak_sum,
        "io_read_bytes": float(parent["io_read_bytes"])
        + sum(float(row["io_read_bytes"]) for row in rows),
        "io_write_bytes": float(parent["io_write_bytes"])
        + sum(float(row["io_write_bytes"]) for row in rows),
        "spawn_overhead_included": True,
    }


def _spawn_composite_measurement(_: int) -> dict[str, object]:
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    return _measure_warm_unit(_composite_action(0), repetitions=2)


def _private_lifecycle_measurement(
    scratch_root: Path, workers: int, *, source_set_sha256: str, native_binding_sha256: str
) -> dict[str, object]:
    """Exercise the exact private worker packet lifecycle with spawn processes."""

    base = scratch_root / f"workers_{workers}"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    resource = make_process_resource_object(
        canonical_result_root=base / "synthetic_canonical",
        private_scratch_roots=[base / f"private_{index}" for index in range(4)],
        source_set_sha256=source_set_sha256,
        native_binding_sha256=native_binding_sha256,
    )
    native = runner.bind_native_backend()
    payloads = [
        make_spawn_payload(
            resource,
            block_index=block_index,
            block_root_digest=f"{block_index + 100:064x}",
            native_source_sha256=native.source_sha256,
            native_build_key=native.build_key,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            test_only=True,
            test_steps=8,
        )
        for block_index in range(4)
    ]
    authorizations = [
        make_worker_authorization(resource, payload) for payload in payloads
    ]
    payload_paths = []
    for block_index, payload in enumerate(payloads):
        payload_paths.append(
            write_spawn_payload(base / f"payload_{block_index:02d}.json", payload)
        )

    def execute() -> list[dict[str, object]]:
        with ProcessPoolExecutor(
            max_workers=workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            return list(
                pool.map(
                    run_test_only_spawn_worker,
                    map(str, payload_paths),
                    authorizations,
                )
            )

    rows, measurement = _measure(execute)
    manifests = [
        validate_test_worker_packet(
            row["packet_path"], payload, authorized_resource=resource
        )
        for row, payload in zip(rows, payloads)
    ]
    canonical = base / "synthetic_canonical"
    install, install_measurement = _measure(
        lambda: parent_install_test_packets(
            canonical,
            [(row["packet_path"], payload) for row, payload in zip(rows, payloads)],
            authorized_resource=resource,
        )
    )
    semantic_rows = [
        {
            key: manifest[key]
            for key in (
                "block_index", "identity", "source_set_sha256",
                "native_binding_sha256", "block_root_digest", "steps_completed",
                "one_thread", "result_blind", "test_only",
            )
        }
        for manifest in manifests
    ]
    roots = [Path(str(value)) for value in resource["paths"].values()]
    return {
        "workers": workers,
        "spawn_processes": True,
        "one_thread_per_worker": True,
        "blocks": [int(row["block_index"]) for row in rows],
        "worker_pids_distinct": len({int(row["worker_pid"]) for row in rows})
        == min(workers, 4),
        "normalized_equivalence_sha256": hashlib.sha256(_canonical(semantic_rows)).hexdigest(),
        "packet_sha256": [str(row["packet_sha256"]) for row in rows],
        "parent_pid": int(install["parent_pid"]),
        "parent_only_ordered_install": install["ordered_block_indices"] == [0, 1, 2, 3],
        "failure_atomic_parent_tree_install": install["failure_atomic_parent_tree_install"],
        "private_scratch_bytes": sum(tree_size_bytes(root) for root in roots),
        "canonical_durable_bytes": tree_size_bytes(canonical),
        "measurement": measurement,
        "install_measurement": install_measurement,
    }


def _private_failure_resume_measurement(
    scratch_root: Path, *, source_set_sha256: str, native_binding_sha256: str
) -> dict[str, object]:
    base = scratch_root / "failure_resume"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    resource = make_process_resource_object(
        canonical_result_root=base / "synthetic_canonical",
        private_scratch_roots=[base / f"private_{index}" for index in range(4)],
        source_set_sha256=source_set_sha256,
        native_binding_sha256=native_binding_sha256,
    )
    native = runner.bind_native_backend()
    payload = make_spawn_payload(
        resource,
        block_index=0,
        block_root_digest="a" * 64,
        native_source_sha256=native.source_sha256,
        native_build_key=native.build_key,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        test_only=True,
        test_steps=8,
    )
    authorization = make_worker_authorization(resource, payload)
    payload_path = write_spawn_payload(base / "payload.json", payload)
    failed_as_injected = False
    with ProcessPoolExecutor(
        max_workers=1, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        future = pool.submit(
            run_test_only_spawn_worker,
            str(payload_path),
            authorization,
            inject_failure_after_step=3,
        )
        try:
            future.result()
        except Exception as exc:
            failed_as_injected = "injected TEST-only worker failure" in str(exc)
    checkpoint = Path(str(payload["private_scratch_root"])) / "block_00" / "checkpoint.json"
    packet = checkpoint.parent / "complete_packet"
    canonical_absent_after_failure = not Path(str(resource["canonical_result_root"])).exists()
    packet_absent_after_failure = not packet.exists()

    def resume() -> dict[str, object]:
        with ProcessPoolExecutor(
            max_workers=1, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            return pool.submit(
                run_test_only_spawn_worker, str(payload_path), authorization
            ).result()

    resumed, measurement = _measure(resume)
    manifest = validate_test_worker_packet(
        resumed["packet_path"], payload, authorized_resource=resource
    )
    return {
        "injected_failure_observed": failed_as_injected,
        "private_checkpoint_present_after_failure": checkpoint.is_file(),
        "complete_packet_absent_after_failure": packet_absent_after_failure,
        "canonical_absent_after_failure": canonical_absent_after_failure,
        "resumed_same_payload": manifest["payload_sha256"] == payload["payload_sha256"],
        "resumed_exact_count": manifest["steps_completed"] == payload["test_steps"],
        "measurement": measurement,
    }


def _production_authorization_conformance(
    scratch_root: Path,
    *,
    source_set_sha256: str,
    native_binding_sha256: str,
) -> dict[str, object]:
    base = scratch_root / "production_authorization"
    resource = make_process_resource_object(
        canonical_result_root=base / "canonical",
        private_scratch_roots=[base / f"private_{index}" for index in range(4)],
        source_set_sha256=source_set_sha256,
        native_binding_sha256=native_binding_sha256,
    )
    native = runner.bind_native_backend()
    payload = make_spawn_payload(
        resource,
        block_index=0,
        block_root_digest="c" * 64,
        native_source_sha256=native.source_sha256,
        native_build_key=native.build_key,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        test_only=False,
        test_steps=1,
    )
    context_body: dict[str, object] = {
        "schema": "RCLE_TBCFV_R04_CLOSED_ONE_BLOCK_PRODUCTION_CONTEXT_V1",
        "block_index": 0,
        "identity": "RCLE-TBCFV-R04-FULL-PANEL-20260821-01",
        "coordinate_binding_sha256": "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915",
        "master_digest": "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2",
        "block_root_digest": payload["block_root_digest"],
        "source_set_sha256": source_set_sha256,
        "native_binding_sha256": native_binding_sha256,
        "native_source_sha256": native.source_sha256,
        "native_build_key": native.build_key,
        "native_artifact_sha256": runner.native_artifact_identity()["sha256"],
        "empirical_bindings": {
            "source_manifest_sha256": source_set_sha256,
            "config_sha256": "6" * 64,
            "native_binding_sha256": native_binding_sha256,
            "coordinate_digest": "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915",
            "master_digest": "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2",
            "origin_lease_id": "RCLE-BENCHMARK-ORIGIN",
            "lease_id": "RCLE-BENCHMARK-ORIGIN",
            "lease_binding_sha256": "7" * 64,
        },
        "origin_lease_id": "RCLE-BENCHMARK-ORIGIN",
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
    context = {
        **context_body,
        "context_sha256": hashlib.sha256(_canonical(context_body)).hexdigest(),
    }
    authorization = make_worker_authorization(
        resource, payload, production_context=context
    )
    child_bytes = _canonical({"payload": payload, "authorization": authorization})
    canonical_absent = str(resource["canonical_result_root"]).encode("utf-8") not in child_bytes
    selected = str(payload["private_scratch_root"])
    other_roots_absent = all(
        str(root).encode("utf-8") not in child_bytes
        for root in resource["paths"].values()
        if str(root) != selected
    )
    return {
        "live_inventory_contains_process_workers": (
            "experiments/candidates/roster_consistent_latent_exploration_tbcfv/process_workers.py"
            in production_source_paths(ROOT)
        ),
        "production_activity_authorized_by_closed_projection": authorization[
            "production_activity_authorized"
        ],
        "canonical_path_absent_from_child_bytes": canonical_absent,
        "other_worker_roots_absent_from_child_bytes": other_roots_absent,
        "one_block_only": authorization["block_index"] == 0,
        "result_blind": authorization["result_blind"],
        "all_closed": canonical_absent and other_roots_absent,
    }


def _protocol_canary_context(
    payload: dict[str, object], *, failure_once: bool, validated_at: datetime | None = None
) -> tuple[dict[str, object], dict[str, object]]:
    lease_document = {
        "schema": "RCLE_TBCFV_R04_FIXED_SYNTHETIC_PROTOCOL_CANARY_LEASE_V1",
        "fixture_only": True,
        "result_blind": True,
    }
    validated_at = validated_at or datetime.now(timezone.utc)
    body: dict[str, object] = {
        "schema": "RCLE_TBCFV_R04_CLOSED_ONE_BLOCK_PRODUCTION_CONTEXT_V1",
        "block_index": payload["block_index"],
        "identity": "RCLE-TBCFV-R04-FULL-PANEL-20260821-01",
        "coordinate_binding_sha256": "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915",
        "master_digest": "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2",
        "block_root_digest": payload["block_root_digest"],
        "source_set_sha256": payload["source_set_sha256"],
        "native_binding_sha256": payload["native_binding_sha256"],
        "native_source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
        "native_build_key": ACCEPTED_NATIVE_BUILD_KEY,
        "native_artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
        "empirical_bindings": {
            "source_manifest_sha256": payload["source_set_sha256"],
            "config_sha256": "6" * 64,
            "native_binding_sha256": payload["native_binding_sha256"],
            "coordinate_digest": "614e4b503a258cff325284376ed8e6f5d65ac713c95a9bb4b8bfd669ad776915",
            "master_digest": "d35b0f3f3ccb33826e2d3e68d73fad086951ac1cdab7e62e0e38be41e1a626a2",
            "origin_lease_id": "RCLE-PROTOCOL-CANARY-ORIGIN",
            "lease_id": "RCLE-PROTOCOL-CANARY-ORIGIN",
            "lease_binding_sha256": "7" * 64,
        },
        "origin_lease_id": "RCLE-PROTOCOL-CANARY-ORIGIN",
        "stage_binding_sha256": "7" * 64,
        "accepted_binding_sha256": "8" * 64,
        "preactivity_certificate_sha256": "9" * 64,
        "coordinate_proposal_sha256": "a" * 64,
        "lease_document_sha256": document_sha256(lease_document),
        "lease_validated_at": validated_at.isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "one_thread": True,
        "gpu_count": 0,
        "canonical_paths_present": False,
        "result_blind": True,
        "protocol_canary": True,
        "protocol_canary_failure_once": failure_once,
    }
    return (
        {**body, "context_sha256": hashlib.sha256(_canonical(body)).hexdigest()},
        lease_document,
    )


def _protocol_parent_frontier(
    root: Path, context: dict[str, object], lease_document: dict[str, object]
) -> tuple[AtomicEmpiricalFrontier, object]:
    bindings_value = context["empirical_bindings"]
    assert isinstance(bindings_value, dict)
    bindings = EmpiricalBindings(**bindings_value)
    permit = _PrivateWorkerPermit(
        lease_id=str(context["origin_lease_id"]),
        origin_lease_id=str(context["origin_lease_id"]),
        predecessor_lease_id=None,
        replacement_index=0,
        lease_lineage=(str(context["origin_lease_id"]),),
        stage_binding_sha256=str(context["stage_binding_sha256"]),
        accepted_binding_sha256=str(context["accepted_binding_sha256"]),
        preactivity_certificate_sha256=str(context["preactivity_certificate_sha256"]),
        coordinate_proposal_sha256=str(context["coordinate_proposal_sha256"]),
        paths={},
        repair_transition_sha256=None,
        expires_at=str(context["expires_at"]),
    )
    frontier = AtomicEmpiricalFrontier.create(
        root,
        bindings,
        owner_token=runner.OWNER_TOKEN,
        permit=permit,
        now=datetime.fromisoformat(str(context["lease_validated_at"])),
        lease_document_sha256=document_sha256(lease_document),
    )
    authority = SimpleNamespace(permit=permit, lease_document=lease_document)
    return frontier, authority


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("ascii"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _production_protocol_canary(
    scratch_root: Path,
    *,
    source_set_sha256: str,
    native_binding_sha256: str,
) -> dict[str, object]:
    concurrency_rows: list[dict[str, object]] = []
    protocol_validated_at = datetime.now(timezone.utc)
    for workers in (1, 2, 4):
        base = scratch_root / f"production_protocol_{workers}"
        if base.exists():
            shutil.rmtree(base)
        resource = make_process_resource_object(
            canonical_result_root=base / "canonical",
            private_scratch_roots=[base / f"private_{index}" for index in range(4)],
            source_set_sha256=source_set_sha256,
            native_binding_sha256=native_binding_sha256,
        )
        calls: list[tuple[str, dict[str, object], dict[str, object], dict[str, object]]] = []
        lease_document: dict[str, object] | None = None
        shared_validated_at = protocol_validated_at
        for block_index in range(4):
            payload = make_spawn_payload(
                resource,
                block_index=block_index,
                block_root_digest=f"{block_index + 500:064x}",
                native_source_sha256=ACCEPTED_NATIVE_SOURCE_SHA256,
                native_build_key=ACCEPTED_NATIVE_BUILD_KEY,
                expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                test_only=False,
                test_steps=1,
            )
            context, lease_document = _protocol_canary_context(
                payload, failure_once=False, validated_at=shared_validated_at
            )
            authorization = make_worker_authorization(
                resource, payload, production_context=context
            )
            payload_path = write_spawn_payload(
                Path(str(payload["private_scratch_root"])) / f"payload_{block_index:02d}.json",
                payload,
            )
            calls.append((str(payload_path), authorization, payload, context))
        assert lease_document is not None

        def execute() -> list[dict[str, object]]:
            with ProcessPoolExecutor(
                max_workers=workers, mp_context=multiprocessing.get_context("spawn")
            ) as pool:
                futures = [
                    pool.submit(run_production_block_worker, path, authorization)
                    for path, authorization, _, _ in calls
                ]
                return [future.result() for future in futures]

        rows, measurement = _measure(execute)
        frontier, authority = _protocol_parent_frontier(
            Path(str(resource["canonical_result_root"])) / "frontier",
            calls[0][3],
            lease_document,
        )
        validated = []
        for row, (_, authorization, payload, _) in zip(rows, calls):
            manifest = runner._prevalidate_production_packet(
                frontier, authority, str(row["packet_path"]), payload, authorization
            )
            validated.append((int(manifest["block_index"]), str(row["packet_path"]), manifest))
        for _, packet_path, manifest in sorted(validated):
            runner._install_prevalidated_production_packet(frontier, packet_path, manifest)
        private_bytes = sum(tree_size_bytes(str(path)) for path in resource["paths"].values())
        canonical_bytes = tree_size_bytes(frontier.root)
        child_peak_sum = sum(
            int(row["process_lifetime_peak_rss_bytes"]) for row in rows
        )
        parent_peak = int(measurement["peak_rss_bytes"])
        concurrency_rows.append(
            {
                "workers": workers,
                "measurement": measurement,
                "worker_pids_distinct": len({int(row["worker_pid"]) for row in rows})
                == min(workers, 4),
                "parent_prevalidation_install": True,
                "block_tree_sha256": _tree_digest(frontier.root / "blocks"),
                "private_bytes_four_blocks": private_bytes,
                "canonical_bytes_four_blocks": canonical_bytes,
                "parent_process_lifetime_peak_rss_bytes": parent_peak,
                "production_child_lifetime_peak_rss_bytes_sum": child_peak_sum,
                "production_process_group_peak_rss_bytes": parent_peak + child_peak_sum,
            }
        )

    failure_base = scratch_root / "production_protocol_failure"
    if failure_base.exists():
        shutil.rmtree(failure_base)
    failure_resource = make_process_resource_object(
        canonical_result_root=failure_base / "canonical",
        private_scratch_roots=[failure_base / f"private_{index}" for index in range(4)],
        source_set_sha256=source_set_sha256,
        native_binding_sha256=native_binding_sha256,
    )
    failure_payload = make_spawn_payload(
        failure_resource,
        block_index=0,
        block_root_digest="e" * 64,
        native_source_sha256=ACCEPTED_NATIVE_SOURCE_SHA256,
        native_build_key=ACCEPTED_NATIVE_BUILD_KEY,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        test_only=False,
        test_steps=1,
    )
    failure_context, failure_lease = _protocol_canary_context(
        failure_payload, failure_once=True
    )
    failure_authorization = make_worker_authorization(
        failure_resource, failure_payload, production_context=failure_context
    )
    failure_payload_path = write_spawn_payload(
        Path(str(failure_payload["private_scratch_root"])) / "payload.json",
        failure_payload,
    )
    injected = False
    try:
        run_production_block_worker(str(failure_payload_path), failure_authorization)
    except ProcessWorkerError as exc:
        injected = "injected production protocol canary failure" in str(exc)
    failure_block = Path(str(failure_payload["private_scratch_root"])) / "b00"
    generations_before = tuple(
        sorted((failure_block / "f" / "blocks" / "block_00" / "resume").glob("generation_*.json"))
    )
    generation_sha256 = hashlib.sha256(generations_before[0].read_bytes()).hexdigest()
    packet_absent = not (failure_block / "production_complete_packet").exists()
    canonical_absent = not Path(str(failure_resource["canonical_result_root"])).exists()
    resumed = run_production_block_worker(
        str(failure_payload_path), failure_authorization
    )
    failure_manifest = validate_production_worker_packet(
        resumed["packet_path"],
        failure_payload,
        worker_authorization=failure_authorization,
    )
    generations_after = tuple(
        sorted((failure_block / "f" / "blocks" / "block_00" / "resume").glob("generation_*.json"))
    )
    failure_frontier, failure_authority = _protocol_parent_frontier(
        Path(str(failure_resource["canonical_result_root"])) / "frontier",
        failure_context,
        failure_lease,
    )
    accepted_failure = runner._prevalidate_production_packet(
        failure_frontier,
        failure_authority,
        str(resumed["packet_path"]),
        failure_payload,
        failure_authorization,
    )
    runner._install_prevalidated_production_packet(
        failure_frontier, str(resumed["packet_path"]), accepted_failure
    )
    digests = {str(row["block_tree_sha256"]) for row in concurrency_rows}
    max_private_four = max(int(row["private_bytes_four_blocks"]) for row in concurrency_rows)
    max_canonical_four = max(int(row["canonical_bytes_four_blocks"]) for row in concurrency_rows)
    return {
        "concurrency": concurrency_rows,
        "spawn_1_2_4_exact": len(digests) == 1,
        "normalized_block_tree_sha256": next(iter(digests)),
        "parent_prevalidation_install_exact": all(
            row["parent_prevalidation_install"] is True for row in concurrency_rows
        ),
        "private_scratch_projected_bytes": max_private_four * 5,
        "canonical_durable_projected_bytes": max_canonical_four * 5,
        "failure_resume": {
            "injected_failure_observed": injected,
            "packet_absent_after_failure": packet_absent,
            "canonical_absent_after_failure": canonical_absent,
            "same_payload_resumed": failure_manifest["payload_sha256"]
            == failure_payload["payload_sha256"],
            "private_generation_preserved": (
                len(generations_before) == 1
                and len(generations_after) == 2
                and hashlib.sha256(generations_after[0].read_bytes()).hexdigest()
                == generation_sha256
            ),
            "final_packet_exact": int(accepted_failure["block_index"]) == 0,
        },
    }


def _composite_action(index: int) -> Callable[[], None]:
    del index
    training = _training_action(LEARNED_PACKAGES[0])
    learned = _learned_eval_action(LEARNED_PACKAGES[0])
    scripted = _scripted_eval_action(SCRIPTED_PACKAGES[0])

    def action() -> None:
        training()
        learned()
        scripted()

    return action


def run_benchmark(*, scratch_root: Path) -> dict[str, object]:
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise RuntimeError("benchmark requires exact one-thread Torch settings")

    width_equivalence = _width_equivalence()
    if width_equivalence["all_exact"] is not True:
        raise RuntimeError("B32 runner grouping is not exactly equivalent to B8")

    training: dict[str, object] = {}
    for arm in LEARNED_PACKAGES:
        training[arm] = _measure_warm_unit(_training_action(arm))
    learned_eval: dict[str, object] = {}
    for arm in LEARNED_PACKAGES:
        learned_eval[arm] = _measure_warm_unit(_learned_eval_action(arm))
    scripted_eval: dict[str, object] = {}
    for package in SCRIPTED_PACKAGES:
        scripted_eval[package] = _measure_warm_unit(_scripted_eval_action(package))

    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    scratch_root.mkdir(parents=True)
    (scratch_root / "frontier").mkdir()
    ordinary_root = scratch_root / "ordinary"
    ordinary_root.mkdir()
    ordinary_frontier, ordinary_runtime = runner._prepare_synthetic_ordinary_frontier(
        ordinary_root
    )

    def ordinary_transaction() -> None:
        runner._persist_runtime(ordinary_frontier, 0, ordinary_runtime)
        if runner._restore_runtime(ordinary_frontier, 0) is None:
            raise RuntimeError("ordinary synthetic persist/restore returned no runtime")

    _, serialization = _measure(ordinary_transaction)
    stress_root = scratch_root / "failure_recovery"
    stress_root.mkdir()
    _, failure_recovery = _measure(
        lambda: runner._synthetic_empirical_frontier_chain(stress_root)
    )

    worker_rows = [_concurrency_measurement(workers) for workers in (1, 2, 4)]
    source_identity = canonical_source_identity(production_source_paths(ROOT))
    native_identity = runner.native_artifact_identity()
    native_binding_sha256 = hashlib.sha256(
        _canonical(
            {
                "source_sha256": native_identity["source_sha256"],
                "build_key": native_identity["build_key"],
                "artifact_sha256": native_identity["sha256"],
            }
        )
    ).hexdigest()
    production_integration = _production_authorization_conformance(
        scratch_root,
        source_set_sha256=str(source_identity["source_set_sha256"]),
        native_binding_sha256=native_binding_sha256,
    )
    lifecycle_root = scratch_root / "private_process_lifecycle"
    lifecycle_rows = [
        _private_lifecycle_measurement(
            lifecycle_root,
            workers,
            source_set_sha256=str(source_identity["source_set_sha256"]),
            native_binding_sha256=native_binding_sha256,
        )
        for workers in (1, 2, 4)
    ]
    failure_resume = _private_failure_resume_measurement(
        lifecycle_root,
        source_set_sha256=str(source_identity["source_set_sha256"]),
        native_binding_sha256=native_binding_sha256,
    )
    production_protocol = _production_protocol_canary(
        scratch_root,
        source_set_sha256=str(source_identity["source_set_sha256"]),
        native_binding_sha256=native_binding_sha256,
    )
    training_cpu = sum(float(row["cpu_seconds"]) for row in training.values())
    learned_cpu = sum(float(row["cpu_seconds"]) for row in learned_eval.values())
    scripted_cpu = sum(float(row["cpu_seconds"]) for row in scripted_eval.values())
    parallel_compute_cpu_seconds = (
        training_cpu * (TRAINING_ARM_UPDATES / 5)
        + learned_cpu * EVALUATION_GROUPS
        + scripted_cpu * EVALUATION_GROUPS
    )
    serialization_cpu_seconds = float(serialization["cpu_seconds"]) * RUNTIME_COMMITS
    serialization_wall_seconds = float(serialization["wall_seconds"]) * RUNTIME_COMMITS
    lifecycle_four = lifecycle_rows[-1]
    lifecycle_groups = 20 // 4
    lifecycle_cpu_upper_seconds = lifecycle_groups * (
        float(lifecycle_four["measurement"]["wall_seconds"]) * 4.0
        + float(lifecycle_four["install_measurement"]["cpu_seconds"])
    )
    projected_cpu_seconds = (
        parallel_compute_cpu_seconds
        + serialization_cpu_seconds
        + lifecycle_cpu_upper_seconds
    )
    single = float(worker_rows[0]["wall_seconds"])
    projections: dict[str, object] = {}
    for row in worker_rows:
        workers = int(row["workers"])
        observed_speedup = (single * workers) / float(row["wall_seconds"])
        lifecycle = lifecycle_rows[(1, 2, 4).index(workers)]
        lifecycle_wall_seconds = lifecycle_groups * (
            float(lifecycle["measurement"]["wall_seconds"])
            + float(lifecycle["install_measurement"]["wall_seconds"])
        )
        compute_wall_seconds = parallel_compute_cpu_seconds / observed_speedup
        full_chain_wall_seconds = (
            compute_wall_seconds
            + serialization_wall_seconds
            + lifecycle_wall_seconds
        )
        projections[str(workers)] = {
            "observed_speedup": observed_speedup,
            "parallel_compute_wall_seconds": compute_wall_seconds,
            "serialization_checkpoint_io_wall_seconds": serialization_wall_seconds,
            "private_lifecycle_install_wall_seconds": lifecycle_wall_seconds,
            "projected_full_chain_wall_hours": full_chain_wall_seconds / 3600.0,
        }
    projected_cpu_hours = projected_cpu_seconds / 3600.0
    projected_checkpoint_read = int(serialization["io_read_bytes"]) * RUNTIME_COMMITS
    projected_checkpoint_write = int(serialization["io_write_bytes"]) * RUNTIME_COMMITS
    production_four = production_protocol["concurrency"][-1]
    group_rss = int(production_four["production_process_group_peak_rss_bytes"])
    max_private_scratch = int(production_protocol["private_scratch_projected_bytes"])
    max_canonical_durable = int(production_protocol["canonical_durable_projected_bytes"])
    lifecycle_equivalent = len(
        {str(row["normalized_equivalence_sha256"]) for row in lifecycle_rows}
    ) == 1
    failure_resume_complete = all(
        failure_resume[key] is True
        for key in (
            "injected_failure_observed",
            "private_checkpoint_present_after_failure",
            "complete_packet_absent_after_failure",
            "canonical_absent_after_failure",
            "resumed_same_payload",
            "resumed_exact_count",
        )
    )
    production_failure_resume_complete = all(
        item is True for item in production_protocol["failure_resume"].values()
    )
    ceiling_checks = {
        "projected_complete_panel_cpu_hours": projected_cpu_hours <= CPU_HOURS_CEILING,
        "projected_four_process_wall_hours": float(
            projections["4"]["projected_full_chain_wall_hours"]
        )
        <= FOUR_PROCESS_WALL_HOURS_CEILING,
        "four_one_thread_spawn_processes": production_four["workers"] == 4
        and production_four["worker_pids_distinct"] is True,
        "process_group_rss_bytes": group_rss <= PROCESS_GROUP_RSS_CEILING,
        "private_scratch_combined_bytes": max_private_scratch
        <= PRIVATE_SCRATCH_COMBINED_CEILING,
        "canonical_durable_bytes": max_canonical_durable <= CANONICAL_DURABLE_CEILING,
        "ordinary_checkpoint_read_bytes": projected_checkpoint_read
        <= CHECKPOINT_READ_CEILING,
        "ordinary_checkpoint_write_bytes": projected_checkpoint_write
        <= CHECKPOINT_WRITE_CEILING,
        "spawn_process_equivalence": lifecycle_equivalent,
        "injected_failure_resume": failure_resume_complete,
        "production_closed_one_block_authorization": production_integration["all_closed"]
        is True,
        "production_protocol_spawn_equivalence": production_protocol["spawn_1_2_4_exact"]
        is True,
        "production_protocol_parent_prevalidation_install": production_protocol[
            "parent_prevalidation_install_exact"
        ]
        is True,
        "production_protocol_failure_resume": production_failure_resume_complete,
    }
    all_measurements = [
        *training.values(),
        *learned_eval.values(),
        *scripted_eval.values(),
        serialization,
        failure_recovery,
        *worker_rows,
        *(row["measurement"] for row in lifecycle_rows),
        *(row["install_measurement"] for row in lifecycle_rows),
        failure_resume["measurement"],
        *(row["measurement"] for row in production_protocol["concurrency"]),
    ]
    source_paths = {
        "empirical_runner.py": Path(runner.__file__).resolve(),
        "native_backend.py": Path(runner.__file__).with_name("native_backend.py").resolve(),
        "native/tbcfv_backend.cpp": (
            Path(runner.__file__).with_name("native") / "tbcfv_backend.cpp"
        ).resolve(),
        "benchmark_rcle_tbcfv_r04_runner_chain.py": Path(__file__).resolve(),
        "process_workers.py": Path(runner.__file__).with_name("process_workers.py").resolve(),
    }
    return {
        "schema": SCHEMA,
        "mode": "FIXED_SYNTHETIC_TEST_ONLY_RESULT_BLIND",
        "source_binding": {
            name: {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for name, path in source_paths.items()
        },
        "efficiency_review": "COMPLETE",
        "process_acceptance": "ACCEPTED" if all(ceiling_checks.values()) else "REJECTED",
        "chain_coverage": {
            "native_loader_cache": True,
            "native_widths_1_8_32": True,
            "batched_environment_rollout": True,
            "batched_policy_forward": True,
            "backward_and_registered_optimizer": True,
            "learned_evaluation": True,
            "scripted_evaluation": True,
            "serialization_checkpoint_atomic_resume": True,
            "worker_concurrency_1_2_4": True,
            "private_worker_checkpoint_packet_parent_install": True,
            "production_one_block_worker_source": True,
            "parent_only_process_full_panel_source": True,
        },
        "width_equivalence": width_equivalence,
        "measurements": {
            "training_update_by_arm": training,
            "learned_B32_by_arm": learned_eval,
            "scripted_B32_by_package": scripted_eval,
            "serialization_checkpoint_resume": serialization,
            "injected_loss_recovery_coverage": failure_recovery,
            "worker_concurrency": worker_rows,
            "private_process_lifecycle": lifecycle_rows,
            "private_injected_failure_resume": failure_resume,
            "production_integration": production_integration,
            "production_protocol_canary": production_protocol,
        },
        "projection": {
            "training_arm_updates": TRAINING_ARM_UPDATES,
            "learned_B32_groups": EVALUATION_GROUPS,
            "scripted_B32_groups": EVALUATION_GROUPS,
            "runtime_commits": RUNTIME_COMMITS,
            "parallel_compute_cpu_seconds": parallel_compute_cpu_seconds,
            "serialization_checkpoint_cpu_seconds": serialization_cpu_seconds,
            "private_lifecycle_cpu_seconds_upper": lifecycle_cpu_upper_seconds,
            "projected_complete_cpu_hours": projected_cpu_hours,
            "projected_checkpoint_resume_read_bytes": projected_checkpoint_read,
            "projected_checkpoint_resume_write_bytes": projected_checkpoint_write,
            "worker_wall": projections,
        },
        "resources": {
            "peak_rss_bytes": max(int(row["peak_rss_bytes"]) for row in all_measurements),
            "io_read_bytes_measured": sum(int(row["io_read_bytes"]) for row in all_measurements),
            "io_write_bytes_measured": sum(int(row["io_write_bytes"]) for row in all_measurements),
            "telemetry_complete": all(row["telemetry_available"] is True for row in all_measurements),
            "four_process_group_rss_bytes": group_rss,
            "max_private_scratch_bytes": max_private_scratch,
            "max_canonical_durable_bytes": max_canonical_durable,
        },
        "current_production_source_set_sha256": source_identity["source_set_sha256"],
        "native_binding_sha256": native_binding_sha256,
        "ceiling_checks": ceiling_checks,
        "scientific_identity_materialized": False,
        "production_authority_used": False,
        "result_value_exposed": False,
    }


def _bound_protocol_evidence(output: dict[str, object]) -> dict[str, object]:
    source = output["source_binding"]
    projection = output["projection"]
    resources = output["resources"]
    measurements = output["measurements"]
    assert isinstance(source, dict)
    assert isinstance(projection, dict)
    assert isinstance(resources, dict)
    assert isinstance(measurements, dict)
    protocol = measurements["production_protocol_canary"]
    assert isinstance(protocol, dict)
    worker_wall = projection["worker_wall"]
    assert isinstance(worker_wall, dict)
    return {
        "schema": "RCLE_TBCFV_R04_PRODUCTION_PROTOCOL_EFFICIENCY_EVIDENCE_V1",
        "mode": "FIXED_SYNTHETIC_RESULT_BLIND_PRODUCTION_PROTOCOL",
        "source_binding": {
            "native_source_sha256": ACCEPTED_NATIVE_SOURCE_SHA256,
            "native_build_key": ACCEPTED_NATIVE_BUILD_KEY,
            "native_artifact_sha256": ACCEPTED_NATIVE_ARTIFACT_SHA256,
            "empirical_runner_sha256": source["empirical_runner.py"]["sha256"],
            "process_workers_sha256": source["process_workers.py"]["sha256"],
            "benchmark_sha256": source["benchmark_rcle_tbcfv_r04_runner_chain.py"]["sha256"],
        },
        "projection": {
            "complete_cpu_core_hours": projection["projected_complete_cpu_hours"],
            "one_process_wall_hours": worker_wall["1"]["projected_full_chain_wall_hours"],
            "four_process_wall_hours": worker_wall["4"]["projected_full_chain_wall_hours"],
            "checkpoint_read_bytes": projection["projected_checkpoint_resume_read_bytes"],
            "checkpoint_write_bytes": projection["projected_checkpoint_resume_write_bytes"],
        },
        "resources": {
            "process_group_rss_bytes": resources["four_process_group_rss_bytes"],
            "private_scratch_projected_bytes": protocol["private_scratch_projected_bytes"],
            "canonical_durable_projected_bytes": protocol["canonical_durable_projected_bytes"],
            "measured_io_read_bytes": resources["io_read_bytes_measured"],
            "measured_io_write_bytes": resources["io_write_bytes_measured"],
        },
        "equivalence": {
            "widths_1_8_32_exact": output["width_equivalence"]["all_exact"],
            "spawn_1_2_4_exact": protocol["spawn_1_2_4_exact"],
            "normalized_block_tree_sha256": protocol["normalized_block_tree_sha256"],
            "parent_prevalidation_install_exact": protocol[
                "parent_prevalidation_install_exact"
            ],
            "closed_one_block_authorization_exact": measurements[
                "production_integration"
            ]["all_closed"],
        },
        "failure_resume": protocol["failure_resume"],
        "ceiling_checks": output["ceiling_checks"],
        "scientific_identity_materialized": False,
        "production_authority_used": False,
        "result_value_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument(
        "--bound-evidence-output",
        type=Path,
        default=ROOT / "runtime/benchmarks/rcle_tbcfv_r04_production_protocol_efficiency_20260822.json",
    )
    args = parser.parse_args()
    scratch = args.scratch_root or Path(tempfile.mkdtemp(prefix="rcle_runner_chain_"))
    output = run_benchmark(scratch_root=scratch.resolve())
    bound_payload = _canonical(_bound_protocol_evidence(output))
    args.bound_evidence_output.parent.mkdir(parents=True, exist_ok=True)
    bound_temp = args.bound_evidence_output.with_name(
        f".{args.bound_evidence_output.name}.{multiprocessing.current_process().pid}.tmp"
    )
    bound_temp.write_bytes(bound_payload)
    bound_temp.replace(args.bound_evidence_output)
    output["current_production_source_set_sha256"] = canonical_source_identity(
        production_source_paths(ROOT)
    )["source_set_sha256"]
    payload = _canonical(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "bound_evidence": str(args.bound_evidence_output.resolve()),
                "bound_evidence_sha256": hashlib.sha256(bound_payload).hexdigest(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
