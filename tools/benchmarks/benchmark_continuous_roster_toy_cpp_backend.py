"""Reproducible non-scientific microbenchmark for the toy C++ environment slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as g38
from envs.continuous_roster import cpp_backend as cpp
from envs.continuous_roster import runtime_capacity as roster_env


def _profiles(capacity: int, batch_size: int) -> tuple[roster_env.RosterProfile, ...]:
    if capacity == 6:
        return (roster_env.SMALL_CAPACITY_6,) * batch_size
    if capacity == 12:
        return (roster_env.LARGE_CAPACITY_12,) * batch_size
    if capacity == 8:
        return tuple(roster_env.TRAIN_PROFILES[index % 3] for index in range(batch_size))
    raise ValueError("benchmark capacity must be 6, 8, or 12")


def _python_episode(
    ledgers: tuple[roster_env.CapacityRosterLedger, ...], actions: np.ndarray
) -> tuple[roster_env.CapacityRosterOutcome, ...]:
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    for _time in range(roster_env.HORIZON):
        views = tuple(
            g38.observe_g38_actor_source(env, input_mode=g38.FOLD6_INPUT)
            for env in envs
        )
        for index, (env, view) in enumerate(zip(envs, views)):
            g38.advance_g38_environment(env, view, actions[index])
    return tuple(env.outcome() for env in envs)


def _native_episode(
    ledgers: tuple[roster_env.CapacityRosterLedger, ...], actions: np.ndarray
) -> tuple[roster_env.CapacityRosterOutcome, ...]:
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    batch = cpp.ContinuousRosterToyBatch(envs)
    for _time in range(roster_env.HORIZON):
        views = batch.observe_six()
        batch.advance(views, actions)
    return tuple(env.outcome() for env in envs)


def run_benchmark(*, batch_size: int, capacity: int, repeats: int) -> dict[str, object]:
    if batch_size <= 0 or repeats <= 0:
        raise ValueError("batch_size and repeats must be positive")
    ledgers = tuple(
        roster_env.make_ledger(
            index,
            master_seed=10_992_000,
            profile=profile,
        )
        for index, profile in enumerate(_profiles(capacity, batch_size))
    )
    actions = np.zeros((batch_size, capacity, roster_env.ACTION_DIM), dtype=np.float32)
    reference = _python_episode(ledgers, actions)
    accelerated = _native_episode(ledgers, actions)
    if accelerated != reference:
        raise RuntimeError("benchmark oracle mismatch")

    python_seconds: list[float] = []
    native_seconds: list[float] = []
    for repeat in range(repeats):
        order = (
            (("python", _python_episode), ("native", _native_episode))
            if repeat % 2 == 0
            else (("native", _native_episode), ("python", _python_episode))
        )
        for name, implementation in order:
            started = perf_counter()
            implementation(ledgers, actions)
            elapsed = perf_counter() - started
            (python_seconds if name == "python" else native_seconds).append(elapsed)
    python_median = median(python_seconds)
    native_median = median(native_seconds)
    return {
        "schema": "continuous_roster_toy_cpp_benchmark_v1",
        "cpu_only": True,
        "bitwise_outcome_oracle": True,
        "batch_size": batch_size,
        "capacity": capacity,
        "horizon": roster_env.HORIZON,
        "repeats": repeats,
        "alternating_order": True,
        "python_seconds": python_seconds,
        "native_seconds": native_seconds,
        "python_median_seconds": python_median,
        "native_median_seconds": native_median,
        "speedup": python_median / native_median,
    }


def run_benchmark_matrix(
    *, batch_sizes: tuple[int, ...], capacity: int, repeats: int
) -> dict[str, object]:
    """Benchmark complete reset-to-terminal episodes at declared batch widths."""

    if not batch_sizes or any(width <= 0 for width in batch_sizes):
        raise ValueError("batch_sizes must contain positive widths")
    if len(set(batch_sizes)) != len(batch_sizes):
        raise ValueError("batch_sizes must be unique")
    cold_started = perf_counter()
    cpp.load_continuous_roster_toy_cpp_backend()
    process_cold_preflight_seconds = perf_counter() - cold_started
    results = [
        run_benchmark(batch_size=width, capacity=capacity, repeats=repeats)
        for width in batch_sizes
    ]
    return {
        "schema": "continuous_roster_toy_cpp_batch_matrix_v2",
        "formal": False,
        "conclusion_bearing": False,
        "native_scope": "observation_reward_hot_path_with_python_lifecycle",
        "full_reset_to_terminal_episode": True,
        "process_cold_preflight_seconds": process_cold_preflight_seconds,
        "steady_measurement_excludes_process_cold_preflight": True,
        "batch_sizes": list(batch_sizes),
        "results": results,
        "bitwise_outcome_oracle": all(
            result["bitwise_outcome_oracle"] for result in results
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=(1, 8, 32))
    parser.add_argument("--capacity", type=int, choices=(6, 8, 12), default=8)
    parser.add_argument("--repeats", type=int, default=10)
    arguments = parser.parse_args()
    print(
        json.dumps(
            run_benchmark_matrix(
                batch_sizes=tuple(arguments.batch_sizes),
                capacity=arguments.capacity,
                repeats=arguments.repeats,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
