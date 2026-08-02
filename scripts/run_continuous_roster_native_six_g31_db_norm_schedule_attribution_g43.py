"""Train, evaluate, and analyze the frozen G43 norm-schedule attribution."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import sys
import time
import tracemalloc
from typing import Any, Mapping, Sequence

_THREAD_ENV_NAMES = (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
for _thread_env_name in _THREAD_ENV_NAMES:
    os.environ[_thread_env_name] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as source,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_direction_balance_attribution_g42 as g42,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from envs.continuous_roster import runtime_capacity as roster_env
from scripts import run_continuous_roster_native_six_coordinate_training_g39 as g39_runner
from scripts import run_continuous_roster_native_six_credit_reduction_g40 as g40_runner
from scripts import run_continuous_roster_reactive_reduction_g35 as g35_runner
from scripts import run_continuous_roster_six_coordinate_cs_g38 as g38_runner


SCHEMA_VERSION = 2
ALGORITHM_ID = source.ALGORITHM_ID
AUTHORIZATION_TOKEN = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_"
    "FORMAL_AUTHORIZATION_V1"
)
ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_ATTRIBUTION_G43_"
    "CODE_SCIENCE_ALIGNMENT_AUDIT"
)
# Independently archived G43 correction recheck disposition: ALIGNED.
ALIGNED_IMPLEMENTATION_COMMIT = "45e16f71d171228135b6444bee1678b157d79abe"
ALIGNMENT_STAGE_COMMIT = "889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76"
ACCEPTED_ANCHOR_ROOT_RELATIVE = Path(
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)

INVALID_BRANCH = (
    "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_ATTRIBUTION_G43"
)
SOURCE_FAILURE_BRANCH = "SOURCE_OR_REFERENCE_ACCESS_FAILURE_G43"
MEAN_SUFFICIENT_BRANCH = "EQUAL_MEAN_RAW_SUM_SUFFICIENT_G43"
DBNORM_ADVANTAGE_BRANCH = "DB_DERIVED_NORM_SCHEDULE_ADVANTAGE_G43"
UNDERPOWERED_BRANCH = "MIXED_UNDERPOWERED_DB_NORM_ATTRIBUTION_G43"
NONFORMAL_BRANCH = (
    "NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DB_NORM_SCHEDULE_"
    "ATTRIBUTION_G43_EXERCISE_COMPLETE"
)
NON_EXECUTABLE_BRANCH = "NON_EXECUTABLE_EVIDENCE_DESIGN"

FINAL_FIXED_DET = "FINAL_FIXED_DET"
FINAL_FIXED_STOCH = "FINAL_FIXED_STOCH"
FINAL_RANDOM_DET = "FINAL_RANDOM_DET"
FINAL_RANDOM_STOCH = "FINAL_RANDOM_STOCH"
MODEL_CELLS = (
    FINAL_FIXED_DET,
    FINAL_FIXED_STOCH,
    FINAL_RANDOM_DET,
    FINAL_RANDOM_STOCH,
)

UTILITY_FLOOR = 0.90
EVENT_FLOOR = 0.85
SEGMENT_FLOOR = 0.85
PROCESS_MARGIN = -0.05
STOCHASTIC_FLOOR = 0.80
MINIMUM_REPLICATE_FLOOR = 0.85
NORM_MARGIN = 0.05
NONFORMAL_WALL_CLOCK_CAP_SECONDS = 1_200.0
FORMAL_WALL_CLOCK_CAP_SECONDS = 28_800.0

FORMAL_REPLICATES = 3
FORMAL_BRANCH_UPDATES = 100
FORMAL_NUM_ENVS = 8
FORMAL_PPO_PASSES = 2
FORMAL_EVAL_EPISODES = 48
FORMAL_BOOTSTRAP_REPETITIONS = 10_000

EXERCISE_REPLICATES = 1
EXERCISE_BRANCH_UPDATES = 10
EXERCISE_NUM_ENVS = 8
EXERCISE_PPO_PASSES = 2
EXERCISE_EVAL_EPISODES = 6
EXERCISE_BOOTSTRAP_REPETITIONS = 250

SEED_BASES = {
    "branch_ledger": 10_431_000,
    "branch_action": 10_432_000,
    "branch_gradient_probe": 10_433_000,
    "evaluation_ledger": 10_434_000,
    "evaluation_process": 10_435_000,
    "evaluation_action": 10_436_000,
}
BOOTSTRAP_SEED = 10_437_043
NONFORMAL_SEED_OFFSET = 900_000
DEFAULT_CPU_BUDGET = 2
DEFAULT_PROCESS_WORKERS = 2
MAX_PROCESS_WORKERS = 6
WORKER_THREAD_ENV = {name: "1" for name in _THREAD_ENV_NAMES}

configure_runtime = g39_runner.configure_runtime
_runtime_identity = g39_runner._runtime_identity
_write_json = g39_runner._write_json
_read_json = g39_runner._read_json
_artifact_digest = g39_runner._artifact_digest
_state_digest = g39_runner._state_digest


def _resolve_cpu_execution(
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    budget = DEFAULT_CPU_BUDGET if cpu_budget is None else cpu_budget
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise TypeError("G43 cpu_budget must be an integer")
    if not 1 <= budget <= MAX_PROCESS_WORKERS:
        raise ValueError("G43 cpu_budget must be in the closed interval [1, 6]")
    workers = (
        min(DEFAULT_PROCESS_WORKERS, budget)
        if process_workers is None
        else process_workers
    )
    if isinstance(workers, bool) or not isinstance(workers, int):
        raise TypeError("G43 process_workers must be an integer")
    if not 1 <= workers <= MAX_PROCESS_WORKERS:
        raise ValueError("G43 process_workers must be in the closed interval [1, 6]")
    if workers > budget:
        raise ValueError("G43 process_workers cannot exceed cpu_budget")
    return {
        "cpu_budget": budget,
        "process_workers": workers,
        "supported_process_worker_ceiling": MAX_PROCESS_WORKERS,
        "fixed_at_launch": True,
        "continuous_adaptation": False,
        "worker_start_method": "spawn",
        "training_parallel_unit": "formal_replicate_only",
        "evaluation_parallel_unit": "replicate_capacity_cell",
        "deterministic_merge": "preassigned_index_not_completion_order",
        "worker_thread_controls": {
            **WORKER_THREAD_ENV,
            "torch_intraop_threads": 1,
        },
    }


def _activate_single_thread_worker() -> None:
    for name, value in WORKER_THREAD_ENV.items():
        os.environ[name] = value
    torch.set_num_threads(1)


def _configure_cpu_execution(
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    execution = _resolve_cpu_execution(cpu_budget, process_workers)
    _activate_single_thread_worker()
    return {
        **execution,
        "hardware_logical_cpu_count": max(1, os.cpu_count() or 1),
        "effective_parent_torch_intraop_threads": torch.get_num_threads(),
    }


def _cpu_configuration_from_artifact(
    value: Mapping[str, Any], *, formal: bool
) -> dict[str, object]:
    configuration = value.get("configuration")
    if not isinstance(configuration, Mapping):
        raise ValueError("G43 artifact has no configuration")
    cpu = _resolve_cpu_execution(
        configuration.get("cpu_budget"),
        configuration.get("process_workers"),
    )
    expected = _configuration(
        formal=formal,
        cpu_budget=int(cpu["cpu_budget"]),
        process_workers=int(cpu["process_workers"]),
    )
    if dict(configuration) != expected:
        raise ValueError("G43 serialized CPU/process configuration mismatch")
    return expected


def _valid_cpu_execution_record(
    value: object, configuration: Mapping[str, object]
) -> bool:
    if not isinstance(value, Mapping):
        return False
    expected = _resolve_cpu_execution(
        int(configuration["cpu_budget"]),
        int(configuration["process_workers"]),
    )
    hardware = value.get("hardware_logical_cpu_count")
    return bool(
        all(value.get(name) == expected[name] for name in expected)
        and isinstance(hardware, int)
        and not isinstance(hardware, bool)
        and hardware >= 1
        and value.get("effective_parent_torch_intraop_threads") == 1
    )


def _valid_worker_runtime(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    environment = value.get("thread_environment")
    return bool(
        isinstance(value.get("pid"), int)
        and not isinstance(value.get("pid"), bool)
        and int(value["pid"]) > 0
        and isinstance(value.get("wall_time_seconds"), (int, float))
        and not isinstance(value.get("wall_time_seconds"), bool)
        and float(value["wall_time_seconds"]) >= 0.0
        and isinstance(value.get("process_cpu_seconds"), (int, float))
        and not isinstance(value.get("process_cpu_seconds"), bool)
        and float(value["process_cpu_seconds"]) >= 0.0
        and isinstance(value.get("python_peak_traced_bytes"), int)
        and not isinstance(value.get("python_peak_traced_bytes"), bool)
        and int(value["python_peak_traced_bytes"]) >= 0
        and value.get("torch_intraop_threads") == 1
        and isinstance(environment, Mapping)
        and all(environment.get(name) == "1" for name in WORKER_THREAD_ENV)
    )


def _native_backend_identity() -> dict[str, object]:
    module = g40.toy_cpp.load_continuous_roster_toy_cpp_backend()
    return {
        "kind": "ContinuousRosterToyBatch_CPU_CPP",
        "required": True,
        "python_fallback": False,
        "module": str(module.__name__),
        "build_identity": g40.toy_cpp._build_identity(),
    }


def _worker_telemetry(
    *, started_wall: float, started_cpu: float, peak_bytes: int
) -> dict[str, object]:
    return {
        "pid": os.getpid(),
        "wall_time_seconds": time.perf_counter() - started_wall,
        "process_cpu_seconds": time.process_time() - started_cpu,
        "python_peak_traced_bytes": int(peak_bytes),
        "torch_intraop_threads": torch.get_num_threads(),
        "thread_environment": {
            name: os.environ.get(name) for name in WORKER_THREAD_ENV
        },
    }


def _run_indexed_worker_tasks(
    tasks: Sequence[Mapping[str, object]],
    worker: Any,
    *,
    process_workers: int,
) -> list[dict[str, object]]:
    expected_indices = list(range(len(tasks)))
    observed_indices = [task.get("index") for task in tasks]
    output_paths = [task.get("output_path") for task in tasks]
    if (
        observed_indices != expected_indices
        or any(not isinstance(path, str) or not path for path in output_paths)
        or len(set(output_paths)) != len(output_paths)
    ):
        raise ValueError("G43 worker task index/output inventory mismatch")
    if not 1 <= process_workers <= MAX_PROCESS_WORKERS:
        raise ValueError("G43 worker pool size is outside [1, 6]")
    if process_workers == 1 or len(tasks) <= 1:
        results = [worker(dict(task)) for task in tasks]
    else:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=min(process_workers, len(tasks)),
            mp_context=context,
            initializer=_activate_single_thread_worker,
        ) as executor:
            futures = [executor.submit(worker, dict(task)) for task in tasks]
            results = [future.result() for future in futures]
    if len(results) != len(tasks):
        raise RuntimeError("G43 worker result count mismatch")
    validated: list[dict[str, object]] = []
    seen: set[int] = set()
    for expected_index, (task, result) in enumerate(zip(tasks, results)):
        if not isinstance(result, Mapping):
            raise RuntimeError("G43 worker returned a non-mapping result")
        index = result.get("index")
        path = result.get("output_path")
        if (
            index != expected_index
            or index in seen
            or path != task["output_path"]
            or not Path(str(path)).is_file()
            or result.get("output_digest") != _artifact_digest(Path(str(path)))
        ):
            raise RuntimeError("G43 worker result index/output mismatch")
        seen.add(expected_index)
        validated.append(dict(result))
    if seen != set(expected_indices):
        raise RuntimeError("G43 worker result inventory incomplete")
    return validated


def _benchmark_outcome_payload(
    outcomes: Sequence[roster_env.CapacityRosterOutcome],
) -> list[dict[str, object]]:
    return [
        {
            "utility": row.utility,
            "minimum_step_utility": row.minimum_step_utility,
            "segment_utilities": list(row.segment_utilities),
            "roster_sizes": list(row.roster_sizes),
            "reward_trace": list(row.reward_trace),
        }
        for row in outcomes
    ]


def _cpu_parallel_benchmark_worker(
    task: Mapping[str, object],
) -> dict[str, object]:
    """Run one conclusion-free native toy slice for process-pool measurement."""

    _activate_single_thread_worker()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    tracemalloc.start()
    index = int(task["index"])
    batch_size = int(task["batch_size"])
    repeats = int(task["repeats"])
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G43 benchmark worker output path is not fresh")
    ledgers = tuple(
        roster_env.make_ledger(
            index * batch_size + episode,
            master_seed=91_043_000,
            profile=roster_env.TRAIN_PROFILES[(index + episode) % 3],
        )
        for episode in range(batch_size)
    )
    actions = np.zeros(
        (batch_size, 8, roster_env.ACTION_DIM), dtype=np.float32
    )
    semantic_rows: list[list[dict[str, object]]] = []
    for _repeat in range(repeats):
        envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
        batch = g40.toy_cpp.ContinuousRosterToyBatch(envs)
        for _time in range(roster_env.HORIZON):
            views = batch.observe_six()
            batch.advance(views, actions)
        semantic_rows.append(
            _benchmark_outcome_payload(tuple(env.outcome() for env in envs))
        )
    semantic_digest = hashlib.sha256(
        json.dumps(
            semantic_rows,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    payload = {
        "index": index,
        "semantic_digest": semantic_digest,
        "worker_runtime": _worker_telemetry(
            started_wall=started_wall,
            started_cpu=started_cpu,
            peak_bytes=peak_bytes,
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, payload)
    return {
        "index": index,
        "output_path": str(output_path),
        "output_digest": _artifact_digest(output_path),
    }


def benchmark_cpu_process_parallelism(
    *,
    benchmark_root: Path,
    worker_counts: Sequence[int] = (1, 2, 3, 4, 6),
    task_count: int = 6,
    batch_size: int = 8,
    repeats: int = 2,
) -> dict[str, object]:
    """Benchmark fixed process counts without training or result selection."""

    counts = tuple(worker_counts)
    if (
        not counts
        or len(set(counts)) != len(counts)
        or any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= MAX_PROCESS_WORKERS
            for value in counts
        )
        or isinstance(task_count, bool)
        or not isinstance(task_count, int)
        or task_count <= 0
        or isinstance(batch_size, bool)
        or not isinstance(batch_size, int)
        or batch_size <= 0
        or isinstance(repeats, bool)
        or not isinstance(repeats, int)
        or repeats <= 0
    ):
        raise ValueError("G43 CPU benchmark inventory is invalid")
    root = Path(benchmark_root).resolve()
    if root.exists():
        raise ValueError("G43 CPU benchmark root must be fresh")
    root.mkdir(parents=True)
    _configure_cpu_execution(1, 1)
    backend = _native_backend_identity()
    baseline: list[str] | None = None
    matrix: list[dict[str, object]] = []
    for workers in counts:
        execution = _configure_cpu_execution(workers, workers)
        tasks = [
            {
                "index": index,
                "batch_size": batch_size,
                "repeats": repeats,
                "output_path": str(
                    root
                    / ".worker_transport"
                    / f"workers_{workers}"
                    / f"task_{index}"
                    / "result.json"
                ),
            }
            for index in range(task_count)
        ]
        started = time.perf_counter()
        results = _run_indexed_worker_tasks(
            tasks,
            _cpu_parallel_benchmark_worker,
            process_workers=workers,
        )
        wall_seconds = time.perf_counter() - started
        semantic_digests: list[str] = []
        worker_runtime: list[dict[str, object]] = []
        for index, result in enumerate(results):
            path = Path(str(result["output_path"]))
            payload = _read_json(path)
            runtime = payload.get("worker_runtime")
            if (
                payload.get("index") != index
                or re.fullmatch(
                    r"[0-9a-f]{64}", str(payload.get("semantic_digest"))
                )
                is None
                or not _valid_worker_runtime(runtime)
            ):
                raise RuntimeError("G43 CPU benchmark artifact reload mismatch")
            semantic_digests.append(str(payload["semantic_digest"]))
            worker_runtime.append(dict(runtime))  # type: ignore[arg-type]
            path.unlink()
        if baseline is None:
            baseline = semantic_digests
        equivalent = semantic_digests == baseline
        if not equivalent:
            raise RuntimeError("G43 worker-count benchmark semantic mismatch")
        cpu_seconds = sum(
            float(row["process_cpu_seconds"]) for row in worker_runtime
        )
        matrix.append(
            {
                "cpu_budget": workers,
                "process_workers": workers,
                "wall_time_seconds": wall_seconds,
                "worker_process_cpu_seconds": cpu_seconds,
                "worker_cpu_to_wall_ratio": cpu_seconds / max(wall_seconds, 1e-12),
                "maximum_python_peak_traced_bytes": max(
                    int(row["python_peak_traced_bytes"])
                    for row in worker_runtime
                ),
                "observed_unique_worker_processes": len(
                    {int(row["pid"]) for row in worker_runtime}
                ),
                "worker_thread_controls_valid": all(
                    _valid_worker_runtime(row) for row in worker_runtime
                ),
                "deterministic_preassigned_merge": True,
                "artifact_reload_valid": True,
                "correctness_disposition": "BITWISE_EQUIVALENT",
                "semantic_digest": hashlib.sha256(
                    "".join(semantic_digests).encode("ascii")
                ).hexdigest(),
                "cpu_execution": execution,
            }
        )
    report = {
        "schema": "g43_fixed_cpu_process_parallelism_benchmark_v1",
        "formal": False,
        "scientific_iteration_cost": 0,
        "conclusion_bearing": False,
        "optimizer_steps": 0,
        "hypothetical_transitions": 0,
        "technical_native_transitions_per_matrix_row": (
            task_count * batch_size * repeats * roster_env.HORIZON
        ),
        "worker_counts": list(counts),
        "task_count": task_count,
        "batch_size": batch_size,
        "repeats": repeats,
        "native_backend": backend,
        "matrix": matrix,
        "all_worker_counts_bitwise_equivalent": True,
        "artifact_reload_valid": True,
        "phase_evidence": {
            "artifact_validation": "digest_bound_indexed_worker_outputs",
            "artifact_reload": "exact_json_reload_before_merge",
            "evaluate_entry": "ContinuousRosterToyBatch_CPU_CPP",
            "analyze_entry": "serial_reference_semantic_digest_comparison",
        },
    }
    report_path = root / "cpu_parallel_benchmark.json"
    _write_json(report_path, report)
    if _read_json(report_path) != report:
        raise RuntimeError("G43 CPU benchmark report reload mismatch")
    return report


def seed_block(replicate: int, *, formal: bool) -> dict[str, int]:
    if isinstance(replicate, bool) or not isinstance(replicate, int):
        raise TypeError("G43 replicate must be an integer")
    limit = FORMAL_REPLICATES if formal else EXERCISE_REPLICATES
    if not 0 <= replicate < limit:
        raise ValueError("G43 replicate outside registered execution support")
    offset = replicate + (0 if formal else NONFORMAL_SEED_OFFSET)
    return {name: base + offset for name, base in SEED_BASES.items()}


def bootstrap_seed(*, formal: bool) -> int:
    return BOOTSTRAP_SEED + (0 if formal else NONFORMAL_SEED_OFFSET)


def _counts(*, formal: bool) -> dict[str, int]:
    if formal:
        return {
            "replicates": FORMAL_REPLICATES,
            "branch_updates_per_arm": FORMAL_BRANCH_UPDATES,
            "num_envs": FORMAL_NUM_ENVS,
            "ppo_passes": FORMAL_PPO_PASSES,
            "evaluation_episodes_per_cell": FORMAL_EVAL_EPISODES,
            "bootstrap_resamples": FORMAL_BOOTSTRAP_REPETITIONS,
        }
    return {
        "replicates": EXERCISE_REPLICATES,
        "branch_updates_per_arm": EXERCISE_BRANCH_UPDATES,
        "num_envs": EXERCISE_NUM_ENVS,
        "ppo_passes": EXERCISE_PPO_PASSES,
        "evaluation_episodes_per_cell": EXERCISE_EVAL_EPISODES,
        "bootstrap_resamples": EXERCISE_BOOTSTRAP_REPETITIONS,
    }


def _configuration(
    *,
    formal: bool,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, object]:
    cpu = _resolve_cpu_execution(cpu_budget, process_workers)
    counts = _counts(formal=formal)
    replicates = int(counts["replicates"])
    updates = int(counts["branch_updates_per_arm"])
    envs = int(counts["num_envs"])
    passes = int(counts["ppo_passes"])
    episodes = int(counts["evaluation_episodes_per_cell"])
    cells_per_replicate = len(source.ARMS) * len(g34.CAPACITIES) * len(MODEL_CELLS)
    training = replicates * len(source.ARMS) * updates * envs * roster_env.HORIZON
    evaluation = replicates * cells_per_replicate * episodes * roster_env.HORIZON
    return {
        **counts,
        "cpu_budget": cpu["cpu_budget"],
        "process_workers": cpu["process_workers"],
        "supported_process_worker_ceiling": cpu[
            "supported_process_worker_ceiling"
        ],
        "cpu_parallelism_fixed_at_launch": True,
        "cpu_continuous_adaptation": False,
        "worker_start_method": "spawn",
        "training_parallel_unit": "formal_replicate_only",
        "evaluation_parallel_unit": "replicate_capacity_cell",
        "deterministic_worker_merge": (
            "preassigned_index_not_completion_order"
        ),
        "worker_thread_controls": cpu["worker_thread_controls"],
        "arms": list(source.ARMS),
        "accepted_anchor_replicates": (
            list(source.ACCEPTED_G40_ANCHOR_REPLICATES) if formal else [0]
        ),
        "common_anchor_training": "none_read_only_accepted_G40_anchors",
        "accepted_common_anchor_updates": g41.ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "accepted_common_anchor_optimizer_steps": g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS,
        "accepted_g40_source_commit": g41.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": (
            source.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT
        ),
        "accepted_g42_aligned_source_commit": (
            source.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT
        ),
        "accepted_g42_alignment_stage_commit": (
            source.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT
        ),
        "aligned_g43_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "horizon": roster_env.HORIZON,
        "stored_training_observation_dim": 6,
        "actor_width": g40.g39.HIDDEN_DIM,
        "learning_rate": g40.LEARNING_RATE,
        "optimizer": "Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)",
        "gradient_clipping": "none",
        "minibatches": "none",
        "actor_head_optimizer": "native_six_actor|log_std|shared_two_output_baseline",
        "standalone_slow_critic": "absent",
        "optimizer_steps_per_ppo_pass_per_arm": 1,
        "checkpoint_selection": "final_only",
        "episode_exclusions": "none",
        "cells_per_arm_capacity": len(MODEL_CELLS),
        "cells_per_replicate": cells_per_replicate,
        "total_cells": replicates * cells_per_replicate,
        "training_transitions": training,
        "evaluation_transitions": evaluation,
        "total_real_transitions": training + evaluation,
        "optimizer_steps": replicates * len(source.ARMS) * updates * passes,
        "evaluation_optimizer_steps": 0,
        "branch_update_order": list(source.ARMS),
        "order_swap_guard": "one_pre_step_disjoint_storage_commutativity_guard",
        "paired_collection_before_update": True,
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_python_fallback": False,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def source_controls() -> dict[str, object]:
    return {
        "source_id": source.SOURCE_ID,
        "parent_source_id": g42.SOURCE_ID,
        "accepted_g40_manifest": g41.ACCEPTED_G40_MANIFEST,
        "accepted_g40_source_commit": g41.ACCEPTED_G40_SOURCE_COMMIT,
        "accepted_common_anchor_updates": g41.ACCEPTED_G40_COMPLETED_ANCHOR_UPDATES,
        "accepted_common_anchor_optimizer_steps": g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g42_reference_source_commit": (
            source.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT
        ),
        "accepted_g42_aligned_source_commit": (
            source.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT
        ),
        "accepted_g42_alignment_stage_commit": (
            source.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT
        ),
        "aligned_g43_implementation_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "training_source": "G32 capacity-8 fixed paired source",
        "evaluation_source": "G34 fixed/random capacities 6|8|12",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "environment_backend_python_fallback": False,
        "horizon": roster_env.HORIZON,
        "training_capacity": roster_env.TRAIN_CAPACITY,
        "evaluation_capacities": list(g34.CAPACITIES),
        "arms": list(source.ARMS),
        "seed_bases": dict(SEED_BASES),
        "bootstrap_seed": BOOTSTRAP_SEED,
        "nonformal_seed_offset": NONFORMAL_SEED_OFFSET,
        "intrinsic_K_search": 0,
        "hypothetical_trajectory_count": 0,
        "hypothetical_transitions": 0,
        "nested_rollout": False,
        "replanning": False,
        "per_episode_complexity": "O(H)",
    }


def _expected_anchor_root() -> Path:
    return (PROJECT_ROOT / ACCEPTED_ANCHOR_ROOT_RELATIVE).resolve()


def _bind_anchor_root(root: Path | None) -> Path:
    if root is None:
        raise ValueError("G43 execution requires the accepted G40 anchor root")
    resolved = Path(root).resolve()
    if resolved != _expected_anchor_root():
        raise ValueError("G43 accepted anchor root is not the immutable registered root")
    return resolved


def _validate_anchor_manifest(root: Path) -> dict[str, str]:
    manifest_path = root / "train_manifest.json"
    manifest = _read_json(manifest_path)
    configuration = manifest.get("configuration")
    rows = manifest.get("replicate_results")
    if (
        manifest.get("schema_version") != g41.ACCEPTED_G40_SCHEMA_VERSION
        or manifest.get("algorithm") != g40.ALGORITHM_ID
        or manifest.get("source_id") != g40.SOURCE_ID
        or manifest.get("source_commit") != g41.ACCEPTED_G40_SOURCE_COMMIT
        or manifest.get("formal") is not True
        or manifest.get("authorization_token") != g41.ACCEPTED_G40_AUTHORIZATION_TOKEN
        or manifest.get("status") != "COMPLETE"
        or not isinstance(configuration, Mapping)
        or any(configuration.get(name) != value for name, value in g41.ACCEPTED_G40_CONFIGURATION_FIELDS)
        or not isinstance(rows, list)
        or len(rows) != len(source.ACCEPTED_G40_ANCHOR_REPLICATES)
    ):
        raise ValueError("G43 accepted G40 authority manifest identity mismatch")
    checkpoint_digests: dict[str, str] = {}
    for replicate in source.ACCEPTED_G40_ANCHOR_REPLICATES:
        authority = g41.accepted_g40_anchor_authority(replicate)
        try:
            row = rows[replicate]
            anchor = row["common_anchor"]
            relative = Path(str(anchor["checkpoint"]))
            expected_name = Path(authority.checkpoint_reference).name
            if (
                row["replicate"] != replicate
                or anchor["state_digest"] != authority.complete_state_digest
                or anchor["optimizer_steps"] != g41.ACCEPTED_G40_ANCHOR_OPTIMIZER_STEPS
                or relative.name != expected_name
            ):
                raise ValueError("G43 accepted G40 anchor row mismatch")
            checkpoint_path = root / "checkpoints" / expected_name
            checkpoint_digests[str(replicate)] = _artifact_digest(checkpoint_path)
        except (KeyError, OSError, TypeError, ValueError) as error:
            raise ValueError(f"G43 accepted anchor {replicate} invalid: {error}") from error
    return {
        "manifest": _artifact_digest(manifest_path),
        **{f"checkpoint_{key}": value for key, value in checkpoint_digests.items()},
    }


def _load_accepted_anchor(root: Path, replicate: int) -> g40.G40NativeSixPolicy:
    authority = g41.accepted_g40_anchor_authority(replicate)
    path = root / "checkpoints" / Path(authority.checkpoint_reference).name
    payload = torch.load(path, map_location="cpu", weights_only=False)
    return g41.load_accepted_g40_anchor_checkpoint(
        payload, accepted_anchor_replicate=replicate
    )


def _balanced_assignments(
    categories: Sequence[object], *, replicate: int, capacity: int,
    process_seed: int, stream: int, count: int,
) -> tuple[object, ...]:
    if len(categories) != 3 or count not in (6, 48) or count % 3:
        raise ValueError("G43 evaluation balance requires 3 categories and 6 or 48 rows")
    order = sorted(
        range(count),
        key=lambda episode: (
            int(g40.g35._process_rng(process_seed, capacity, episode, stream).integers(0, 2**63)),
            episode,
        ),
    )
    assigned: list[object | None] = [None] * count
    width = count // 3
    for category_index, category in enumerate(categories):
        for episode in order[category_index * width : (category_index + 1) * width]:
            assigned[episode] = category
    if any(row is None for row in assigned):
        raise RuntimeError("G43 balanced assignment did not close")
    return tuple(assigned)  # type: ignore[return-value]


def _source_inventory(
    *, replicate: int, capacity: int, episode_count: int, formal: bool
) -> tuple[tuple[g34.RandomProcessLedger, ...], dict[str, object]]:
    if capacity not in g34.CAPACITIES or episode_count not in (6, 48):
        raise ValueError("G43 evaluation source request is outside frozen support")
    seeds = seed_block(replicate, formal=formal)
    times = g40.g35._time_assignments(
        capacity=capacity, process_seed=seeds["evaluation_process"]
    )[:episode_count]
    orders = _balanced_assignments(
        g34.EVENT_ORDERS,
        replicate=replicate,
        capacity=capacity,
        process_seed=seeds["evaluation_process"],
        stream=1,
        count=episode_count,
    )
    if capacity == 6:
        profiles: Sequence[object] = (roster_env.SMALL_CAPACITY_6,) * episode_count
    elif capacity == 12:
        profiles = (roster_env.LARGE_CAPACITY_12,) * episode_count
    else:
        profiles = _balanced_assignments(
            roster_env.TRAIN_PROFILES,
            replicate=replicate,
            capacity=capacity,
            process_seed=seeds["evaluation_process"],
            stream=2,
            count=episode_count,
        )
    processes: list[g34.RandomProcessLedger] = []
    for local_episode in range(episode_count):
        base = roster_env.make_ledger(
            g34.episode_address(capacity, local_episode),
            master_seed=seeds["evaluation_ledger"],
            profile=profiles[local_episode],  # type: ignore[arg-type]
        )
        expected, trajectory = g34._expected_roster_schedule(
            base, times[local_episode], orders[local_episode]  # type: ignore[arg-type]
        )
        row = g34.RandomProcessLedger(
            base=base,
            local_episode_id=local_episode,
            event_times=times[local_episode],
            event_order=orders[local_episode],  # type: ignore[arg-type]
            expected_roster_sizes=expected,
            count_trajectory=trajectory,
        )
        row.validate()
        processes.append(row)
    if len({row.signature for row in processes}) != episode_count:
        raise ValueError("G43 process signatures are not unique")
    inventory = {
        "replicate": replicate,
        "capacity": capacity,
        "seeds": seeds,
        "order_counts": {
            "LRJT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[0]) for row in processes),
            "LJRT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[1]) for row in processes),
            "JLRT": sum(tuple(row.event_order) == tuple(g34.EVENT_ORDERS[2]) for row in processes),
        },
        "profile_counts": {
            profile.name: sum(row.profile.name == profile.name for row in processes)
            for profile in roster_env.TRAIN_PROFILES
        } if capacity == 8 else None,
        "processes": [
            {
                "local_episode_id": row.local_episode_id,
                "episode_id": row.episode_id,
                "profile": row.profile.name,
                "event_times": list(row.event_times),
                "event_order": list(row.event_order),
                "count_trajectory": list(row.count_trajectory),
                "random_expected_roster_sizes": list(row.expected_roster_sizes),
                "fixed_expected_roster_sizes": list(row.base.expected_roster_sizes),
                "signature": repr(row.signature),
            }
            for row in processes
        ],
    }
    expected_per_category = episode_count // 3
    if set(inventory["order_counts"].values()) != {expected_per_category}:  # type: ignore[union-attr]
        raise RuntimeError("G43 event-order inventory is not exactly balanced")
    if capacity == 8 and set(inventory["profile_counts"].values()) != {expected_per_category}:  # type: ignore[union-attr]
        raise RuntimeError("G43 capacity-8 profile inventory is not exactly balanced")
    return tuple(processes), inventory


def _optimizer_step_values(
    optimizer: torch.optim.Optimizer,
    model: g41.G41NoSlowProjection,
) -> tuple[float, ...]:
    return tuple(
        source._optimizer_step_value(optimizer, parameter)
        for parameter in model.actor_credit_parameters()
    )


def _continuation_audit(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    *,
    update_index: int,
) -> dict[str, object]:
    if isinstance(update_index, bool) or not isinstance(update_index, int) or update_index < 0:
        raise ValueError("G43 update index must be a nonnegative integer")
    if update_index == 0:
        return source.branch_boundary_audit(models, optimizers)
    inventory_valid = tuple(models) == source.ARMS and tuple(optimizers) == source.ARMS
    expected_steps = float(update_index * source.PPO_PASSES)
    authorities = [
        model.accepted_g40_anchor_authority for model in models.values()
    ] if inventory_valid else []
    authority_valid = bool(
        authorities
        and all(
            authority == authorities[0]
            and authority == g41.accepted_g40_anchor_authority(authority.replicate)
            for authority in authorities
        )
    )
    no_slow = bool(inventory_valid and all(not hasattr(model, "slow_critic") for model in models.values()))
    phases_valid = bool(inventory_valid and all(model.phase == "credit_branch" for model in models.values()))
    optimizer_inventory = bool(
        inventory_valid
        and all(
            isinstance(optimizers[arm], torch.optim.Adam)
            and source._optimizer_owns_actor_head(optimizers[arm], models[arm])
            for arm in source.ARMS
        )
    )
    step_state_valid = bool(
        optimizer_inventory
        and all(
            values
            and all(value == expected_steps for value in values)
            for values in (
                _optimizer_step_values(optimizers[arm], models[arm])
                for arm in source.ARMS
            )
        )
    )
    optimizer_storage_separate = bool(
        inventory_valid
        and id(optimizers[source.DBNORM_ARM].state)
        != id(optimizers[source.MEAN_ARM].state)
    )
    passed = bool(
        inventory_valid
        and authority_valid
        and no_slow
        and phases_valid
        and optimizer_inventory
        and step_state_valid
        and optimizer_storage_separate
    )
    authority_identity = (
        g41.accepted_g40_anchor_identity(authorities[0].replicate)
        if authority_valid
        else None
    )
    return {
        "passed": passed,
        "continuation": True,
        "update_index": update_index,
        "inventory_valid": inventory_valid,
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "accepted_g40_anchor_authority": authority_identity,
        "authority_valid": authority_valid,
        "standalone_slow_absent": no_slow,
        "branch_phases_valid": phases_valid,
        "optimizer_parameter_order_equal": optimizer_inventory,
        "optimizer_expected_step_before": expected_steps,
        "optimizer_step_state_valid": step_state_valid,
        "optimizer_states_separate": optimizer_storage_separate,
    }


def _paired_source_audit(
    trajectories: Mapping[str, g40.AnchoredRosterTrajectory],
    *,
    update_index: int,
    ledger_seed: int,
    action_seed: int,
) -> dict[str, object]:
    if tuple(trajectories) != source.ARMS:
        return {"passed": False, "inventory_valid": False}
    left, right = (trajectories[arm] for arm in source.ARMS)
    def ledger_key(ledger: roster_env.CapacityRosterLedger) -> tuple[object, ...]:
        return (
            ledger.episode_id,
            ledger.profile,
            ledger.initial_keys,
            ledger.temporarily_absent,
            ledger.fresh_join,
            ledger.terminal_leave,
            ledger.capabilities.tobytes(),
            ledger.load.tobytes(),
            ledger.target_mix.tobytes(),
            ledger.presentation_priority.tobytes(),
            ledger.expected_roster_sizes,
        )

    ledgers_equal = tuple(ledger_key(ledger) for ledger in left.ledgers) == tuple(
        ledger_key(ledger) for ledger in right.ledgers
    )
    source_tensors_equal = all(
        torch.equal(getattr(left, name), getattr(right, name))
        for name in ("observations", "active_mask", "critic_states")
    )
    lifecycle_equal = tuple(outcome.roster_sizes for outcome in left.outcomes) == tuple(
        outcome.roster_sizes for outcome in right.outcomes
    )
    initial_exact = (
        g40.branch_trajectory_match(left, right)
        if update_index == 0
        else None
    )
    return {
        "passed": bool(
            ledgers_equal
            and source_tensors_equal
            and lifecycle_equal
            and (initial_exact is None or initial_exact["passed"] is True)
        ),
        "inventory_valid": True,
        "update_index": update_index,
        "ledger_signatures_equal": ledgers_equal,
        "source_observation_mask_critic_tensors_equal": source_tensors_equal,
        "roster_lifecycle_equal": lifecycle_equal,
        "initial_complete_trajectory_equal": initial_exact,
        "ledger_seed": ledger_seed,
        "action_seed": action_seed,
        "member_owned_action_stream_seed_equal": True,
    }


def _collect_trajectory(
    model: g41.G41NoSlowProjection,
    *,
    episode_ids: Sequence[int],
    ledger_seed: int,
    action_seed: int,
) -> g40.AnchoredRosterTrajectory:
    """Collect the accepted no-slow policy through the required C++ toy batch."""

    ids = tuple(int(value) for value in episode_ids)
    profiles = tuple(roster_env.TRAIN_PROFILES)
    if len(ids) != 8 or model.member_capacity != roster_env.TRAIN_CAPACITY:
        raise ValueError("G43 branch collection requires exactly 8 capacity-8 episodes")
    ledgers = tuple(
        roster_env.make_ledger(
            episode,
            master_seed=int(ledger_seed),
            profile=profiles[episode % len(profiles)],
        )
        for episode in ids
    )
    envs = tuple(roster_env.RuntimeCapacityRosterEnv(row) for row in ledgers)
    env_batch = g40.toy_cpp.ContinuousRosterToyBatch(envs)
    noise = roster_env.make_action_noise(
        ids, action_seed=int(action_seed), member_capacity=roster_env.TRAIN_CAPACITY
    )
    hidden = torch.zeros((len(ids), roster_env.TRAIN_CAPACITY, model.hidden_dim))
    shapes = {
        "observations": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY, 6),
        "active_mask": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY),
        "critic_states": (roster_env.HORIZON, len(ids), roster_env.CRITIC_STATE_DIM),
        "actions": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY, roster_env.ACTION_DIM),
        "pre_tanh_actions": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY, roster_env.ACTION_DIM),
        "old_log_probs": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY),
        "old_values": (roster_env.HORIZON, len(ids)),
        "rewards": (roster_env.HORIZON, len(ids)),
        "hidden_before": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY, model.hidden_dim),
        "hidden_after": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY, model.hidden_dim),
        "prefix_action_sums": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY, roster_env.ACTION_DIM),
        "terminal_hidden_reset_mask": (roster_env.HORIZON, len(ids), roster_env.TRAIN_CAPACITY),
    }
    rows = {
        name: torch.empty(
            shape,
            dtype=(
                torch.bool
                if name in ("active_mask", "terminal_hidden_reset_mask")
                else torch.float32
            ),
        )
        for name, shape in shapes.items()
    }
    model.eval()
    with torch.no_grad():
        for step in range(roster_env.HORIZON):
            views = env_batch.observe_six()
            terminal_reset = torch.zeros(
                (len(ids), roster_env.TRAIN_CAPACITY), dtype=torch.bool
            )
            for batch_index, view in enumerate(views):
                if view.membership_change.terminally_left:
                    terminal_reset[
                        batch_index,
                        list(view.membership_change.terminally_left),
                    ] = True
            g32._delete_terminal_hidden(hidden, views)
            observations = torch.as_tensor(
                np.stack([row.observations for row in views])
            )
            active = torch.as_tensor(np.stack([row.active_mask for row in views]))
            critic = torch.as_tensor(np.stack([row.critic_state for row in views]))
            before = hidden.clone()
            output = g41.retained_actor_step(
                model,
                observations=observations,
                active_mask=active,
                critic_state=critic,
                hidden=hidden,
                sampling_noise=torch.as_tensor(noise[step]),
            )
            action_rows = np.ascontiguousarray(
                output.actions.detach().cpu().numpy(), dtype=np.float32
            )
            rewards = np.asarray(
                env_batch.advance(views, action_rows), dtype=np.float32
            )
            values = {
                "observations": observations,
                "active_mask": active,
                "critic_states": critic,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "old_values": torch.zeros(len(ids), dtype=torch.float32),
                "rewards": torch.as_tensor(rewards),
                "hidden_before": before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
                "terminal_hidden_reset_mask": terminal_reset,
            }
            for name, value in values.items():
                rows[name][step].copy_(value.detach().cpu())
            hidden = output.next_hidden
        immediate, successor = model.baseline_values(rows["critic_states"])
    return g40.AnchoredRosterTrajectory(
        **rows,
        old_immediate_baselines=immediate.detach().cpu(),
        old_successor_baselines=successor.detach().cpu(),
        outcomes=tuple(env.outcome() for env in envs),
        ledgers=ledgers,
    )


def _apply_matched_update(
    models: Mapping[str, g41.G41NoSlowProjection],
    optimizers: Mapping[str, torch.optim.Optimizer],
    trajectories: Mapping[str, g40.AnchoredRosterTrajectory],
    *,
    update_index: int,
    ledger_seed: int,
    action_seed: int,
) -> dict[str, object]:
    """Run the accepted G43 paired kernel with persistent arm-owned Adam state."""

    boundary = _continuation_audit(models, optimizers, update_index=update_index)
    if boundary.get("passed") is not True:
        raise ValueError("G43 branch/continuation gate failed before optimizer step")
    if tuple(trajectories) != source.ARMS or any(
        trajectory.rewards.numel() != source.MAX_CONFORMANCE_TRANSITIONS
        for trajectory in trajectories.values()
    ):
        raise ValueError("G43 update requires two paired 8x48 real trajectories")
    paired_source = _paired_source_audit(
        trajectories,
        update_index=update_index,
        ledger_seed=ledger_seed,
        action_seed=action_seed,
    )
    if paired_source["passed"] is not True:
        raise ValueError("G43 paired source/RNG gate failed before optimizer step")

    record = source.optimize_norm_schedule_update(
        models,
        optimizers,
        trajectories,
        update_index=update_index,
    )
    record["paired_source_audit"] = paired_source
    record["branch_ledger_seed"] = ledger_seed
    record["branch_action_seed"] = action_seed
    if not source._update_evidence_valid(record):
        raise RuntimeError("G43 repeated update evidence failed validation")
    return record


def _checkpoint_reference(replicate: int, arm: str) -> str:
    if arm not in source.ARMS:
        raise ValueError("G43 checkpoint arm is not registered")
    safe_arm = arm.lower()
    return f"checkpoints/replicate_{replicate}_{safe_arm}_final.pt"


def _save_checkpoint(
    path: Path,
    *,
    source_commit: str,
    aligned_source_commit: str | None,
    formal: bool,
    replicate: int,
    arm: str,
    configuration: Mapping[str, object],
    seeds: Mapping[str, int],
    model: g41.G41NoSlowProjection,
    final_update_record: Mapping[str, object],
    conclusion_evidence: Mapping[str, object],
) -> dict[str, object]:
    certificate = source.build_final_checkpoint(
        arm,
        model,
        final_update_record,
        conclusion_evidence,
        formal=formal,
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": source_commit,
        "aligned_source_commit": aligned_source_commit,
        "formal": formal,
        "replicate": replicate,
        "arm": arm,
        "kind": "final_only",
        "configuration": dict(configuration),
        "seeds": dict(seeds),
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(replicate),
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
        "actor_head_optimizer_steps": (
            int(configuration["branch_updates_per_arm"])
            * int(configuration["ppo_passes"])
        ),
        "conclusion_evidence": dict(conclusion_evidence),
        "source_final_checkpoint_certificate": certificate,
        "model_state": certificate["model_state"],
        "model_state_digest": certificate["model_state_digest"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return payload


def _finite_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise ValueError(f"G43 {name} timing invalid")
    return float(value)


def _preflight_digests(root: Path) -> dict[str, str]:
    return {
        "training": _artifact_digest(root / "train_manifest.json"),
        "evaluation": _artifact_digest(root / "evaluation_manifest.json"),
        "analysis": _artifact_digest(root / "analysis_result.json"),
    }


def _validate_formal_preflight(
    preflight_root: Path | None,
    *,
    source_commit: str,
    alignment_disposition: str | None,
    aligned_source_commit: str | None,
    alignment_stage_commit: str | None,
    accepted_anchor_root: Path,
) -> dict[str, str]:
    if ALIGNED_IMPLEMENTATION_COMMIT is None or ALIGNMENT_STAGE_COMMIT is None:
        raise ValueError(
            "formal G43 execution requires an independently archived ALIGNED source"
        )
    if preflight_root is None:
        raise ValueError("formal G43 execution requires a bounded preflight root")
    if (
        alignment_disposition != "ALIGNED"
        or aligned_source_commit != ALIGNED_IMPLEMENTATION_COMMIT
        or alignment_stage_commit != ALIGNMENT_STAGE_COMMIT
    ):
        raise ValueError("formal G43 execution requires the registered ALIGNED source")
    root = Path(preflight_root).resolve()
    training = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    errors = _evaluation_errors(root, training, evaluation)
    if errors:
        raise ValueError("G43 formal preflight artifacts invalid: " + " | ".join(errors))
    train_seconds = _finite_seconds(training.get("stage_wall_time_seconds"), "preflight train")
    eval_seconds = _finite_seconds(evaluation.get("stage_wall_time_seconds"), "preflight evaluate")
    analyze_seconds = _finite_seconds(analysis.get("stage_wall_time_seconds"), "preflight analyze")
    total_seconds = train_seconds + eval_seconds + analyze_seconds
    if (
        training.get("formal") is not False
        or evaluation.get("formal") is not False
        or analysis.get("formal") is not False
        or training.get("source_commit") != source_commit
        or evaluation.get("source_commit") != source_commit
        or analysis.get("source_commit") != source_commit
        or training.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or evaluation.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or analysis.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or training.get("accepted_anchor_root") != str(accepted_anchor_root)
        or training.get("configuration") != _configuration(formal=False)
        or evaluation.get("configuration") != _configuration(formal=False)
        or analysis.get("algorithm") != ALGORITHM_ID
        or analysis.get("source_id") != source.SOURCE_ID
        or analysis.get("branch") != NONFORMAL_BRANCH
        or analysis.get("operational_valid") is not True
        or analysis.get("operational_errors") != []
        or analysis.get("training_manifest_digest")
        != _artifact_digest(root / "train_manifest.json")
        or analysis.get("evaluation_manifest_digest")
        != _artifact_digest(root / "evaluation_manifest.json")
        or analysis.get("formal_projection_seconds") is not None
        or analysis.get("formal_projection_executable") is not None
        or total_seconds > NONFORMAL_WALL_CLOCK_CAP_SECONDS
    ):
        raise ValueError("G43 formal preflight is not valid for the aligned source")
    return _preflight_digests(root)


def _train_replicate(
    *,
    formal: bool,
    replicate: int,
    configuration: Mapping[str, object],
    accepted_anchor_root: Path,
) -> dict[str, Any]:
    seeds = seed_block(replicate, formal=formal)
    configure_runtime(seeds["branch_gradient_probe"])
    anchor = _load_accepted_anchor(accepted_anchor_root, replicate)
    anchor_digest = g41._state_digest(anchor.state_dict())
    models = source.project_g43_arms(
        anchor, accepted_anchor_replicate=replicate
    )
    for model in models.values():
        model.begin_credit_branch_phase()
    initial_actor = {
        arm: g40.state_bytes(model.policy) for arm, model in models.items()
    }
    initial_baseline = {
        arm: g40.state_bytes(model.credit_baselines)
        for arm, model in models.items()
    }
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = source.branch_boundary_audit(models, optimizers)
    if boundary["passed"] is not True:
        raise RuntimeError("G43 branch boundary failed before the first update")
    records: list[dict[str, object]] = []
    lifecycle = {arm: True for arm in source.ARMS}
    for update_index in range(int(configuration["branch_updates_per_arm"])):
        first = update_index * int(configuration["num_envs"])
        episode_ids = tuple(
            range(first, first + int(configuration["num_envs"]))
        )
        ledger_seed = (
            seeds["branch_gradient_probe"]
            if update_index == 0
            else seeds["branch_ledger"]
        )
        action_seed = (
            seeds["branch_gradient_probe"]
            if update_index == 0
            else seeds["branch_action"]
        )
        trajectories = {
            arm: _collect_trajectory(
                model,
                episode_ids=episode_ids,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
            )
            for arm, model in models.items()
        }
        for arm, trajectory in trajectories.items():
            lifecycle[arm] &= g40_runner._lifecycle_valid(trajectory)
        if not all(lifecycle.values()):
            raise RuntimeError("G43 lifecycle failed before an optimizer step")
        records.append(
            _apply_matched_update(
                models,
                optimizers,
                trajectories,
                update_index=update_index,
                ledger_seed=ledger_seed,
                action_seed=action_seed,
            )
        )
    expected_steps = (
        int(configuration["branch_updates_per_arm"])
        * int(configuration["ppo_passes"])
    )
    actor_departure = {
        arm: g40.state_bytes(model.policy) != initial_actor[arm]
        for arm, model in models.items()
    }
    baseline_departure = {
        arm: g40.state_bytes(model.credit_baselines) != initial_baseline[arm]
        for arm, model in models.items()
    }
    exposure = {
        arm: min(_optimizer_step_values(optimizers[arm], models[arm]))
        for arm in source.ARMS
    }
    if (
        not all(actor_departure.values())
        or not all(baseline_departure.values())
        or any(value != float(expected_steps) for value in exposure.values())
    ):
        raise RuntimeError("G43 final treatment liveness/exposure gate failed")
    return {
        "replicate": replicate,
        "seeds": seeds,
        "accepted_anchor": g41.accepted_g40_anchor_identity(replicate),
        "accepted_anchor_state_digest": anchor_digest,
        "branch_boundary_audit": boundary,
        "paired_collection_before_update": True,
        "branch_update_order": list(source.ARMS),
        "lifecycle_contract_valid": lifecycle,
        "actor_parameter_departure": actor_departure,
        "shared_baseline_parameter_departure": baseline_departure,
        "actor_head_optimizer_steps": exposure,
        "update_records": records,
        "models": models,
    }


def _training_replicate_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    tracemalloc.start()
    index = int(task["index"])
    replicate = int(task["replicate"])
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G43 training worker output path is not fresh")
    row = _train_replicate(
        formal=bool(task["formal"]),
        replicate=replicate,
        configuration=dict(task["configuration"]),  # type: ignore[arg-type]
        accepted_anchor_root=Path(str(task["accepted_anchor_root"])),
    )
    models = row.pop("models")
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    payload = {
        "index": index,
        "replicate": replicate,
        "row": row,
        "model_states": {
            arm: {
                name: value.detach().cpu().clone()
                for name, value in models[arm].state_dict().items()
            }
            for arm in source.ARMS
        },
        "worker_runtime": _worker_telemetry(
            started_wall=started_wall,
            started_cpu=started_cpu,
            peak_bytes=peak_bytes,
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, output_path)
    return {
        "index": index,
        "output_path": str(output_path),
        "output_digest": _artifact_digest(output_path),
    }


def _consume_training_worker_result(
    result: Mapping[str, object],
    *,
    accepted_anchor_root: Path,
) -> dict[str, Any]:
    path = Path(str(result["output_path"]))
    payload = torch.load(path, map_location="cpu", weights_only=False)
    index = int(result["index"])
    if (
        not isinstance(payload, Mapping)
        or payload.get("index") != index
        or payload.get("replicate") != index
        or not isinstance(payload.get("row"), Mapping)
        or not isinstance(payload.get("model_states"), Mapping)
        or not isinstance(payload.get("worker_runtime"), Mapping)
    ):
        raise RuntimeError("G43 training worker payload identity mismatch")
    replicate = index
    anchor = _load_accepted_anchor(accepted_anchor_root, replicate)
    models = source.project_g43_arms(
        anchor, accepted_anchor_replicate=replicate
    )
    for model in models.values():
        model.begin_credit_branch_phase()
    for arm in source.ARMS:
        models[arm].load_state_dict(payload["model_states"][arm], strict=True)
    row = dict(payload["row"])
    row["models"] = models
    row["worker_execution"] = {
        "index": index,
        "replicate": replicate,
        "configured_process_workers": None,
        "output_path": str(path),
        "output_digest": result["output_digest"],
        "output_transport_consumed": True,
        "runtime": dict(payload["worker_runtime"]),
    }
    path.unlink()
    return row


def train(
    *,
    run_root: Path,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    accepted_anchor_root: Path | None,
    preflight_root: Path | None = None,
    alignment_disposition: str | None = None,
    aligned_source_commit: str | None = None,
    alignment_stage_commit: str | None = None,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("G43 training requires an integrated source commit")
    anchor_root = _bind_anchor_root(accepted_anchor_root)
    resolved_run_root = Path(run_root).resolve()
    if resolved_run_root == anchor_root or anchor_root in resolved_run_root.parents:
        raise ValueError("G43 run root cannot write inside the read-only anchor root")
    run_root = resolved_run_root
    preflight_digests: dict[str, str] | None = None
    if formal:
        if authorization_token != AUTHORIZATION_TOKEN:
            raise ValueError("G43 formal authorization token mismatch")
        preflight_digests = _validate_formal_preflight(
            preflight_root,
            source_commit=source_commit,
            alignment_disposition=alignment_disposition,
            aligned_source_commit=aligned_source_commit,
            alignment_stage_commit=alignment_stage_commit,
            accepted_anchor_root=anchor_root,
        )
    elif any(
        value is not None
        for value in (
            authorization_token,
            preflight_root,
            alignment_disposition,
            aligned_source_commit,
            alignment_stage_commit,
        )
    ):
        raise ValueError("G43 nonformal training cannot carry formal authority")
    started = time.perf_counter()
    cpu_execution = _configure_cpu_execution(cpu_budget, process_workers)
    configuration = _configuration(
        formal=formal,
        cpu_budget=int(cpu_execution["cpu_budget"]),
        process_workers=int(cpu_execution["process_workers"]),
    )
    configure_runtime(bootstrap_seed(formal=formal))
    native_backend = _native_backend_identity()
    anchor_digests = _validate_anchor_manifest(anchor_root)
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "checkpoints").mkdir(exist_ok=True)
    training_tasks = [
        {
            "index": replicate,
            "replicate": replicate,
            "formal": formal,
            "configuration": configuration,
            "accepted_anchor_root": str(anchor_root),
            "output_path": str(
                run_root
                / ".worker_transport"
                / "train"
                / f"replicate_{replicate}"
                / "result.pt"
            ),
        }
        for replicate in range(int(configuration["replicates"]))
    ]
    training_results = _run_indexed_worker_tasks(
        training_tasks,
        _training_replicate_worker,
        process_workers=(
            int(configuration["process_workers"]) if formal else 1
        ),
    )
    internal_rows = [
        _consume_training_worker_result(
            result, accepted_anchor_root=anchor_root
        )
        for result in training_results
    ]
    for row in internal_rows:
        row["worker_execution"]["configured_process_workers"] = int(
            configuration["process_workers"]
        )
    update_records = [
        record
        for row in internal_rows
        for record in row["update_records"]
    ]
    conclusion_evidence = source.build_conclusion_evidence(
        update_records, formal=formal
    )
    if not source.validate_conclusion_evidence(conclusion_evidence):
        raise RuntimeError("G43 norm-schedule treatment did not activate in every replicate")
    rows: list[dict[str, Any]] = []
    for internal in internal_rows:
        replicate = int(internal["replicate"])
        models = internal.pop("models")
        arms: dict[str, dict[str, object]] = {}
        for arm in source.ARMS:
            reference = _checkpoint_reference(replicate, arm)
            payload = _save_checkpoint(
                run_root / reference,
                source_commit=source_commit,
                aligned_source_commit=ALIGNED_IMPLEMENTATION_COMMIT,
                formal=formal,
                replicate=replicate,
                arm=arm,
                configuration=configuration,
                seeds=internal["seeds"],
                model=models[arm],
                final_update_record=internal["update_records"][-1],
                conclusion_evidence=conclusion_evidence,
            )
            arms[arm] = {
                "final_checkpoint": reference,
                "final_checkpoint_file_digest": _artifact_digest(run_root / reference),
                "final_state_digest": payload["model_state_digest"],
                "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
                "actor_head_optimizer_steps": payload["actor_head_optimizer_steps"],
                "actor_parameter_departure": internal["actor_parameter_departure"][arm],
                "shared_baseline_parameter_departure": internal["shared_baseline_parameter_departure"][arm],
            }
        internal["arms"] = arms
        rows.append(internal)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": source_commit,
        "authorization_token": authorization_token,
        "alignment_audit_id": ALIGNMENT_AUDIT_ID if formal else None,
        "alignment_disposition": alignment_disposition,
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": alignment_stage_commit,
        "preflight_root": (
            str(Path(preflight_root).resolve()) if preflight_root is not None else None
        ),
        "preflight_artifact_digests": preflight_digests,
        "accepted_anchor_root": str(anchor_root),
        "accepted_anchor_root_mode": "read_only_input_no_writes",
        "accepted_anchor_artifact_digests": anchor_digests,
        "runtime": _runtime_identity(),
        "cpu_execution": cpu_execution,
        "native_backend": native_backend,
        "configuration": configuration,
        "source_controls": source_controls(),
        "conclusion_evidence": conclusion_evidence,
        "stage_wall_time_seconds": time.perf_counter() - started,
        "replicate_results": rows,
    }
    _write_json(run_root / "train_manifest.json", manifest)
    return manifest


def _cell_contract(name: str) -> dict[str, object]:
    contracts = {
        FINAL_FIXED_DET: {"process": "fixed", "deterministic": True},
        FINAL_FIXED_STOCH: {"process": "fixed", "deterministic": False},
        FINAL_RANDOM_DET: {"process": "random", "deterministic": True},
        FINAL_RANDOM_STOCH: {"process": "random", "deterministic": False},
    }
    if name not in contracts:
        raise ValueError("G43 unknown evaluation cell")
    return {"checkpoint": "final", **contracts[name]}


def _load_checkpoint_payload(
    path: Path,
    *,
    training: Mapping[str, Any],
    replicate: int,
    arm: str,
) -> Mapping[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    configuration = training["configuration"]
    seeds = seed_block(replicate, formal=bool(training["formal"]))
    expected = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "source_commit": training["source_commit"],
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "formal": bool(training["formal"]),
        "replicate": replicate,
        "arm": arm,
        "kind": "final_only",
        "configuration": configuration,
        "seeds": seeds,
        "accepted_g40_anchor_authority": g41.accepted_g40_anchor_identity(replicate),
        "accepted_g41_source_commit": source.ACCEPTED_G41_SOURCE_COMMIT,
        "completed_branch_updates": int(configuration["branch_updates_per_arm"]),
        "actor_head_optimizer_steps": (
            int(configuration["branch_updates_per_arm"])
            * int(configuration["ppo_passes"])
        ),
        "conclusion_evidence": training["conclusion_evidence"],
    }
    expected_keys = {
        *expected,
        "source_final_checkpoint_certificate",
        "model_state",
        "model_state_digest",
    }
    if (
        not isinstance(payload, Mapping)
        or set(payload) != expected_keys
        or any(payload.get(name) != value for name, value in expected.items())
    ):
        raise ValueError("G43 final checkpoint identity mismatch")
    state = payload.get("model_state")
    digest = payload.get("model_state_digest")
    if (
        not isinstance(state, Mapping)
        or not all(isinstance(name, str) and isinstance(value, torch.Tensor) for name, value in state.items())
        or not isinstance(digest, str)
        or g41._state_digest(state) != digest
        or any("slow_critic" in name for name in state)
    ):
        raise ValueError("G43 final checkpoint state mismatch")
    certificate = payload.get("source_final_checkpoint_certificate")
    certificate_diagnostics = (
        certificate.get("diagnostics") if isinstance(certificate, Mapping) else None
    )
    if (
        not isinstance(certificate, Mapping)
        or certificate.get("model_state_digest") != digest
        or certificate.get("arm") != arm
        or certificate.get("formal") is not bool(training["formal"])
        or certificate.get("standalone_slow_present") is not False
        or certificate.get("actor_head_optimizer_steps") != source.PPO_PASSES
        or not isinstance(certificate_diagnostics, Mapping)
        or certificate_diagnostics.get("treatment_activation")
        != training["conclusion_evidence"]
    ):
        raise ValueError("G43 accepted-source checkpoint certificate mismatch")
    return payload


def _load_final_model(
    *,
    run_root: Path,
    training: Mapping[str, Any],
    replicate: int,
    capacity: int,
    arm: str,
) -> g41.G41NoSlowProjection:
    reference = training["replicate_results"][replicate]["arms"][arm]["final_checkpoint"]
    payload = _load_checkpoint_payload(
        run_root / reference,
        training=training,
        replicate=replicate,
        arm=arm,
    )
    anchor_root = _bind_anchor_root(Path(str(training["accepted_anchor_root"])))
    anchor = _load_accepted_anchor(anchor_root, replicate)
    if capacity != roster_env.TRAIN_CAPACITY:
        authority = g41.accepted_g40_anchor_authority(replicate)
        resized = g40.make_model(
            capacity, initialization_seed=authority.anchor_model_seed
        )
        resized.load_state_dict(anchor.state_dict(), strict=True)
        anchor = resized
    models = source.project_g43_arms(
        anchor, accepted_anchor_replicate=replicate
    )
    for model in models.values():
        model.begin_credit_branch_phase()
    model = models[arm]
    model.load_state_dict(payload["model_state"], strict=True)
    if g41._state_digest(model.state_dict()) != payload["model_state_digest"]:
        raise ValueError("G43 deployed final state digest mismatch")
    return model


def _expected_final_checkpoint_files(
    rows: Sequence[object],
) -> set[str]:
    expected_files: set[str] = set()
    for replicate, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError("G43 final checkpoint inventory mismatch")
        arms = row.get("arms")
        if not isinstance(arms, Mapping) or set(arms) != set(source.ARMS):
            raise ValueError("G43 final checkpoint inventory mismatch")
        for arm in source.ARMS:
            arm_row = arms.get(arm)
            if not isinstance(arm_row, Mapping):
                raise ValueError("G43 final checkpoint inventory mismatch")
            reference = arm_row.get("final_checkpoint")
            if reference != _checkpoint_reference(replicate, arm):
                raise ValueError("G43 final checkpoint inventory mismatch")
            expected_files.add(Path(reference).name)
    if len(expected_files) != len(rows) * len(source.ARMS):
        raise ValueError("G43 final checkpoint inventory mismatch")
    return expected_files


def _training_errors(
    run_root: Path, training: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    formal = bool(training.get("formal"))
    try:
        configuration = _cpu_configuration_from_artifact(
            training, formal=formal
        )
    except (TypeError, ValueError) as error:
        return [str(error)]
    if (
        training.get("schema_version") != SCHEMA_VERSION
        or training.get("algorithm") != ALGORITHM_ID
        or training.get("source_id") != source.SOURCE_ID
        or training.get("stage") != "train"
        or training.get("status") != "COMPLETE"
        or training.get("configuration") != configuration
        or training.get("source_controls") != source_controls()
        or training.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or re.fullmatch(r"[0-9a-f]{40}", str(training.get("source_commit"))) is None
    ):
        return ["G43 training identity mismatch"]
    if not _valid_cpu_execution_record(
        training.get("cpu_execution"), configuration
    ):
        errors.append("G43 training CPU/process execution mismatch")
    backend = training.get("native_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        errors.append("G43 native backend binding mismatch")
    try:
        anchor_root = _bind_anchor_root(Path(str(training["accepted_anchor_root"])))
        if training.get("accepted_anchor_root_mode") != "read_only_input_no_writes":
            raise ValueError("G43 accepted anchor mode mismatch")
        if _validate_anchor_manifest(anchor_root) != training.get(
            "accepted_anchor_artifact_digests"
        ):
            raise ValueError("G43 accepted anchor digest binding mismatch")
    except (KeyError, OSError, TypeError, ValueError) as error:
        errors.append(str(error))
        anchor_root = _expected_anchor_root()
    if formal:
        if (
            training.get("authorization_token") != AUTHORIZATION_TOKEN
            or training.get("alignment_audit_id") != ALIGNMENT_AUDIT_ID
            or training.get("alignment_disposition") != "ALIGNED"
            or training.get("alignment_stage_commit") != ALIGNMENT_STAGE_COMMIT
            or not isinstance(training.get("preflight_artifact_digests"), dict)
        ):
            errors.append("G43 formal authority binding mismatch")
        else:
            try:
                serialized = training.get("preflight_root")
                if not isinstance(serialized, str) or not Path(serialized).is_absolute():
                    raise ValueError("G43 formal preflight root mismatch")
                live = _validate_formal_preflight(
                    Path(serialized),
                    source_commit=str(training["source_commit"]),
                    alignment_disposition=str(training["alignment_disposition"]),
                    aligned_source_commit=str(training["aligned_source_commit"]),
                    alignment_stage_commit=str(training["alignment_stage_commit"]),
                    accepted_anchor_root=anchor_root,
                )
                if live != training.get("preflight_artifact_digests"):
                    raise ValueError("G43 formal preflight digest binding mismatch")
            except (OSError, TypeError, ValueError) as error:
                errors.append(str(error))
    elif any(
        training.get(name) is not None
        for name in (
            "authorization_token",
            "alignment_audit_id",
            "alignment_disposition",
            "alignment_stage_commit",
            "preflight_root",
            "preflight_artifact_digests",
        )
    ):
        errors.append("G43 nonformal artifact carried formal authority")
    rows = training.get("replicate_results")
    if not isinstance(rows, list) or len(rows) != int(configuration["replicates"]):
        return errors + ["G43 training replicate inventory mismatch"]
    all_update_records: list[Mapping[str, object]] = []
    update_records_complete = True
    try:
        expected_files = _expected_final_checkpoint_files(rows)
    except (TypeError, ValueError) as error:
        errors.append(str(error))
        expected_files = None
    expected_steps = (
        int(configuration["branch_updates_per_arm"])
        * int(configuration["ppo_passes"])
    )
    for replicate, row in enumerate(rows):
        try:
            records = row["update_records"]
            worker_execution = row.get("worker_execution")
            if (
                row["replicate"] != replicate
                or row["seeds"] != seed_block(replicate, formal=formal)
                or row["accepted_anchor"] != g41.accepted_g40_anchor_identity(replicate)
                or row["accepted_anchor_state_digest"]
                != g41.accepted_g40_anchor_authority(replicate).complete_state_digest
                or row["branch_boundary_audit"]["passed"] is not True
                or row["paired_collection_before_update"] is not True
                or row["branch_update_order"] != list(source.ARMS)
                or not all(row["lifecycle_contract_valid"].values())
                or not all(row["actor_parameter_departure"].values())
                or not all(row["shared_baseline_parameter_departure"].values())
                or any(float(value) != float(expected_steps) for value in row["actor_head_optimizer_steps"].values())
                or not isinstance(records, list)
                or len(records) != int(configuration["branch_updates_per_arm"])
                or not isinstance(worker_execution, Mapping)
                or worker_execution.get("index") != replicate
                or worker_execution.get("replicate") != replicate
                or worker_execution.get("configured_process_workers")
                != int(configuration["process_workers"])
                or re.fullmatch(
                    r"[0-9a-f]{64}",
                    str(worker_execution.get("output_digest")),
                )
                is None
                or not isinstance(worker_execution.get("output_path"), str)
                or worker_execution.get("output_transport_consumed") is not True
                or not _valid_worker_runtime(worker_execution.get("runtime"))
            ):
                raise ValueError("G43 replicate invariant mismatch")
            for update_index, record in enumerate(records):
                paired_source = record.get("paired_source_audit")
                expected_ledger_seed = (
                    row["seeds"]["branch_gradient_probe"]
                    if update_index == 0
                    else row["seeds"]["branch_ledger"]
                )
                expected_action_seed = (
                    row["seeds"]["branch_gradient_probe"]
                    if update_index == 0
                    else row["seeds"]["branch_action"]
                )
                if (
                    record.get("update_index") != update_index
                    or not source._update_evidence_valid(record)
                    or not isinstance(paired_source, Mapping)
                    or paired_source.get("passed") is not True
                    or paired_source.get("update_index") != update_index
                    or paired_source.get("ledger_seed") != expected_ledger_seed
                    or paired_source.get("action_seed") != expected_action_seed
                    or record.get("paired_collection_before_update") is not True
                    or record.get("branch_update_order") != list(source.ARMS)
                    or record.get("K_search") != 0
                    or record.get("hypothetical_transitions") != 0
                ):
                    raise ValueError("G43 update evidence mismatch")
                all_update_records.append(record)
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
            update_records_complete = False
        try:
            for arm in source.ARMS:
                arm_row = row["arms"][arm]
                reference = arm_row["final_checkpoint"]
                if (
                    arm_row["completed_branch_updates"]
                    != int(configuration["branch_updates_per_arm"])
                    or arm_row["actor_head_optimizer_steps"] != expected_steps
                    or arm_row["actor_parameter_departure"] is not True
                    or arm_row["shared_baseline_parameter_departure"] is not True
                    or arm_row["final_checkpoint_file_digest"]
                    != _artifact_digest(run_root / reference)
                ):
                    raise ValueError("G43 final checkpoint inventory mismatch")
                payload = _load_checkpoint_payload(
                    run_root / reference,
                    training=training,
                    replicate=replicate,
                    arm=arm,
                )
                if payload["model_state_digest"] != arm_row["final_state_digest"]:
                    raise ValueError("G43 final checkpoint digest mismatch")
        except (KeyError, OSError, TypeError, ValueError) as error:
            errors.append(str(error))
    conclusion_evidence = training.get("conclusion_evidence")
    if not source.validate_conclusion_evidence(conclusion_evidence):
        errors.append("G43 conclusion treatment-activation evidence mismatch")
    elif update_records_complete:
        expected_conclusion = source.build_conclusion_evidence(
            all_update_records, formal=formal
        )
        if expected_conclusion != conclusion_evidence:
            errors.append("G43 conclusion treatment-activation evidence mismatch")
    try:
        observed_files = {path.name for path in (run_root / "checkpoints").iterdir()}
        if expected_files is not None and observed_files != expected_files:
            errors.append("G43 checkpoint inventory is not final-only")
    except OSError as error:
        errors.append(str(error))
    return errors


class _G43RetainedEvaluationPolicy:
    """Expose only the accepted retained actor step to the generic evaluator."""

    __slots__ = ("_projection",)

    def __init__(self, projection: g41.G41NoSlowProjection) -> None:
        if projection.phase != "credit_branch" or hasattr(
            projection, "slow_critic"
        ):
            raise ValueError("G43 evaluation requires the retained no-slow branch")
        self._projection = projection

    @property
    def member_capacity(self) -> int:
        return self._projection.member_capacity

    @property
    def hidden_dim(self) -> int:
        return self._projection.hidden_dim

    def eval(self) -> _G43RetainedEvaluationPolicy:
        self._projection.eval()
        return self

    def forward_step(self, **arguments: Any) -> g41.G41ActorStep:
        return g41.retained_actor_step(self._projection, **arguments)


def _evaluate_cell(
    *,
    replicate: int,
    capacity: int,
    arm: str,
    name: str,
    processes: Sequence[g34.RandomProcessLedger],
    action_seed: int,
    deployed: g41.G41NoSlowProjection,
) -> dict[str, object]:
    contract = _cell_contract(name)
    before = _state_digest(deployed)
    episodes, lifecycle = g40.evaluate_model(
        _G43RetainedEvaluationPolicy(deployed),  # type: ignore[arg-type]
        processes=processes,
        action_seed=action_seed,
        process_kind=str(contract["process"]),
        deterministic=bool(contract["deterministic"]),
    )
    return {
        "replicate": replicate,
        "capacity": capacity,
        "arm": arm,
        "cell": name,
        **contract,
        "optimizer_steps": 0,
        "state_before": before,
        "state_after": _state_digest(deployed),
        "lifecycle_valid": lifecycle,
        "episodes": list(episodes),
    }


def _evaluation_cell_worker(task: Mapping[str, object]) -> dict[str, object]:
    _activate_single_thread_worker()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    tracemalloc.start()
    index = int(task["index"])
    replicate = int(task["replicate"])
    capacity = int(task["capacity"])
    name = str(task["cell"])
    formal = bool(task["formal"])
    run_root = Path(str(task["run_root"]))
    output_path = Path(str(task["output_path"]))
    if output_path.exists():
        raise RuntimeError("G43 evaluation worker output path is not fresh")
    training = _read_json(run_root / "train_manifest.json")
    if training.get("configuration") != task.get("configuration"):
        raise RuntimeError("G43 evaluation worker configuration mismatch")
    processes, inventory = _source_inventory(
        replicate=replicate,
        capacity=capacity,
        episode_count=int(training["configuration"]["evaluation_episodes_per_cell"]),
        formal=formal,
    )
    seeds = seed_block(replicate, formal=formal)
    cells = []
    for arm in source.ARMS:
        deployed = _load_final_model(
            run_root=run_root,
            training=training,
            replicate=replicate,
            capacity=capacity,
            arm=arm,
        )
        cells.append(
            _evaluate_cell(
                replicate=replicate,
                capacity=capacity,
                arm=arm,
                name=name,
                processes=processes,
                action_seed=seeds["evaluation_action"],
                deployed=deployed,
            )
        )
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    payload = {
        "index": index,
        "task_identity": {
            "replicate": replicate,
            "capacity": capacity,
            "cell": name,
        },
        "direct_source_validation": g38_runner._direct_source_validation(
            processes
        ),
        "source_inventory": inventory,
        "cells": cells,
        "worker_runtime": _worker_telemetry(
            started_wall=started_wall,
            started_cpu=started_cpu,
            peak_bytes=peak_bytes,
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, payload)
    return {
        "index": index,
        "output_path": str(output_path),
        "output_digest": _artifact_digest(output_path),
    }


def _consume_evaluation_worker_results(
    results: Sequence[Mapping[str, object]],
    tasks: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], bool]:
    cells: list[dict[str, object]] = []
    inventories: dict[tuple[int, int], dict[str, object]] = {}
    worker_records: list[dict[str, object]] = []
    direct_source_valid = True
    for expected_index, (task, result) in enumerate(zip(tasks, results)):
        path = Path(str(result["output_path"]))
        payload = _read_json(path)
        expected_identity = {
            "replicate": int(task["replicate"]),
            "capacity": int(task["capacity"]),
            "cell": str(task["cell"]),
        }
        if (
            payload.get("index") != expected_index
            or payload.get("task_identity") != expected_identity
            or not isinstance(payload.get("cells"), list)
            or len(payload["cells"]) != len(source.ARMS)
            or not isinstance(payload.get("source_inventory"), Mapping)
            or not isinstance(payload.get("worker_runtime"), Mapping)
        ):
            raise RuntimeError("G43 evaluation worker payload identity mismatch")
        inventory_key = (
            expected_identity["replicate"],
            expected_identity["capacity"],
        )
        inventory = dict(payload["source_inventory"])
        if inventory_key in inventories and inventories[inventory_key] != inventory:
            raise RuntimeError("G43 duplicate evaluation inventory disagrees")
        inventories[inventory_key] = inventory
        direct_source_valid &= payload.get("direct_source_validation") is True
        cells.extend(dict(row) for row in payload["cells"])
        worker_records.append(
            {
                "index": expected_index,
                "task_identity": expected_identity,
                "configured_process_workers": int(
                    task["configured_process_workers"]
                ),
                "output_path": str(path),
                "output_digest": result["output_digest"],
                "output_transport_consumed": True,
                "runtime": dict(payload["worker_runtime"]),
            }
        )
        path.unlink()
    expected_inventory_keys = [
        (replicate, capacity)
        for replicate in range(
            1 + max(int(task["replicate"]) for task in tasks)
        )
        for capacity in g34.CAPACITIES
    ]
    if list(inventories) != expected_inventory_keys:
        raise RuntimeError("G43 evaluation inventory merge mismatch")
    arm_order = {arm: index for index, arm in enumerate(source.ARMS)}
    cell_order = {name: index for index, name in enumerate(MODEL_CELLS)}
    cells.sort(
        key=lambda row: (
            int(row["replicate"]),
            int(row["capacity"]),
            arm_order[str(row["arm"])],
            cell_order[str(row["cell"])],
        )
    )
    return cells, list(inventories.values()), worker_records, direct_source_valid


def evaluate(
    *,
    run_root: Path,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    errors = _training_errors(run_root, training)
    if errors:
        raise ValueError("G43 training artifact invalid: " + " | ".join(errors))
    formal = bool(training["formal"])
    configuration = _cpu_configuration_from_artifact(training, formal=formal)
    requested = _resolve_cpu_execution(
        int(configuration["cpu_budget"])
        if cpu_budget is None
        else cpu_budget,
        int(configuration["process_workers"])
        if process_workers is None
        else process_workers,
    )
    if (cpu_budget is not None or process_workers is not None) and (
        requested["cpu_budget"] != configuration["cpu_budget"]
        or requested["process_workers"] != configuration["process_workers"]
    ):
        raise ValueError("G43 evaluate CPU/process settings differ from training")
    cpu_execution = _configure_cpu_execution(
        int(configuration["cpu_budget"]),
        int(configuration["process_workers"]),
    )
    configure_runtime(bootstrap_seed(formal=formal))
    native_backend = _native_backend_identity()
    tasks: list[dict[str, object]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            for name in MODEL_CELLS:
                index = len(tasks)
                tasks.append(
                    {
                        "index": index,
                        "replicate": replicate,
                        "capacity": capacity,
                        "cell": name,
                        "formal": formal,
                        "configuration": configuration,
                        "configured_process_workers": int(
                            configuration["process_workers"]
                        ),
                        "run_root": str(Path(run_root).resolve()),
                        "output_path": str(
                            Path(run_root).resolve()
                            / ".worker_transport"
                            / "evaluate"
                            / f"task_{index}"
                            / "result.json"
                        ),
                    }
                )
    results = _run_indexed_worker_tasks(
        tasks,
        _evaluation_cell_worker,
        process_workers=int(configuration["process_workers"]),
    )
    cells, inventories, worker_records, direct_source_valid = (
        _consume_evaluation_worker_results(results, tasks)
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "formal": formal,
        "source_commit": training["source_commit"],
        "authorization_token": training["authorization_token"],
        "alignment_audit_id": training["alignment_audit_id"],
        "alignment_disposition": training["alignment_disposition"],
        "aligned_source_commit": training["aligned_source_commit"],
        "alignment_stage_commit": training["alignment_stage_commit"],
        "preflight_artifact_digests": training["preflight_artifact_digests"],
        "accepted_anchor_artifact_digests": training["accepted_anchor_artifact_digests"],
        "runtime": _runtime_identity(),
        "cpu_execution": cpu_execution,
        "native_backend": native_backend,
        "configuration": configuration,
        "source_controls": source_controls(),
        "conclusion_evidence": training["conclusion_evidence"],
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "stage_wall_time_seconds": time.perf_counter() - started,
        "direct_source_validation": bool(direct_source_valid),
        "source_inventory": inventories,
        "worker_execution": worker_records,
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", manifest)
    return manifest


def _evaluation_errors(
    run_root: Path,
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> list[str]:
    errors = _training_errors(run_root, training)
    formal = bool(training.get("formal"))
    try:
        configuration = _cpu_configuration_from_artifact(
            training, formal=formal
        )
    except (TypeError, ValueError) as error:
        return errors + [str(error)]
    if (
        evaluation.get("schema_version") != SCHEMA_VERSION
        or evaluation.get("algorithm") != ALGORITHM_ID
        or evaluation.get("source_id") != source.SOURCE_ID
        or evaluation.get("stage") != "evaluate"
        or evaluation.get("status") != "COMPLETE"
        or evaluation.get("formal") is not formal
        or evaluation.get("source_commit") != training.get("source_commit")
        or evaluation.get("authorization_token") != training.get("authorization_token")
        or evaluation.get("alignment_audit_id") != training.get("alignment_audit_id")
        or evaluation.get("alignment_disposition") != training.get("alignment_disposition")
        or evaluation.get("aligned_source_commit") != ALIGNED_IMPLEMENTATION_COMMIT
        or evaluation.get("alignment_stage_commit") != training.get("alignment_stage_commit")
        or evaluation.get("preflight_artifact_digests")
        != training.get("preflight_artifact_digests")
        or evaluation.get("accepted_anchor_artifact_digests")
        != training.get("accepted_anchor_artifact_digests")
        or evaluation.get("configuration") != configuration
        or evaluation.get("source_controls") != source_controls()
        or evaluation.get("conclusion_evidence") != training.get("conclusion_evidence")
        or evaluation.get("training_manifest_digest")
        != _artifact_digest(run_root / "train_manifest.json")
        or evaluation.get("direct_source_validation") is not True
    ):
        errors.append("G43 evaluation identity/source mismatch")
    if not _valid_cpu_execution_record(
        evaluation.get("cpu_execution"), configuration
    ):
        errors.append("G43 evaluation CPU/process execution mismatch")
    backend = evaluation.get("native_backend")
    if (
        not isinstance(backend, Mapping)
        or backend.get("kind") != "ContinuousRosterToyBatch_CPU_CPP"
        or backend.get("required") is not True
        or backend.get("python_fallback") is not False
    ):
        errors.append("G43 evaluation native backend mismatch")
    cells = evaluation.get("cells")
    if not isinstance(cells, list) or len(cells) != int(configuration["total_cells"]):
        return errors + ["G43 evaluation cell inventory mismatch"]
    worker_execution = evaluation.get("worker_execution")
    expected_worker_tasks = (
        int(configuration["replicates"])
        * len(g34.CAPACITIES)
        * len(MODEL_CELLS)
    )
    if not isinstance(worker_execution, list) or len(worker_execution) != expected_worker_tasks:
        errors.append("G43 evaluation worker inventory mismatch")
    else:
        observed_worker_keys: list[tuple[int, int, str]] = []
        for index, row in enumerate(worker_execution):
            identity = row.get("task_identity") if isinstance(row, Mapping) else None
            if (
                not isinstance(row, Mapping)
                or row.get("index") != index
                or not isinstance(identity, Mapping)
                or row.get("configured_process_workers")
                != int(configuration["process_workers"])
                or re.fullmatch(
                    r"[0-9a-f]{64}", str(row.get("output_digest"))
                )
                is None
                or not isinstance(row.get("output_path"), str)
                or row.get("output_transport_consumed") is not True
                or not _valid_worker_runtime(row.get("runtime"))
            ):
                errors.append("G43 evaluation worker index/runtime mismatch")
                break
            observed_worker_keys.append(
                (
                    int(identity["replicate"]),
                    int(identity["capacity"]),
                    str(identity["cell"]),
                )
            )
        expected_worker_keys = [
            (replicate, capacity, name)
            for replicate in range(int(configuration["replicates"]))
            for capacity in g34.CAPACITIES
            for name in MODEL_CELLS
        ]
        if observed_worker_keys != expected_worker_keys:
            errors.append("G43 evaluation worker task identity mismatch")
    expected_inventories: list[dict[str, object]] = []
    for replicate in range(int(configuration["replicates"])):
        for capacity in g34.CAPACITIES:
            _, inventory = _source_inventory(
                replicate=replicate,
                capacity=capacity,
                episode_count=int(configuration["evaluation_episodes_per_cell"]),
                formal=formal,
            )
            expected_inventories.append(inventory)
    if evaluation.get("source_inventory") != expected_inventories:
        errors.append("G43 source inventory mismatch")
    inventories = {
        (int(row["replicate"]), int(row["capacity"])): row["processes"]
        for row in evaluation.get("source_inventory", [])
    }
    observed: set[tuple[int, int, str, str]] = set()
    for cell in cells:
        try:
            key = (
                int(cell["replicate"]),
                int(cell["capacity"]),
                str(cell["arm"]),
                str(cell["cell"]),
            )
            if (
                key in observed
                or key[0] not in range(int(configuration["replicates"]))
                or key[1] not in g34.CAPACITIES
                or key[2] not in source.ARMS
                or key[3] not in MODEL_CELLS
            ):
                raise ValueError("G43 evaluation cell identity mismatch")
            observed.add(key)
            contract = _cell_contract(key[3])
            if any(cell.get(name) != value for name, value in contract.items()):
                raise ValueError("G43 evaluation route mismatch")
            expected_digest = training["replicate_results"][key[0]]["arms"][key[2]]["final_state_digest"]
            if (
                cell.get("optimizer_steps") != 0
                or cell.get("state_before") != cell.get("state_after")
                or cell.get("state_before") != expected_digest
                or cell.get("lifecycle_valid") is not True
            ):
                raise ValueError("G43 evaluation mutation/checkpoint mismatch")
            episodes = cell.get("episodes")
            if not isinstance(episodes, list) or len(episodes) != int(
                configuration["evaluation_episodes_per_cell"]
            ):
                raise ValueError("G43 evaluation episode inventory mismatch")
            expected_rows = inventories[(key[0], key[1])]
            roster_field = (
                "random_expected_roster_sizes"
                if contract["process"] == "random"
                else "fixed_expected_roster_sizes"
            )
            for index, episode in enumerate(episodes):
                expected = expected_rows[index]
                if (
                    episode.get("local_episode_id") != index
                    or episode.get("episode_id") != expected["episode_id"]
                    or episode.get("signature") != expected["signature"]
                    or episode.get("event_times") != expected["event_times"]
                    or episode.get("event_order") != expected["event_order"]
                    or episode.get("roster_sizes_valid") is not True
                ):
                    raise ValueError("G43 paired evaluation episode mismatch")
                trace = g39_runner.g34_runner._trace_evidence(episode)
                if (
                    trace["roster_size_trace"] != tuple(expected[roster_field])
                    or not g39_runner.g34_runner._summary_matches_trace(episode, trace)
                ):
                    raise ValueError("G43 evaluation trace mismatch")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))
    expected_keys = {
        (replicate, capacity, arm, name)
        for replicate in range(int(configuration["replicates"]))
        for capacity in g34.CAPACITIES
        for arm in source.ARMS
        for name in MODEL_CELLS
    }
    if observed != expected_keys:
        errors.append("G43 evaluation cell key set mismatch")
    return errors


def _cell_map(
    evaluation: Mapping[str, Any],
) -> dict[tuple[int, int, str, str], Mapping[str, Any]]:
    return {
        (
            int(row["replicate"]),
            int(row["capacity"]),
            str(row["arm"]),
            str(row["cell"]),
        ): row
        for row in evaluation["cells"]
    }


def _metric_arrays(
    evaluation: Mapping[str, Any], arm: str, cell: str, metric: str
) -> dict[int, np.ndarray]:
    cells = _cell_map(evaluation)
    replicates = int(evaluation["configuration"]["replicates"])
    return {
        capacity: np.asarray(
            [
                [
                    g39_runner.g34_runner._trace_evidence(episode)[metric]
                    for episode in cells[(replicate, capacity, arm, cell)]["episodes"]
                ]
                for replicate in range(replicates)
            ],
            dtype=np.float64,
        )
        for capacity in g34.CAPACITIES
    }


def _difference(
    left: Mapping[int, np.ndarray], right: Mapping[int, np.ndarray]
) -> dict[int, np.ndarray]:
    return {capacity: left[capacity] - right[capacity] for capacity in left}


def _bootstrap_plan(
    *, formal: bool, replicates: int, episodes: int, repetitions: int
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(bootstrap_seed(formal=formal))
    return (
        rng.integers(0, replicates, size=(repetitions, replicates), dtype=np.int16),
        rng.integers(
            0,
            episodes,
            size=(repetitions, replicates, len(g34.CAPACITIES), episodes),
            dtype=np.int16,
        ),
    )


def _hierarchical_ci(
    values: Mapping[int, np.ndarray],
    *,
    capacities: Sequence[int],
    plan: tuple[np.ndarray, np.ndarray],
) -> list[float]:
    return g35_runner._hierarchical_ci(values, capacities=capacities, plan=plan)


def _arm_access(
    evaluation: Mapping[str, Any], arm: str, plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    fixed = _metric_arrays(evaluation, arm, FINAL_FIXED_DET, "utility")
    fixed_stoch = _metric_arrays(evaluation, arm, FINAL_FIXED_STOCH, "utility")
    random = _metric_arrays(evaluation, arm, FINAL_RANDOM_DET, "utility")
    event = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "minimum_event_window_utility"
    )
    segment = _metric_arrays(
        evaluation, arm, FINAL_RANDOM_DET, "minimum_process_segment_utility"
    )
    random_stoch = _metric_arrays(evaluation, arm, FINAL_RANDOM_STOCH, "utility")
    process = _difference(random, fixed)
    per_capacity = lambda values: {
        capacity: _hierarchical_ci(values, capacities=(capacity,), plan=plan)
        for capacity in g34.CAPACITIES
    }
    fixed_ci, random_ci, event_ci, segment_ci, process_ci = map(
        per_capacity, (fixed, random, event, segment, process)
    )
    fixed_stoch_ci = _hierarchical_ci(
        fixed_stoch, capacities=g34.CAPACITIES, plan=plan
    )
    random_stoch_ci = _hierarchical_ci(
        random_stoch, capacities=g34.CAPACITIES, plan=plan
    )
    min_fixed = g38_runner._minimum_replicate_mean(fixed)
    min_random = g38_runner._minimum_replicate_mean(random)
    access_pass = (
        all(g38_runner._inclusive_ge(fixed_ci[c][0], UTILITY_FLOOR) for c in g34.CAPACITIES)
        and g38_runner._inclusive_ge(fixed_stoch_ci[0], STOCHASTIC_FLOOR)
        and g38_runner._inclusive_ge(min_fixed, MINIMUM_REPLICATE_FLOOR)
        and all(g38_runner._inclusive_ge(random_ci[c][0], UTILITY_FLOOR) for c in g34.CAPACITIES)
        and all(g38_runner._inclusive_ge(event_ci[c][0], EVENT_FLOOR) for c in g34.CAPACITIES)
        and all(g38_runner._inclusive_ge(segment_ci[c][0], SEGMENT_FLOOR) for c in g34.CAPACITIES)
        and all(g38_runner._inclusive_ge(process_ci[c][0], PROCESS_MARGIN) for c in g34.CAPACITIES)
        and g38_runner._inclusive_ge(random_stoch_ci[0], STOCHASTIC_FLOOR)
        and g38_runner._inclusive_ge(min_random, MINIMUM_REPLICATE_FLOOR)
    )
    confident_fail = (
        any(not g38_runner._inclusive_ge(fixed_ci[c][2], UTILITY_FLOOR) for c in g34.CAPACITIES)
        or not g38_runner._inclusive_ge(fixed_stoch_ci[2], STOCHASTIC_FLOOR)
        or not g38_runner._inclusive_ge(min_fixed, MINIMUM_REPLICATE_FLOOR)
        or any(not g38_runner._inclusive_ge(random_ci[c][2], UTILITY_FLOOR) for c in g34.CAPACITIES)
        or any(not g38_runner._inclusive_ge(event_ci[c][2], EVENT_FLOOR) for c in g34.CAPACITIES)
        or any(not g38_runner._inclusive_ge(segment_ci[c][2], SEGMENT_FLOOR) for c in g34.CAPACITIES)
        or any(not g38_runner._inclusive_ge(process_ci[c][2], PROCESS_MARGIN) for c in g34.CAPACITIES)
        or not g38_runner._inclusive_ge(random_stoch_ci[2], STOCHASTIC_FLOOR)
        or not g38_runner._inclusive_ge(min_random, MINIMUM_REPLICATE_FLOOR)
    )
    return {
        "fixed_utility_ci95": fixed_ci,
        "fixed_stochastic_pooled_ci95": fixed_stoch_ci,
        "minimum_fixed_deterministic_replicate_mean": min_fixed,
        "random_utility_ci95": random_ci,
        "random_event_window_ci95": event_ci,
        "random_process_segment_ci95": segment_ci,
        "random_minus_fixed_ci95": process_ci,
        "random_stochastic_pooled_ci95": random_stoch_ci,
        "minimum_random_deterministic_replicate_mean": min_random,
        "access_pass": bool(access_pass),
        "access_confident_fail": bool(confident_fail),
    }


def _comparison(
    evaluation: Mapping[str, Any], plan: tuple[np.ndarray, np.ndarray]
) -> dict[str, object]:
    component_specs = (
        ("fixed_deterministic_utility", FINAL_FIXED_DET, "utility", False),
        ("random_deterministic_utility", FINAL_RANDOM_DET, "utility", False),
        ("fixed_stochastic_utility", FINAL_FIXED_STOCH, "utility", True),
        ("random_stochastic_utility", FINAL_RANDOM_STOCH, "utility", True),
        ("random_event_window", FINAL_RANDOM_DET, "minimum_event_window_utility", False),
        ("random_process_segment", FINAL_RANDOM_DET, "minimum_process_segment_utility", False),
    )
    component_ci: dict[str, object] = {}
    component_ucbs: list[float] = []
    for name, cell, metric, pooled in component_specs:
        delta = _difference(
            _metric_arrays(evaluation, source.DBNORM_ARM, cell, metric),
            _metric_arrays(evaluation, source.MEAN_ARM, cell, metric),
        )
        if pooled:
            ci = _hierarchical_ci(delta, capacities=g34.CAPACITIES, plan=plan)
            component_ci[name] = ci
            component_ucbs.append(ci[2])
        else:
            rows = {
                capacity: _hierarchical_ci(delta, capacities=(capacity,), plan=plan)
                for capacity in g34.CAPACITIES
            }
            component_ci[name] = rows
            component_ucbs.extend(row[2] for row in rows.values())
    transport = _difference(
        _difference(
            _metric_arrays(evaluation, source.DBNORM_ARM, FINAL_RANDOM_DET, "utility"),
            _metric_arrays(evaluation, source.DBNORM_ARM, FINAL_FIXED_DET, "utility"),
        ),
        _difference(
            _metric_arrays(evaluation, source.MEAN_ARM, FINAL_RANDOM_DET, "utility"),
            _metric_arrays(evaluation, source.MEAN_ARM, FINAL_FIXED_DET, "utility"),
        ),
    )
    transport_rows = {
        capacity: _hierarchical_ci(transport, capacities=(capacity,), plan=plan)
        for capacity in g34.CAPACITIES
    }
    component_ci["random_minus_fixed_transport"] = transport_rows
    component_ucbs.extend(row[2] for row in transport_rows.values())
    primary_values = _difference(
        _metric_arrays(evaluation, source.DBNORM_ARM, FINAL_RANDOM_DET, "utility"),
        _metric_arrays(evaluation, source.MEAN_ARM, FINAL_RANDOM_DET, "utility"),
    )
    primary = _hierarchical_ci(
        primary_values, capacities=g34.CAPACITIES, plan=plan
    )
    capacity_primary = {
        capacity: _hierarchical_ci(
            primary_values, capacities=(capacity,), plan=plan
        )
        for capacity in g34.CAPACITIES
    }
    noninferior = g38_runner._inclusive_le(primary[2], NORM_MARGIN) and all(
        g38_runner._inclusive_le(value, NORM_MARGIN)
        for value in component_ucbs
    )
    material = g38_runner._strict_gt(primary[0], NORM_MARGIN) and all(
        g38_runner._strict_gt(capacity_primary[capacity][0], 0.0)
        for capacity in g34.CAPACITIES
    )
    return {
        "dbnorm_minus_mean_primary_ci95": primary,
        "dbnorm_minus_mean_capacity_ci95": capacity_primary,
        "component_ci95": component_ci,
        "mean_noninferior": bool(noninferior),
        "material_dbnorm_advantage": bool(material),
    }


def select_g43_result_branch(metrics: Mapping[str, Any]) -> str:
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH
    if not bool(metrics["source_valid"]) or bool(metrics["dbnorm_access_confident_fail"]):
        return SOURCE_FAILURE_BRANCH
    if (
        bool(metrics["dbnorm_access_pass"])
        and bool(metrics["mean_access_pass"])
        and bool(metrics["mean_noninferior"])
    ):
        return MEAN_SUFFICIENT_BRANCH
    if bool(metrics["dbnorm_access_pass"]) and (
        bool(metrics["mean_access_confident_fail"])
        or bool(metrics["material_dbnorm_advantage"])
    ):
        return DBNORM_ADVANTAGE_BRANCH
    return UNDERPOWERED_BRANCH


def analyze(
    *,
    run_root: Path,
    require_formal: bool = False,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    formal = bool(training.get("formal"))
    if require_formal and not formal:
        raise ValueError("formal G43 analysis requires formal artifacts")
    configuration = _cpu_configuration_from_artifact(training, formal=formal)
    requested = _resolve_cpu_execution(
        int(configuration["cpu_budget"])
        if cpu_budget is None
        else cpu_budget,
        int(configuration["process_workers"])
        if process_workers is None
        else process_workers,
    )
    if (cpu_budget is not None or process_workers is not None) and (
        requested["cpu_budget"] != configuration["cpu_budget"]
        or requested["process_workers"] != configuration["process_workers"]
    ):
        raise ValueError("G43 analyze CPU/process settings differ from training")
    cpu_execution = _configure_cpu_execution(
        int(configuration["cpu_budget"]),
        int(configuration["process_workers"]),
    )
    configure_runtime(bootstrap_seed(formal=formal))
    errors = _evaluation_errors(run_root, training, evaluation)
    metrics: dict[str, Any] = {"operational_valid": not errors}
    if not errors:
        configuration = evaluation["configuration"]
        plan = _bootstrap_plan(
            formal=formal,
            replicates=int(configuration["replicates"]),
            episodes=int(configuration["evaluation_episodes_per_cell"]),
            repetitions=int(configuration["bootstrap_resamples"]),
        )
        access = {arm: _arm_access(evaluation, arm, plan) for arm in source.ARMS}
        comparison = _comparison(evaluation, plan)
        metrics.update(
            {
                "source_valid": evaluation["direct_source_validation"] is True,
                "arm_access": access,
                "dbnorm_access_pass": access[source.DBNORM_ARM]["access_pass"],
                "mean_access_pass": access[source.MEAN_ARM]["access_pass"],
                "dbnorm_access_confident_fail": access[source.DBNORM_ARM]["access_confident_fail"],
                "mean_access_confident_fail": access[source.MEAN_ARM]["access_confident_fail"],
                "treatment_activation_valid": source.validate_conclusion_evidence(
                    training["conclusion_evidence"]
                ),
                **comparison,
            }
        )
    analysis_seconds = time.perf_counter() - started
    nonformal_total: float | None = None
    if not formal and not errors:
        train_seconds = float(training["stage_wall_time_seconds"])
        eval_seconds = float(evaluation["stage_wall_time_seconds"])
        nonformal_total = train_seconds + eval_seconds + analysis_seconds
    if errors:
        branch = INVALID_BRANCH
    elif formal:
        branch = select_g43_result_branch(metrics)
    elif nonformal_total is not None and nonformal_total <= NONFORMAL_WALL_CLOCK_CAP_SECONDS:
        branch = NONFORMAL_BRANCH
    else:
        branch = NON_EXECUTABLE_BRANCH
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "source_id": source.SOURCE_ID,
        "stage": "analyze",
        "status": "COMPLETE" if not errors else "INVALID",
        "formal": formal,
        "source_commit": training.get("source_commit"),
        "aligned_source_commit": ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": training.get("alignment_stage_commit"),
        "preflight_artifact_digests": training.get("preflight_artifact_digests"),
        "operational_valid": not errors,
        "operational_errors": errors,
        "branch": branch,
        "metrics": metrics,
        "native_backend": evaluation.get("native_backend"),
        "cpu_execution": cpu_execution,
        "training_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(run_root / "evaluation_manifest.json"),
        "stage_wall_time_seconds": analysis_seconds,
        "nonformal_total_wall_time_seconds": nonformal_total,
        "nonformal_wall_clock_cap_seconds": NONFORMAL_WALL_CLOCK_CAP_SECONDS,
        "formal_projection_seconds": None,
        "formal_projection_executable": None,
        "formal_wall_clock_cap_seconds": FORMAL_WALL_CLOCK_CAP_SECONDS,
        "thresholds": {
            "utility_floor": UTILITY_FLOOR,
            "event_floor": EVENT_FLOOR,
            "segment_floor": SEGMENT_FLOOR,
            "process_noninferiority_margin": PROCESS_MARGIN,
            "stochastic_floor": STOCHASTIC_FLOOR,
            "minimum_replicate_floor": MINIMUM_REPLICATE_FLOOR,
            "norm_margin": NORM_MARGIN,
        },
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(
    *,
    run_root: Path,
    source_commit: str,
    accepted_anchor_root: Path,
    cpu_budget: int | None = None,
    process_workers: int | None = None,
) -> dict[str, Any]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        accepted_anchor_root=accepted_anchor_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )
    evaluate(
        run_root=run_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )
    return analyze(
        run_root=run_root,
        cpu_budget=cpu_budget,
        process_workers=process_workers,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--authorization-token")
    parser.add_argument("--accepted-anchor-root", type=Path)
    parser.add_argument("--preflight-root", type=Path)
    parser.add_argument("--alignment-disposition")
    parser.add_argument("--aligned-source-commit")
    parser.add_argument("--alignment-stage-commit")
    parser.add_argument("--cpu-budget", type=int)
    parser.add_argument("--process-workers", type=int)
    args = parser.parse_args()
    if args.stage == "train":
        if args.source_commit is None:
            raise ValueError("G43 train requires --source-commit")
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
            accepted_anchor_root=args.accepted_anchor_root,
            preflight_root=args.preflight_root,
            alignment_disposition=args.alignment_disposition,
            aligned_source_commit=args.aligned_source_commit,
            alignment_stage_commit=args.alignment_stage_commit,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    elif args.stage == "evaluate":
        evaluate(
            run_root=args.run_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    elif args.stage == "analyze":
        analyze(
            run_root=args.run_root,
            require_formal=args.formal,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )
    else:
        if args.source_commit is None or args.accepted_anchor_root is None:
            raise ValueError("G43 exercise requires source and accepted anchor root")
        exercise(
            run_root=args.run_root,
            source_commit=args.source_commit,
            accepted_anchor_root=args.accepted_anchor_root,
            cpu_budget=args.cpu_budget,
            process_workers=args.process_workers,
        )


if __name__ == "__main__":
    main()
