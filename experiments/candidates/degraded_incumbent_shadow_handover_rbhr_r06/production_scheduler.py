"""Deterministic <=8-core failure-atomic scheduler for the R06 panel."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import importlib
import json
import multiprocessing
import os
from pathlib import Path
import threading
import time
from typing import Mapping, Sequence

from .production_full_panel import STAGE_ORDER, STAGE_TOTALS, FullPanelError


class SchedulerError(RuntimeError):
    pass


_PROCESS_DATA_PLANE: object | None = None


@dataclass(frozen=True)
class ProcessWorkerSpec:
    loader_module: str
    loader_function: str
    loader_kwargs: Mapping[str, object]

    def validate(self) -> None:
        if not self.loader_module or not self.loader_function or not isinstance(self.loader_kwargs, Mapping):
            raise SchedulerError("process worker loader specification differs")


def _initialize_process_worker(spec_value: Mapping[str, object], slot_counter: object | None = None,
                               slot_lock: object | None = None, cpu_count: int = 8) -> None:
    global _PROCESS_DATA_PLANE
    spec = ProcessWorkerSpec(str(spec_value["loader_module"]), str(spec_value["loader_function"]), dict(spec_value["loader_kwargs"]))
    spec.validate()
    os.environ["OMP_NUM_THREADS"] = "1"; os.environ["MKL_NUM_THREADS"] = "1"
    slot = 0
    if slot_counter is not None and slot_lock is not None:
        with slot_lock:
            slot = int(slot_counter.value); slot_counter.value += 1
    if os.name == "nt" and bool(spec_value.get("pin_affinity", False)):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.argtypes = []; kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
        kernel32.GetProcessAffinityMask.restype = ctypes.c_int
        kernel32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]; kernel32.SetProcessAffinityMask.restype = ctypes.c_int
        process = kernel32.GetCurrentProcess()
        process_mask = ctypes.c_size_t(); system_mask = ctypes.c_size_t()
        if not kernel32.GetProcessAffinityMask(process, ctypes.byref(process_mask), ctypes.byref(system_mask)):
            raise SchedulerError("process worker CPU affinity inventory failed")
        allowed = [index for index in range(ctypes.sizeof(ctypes.c_size_t) * 8) if process_mask.value & (1 << index)]
        if not allowed:
            raise SchedulerError("process worker CPU affinity inventory is empty")
        target = max(1, min(int(cpu_count), len(allowed)))
        strategy = str(spec_value.get("affinity_strategy", "compact"))
        bounded = allowed[:target] if strategy == "compact" else [allowed[(index * len(allowed)) // target] for index in range(target)]
        mask = 1 << bounded[slot % len(bounded)]
        if not kernel32.SetProcessAffinityMask(process, mask):
            raise SchedulerError("process worker CPU affinity failed")
    if os.name == "nt" and bool(spec_value.get("high_priority", False)):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcess.argtypes = []; kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]; kernel32.SetPriorityClass.restype = ctypes.c_int
        if not kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x00000080):
            raise SchedulerError("process worker priority assignment failed")
    if os.name == "nt" and bool(spec_value.get("ideal_processor", False)):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentThread.argtypes = []; kernel32.GetCurrentThread.restype = ctypes.c_void_p
        kernel32.SetThreadIdealProcessor.argtypes = [ctypes.c_void_p, ctypes.c_uint32]; kernel32.SetThreadIdealProcessor.restype = ctypes.c_uint32
        if kernel32.SetThreadIdealProcessor(kernel32.GetCurrentThread(), slot % max(1, int(cpu_count))) == 0xFFFFFFFF:
            raise SchedulerError("process worker ideal-processor assignment failed")
    import torch
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    loader = getattr(importlib.import_module(spec.loader_module), spec.loader_function)
    loaded = loader(**dict(spec.loader_kwargs))
    _PROCESS_DATA_PLANE = loaded[1] if isinstance(loaded, tuple) and len(loaded) == 2 else loaded


def _process_execute_task(task: "ScheduledTask", journal_root: str, identity_sha256: str) -> tuple[int, str, int]:
    if _PROCESS_DATA_PLANE is None:
        raise SchedulerError("process worker data plane is uninitialized")
    journal = TaskJournal(Path(journal_root), identity_sha256=identity_sha256)
    completed, chain = journal.load(task)
    execute = getattr(_PROCESS_DATA_PLANE, "execute_scheduled", None)
    if not callable(execute):
        raise SchedulerError("process data plane lacks scheduled execution")
    while completed < task.total_units:
        start = task.start + completed
        receipts = tuple(bytes(row) for row in execute(task.stage, start, task.unit_width))
        if len(receipts) != task.unit_width or any(not row for row in receipts):
            raise SchedulerError("process scheduled receipt inventory differs")
        chain = ParallelPanelScheduler._chain(chain, receipts); completed += task.unit_width
        journal.commit(task, completed=completed, chain=chain)
    return task.task_index, chain, os.getpid()


@dataclass(frozen=True, order=True)
class ScheduledTask:
    stage: str
    task_index: int
    start: int
    total_units: int
    unit_width: int

    def validate(self) -> None:
        if self.stage not in STAGE_TOTALS or self.task_index < 0 or self.start < 0:
            raise SchedulerError("scheduled task coordinate differs")
        if self.total_units <= 0 or self.unit_width <= 0 or self.total_units % self.unit_width:
            raise SchedulerError("scheduled task width differs")
        if self.start + self.total_units > STAGE_TOTALS[self.stage]:
            raise SchedulerError("scheduled task exceeds stage inventory")


def complete_stage_plan(stage: str) -> tuple[ScheduledTask, ...]:
    if stage == "POPULATION":
        tasks = tuple(ScheduledTask(stage, index, 32 * index, 32, 32) for index in range(360))
    elif stage == "TRAINING":
        tasks = tuple(ScheduledTask(stage, job, 1_024 * job, 1_024, 1) for job in range(120))
    elif stage == "EVALUATION":
        tasks = tuple(ScheduledTask(stage, index, 32 * index, 32, 32) for index in range(3_600))
    elif stage == "FORK":
        tasks = tuple(ScheduledTask(stage, index, 32 * index, 32, 32) for index in range(216))
    elif stage == "INFERENCE":
        tasks = (ScheduledTask(stage, 0, 0, 1, 1),)
    else:
        raise SchedulerError("unknown scheduled stage")
    for task in tasks: task.validate()
    ordered = sorted((unit, task.task_index) for task in tasks for unit in range(task.start, task.start + task.total_units))
    if len(ordered) != STAGE_TOTALS[stage] or [unit for unit, _ in ordered] != list(range(STAGE_TOTALS[stage])):
        raise SchedulerError("scheduled stage coverage differs")
    return tasks


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _replace(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}-{threading.get_ident()}")
    with temporary.open("xb") as stream:
        stream.write(_canonical(value)); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


class TaskJournal:
    """One create/replace atomic progress row per independent scheduled task."""

    def __init__(self, root: Path, *, identity_sha256: str) -> None:
        if len(identity_sha256) != 64:
            raise SchedulerError("scheduler identity binding differs")
        self.root = root.resolve(); self.identity_sha256 = identity_sha256

    def path(self, task: ScheduledTask) -> Path:
        return self.root / task.stage.lower() / f"task-{task.task_index:05d}.json"

    def load(self, task: ScheduledTask) -> tuple[int, str]:
        path = self.path(task)
        if not path.exists(): return 0, "0" * 64
        value = json.loads(path.read_text(encoding="ascii"))
        expected = {"schema", "identity_sha256", "stage", "task_index", "start", "total_units", "unit_width", "completed_units", "receipt_chain_sha256"}
        if set(value) != expected or value["identity_sha256"] != self.identity_sha256:
            raise SchedulerError("scheduler journal binding differs")
        if (value["stage"], value["task_index"], value["start"], value["total_units"], value["unit_width"]) != (
            task.stage, task.task_index, task.start, task.total_units, task.unit_width,
        ):
            raise SchedulerError("scheduler journal task differs")
        completed = int(value["completed_units"]); chain = str(value["receipt_chain_sha256"])
        if completed < 0 or completed > task.total_units or completed % task.unit_width or len(chain) != 64:
            raise SchedulerError("scheduler journal frontier differs")
        return completed, chain

    def commit(self, task: ScheduledTask, *, completed: int, chain: str) -> None:
        if completed <= 0 or completed > task.total_units or completed % task.unit_width or len(chain) != 64:
            raise SchedulerError("scheduler journal commit differs")
        prior_completed, _ = self.load(task)
        if completed != prior_completed + task.unit_width:
            raise SchedulerError("scheduler task commit is not consecutive")
        _replace(self.path(task), {
            "schema": "DISH_RBHR_R06_SCHEDULER_TASK_JOURNAL_V1", "identity_sha256": self.identity_sha256,
            "stage": task.stage, "task_index": task.task_index, "start": task.start,
            "total_units": task.total_units, "unit_width": task.unit_width,
            "completed_units": completed, "receipt_chain_sha256": chain,
        })


class ParallelPanelScheduler:
    """Run independent tasks concurrently and expose only ordered task digests."""

    def __init__(self, *, authority: object, data_plane: object, journal_root: Path) -> None:
        require = getattr(authority, "require_active", None)
        if not callable(require): raise SchedulerError("scheduler requires active authority")
        require()
        workers = int(getattr(authority, "workers", 0)); cores = int(getattr(authority, "cpu_cores", 0)); gpu = int(getattr(authority, "gpu", -1))
        if not 6 <= workers <= 8 or not 6 <= cores <= 8 or workers > cores or gpu != 0:
            raise SchedulerError("scheduler requires 6..8 workers within <=8 CPU cores and GPU0")
        self.authority = authority; self.data_plane = data_plane; self.workers = workers; self.cores = cores
        self.journal = TaskJournal(journal_root, identity_sha256=str(getattr(authority, "identity_sha256", "")))
        raw_spec = getattr(data_plane, "process_worker_spec", None)
        if not isinstance(raw_spec, Mapping):
            raise SchedulerError("production scheduler requires an isolated-process worker specification")
        self.worker_spec = dict(raw_spec)
        ProcessWorkerSpec(str(self.worker_spec.get("loader_module", "")), str(self.worker_spec.get("loader_function", "")), dict(self.worker_spec.get("loader_kwargs", {}))).validate()
        self.max_observed_concurrency = 0

    @staticmethod
    def _chain(previous: str, receipts: Sequence[bytes]) -> str:
        chain = previous
        for receipt in receipts: chain = hashlib.sha256(bytes.fromhex(chain) + bytes(receipt)).hexdigest()
        return chain

    def run_stage(self, stage: str) -> tuple[str, ...]:
        prepare = getattr(self.data_plane, "prepare_parallel_stage", None)
        if callable(prepare): prepare(stage=stage, workers=self.workers, total_cores=self.cores)
        tasks = complete_stage_plan(stage); results: dict[int, str] = {}; pids: set[int] = set()
        context = multiprocessing.get_context("spawn")
        counter = context.Value("i", 0); lock = context.Lock()
        with ProcessPoolExecutor(max_workers=self.workers, mp_context=context,
                                 initializer=_initialize_process_worker,
                                 initargs=(self.worker_spec, counter, lock, self.cores)) as pool:
            futures = {pool.submit(_process_execute_task, task, str(self.journal.root), self.journal.identity_sha256): task for task in tasks}
            for future in as_completed(futures):
                index, digest, pid = future.result(); results[index] = digest; pids.add(pid)
        self.max_observed_concurrency = max(self.max_observed_concurrency, len(pids))
        if set(results) != {task.task_index for task in tasks}:
            raise SchedulerError("scheduled stage result inventory differs")
        return tuple(results[index] for index in sorted(results))

    def run_slice(self, *, executor: object, max_units: int) -> Mapping[str, object]:
        if max_units <= 0: raise FullPanelError("slice unit budget must be positive")
        frontier = executor.load_or_create_frontier(); used = 0
        while frontier.stage != "COMPLETE":
            total = STAGE_TOTALS[frontier.stage]
            if frontier.stage_index != 0:
                raise SchedulerError("parallel scheduler requires stage-atomic global frontier")
            if used + total > max_units: break
            reason = executor._guard(frontier)
            if reason:
                frontier.terminal = reason; break
            started_wall = time.perf_counter(); started_cpu = time.process_time()
            digests = self.run_stage(frontier.stage)
            executor.commit_parallel_stage(frontier, digests=digests,
                                           cpu_seconds=time.process_time() - started_cpu,
                                           wall_seconds=time.perf_counter() - started_wall)
            used += total
        return executor.finish_slice(frontier)


def scheduler_manifest() -> Mapping[str, object]:
    return {
        "schema": "DISH_RBHR_R06_PARALLEL_SCHEDULER_MANIFEST_V1",
        "worker_substrate": "ISOLATED_SPAWN_PROCESSES",
        "workers_min": 6, "workers_max": 8, "cpu_cores_max": 8, "gpu": 0,
        "training_tasks": 120, "updates_per_training_task": 1_024,
        "evaluation_tasks": 3_600, "fork_tasks": 216,
        "deterministic_ordered_task_digest_commit": True,
        "per_task_failure_atomic_journal": True, "same_identity_successor": True,
        "partial_values_exposed": False,
    }


__all__ = ["ParallelPanelScheduler", "ProcessWorkerSpec", "ScheduledTask", "SchedulerError", "TaskJournal",
           "complete_stage_plan", "scheduler_manifest"]
