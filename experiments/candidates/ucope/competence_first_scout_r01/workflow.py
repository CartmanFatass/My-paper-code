"""Core workload API used by the later script-level resource/runner layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import json
import os
import platform
import sys
import time

from .artifact import atomic_create_json
from .contract import ARM_IDS, OBJECT_ID, RunBinding, ScoutConfig, expected_activity_totals, expected_parameter_counts, expected_work, validate_host_opportunity_map
from .evaluation import enforce_conditional_acquisition
from .gates import apply_gates
from .host import generate_population, validate_population
from .model import build_arm
from .training import PolicyRun, train_policy

FORBIDDEN_PATH_PARTS = frozenset(
    {
        "contextual_paid_acquisition_r01",
        "structural_competence",
        "ucope-contextual-paid-acquisition-r01-production",
        "ucope-structural-competence",
    }
)


@dataclass(frozen=True)
class WorkloadResult:
    config: ScoutConfig
    run_binding: RunBinding
    work: dict[str, Any]
    activity: dict[str, Any]
    stage_times: tuple[dict[str, Any], ...]
    source_refs: tuple[str, ...]
    runtime_refs: dict[str, Any]
    internal_result: dict[str, Any]
    checkpoints: tuple[str, ...]


def validate_scratch_fence(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    lowered = str(resolved).lower()
    if any(part in lowered for part in FORBIDDEN_PATH_PARTS):
        raise ValueError("scratch root may not enter consumed/source artifact namespaces")
    return resolved


def _manifest(config: ScoutConfig, run_binding: RunBinding) -> dict[str, Any]:
    return {
        "object_id": OBJECT_ID,
        "config": config.to_dict(),
        "run_binding": run_binding.to_dict(),
        "rng_version": config.rng_version,
        "data_source": "fresh_counter_generated_host_only",
        "consumed_artifacts_read": False,
    }


def _bind_manifest(config: ScoutConfig, run_binding: RunBinding, scratch: Path) -> None:
    path = scratch / "run-manifest.json"
    expected = _manifest(config, run_binding)
    if path.exists():
        with path.open("r", encoding="utf-8") as stream:
            existing = json.load(stream)
        if existing != expected:
            raise ValueError("scratch root is bound to a different frozen config/RNG/data source")
    else:
        atomic_create_json(path, expected)


def _parameter_count() -> dict[str, int]:
    result = {}
    for arm in ARM_IDS:
        root, tail = build_arm(arm, "parameter-sizing-only", 0)
        result[arm] = sum(parameter.numel() for scorer in (root, tail) for parameter in scorer.parameters())
    return result


def run_workload(
    config: ScoutConfig,
    scratch_root: str | Path,
    stage_callback: Callable[[dict[str, Any]], None] | None = None,
    *,
    run_binding: RunBinding | dict[str, Any] | None = None,
) -> WorkloadResult:
    """Run a frozen core workload; callers own resource admission and external publication.

    ``ScoutConfig.assess()`` is a deliberately reduced two-checkpoint A/RECON sizing path. Its
    checkpoints live only under ``non_scientific_assess_state`` and carry no result authority.
    """
    config.validate()
    if run_binding is None:
        raise ValueError("run_workload requires an explicit prospective run_binding")
    run_binding = RunBinding.from_value(run_binding, config.mode)
    scratch = validate_scratch_fence(scratch_root)
    scratch.mkdir(parents=True, exist_ok=True)
    _bind_manifest(config, run_binding, scratch)
    validate_host_opportunity_map()
    stage_times = []

    def emit(event):
        stage_times.append(dict(event))
        if stage_callback:
            stage_callback(dict(event))

    populations = {}
    support_limited = {}
    support_histograms = {}
    data_activity = {"environment_episodes": 0, "environment_transitions": 0, "root_rows": 0, "tail_rows": 0}
    data_start_wall, data_start_cpu = time.perf_counter(), time.process_time()
    for seed in config.seed_ids:
        population = generate_population(config, seed)
        populations[seed] = population
        audit = validate_population(config, seed, population)
        support_limited[seed] = bool(audit["support_limited"])
        support_histograms[seed] = {
            cell: {
                f"fold-{fold}": [audit["displayed_count_support"][(cell, fold)][count] for count in range(7)]
                for fold in (0, 1)
            }
            for cell in sorted({key[0] for key in audit["displayed_count_support"]})
        }
        audit_fields = {
            "environment_episodes": "episodes",
            "environment_transitions": "transitions",
            "root_rows": "root_rows",
            "tail_rows": "tail_rows",
        }
        for field, audit_field in audit_fields.items():
            data_activity[field] += int(audit[audit_field])
    emit({"stage": "fresh_data", "wall_seconds": time.perf_counter() - data_start_wall, "cpu_seconds": time.process_time() - data_start_cpu})

    policy_runs: list[PolicyRun] = []
    state_name = "non_scientific_assess_state" if config.mode == "ASSESS" else "scientific_checkpoints"
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                start_wall, start_cpu = time.perf_counter(), time.process_time()
                run = train_policy(
                    config,
                    populations[seed],
                    arm_id=arm,
                    seed_id=seed,
                    fold_id=fold,
                    run_binding=run_binding,
                    checkpoint_root=scratch / state_name / arm / seed / f"fold-{fold}",
                    stage_callback=stage_callback,
                )
                policy_runs.append(run)
                emit({
                    "stage": "policy", "arm_id": arm, "seed_id": seed, "fold_id": fold,
                    "wall_seconds": time.perf_counter() - start_wall,
                    "cpu_seconds": time.process_time() - start_cpu,
                    "root_updates": run.activity["root_optimizer_updates"],
                    "tail_updates": run.activity["tail_optimizer_updates"],
                })
    evaluations = enforce_conditional_acquisition(
        tuple(item for run in policy_runs for item in run.evaluations),
        final_root_update=config.root_updates,
        support_limited=support_limited,
    )
    gates = apply_gates(
        evaluations,
        seed_ids=config.seed_ids,
        final_root_update=config.root_updates,
        host_valid=True,
        support_limited=support_limited,
    )
    per_policy = {f"{run.arm_id}|{run.seed_id}|fold-{run.fold_id}": dict(run.activity) for run in policy_runs}
    activity = dict(data_activity)
    for field in (
        "root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures", "tail_example_exposures",
        "target_refresh_events", "target_refresh_rows", "target_materialization_events", "target_materialization_rows",
        "root_clipping_events", "tail_clipping_events", "root_gradient_norm_sum", "tail_gradient_norm_sum",
        "nonfinite_events", "exact_policy_evaluations", "sampled_evaluation_episodes", "sampled_evaluation_transitions",
    ):
        activity[field] = sum(run.activity[field] for run in policy_runs)
    activity["root_gradient_norm_max"] = max(run.activity["root_gradient_norm_max"] for run in policy_runs)
    activity["tail_gradient_norm_max"] = max(run.activity["tail_gradient_norm_max"] for run in policy_runs)
    activity["parameter_count"] = _parameter_count()
    if activity["parameter_count"] != expected_parameter_counts():
        raise ValueError("parameter-count proxy drift")
    activity["checkpoint_writes"] = sum(len(run.checkpoint_paths) for run in policy_runs)
    activity["policies_completed"] = sum(run.activity["root_optimizer_updates"] == config.root_updates and run.activity["tail_optimizer_updates"] == config.tail_updates for run in policy_runs)
    activity["per_policy"] = per_policy
    for field, expected in expected_activity_totals(config).items():
        if activity[field] != expected:
            raise ValueError(f"activity counter mismatch for {field}: {activity[field]} != {expected}")
    work = expected_work(config)
    source_root = Path(__file__).resolve().parent
    source_refs = tuple(str(path) for path in sorted(source_root.glob("*.py")))
    if any(any(part in path.lower() for part in FORBIDDEN_PATH_PARTS) for path in source_refs):
        raise ValueError("consumed source import/path fence violated")
    import torch
    runtime_refs = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "dtype": "float32",
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "pid": os.getpid(),
        "torch_intraop_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
        "core_worker_processes": 1,
    }
    internal = {
        "support_limited": support_limited,
        "support_histograms": support_histograms,
        "evaluations": [item.to_dict() for item in evaluations],
        "gates": gates,
    }
    checkpoints = tuple(path for run in policy_runs for path in run.checkpoint_paths)
    return WorkloadResult(config, run_binding, work, activity, tuple(stage_times), source_refs, runtime_refs, internal, checkpoints)
