from __future__ import annotations

import os
import time
from pathlib import Path

import torch

from .config import CANDIDATE, RESULT_OBJECT, REVISION


def atomic_save(path: Path, value: dict[str, object]) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(target) + f".{os.getpid()}.{time.time_ns()}.tmp")
    with temporary.open("xb") as stream:
        torch.save(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)


def load(path: Path) -> dict[str, object]:
    value = torch.load(path.resolve(), map_location="cpu", weights_only=False)
    if not isinstance(value, dict) or value.get("candidate") != CANDIDATE \
            or value.get("result_object") != RESULT_OBJECT \
            or value.get("revision") != REVISION:
        raise RuntimeError("frontier identity does not match exact SRF r03 factorial")
    if value.get("partial_inspection_permitted") is not False:
        raise RuntimeError("frontier is not the blinded atomic SRF r03 format")
    return value


def model_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }
