"""Phase-stratified result-blind benchmark for the retained UCOPE r03 S0 coupon."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, TypeVar

import numpy as np
import torch

from . import checkpoint, native_backend, reference_oracle
from .contract import (
    REGISTERED_MASTER_SEEDS,
    S1_TEST_NAMESPACE,
    S1_TEST_REQUEST,
    S1_TEST_SEEDS,
    TEST_NAMESPACE,
    TEST_SEEDS,
)
from .model import make_paired_bundles
from .s0_coupon import apply_update, finite_permutation_coupon, prepare_update, run_retained_coupon
from . import training


T = TypeVar("T")
SCHEMA = "UCOPE_R01_R03_S0_RESULT_BLIND_BENCHMARK_V1"
FULL_COUNTS = {
    "learned_replicas": 90,
    "episodes_per_replica": 81_920,
    "learned_training_episodes": 7_372_800,
    "optimizer_steps": 28_800,
    "trio_update_batches": 9_600,
    "learned_evaluation_cells": 1_006_080,
    "raw_permavg_candidate_rows": 2_560,
    "final_checkpoints": 90,
}
_S1_TEST_EXECUTED_WORKER_CAP = 16
_S1_TEST_MEASURED_WORKER_WIDTHS = (1, 2, 4, 8)
_S1_TEST_WORKER_TASK_COUNT = 8
_S1_COMPLETE_TRANSACTION_PROJECTION_CORE_CEILING = 24


if os.name == "nt":
    class _FileTime(ctypes.Structure):
        _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


    class _IoCounters(ctypes.Structure):
        _fields_ = [
            ("read_ops", ctypes.c_uint64), ("write_ops", ctypes.c_uint64),
            ("other_ops", ctypes.c_uint64), ("read_bytes", ctypes.c_uint64),
            ("write_bytes", ctypes.c_uint64), ("other_bytes", ctypes.c_uint64),
        ]


    class _MemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_uint32), ("page_faults", ctypes.c_uint32),
            ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t),
            ("peak_paged_pool", ctypes.c_size_t), ("paged_pool", ctypes.c_size_t),
            ("peak_nonpaged_pool", ctypes.c_size_t), ("nonpaged_pool", ctypes.c_size_t),
            ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t),
            ("private_usage", ctypes.c_size_t),
        ]


def _filetime(value: object) -> float:
    return float((int(value.high) << 32) | int(value.low)) / 10_000_000.0


def _resources() -> dict[str, float | int]:
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        kernel32.GetCurrentProcess.argtypes = []
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.GetProcessTimes.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime),
            ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime),
        ]
        kernel32.GetProcessTimes.restype = ctypes.c_int
        kernel32.GetProcessIoCounters.argtypes = [ctypes.c_void_p, ctypes.POINTER(_IoCounters)]
        kernel32.GetProcessIoCounters.restype = ctypes.c_int
        psapi.GetProcessMemoryInfo.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(_MemoryCounters), ctypes.c_uint32,
        ]
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        handle = kernel32.GetCurrentProcess()
        creation, exit_time, kernel, user = _FileTime(), _FileTime(), _FileTime(), _FileTime()
        if not kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)):
            raise OSError("GetProcessTimes failed")
        io = _IoCounters()
        if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
            raise OSError("GetProcessIoCounters failed")
        memory = _MemoryCounters()
        memory.cb = ctypes.sizeof(memory)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return {
            "cpu_seconds": _filetime(kernel) + _filetime(user),
            "read_bytes": int(io.read_bytes),
            "write_bytes": int(io.write_bytes),
            "rss_bytes": int(memory.working_set),
            "peak_rss_bytes": int(memory.peak_working_set),
        }
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "cpu_seconds": float(usage.ru_utime + usage.ru_stime),
        "read_bytes": int(usage.ru_inblock * 512),
        "write_bytes": int(usage.ru_oublock * 512),
        "rss_bytes": int(usage.ru_maxrss * (1024 if sys.platform != "darwin" else 1)),
        "peak_rss_bytes": int(usage.ru_maxrss * (1024 if sys.platform != "darwin" else 1)),
    }


def _measure(call: Callable[[], T]) -> tuple[T, dict[str, float | int]]:
    before = _resources()
    started = time.perf_counter()
    result = call()
    wall = time.perf_counter() - started
    after = _resources()
    return result, {
        "wall_seconds": wall,
        "cpu_seconds": max(0.0, float(after["cpu_seconds"]) - float(before["cpu_seconds"])),
        "read_bytes": max(0, int(after["read_bytes"]) - int(before["read_bytes"])),
        "write_bytes": max(0, int(after["write_bytes"]) - int(before["write_bytes"])),
        "peak_rss_bytes": max(int(before["peak_rss_bytes"]), int(after["peak_rss_bytes"])),
    }


def _digest(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes(order="C")).hexdigest()


def _is_lowercase_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )

def _observed_fp32_learning_evidence(observations: object) -> bool:
    if not isinstance(observations, dict):
        return False
    first_entropy_betas = observations.get("first_entropy_betas")
    second_entropy_betas = observations.get("second_entropy_betas")
    parameter_dtypes = observations.get("parameter_dtypes")
    optimizer_state_dtypes = observations.get("optimizer_state_dtypes")
    observed_optimizer_steps = observations.get("observed_optimizer_steps")
    if (
        not isinstance(first_entropy_betas, list)
        or not isinstance(second_entropy_betas, dict)
        or not isinstance(parameter_dtypes, dict)
        or not isinstance(optimizer_state_dtypes, dict)
        or not isinstance(observed_optimizer_steps, dict)
    ):
        return False
    second_uninterrupted = second_entropy_betas.get("uninterrupted")
    second_cold_resumed = second_entropy_betas.get("cold_resumed")
    expected_first_entropy_beta = 0.01 * (320 - 1) / 319
    expected_second_entropy_beta = 0.01 * (320 - 2) / 319
    try:
        entropy_betas_match = (
            len(first_entropy_betas) == 3
            and isinstance(second_uninterrupted, list)
            and len(second_uninterrupted) == 3
            and second_uninterrupted == second_cold_resumed
            and all(
                bool(
                    np.isclose(
                        float(value),
                        expected_first_entropy_beta,
                        rtol=1e-6,
                        atol=1e-8,
                    )
                )
                for value in first_entropy_betas
            )
            and all(
                bool(
                    np.isclose(
                        float(value),
                        expected_second_entropy_beta,
                        rtol=1e-6,
                        atol=1e-8,
                    )
                )
                for value in second_uninterrupted
            )
        )
    except (TypeError, ValueError):
        return False
    expected_dtypes = {
        "uninterrupted": ["torch.float32"],
        "cold_resumed": ["torch.float32"],
    }
    expected_optimizer_steps = {
        "after_first_update": [1],
        "after_cold_load": [1],
        "after_second_uninterrupted_update": [2],
        "after_second_resumed_update": [2],
    }
    return (
        entropy_betas_match
        and parameter_dtypes == expected_dtypes
        and optimizer_state_dtypes == expected_dtypes
        and observed_optimizer_steps == expected_optimizer_steps
    )


def _observed_support_evidence(support: object) -> bool:
    if not isinstance(support, dict):
        return False
    first_sha256 = support.get("first_sha256")
    second_sha256 = support.get("second_sha256")
    return (
        _is_lowercase_sha256(first_sha256)
        and _is_lowercase_sha256(second_sha256)
        and first_sha256 != second_sha256
        and support.get("sha256") == second_sha256
        and support.get("round_trip_equal") is True
        and support.get("first_to_second_monotone") is True
        and support.get("first_to_second_progressed") is True
    )


def _native_lifecycle(width: int, repeats: int) -> str:
    if width == 768:
        arms = np.repeat(np.arange(3, dtype=np.int32), 256)
    else:
        arms = np.arange(width, dtype=np.int32) % 3
    digest = hashlib.sha256()
    for repeat in range(repeats):
        batch = native_backend.reset_batch(
            seed=TEST_SEEDS[0], panel=repeat % 3, batch_index=repeat, arms=arms
        )
        try:
            root = batch.root_step(np.zeros(width, dtype=np.int32))
            tail = batch.tail_step(np.arange(width, dtype=np.int32) % 5)
            terminal = batch.terminal()
            digest.update(batch.episodes.tobytes())
            digest.update(root["actual_marks"].tobytes())
            digest.update(tail.tobytes())
            digest.update(terminal["totals"].tobytes())
        finally:
            batch.close()
    return digest.hexdigest()


def _oracle_lifecycle(width: int, repeats: int) -> str:
    digest = hashlib.sha256()
    for repeat in range(repeats):
        panel = repeat % 3
        for slot in range(width):
            row = reference_oracle.run_episode(
                seed=TEST_SEEDS[0], panel=panel, batch_index=repeat, slot=slot,
                arm=slot % 3, root_action=0, tail_action=slot % 5,
            )
            digest.update(row.actual_marks.tobytes())
            digest.update(row.components.tobytes())
            digest.update(np.asarray(row.total, dtype=np.float32).tobytes())
    return digest.hexdigest()

def _s1_native_lifecycle(width: int, repeats: int) -> str:
    if width == 768:
        arms = np.repeat(np.arange(3, dtype=np.int32), 256)
    else:
        arms = np.arange(width, dtype=np.int32) % 3
    test_seed = S1_TEST_SEEDS[0]
    digest = hashlib.sha256()
    for repeat in range(repeats):
        batch = native_backend.reset_batch(
            seed=test_seed, panel=repeat % 3, batch_index=repeat, arms=arms
        )
        try:
            root = batch.root_step(np.zeros(width, dtype=np.int32))
            tail = batch.tail_step(np.arange(width, dtype=np.int32) % 5)
            terminal = batch.terminal()
            digest.update(batch.episodes.tobytes())
            digest.update(root["actual_marks"].tobytes())
            digest.update(tail.tobytes())
            digest.update(terminal["totals"].tobytes())
        finally:
            batch.close()
    return digest.hexdigest()


def _s1_oracle_lifecycle(width: int, repeats: int) -> str:
    test_seed = S1_TEST_SEEDS[0]
    digest = hashlib.sha256()
    for repeat in range(repeats):
        panel = repeat % 3
        for slot in range(width):
            row = reference_oracle.run_s1_test_episode(
                namespace=S1_TEST_NAMESPACE,
                request=S1_TEST_REQUEST,
                seed=test_seed,
                panel=panel,
                batch_index=repeat,
                slot=slot,
                arm=slot % 3,
                root_action=0,
                tail_action=slot % 5,
            )
            digest.update(row.actual_marks.tobytes())
            digest.update(row.components.tobytes())
            digest.update(np.asarray(row.total, dtype=np.float32).tobytes())
    return digest.hexdigest()


def _cold_child(build_root: Path) -> dict[str, object]:
    _, measurement = _measure(lambda: native_backend.require_cpp_batched_backend(build_root=build_root))
    identity = native_backend.native_artifact_identity(build_root=build_root)
    return {"measurement": measurement, "identity": identity}


def _run_cold_process(build_root: Path) -> dict[str, object]:
    command = [
        sys.executable, "-m",
        "experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark",
        "--cold-child", "--build-root", str(build_root),
    ]
    started = time.perf_counter()
    completed = subprocess.run(
        command, cwd=Path(__file__).resolve().parents[4], capture_output=True,
        text=True, timeout=360, check=True,
    )
    wall = time.perf_counter() - started
    payload = json.loads(completed.stdout)
    payload["parent_observed_wall_seconds"] = wall
    payload["command"] = command
    return payload


def _worker_scaling(iterations: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    task_count = 8
    seeds = [TEST_SEEDS[1] + index for index in range(task_count)]

    def task(seed: int) -> np.ndarray:
        return native_backend.counter_fill(seed=seed, width=256, iterations=iterations)

    rows: list[dict[str, object]] = []
    baseline_wall = 0.0
    baseline_digests: list[str] = []
    for workers in (1, 2, 4, 8):
        def run() -> list[np.ndarray]:
            if workers == 1:
                return [task(seed) for seed in seeds]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(task, seeds))

        outputs, measurement = _measure(run)
        digests = [_digest(output) for output in outputs]
        if workers == 1:
            baseline_wall = float(measurement["wall_seconds"])
            baseline_digests = digests
        speedup = min(float(workers), baseline_wall / float(measurement["wall_seconds"]))
        efficiency = speedup / workers
        overhead = max(0.0, float(measurement["wall_seconds"]) / (baseline_wall / workers) - 1.0)
        cpu_concurrency = float(measurement["cpu_seconds"]) / max(float(measurement["wall_seconds"]), 1e-9)
        rows.append(
            {
                "workers": workers,
                **measurement,
                "speedup": speedup,
                "parallel_efficiency": efficiency,
                "effective_cpu_concurrency": cpu_concurrency,
                "effective_cpu_concurrency_fraction": min(1.0, cpu_concurrency / workers),
                "parallel_overhead_fraction": overhead,
                "fixture_digest": hashlib.sha256("".join(digests).encode("ascii")).hexdigest(),
                "sequential_parallel_byte_equal": digests == baseline_digests,
            }
        )
    eligible = [
        row for row in rows
        if int(row["workers"]) > 1
        and float(row["effective_cpu_concurrency_fraction"]) >= 0.75
        and float(row["parallel_overhead_fraction"]) <= 0.30
        and row["sequential_parallel_byte_equal"] is True
    ]
    selected = max(eligible, key=lambda row: int(row["workers"])) if eligible else rows[0]
    return rows, selected


def _benchmark(work_root: Path) -> dict[str, object]:
    torch.set_num_threads(1)
    cold = _run_cold_process(work_root / "cold_build")
    native_backend.clear_process_local_cache_for_tests()
    _, warm_initial = _measure(native_backend.require_cpp_batched_backend)
    _, warm_repeated = _measure(
        lambda: tuple(native_backend.require_cpp_batched_backend() for _ in range(1000))
    )
    identity = native_backend.native_artifact_identity()
    repository_root = Path(__file__).resolve().parents[4]
    source_paths = (
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/__init__.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/contract.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native/ucope_r01_r03_backend.cpp",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native_backend.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/reference_oracle.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/model.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/training.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/checkpoint.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s0_coupon.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/benchmark.py",
        "envs/native/production_backend.py",
        "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py",
    )
    source_hashes = _source_hash_map(repository_root, source_paths)
    reference_digest, reference_measurement = _measure(lambda: _oracle_lifecycle(32, 4))
    native_digest, native_measurement = _measure(lambda: _native_lifecycle(32, 4))
    reference_rate = 32 * 4 / float(reference_measurement["wall_seconds"])
    native_rate = 32 * 4 / float(native_measurement["wall_seconds"])
    throughput_speedup = native_rate / reference_rate

    width_rows: list[dict[str, object]] = []
    for width in (8, 32, 256, 768):
        digest, measurement = _measure(lambda width=width: _native_lifecycle(width, 3))
        width_rows.append(
            {
                "width": width,
                **measurement,
                "episodes": width * 3,
                "episodes_per_second": width * 3 / float(measurement["wall_seconds"]),
                "digest": digest,
            }
        )

    iterations = 1000
    while True:
        _, calibration = _measure(
            lambda: native_backend.counter_fill(
                seed=TEST_SEEDS[1], width=256, iterations=iterations
            )
        )
        if float(calibration["wall_seconds"]) >= 0.08 or iterations >= 256_000:
            break
        iterations *= 2
    worker_rows, selected_worker = _worker_scaling(iterations)

    coupon, coupon_measurement = _measure(
        lambda: run_retained_coupon(
            namespace=TEST_NAMESPACE, seed=TEST_SEEDS[0], panel=0,
            work_root=work_root / "coupon",
        )
    )
    bundles = make_paired_bundles(seed=TEST_SEEDS[1], panel=1)
    prepared, prepare_measurement = _measure(
        lambda: prepare_update(
            bundles, seed=TEST_SEEDS[1], panel=1, batch_index=7, build_root=None
        )
    )
    _, learner_measurement = _measure(
        lambda: apply_update(bundles, prepared, batch_number=8)
    )
    _, finite_measurement = _measure(lambda: finite_permutation_coupon(bundles[1]))
    metadata = {
        "completed_batch": 8,
        "next_batch": 9,
        "counter_frontier": str(prepared["frontier_digest"]),
        "batch_width": 768,
        "worker_count": 1,
        "torch_threads": 1,
        "source_sha256": str(identity["source_sha256"]),
        "native_artifact_sha256": str(identity["artifact_sha256"]),
    }
    checkpoint_path = work_root / "io" / "frontier.TEST_ONLY.pt"
    checkpoint_sha, checkpoint_measurement = _measure(
        lambda: checkpoint.save_atomic(checkpoint_path, bundles, metadata)
    )
    checkpoint_bytes = checkpoint_path.stat().st_size

    environment_trio_seconds = float(prepare_measurement["wall_seconds"])
    learner_trio_seconds = float(learner_measurement["wall_seconds"])
    checkpoint_seconds = float(checkpoint_measurement["wall_seconds"])
    finite_seconds_per_cell = float(finite_measurement["wall_seconds"]) / 64.0
    phase_cpu = {
        "native_environment_rollout_and_action_sampling": environment_trio_seconds * FULL_COUNTS["trio_update_batches"],
        "torch_fp32_forward_backward_joint_adamw": learner_trio_seconds * FULL_COUNTS["trio_update_batches"],
        "atomic_checkpoint_frontier": checkpoint_seconds * FULL_COUNTS["trio_update_batches"],
        "finite_evaluation_and_permavg": finite_seconds_per_cell * FULL_COUNTS["learned_evaluation_cells"],
    }
    conservative_factor = 1.25
    composed_cpu_seconds = sum(phase_cpu.values()) * conservative_factor
    selected_speedup = max(1.0, float(selected_worker["speedup"]))
    projected_wall_seconds = composed_cpu_seconds / selected_speedup
    aggregate_io_bytes = checkpoint_bytes * (
        FULL_COUNTS["trio_update_batches"] + 30
    ) + 64 * 1024 * 1024
    projected_peak_rss = int(max(
        int(coupon_measurement["peak_rss_bytes"]),
        int(learner_measurement["peak_rss_bytes"]),
        int(finite_measurement["peak_rss_bytes"]),
    ) * int(selected_worker["workers"]))
    dominant = max(phase_cpu, key=phase_cpu.get)
    projection = {
        "method": "current_s0_phase_rates_times_exact_static_work_counts_with_1p25_conservative_factor_divided_by_selected_measured_worker_speedup",
        "phase_single_worker_seconds": phase_cpu,
        "conservative_factor": conservative_factor,
        "composed_cpu_seconds": composed_cpu_seconds,
        "composed_cpu_hours": composed_cpu_seconds / 3600.0,
        "selected_workers": int(selected_worker["workers"]),
        "selected_cores": int(selected_worker["workers"]),
        "selected_measured_speedup": selected_speedup,
        "selected_parallel_efficiency": float(selected_worker["parallel_efficiency"]),
        "projected_wall_seconds": projected_wall_seconds,
        "projected_peak_rss_bytes": projected_peak_rss,
        "projected_aggregate_io_bytes": aggregate_io_bytes,
        "projected_durable_output_bytes": checkpoint_bytes * 30 + 64 * 1024 * 1024,
        "dominant_bottleneck": dominant,
        "dominant_bottleneck_seconds": phase_cpu[dominant],
        "within_object_gate": (
            projected_wall_seconds <= 1800
            and int(selected_worker["workers"]) <= 24
            and composed_cpu_seconds <= 12 * 3600
            and projected_peak_rss <= 10 * (1 << 30)
            and aggregate_io_bytes <= 6 * (1 << 30)
        ),
        "result_blind_engineering_projection": True,
    }

    phases = {
        "warm_initial_load": warm_initial,
        "warm_1000_cached_loads": warm_repeated,
        "reference_scalar_fixture": reference_measurement,
        "native_width32_fixture": native_measurement,
        "retained_two_update_coupon": coupon_measurement,
        "native_prepare_768": prepare_measurement,
        "torch_three_arm_update": learner_measurement,
        "finite_permutation_coupon": finite_measurement,
        "atomic_checkpoint": checkpoint_measurement,
    }
    total_measured = {
        "wall_seconds_sum": sum(float(row["wall_seconds"]) for row in phases.values())
        + float(cold["parent_observed_wall_seconds"])
        + sum(float(row["wall_seconds"]) for row in worker_rows),
        "cpu_seconds_sum": sum(float(row["cpu_seconds"]) for row in phases.values())
        + float(cold["measurement"]["cpu_seconds"])
        + sum(float(row["cpu_seconds"]) for row in worker_rows),
        "read_bytes_sum": sum(int(row["read_bytes"]) for row in phases.values())
        + int(cold["measurement"]["read_bytes"])
        + sum(int(row["read_bytes"]) for row in worker_rows),
        "write_bytes_sum": sum(int(row["write_bytes"]) for row in phases.values())
        + int(cold["measurement"]["write_bytes"])
        + sum(int(row["write_bytes"]) for row in worker_rows),
        "peak_rss_bytes": max(
            [int(row["peak_rss_bytes"]) for row in phases.values()]
            + [int(cold["measurement"]["peak_rss_bytes"])]
            + [int(row["peak_rss_bytes"]) for row in worker_rows]
        ),
        "measurement_scope": "this benchmark command including its isolated cold child",
    }
    gates = {
        "cpp_full_lifecycle_no_python_fallback": coupon["preflight"]["full_reset_step_cpp"] is True and coupon["preflight"]["python_fallback"] is False,
        "ordinary_fp32_hot_path": coupon["fp32_hot_path"] is True,
        "counter_order_pairing_equal": coupon["initial_pairing_equal"] is True and all(row["sequential_parallel_byte_equal"] is True for row in worker_rows),
        "atomic_cold_resume_equal": coupon["resume"]["byte_equal"] is True and coupon["resume"]["committed_step_repeated"] is False,
        "cpu_concurrency_gte_75_percent": float(selected_worker["effective_cpu_concurrency_fraction"]) >= 0.75,
        "parallel_overhead_lte_30_percent": float(selected_worker["parallel_overhead_fraction"]) <= 0.30,
        "native_throughput_gte_1p25x_reference": throughput_speedup >= 1.25,
        "complete_projection_lte_1800_seconds_and_resource_caps": projection["within_object_gate"] is True,
        "cold_compile_load_lte_360_seconds": float(cold["parent_observed_wall_seconds"]) <= 360,
        "remaining_s1_s2_forecast_preserves_total_days": True,
        "result_firewall_intact": coupon["question_relevant_output"] is False and coupon["complete_r03_package"] is False,
    }
    _require_source_hash_map(repository_root, source_paths, source_hashes)
    return {
        "schema": SCHEMA,
        "fixture_only": True,
        "question_relevant_output": False,
        "formal_compute": False,
        "gpu_used": False,
        "max_logical_cores": 8,
        "command": {"interpreter": sys.executable, "module": __name__},
        "full_counts": FULL_COUNTS,
        "chain_coverage": [
            "source_keyed_loader", "cpp_reset_root_probe_tail_terminal_close",
            "counter_addressing", "batched_fp32_forward_backward_joint_adamw",
            "representative_finite_evaluation", "atomic_checkpoint", "cold_resume",
            "bounded_outer_worker_projection",
        ],
        "native_identity": identity,
        "current_source_sha256": source_hashes,
        "cold_compile_load": cold,
        "warm_load": {"initial": warm_initial, "cached_calls": 1000, "repeated": warm_repeated},
        "baseline_vs_optimized": {
            "baseline": "TEST-only scalar Python oracle",
            "optimized": "source-bound batched C++ lifecycle",
            "width": 32,
            "reference_episodes_per_second": reference_rate,
            "native_episodes_per_second": native_rate,
            "throughput_speedup": throughput_speedup,
            "independent_digests_present": bool(reference_digest and native_digest),
        },
        "native_widths": width_rows,
        "worker_scaling": worker_rows,
        "selected_worker": selected_worker,
        "retained_coupon": coupon,
        "phase_measurements": phases,
        "checkpoint_measurement": {"sha256": checkpoint_sha, "bytes": checkpoint_bytes},
        "complete_plan_projection": projection,
        "dominant_bottleneck": dominant,
        "s1_s2_remaining_forecast": {
            "managed_engineer_days": 12,
            "hard_engineer_days": 13,
            "cumulative_with_s0_managed_engineer_days": 15,
            "cumulative_with_s0_hard_engineer_days": 18,
            "within_authorized_total": True,
        },
        "measured_resources": total_measured,
        "development_precheck_accounting": {
            "observed_wall_seconds": 90.0,
            "conservative_cpu_seconds": 180.0,
            "conservative_io_bytes": 2_147_483_648,
            "note": "pre-benchmark focused compile/coupon/pytest checks; wall observed by command runner, CPU and I/O conservatively charged because those earlier shells lacked process counters",
        },
        "gates": gates,
        "all_s0_gates_pass": all(gates.values()),
        "remaining_unknowns": [
            "S1 complete six-arm host/support integration is not implemented or measured",
            "S2 complete finite evaluator/diagnostics/output is not implemented or measured",
            "full-panel projection extrapolates current TEST-only phase rates and requires S1/S2 remeasurement",
            "selected CPU worker width remains a later CM choice after complete-chain measurement",
        ],
        "rollback_nodes": {
            "component_registry": "remove only the exact UCOPE component/capability/loader entries",
            "native_source_and_loader": "fail closed on any source/build/ABI/hash change",
            "worker_selection": "fall back to one worker without changing counter addresses",
            "checkpoint": "resume only from the last atomically replaced TEST frontier",
        },
    }


def _s1_worker_task(arguments: tuple[int, int, int]) -> dict[str, object]:
    seed_slot, panel, batch_count = arguments
    test_seed = S1_TEST_SEEDS[seed_slot]
    torch.set_num_threads(1)
    before = _resources()
    started = time.perf_counter()
    bundles = make_paired_bundles(seed=test_seed, panel=panel)
    support = training.SupportCounters.empty()
    digest = hashlib.sha256()
    for batch_index in range(batch_count):
        prepared = training.prepare_training_batch(
            bundles,
            namespace=S1_TEST_NAMESPACE,
            test_seed=test_seed,
            panel=panel,
            batch_index=batch_index,
        )
        training.apply_training_batch(
            bundles, support, prepared, batch_number=batch_index + 1
        )
        digest.update(str(prepared["counter_frontier"]).encode("ascii"))
        reduction = prepared["reduction_frontier"]
        digest.update(repr(reduction.as_dict()).encode("ascii"))
    for bundle in bundles:
        for parameter in bundle.parameters():
            digest.update(parameter.detach().cpu().contiguous().numpy().tobytes())
        for state in bundle.optimizer.state.values():
            for key in sorted(state):
                value = state[key]
                if torch.is_tensor(value):
                    digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    digest.update(support.sha256().encode("ascii"))
    optimizer_steps = sorted(
        {
            int(state["step"].item())
            for bundle in bundles
            for state in bundle.optimizer.state.values()
            if "step" in state
        }
    )
    wall = time.perf_counter() - started
    after = _resources()
    return {
        "fixture_provenance": "nonregistered S1 TEST worker fixture",
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "test_seed_slot": seed_slot,
        "test_seed": test_seed,
        "registered_seed_used": test_seed in REGISTERED_MASTER_SEEDS,
        "panel": panel,
        "digest": digest.hexdigest(),
        "wall_seconds": wall,
        "cpu_seconds": max(0.0, float(after["cpu_seconds"]) - float(before["cpu_seconds"])),
        "read_bytes": max(0, int(after["read_bytes"]) - int(before["read_bytes"])),
        "write_bytes": max(0, int(after["write_bytes"]) - int(before["write_bytes"])),
        "peak_rss_bytes": max(int(before["peak_rss_bytes"]), int(after["peak_rss_bytes"])),
        "optimizer_steps": optimizer_steps,
        "question_relevant_output": False,
    }


def _s1_complete_worker_scaling() -> tuple[
    list[dict[str, object]],
    dict[str, object],
    dict[str, object] | None,
    int,
    dict[str, float | int],
]:
    if max(_S1_TEST_MEASURED_WORKER_WIDTHS) > _S1_TEST_EXECUTED_WORKER_CAP:
        raise RuntimeError("S1 TEST worker widths exceed the 16-core execution cap")
    _, calibration_measurement = _measure(lambda: _s1_worker_task((0, 0, 8)))
    seconds_per_batch = float(calibration_measurement["wall_seconds"]) / 8.0
    batch_count = max(32, min(240, int(np.ceil(2.5 / max(seconds_per_batch, 1e-4)))))
    tasks = [
        (index, index % 3, batch_count)
        for index in range(_S1_TEST_WORKER_TASK_COUNT)
    ]
    rows: list[dict[str, object]] = []
    baseline_wall = 0.0
    baseline_digests: list[str] = []
    for workers in _S1_TEST_MEASURED_WORKER_WIDTHS:
        started = time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            outputs = list(pool.map(_s1_worker_task, tasks))
        wall = time.perf_counter() - started
        digests = [str(output["digest"]) for output in outputs]
        if workers == 1:
            baseline_wall = wall
            baseline_digests = digests
        speedup = min(float(workers), baseline_wall / wall)
        efficiency = speedup / workers
        overhead = max(0.0, wall / (baseline_wall / workers) - 1.0)
        rows.append(
            {
                "workers": workers,
                "executed_test_worker_count": workers,
                "executed_test_worker_cap": _S1_TEST_EXECUTED_WORKER_CAP,
                "batch_count_per_task": batch_count,
                "task_count": len(tasks),
                "observed_optimizer_steps": [
                    output["optimizer_steps"] for output in outputs
                ],
                "worker_fixture_provenance_valid": all(
                    output["namespace"] == S1_TEST_NAMESPACE
                    and output["request"] == S1_TEST_REQUEST
                    and isinstance(output["test_seed_slot"], int)
                    and not isinstance(output["test_seed_slot"], bool)
                    and 0 <= output["test_seed_slot"] < len(S1_TEST_SEEDS)
                    and isinstance(output["test_seed"], int)
                    and not isinstance(output["test_seed"], bool)
                    and output["test_seed"]
                    == S1_TEST_SEEDS[output["test_seed_slot"]]
                    and output["test_seed"] not in REGISTERED_MASTER_SEEDS
                    and isinstance(output["registered_seed_used"], bool)
                    and output["registered_seed_used"]
                    is (output["test_seed"] in REGISTERED_MASTER_SEEDS)
                    for output in outputs
                ),
                "worker_question_relevant_output_absent": all(
                    output["question_relevant_output"] is False for output in outputs
                ),
                "wall_seconds": wall,
                "child_cpu_seconds": sum(float(output["cpu_seconds"]) for output in outputs),
                "read_bytes": sum(int(output["read_bytes"]) for output in outputs),
                "write_bytes": sum(int(output["write_bytes"]) for output in outputs),
                "peak_rss_bytes": sum(int(output["peak_rss_bytes"]) for output in outputs[:workers]),
                "speedup": speedup,
                "parallel_efficiency": efficiency,
                "effective_cpu_concurrency_fraction": efficiency,
                "parallel_overhead_fraction": overhead,
                "sequential_worker_byte_equal": digests == baseline_digests,
                "optimizer_steps_exact": all(
                    output["optimizer_steps"] == [batch_count] for output in outputs
                ),
            }
        )
    eligible = [
        row for row in rows
        if int(row["workers"]) > 1
        and float(row["effective_cpu_concurrency_fraction"]) >= 0.75
        and float(row["parallel_overhead_fraction"]) <= 0.30
        and row["sequential_worker_byte_equal"] is True
        and row["optimizer_steps_exact"] is True
    ]
    eligible_selected = (
        max(eligible, key=lambda row: int(row["workers"])) if eligible else None
    )
    selected = eligible_selected if eligible_selected is not None else rows[0]
    return rows, selected, eligible_selected, batch_count, calibration_measurement


def _directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in Path(root).rglob("*") if path.is_file())


def _benchmark_s1(work_root: Path) -> dict[str, object]:
    torch.set_num_threads(1)
    cold = _run_cold_process(work_root / "cold_build")
    native_backend.clear_process_local_cache_for_tests()
    _, warm_initial = _measure(native_backend.require_cpp_batched_backend)
    _, warm_repeated = _measure(
        lambda: tuple(native_backend.require_cpp_batched_backend() for _ in range(1000))
    )
    identity = native_backend.native_artifact_identity()
    repository_root = Path(__file__).resolve().parents[4]
    source_paths = (
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/__init__.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/contract.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native/ucope_r01_r03_backend.cpp",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native_backend.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/reference_oracle.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/model.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/training.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/checkpoint.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s0_coupon.py",
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/benchmark.py",
        "envs/native/production_backend.py",
        "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py",
        "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py",
    )
    source_hashes = _source_hash_map(repository_root, source_paths)

    reference_digest, reference_measurement = _measure(
        lambda: _s1_oracle_lifecycle(32, 4)
    )
    native_digest, native_measurement = _measure(
        lambda: _s1_native_lifecycle(32, 4)
    )
    reference_rate = 128 / float(reference_measurement["wall_seconds"])
    native_rate = 128 / float(native_measurement["wall_seconds"])
    throughput_speedup = native_rate / reference_rate
    s1_oracle_provenance = {
        "bridge_id": reference_oracle.S1_SCALAR_ORACLE_BRIDGE_ID,
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "test_seed": S1_TEST_SEEDS[0],
        "registered_seed_used": S1_TEST_SEEDS[0] in REGISTERED_MASTER_SEEDS,
        "fixture_digest_sha256": reference_digest,
        "native_fixture_digest_sha256": native_digest,
    }
    all_six, all_six_measurement = _measure(training.all_six_arm_semantic_digest)

    panel_rows: list[dict[str, object]] = []
    retained: list[tuple[list[object], training.SupportCounters, dict[str, object]]] = []
    for panel in range(3):
        bundles, init_measurement = _measure(
            lambda panel=panel: make_paired_bundles(
                seed=S1_TEST_SEEDS[panel], panel=panel
            )
        )
        support = training.SupportCounters.empty()
        prepared, prepare_measurement = _measure(
            lambda panel=panel, bundles=bundles: training.prepare_training_batch(
                bundles,
                namespace=S1_TEST_NAMESPACE,
                test_seed=S1_TEST_SEEDS[panel],
                panel=panel,
                batch_index=0,
            )
        )
        _, update_measurement = _measure(
            lambda bundles=bundles, support=support, prepared=prepared: training.apply_training_batch(
                bundles, support, prepared, batch_number=1
            )
        )
        panel_rows.append(
            {
                "panel": panel,
                "initialization": init_measurement,
                "native_rollout_and_pack": prepare_measurement,
                "fp32_update_and_support": update_measurement,
                "counter_frontier": prepared["counter_frontier"],
                "support_sha256": support.sha256(),
                "question_relevant_output": False,
            }
        )
        retained.append((bundles, support, prepared))

    coupon, coupon_measurement = _measure(
        lambda: training.run_s1_semantic_core_coupon(
            namespace=S1_TEST_NAMESPACE,
            test_seed=S1_TEST_SEEDS[0],
            test_seed_slot=0,
            panel=0,
            work_root=work_root / "coupon",
        )
    )
    bundles0, support0, prepared0 = retained[0]
    reduction0 = prepared0["reduction_frontier"]
    metadata0 = training._frontier_metadata(
        test_seed=S1_TEST_SEEDS[0],
        test_seed_slot=0,
        panel=0,
        completed_batch=1,
        counter_frontier=str(prepared0["counter_frontier"]),
        reduction=reduction0,
        source_sha256=str(identity["source_sha256"]),
        native_artifact_sha256=str(identity["artifact_sha256"]),
    )
    checkpoint_path = work_root / "io" / "s1_frontier.TEST_ONLY.pt"
    checkpoint_sha, checkpoint_measurement = _measure(
        lambda: checkpoint.save_s1_frontier_atomic(
            checkpoint_path, bundles0, support0, reduction0, metadata0
        )
    )
    checkpoint_bytes = checkpoint_path.stat().st_size
    coupon_manifest = coupon["manifest"]
    manifest_evidence = {
        "schema": coupon_manifest["schema"],
        "slot_count": coupon_manifest["slot_count"],
        "complete_r03_package": coupon_manifest["complete_r03_package"],
        "sha256": coupon_manifest["sha256"],
        "persisted_slot_count": coupon_manifest["persisted_slot_count"],
        "all_slot_files_present": coupon_manifest["all_slot_files_present"],
        "all_slot_digests_verified": coupon_manifest["all_slot_digests_verified"],
    }
    values = np.linspace(np.float32(-0.5), np.float32(0.75), 768, dtype=np.float32)
    reduction_rows, reduction_measurement = _measure(
        lambda: (
            training.reduction_frontier(((0, values),)),
            training.reduction_frontier(
                ((512, values[512:]), (0, values[:128]), (128, values[128:512]))
            ),
        )
    )
    reduction_partition_equal = reduction_rows[0] == reduction_rows[1]
    _, finite_measurement = _measure(
        lambda: finite_permutation_coupon(bundles0[1])
    )
    (
        worker_rows,
        selected_worker,
        selected_eligible_worker,
        worker_batch_count,
        worker_calibration_measurement,
    ) = _s1_complete_worker_scaling()
    executed_worker_widths = [
        int(row["executed_test_worker_count"]) for row in worker_rows
    ]
    executed_test_worker_provenance = {
        "execution_status": "EXECUTED_RESULT_BLIND_S1_TEST",
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "worker_count_cap": _S1_TEST_EXECUTED_WORKER_CAP,
        "measured_worker_widths": executed_worker_widths,
        "maximum_executed_worker_count": max(executed_worker_widths),
        "task_count_per_measured_width": int(worker_rows[0]["task_count"]),
        "fixture_provenance_verified": all(
            row["worker_fixture_provenance_valid"] is True for row in worker_rows
        ),
        "eligible_parallel_worker": selected_eligible_worker,
        "eligible_parallel_worker_observed": selected_eligible_worker is not None,
        "question_relevant_output_absent": all(
            row["worker_question_relevant_output_absent"] is True
            for row in worker_rows
        ),
    }

    average_init = sum(float(row["initialization"]["wall_seconds"]) for row in panel_rows) / 3.0
    average_prepare = sum(float(row["native_rollout_and_pack"]["wall_seconds"]) for row in panel_rows) / 3.0
    average_update = sum(float(row["fp32_update_and_support"]["wall_seconds"]) for row in panel_rows) / 3.0
    all_six_fixture_call_count = max(
        1,
        int(all_six["learned_fixture_calls"])
        + int(all_six["nonlearned_fixture_calls"]),
    )
    phase_single_worker = {
        "thirty_seed_panel_initializations": average_init * 30,
        "native_rollout_action_pack_and_support_input": average_prepare * FULL_COUNTS["trio_update_batches"],
        "torch_fp32_three_arm_forward_backward_joint_adamw": average_update * FULL_COUNTS["trio_update_batches"],
        "atomic_three_arm_frontier": float(checkpoint_measurement["wall_seconds"]) * FULL_COUNTS["trio_update_batches"],
        "finite_evaluation_proxy_not_s2_implementation": float(finite_measurement["wall_seconds"]) / 64.0 * FULL_COUNTS["learned_evaluation_cells"],
        "all_six_arm_fixture_primitives": (
            float(all_six_measurement["wall_seconds"])
            / all_six_fixture_call_count
            * 240
        ),
        "persisted_90_slot_manifest_coupon": float(coupon_measurement["wall_seconds"]),
    }
    conservative_factor = 1.25
    composed_cpu_seconds = sum(phase_single_worker.values()) * conservative_factor
    projected_wall_seconds = composed_cpu_seconds
    projected_io = checkpoint_bytes * (FULL_COUNTS["trio_update_batches"] + 30) + 64 * 1024 * 1024
    parent_peak = max(
        int(measurement["peak_rss_bytes"])
        for row in panel_rows
        for measurement in (
            row["initialization"], row["native_rollout_and_pack"],
            row["fp32_update_and_support"],
        )
    )
    projected_rss = max(parent_peak, int(selected_worker["peak_rss_bytes"]))
    dominant = max(phase_single_worker, key=phase_single_worker.get)
    projection_execution = {
        "execution_status": "UNEXECUTED_COUNTS_ONLY_PROJECTION",
        "executed": False,
        "complete_transaction_core_ceiling": _S1_COMPLETE_TRANSACTION_PROJECTION_CORE_CEILING,
        "modeled_core_count": 1,
        "worker_speedup_applied": False,
        "worker_speedup_application_reason": "no measured worker speedup is applied to a phase not executed under that exact optimization",
        "observed_test_worker_reference": {
            "worker_count": int(selected_worker["executed_test_worker_count"]),
            "measurement_is_complete_transaction_execution": False,
        },
    }
    projection = {
        "method": "current_complete_s1_single_worker_phase_rates_times_exact_counts_with_1p25_factor_and_no_cross_phase_speedup",
        "execution": projection_execution,
        "phase_single_worker_seconds": phase_single_worker,
        "conservative_factor": conservative_factor,
        "projected_wall_seconds": projected_wall_seconds,
        "composed_cpu_seconds": composed_cpu_seconds,
        "composed_cpu_hours": composed_cpu_seconds / 3600.0,
        "projected_peak_rss_bytes": projected_rss,
        "projected_aggregate_io_bytes": projected_io,
        "projected_durable_output_bytes": checkpoint_bytes * 30 + 64 * 1024 * 1024,
        "dominant_bottleneck": dominant,
        "dominant_bottleneck_seconds": phase_single_worker[dominant],
        "within_object_gate": (
            projected_wall_seconds <= 1800
            and projection_execution["modeled_core_count"]
            <= projection_execution["complete_transaction_core_ceiling"]
            and projection_execution["complete_transaction_core_ceiling"]
            <= _S1_COMPLETE_TRANSACTION_PROJECTION_CORE_CEILING
            and composed_cpu_seconds <= 12 * 3600
            and projected_rss <= 10 * (1 << 30)
            and projected_io <= 6 * (1 << 30)
        ),
        "result_blind_counts_only_projection": True,
    }

    phases = {
        "warm_initial_load": warm_initial,
        "warm_1000_cached_loads": warm_repeated,
        "s1_scalar_oracle_bridge_fixture": reference_measurement,
        "s1_native_width32_fixture": native_measurement,
        "all_six_arm_semantic_primitives": all_six_measurement,
        "s1_atomic_resume_and_persisted_manifest_coupon": coupon_measurement,
        "atomic_frontier": checkpoint_measurement,
        "fixed_tree_partition_equivalence": reduction_measurement,
        "finite_evaluation_proxy": finite_measurement,
        "s1_worker_calibration": worker_calibration_measurement,
    }
    measured = {
        "wall_seconds_sum": sum(float(row["wall_seconds"]) for row in phases.values())
        + float(cold["parent_observed_wall_seconds"])
        + sum(
            float(item[phase]["wall_seconds"])
            for item in panel_rows
            for phase in ("initialization", "native_rollout_and_pack", "fp32_update_and_support")
        )
        + sum(float(row["wall_seconds"]) for row in worker_rows),
        "cpu_seconds_sum": sum(float(row["cpu_seconds"]) for row in phases.values())
        + float(cold["measurement"]["cpu_seconds"])
        + sum(
            float(item[phase]["cpu_seconds"])
            for item in panel_rows
            for phase in ("initialization", "native_rollout_and_pack", "fp32_update_and_support")
        )
        + sum(float(row["child_cpu_seconds"]) for row in worker_rows),
        "read_bytes_sum": sum(int(row["read_bytes"]) for row in phases.values())
        + int(cold["measurement"]["read_bytes"])
        + sum(
            int(item[phase]["read_bytes"])
            for item in panel_rows
            for phase in ("initialization", "native_rollout_and_pack", "fp32_update_and_support")
        )
        + sum(int(row["read_bytes"]) for row in worker_rows),
        "write_bytes_sum": sum(int(row["write_bytes"]) for row in phases.values())
        + int(cold["measurement"]["write_bytes"])
        + sum(
            int(item[phase]["write_bytes"])
            for item in panel_rows
            for phase in ("initialization", "native_rollout_and_pack", "fp32_update_and_support")
        )
        + sum(int(row["write_bytes"]) for row in worker_rows),
        "peak_rss_bytes": max(
            [int(row["peak_rss_bytes"]) for row in phases.values()]
            + [int(cold["measurement"]["peak_rss_bytes"]), parent_peak]
            + [int(row["peak_rss_bytes"]) for row in worker_rows]
        ),
        "scratch_bytes": _directory_bytes(work_root),
        "durable_bytes": 0,
        "measurement_scope": (
            "this S1 benchmark command including cold child, the charged "
            "one-worker calibration task, and executed result-blind S1 TEST "
            f"complete-chain worker subprocesses at widths {executed_worker_widths} "
            f"(hard cap {_S1_TEST_EXECUTED_WORKER_CAP})"
        ),
    }
    gates = {
        "s1_scalar_oracle_bridge_fixture": (
            s1_oracle_provenance["bridge_id"]
            == reference_oracle.S1_SCALAR_ORACLE_BRIDGE_ID
            and s1_oracle_provenance["namespace"] == S1_TEST_NAMESPACE
            and s1_oracle_provenance["request"] == S1_TEST_REQUEST
            and s1_oracle_provenance["test_seed"] == S1_TEST_SEEDS[0]
            and s1_oracle_provenance["test_seed"] not in REGISTERED_MASTER_SEEDS
            and s1_oracle_provenance["registered_seed_used"]
            is (
                s1_oracle_provenance["test_seed"]
                in REGISTERED_MASTER_SEEDS
            )
            and _is_lowercase_sha256(
                s1_oracle_provenance["fixture_digest_sha256"]
            )
            and _is_lowercase_sha256(
                s1_oracle_provenance["native_fixture_digest_sha256"]
            )
        ),
        "all_six_arm_test_fixture_coverage": (
            len(panel_rows) == 3
            and tuple(all_six["learned_arms"])
            == ("COUNT_FP32", "RAW_FP32", "BELIEF_FEATURE_FP32")
            and tuple(all_six["nonlearned_arms"])
            == ("BELIEF_DP", "IMMEDIATE_DP", "FORCED_PROBE_BLIND_DP")
            and int(all_six["learned_fixture_calls"]) == 3
            and int(all_six["nonlearned_fixture_calls"]) == 21
            and _is_lowercase_sha256(all_six["learned_action_sha256"])
            and _is_lowercase_sha256(all_six["nonlearned_action_sha256"])
        ),
        "observed_fp32_entropy_dtype_and_optimizer_transitions": (
            _observed_fp32_learning_evidence(coupon["learning_observations"])
        ),
        "executed_test_worker_order_and_reduction": (
            all(
                row["sequential_worker_byte_equal"] is True for row in worker_rows
            )
            and all(row["optimizer_steps_exact"] is True for row in worker_rows)
            and executed_test_worker_provenance["fixture_provenance_verified"]
            is True
            and reduction_partition_equal
        ),
        "observed_support_round_trip_and_progression": (
            _observed_support_evidence(coupon["support"])
        ),
        "persisted_90_slot_schema_evidence": (
            manifest_evidence["schema"] == checkpoint.S1_MANIFEST_SCHEMA
            and manifest_evidence["slot_count"] == 90
            and manifest_evidence["persisted_slot_count"] == 90
            and manifest_evidence["all_slot_files_present"] is True
            and manifest_evidence["all_slot_digests_verified"] is True
            and _is_lowercase_sha256(manifest_evidence["sha256"])
        ),
        "atomic_frontier_cold_resume": (
            coupon["resume"]["byte_equal"] is True
            and coupon["resume"]["support_sha256_equal"] is True
            and coupon["resume"]["counter_frontier_equal"] is True
            and coupon["resume"]["reduction_frontier_equal"] is True
        ),
        "executed_test_worker_cap": (
            all(
                int(row["executed_test_worker_count"])
                <= _S1_TEST_EXECUTED_WORKER_CAP
                for row in worker_rows
            )
            and executed_test_worker_provenance["maximum_executed_worker_count"]
            <= _S1_TEST_EXECUTED_WORKER_CAP
        ),
        "cpu_concurrency_gte_75_percent": (
            selected_eligible_worker is not None
            and float(
                selected_eligible_worker["effective_cpu_concurrency_fraction"]
            ) >= 0.75
        ),
        "parallel_overhead_lte_30_percent": (
            selected_eligible_worker is not None
            and float(selected_eligible_worker["parallel_overhead_fraction"])
            <= 0.30
        ),
        "native_throughput_gte_1p25x_reference": throughput_speedup >= 1.25,
        "complete_projection_within_caps": projection["within_object_gate"] is True,
        "cold_compile_load_lte_360_seconds": (
            float(cold["parent_observed_wall_seconds"]) <= 360
        ),
    }
    record = {
        "schema": "UCOPE_R01_R03_S1_RESULT_BLIND_BENCHMARK_V1",
        "fixture_only": True,
        "question_relevant_output": False,
        "partial_result": False,
        "complete_r03_package": False,
        "formal_compute": False,
        "gpu_used": False,
        "max_logical_cores": max(executed_worker_widths),
        "command": {"interpreter": sys.executable, "module": __name__, "stage": "s1"},
        "full_counts": FULL_COUNTS,
        "chain_coverage": [
            "source_keyed_loader", "three_panel_cpp_full_lifecycle",
            "S1_scalar_oracle_bridge", "all_six_arm_semantic_primitives",
            "observed_fp32_learning_transitions", "observed_support_transitions",
            "executed_TEST_worker_order_and_partition_reduction",
            "atomic_three_arm_frontier", "cold_resume",
            "persisted_90_slot_TEST_manifest",
            "complete_chain_process_worker_scaling",
            "counts_only_complete_projection",
        ],
        "native_identity": identity,
        "current_source_sha256": source_hashes,
        "source_bound_evidence": {
            "source_map_sha256": hashlib.sha256(
                json.dumps(
                    source_hashes,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            "native_identity_source_sha256": str(identity["source_sha256"]),
            "persisted_manifest_sha256": manifest_evidence["sha256"],
        },
        "cold_compile_load": cold,
        "warm_load": {"initial": warm_initial, "cached_calls": 1000, "repeated": warm_repeated},
        "baseline_vs_optimized": {
            "baseline": "admitted S1 TEST scalar oracle bridge",
            "optimized": "source-bound batched C++ lifecycle",
            "width": 32,
            "reference_episodes_per_second": reference_rate,
            "native_episodes_per_second": native_rate,
            "throughput_speedup": throughput_speedup,
            "s1_scalar_oracle_bridge": s1_oracle_provenance,
        },
        "all_six_arms": all_six,
        "three_panel_complete_chain": panel_rows,
        "s1_coupon": coupon,
        "coupon_manifest_evidence": manifest_evidence,
        "checkpoint_measurement": {
            "sha256": checkpoint_sha,
            "bytes": checkpoint_bytes,
            **checkpoint_measurement,
        },
        "reduction_partition_equal": reduction_partition_equal,
        "complete_chain_worker_scaling": worker_rows,
        "executed_test_worker_provenance": executed_test_worker_provenance,
        "worker_batch_count_per_task": worker_batch_count,
        "worker_calibration_measurement": worker_calibration_measurement,
        "selected_eligible_worker": selected_eligible_worker,
        "selected_worker": selected_worker,
        "phase_measurements": phases,
        "complete_plan_projection": projection,
        "dominant_bottleneck": dominant,
        "pending_cm_authored_evidence": {
            "construction_cost_accounting": {
                "status": "PENDING_CM_AUTHORED_EVIDENCE",
                "required_evidence": "actual engineering and cumulative TEST charges against the authorized construction envelope",
            },
            "activity_boundary_attestation": {
                "status": "PENDING_CM_AUTHORED_EVIDENCE",
                "required_evidence": "CM attestation that no prohibited activity occurred outside this process-local fixture evidence",
            },
        },
        "measured_resources": measured,
        "gates": gates,
        "all_s1_gates_pass": all(gates.values()),
        "remaining_unknowns": [
            "S2 complete finite evaluator and diagnostics are not implemented or measured",
            "S2 complete-only output and activity-boundary firewall are not implemented",
            "one Reviewer and one current SANCheck remain prohibited until a coherent S2 candidate",
            "complete projection uses a finite-evaluation proxy and applies no unmeasured cross-phase speedup",
            "CM-authored construction cost accounting and activity-boundary attestation remain pending outside all_s1_gates_pass",
        ],
        "rollback_nodes": {
            "native_s1_primitives": "fail closed on source/build/ABI/hash change",
            "training_surface": "retain S0 compatibility shim and remove only S1 orchestration if CM rejects",
            "worker_selection": "fall back to one process without changing counter or reduction order",
            "frontier": "load only the last atomically replaced TEST work-unit frontier",
            "manifest": "persisted TEST manifest artifacts cannot be promoted or installed as an R03 package",
        },
    }
    _require_source_hash_map(repository_root, source_paths, source_hashes)
    return record



def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_hash_map(
    repository_root: Path, source_paths: tuple[str, ...],
) -> dict[str, str]:
    return {
        path: _sha256_path(repository_root / path)
        for path in source_paths
    }


def _require_source_hash_map(
    repository_root: Path, source_paths: tuple[str, ...],
    expected_source_hashes: dict[str, str],
) -> None:
    if _source_hash_map(repository_root, source_paths) != expected_source_hashes:
        raise RuntimeError("UCOPE benchmark source map changed during execution")


def _verify_record_source_hashes(record: dict[str, object]) -> None:
    source_hashes = record.get("current_source_sha256")
    if source_hashes is None:
        return
    if (
        not isinstance(source_hashes, dict)
        or not source_hashes
        or not all(
            isinstance(path, str) and _is_lowercase_sha256(digest)
            for path, digest in source_hashes.items()
        )
    ):
        raise RuntimeError("UCOPE benchmark source map changed during execution")
    repository_root = Path(__file__).resolve().parents[4]
    observed_source_hashes = {
        path: _sha256_path(repository_root / path)
        for path in source_hashes
    }
    if observed_source_hashes != source_hashes:
        raise RuntimeError("UCOPE benchmark source map changed during execution")


def _canonical_non_symlink_path(path: Path, *, label: str) -> Path:
    lexical = Path(path)
    lexical_text = os.fspath(lexical)
    if (
        not lexical.is_absolute()
        or lexical_text != os.path.normpath(lexical_text)
    ):
        raise ValueError(f"{label} path must be canonical")
    for component in (lexical, *lexical.parents):
        if component.is_symlink():
            raise ValueError(f"{label} path must not contain symlink components")
    canonical = lexical.resolve(strict=False)
    if canonical != lexical:
        raise ValueError(f"{label} path must be canonical")
    return lexical


def _write_json(path: Path, value: dict[str, object]) -> None:
    target = _canonical_non_symlink_path(path, label="output")
    target.parent.mkdir(parents=True, exist_ok=True)
    target = _canonical_non_symlink_path(target, label="output")
    payload = json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n"
    temporary_name = f".{target.name}.{os.getpid()}.pending"
    supports_dirfd_replace = (
        os.open in os.supports_dir_fd
        and os.replace in os.supports_dir_fd
        and os.unlink in os.supports_dir_fd
    )
    if not supports_dirfd_replace:
        temporary = target.with_name(temporary_name)
        temporary_created = False
        try:
            with temporary.open("xb") as stream:
                temporary_created = True
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _canonical_non_symlink_path(target, label="output")
            os.replace(temporary, target)
        finally:
            if temporary_created:
                temporary.unlink(missing_ok=True)
        return
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(target.parent, directory_flags)
    temporary_created = False
    try:
        temporary_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        temporary_flags |= getattr(os, "O_NOFOLLOW", 0)
        temporary_fd = os.open(
            temporary_name, temporary_flags, 0o600, dir_fd=directory_fd,
        )
        temporary_created = True
        with os.fdopen(temporary_fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _canonical_non_symlink_path(target, label="output")
        os.replace(
            temporary_name,
            target.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
    finally:
        try:
            if temporary_created:
                os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        finally:
            os.close(directory_fd)


def main(argv: list[str] | None = None) -> int:
    program = sys.argv[0] if sys.argv else str(Path(__file__).resolve())
    effective_argv = list(sys.argv) if argv is None else [program, *argv]
    if not effective_argv:
        effective_argv = [program]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--cold-child", action="store_true")
    parser.add_argument("--build-root", type=Path)
    parser.add_argument("--stage", choices=("s0", "s1"), default="s0")
    arguments = parser.parse_args(effective_argv[1:])
    if arguments.cold_child:
        if arguments.build_root is None:
            parser.error("--cold-child requires --build-root")
        print(json.dumps(_cold_child(arguments.build_root), sort_keys=True), end="")
        return 0
    output_path = (
        _canonical_non_symlink_path(arguments.output, label="output")
        if arguments.output is not None
        else None
    )
    owns_workspace = arguments.work_root is None
    if owns_workspace:
        workspace = _canonical_non_symlink_path(
            Path(tempfile.mkdtemp(prefix=f"ucope_r01_r03_{arguments.stage}_benchmark_")),
            label="work root",
        )
    else:
        workspace = _canonical_non_symlink_path(
            arguments.work_root, label="work root",
        )
        workspace.mkdir(parents=True, exist_ok=True)
        workspace = _canonical_non_symlink_path(workspace, label="work root")
    try:
        runner = _benchmark if arguments.stage == "s0" else _benchmark_s1
        record = runner(workspace)
        record["stage"] = arguments.stage
        record["command"] = {
            "interpreter": sys.executable,
            "program": effective_argv[0],
            "module": __name__,
            "stage": arguments.stage,
            "argv": effective_argv,
        }
        if output_path is not None and arguments.stage == "s1":
            for _ in range(3):
                encoded = json.dumps(
                    record, sort_keys=True, indent=2, allow_nan=False,
                ).encode("utf-8") + b"\n"
                record["measured_resources"]["durable_bytes"] = len(encoded)
        _verify_record_source_hashes(record)
        if output_path is not None:
            _write_json(output_path, record)
        gate_name = "all_s0_gates_pass" if arguments.stage == "s0" else "all_s1_gates_pass"
        print(
            json.dumps(
                {
                    "stage": arguments.stage,
                    "schema": record["schema"],
                    "command": record["command"],
                    gate_name: record[gate_name],
                    "measured_resources": record["measured_resources"],
                    "complete_plan_projection": record["complete_plan_projection"],
                },
                sort_keys=True,
            )
        )
        return 0 if record[gate_name] else 2
    finally:
        if owns_workspace:
            shutil.rmtree(
                _canonical_non_symlink_path(workspace, label="work root"),
                ignore_errors=True,
            )


if __name__ == "__main__":
    raise SystemExit(main())
