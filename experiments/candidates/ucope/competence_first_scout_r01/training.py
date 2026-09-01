"""Exact three-arm target clocks, separate optimizers, and cold-resume seam."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
import math

from .checkpoint import load_checkpoint, make_checkpoint, restore_checkpoint, save_checkpoint
from .contract import K_TRAIN, RunBinding, ScoutConfig
from .evaluation import PolicyEvaluation, evaluate_policy
from .host import Episode, validate_population
from .model import build_arm, optimizer_for, tensors_for_record


def _torch():
    import torch
    return torch


@dataclass(frozen=True)
class PolicyRun:
    arm_id: str
    seed_id: str
    fold_id: int
    activity: dict[str, Any]
    evaluations: tuple[PolicyEvaluation, ...]
    checkpoint_paths: tuple[str, ...]


def _canonical_rows(population: Iterable[Episode], *, fold: int, tail: bool) -> tuple[Episode, ...]:
    wanted = 1 - fold if tail else fold
    rows = tuple(
        row for row in population
        if row.fold_id == wanted and (not tail or row.behavior_action == "PROBE")
    )
    return tuple(sorted(rows, key=lambda row: (row.episode_index, row.context_id)))


def _cyclic_batch(rows: tuple[Any, ...], update_index: int, batch_size: int):
    start = (update_index * batch_size) % len(rows)
    return tuple(rows[(start + offset) % len(rows)] for offset in range(batch_size))


def _tail_batch(rows):
    torch = _torch()
    x, z, y = [], [], []
    for row in rows:
        pair = tensors_for_record(row, stage="tail", action_probe=False, period=row.behavior_period, belief=float(row.belief_short))
        x.append(pair[0]); z.append(pair[1]); y.append(row.tail_return)
    return torch.stack(x), torch.stack(z), torch.tensor(y, dtype=torch.float32)


def _root_features(rows):
    torch = _torch()
    x, z = [], []
    for row in rows:
        probe = row.behavior_action == "PROBE"
        pair = tensors_for_record(row, stage="root", action_probe=probe, period=0 if probe else row.behavior_period, belief=0.5)
        x.append(pair[0]); z.append(pair[1])
    return torch.stack(x), torch.stack(z)


def _root_targets(rows, tail_scorer):
    torch = _torch()
    targets = torch.empty(len(rows), dtype=torch.float32)
    probe_indices = []
    candidate_x = []
    candidate_z = []
    with torch.no_grad():
        for index, row in enumerate(rows):
            if row.behavior_action == "IMMEDIATE":
                targets[index] = row.tail_return
                continue
            probe_indices.append(index)
            candidates = [tensors_for_record(row, stage="tail", action_probe=False, period=period, belief=float(row.belief_short)) for period in K_TRAIN]
            candidate_x.extend(pair[0] for pair in candidates)
            candidate_z.extend(pair[1] for pair in candidates)
        if probe_indices:
            values = tail_scorer(torch.stack(candidate_x), torch.stack(candidate_z)).reshape(len(probe_indices), len(K_TRAIN)).max(dim=1).values
            primitive = torch.tensor([rows[index].probe_primitive for index in probe_indices], dtype=torch.float32)
            targets[torch.tensor(probe_indices, dtype=torch.int64)] = primitive + values
    if not torch.isfinite(targets).all().item():
        raise ValueError("nonfinite root target")
    return targets


def _step(scorer, optimizer, x, z, targets, activity, prefix):
    torch = _torch()
    optimizer.zero_grad(set_to_none=True)
    prediction = scorer(x, z)
    loss = torch.nn.functional.mse_loss(prediction, targets)
    if not torch.isfinite(loss).item():
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite training loss")
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(scorer.parameters(), 1.0)
    norm_value = float(norm.item())
    if not math.isfinite(norm_value):
        activity["nonfinite_events"] += 1
        raise ValueError("nonfinite gradient norm")
    activity[f"{prefix}_gradient_norm_sum"] += norm_value
    activity[f"{prefix}_gradient_norm_max"] = max(activity[f"{prefix}_gradient_norm_max"], norm_value)
    activity[f"{prefix}_clipping_events"] += int(norm_value > 1.0)
    optimizer.step()
    for parameter in scorer.parameters():
        if parameter.dtype != torch.float32 or not torch.isfinite(parameter).all().item():
            activity["nonfinite_events"] += 1
            raise ValueError("nonfinite/non-FP32 parameter after update")


def _initial_activity(root_rows: int, tail_rows: int) -> dict[str, Any]:
    return {
        "root_inventory": root_rows,
        "tail_inventory": tail_rows,
        "root_optimizer_updates": 0,
        "tail_optimizer_updates": 0,
        "root_example_exposures": 0,
        "tail_example_exposures": 0,
        "target_refresh_events": 0,
        "target_refresh_rows": 0,
        "target_materialization_events": 0,
        "target_materialization_rows": 0,
        "root_clipping_events": 0,
        "tail_clipping_events": 0,
        "root_gradient_norm_sum": 0.0,
        "tail_gradient_norm_sum": 0.0,
        "root_gradient_norm_max": 0.0,
        "tail_gradient_norm_max": 0.0,
        "nonfinite_events": 0,
        "exact_policy_evaluations": 0,
        "sampled_evaluation_episodes": 0,
        "sampled_evaluation_transitions": 0,
    }


def _latest_checkpoint(root: Path, config: ScoutConfig):
    existing = []
    for update in config.evaluation_root_updates:
        path = root / f"root-{update:04d}.pt"
        if path.exists():
            existing.append((update, path))
    return max(existing)[1] if existing else None


def train_policy(
    config: ScoutConfig,
    population: tuple[Episode, ...],
    *,
    arm_id: str,
    seed_id: str,
    fold_id: int,
    run_binding: RunBinding,
    checkpoint_root: str | Path,
    stage_callback: Callable[[dict[str, Any]], None] | None = None,
    stop_after_root_updates: int | None = None,
) -> PolicyRun:
    """Train one policy; interruption is allowed only at a declared checkpoint root."""
    config.validate()
    run_binding = RunBinding.from_value(run_binding, config.mode)
    validate_population(config, seed_id, population)
    if stop_after_root_updates is not None and stop_after_root_updates not in config.evaluation_root_updates:
        raise ValueError("test interruption must coincide with a declared checkpoint")
    torch = _torch()
    torch.use_deterministic_algorithms(True)
    root_rows = _canonical_rows(population, fold=fold_id, tail=False)
    tail_rows = _canonical_rows(population, fold=fold_id, tail=True)
    checkpoint_root = Path(checkpoint_root)
    latest = _latest_checkpoint(checkpoint_root, config)
    frozen_targets = None
    checkpoint_paths = []
    if latest is None:
        root, tail = build_arm(arm_id, seed_id, fold_id)
        root_optimizer, tail_optimizer = optimizer_for(root), optimizer_for(tail)
        root_updates = tail_updates = 0
        activity = _initial_activity(len(root_rows), len(tail_rows))
    else:
        payload = load_checkpoint(latest)
        if payload["config"] != config.to_dict() or payload["run_binding"] != run_binding.to_dict() or (payload["arm_id"], payload["seed_id"], payload["fold_id"]) != (arm_id, seed_id, fold_id):
            raise ValueError("cold-resume checkpoint binding mismatch")
        root, tail, root_optimizer, tail_optimizer = restore_checkpoint(payload)
        root_updates, tail_updates = payload["root_updates"], payload["tail_updates"]
        activity = dict(payload["activity"])
        frozen_targets = payload["frozen_root_targets"]
    if stage_callback:
        stage_callback({"stage": "policy_start", "arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "resumed_root_updates": root_updates})

    def tail_update():
        nonlocal tail_updates
        batch = _cyclic_batch(tail_rows, tail_updates, config.batch_size)
        x, z, y = _tail_batch(batch)
        _step(tail, tail_optimizer, x, z, y, activity, "tail")
        tail_updates += 1
        activity["tail_optimizer_updates"] += 1
        activity["tail_example_exposures"] += len(batch)

    def root_update():
        nonlocal root_updates
        batch = _cyclic_batch(root_rows, root_updates, config.batch_size)
        x, z = _root_features(batch)
        if arm_id == "MT-XF-FLEX":
            y = _root_targets(batch, tail)
            activity["target_refresh_events"] += 1
            activity["target_refresh_rows"] += sum(row.behavior_action == "PROBE" for row in batch)
        else:
            indices = [((root_updates * config.batch_size) + offset) % len(root_rows) for offset in range(config.batch_size)]
            y = frozen_targets[indices]
        _step(root, root_optimizer, x, z, y, activity, "root")
        root_updates += 1
        activity["root_optimizer_updates"] += 1
        activity["root_example_exposures"] += len(batch)

    if arm_id == "MT-XF-FLEX":
        while root_updates < config.root_updates:
            expected_tail = root_updates // 2
            if tail_updates <= expected_tail and tail_updates < config.tail_updates:
                tail_update()
            root_update()
            if root_updates % 2 == 1:
                root_update()
            _maybe_checkpoint(config, run_binding, arm_id, seed_id, fold_id, root, tail, root_optimizer, tail_optimizer, root_updates, tail_updates, activity, checkpoint_root, None, checkpoint_paths, stage_callback)
            if stop_after_root_updates == root_updates:
                break
    else:
        while tail_updates < config.tail_updates:
            tail_update()
        if frozen_targets is None:
            frozen_targets = _root_targets(root_rows, tail)
            activity["target_materialization_events"] += 1
            activity["target_materialization_rows"] += len(root_rows)
        while root_updates < config.root_updates:
            root_update()
            _maybe_checkpoint(config, run_binding, arm_id, seed_id, fold_id, root, tail, root_optimizer, tail_optimizer, root_updates, tail_updates, activity, checkpoint_root, frozen_targets, checkpoint_paths, stage_callback)
            if stop_after_root_updates == root_updates:
                break
    if stage_callback:
        stage_callback({"stage": "policy_end", "arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "root_updates": root_updates, "tail_updates": tail_updates})
    expected_checkpoints = tuple(checkpoint_root / f"root-{update:04d}.pt" for update in config.evaluation_root_updates if update <= root_updates)
    if any(not path.is_file() for path in expected_checkpoints):
        raise ValueError("declared checkpoint cadence is incomplete")
    evaluations = []
    for path in expected_checkpoints:
        payload = load_checkpoint(path)
        checkpoint_root_model, checkpoint_tail_model, _root_optimizer, _tail_optimizer = restore_checkpoint(payload)
        item = evaluate_policy(
            checkpoint_root_model, checkpoint_tail_model, arm_id=arm_id, seed_id=seed_id,
            fold_id=fold_id, root_update=payload["root_updates"],
            sampled_episodes=config.sampled_evaluation_episodes,
        )
        evaluations.append(item)
    activity = dict(activity)
    activity["exact_policy_evaluations"] = sum(item.exact_policy_evaluations for item in evaluations)
    activity["sampled_evaluation_episodes"] = sum(item.sampled_evaluation_episodes for item in evaluations)
    activity["sampled_evaluation_transitions"] = sum(item.sampled_evaluation_transitions for item in evaluations)
    return PolicyRun(arm_id, seed_id, fold_id, activity, tuple(evaluations), tuple(str(path) for path in expected_checkpoints))


def _maybe_checkpoint(config, run_binding, arm_id, seed_id, fold_id, root, tail, root_optimizer, tail_optimizer, root_updates, tail_updates, activity, checkpoint_root, frozen_targets, checkpoint_paths, stage_callback):
    if root_updates not in config.evaluation_root_updates:
        return
    path = checkpoint_root / f"root-{root_updates:04d}.pt"
    payload = make_checkpoint(
        config=config, run_binding=run_binding, arm_id=arm_id, seed_id=seed_id, fold_id=fold_id,
        root=root, tail=tail, root_optimizer=root_optimizer, tail_optimizer=tail_optimizer,
        root_updates=root_updates, tail_updates=tail_updates, activity=activity,
        frozen_root_targets=frozen_targets,
    )
    save_checkpoint(path, payload)
    checkpoint_paths.append(str(path))
    if stage_callback:
        stage_callback({
            "stage": "checkpoint", "arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id,
            "root_update": root_updates, "activity": dict(activity),
        })
