from __future__ import annotations

import os
import time
import copy
from collections.abc import Mapping, Sequence
from pathlib import Path

import torch

from .config import CANDIDATE, REVISION


def atomic_save(path: Path, value: dict[str, object]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("xb") as stream:
        torch.save(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def load(path: Path) -> dict[str, object]:
    value = torch.load(path.resolve(), map_location="cpu", weights_only=False)
    if not isinstance(value, dict) or value.get("candidate") != CANDIDATE \
            or value.get("revision") != REVISION:
        raise RuntimeError("frontier identity does not match exact B3 revision")
    if value.get("partial_selection_permitted") is not False:
        raise RuntimeError("frontier is not the blinded nonselectable B3 format")
    return value


def model_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def _snapshot_value(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {copy.deepcopy(key): _snapshot_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_snapshot_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_snapshot_value(item) for item in value)
    return copy.deepcopy(value)


def optimizer_state(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    """Detached snapshot: later optimizer steps cannot mutate a frontier boundary."""
    value = _snapshot_value(optimizer.state_dict())
    if not isinstance(value, dict):
        raise RuntimeError("optimizer state snapshot must be a dictionary")
    return value


def active_seed_snapshot(*, algorithm_seed: int, next_update: int,
                         models: Mapping[str, torch.nn.Module],
                         optimizers: Mapping[str, torch.optim.Optimizer],
                         traces: Mapping[str, Sequence[dict[str, object]]],
                         final_losses: Mapping[str, dict[str, float]],
                         fixed_coefficients: Mapping[str, float]) -> dict[str, object]:
    arms = tuple(models)
    if tuple(optimizers) != arms or tuple(traces) != arms or tuple(final_losses) != arms \
            or tuple(fixed_coefficients) != arms:
        raise RuntimeError("active B3 seed snapshot requires identical fixed arm order")
    return {"algorithm_seed": algorithm_seed, "next_update": next_update,
            "arm_order": list(arms),
            "model_states": {arm: model_state(models[arm]) for arm in arms},
            "optimizer_states": {arm: optimizer_state(optimizers[arm]) for arm in arms},
            "gradient_traces": {arm: copy.deepcopy(list(traces[arm])) for arm in arms},
            "final_losses": {arm: copy.deepcopy(final_losses[arm]) for arm in arms},
            "fixed_coefficients": {arm: float(fixed_coefficients[arm]) for arm in arms},
            "boundary": "after_complete_three_arm_update"}
