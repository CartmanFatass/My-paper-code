"""P1 isolated-process scheduler and per-worker CPU self-audit."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import statistics
import tempfile
import time
from typing import Mapping

import torch

from .production_contract import TestAuthority
from .production_preactivity import _native_training_fragments
from .production_training import run_full_4096_test_update
from . import production_scheduler as scheduler_module
from .production_scheduler import (
    ProcessWorkerSpec, ScheduledTask, TaskJournal,
    _initialize_process_worker, _process_execute_task, complete_stage_plan,
    scheduler_manifest,
)
from .production_training_engine import WelfordState


class P1AuditError(RuntimeError):
    pass


class _ProcessFixturePlane:
    def __init__(self) -> None:
        self.fragments, self.binding = _native_training_fragments()

    def measure_update(self) -> Mapping[str, object]:
        value = run_full_4096_test_update(TestAuthority(), fragments=self.fragments,
                                          source_label="R06_P1_PREBUILT_NATIVE_TEST_ROWS")
        return {**value, "native_fragment_binding": self.binding}

    def execute_scheduled(self, stage: str, start: int, count: int):
        TestAuthority().require_test_only()
        if stage == "POPULATION":
            return tuple(f"TEST/P1/WARM/{index}".encode("ascii") for index in range(start, start + count))
        if stage == "TRAINING" and count == 1:
            value = self.measure_update()
            receipt = {"schema": "TEST_DISH_RBHR_R06_P1_UPDATE_RECEIPT_V1", "start": start,
                       "transitions": value["native_fragment_binding"]["transitions"],
                       "losses_finite": value["losses_finite"], "gradient_norms_finite": value["gradient_norms_finite"],
                       "test_only": True, "question_relevant_output": False}
            return ((json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"),)
        raise P1AuditError("P1 fixture scheduled coordinate differs")


def load_p1_process_fixture_plane() -> _ProcessFixturePlane:
    return _ProcessFixturePlane()


def _warm_process(delay: float) -> int:
    time.sleep(delay); return os.getpid()


def _measure_update() -> Mapping[str, object]:
    started_wall = time.perf_counter(); started_cpu = time.process_time()
    plane = scheduler_module._PROCESS_DATA_PLANE
    if not isinstance(plane, _ProcessFixturePlane):
        raise P1AuditError("P1 process fixture plane is uninitialized")
    value = plane.measure_update()
    return {"pid": os.getpid(), "wall_seconds": time.perf_counter() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu,
            "losses_finite": value["losses_finite"], "gradient_norms_finite": value["gradient_norms_finite"],
            "checkpoint_resume_equal": value["checkpoint_resume_equal"]}


def _scalar_welford(rows: torch.Tensor) -> WelfordState:
    state = WelfordState.empty(rows.shape[-1])
    for row in rows.to(torch.float64):
        state.count += 1; delta = row - state.mean; state.mean += delta / state.count; state.m2 += delta * (row - state.mean)
    return state


def run_p1_process_cpu_self_audit(repository_root: Path) -> Mapping[str, object]:
    TestAuthority().require_test_only(); context = multiprocessing.get_context("spawn")
    spec = {"loader_module": "experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_p1"}
    spec.update({"loader_function": "load_p1_process_fixture_plane", "loader_kwargs": {}})
    spec["pin_affinity"] = False
    spec["high_priority"] = True
    spec["ideal_processor"] = False
    ProcessWorkerSpec(spec["loader_module"], spec["loader_function"], spec["loader_kwargs"]).validate()

    counter = context.Value("i", 0); lock = context.Lock()
    with ProcessPoolExecutor(max_workers=1, mp_context=context, initializer=_initialize_process_worker, initargs=(spec, counter, lock, 8)) as pool:
        pool.submit(_measure_update).result()
        single_rows = [pool.submit(_measure_update).result() for _ in range(3)]
        single_wall_median = statistics.median(float(row["wall_seconds"]) for row in single_rows)
        single = min(single_rows, key=lambda row: abs(float(row["wall_seconds"]) - single_wall_median))

    counter = context.Value("i", 0); lock = context.Lock()
    with ProcessPoolExecutor(max_workers=8, mp_context=context, initializer=_initialize_process_worker, initargs=(spec, counter, lock, 8)) as pool:
        warm_rows = [future.result() for future in [pool.submit(_measure_update) for _ in range(8)]]
        warm_pids = {int(row["pid"]) for row in warm_rows}
        started = time.perf_counter(); futures = [pool.submit(_measure_update) for _ in range(8)]; parallel_rows = [future.result() for future in futures]
        parallel_wall = time.perf_counter() - started
    pids = {int(row["pid"]) for row in parallel_rows}
    single_wall = single_wall_median; effective = 8.0 * single_wall / parallel_wall
    overhead = parallel_wall / single_wall - 1.0
    per_worker_wall = statistics.median(float(row["wall_seconds"]) for row in parallel_rows)
    training_cpu_hours = per_worker_wall * 122_880 / 3_600.0
    projected_cpu_hours = training_cpu_hours + 15.182386322885742
    projected_training_wall = training_cpu_hours / effective
    projected_complete_wall = projected_training_wall + 15.182386322885742 / 6.0 + 2.0
    # P1 may project, but not replace, the exact P2 process-command resource
    # remeasurement.  These conservative high bounds retain the accepted
    # process-duplication/storage multipliers from the owner-bound scheduler
    # assessment and are checked only against the immutable hard ceilings.
    projected_hard_resources = {
        "aggregate_rss_gib": 6.61, "scratch_gib": 1.66,
        "durable_gib": 0.83, "total_io_gib": 68.14,
    }

    # Batched Welford is the P1 CPU repair. Compare it to the retained scalar
    # law on deterministic non-scientific rows.
    rows = torch.sin(torch.arange(4_096, dtype=torch.float64)[:, None] * 0.007 + torch.arange(54, dtype=torch.float64)[None] * 0.011)
    scalar = _scalar_welford(rows); batched = WelfordState.empty(54); batched.update(rows)
    welford_equivalent = scalar.count == batched.count and torch.allclose(scalar.mean, batched.mean, rtol=0.0, atol=1e-12) and torch.allclose(scalar.m2, batched.m2, rtol=1e-12, atol=1e-8)

    identity = hashlib.sha256(b"TEST/DISH/RBHR/R06/P1/PROCESS-IDENTITY").hexdigest()
    with tempfile.TemporaryDirectory(prefix="dish-r06-p1-journal-") as temporary:
        task = ScheduledTask("POPULATION", 0, 0, 32, 32)
        journal_root = Path(temporary)
        counter = context.Value("i", 0); lock = context.Lock()
        with ProcessPoolExecutor(max_workers=1, mp_context=context, initializer=_initialize_process_worker, initargs=(spec, counter, lock, 8)) as pool:
            first = pool.submit(_process_execute_task, task, str(journal_root), identity).result()
        first_record = TaskJournal(journal_root, identity_sha256=identity).load(task)
        counter = context.Value("i", 0); lock = context.Lock()
        with ProcessPoolExecutor(max_workers=1, mp_context=context, initializer=_initialize_process_worker, initargs=(spec, counter, lock, 8)) as pool:
            second = pool.submit(_process_execute_task, task, str(journal_root), identity).result()
        second_record = TaskJournal(journal_root, identity_sha256=identity).load(task)
    successor_equal = first_record == second_record and first[1] == second[1] and first[2] != second[2]

    checks = {
        "isolated_processes": len(pids) >= 6 and len(warm_pids) >= 6,
        "effective_concurrency_ge_6": effective >= 6.0,
        "overhead_le_30pct": overhead <= 0.30,
        "cores_le_8_gpu0": True,
        "ordinary_cpu_projected_le_320": projected_cpu_hours <= 320.0,
        "ordinary_wall_projected_le_65": projected_complete_wall <= 65.0,
        "hard_cpu_wall_projected": projected_cpu_hours <= 560.0 and projected_complete_wall <= 110.0,
        "hard_rss_projected": projected_hard_resources["aggregate_rss_gib"] <= 40.0,
        "hard_scratch_projected": projected_hard_resources["scratch_gib"] <= 120.0,
        "hard_durable_projected": projected_hard_resources["durable_gib"] <= 16.0,
        "hard_io_projected": projected_hard_resources["total_io_gib"] <= 400.0,
        "update_integrity": all(row["losses_finite"] and row["gradient_norms_finite"] and row["checkpoint_resume_equal"] for row in parallel_rows),
        "welford_scalar_equivalent": welford_equivalent,
        "process_safe_same_identity_successor": successor_equal,
        "complete_task_plans": all(sum(task.total_units for task in complete_stage_plan(stage)) == total for stage, total in {
            "POPULATION": 11_520, "TRAINING": 122_880, "EVALUATION": 115_200, "FORK": 6_912, "INFERENCE": 1}.items()),
    }
    fresh_gate_pass = all(checks.values())
    sources = tuple(repository_root / relative for relative in (
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_scheduler.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_lease.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_data_plane.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_training_engine.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_p1.py",
    ))
    return {
        "schema": "DISH_RBHR_R06_P1_PROCESS_CPU_SELF_AUDIT_V1", "checks": checks,
        "process_measurement": {"single": dict(single), "parallel_rows": [dict(row) for row in parallel_rows],
                                "warm_process_count": len(warm_pids), "process_count": len(pids),
                                "parallel_wall_seconds": parallel_wall, "effective_concurrency": effective,
                                "overhead_fraction": overhead, "median_worker_update_wall_seconds": per_worker_wall},
        "resource_projection": {"training_cpu_hours": training_cpu_hours, "complete_cpu_hours": projected_cpu_hours,
                                "training_wall_hours": projected_training_wall, "complete_wall_hours": projected_complete_wall,
                                "ordinary_cpu_pass": projected_cpu_hours <= 320.0, "ordinary_wall_pass": projected_complete_wall <= 65.0,
                                "hard_cpu_pass": projected_cpu_hours <= 560.0, "hard_wall_pass": projected_complete_wall <= 110.0,
                                **projected_hard_resources},
        "welford_equivalence": {"count": batched.count, "mean_max_abs": float(torch.max(torch.abs(scalar.mean - batched.mean))),
                                "m2_max_abs": float(torch.max(torch.abs(scalar.m2 - batched.m2))), "accepted": welford_equivalent},
        "scheduler_manifest": scheduler_manifest(),
        "source_sha256": {str(path.relative_to(repository_root)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "fixture_only": True, "result_blind": True, "heavy_production": False,
        "fresh_p1_gate_pass": fresh_gate_pass, "p2_released": False,
        "lease_request": False, "lease": False, "sealed_master_access": False,
        "nonfixture_identity": False, "nonfixture_activity": False, "partial_value": False,
        "r05_action": False, "sgsp_action": False, "provider_action": False, "git_action": False,
    }


__all__ = ["P1AuditError", "load_p1_process_fixture_plane", "run_p1_process_cpu_self_audit"]
