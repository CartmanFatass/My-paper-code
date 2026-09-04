"""Target-frozen tail-first training, exact exposure, and cold resume."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
import math

from .checkpoint import load_checkpoint, load_evaluation_projection, save_snapshot_transaction
from .conditioning import TransformRecord, build_transform
from .contract import CONTEXTS, K_EVAL, K_TRAIN, WorkloadConfig
from .host import Episode, ordered_rows
from .model import basis_for_record, build_arm
from .model import BCScorer, build_arm, initial_beta_for_arm, raw_initialization
from .conditioning import pair_initial_coefficients
from .oracle import posterior_short
from .topology import configure_torch_topology_once
from fractions import Fraction
from types import SimpleNamespace


def _torch():
    import torch
    return torch


def feature_matrix(rows: Iterable[Episode], *, stage: str):
    torch = _torch()
    values = []
    for row in rows:
        probe = row.behavior_action == "PROBE"
        values.append(basis_for_record(row, stage=stage, period=row.behavior_period if stage == "tail" or not probe else 0, action_probe=probe if stage == "root" else False))
    return torch.stack(values)


@dataclass(frozen=True)
class PreparedFold:
    seed_id: str
    fold_id: int
    root_rows: tuple[Episode, ...]
    tail_rows: tuple[Episode, ...]
    root_features: Any
    tail_features: Any
    root_candidate_features: Any
    tail_candidate_features: Any
    transforms: dict[str, TransformRecord]


def prepare_fold_data(config: WorkloadConfig, population: tuple[Episode, ...], *, seed_id: str, fold_id: int) -> PreparedFold:
    tail_rows = ordered_rows(population, fold_id=fold_id, stage="tail")
    root_rows = ordered_rows(population, fold_id=fold_id, stage="root")
    if config.mode == "SCIENCE" and (len(tail_rows), len(root_rows)) != (10_240, 20_480):
        raise ValueError("scientific transform row inventory drift")
    tail_features, root_features = feature_matrix(tail_rows, stage="tail"), feature_matrix(root_rows, stage="root")
    transforms = {"tail": build_transform("tail", tail_features), "root": build_transform("root", root_features)}
    return PreparedFold(seed_id, fold_id, root_rows, tail_rows, root_features, tail_features, _candidate_features("root"), _candidate_features("tail"), transforms)


def build_fold_transforms(config: WorkloadConfig, population: tuple[Episode, ...], *, seed_id: str, fold_id: int) -> dict[str, TransformRecord]:
    return prepare_fold_data(config, population, seed_id=seed_id, fold_id=fold_id).transforms


def _cyclic_indices(row_count: int, update: int, batch_size: int) -> list[int]:
    start = (update * batch_size) % row_count
    return [(start + offset) % row_count for offset in range(batch_size)]


def _tail_targets(rows: tuple[Episode, ...]):
    return _torch().tensor([row.tail_return for row in rows], dtype=_torch().float32)


def materialize_root_targets(rows: tuple[Episode, ...], tail, tail_record: TransformRecord):
    torch = _torch()
    targets = torch.empty(len(rows), dtype=torch.float32)
    with torch.no_grad():
        for index, row in enumerate(rows):
            if row.behavior_action == "IMMEDIATE":
                targets[index] = row.tail_return
            else:
                candidates = torch.stack([basis_for_record(row, stage="tail", period=period) for period in K_TRAIN])
                targets[index] = row.probe_primitive + tail(candidates).max()
    if not torch.isfinite(targets).all().item():
        raise ValueError("root target materialization is nonfinite")
    return targets


def _step(model, optimizer, features, targets) -> tuple[float, bool]:
    torch = _torch()
    optimizer.zero_grad(set_to_none=True)
    prediction = model(features)
    loss = torch.nn.functional.mse_loss(prediction, targets)
    if loss.dtype != torch.float32 or not torch.isfinite(loss).item():
        raise ValueError("training loss is nonfinite/non-FP32")
    loss.backward()
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    norm_value = float(norm.item())
    if not math.isfinite(norm_value):
        raise ValueError("gradient norm is nonfinite")
    optimizer.step()
    for parameter in model.parameters():
        if parameter.dtype != torch.float32 or not torch.isfinite(parameter).all().item():
            raise ValueError("updated parameter is nonfinite/non-FP32")
    return norm_value, norm_value > 1.0


def _activity(root_rows: int, tail_rows: int) -> dict[str, Any]:
    return {
        "root_inventory": root_rows, "tail_inventory": tail_rows,
        "root_optimizer_updates": 0, "tail_optimizer_updates": 0,
        "root_example_exposures": 0, "tail_example_exposures": 0,
        "target_materialization_events": 0, "target_materialization_rows": 0,
        "root_gradient_norm_sum": 0.0, "tail_gradient_norm_sum": 0.0,
        "root_gradient_norm_max": 0.0, "tail_gradient_norm_max": 0.0,
        "root_clip_events": 0, "tail_clip_events": 0, "nonfinite_events": 0,
    }


@dataclass(frozen=True)
class PolicyRun:
    arm_id: str
    seed_id: str
    fold_id: int
    activity: dict[str, Any]
    checkpoint_paths: tuple[dict[str, Any], ...]
    transform_records: dict[str, bytes]
    parity: dict[str, dict[str, Any]]


def _latest_checkpoint(root: Path, config: WorkloadConfig) -> Path | None:
    candidates = [root / f"root-{update:04d}.full.pt" for update in config.checkpoint_root_updates]
    existing = [path for path in candidates if path.is_file()]
    return existing[-1] if existing else None


def _restore_bundle(payload, bundle):
    bundle.root.load_state_dict(payload["root_state"], strict=True)
    bundle.tail.load_state_dict(payload["tail_state"], strict=True)
    bundle.root_optimizer.load_state_dict(payload["root_optimizer"])
    bundle.tail_optimizer.load_state_dict(payload["tail_optimizer"])


def _candidate_features(stage: str):
    """Complete fixed odd/even candidate coordinates, target-free."""
    candidates = []
    periods = tuple(sorted(set(K_TRAIN + K_EVAL)))
    for link, reliability, cost in CONTEXTS:
        if stage == "root":
            record = SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=Fraction(1, 2))
            candidates.append(basis_for_record(record, stage="root", period=0, action_probe=True))
            candidates.extend(basis_for_record(record, stage="root", period=period, action_probe=False) for period in periods)
        else:
            for count in range(7):
                record = SimpleNamespace(link=link, reliability=reliability, total_cost=cost, belief_short=posterior_short(link, reliability, count))
                candidates.extend(basis_for_record(record, stage="tail", period=period) for period in periods)
    return _torch().stack(candidates)


def _verification_features(stage: str, training_features):
    return _torch().cat((training_features, _candidate_features(stage)), dim=0)


@dataclass(frozen=True)
class ArmInitialization:
    root_initial: Any
    tail_initial: Any
    parity: dict[str, dict[str, Any]]


def prepare_arm_initialization(prepared: PreparedFold, arm_id: str) -> ArmInitialization:
    initial = {}; parity = {}
    for stage in ("root", "tail"):
        raw = raw_initialization(stage, prepared.seed_id, prepared.fold_id); transform = prepared.transforms[stage]
        training = prepared.root_features if stage == "root" else prepared.tail_features
        candidates = prepared.root_candidate_features if stage == "root" else prepared.tail_candidate_features
        training_evidence = pair_initial_coefficients(transform, raw, training); candidate_evidence = pair_initial_coefficients(transform, raw, candidates)
        initial[stage] = training_evidence.raw_beta0 if arm_id == "FT-XF-BC-RAW" else training_evidence.whitened_beta0
        parity[stage] = {"exact": training_evidence.exact and candidate_evidence.exact, "maximum_absolute_error": max(training_evidence.maximum_absolute_error, candidate_evidence.maximum_absolute_error), "training_rows_checked": int(training.shape[0]), "candidate_rows_checked": int(candidates.shape[0])}
    return ArmInitialization(initial["root"], initial["tail"], parity)


def load_checkpoint_bundle(config: WorkloadConfig, population: tuple[Episode, ...], *, transforms: Mapping[str, TransformRecord], path: str | Path):
    """Rehydrate one checkpoint without stepping or rewriting it."""
    payload = load_checkpoint(path)
    root_rows = ordered_rows(population, fold_id=payload["fold_id"], stage="root")
    tail_rows = ordered_rows(population, fold_id=payload["fold_id"], stage="tail")
    bundle = build_arm(
        payload["arm_id"], payload["seed_id"], payload["fold_id"],
        root_transform=transforms["root"], tail_transform=transforms["tail"],
        root_features=_verification_features("root", feature_matrix(root_rows, stage="root")), tail_features=_verification_features("tail", feature_matrix(tail_rows, stage="tail")),
    )
    _restore_bundle(payload, bundle)
    return payload, bundle


def load_checkpoint_models_read_only(path: str | Path):
    """Rehydrate scorer tensors from bound transforms without data or optimizer."""
    payload = load_evaluation_projection(path); torch = _torch(); models = {}
    for stage in ("root", "tail"):
        record = TransformRecord.from_bytes(payload["transforms"][stage]); dim = record.feature_dim
        initial = initial_beta_for_arm(stage, payload["arm_id"], payload["seed_id"], payload["fold_id"], record)
        model = BCScorer.build(stage, payload["arm_id"], initial, record)
        model.load_state_dict(payload[f"{stage}_state"], strict=True); models[stage] = model
    return payload, models["root"], models["tail"]


def train_policy(config: WorkloadConfig, population: tuple[Episode, ...], *, arm_id: str, seed_id: str, fold_id: int, transforms: Mapping[str, TransformRecord] | None = None, prepared: PreparedFold | None = None, initialization: ArmInitialization | None = None, binding: str, checkpoint_root: str | Path, event_callback: Callable[[Mapping[str, Any]], None] | None = None, stop_after_root_update: int | None = None) -> PolicyRun:
    config.validate()
    if stop_after_root_update is not None and stop_after_root_update not in config.checkpoint_root_updates:
        raise ValueError("interruption must be a declared checkpoint")
    configure_torch_topology_once(); torch = _torch()
    if prepared is None:
        prepared = prepare_fold_data(config, population, seed_id=seed_id, fold_id=fold_id)
    if (prepared.seed_id, prepared.fold_id) != (seed_id, fold_id): raise ValueError("prepared fold identity mismatch")
    root_rows, tail_rows, root_features, tail_features = prepared.root_rows, prepared.tail_rows, prepared.root_features, prepared.tail_features
    transforms = prepared.transforms if transforms is None else transforms
    if any(transforms[stage].to_bytes() != prepared.transforms[stage].to_bytes() for stage in ("root", "tail")): raise ValueError("prepared transform binding mismatch")
    transform_bytes = {stage: transforms[stage].to_bytes() for stage in ("root", "tail")}
    initialization = prepare_arm_initialization(prepared, arm_id) if initialization is None else initialization
    bundle = build_arm(arm_id, seed_id, fold_id, root_transform=transforms["root"], tail_transform=transforms["tail"], root_initial=initialization.root_initial, tail_initial=initialization.tail_initial)
    parity = initialization.parity
    checkpoint_root = Path(checkpoint_root)
    latest = _latest_checkpoint(checkpoint_root, config)
    if latest is None:
        root_update = tail_update = 0
        activity = _activity(len(root_rows), len(tail_rows))
        frozen_targets = None
    else:
        payload = load_checkpoint(latest)
        if payload["config"] != config.to_dict() or payload["binding"] != binding or (payload["arm_id"], payload["seed_id"], payload["fold_id"]) != (arm_id, seed_id, fold_id) or payload["transforms"] != transform_bytes:
            raise ValueError("cold-resume binding mismatch")
        _restore_bundle(payload, bundle)
        root_update, tail_update = payload["root_update"], payload["tail_updates"]
        frozen_targets, activity = payload["frozen_root_targets"], dict(payload["activity"])
    if event_callback:
        event_callback({"stage": "policy_start", "arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "resumed_root_update": root_update})
    tail_y = _tail_targets(tail_rows)
    while tail_update < config.tail_updates:
        indices = _cyclic_indices(len(tail_rows), tail_update, config.batch_size)
        norm, clipped = _step(bundle.tail, bundle.tail_optimizer, tail_features[indices], tail_y[indices])
        tail_update += 1
        activity["tail_optimizer_updates"] += 1; activity["tail_example_exposures"] += config.batch_size
        activity["tail_gradient_norm_sum"] += norm; activity["tail_gradient_norm_max"] = max(activity["tail_gradient_norm_max"], norm); activity["tail_clip_events"] += int(clipped)
    if frozen_targets is None:
        frozen_targets = materialize_root_targets(root_rows, bundle.tail, transforms["tail"])
        activity["target_materialization_events"] += 1; activity["target_materialization_rows"] += len(root_rows)
    while root_update < config.root_updates:
        indices = _cyclic_indices(len(root_rows), root_update, config.batch_size)
        norm, clipped = _step(bundle.root, bundle.root_optimizer, root_features[indices], frozen_targets[indices])
        root_update += 1
        activity["root_optimizer_updates"] += 1; activity["root_example_exposures"] += config.batch_size
        activity["root_gradient_norm_sum"] += norm; activity["root_gradient_norm_max"] = max(activity["root_gradient_norm_max"], norm); activity["root_clip_events"] += int(clipped)
        if root_update in config.checkpoint_root_updates:
            record = save_snapshot_transaction(checkpoint_root / f"root-{root_update:04d}", config=config, binding=binding, arm_id=arm_id, seed_id=seed_id, fold_id=fold_id, root_update=root_update, tail_updates=tail_update, root=bundle.root, tail=bundle.tail, root_optimizer=bundle.root_optimizer, tail_optimizer=bundle.tail_optimizer, frozen_root_targets=frozen_targets, transforms=transform_bytes, activity=activity)
            if event_callback: event_callback({"stage": "checkpoint", "arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "root_update": root_update})
            if stop_after_root_update == root_update:
                break
    paths = tuple({"arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "root_update": update, "full_path": str(checkpoint_root / f"root-{update:04d}.full.pt"), "projection_path": str(checkpoint_root / f"root-{update:04d}.eval.pt"), "binding_path": str(checkpoint_root / f"root-{update:04d}.binding.json")} for update in config.checkpoint_root_updates if update <= root_update)
    if any(not all(Path(record[key]).is_file() for key in ("full_path", "projection_path", "binding_path")) for record in paths):
        raise ValueError("checkpoint cadence incomplete")
    return PolicyRun(arm_id, seed_id, fold_id, activity, paths, transform_bytes, parity)
