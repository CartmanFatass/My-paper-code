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
    for _repeat in range(repeats):
        started = perf_counter()
        _python_episode(ledgers, actions)
        python_seconds.append(perf_counter() - started)
        started = perf_counter()
        _native_episode(ledgers, actions)
        native_seconds.append(perf_counter() - started)
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
        "python_seconds": python_seconds,
        "native_seconds": native_seconds,
        "python_median_seconds": python_median,
        "native_median_seconds": native_median,
        "speedup": python_median / native_median,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--capacity", type=int, choices=(6, 8, 12), default=8)
    parser.add_argument("--repeats", type=int, default=10)
    arguments = parser.parse_args()
    print(
        json.dumps(
            run_benchmark(
                batch_size=arguments.batch_size,
                capacity=arguments.capacity,
                repeats=arguments.repeats,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
