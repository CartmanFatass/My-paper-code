"""Proof-sized CPU benchmark for the batched UAV C++ geometry kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

import numpy as np
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from envs.pettingzoo.uav_cpp_backend import BatchedUAVGeometry, step_geometry_batch


SPEEDUP_THRESHOLD = 1.20


def _air_to_ground(
    airborne: np.ndarray,
    ground: np.ndarray,
    *,
    frequency: float,
) -> float:
    delta = airborne - ground
    distance_3d = np.sqrt(np.sum(delta**2))
    distance_2d = np.sqrt(delta[0] ** 2 + delta[1] ** 2)
    safe_distance_3d = max(distance_3d, 1e-6)
    safe_distance_2d = max(distance_2d, 1e-6)
    elevation_angle = np.degrees(np.arctan(abs(delta[2]) / safe_distance_2d))
    p_los = 1.0 / (1.0 + 0.3 * np.exp(-5e-4 * (elevation_angle - 0.3)))
    p_los = np.clip(p_los, 0.0, 1.0)
    fspl = (
        20.0 * np.log10(safe_distance_3d)
        + 20.0 * np.log10(frequency)
        - 147.55
    )
    los_linear = 10.0 ** (-(fspl + 1.5) / 10.0)
    nlos_linear = 10.0 ** (-(fspl + 25.0) / 10.0)
    return float(-10.0 * np.log10(p_los * los_linear + (1.0 - p_los) * nlos_linear))


def _air_to_air(
    first: np.ndarray, second: np.ndarray, *, frequency: float
) -> float:
    distance = np.sqrt(np.sum((first - second) ** 2))
    return float(
        20.0 * np.log10(max(distance, 1e-6))
        + 20.0 * np.log10(frequency)
        - 147.55
    )


def _python_reference(
    uavs: np.ndarray,
    users: np.ndarray,
    bases: np.ndarray,
    velocities: np.ndarray,
    movable: np.ndarray,
) -> BatchedUAVGeometry:
    time_step = 0.37
    frequency = 2.0e9
    next_uavs = uavs.copy()
    for batch_index in range(uavs.shape[0]):
        for uav_index in range(uavs.shape[1]):
            candidate = uavs[batch_index, uav_index].copy()
            if movable[batch_index, uav_index]:
                candidate += velocities[batch_index, uav_index] * time_step
            candidate[0] = np.clip(candidate[0], 0.0, 1000.0)
            candidate[1] = np.clip(candidate[1], 0.0, 1000.0)
            candidate[2] = np.clip(candidate[2], 50.0, 200.0)
            next_uavs[batch_index, uav_index] = candidate

    access = np.empty(
        (uavs.shape[0], uavs.shape[1], users.shape[1]), dtype=np.float64
    )
    air = np.empty(
        (uavs.shape[0], uavs.shape[1], uavs.shape[1]), dtype=np.float64
    )
    base = np.empty(
        (uavs.shape[0], uavs.shape[1], bases.shape[1]), dtype=np.float64
    )
    for batch_index in range(uavs.shape[0]):
        for uav_index in range(uavs.shape[1]):
            airborne = next_uavs[batch_index, uav_index]
            for user_index in range(users.shape[1]):
                access[batch_index, uav_index, user_index] = _air_to_ground(
                    airborne,
                    users[batch_index, user_index],
                    frequency=frequency,
                )
            for peer_index in range(uavs.shape[1]):
                air[batch_index, uav_index, peer_index] = _air_to_air(
                    airborne,
                    next_uavs[batch_index, peer_index],
                    frequency=frequency,
                )
            for base_index in range(bases.shape[1]):
                base[batch_index, uav_index, base_index] = _air_to_ground(
                    airborne,
                    bases[batch_index, base_index],
                    frequency=frequency,
                )
    return BatchedUAVGeometry(next_uavs, access, air, base)


def _native(
    uavs: np.ndarray,
    users: np.ndarray,
    bases: np.ndarray,
    velocities: np.ndarray,
    movable: np.ndarray,
) -> BatchedUAVGeometry:
    return step_geometry_batch(
        uav_positions=uavs,
        user_positions=users,
        ground_bs_positions=bases,
        prepared_velocities=velocities,
        movable_mask=movable,
        time_step=0.37,
        area_size=1000.0,
        height_range=(50.0, 200.0),
        carrier_frequency=2.0e9,
        environment_type="urban",
    )


def _inputs(seed: int) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    uavs = np.empty((8, 8, 3), dtype=np.float64)
    uavs[..., :2] = rng.uniform(0.0, 1000.0, size=(8, 8, 2))
    uavs[..., 2] = rng.uniform(50.0, 200.0, size=(8, 8))
    users = np.empty((8, 30, 3), dtype=np.float64)
    users[..., :2] = rng.uniform(0.0, 1000.0, size=(8, 30, 2))
    users[..., 2] = 1.5
    base_template = np.array(
        [[0.0, 500.0, 0.0], [1000.0, 500.0, 0.0]], dtype=np.float64
    )
    bases = np.repeat(base_template[None, ...], 8, axis=0)
    velocities = rng.uniform(-20.0, 20.0, size=(8, 8, 3)).astype(np.float32)
    movable = np.ascontiguousarray(rng.random((8, 8)) > 0.1, dtype=np.bool_)
    return uavs, users, bases, velocities, movable


def _exact_equal(left: BatchedUAVGeometry, right: BatchedUAVGeometry) -> bool:
    return all(
        np.array_equal(a, b)
        for a, b in zip(
            (
                left.next_uav_positions,
                left.access_path_loss,
                left.air_path_loss,
                left.base_path_loss,
            ),
            (
                right.next_uav_positions,
                right.access_path_loss,
                right.air_path_loss,
                right.base_path_loss,
            ),
        )
    )


def _measure(callable_, inputs: tuple[np.ndarray, ...], iterations: int) -> float:
    started = time.perf_counter()
    for _ in range(iterations):
        callable_(*inputs)
    return (time.perf_counter() - started) / iterations


def run_benchmark(*, repeats: int, iterations: int, seed: int) -> dict[str, object]:
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    inputs = _inputs(seed)
    reference = _python_reference(*inputs)
    candidate = _native(*inputs)
    exact = _exact_equal(reference, candidate)
    if not exact:
        raise RuntimeError("native benchmark candidate differs from Python bitwise")
    for _ in range(3):
        _python_reference(*inputs)
        _native(*inputs)

    timings = {"python": [], "cpp": []}
    for repeat in range(repeats):
        order = (
            (("python", _python_reference), ("cpp", _native))
            if repeat % 2 == 0
            else (("cpp", _native), ("python", _python_reference))
        )
        for name, callable_ in order:
            timings[name].append(_measure(callable_, inputs, iterations))
    python_median = statistics.median(timings["python"])
    cpp_median = statistics.median(timings["cpp"])
    speedup = python_median / cpp_median
    return {
        "schema": "hmasd.uav_cpp_geometry_benchmark.v1",
        "formal": False,
        "conclusion_bearing": False,
        "backend": "cpu",
        "torch_threads": 1,
        "seed": seed,
        "workload": {
            "batch": 8,
            "uavs": 8,
            "users": 30,
            "ground_bases": 2,
            "repeats": repeats,
            "iterations_per_repeat": iterations,
            "alternating_order": True,
            "warmup_pairs": 3,
        },
        "bitwise_equal": exact,
        "python_seconds_per_call": timings["python"],
        "cpp_seconds_per_call": timings["cpp"],
        "python_median_seconds": python_median,
        "cpp_median_seconds": cpp_median,
        "speedup": speedup,
        "required_speedup": SPEEDUP_THRESHOLD,
        "accepted": exact and speedup >= SPEEDUP_THRESHOLD,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260725)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repeats < 3 or args.iterations < 1:
        raise ValueError("benchmark requires at least three repeats and one iteration")
    result = run_benchmark(
        repeats=args.repeats, iterations=args.iterations, seed=args.seed
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["accepted"] is not True:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
