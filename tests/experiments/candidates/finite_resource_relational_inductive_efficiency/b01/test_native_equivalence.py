from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.host import NativeBackendUnavailable
from experiments.candidates.finite_resource_relational_inductive_efficiency.native.native_abi import STATE_SIZE
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import (
    build_package_native_artifact, load_package_native_adapter,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.orchestration import PackageExternalActionEnvironment
from experiments.candidates.finite_resource_relational_inductive_efficiency.tapes import complete_test_only_witness
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    named_compute_profile, validate_resource_receipt,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import (
    B01NativeBatchEnvironment, bounded_worker_map, performance_readiness,
)


def _fresh_admit_memory(receipt_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable, str(Path("scripts/hmasd_resource_preflight.py").resolve()),
            "admit-memory", "--out", str(receipt_path),
        ],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    validate_resource_receipt(json.loads(receipt_path.read_text(encoding="utf-8")))


def _direct_observation_equal(scalar, batch, lane: int) -> bool:
    return (
        scalar.observations.tobytes() == batch.observations[lane].tobytes()
        and scalar.roles.tobytes() == batch.roles[lane].tobytes()
        and scalar.legal_masks.tobytes() == batch.legal_masks[lane].tobytes()
        and scalar.slot == batch.slots[lane]
        and scalar.terminal == batch.terminals[lane]
    )


def test_actual_package_native_scalar_batch_and_worker_equivalence(tmp_path):
    try:
        build_package_native_artifact()
    except NativeBackendUnavailable as exc:
        pytest.skip(f"REPAIR_REQUIRED: package C++ toolchain unavailable: {exc}")

    # Required admission is deliberately adjacent to the first real native
    # environment/adapter operation and its direct receipt remains in basetemp.
    _fresh_admit_memory((tmp_path / "native-equivalence-admit-memory.json").resolve())
    adapter = load_package_native_adapter(named_compute_profile())

    tapes = [complete_test_only_witness(roster=6, episode=index) for index in range(4)]
    scalar = PackageExternalActionEnvironment(adapter, 6)
    batch = B01NativeBatchEnvironment(adapter, roster=6, lanes=4)
    scalar.reset(tapes[0])
    batch.reset(tapes)
    for slot in range(12):
        scalar_observation = scalar.observe()
        batch_observation = batch.observe()
        assert _direct_observation_equal(scalar_observation, batch_observation, 0)
        scalar_step = scalar.step([5] * 6)
        batch_step = batch.step(np.full((4, 6), 5, dtype=np.int64))
        assert scalar_step.terminal == batch_step.terminals[0]
        assert np.float32(scalar_step.terminal_return).tobytes() == np.float32(
            batch_step.returns[0]
        ).tobytes()
        assert scalar.snapshot() == batch.snapshot()[:STATE_SIZE]
        assert scalar_step.terminal == (slot == 11)
    assert batch.work_ledger().environment_slots == 4 * 12

    def rollout(episode: int):
        environment = B01NativeBatchEnvironment(adapter, roster=6, lanes=1)
        environment.reset([complete_test_only_witness(roster=6, episode=episode)])
        trace = []
        for _ in range(12):
            observation = environment.observe()
            step = environment.step([[5] * 6])
            trace.append((
                observation.observations.tobytes(), observation.roles.tobytes(),
                observation.legal_masks.tobytes(), step.terminals,
                tuple(np.float32(value).tobytes() for value in step.returns),
                step.previous_success.tobytes(),
            ))
        return tuple(trace), environment.snapshot(), environment.work_ledger()

    tasks = tuple(range(8))
    results = {
        workers: bounded_worker_map(rollout, tasks, workers=workers)
        for workers in (1, 2, 4)
    }
    assert results[1] == results[2] == results[4]


def test_performance_readiness_fails_closed_without_end_to_end_telemetry():
    assert performance_readiness({
        "schema": "FRRIE_B01_PERFORMANCE_TELEMETRY_V1",
        "disposition": "REPAIR_REQUIRED", "blocker": "END_TO_END_TELEMETRY_ABSENT",
        "measured_at": None, "end_to_end_wall_seconds": None,
        "scientific_slots": None, "slots_per_second": None, "cpu_seconds": None,
        "cpu_occupancy_fraction": None, "process_tree_peak_rss_bytes": None,
        "scratch_peak_bytes": None, "durable_peak_bytes": None,
        "read_bytes": None, "write_bytes": None, "worker_peak": None,
        "scalar_batch_equivalence": None, "worker_equivalence": None,
    }) == "REPAIR_REQUIRED"
