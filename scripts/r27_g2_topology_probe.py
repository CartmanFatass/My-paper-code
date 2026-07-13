"""Bounded operational probe for the R27-G2 multi-process CUDA topology.

This program is deliberately not an R27-G2 evidence collector.  Each spawned
worker loads the registered final checkpoint into its own CUDA process, creates
one real Scenario-7 environment, performs real high/low-agent and environment
forwards, allocates the normal in-memory reset artifact, and then waits at a
process barrier.  The barrier proves simultaneous residency; the result only
classifies the execution topology as operational PASS/FAIL.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import queue
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CHECKPOINT = (
    ROOT
    / "dist"
    / "logs_cloud_r25_qa_verification_1m"
    / "arm0_arch_only"
    / "seed1"
    / "standalone_process_core_final.pt"
)
EXPECTED_UPDATE = 32
EXPECTED_TOTAL_STEPS = 1_000_000
DEFAULT_WORKERS = 8
DEFAULT_RESIDENCY_SECONDS = 300.0
DEFAULT_STARTUP_TIMEOUT_SECONDS = 480.0
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_WALL_SECONDS = 900.0
DEFAULT_MIN_FREE_GPU_MIB = 4096.0
DEFAULT_MIN_FREE_HOST_MIB = 8192.0
DEFAULT_MIN_FREE_HOST_FRACTION = 0.15


@dataclass(frozen=True)
class WorkerConfig:
    checkpoint: str
    worker_count: int
    residency_seconds: float
    startup_timeout_seconds: float
    fixture: bool
    fixture_fail_worker: int
    fixture_resource_fail_worker: int


def _host_memory() -> tuple[float | None, float | None]:
    """Return Linux MemAvailable and MemTotal in MiB when available."""

    path = Path("/proc/meminfo")
    if not path.is_file():
        return None, None
    values: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, remainder = line.partition(":")
        if not separator:
            continue
        fields = remainder.strip().split()
        if fields:
            values[key] = float(fields[0]) / 1024.0
    return values.get("MemAvailable"), values.get("MemTotal")


def _queue_message(message_queue: Any, **payload: Any) -> None:
    message_queue.put({"monotonic": time.monotonic(), **payload})


def _fixture_worker(
    worker_id: int,
    config: WorkerConfig,
    barrier: Any,
    message_queue: Any,
) -> None:
    if worker_id == config.fixture_fail_worker:
        raise RuntimeError(f"fixture worker {worker_id} requested failure")
    if worker_id == config.fixture_resource_fail_worker:
        raise MemoryError(f"fixture worker {worker_id} out of memory")
    resident_buffer = bytearray(1024 * 1024)
    _queue_message(
        message_queue,
        worker_id=worker_id,
        phase="ready",
        pid=os.getpid(),
        reset_id=worker_id,
        checkpoint_update=EXPECTED_UPDATE,
        checkpoint_total_steps=EXPECTED_TOTAL_STEPS,
        cuda_device="fixture",
        gpu_name="fixture",
        cuda_allocated_mib=1.0,
        cuda_reserved_mib=1.0,
        cuda_max_reserved_mib=1.0,
        artifact_mib=float(len(resident_buffer)) / (1024.0 * 1024.0),
        initial_forward_seconds=0.001,
    )
    barrier.wait(timeout=config.startup_timeout_seconds)
    _queue_message(
        message_queue,
        worker_id=worker_id,
        phase="resident",
        gpu_free_mib=65536.0,
        gpu_total_mib=65536.0,
        host_available_mib=131072.0,
        host_total_mib=262144.0,
    )
    time.sleep(config.residency_seconds)
    _queue_message(
        message_queue,
        worker_id=worker_id,
        phase="passed",
        activity_cycles=1,
        gpu_free_mib=65536.0,
        gpu_total_mib=65536.0,
    )


def _production_worker(
    worker_id: int,
    config: WorkerConfig,
    barrier: Any,
    message_queue: Any,
) -> None:
    # These must be fixed before this child initializes CUDA.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")

    import random

    import numpy as np
    import torch

    from ha_ctse_process.r27_g2_collector import (
        R27G2ResetArtifact,
        build_branch_specs,
        prefix_policy_seed_for_reset,
        prefix_steps_for_reset,
    )
    from ha_ctse_process.r27_g2_runtime import configure_deterministic_cuda
    from scripts.audit_r27_forced_trajectory_effect import (
        _configure_agent,
        _state_from_info,
        validate_collect_args,
    )

    torch.set_num_threads(1)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; topology probe forbids CPU fallback")
    configure_deterministic_cuda("cuda")

    reset_id = int(worker_id)
    source_args = argparse.Namespace(
        checkpoint=config.checkpoint,
        checkpoint_id="arm0_final",
        checkpoint_update=EXPECTED_UPDATE,
        config="ha_ctse_process.config",
        scenario="energy",
        preset="S7-S1",
        n_agents=6,
        device="cuda",
        reset_id=reset_id,
    )
    validate_collect_args(source_args)
    (
        _algorithm_config,
        _metadata,
        agent,
        env_factory,
        total_steps,
        loaded_update,
        loaded_value_norm_equal,
    ) = _configure_agent(source_args)
    if str(agent.device).split(":", maxsplit=1)[0] != "cuda":
        raise RuntimeError("agent silently left CUDA")
    if int(loaded_update) != EXPECTED_UPDATE:
        raise RuntimeError(f"final checkpoint update mismatch: {loaded_update}")
    if int(total_steps) != EXPECTED_TOTAL_STEPS:
        raise RuntimeError(f"final checkpoint total_steps mismatch: {total_steps}")
    if not bool(loaded_value_norm_equal):
        raise RuntimeError("final checkpoint ValueNorm load mismatch")

    env = env_factory()
    artifact = None
    try:
        obs, info = env.reset(seed=reset_id + 1)
        obs = np.asarray(obs, dtype=np.float32)
        state = np.asarray(_state_from_info(info), dtype=np.float32).reshape(-1)
        agent.reset_env_state(0)
        if hasattr(agent.segments, "active"):
            agent.segments.active[0] = [None for _ in range(6)]

        policy_seed = prefix_policy_seed_for_reset(reset_id)
        random.seed(policy_seed)
        np.random.seed(policy_seed)
        torch.manual_seed(policy_seed)
        torch.cuda.manual_seed_all(policy_seed)

        started_forward = time.monotonic()
        with torch.no_grad():
            agent.maybe_assign_skills(
                obs,
                state=state,
                step=0,
                k=10,
                env_id=0,
                deterministic=False,
            )
            actions, _logp, _values = agent.act_low(
                obs,
                env_id=0,
                deterministic=False,
                state=state,
            )
        next_obs, _reward, terminated, truncated, next_info = env.step(actions)
        if bool(terminated or truncated):
            raise RuntimeError("topology probe environment ended on its first step")
        obs = np.asarray(next_obs, dtype=np.float32)
        state = np.asarray(_state_from_info(next_info), dtype=np.float32).reshape(-1)
        focal_skill = int(np.asarray(agent.active_skills[0], dtype=np.int64)[0])
        live = agent.r27_g2_audit_step(
            obs,
            env_id=0,
            state=state,
            focal_agent=0,
            focal_skill=focal_skill,
            focal_inactive_film=False,
        )
        next_obs, _reward, terminated, truncated, next_info = env.step(
            live["deterministic_action"]
        )
        if bool(terminated or truncated):
            raise RuntimeError("topology probe environment ended on its audit step")
        obs = np.asarray(next_obs, dtype=np.float32)
        state = np.asarray(_state_from_info(next_info), dtype=np.float32).reshape(-1)
        torch.cuda.synchronize(agent.device)
        initial_forward_seconds = time.monotonic() - started_forward

        natural_roster = np.asarray(agent.active_skills[0], dtype=np.int64).copy()
        artifact = R27G2ResetArtifact.allocate(
            reset_id=reset_id,
            prefix_steps=prefix_steps_for_reset(reset_id),
            obs_dim=int(obs.shape[1]),
            hidden_dim=int(agent.low_actor_hxs.shape[-1]),
            state_dim=int(state.size),
            branches=build_branch_specs(natural_roster),
        )
        artifact_mib = sum(
            value.nbytes
            for value in vars(artifact).values()
            if isinstance(value, np.ndarray)
        ) / (1024.0 * 1024.0)
        device_index = agent.device.index
        if device_index is None:
            device_index = torch.cuda.current_device()
        properties = torch.cuda.get_device_properties(device_index)
        _queue_message(
            message_queue,
            worker_id=worker_id,
            phase="ready",
            pid=os.getpid(),
            reset_id=reset_id,
            checkpoint_update=int(loaded_update),
            checkpoint_total_steps=int(total_steps),
            cuda_device=str(agent.device),
            gpu_name=str(properties.name),
            cuda_allocated_mib=float(torch.cuda.memory_allocated(device_index))
            / (1024.0 * 1024.0),
            cuda_reserved_mib=float(torch.cuda.memory_reserved(device_index))
            / (1024.0 * 1024.0),
            cuda_max_reserved_mib=float(
                torch.cuda.max_memory_reserved(device_index)
            )
            / (1024.0 * 1024.0),
            artifact_mib=float(artifact_mib),
            initial_forward_seconds=float(initial_forward_seconds),
        )

        barrier.wait(timeout=config.startup_timeout_seconds)
        torch.cuda.synchronize(agent.device)
        gpu_free, gpu_total = torch.cuda.mem_get_info(device_index)
        host_available, host_total = _host_memory()
        _queue_message(
            message_queue,
            worker_id=worker_id,
            phase="resident",
            gpu_free_mib=float(gpu_free) / (1024.0 * 1024.0),
            gpu_total_mib=float(gpu_total) / (1024.0 * 1024.0),
            host_available_mib=host_available,
            host_total_mib=host_total,
        )

        deadline = time.monotonic() + config.residency_seconds
        activity_cycles = 0
        while time.monotonic() < deadline:
            cycle_started = time.monotonic()
            focal_skill = int(np.asarray(agent.active_skills[0], dtype=np.int64)[0])
            live = agent.r27_g2_audit_step(
                obs,
                env_id=0,
                state=state,
                focal_agent=0,
                focal_skill=focal_skill,
                focal_inactive_film=False,
            )
            next_obs, _reward, terminated, truncated, next_info = env.step(
                live["deterministic_action"]
            )
            if bool(terminated or truncated):
                raise RuntimeError("topology probe environment ended during residency")
            obs = np.asarray(next_obs, dtype=np.float32)
            state = np.asarray(_state_from_info(next_info), dtype=np.float32).reshape(-1)
            torch.cuda.synchronize(agent.device)
            activity_cycles += 1
            remaining = min(1.0 - (time.monotonic() - cycle_started), deadline - time.monotonic())
            if remaining > 0:
                time.sleep(remaining)

        gpu_free, gpu_total = torch.cuda.mem_get_info(device_index)
        _queue_message(
            message_queue,
            worker_id=worker_id,
            phase="passed",
            activity_cycles=int(activity_cycles),
            gpu_free_mib=float(gpu_free) / (1024.0 * 1024.0),
            gpu_total_mib=float(gpu_total) / (1024.0 * 1024.0),
            cuda_max_reserved_mib=float(
                torch.cuda.max_memory_reserved(device_index)
            )
            / (1024.0 * 1024.0),
        )
    finally:
        # Keep the full-sized artifact resident until all activity is complete.
        _ = artifact
        env.close()


def _worker_entry(
    worker_id: int,
    config: WorkerConfig,
    barrier: Any,
    message_queue: Any,
) -> None:
    try:
        if config.fixture:
            _fixture_worker(worker_id, config, barrier, message_queue)
        else:
            _production_worker(worker_id, config, barrier, message_queue)
    except BaseException as error:  # Child failures must always reach the parent.
        try:
            barrier.abort()
        except BaseException:
            pass
        _queue_message(
            message_queue,
            worker_id=worker_id,
            phase="failed",
            pid=os.getpid(),
            error_type=type(error).__name__,
            error=str(error),
            traceback=traceback.format_exc(),
        )
        raise


def _validate_args(args: argparse.Namespace) -> None:
    if str(args.device).lower() != "cuda":
        raise ValueError("R27-G2 topology probe requires exact device=cuda")
    if not 2 <= int(args.workers) <= 64:
        raise ValueError("workers must be in 2..64; serial probing is not accepted")
    if int(args.fixture_fail_worker) >= int(args.workers):
        raise ValueError("fixture-fail-worker must be less than workers")
    if int(args.fixture_resource_fail_worker) >= int(args.workers):
        raise ValueError("fixture-resource-fail-worker must be less than workers")
    if float(args.min_free_gpu_mib) < DEFAULT_MIN_FREE_GPU_MIB:
        raise ValueError(
            f"min-free-gpu-mib cannot be below {DEFAULT_MIN_FREE_GPU_MIB}"
        )
    if float(args.min_free_host_mib) < DEFAULT_MIN_FREE_HOST_MIB:
        raise ValueError(
            f"min-free-host-mib cannot be below {DEFAULT_MIN_FREE_HOST_MIB}"
        )
    if not DEFAULT_MIN_FREE_HOST_FRACTION <= float(
        args.min_free_host_fraction
    ) <= 1.0:
        raise ValueError(
            "min-free-host-fraction must be in "
            f"[{DEFAULT_MIN_FREE_HOST_FRACTION}, 1.0]"
        )
    if bool(args.fixture):
        if float(args.residency_seconds) <= 0:
            raise ValueError("fixture residency-seconds must be positive")
        return
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file() or checkpoint.stat().st_size <= 0:
        raise FileNotFoundError(checkpoint)
    if not 300.0 <= float(args.residency_seconds) <= 600.0:
        raise ValueError("production residency-seconds must be in 300..600")
    if not 60.0 <= float(args.startup_timeout_seconds) <= 480.0:
        raise ValueError("production startup-timeout-seconds must be in 60..480")
    if not 10.0 <= float(args.shutdown_timeout_seconds) <= 120.0:
        raise ValueError("production shutdown-timeout-seconds must be in 10..120")
    if not 300.0 <= float(args.max_wall_seconds) <= 900.0:
        raise ValueError("production max-wall-seconds must be in 300..900")
    if (
        float(args.startup_timeout_seconds)
        + float(args.residency_seconds)
        + float(args.shutdown_timeout_seconds)
        > float(args.max_wall_seconds)
    ):
        raise ValueError("startup + residency + shutdown exceeds max-wall-seconds")


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _classify_probe_failure(
    *,
    passed: bool,
    records: Sequence[dict[str, Any]],
    failures: Sequence[str],
) -> str:
    """Classify the root failure without promoting barrier-abort cascades."""

    resource_markers = (
        "probe exceeded max-wall-seconds",
        "simultaneous residency before startup timeout",
        "GPU free memory",
        "host available memory",
        "host available fraction",
    )

    def worker_reports_resource_failure(item: dict[str, Any]) -> bool:
        error_text = (
            f"{item.get('error_type', '')} {item.get('error', '')}"
        ).lower()
        return any(
            marker in error_text
            for marker in (
                "outofmemory",
                "out of memory",
                "memoryerror",
                "cublas_status_alloc_failed",
                "cannot allocate memory",
                "std::bad_alloc",
                "resource temporarily unavailable",
                "not enough memory",
                "cannot start new thread",
                "can't start new thread",
                "errno 11",
                "errno 12",
            )
        )

    def worker_reports_barrier_cascade(item: dict[str, Any]) -> bool:
        return str(item.get("error_type", "")) == "BrokenBarrierError"

    if passed:
        return "NONE"
    worker_error_records = [item for item in records if item.get("error_type")]
    resource_controller_condition = any(
        any(marker in failure for marker in resource_markers)
        for failure in failures
    )
    resource_worker_condition = any(
        worker_reports_resource_failure(item) for item in worker_error_records
    )
    known_resource_condition = bool(
        resource_controller_condition or resource_worker_condition
    )
    non_resource_worker_error = any(
        not worker_reports_resource_failure(item)
        and not (
            resource_worker_condition and worker_reports_barrier_cascade(item)
        )
        for item in worker_error_records
    )
    unknown_bad_exit = bool(
        not known_resource_condition
        and any(
            item.get("exit_code") not in (0, None) and not item.get("error_type")
            for item in records
        )
    )
    if known_resource_condition and not non_resource_worker_error and not unknown_bad_exit:
        return "RESOURCE_CAPACITY"
    return "EXECUTION"


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    _validate_args(args)
    started = time.monotonic()
    context = mp.get_context("spawn")
    barrier = context.Barrier(int(args.workers))
    message_queue = context.Queue()
    config = WorkerConfig(
        checkpoint=str(Path(args.checkpoint).resolve()),
        worker_count=int(args.workers),
        residency_seconds=float(args.residency_seconds),
        startup_timeout_seconds=float(args.startup_timeout_seconds),
        fixture=bool(args.fixture),
        fixture_fail_worker=int(args.fixture_fail_worker),
        fixture_resource_fail_worker=int(args.fixture_resource_fail_worker),
    )
    processes = [
        context.Process(
            target=_worker_entry,
            args=(worker_id, config, barrier, message_queue),
            name=f"r27-g2-topology-{worker_id:02d}",
        )
        for worker_id in range(int(args.workers))
    ]
    workers: dict[int, dict[str, Any]] = {
        worker_id: {
            "worker_id": worker_id,
            "started": False,
            "ready": False,
            "resident": False,
            "passed": False,
        }
        for worker_id in range(int(args.workers))
    }
    failures: list[str] = []
    started_processes: list[tuple[int, Any]] = []
    for worker_id, process in enumerate(processes):
        try:
            process.start()
        except BaseException as error:
            workers[worker_id].update(
                {
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
            failures.append(
                f"worker {worker_id} {type(error).__name__}: {error}"
            )
            try:
                barrier.abort()
            except BaseException:
                pass
            break
        workers[worker_id]["started"] = True
        started_processes.append((worker_id, process))

    startup_deadline = started + float(args.startup_timeout_seconds)
    hard_deadline = started + float(args.max_wall_seconds)

    def consume(message: dict[str, Any]) -> None:
        worker_id = int(message["worker_id"])
        phase = str(message["phase"])
        record = workers[worker_id]
        record.update(
            {
                key: value
                for key, value in message.items()
                if key not in {"worker_id", "phase", "monotonic"}
            }
        )
        if phase == "ready":
            record["ready"] = True
        elif phase == "resident":
            record["resident"] = True
        elif phase == "passed":
            record["passed"] = True
        elif phase == "failed":
            failures.append(
                f"worker {worker_id} {record.get('error_type')}: {record.get('error')}"
            )

    while not failures:
        now = time.monotonic()
        if now >= hard_deadline:
            failures.append("probe exceeded max-wall-seconds")
            break
        if now >= startup_deadline and not all(
            item["resident"] for item in workers.values()
        ):
            failures.append("not all workers reached simultaneous residency before startup timeout")
            break
        try:
            consume(message_queue.get(timeout=min(0.2, hard_deadline - now)))
        except queue.Empty:
            pass
        if failures:
            break
        if all(item["passed"] for item in workers.values()):
            break
        for worker_id, process in started_processes:
            if process.exitcode not in (None, 0) and not workers[worker_id].get("passed"):
                failures.append(
                    f"worker {worker_id} exited early with code {process.exitcode}"
                )
                break
        if failures:
            break

    if failures:
        try:
            barrier.abort()
        except BaseException:
            pass
        for _worker_id, process in started_processes:
            if process.is_alive():
                process.terminate()

    shutdown_deadline = time.monotonic() + float(args.shutdown_timeout_seconds)
    for _worker_id, process in started_processes:
        process.join(timeout=max(0.0, shutdown_deadline - time.monotonic()))
    for _worker_id, process in started_processes:
        if process.is_alive():
            process.kill()
            process.join(timeout=1.0)

    while True:
        try:
            consume(message_queue.get_nowait())
        except queue.Empty:
            break

    for worker_id, process in started_processes:
        workers[worker_id]["exit_code"] = process.exitcode
        if process.exitcode != 0 and not any(
            item.startswith(f"worker {worker_id} ") for item in failures
        ):
            failures.append(f"worker {worker_id} exit_code={process.exitcode}")
    for worker_id, record in workers.items():
        if not bool(record["started"]):
            record["exit_code"] = None

    records = [workers[index] for index in sorted(workers)]
    ready_count = sum(bool(item["ready"]) for item in records)
    resident_count = sum(bool(item["resident"]) for item in records)
    passed_count = sum(bool(item["passed"]) for item in records)
    if ready_count != int(args.workers):
        failures.append(f"ready workers {ready_count}/{args.workers}")
    if resident_count != int(args.workers):
        failures.append(f"resident workers {resident_count}/{args.workers}")
    if passed_count != int(args.workers):
        failures.append(f"passed workers {passed_count}/{args.workers}")

    resident_records = [item for item in records if item["resident"]]
    gpu_free_values = [
        float(item["gpu_free_mib"])
        for item in resident_records
        if item.get("gpu_free_mib") is not None
    ]
    host_available_values = [
        float(item["host_available_mib"])
        for item in resident_records
        if item.get("host_available_mib") is not None
    ]
    host_fractions = [
        float(item["host_available_mib"]) / float(item["host_total_mib"])
        for item in resident_records
        if item.get("host_available_mib") is not None
        and item.get("host_total_mib") not in (None, 0)
    ]
    min_gpu_free = min(gpu_free_values, default=None)
    min_host_available = min(host_available_values, default=None)
    min_host_fraction = min(host_fractions, default=None)
    if min_gpu_free is None:
        failures.append("concurrent GPU free-memory evidence is missing")
    elif min_gpu_free < float(args.min_free_gpu_mib):
        failures.append(
            f"GPU free memory {min_gpu_free:.1f} MiB below {args.min_free_gpu_mib:.1f} MiB"
        )
    if min_host_available is None or min_host_fraction is None:
        failures.append("concurrent host memory evidence is missing")
    else:
        if min_host_available < float(args.min_free_host_mib):
            failures.append(
                f"host available memory {min_host_available:.1f} MiB below "
                f"{args.min_free_host_mib:.1f} MiB"
            )
        if min_host_fraction < float(args.min_free_host_fraction):
            failures.append(
                f"host available fraction {min_host_fraction:.3f} below "
                f"{args.min_free_host_fraction:.3f}"
            )
    if any(int(item.get("activity_cycles", 0)) < 1 for item in records):
        failures.append("one or more workers made no concurrent forward progress")

    # Preserve unique failure reasons without hiding their first occurrence.
    failures = list(dict.fromkeys(failures))
    passed = not failures
    failure_class = _classify_probe_failure(
        passed=passed,
        records=records,
        failures=failures,
    )
    resource_failure = failure_class == "RESOURCE_CAPACITY"
    operational_gate = "PASS" if passed else "FAIL"
    status = (
        f"FIXTURE_{operational_gate}" if bool(args.fixture) else operational_gate
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "probe": "r27_g2_independent_cuda_process_topology",
        "status": status,
        "operational_gate": operational_gate,
        "classification": "NOT_APPLICABLE",
        "scientific_evidence": False,
        "failure_class": failure_class,
        "resource_failure": resource_failure,
        "scientific_boundary": (
            "This bounded topology probe cannot support or alter any R27-G2 "
            "behavior/effect classification."
        ),
        "fixture": bool(args.fixture),
        "device": str(args.device),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_id": "arm0_final",
        "checkpoint_update": EXPECTED_UPDATE,
        "checkpoint_total_steps": EXPECTED_TOTAL_STEPS,
        "git_commit": str(args.git_commit),
        "workers_requested": int(args.workers),
        "workers_ready": int(ready_count),
        "workers_resident": int(resident_count),
        "workers_passed": int(passed_count),
        "residency_seconds": float(args.residency_seconds),
        "startup_timeout_seconds": float(args.startup_timeout_seconds),
        "shutdown_timeout_seconds": float(args.shutdown_timeout_seconds),
        "max_wall_seconds": float(args.max_wall_seconds),
        "wall_seconds": float(time.monotonic() - started),
        "minimum_gpu_free_mib": min_gpu_free,
        "required_gpu_free_mib": float(args.min_free_gpu_mib),
        "minimum_host_available_mib": min_host_available,
        "required_host_available_mib": float(args.min_free_host_mib),
        "minimum_host_available_fraction": min_host_fraction,
        "required_host_available_fraction": float(args.min_free_host_fraction),
        "failures": failures,
        "workers": records,
    }
    _atomic_json(Path(args.output), report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bounded non-scientific R27-G2 independent-CUDA-process probe"
    )
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--residency-seconds", type=float, default=DEFAULT_RESIDENCY_SECONDS
    )
    parser.add_argument(
        "--startup-timeout-seconds",
        type=float,
        default=DEFAULT_STARTUP_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--shutdown-timeout-seconds",
        type=float,
        default=DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--max-wall-seconds", type=float, default=DEFAULT_MAX_WALL_SECONDS
    )
    parser.add_argument(
        "--min-free-gpu-mib", type=float, default=DEFAULT_MIN_FREE_GPU_MIB
    )
    parser.add_argument(
        "--min-free-host-mib", type=float, default=DEFAULT_MIN_FREE_HOST_MIB
    )
    parser.add_argument(
        "--min-free-host-fraction",
        type=float,
        default=DEFAULT_MIN_FREE_HOST_FRACTION,
    )
    parser.add_argument("--git-commit", default="")
    parser.add_argument("--fixture", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--fixture-fail-worker", type=int, default=-1, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--fixture-resource-fail-worker",
        type=int,
        default=-1,
        help=argparse.SUPPRESS,
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_probe(args)
    except BaseException as error:
        report = {
            "schema_version": 1,
            "probe": "r27_g2_independent_cuda_process_topology",
            "status": "FIXTURE_FAIL" if bool(getattr(args, "fixture", False)) else "FAIL",
            "operational_gate": "FAIL",
            "classification": "NOT_APPLICABLE",
            "scientific_evidence": False,
            "failure_class": "EXECUTION",
            "resource_failure": False,
            "fixture": bool(getattr(args, "fixture", False)),
            "workers_requested": int(getattr(args, "workers", 0)),
            "workers_ready": 0,
            "workers_resident": 0,
            "workers_passed": 0,
            "failures": [f"{type(error).__name__}: {error}"],
        }
        try:
            _atomic_json(Path(args.output), report)
        except BaseException:
            pass
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0 if report["operational_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
