"""Dedicated host-to-publication workload with no historical runtime imports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
import hashlib
import platform
import time

from .checkpoint import file_record
from .contract import ARM_IDS, CONTEXTS, WorkloadConfig, expected_counts
from .evaluation import CheckpointEvaluation, evaluate_checkpoint
from .firewall import validate_import_firewall, validate_runtime_path, zero_effect_ledger
from .host import generate_population, validate_population
from .oracle import validate_host
from .reducer import reduce_results
from .training import load_checkpoint_models_read_only, prepare_arm_initialization, prepare_fold_data, train_policy
from .model import basis_for_record
from .oracle import posterior_short
from .topology import configure_torch_topology_once
from fractions import Fraction
from types import SimpleNamespace


@dataclass(frozen=True)
class WorkloadResult:
    config: WorkloadConfig
    binding: str
    activity: dict[str, Any]
    stage_times: tuple[dict[str, Any], ...]
    transform_evidence: tuple[dict[str, Any], ...]
    initialization_parity: tuple[dict[str, Any], ...]
    evaluations: tuple[CheckpointEvaluation, ...]
    reducer: dict[str, Any]
    checkpoints: tuple[dict[str, Any], ...]
    zero_effects: dict[str, int]
    runtime: dict[str, Any]


def _transform_evidence(seed_id, fold_id, stage, record):
    import torch
    gram, lower = record.gram_matrix(), record.lower_matrix(); residual = torch.max(torch.abs(gram - lower @ lower.T)).item()
    return {
        "seed_id": seed_id, "fold_id": fold_id, "stage": stage,
        "x_shape": [record.row_count, record.feature_dim], "g_shape": list(gram.shape), "l_shape": list(lower.shape),
        "ordered_x_sha256": record.ordered_design_sha256,
        "g_sha256": hashlib.sha256(record.gram_fp32_le).hexdigest(), "l_sha256": hashlib.sha256(record.cholesky_lower_fp32_le).hexdigest(),
        "cholesky_success": True, "positive_diagonal": bool(torch.all(torch.diagonal(lower) > 0).item()),
        "reconstruction_max_abs": float(residual), "precision": "float32", "accumulation": "torch_matmul_ordered_rows",
        "factorization": "torch.linalg.cholesky_upper_false", "solve": "torch.linalg.solve_triangular_column_convention",
        "serialization": "canonical_little_endian_fp32_and_sorted_json",
        "target_fields_read": 0, "outcome_fields_read": 0,
    }


def run_workload(config: WorkloadConfig, *, binding: str, scratch_root: str | Path, event_callback: Callable[[Mapping[str, Any]], None] | None = None) -> WorkloadResult:
    topology_record = configure_torch_topology_once()
    config.validate()
    if type(binding) is not str or len(binding) != 64 or any(c not in "0123456789abcdef" for c in binding):
        raise ValueError("workload requires lowercase SHA-256 binding")
    scratch = validate_runtime_path(scratch_root)
    if scratch.exists() and not scratch.is_dir(): raise ValueError("scratch root must be a directory")
    scratch.mkdir(parents=True, exist_ok=True)
    package_root = Path(__file__).resolve().parent; sources = tuple(sorted(package_root.glob("*.py")))
    validate_import_firewall(sources)
    if config.mode != "ASSESS": validate_host()
    stages = []
    def stage(name, started, **extra):
        row = {"stage": name, "wall_seconds": time.perf_counter() - started, **extra}; stages.append(row)
        if event_callback: event_callback(row)
    populations = {}; data_activity = {"environment_episodes": 0, "environment_transitions": 0, "root_rows": 0, "tail_rows": 0}
    started = time.perf_counter()
    for seed in config.seed_ids:
        population = generate_population(config, seed); populations[seed] = population; audit = validate_population(config, seed, population)
        for key in data_activity: data_activity[key] += audit[{"environment_episodes": "episodes", "environment_transitions": "transitions", "root_rows": "root_rows", "tail_rows": "tail_rows"}[key]]
    stage("fresh_environment", started)
    transforms = {}; prepared = {}; transform_evidence = []
    started = time.perf_counter()
    for seed in config.seed_ids:
        for fold in (0, 1):
            prepared[(seed, fold)] = prepare_fold_data(config, populations[seed], seed_id=seed, fold_id=fold); cell = prepared[(seed, fold)].transforms; transforms[(seed, fold)] = cell
            transform_evidence.extend(_transform_evidence(seed, fold, stage_name, record) for stage_name, record in cell.items())
    stage("feature_only_transforms", started)
    policy_runs = []; parity = []
    initializations = {(arm, seed, fold): prepare_arm_initialization(prepared[(seed, fold)], arm) for arm in config.arms for seed in config.seed_ids for fold in (0, 1)}
    for arm in config.arms:
        for seed in config.seed_ids:
            for fold in (0, 1):
                started = time.perf_counter(); run = train_policy(config, populations[seed], arm_id=arm, seed_id=seed, fold_id=fold, prepared=prepared[(seed, fold)], initialization=initializations[(arm, seed, fold)], binding=binding, checkpoint_root=scratch / "checkpoints" / arm / seed / f"fold-{fold}", event_callback=event_callback)
                policy_runs.append(run)
                parity.extend({"arm_id": arm, "seed_id": seed, "fold_id": fold, "stage": stage_name, **evidence} for stage_name, evidence in run.parity.items())
                stage("policy_training", started, arm_id=arm, seed_id=seed, fold_id=fold)
    evaluations = []; checkpoints = []; assessment_score_calls = 0
    started = time.perf_counter()
    for run in policy_runs:
        for snapshot in run.checkpoint_paths:
            payload, root_model, tail_model = load_checkpoint_models_read_only(snapshot["projection_path"])
            if config.mode == "ASSESS":
                import torch
                for context in CONTEXTS:
                    link, reliability, cost = context
                    root_record = SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=Fraction(1, 2))
                    root_rows = [basis_for_record(root_record, stage="root", period=0, action_probe=True)] + [basis_for_record(root_record, stage="root", period=period, action_probe=False) for period in tuple(sorted(set((1,2,3,4,5,6,7,8,9))))]
                    with torch.no_grad():
                        values = root_model(torch.stack(root_rows))
                    if not torch.isfinite(values).all().item(): raise ValueError("assessment candidate-score workload nonfinite")
                    assessment_score_calls += len(root_rows)
                    for count in range(7):
                        tail_record = SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=posterior_short(link, reliability, count))
                        tail_rows = [basis_for_record(tail_record, stage="tail", period=period) for period in tuple(sorted(set((1,2,3,4,5,6,7,8,9))))]
                        with torch.no_grad(): values = tail_model(torch.stack(tail_rows))
                        if not torch.isfinite(values).all().item(): raise ValueError("assessment candidate-score workload nonfinite")
                        assessment_score_calls += len(tail_rows)
            else:
                evaluations.append(evaluate_checkpoint(root_model, tail_model, arm_id=run.arm_id, seed_id=run.seed_id, fold_id=run.fold_id, root_update=payload["root_update"], sampled_episodes=config.sampled_evaluation_episodes))
            checkpoints.append({"arm_id": run.arm_id, "seed_id": run.seed_id, "fold_id": run.fold_id, "root_update": payload["root_update"], **{name: {"path": str(Path(snapshot[f"{name}_path"]).resolve()), **file_record(snapshot[f"{name}_path"])} for name in ("full", "projection", "binding")}})
    stage("odd_even_and_sampled_evaluation", started)
    reduced = {} if config.mode == "ASSESS" else reduce_results(evaluations, seed_ids=config.seed_ids, final_update=config.root_updates)
    activity = dict(data_activity)
    for key in ("root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures", "tail_example_exposures", "target_materialization_events", "target_materialization_rows", "root_clip_events", "tail_clip_events", "nonfinite_events"):
        activity[key] = sum(run.activity[key] for run in policy_runs)
    activity["policies"] = len(policy_runs); activity["checkpoints"] = len(checkpoints)
    activity["exact_support_evaluations"] = len(checkpoints) * 2
    activity["sampled_evaluation_episodes"] = sum(item.sampled["episodes"] for item in evaluations)
    activity["sampled_evaluation_transitions"] = sum(item.sampled["transitions"] for item in evaluations)
    if config.mode == "ASSESS": activity["evaluator_candidate_score_calls"] = assessment_score_calls
    expected = expected_counts(config)
    for key, value in expected.items():
        if activity.get(key) != value: raise ValueError(f"activity count drift: {key}={activity.get(key)} expected {value}")
    import torch
    runtime = {"python": platform.python_version(), "torch": torch.__version__, "torch_threads": torch.get_num_threads(), "execution_topology": topology_record}
    return WorkloadResult(config, binding, activity, tuple(stages), tuple(transform_evidence), tuple(parity), tuple(evaluations), reduced, tuple(checkpoints), zero_effect_ledger(), runtime)
