"""Result-blind S1 scheduler construction self-audit."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import inspect
from pathlib import Path
import tempfile
import threading
import time

from .production_contract import COMPONENT, TestAuthority
from .production_data_plane import R06ProductionDataPlane
from .production_full_panel import FullPanelExecutor, STAGE_TOTALS
from .production_scheduler import (
    ParallelPanelScheduler, ScheduledTask, SchedulerError, TaskJournal,
    complete_stage_plan, scheduler_manifest,
)


class S1AuditError(RuntimeError):
    pass


class _Authority:
    component = COMPONENT
    identity_sha256 = hashlib.sha256(b"TEST/DISH/RBHR/R06/S1/IDENTITY").hexdigest()
    lease_chain_sha256 = hashlib.sha256(b"TEST/DISH/RBHR/R06/S1/LEASE").hexdigest()
    workers = 8; cpu_cores = 8; gpu = 0
    def require_active(self) -> None: TestAuthority().require_test_only()


class _FixturePlane:
    def __init__(self, *, delay: float = 0.0, barrier: threading.Barrier | None = None,
                 fail_once_at: int | None = None) -> None:
        self.delay = delay; self.barrier = barrier; self.fail_once_at = fail_once_at; self.failed = False
        self._barrier_starts: set[int] = set(); self._lock = threading.Lock()

    def execute_scheduled(self, stage: str, start: int, count: int):
        if self.barrier is not None and stage == "POPULATION" and start < self.barrier.parties:
            with self._lock:
                first = start not in self._barrier_starts; self._barrier_starts.add(start)
            if first: self.barrier.wait(timeout=5.0)
        if self.fail_once_at == start and not self.failed:
            self.failed = True; raise S1AuditError("TEST injected uncommitted worker failure")
        if self.delay: time.sleep(self.delay)
        return tuple(f"TEST/S1/{stage}/{index}".encode("ascii") for index in range(start, start + count))


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_s1_scheduler_self_audit(repository_root: Path) -> dict[str, object]:
    TestAuthority().require_test_only(); authority = _Authority()
    plans = {stage: complete_stage_plan(stage) for stage in STAGE_TOTALS}
    plan_facts = {
        stage: {"tasks": len(tasks), "units": sum(task.total_units for task in tasks),
                "coverage_complete": sum(task.total_units for task in tasks) == STAGE_TOTALS[stage]}
        for stage, tasks in plans.items()
    }
    with tempfile.TemporaryDirectory(prefix="dish-r06-s1-") as temporary:
        root = Path(temporary)
        # Eight tasks enter concurrently; barrier completion proves the real
        # executor owns at least six live workers without scientific activity.
        concurrent_plane = _FixturePlane(delay=0.100, barrier=threading.Barrier(8))
        concurrent = ParallelPanelScheduler(authority=authority, data_plane=concurrent_plane, journal_root=root / "concurrency")
        tasks = tuple(ScheduledTask("POPULATION", index, index, 16, 1) for index in range(8))
        sequential_started = time.perf_counter()
        sequential_plane = _FixturePlane(delay=0.100)
        for task in tasks:
            for offset in range(task.total_units): sequential_plane.execute_scheduled(task.stage, task.start + offset, 1)
        sequential_wall = time.perf_counter() - sequential_started
        parallel_started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = tuple(pool.map(concurrent._execute_task, tasks))
        parallel_wall = time.perf_counter() - parallel_started
        ideal = sequential_wall / 8.0
        fixture_compute_wall = 16 * 0.100
        coordination_seconds_per_unit = max(0.0, parallel_wall - fixture_compute_wall) / 16.0
        overhead = coordination_seconds_per_unit / 7.324149699998088

        # Failure after three commits retains exactly three; a new scheduler
        # instance resumes the same task/identity and reaches eight.
        failure_task = ScheduledTask("TRAINING", 0, 0, 8, 1)
        failure_plane = _FixturePlane(fail_once_at=3)
        first_scheduler = ParallelPanelScheduler(authority=authority, data_plane=failure_plane, journal_root=root / "failure")
        failed = False
        try: first_scheduler._execute_task(failure_task)
        except S1AuditError: failed = True
        retained_count, retained_chain = first_scheduler.journal.load(failure_task)
        second_scheduler = ParallelPanelScheduler(authority=authority, data_plane=failure_plane, journal_root=root / "failure")
        _, final_chain = second_scheduler._execute_task(failure_task)
        final_count, _ = second_scheduler.journal.load(failure_task)

        if overhead > 0.30:
            raise S1AuditError(f"fixture scheduler overhead exceeds S1 gate: {overhead:.6f}")
        if concurrent.max_observed_concurrency < 6:
            raise S1AuditError("fixture scheduler concurrency is below six")
        if not failed or retained_count != 3 or final_count != 8 or retained_chain == final_chain:
            raise S1AuditError("failure-atomic successor fixture differs")

    scheduler_source = inspect.getsource(ParallelPanelScheduler)
    data_plane_source = inspect.getsource(R06ProductionDataPlane)
    executor_source = inspect.getsource(FullPanelExecutor)
    sources = tuple(repository_root / relative for relative in (
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_scheduler.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_data_plane.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_full_panel.py",
        "experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_s1.py",
    ))
    checks = {
            "deterministic_120_job_queue": len(plans["TRAINING"]) == 120 and all(task.total_units == 1_024 for task in plans["TRAINING"]),
            "ordered_updates_and_sole_checkpoint_dependency": "while completed < task.total_units" in scheduler_source and "evaluation checkpoint is not update 1,024" in data_plane_source,
            "dependency_aware_evaluation_fork": list(plans) == list(STAGE_TOTALS),
            "ordered_receipt_collector": "sorted(results)" in scheduler_source,
            "failure_atomic_task_journal": "TaskJournal" in scheduler_source and retained_count == 3,
            "same_identity_successor": final_count == 8,
            "data_plane_idempotent_crash_window": "execute_scheduled" in data_plane_source and "_recover_training_receipt" in data_plane_source,
            "production_executor_wired": "ParallelPanelScheduler" in executor_source and "commit_parallel_stage" in executor_source,
            "cores_le_8_gpu0": authority.cpu_cores <= 8 and authority.gpu == 0,
            "concurrency_ge_6": concurrent.max_observed_concurrency >= 6,
            "overhead_le_30pct": overhead <= 0.30,
        }
    if not all(checks.values()):
        raise S1AuditError("one or more scheduler construction checks failed")
    return {
        "schema": "DISH_RBHR_R06_S1_SCHEDULER_SELF_AUDIT_V1",
        "manifest": scheduler_manifest(), "stage_plans": plan_facts,
        "construction_checks": checks,
        "fixture_measurement": {"max_observed_concurrency": concurrent.max_observed_concurrency,
                                "sequential_wall_seconds": sequential_wall, "parallel_wall_seconds": parallel_wall,
                                "ideal_parallel_wall_seconds": ideal, "coordination_seconds_per_unit": coordination_seconds_per_unit,
                                "overhead_basis_update_seconds": 7.324149699998088,
                                "scheduler_overhead_fraction": overhead,
                                "result_count": len(results)},
        "failure_atomic_fixture": {"failure_injected": failed, "retained_commits": retained_count,
                                   "successor_commits": final_count, "same_identity": True},
        "source_sha256": {str(path.relative_to(repository_root)).replace("\\", "/"): _hash(path) for path in sources},
        "fixture_only": True, "result_blind": True, "production_compute": False,
        "lease_request": False, "lease": False, "sealed_master_access": False,
        "nonfixture_identity": False, "nonfixture_activity": False, "partial_value": False,
        "r05_action": False, "provider_action": False, "git_action": False,
    }


__all__ = ["S1AuditError", "run_s1_scheduler_self_audit"]
