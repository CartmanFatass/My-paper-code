"""Fixed-workload benchmark for standalone collector result transports.

The benchmark is deliberately synthetic but exercises complete ``EnvStep``
objects, including observations, critic state, nested process outcomes, strings,
and environment RNG draws.  It never changes the production default itself;
its JSON result is the evidence used to decide whether ``shared_memory_v1`` may
replace ``pipe_pickle`` on a fixed machine.
"""

from __future__ import annotations

import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
import pickle
import platform
import statistics
import sys
import time
from types import SimpleNamespace

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ha_ctse_process.collectors import (
    DEFAULT_SUBPROC_TRANSPORT,
    PIPE_PICKLE_TRANSPORT,
    SHARED_MEMORY_TRANSPORT,
    SubprocEnvCollector,
)


BENCHMARK_NAME = "standalone_collector_transport_v2"
WARMUP_STEPS = 5
ACTION_WIDTH = 8
SOURCE_PATHS = (
    Path("ha_ctse_process/collectors.py"),
    Path("tools/benchmarks/benchmark_collectors.py"),
)


class _ActionSpace:
    dtype = np.dtype(np.int64)
    shape = (8,)
    n = 5


class BenchmarkCollectorEnv:
    obs_dim = 128
    state_dim = 256
    action_dim = 5
    n_uavs = 8
    action_space = _ActionSpace()

    def __init__(self, rank: int, width: int):
        self.rank = int(rank)
        self.width = int(width)
        self.step_count = 0
        self.rng = np.random.default_rng(1)

    def reset(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.step_count = 0
        return self._obs(), self._info()

    def _obs(self):
        return self.rng.normal(size=(self.n_uavs, self.width)).astype(np.float32)

    def _info(self):
        state = self.rng.normal(size=self.width * 2).astype(np.float32)
        return {
            "state": state,
            "next_state": state.copy(),
            "worker": self.rank,
            "process_outcome": {
                "frontier": tuple(range(self.n_uavs)),
                "active_mask": np.ones(self.n_uavs, dtype=np.bool_),
                "score": float(self.rng.random()),
            },
        }

    def step(self, action):
        self.step_count += 1
        info = self._info()
        info["action"] = np.asarray(action).copy()
        return self._obs(), float(self.rng.random()), False, False, info

    def close(self):
        return None


def _collector(transport: str, num_envs: int, width: int):
    return SubprocEnvCollector(
        config=SimpleNamespace(),
        scenario="base",
        seed=0,
        num_envs=num_envs,
        scale_mode="train",
        start_method="spawn",
        transport=transport,
        shared_memory_bytes=max(1 << 20, num_envs * width * 128),
        env_factories=[
            partial(BenchmarkCollectorEnv, rank=rank, width=width)
            for rank in range(num_envs)
        ],
    )


def _digest(value) -> str:
    return hashlib.sha256(
        pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    ).hexdigest()


def _canonical_sha256(value) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_fingerprint() -> dict[str, object]:
    files = {
        path.as_posix(): hashlib.sha256((REPOSITORY_ROOT / path).read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    default_declaration = {
        "symbol": "ha_ctse_process.collectors.DEFAULT_SUBPROC_TRANSPORT",
        "value": str(DEFAULT_SUBPROC_TRANSPORT),
    }
    default_declaration["sha256"] = _canonical_sha256(default_declaration)
    aggregate_payload = {
        "files": files,
        "production_default_declaration": default_declaration,
    }
    return {
        "algorithm": "sha256",
        "files": files,
        "production_default_declaration": default_declaration,
        "aggregate_sha256": _canonical_sha256(aggregate_payload),
    }


def _evidence_context(
    *, repeats: int, iterations: int, num_envs: int, width: int, seed: int
) -> tuple[dict[str, object], dict[str, object], str]:
    shared_memory_bytes = max(1 << 20, num_envs * width * 128)
    configuration = {
        "reference_transport": PIPE_PICKLE_TRANSPORT,
        "optimized_transport": SHARED_MEMORY_TRANSPORT,
        "production_default_under_test": str(DEFAULT_SUBPROC_TRANSPORT),
        "multiprocessing_start_method": "spawn",
        "shared_memory_bytes_per_worker": shared_memory_bytes,
        "pickle_protocol": int(pickle.HIGHEST_PROTOCOL),
        "warmup_steps": WARMUP_STEPS,
        "sample_execution_order": "alternating_reference_first_by_sample_parity",
        "timing_clock": "time.perf_counter",
        "statistic": "median_seconds_per_collector_step",
        "acceptance": {
            "semantic_rng_equivalence_required": True,
            "optimized_median_strictly_less_than_reference": True,
        },
        "synthetic_environment": {
            "class": "BenchmarkCollectorEnv",
            "n_uavs": BenchmarkCollectorEnv.n_uavs,
            "obs_dim_contract": BenchmarkCollectorEnv.obs_dim,
            "state_dim_contract": BenchmarkCollectorEnv.state_dim,
            "action_dim": BenchmarkCollectorEnv.action_dim,
            "observation_dtype": "float32",
            "state_dtype": "float32",
            "action_dtype": "int64",
            "terminated": False,
            "truncated": False,
            "nested_process_outcome_included": True,
        },
    }
    workload = {
        "seed": seed,
        "repeats": repeats,
        "iterations_per_sample": iterations,
        "num_envs": num_envs,
        "observation_shape_per_env": [BenchmarkCollectorEnv.n_uavs, width],
        "state_shape_per_env": [width * 2],
        "action_shape_per_env": [ACTION_WIDTH],
        "measured_collector_steps_per_transport": repeats * iterations,
    }
    fingerprint = _canonical_sha256(
        {"configuration": configuration, "workload": workload}
    )
    return configuration, workload, fingerprint


def _enforce_acceptance(result: dict[str, object]) -> None:
    if not bool(result["semantic_rng_equivalence"]):
        raise RuntimeError("collector transport semantic/RNG equivalence failed")
    if not bool(result["shared_memory_positive_median"]):
        raise RuntimeError(
            "collector shared-memory median is non-positive; production promotion is forbidden"
        )


def _measure(collector, actions, iterations: int) -> tuple[float, str]:
    digest = hashlib.sha256()
    started = time.perf_counter()
    for _ in range(iterations):
        digest.update(bytes.fromhex(_digest(collector.step(actions))))
    return time.perf_counter() - started, digest.hexdigest()


def run_benchmark(
    *, repeats: int = 31,
    iterations: int = 10,
    num_envs: int = 4,
    width: int = 4096,
    seed: int = 20260815,
) -> dict[str, object]:
    if repeats < 31 or repeats % 2 != 1:
        raise ValueError("collector benchmark requires an odd sample count of at least 31")
    if iterations <= 0 or num_envs <= 0 or width <= 0:
        raise ValueError("collector benchmark dimensions must be positive")

    pipe = _collector(PIPE_PICKLE_TRANSPORT, num_envs, width)
    shared = _collector(SHARED_MEMORY_TRANSPORT, num_envs, width)
    actions = [np.arange(ACTION_WIDTH, dtype=np.int64) % 5 for _ in range(num_envs)]
    pipe_times: list[float] = []
    shared_times: list[float] = []
    semantic_match = True
    try:
        pipe_reset = pipe.reset_all(seed)
        shared_reset = shared.reset_all(seed)
        semantic_match &= _digest(pipe_reset) == _digest(shared_reset)
        for _ in range(WARMUP_STEPS):
            semantic_match &= _digest(pipe.step(actions)) == _digest(shared.step(actions))

        for sample in range(repeats):
            if sample % 2 == 0:
                pipe_elapsed, pipe_digest = _measure(pipe, actions, iterations)
                shared_elapsed, shared_digest = _measure(shared, actions, iterations)
            else:
                shared_elapsed, shared_digest = _measure(shared, actions, iterations)
                pipe_elapsed, pipe_digest = _measure(pipe, actions, iterations)
            pipe_times.append(pipe_elapsed / iterations)
            shared_times.append(shared_elapsed / iterations)
            semantic_match &= pipe_digest == shared_digest
    finally:
        pipe.close()
        shared.close()

    pipe_median = statistics.median(pipe_times)
    shared_median = statistics.median(shared_times)
    configuration, workload, configuration_workload_sha256 = _evidence_context(
        repeats=repeats,
        iterations=iterations,
        num_envs=num_envs,
        width=width,
        seed=seed,
    )
    result = {
        "benchmark": BENCHMARK_NAME,
        "source_fingerprint": _source_fingerprint(),
        "configuration": configuration,
        "workload": workload,
        "configuration_workload_sha256": configuration_workload_sha256,
        "production_default_under_test": str(DEFAULT_SUBPROC_TRANSPORT),
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "python_executable": sys.executable,
            "numpy": np.__version__,
        },
        "semantic_rng_equivalence": bool(semantic_match),
        "pipe_pickle_median_seconds": pipe_median,
        "shared_memory_v1_median_seconds": shared_median,
        "shared_memory_speedup": pipe_median / shared_median,
        "shared_memory_positive_median": bool(
            semantic_match and shared_median < pipe_median
        ),
    }
    _enforce_acceptance(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=31)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--width", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_benchmark(
        repeats=args.repeats,
        iterations=args.iterations,
        num_envs=args.num_envs,
        width=args.width,
        seed=args.seed,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
