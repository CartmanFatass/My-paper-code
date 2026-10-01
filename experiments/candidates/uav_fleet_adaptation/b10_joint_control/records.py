"""Compact evidence and exact model/optimizer state identity."""
import hashlib
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json


def add(counts, key, amount=1):
    counts[key] = counts.get(key, 0) + amount


def artifact(path, root):
    return dict(file_identity(path), path=str(Path(path).relative_to(root)))


def state_copy(model):
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}


def movement(before, after):
    if set(before) != set(after):
        raise ValueError("parameter sets changed")
    start = torch.cat([before[key].reshape(-1).double() for key in sorted(before)])
    finish = torch.cat([after[key].reshape(-1).double() for key in sorted(after)])
    delta = finish - start
    return dict(parameters=start.numel(), initial_norm=float(start.norm()), final_norm=float(finish.norm()),
                l2=float(delta.norm()), max_abs=float(delta.abs().max()),
                nonzero_parameters=int(torch.count_nonzero(delta)),
                relative_l2=float(delta.norm() / (start.norm() + 1e-12)))


def nested_digest(value):
    digest = hashlib.sha256()
    def visit(item):
        if isinstance(item, torch.Tensor):
            array = item.detach().cpu().contiguous().numpy()
            digest.update(b"tensor" + str(array.dtype).encode() + repr(array.shape).encode() + array.tobytes())
        elif isinstance(item, np.ndarray):
            digest.update(b"array" + str(item.dtype).encode() + repr(item.shape).encode() + item.tobytes(order="C"))
        elif isinstance(item, dict):
            digest.update(b"dict")
            for key in sorted(item, key=repr):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            digest.update(type(item).__name__.encode())
            for part in item:
                visit(part)
        else:
            digest.update((type(item).__name__ + ":" + repr(item)).encode())
    visit(value)
    return digest.hexdigest()
