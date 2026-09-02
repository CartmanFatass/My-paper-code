"""Create-once bound checkpoints and cold-resume restoration."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
import hashlib
import math
import os
import tempfile

from .contract import OBJECT_ID, SCHEMA_VERSION, WorkloadConfig
from .model import build_arm
from .conditioning import TransformRecord

FORMAT = "UCOPE_BC_CONDITIONING_R01_CHECKPOINT_V1"
PROJECTION_FORMAT = "UCOPE_BC_CONDITIONING_R01_EVALUATION_PROJECTION_V1"
SNAPSHOT_BINDING_FORMAT = "UCOPE_BC_CONDITIONING_R01_SNAPSHOT_BINDING_V1"
FORBIDDEN_FIELDS = {"evaluation", "scores", "regret", "competence", "near", "dominance", "branch", "returns"}


def _torch():
    import torch
    return torch


def _reject_outcomes(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_FIELDS:
                raise ValueError("outcome field forbidden from resume checkpoint")
            _reject_outcomes(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_outcomes(item)


def make_checkpoint(*, config: WorkloadConfig, binding: str, arm_id: str, seed_id: str, fold_id: int, root_update: int, tail_updates: int, root, tail, root_optimizer, tail_optimizer, frozen_root_targets, transforms: Mapping[str, bytes], activity: Mapping[str, Any], evaluation_projection_sha256: str) -> dict[str, Any]:
    value = {
        "format": FORMAT, "schema_version": SCHEMA_VERSION, "object_id": OBJECT_ID,
        "config": config.to_dict(), "binding": binding, "arm_id": arm_id, "seed_id": seed_id,
        "fold_id": fold_id, "root_update": root_update, "tail_updates": tail_updates,
        "root_state": {key: tensor.detach().cpu().clone() for key, tensor in root.state_dict().items()},
        "tail_state": {key: tensor.detach().cpu().clone() for key, tensor in tail.state_dict().items()},
        "root_optimizer": deepcopy(root_optimizer.state_dict()), "tail_optimizer": deepcopy(tail_optimizer.state_dict()),
        "frozen_root_targets": frozen_root_targets.detach().cpu().clone(),
        "transforms": dict(transforms), "activity": dict(activity), "evaluation_projection_sha256": evaluation_projection_sha256,
    }
    return validate_checkpoint(value)


def validate_checkpoint(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {"format", "schema_version", "object_id", "config", "binding", "arm_id", "seed_id", "fold_id", "root_update", "tail_updates", "root_state", "tail_state", "root_optimizer", "tail_optimizer", "frozen_root_targets", "transforms", "activity", "evaluation_projection_sha256"}
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("checkpoint field inventory mismatch")
    _reject_outcomes(value)
    config = WorkloadConfig.from_dict(value["config"])
    if value["format"] != FORMAT or value["object_id"] != OBJECT_ID or value["schema_version"] != SCHEMA_VERSION:
        raise ValueError("checkpoint identity mismatch")
    if value["arm_id"] not in config.arms or value["seed_id"] not in config.seed_ids or value["fold_id"] not in (0, 1):
        raise ValueError("checkpoint workload binding mismatch")
    if type(value["binding"]) is not str or len(value["binding"]) != 64 or any(character not in "0123456789abcdef" for character in value["binding"]):
        raise ValueError("checkpoint binding digest mismatch")
    if type(value["evaluation_projection_sha256"]) is not str or len(value["evaluation_projection_sha256"]) != 64 or any(character not in "0123456789abcdef" for character in value["evaluation_projection_sha256"]): raise ValueError("checkpoint projection digest mismatch")
    if value["root_update"] not in config.checkpoint_root_updates or value["tail_updates"] != config.tail_updates:
        raise ValueError("checkpoint progress mismatch")
    torch = _torch()
    if not isinstance(value["frozen_root_targets"], torch.Tensor) or value["frozen_root_targets"].dtype != torch.float32 or tuple(value["frozen_root_targets"].shape) != (config.episodes_per_context * 4,) or not torch.isfinite(value["frozen_root_targets"]).all().item():
        raise ValueError("checkpoint root-target inventory mismatch")
    if set(value["transforms"]) != {"root", "tail"} or any(type(item) is not bytes for item in value["transforms"].values()):
        raise ValueError("checkpoint transform binding mismatch")
    for stage in ("root", "tail"):
        record = TransformRecord.from_bytes(value["transforms"][stage])
        expected_rows = config.episodes_per_context * (4 if stage == "root" else 2)
        if record.stage != stage or record.row_count != expected_rows:
            raise ValueError("checkpoint transform row/stage mismatch")
    for state, dim in ((value["root_state"], 7), (value["tail_state"], 5)):
        if set(state) != {"beta"} or state["beta"].dtype != torch.float32 or tuple(state["beta"].shape) != (dim,) or not torch.isfinite(state["beta"]).all().item():
            raise ValueError("checkpoint scorer state mismatch")
    for optimizer, expected, dim in ((value["root_optimizer"], value["root_update"], 7), (value["tail_optimizer"], value["tail_updates"], 5)):
        if set(optimizer) != {"state", "param_groups"} or set(optimizer["state"]) != {0}:
            raise ValueError("checkpoint optimizer state mismatch")
        if len(optimizer["param_groups"]) != 1 or optimizer["param_groups"][0].get("params") != [0]: raise ValueError("checkpoint optimizer parameter inventory mismatch")
        group = optimizer["param_groups"][0]
        for key, expected_value in {"lr": 3e-4, "betas": (0.9, 0.999), "eps": 1e-8, "weight_decay": 0.0}.items():
            if group.get(key) != expected_value: raise ValueError("checkpoint optimizer hyperparameter mismatch")
        item = optimizer["state"][0]
        if set(item) != {"step", "exp_avg", "exp_avg_sq"} or not isinstance(item["step"], torch.Tensor) or item["step"].numel() != 1 or float(item["step"].item()) != expected:
            raise ValueError("checkpoint optimizer step/precision mismatch")
        for moment in (item["exp_avg"], item["exp_avg_sq"]):
            if not isinstance(moment, torch.Tensor) or moment.dtype != torch.float32 or tuple(moment.shape) != (dim,) or not torch.isfinite(moment).all().item(): raise ValueError("checkpoint optimizer moment mismatch")
    activity = value["activity"]
    required_activity = {"root_inventory", "tail_inventory", "root_optimizer_updates", "tail_optimizer_updates", "root_example_exposures", "tail_example_exposures", "target_materialization_events", "target_materialization_rows", "root_gradient_norm_sum", "tail_gradient_norm_sum", "root_gradient_norm_max", "tail_gradient_norm_max", "root_clip_events", "tail_clip_events", "nonfinite_events"}
    if not isinstance(activity, Mapping) or set(activity) != required_activity: raise ValueError("checkpoint activity inventory mismatch")
    expected_frontier = {"root_inventory": config.episodes_per_context * 4, "tail_inventory": config.episodes_per_context * 2, "root_optimizer_updates": value["root_update"], "tail_optimizer_updates": config.tail_updates, "root_example_exposures": value["root_update"] * config.batch_size, "tail_example_exposures": config.tail_updates * config.batch_size, "target_materialization_events": 1, "target_materialization_rows": config.episodes_per_context * 4, "nonfinite_events": 0}
    if any(activity.get(key) != expected_value for key, expected_value in expected_frontier.items()): raise ValueError("checkpoint activity frontier mismatch")
    for prefix, updates in (("root", value["root_update"]), ("tail", config.tail_updates)):
        if type(activity[f"{prefix}_clip_events"]) is not int or not 0 <= activity[f"{prefix}_clip_events"] <= updates: raise ValueError("checkpoint clipping count mismatch")
        values = (activity[f"{prefix}_gradient_norm_sum"], activity[f"{prefix}_gradient_norm_max"])
        if any(not isinstance(item, (int, float)) or not math.isfinite(item) for item in values) or not 0 <= values[1] <= values[0]: raise ValueError("checkpoint gradient telemetry mismatch")
    return dict(value)


def save_checkpoint(path: str | Path, value: Mapping[str, Any]) -> Path:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"checkpoint is create-once: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(handle)
    try:
        _torch().save(validate_checkpoint(value), temporary)
        os.link(temporary, destination)
    finally:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
    return destination


def load_checkpoint(path: str | Path) -> dict[str, Any]:
    return validate_checkpoint(_torch().load(Path(path), map_location="cpu", weights_only=False))


def file_record(path: str | Path) -> dict[str, Any]:
    item = Path(path)
    return {"size_bytes": item.stat().st_size, "sha256": hashlib.sha256(item.read_bytes()).hexdigest()}


def make_evaluation_projection(*, config, binding, arm_id, seed_id, fold_id, root_update, root, tail, transforms):
    value = {"format": PROJECTION_FORMAT, "schema_version": SCHEMA_VERSION, "object_id": OBJECT_ID, "config": config.to_dict(), "binding": binding, "arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "root_update": root_update, "root_state": {k: v.detach().cpu().clone() for k, v in root.state_dict().items()}, "tail_state": {k: v.detach().cpu().clone() for k, v in tail.state_dict().items()}, "transforms": dict(transforms)}
    return validate_evaluation_projection(value)


def validate_evaluation_projection(value):
    required = {"format", "schema_version", "object_id", "config", "binding", "arm_id", "seed_id", "fold_id", "root_update", "root_state", "tail_state", "transforms"}
    if not isinstance(value, Mapping) or set(value) != required or value.get("format") != PROJECTION_FORMAT or value.get("object_id") != OBJECT_ID: raise ValueError("evaluation projection schema mismatch")
    config = WorkloadConfig.from_dict(value["config"]); torch = _torch()
    if value["arm_id"] not in config.arms or value["seed_id"] not in config.seed_ids or value["fold_id"] not in (0, 1) or value["root_update"] not in config.checkpoint_root_updates: raise ValueError("evaluation projection identity mismatch")
    if set(value["transforms"]) != {"root", "tail"}: raise ValueError("evaluation projection transform inventory mismatch")
    for stage, dim in (("root", 7), ("tail", 5)):
        TransformRecord.from_bytes(value["transforms"][stage]); state = value[f"{stage}_state"]
        if set(state) != {"beta"} or state["beta"].dtype != torch.float32 or tuple(state["beta"].shape) != (dim,) or not torch.isfinite(state["beta"]).all().item(): raise ValueError("evaluation projection scorer mismatch")
    return dict(value)


def load_evaluation_projection(path):
    path = Path(path)
    if not path.name.endswith(".eval.pt"): raise ValueError("evaluator may open only .eval.pt projection")
    return validate_evaluation_projection(_torch().load(path, map_location="cpu", weights_only=False))


def _atomic_json(path, value):
    import json
    destination = Path(path); destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists(): raise FileExistsError("snapshot binding is create-once")
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with destination.open("xb") as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())


def save_snapshot_transaction(base_path: str | Path, *, config, binding, arm_id, seed_id, fold_id, root_update, tail_updates, root, tail, root_optimizer, tail_optimizer, frozen_root_targets, transforms, activity):
    base = Path(base_path); full_path = base.with_suffix(".full.pt"); projection_path = base.with_suffix(".eval.pt"); binding_path = base.with_suffix(".binding.json")
    projection = make_evaluation_projection(config=config, binding=binding, arm_id=arm_id, seed_id=seed_id, fold_id=fold_id, root_update=root_update, root=root, tail=tail, transforms=transforms)
    save_checkpoint_projection(projection_path, projection); projection_record = file_record(projection_path)
    full = make_checkpoint(config=config, binding=binding, arm_id=arm_id, seed_id=seed_id, fold_id=fold_id, root_update=root_update, tail_updates=tail_updates, root=root, tail=tail, root_optimizer=root_optimizer, tail_optimizer=tail_optimizer, frozen_root_targets=frozen_root_targets, transforms=transforms, activity=activity, evaluation_projection_sha256=projection_record["sha256"])
    save_checkpoint(full_path, full); full_record = file_record(full_path)
    binding_value = {"format": SNAPSHOT_BINDING_FORMAT, "identity": [arm_id, seed_id, fold_id, root_update], "full": full_record, "projection": projection_record}
    _atomic_json(binding_path, binding_value); binding_record = file_record(binding_path)
    return {"arm_id": arm_id, "seed_id": seed_id, "fold_id": fold_id, "root_update": root_update, "full_path": str(full_path), "projection_path": str(projection_path), "binding_path": str(binding_path), "full": full_record, "projection": projection_record, "transaction_binding": binding_record}


def save_checkpoint_projection(path, value):
    destination = Path(path)
    if destination.exists(): raise FileExistsError("evaluation projection is create-once")
    destination.parent.mkdir(parents=True, exist_ok=True); _torch().save(validate_evaluation_projection(value), destination)
    return destination
