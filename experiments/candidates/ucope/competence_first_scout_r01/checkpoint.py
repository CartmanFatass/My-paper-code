"""Atomic, create-once, cold-resumable policy checkpoints."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
import hashlib
import os
import shutil
import tempfile

from .contract import OBJECT_ID, SCHEMA_VERSION, RunBinding, ScoutConfig
from .model import build_arm, optimizer_for, validate_arm
from .rng import rng_contract

FORMAT = "UCOPE_SCOUT_R01_POLICY_CHECKPOINT_V1"
INVENTORY_FORMAT = "UCOPE_SCOUT_R01_CHECKPOINT_INVENTORY_V1"
FORBIDDEN_OUTCOME_FIELDS = frozenset({
    "evaluations", "scores", "regret", "competence", "acquisition", "returns",
    "root_actions", "tail_agreement", "gates", "polarity",
})
CHECKPOINT_ACTIVITY_FIELDS = frozenset({
    "root_inventory", "tail_inventory", "root_optimizer_updates", "tail_optimizer_updates",
    "root_example_exposures", "tail_example_exposures", "target_refresh_events", "target_refresh_rows",
    "target_materialization_events", "target_materialization_rows", "root_clipping_events",
    "tail_clipping_events", "root_gradient_norm_sum", "tail_gradient_norm_sum", "root_gradient_norm_max",
    "tail_gradient_norm_max", "nonfinite_events",
})


def _torch():
    import torch
    return torch


def make_checkpoint(
    *,
    config: ScoutConfig,
    run_binding: RunBinding,
    arm_id: str,
    seed_id: str,
    fold_id: int,
    root,
    tail,
    root_optimizer,
    tail_optimizer,
    root_updates: int,
    tail_updates: int,
    activity: Mapping[str, Any],
    frozen_root_targets=None,
) -> dict[str, Any]:
    value = {
        "format": FORMAT,
        "schema_version": SCHEMA_VERSION,
        "object_id": OBJECT_ID,
        "config": config.to_dict(),
        "run_binding": run_binding.validate(config.mode).to_dict(),
        "arm_id": arm_id,
        "seed_id": seed_id,
        "fold_id": fold_id,
        "root_updates": root_updates,
        "tail_updates": tail_updates,
        "activity": {key: deepcopy(activity[key]) for key in CHECKPOINT_ACTIVITY_FIELDS},
        "rng": rng_contract(),
        "root_state": {name: tensor.detach().cpu().clone() for name, tensor in root.state_dict().items()},
        "tail_state": {name: tensor.detach().cpu().clone() for name, tensor in tail.state_dict().items()},
        "root_optimizer_state": deepcopy(root_optimizer.state_dict()),
        "tail_optimizer_state": deepcopy(tail_optimizer.state_dict()),
        "frozen_root_targets": None if frozen_root_targets is None else frozen_root_targets.detach().cpu().clone(),
    }
    return validate_checkpoint(value)


def validate_checkpoint(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "format", "schema_version", "object_id", "config", "run_binding", "arm_id", "seed_id", "fold_id",
        "root_updates", "tail_updates", "activity", "rng", "root_state", "tail_state",
        "root_optimizer_state", "tail_optimizer_state", "frozen_root_targets",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("checkpoint field inventory mismatch")
    _reject_outcome_fields(value)
    config = ScoutConfig.from_dict(value["config"])
    RunBinding.from_value(value["run_binding"], config.mode)
    if value["format"] != FORMAT or value["schema_version"] != SCHEMA_VERSION or value["object_id"] != OBJECT_ID:
        raise ValueError("checkpoint identity mismatch")
    if value["arm_id"] not in config.arms or value["seed_id"] not in config.seed_ids or value["fold_id"] not in (0, 1):
        raise ValueError("checkpoint run binding mismatch")
    if type(value["root_updates"]) is not int or type(value["tail_updates"]) is not int:
        raise ValueError("checkpoint progress must use exact integers")
    if not (0 <= value["root_updates"] <= config.root_updates and 0 <= value["tail_updates"] <= config.tail_updates):
        raise ValueError("checkpoint progress outside workload")
    if value["root_updates"] not in config.evaluation_root_updates:
        raise ValueError("checkpoint may exist only at an evaluation root")
    if value["rng"] != rng_contract() or not isinstance(value["activity"], Mapping):
        raise ValueError("checkpoint RNG/activity structure mismatch")
    _validate_checkpoint_activity(value, config)
    torch = _torch()
    flexible = value["arm_id"].endswith("FLEX")
    probe_root, probe_tail = build_arm(value["arm_id"], value["seed_id"], value["fold_id"])
    for name, state, probe in (("root", value["root_state"], probe_root), ("tail", value["tail_state"], probe_tail)):
        if not isinstance(state, Mapping) or set(state) != set(probe.state_dict()):
            raise ValueError(f"checkpoint {name} tensor inventory mismatch")
        for key, tensor in state.items():
            if not isinstance(tensor, torch.Tensor) or tensor.dtype != torch.float32 or tuple(tensor.shape) != tuple(probe.state_dict()[key].shape) or not torch.isfinite(tensor).all().item():
                raise ValueError(f"invalid checkpoint tensor: {name}.{key}")
    for name in ("root_optimizer_state", "tail_optimizer_state"):
        state = value[name]
        if not isinstance(state, Mapping) or set(state) != {"state", "param_groups"}:
            raise ValueError("optimizer checkpoint structure mismatch")
        for item in state["state"].values():
            for tensor in item.values():
                if isinstance(tensor, torch.Tensor) and not torch.isfinite(tensor).all().item():
                    raise ValueError("nonfinite optimizer state")
    targets = value["frozen_root_targets"]
    if value["arm_id"].startswith("FT-"):
        if not isinstance(targets, torch.Tensor) or targets.dtype != torch.float32 or tuple(targets.shape) != (config.episodes_per_context * 4,) or not torch.isfinite(targets).all().item():
            raise ValueError("frozen-target checkpoint lacks materialized FP32 targets")
    elif targets is not None:
        raise ValueError("moving-target checkpoint must not contain materialized targets")
    validate_arm(probe_root, probe_tail, flexible=flexible)
    for prefix, scorer, optimizer_state, expected_steps in (
        ("root", probe_root, value["root_optimizer_state"], value["root_updates"]),
        ("tail", probe_tail, value["tail_optimizer_state"], value["tail_updates"]),
    ):
        parameters = list(scorer.parameters())
        group = optimizer_state["param_groups"]
        if len(group) != 1 or group[0].get("params") != list(range(len(parameters))):
            raise ValueError(f"{prefix} optimizer parameter inventory mismatch")
        expected_hyper = {"lr": 3e-4, "betas": (0.9, 0.999), "eps": 1e-8, "weight_decay": 0.0}
        if any(group[0].get(key) != item for key, item in expected_hyper.items()):
            raise ValueError(f"{prefix} optimizer hyperparameter drift")
        state = optimizer_state["state"]
        if expected_steps == 0 and state:
            raise ValueError(f"zero-update {prefix} optimizer has state")
        if expected_steps and set(state) != set(range(len(parameters))):
            raise ValueError(f"updated {prefix} optimizer state incomplete")
        for index, parameter in enumerate(parameters):
            if not expected_steps:
                continue
            item = state[index]
            if set(item) != {"step", "exp_avg", "exp_avg_sq"}:
                raise ValueError(f"{prefix} optimizer moment field drift")
            step = item["step"]
            if not isinstance(step, torch.Tensor) or step.numel() != 1 or float(step.item()) != expected_steps:
                raise ValueError(f"{prefix} optimizer step/progress mismatch")
            for moment_name in ("exp_avg", "exp_avg_sq"):
                moment = item[moment_name]
                if not isinstance(moment, torch.Tensor) or moment.dtype != torch.float32 or tuple(moment.shape) != tuple(parameter.shape) or not torch.isfinite(moment).all().item():
                    raise ValueError(f"{prefix} optimizer moment shape/dtype mismatch")
    return dict(value)


def _reject_outcome_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_OUTCOME_FIELDS:
                raise ValueError("scientific outcome field is forbidden from checkpoint resume state")
            _reject_outcome_fields(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_outcome_fields(item)


def _probe_refresh_rows(config: ScoutConfig, fold_id: int, root_updates: int) -> int:
    """Exact PROBE rows visited by the canonical cyclic root batches."""
    from .host import behavior_stratum, group_fold

    episode_indices = [index for index in range(config.episodes_per_context) if group_fold(index) == fold_id]
    probe_flags = tuple(behavior_stratum(index)[0] == "PROBE" for index in episode_indices for _context in range(8))
    return sum(
        probe_flags[(update * config.batch_size + offset) % len(probe_flags)]
        for update in range(root_updates)
        for offset in range(config.batch_size)
    )


def expected_policy_activity(config: ScoutConfig, arm_id: str, fold_id: int, root_updates: int, tail_updates: int) -> dict[str, int]:
    if arm_id not in config.arms or fold_id not in (0, 1):
        raise ValueError("policy activity identity mismatch")
    checkpoint_count = sum(update <= root_updates for update in config.evaluation_root_updates)
    frozen = arm_id.startswith("FT-")
    return {
        "root_inventory": config.episodes_per_context * 4,
        "tail_inventory": config.episodes_per_context * 2,
        "root_optimizer_updates": root_updates,
        "tail_optimizer_updates": tail_updates,
        "root_example_exposures": root_updates * config.batch_size,
        "tail_example_exposures": tail_updates * config.batch_size,
        "target_refresh_events": root_updates if arm_id == "MT-XF-FLEX" else 0,
        "target_refresh_rows": _probe_refresh_rows(config, fold_id, root_updates) if arm_id == "MT-XF-FLEX" else 0,
        "target_materialization_events": int(frozen),
        "target_materialization_rows": config.episodes_per_context * 4 if frozen else 0,
        "nonfinite_events": 0,
        "exact_policy_evaluations": checkpoint_count * 8,
        "sampled_evaluation_episodes": checkpoint_count * 8 * config.sampled_evaluation_episodes,
    }


def _validate_checkpoint_activity(value: Mapping[str, Any], config: ScoutConfig) -> None:
    activity = value["activity"]
    if set(activity) != CHECKPOINT_ACTIVITY_FIELDS:
        raise ValueError("checkpoint activity field inventory mismatch")
    expected_tail = value["root_updates"] // 2 if value["arm_id"] == "MT-XF-FLEX" else config.tail_updates
    if value["tail_updates"] != expected_tail:
        raise ValueError("checkpoint root/tail clock mismatch")
    expected = expected_policy_activity(config, value["arm_id"], value["fold_id"], value["root_updates"], value["tail_updates"])
    # Curve audits are reconstructed from the outcome-free checkpoints after training. They are
    # deliberately never serialized in resume state, including ASSESS crash state.
    expected.pop("exact_policy_evaluations")
    expected.pop("sampled_evaluation_episodes")
    if any(activity.get(field) != item for field, item in expected.items()):
        raise ValueError("checkpoint activity/progress ledger mismatch")
    for prefix, updates in (("root", value["root_updates"]), ("tail", value["tail_updates"])):
        clipping = activity.get(f"{prefix}_clipping_events")
        norm_sum = activity.get(f"{prefix}_gradient_norm_sum")
        norm_max = activity.get(f"{prefix}_gradient_norm_max")
        if type(clipping) is not int or not 0 <= clipping <= updates:
            raise ValueError("checkpoint clipping count mismatch")
        if not isinstance(norm_sum, (int, float)) or not isinstance(norm_max, (int, float)) or not (0 <= norm_max <= norm_sum):
            raise ValueError("checkpoint gradient-norm ledger mismatch")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_locator(path: Path, complete_root: Path) -> str:
    resolved = path.resolve()
    root = complete_root.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("checkpoint is outside the final complete root") from exc
    if not relative.parts or ".." in relative.parts:
        raise ValueError("checkpoint locator must be a nonempty relative final locator")
    return relative.as_posix()


def build_checkpoint_inventory(config: ScoutConfig, checkpoint_paths, *, complete_root: str | Path, run_binding: RunBinding | Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    config.validate()
    root = Path(complete_root)
    expected_binding = RunBinding.from_value(run_binding, config.mode).to_dict() if run_binding is not None else None
    records = []
    for path_value in checkpoint_paths:
        path = Path(path_value)
        payload = load_checkpoint(path)
        if payload["config"] != config.to_dict():
            raise ValueError("checkpoint inventory configuration mismatch")
        if expected_binding is None:
            expected_binding = payload["run_binding"]
        if payload["run_binding"] != expected_binding:
            raise ValueError("checkpoint inventory run-binding mismatch")
        records.append({
            "format": INVENTORY_FORMAT,
            "arm_id": payload["arm_id"],
            "seed_id": payload["seed_id"],
            "fold_id": payload["fold_id"],
            "root_update": payload["root_updates"],
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "locator": _relative_locator(path, root),
        })
    return validate_checkpoint_inventory(records, config=config, artifact_root=root, run_binding=expected_binding)


def stage_checkpoint_inventory(config: ScoutConfig, source_paths, *, staging_root: str | Path, run_binding: RunBinding | Mapping[str, Any]) -> list[dict[str, Any]]:
    """Create the fixed complete/checkpoints tree and return relative content inventory."""
    config.validate()
    root = Path(staging_root)
    expected_binding = RunBinding.from_value(run_binding, config.mode).to_dict()
    sources = []
    identities = set()
    for source_value in source_paths:
        source = Path(source_value)
        payload = load_checkpoint(source)
        if payload["config"] != config.to_dict() or payload["run_binding"] != expected_binding:
            raise ValueError("staged checkpoint configuration mismatch")
        identity = (payload["arm_id"], payload["seed_id"], payload["fold_id"], payload["root_updates"])
        if identity in identities:
            raise ValueError("duplicate staged checkpoint identity")
        identities.add(identity)
        destination = root / "checkpoints" / payload["arm_id"] / payload["seed_id"] / f"fold-{payload['fold_id']}" / f"root-{payload['root_updates']:04d}.pt"
        sources.append((source, destination))
    expected = {(arm, seed, fold, update) for arm in config.arms for seed in config.seed_ids for fold in (0, 1) for update in config.evaluation_root_updates}
    if identities != expected:
        raise ValueError("staged checkpoint sources are not the exact frozen inventory")
    staged = []
    for source, destination in sources:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise FileExistsError(f"staged checkpoint is create-once: {destination}")
        try:
            os.link(source, destination)
        except OSError:
            with source.open("rb") as source_stream, destination.open("xb") as destination_stream:
                shutil.copyfileobj(source_stream, destination_stream, length=1024 * 1024)
                destination_stream.flush()
                os.fsync(destination_stream.fileno())
        staged.append(destination)
    return build_checkpoint_inventory(config, staged, complete_root=root, run_binding=expected_binding)


def validate_checkpoint_inventory(records, *, config: ScoutConfig, artifact_root: str | Path | None = None, run_binding: RunBinding | Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    config.validate()
    required = {"format", "arm_id", "seed_id", "fold_id", "root_update", "size_bytes", "sha256", "locator"}
    expected_binding = RunBinding.from_value(run_binding, config.mode).to_dict() if run_binding is not None else None
    expected = {(arm, seed, fold, update) for arm in config.arms for seed in config.seed_ids for fold in (0, 1) for update in config.evaluation_root_updates}
    values = []
    identities = set()
    locators = set()
    for record in records:
        if not isinstance(record, Mapping) or set(record) != required or record["format"] != INVENTORY_FORMAT:
            raise ValueError("checkpoint inventory record structure mismatch")
        identity = (record["arm_id"], record["seed_id"], record["fold_id"], record["root_update"])
        if identity not in expected or identity in identities:
            raise ValueError("checkpoint inventory identity mismatch or duplicate")
        if type(record["size_bytes"]) is not int or record["size_bytes"] <= 0 or type(record["sha256"]) is not str or len(record["sha256"]) != 64 or any(character not in "0123456789abcdef" for character in record["sha256"]):
            raise ValueError("checkpoint inventory size/digest mismatch")
        locator = record["locator"]
        locator_path = Path(locator)
        if type(locator) is not str or "\\" in locator or locator_path.is_absolute() or not locator_path.parts or ".." in locator_path.parts or locator in locators:
            raise ValueError("checkpoint inventory locator must be unique and relative")
        identities.add(identity); locators.add(locator); values.append(dict(record))
        if artifact_root is not None:
            path = Path(artifact_root) / locator_path
            if path.is_symlink() or not path.is_file() or path.stat().st_size != record["size_bytes"] or _sha256(path) != record["sha256"]:
                raise ValueError("checkpoint inventory file/size/digest mismatch")
            payload = load_checkpoint(path)
            if payload["config"] != config.to_dict() or (payload["arm_id"], payload["seed_id"], payload["fold_id"], payload["root_updates"]) != identity:
                raise ValueError("checkpoint inventory payload identity/progress mismatch")
            if expected_binding is not None and payload["run_binding"] != expected_binding:
                raise ValueError("checkpoint inventory payload run-binding mismatch")
    if identities != expected:
        raise ValueError("checkpoint inventory is not the exact frozen combination")
    return sorted(values, key=lambda row: (config.arms.index(row["arm_id"]), config.seed_ids.index(row["seed_id"]), row["fold_id"], row["root_update"]))


def save_checkpoint(path: str | Path, value: Mapping[str, Any]) -> Path:
    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"checkpoint is create-once: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = validate_checkpoint(value)
    handle, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(handle)
    try:
        _torch().save(payload, temporary)
        with open(temporary, "r+b") as stream:
            os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return destination


def load_checkpoint(path: str | Path):
    torch = _torch()
    try:
        value = torch.load(Path(path), map_location="cpu", weights_only=False)
    except TypeError:  # pragma: no cover - old torch
        value = torch.load(Path(path), map_location="cpu")
    return validate_checkpoint(value)


def restore_checkpoint(value: Mapping[str, Any]):
    value = validate_checkpoint(value)
    root, tail = build_arm(value["arm_id"], value["seed_id"], value["fold_id"])
    root_optimizer, tail_optimizer = optimizer_for(root), optimizer_for(tail)
    root.load_state_dict(value["root_state"], strict=True)
    tail.load_state_dict(value["tail_state"], strict=True)
    root_optimizer.load_state_dict(value["root_optimizer_state"])
    tail_optimizer.load_state_dict(value["tail_optimizer_state"])
    return root, tail, root_optimizer, tail_optimizer
