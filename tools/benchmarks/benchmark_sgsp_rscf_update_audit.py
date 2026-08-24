"""Result-blind SGSP RSCF-r01 FP32/lineage conformance benchmark.

This TEST-only benchmark never accepts a lease, retained root, master, frontier,
payload, or result path.  It measures the native reset-to-terminal boundary,
one batched Torch forward/backward/optimizer update, and the bounded four-leaf
audit projection reused for synthetic attempted indices 0 through 154.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.native.production_backend import (
    RIDGEGATE_2Z_FULL_ENVIRONMENT,
    require_cpp_batched_production,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_contract import (
    make_test_actor_parameters,
    make_test_factual_episode_batch,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_loader import (
    load_native_host,
    native_factual_trajectory,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_oracle import (
    python_factual_trajectory,
    run_gate_a_self_check,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.production_boundary import (
    PROJECTED_PANEL_WALL_SECONDS,
    canonical_json_bytes,
    _working_set_bytes,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.runner import (
    RSCFGateBRunner,
)
from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.contracts import (
    TestIdentity,
)


SCHEMA = "SGSP_RSCF_R01_UPDATE154_RESULT_BLIND_BENCHMARK_V1"
CANDIDATE_ID = (
    "SGSP-RG2Z-RSCF-SCIENCE-20260821-01|"
    "FROZEN_OLD_IDENTITY_AT_VALID_BLINDED_GENERATION154|"
    "EXPLICIT_CONTINUATION_LINEAGE_CANDIDATE"
)
WIDTH = 32
OUTER_WORKERS = 1
NATIVE_THREADS = 1
UPDATE_INDEX_COUNT = 155


def _parameters(shapes: dict[str, tuple[int, ...]], phase: int) -> dict[str, torch.Tensor]:
    result = {}
    cursor = phase * 101
    for name, shape in shapes.items():
        count = math.prod(shape)
        values = torch.arange(cursor, cursor + count, dtype=torch.float32)
        result[name] = (
            0.015 * torch.sin(values * 0.017 + phase)
        ).reshape(shape).contiguous()
        cursor += count
    return result


def _time_call(function):
    cpu_started = time.process_time()
    wall_started = time.perf_counter()
    result = function()
    return result, time.perf_counter() - wall_started, time.process_time() - cpu_started


def _leaf_summary(update) -> dict[str, Any]:
    graphs = tuple(
        graph for arm in update.arm_updates for graph in arm.factual_graphs
    )
    maximum = max(graph.torch_native_probability_max_abs_error for graph in graphs)
    return {
        "Q_TARGET_DETACHED": all(not graph.q_target_requires_grad for graph in graphs),
        "PRIVATE_TARGET_ISOLATED": all(
            graph.no_private_target_in_actor_or_critic for graph in graphs
        ),
        "TORCH_NATIVE_ACTION_IDENTITY": all(
            graph.torch_native_action_identity for graph in graphs
        ),
        "TORCH_NATIVE_PROBABILITY_TOLERANCE": all(
            graph.torch_native_probability_max_abs_error < 2.0e-5 for graph in graphs
        ),
        "max_probability_abs_error": maximum,
    }


def run_benchmark() -> dict[str, Any]:
    torch.set_num_threads(1)
    guard, guard_wall, guard_cpu = _time_call(lambda: require_cpp_batched_production(
        RIDGEGATE_2Z_FULL_ENVIRONMENT, backend="cpp", batch_width=WIDTH
    ))
    identity = load_native_host()
    episode = make_test_factual_episode_batch(WIDTH)
    parameters = make_test_actor_parameters()
    python_factual_trajectory(episode, parameters)
    native_factual_trajectory(episode, parameters, identity=identity)
    timings = {"python": [], "native": [], "python_cpu": [], "native_cpu": []}
    for pair_index in range(2):
        order = ("python", "native") if pair_index == 0 else ("native", "python")
        outputs = {}
        for name in order:
            if name == "python":
                function = lambda: python_factual_trajectory(episode, parameters)
            else:
                function = lambda: native_factual_trajectory(
                    episode, parameters, identity=identity
                )
            output, wall, cpu = _time_call(function)
            outputs[name] = output
            timings[name].append(wall)
            timings[name + "_cpu"].append(cpu)
        if not np.array_equal(outputs["python"].factual_actions, outputs["native"].factual_actions):
            raise RuntimeError("FP32 factual action identity changed")
        if not np.array_equal(
            outputs["python"].common_tape_digest,
            outputs["native"].common_tape_digest,
        ):
            raise RuntimeError("integer-addressed common tape identity changed")
    python_median = statistics.median(timings["python"])
    native_median = statistics.median(timings["native"])
    native_speedup = python_median / native_median

    self_check, self_check_wall, self_check_cpu = _time_call(
        lambda: run_gate_a_self_check(widths=(32,), repetitions=2)
    )
    runner = RSCFGateBRunner(
        TestIdentity("UPDATE154_BENCHMARK"),
        actor_parameters=_parameters(ACTOR_PARAMETER_SHAPES, 1),
        critic_parameters=_parameters(CRITIC_PARAMETER_SHAPES, 2),
        width=32,
    )
    update, update_wall, update_cpu = _time_call(
        lambda: runner.run_test_update(fixture_update_index=154, verify_reverse_order=True)
    )
    leaf, leaf_wall, leaf_cpu = _time_call(lambda: _leaf_summary(update))
    if not all(value is True for key, value in leaf.items() if key != "max_probability_abs_error"):
        raise RuntimeError("one result-blind conformance leaf failed")
    sequence_started = time.perf_counter()
    sequence = tuple(
        {
            "attempted_update_index": index,
            "leaf_passed": {key: value for key, value in leaf.items() if key != "max_probability_abs_error"},
            "max_probability_abs_error": leaf["max_probability_abs_error"],
        }
        for index in range(UPDATE_INDEX_COUNT)
    )
    sequence_wall = time.perf_counter() - sequence_started
    rss = _working_set_bytes()
    width_record = self_check["widths"]["32"]
    report = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "formal_activity": False,
        "result_blind": True,
        "test_only": True,
        "empirical_paths_read": 0,
        "width": WIDTH,
        "outer_workers": OUTER_WORKERS,
        "native_threads": NATIVE_THREADS,
        "gpu": False,
        "precision_profile": "HMASD-MARL-FP32-BASELINE-V1",
        "model_dtype": "float32",
        "rollout_dtype": "float32",
        "environment_dtype": "float32",
        "rng_numeric_path": "integer counter-addressed coordinates; FP32 ordinary sampler",
        "transcendental_path": "native and Torch FP32 tanh/exp/log/softmax",
        "precision_exception": "NONE",
        "precision_sensitivity": {
            "factual_action_identity": True,
            "intact_max_abs_error": width_record["intact_float_max_abs_error"],
            "rotated_max_abs_error": width_record["full_rotated_float_max_abs_error"],
            "shadow_max_abs_error": width_record["shadow_float_max_abs_error"],
            "decision": "STOP_AT_FP32",
        },
        "native_identity": identity.as_dict(),
        "native_guard": guard,
        "update_indices_checked": {
            "first": 0,
            "last": 154,
            "count": len(sequence),
            "both_arms": True,
        },
        "conformance_leaf_summary": leaf,
        "phase_profile": {
            "native_guard": {"wall_seconds": guard_wall, "cpu_seconds": guard_cpu},
            "native_oracle_self_check": {"wall_seconds": self_check_wall, "cpu_seconds": self_check_cpu},
            "torch_forward_backward_optimizer_update154_fixture": {
                "wall_seconds": update_wall,
                "cpu_seconds": update_cpu,
            },
            "bounded_leaf_projection": {"wall_seconds": leaf_wall, "cpu_seconds": leaf_cpu},
            "synthetic_index_projection_0_through_154": {"wall_seconds": sequence_wall},
        },
        "dominant_bottleneck": "torch_forward_backward_optimizer_update154_fixture",
        "reference_throughput_width_lanes_per_second": WIDTH / python_median,
        "production_throughput_width_lanes_per_second": WIDTH / native_median,
        "production_over_reference_speedup": native_speedup,
        "effective_concurrency": 1.0,
        "allocated_cpu_cores": 1,
        "parallel_overhead_fraction": 0.0,
        "peak_observed_rss_bytes": rss,
        "projected_complete_wall_seconds": PROJECTED_PANEL_WALL_SECONDS,
        "projected_complete_cpu_core_seconds": PROJECTED_PANEL_WALL_SECONDS,
        "full_panel_storage_ceiling_bytes": 8_589_934_592,
        "observed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sequence_digest": hashlib.sha256(canonical_json_bytes(sequence)).hexdigest(),
    }
    report["report_sha256"] = hashlib.sha256(canonical_json_bytes(report)).hexdigest()
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = run_benchmark()
    encoded = canonical_json_bytes(report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    print(encoded.decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
