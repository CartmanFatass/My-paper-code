"""Proof-sized benchmark for variable-roster low-step host transfers.

This benchmark measures only the immutable host-transfer slice.  It verifies
the packed candidate against the legacy NumPy arrays before timing and reports
whether this fixed machine justifies changing the production default.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Callable

import numpy as np
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ha_ctse_process import variable_roster_event_batching as batching


def _workload(*, device: torch.device, rows: int, environments: int) -> dict[str, torch.Tensor]:
    if rows < environments or environments <= 0:
        raise ValueError("benchmark requires rows >= environments > 0")
    generator = torch.Generator(device=device)
    generator.manual_seed(20260815)

    def random(*shape: int) -> torch.Tensor:
        return torch.rand(*shape, dtype=torch.float32, device=device, generator=generator)

    return {
        "member_obs": random(rows, 32),
        "skills": torch.arange(rows, dtype=torch.int64, device=device) % 8,
        "critic_member_features": random(rows, 24),
        "critic_global_features": random(environments, 16),
        "actor_hidden_before": random(rows, 64),
        "critic_hidden_before": random(rows, 64),
        "actions": torch.arange(rows, dtype=torch.int64, device=device) % 5,
        "logp": random(rows),
        "values": random(rows),
        "actor_hidden": random(rows, 64),
        "critic_hidden": random(rows, 64),
        "critic_source": random(rows, 81),
    }


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _assert_oracle(
    reference: dict[str, np.ndarray], candidate: dict[str, np.ndarray]
) -> None:
    if set(reference) != set(candidate):
        raise RuntimeError("packed low-step transfer changed the field set")
    for name, expected in reference.items():
        actual = candidate[name]
        if (
            actual.shape != expected.shape
            or actual.dtype != expected.dtype
            or not np.array_equal(actual, expected)
        ):
            raise RuntimeError(f"packed low-step transfer changed field {name!r}")


def _time_backend(
    function: Callable[[dict[str, torch.Tensor]], dict[str, np.ndarray]],
    tensors: dict[str, torch.Tensor],
    *,
    iterations: int,
    device: torch.device,
) -> float:
    _synchronize(device)
    started = time.perf_counter()
    checksum = 0.0
    for _ in range(iterations):
        result = function(tensors)
        checksum += float(result["values"][0])
    _synchronize(device)
    elapsed = time.perf_counter() - started
    if not np.isfinite(checksum):
        raise RuntimeError("benchmark checksum is non-finite")
    return elapsed


def run_benchmark(
    *,
    repeats: int = 31,
    iterations: int = 200,
    rows: int = 64,
    environments: int = 8,
    device: str = "cpu",
) -> dict[str, object]:
    if repeats < 3 or iterations <= 0:
        raise ValueError("benchmark requires at least three repeats and one iteration")
    selected_device = torch.device(device)
    if selected_device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA benchmark requested but CUDA is unavailable")
    tensors = _workload(
        device=selected_device,
        rows=int(rows),
        environments=int(environments),
    )
    legacy = batching._legacy_low_step_cpu_cache(tensors)
    packed = batching._packed_low_step_cpu_cache(tensors)
    _assert_oracle(legacy, packed)

    for _ in range(5):
        batching._legacy_low_step_cpu_cache(tensors)
        batching._packed_low_step_cpu_cache(tensors)
    timings = {"legacy": [], "packed": []}
    functions = {
        "legacy": batching._legacy_low_step_cpu_cache,
        "packed": batching._packed_low_step_cpu_cache,
    }
    for repeat in range(repeats):
        order = ("legacy", "packed") if repeat % 2 == 0 else ("packed", "legacy")
        for name in order:
            timings[name].append(
                _time_backend(
                    functions[name],
                    tensors,
                    iterations=iterations,
                    device=selected_device,
                )
            )
    legacy_median = statistics.median(timings["legacy"])
    packed_median = statistics.median(timings["packed"])
    packed_is_faster = packed_median < legacy_median
    return {
        "schema": "hmasd.variable_roster_low_step_host_transfer_benchmark.v1",
        "bounded_workload": True,
        "oracle_equal": True,
        "device": str(selected_device),
        "torch_version": torch.__version__,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "rows": int(rows),
        "environments": int(environments),
        "repeats": int(repeats),
        "iterations": int(iterations),
        "legacy_median_seconds": legacy_median,
        "packed_median_seconds": packed_median,
        "packed_speedup": legacy_median / packed_median,
        "packed_is_faster": packed_is_faster,
        "production_default": batching.DEFAULT_LOW_STEP_HOST_TRANSFER,
        "promotion_allowed": bool(
            packed_is_faster
            and batching.DEFAULT_LOW_STEP_HOST_TRANSFER
            == batching.PACKED_LOW_STEP_HOST_TRANSFER
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=31)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--rows", type=int, default=64)
    parser.add_argument("--environments", type=int, default=8)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    encoded = json.dumps(
        run_benchmark(
            repeats=arguments.repeats,
            iterations=arguments.iterations,
            rows=arguments.rows,
            environments=arguments.environments,
            device=arguments.device,
        ),
        indent=2,
        sort_keys=True,
    )
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
