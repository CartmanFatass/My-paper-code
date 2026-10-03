"""Fixed 10,272-parameter B08 CPU scorer and exact state contract.

Affine row flattening is C order (world,candidate,entity[,neighbor]); each
encoder restores those axes before torch.mean. Training B=16, inference B=1.
Callers bind the CPU runtime and set the selected one numerical thread.
"""
import hashlib

import torch
from torch import nn
from torch.nn import functional as F

from .features import SHAPES

WIDTHS = {"u": (20, 32, 32), "y": (2, 16, 16), "uy": (9, 16, 16),
          "uu": (9, 16, 16), "update": (64, 32, 32), "readout": (97, 32, 32, 1)}
STATE_SHAPES = {}
for _name, _widths in WIDTHS.items():
    for _i, (_left, _right) in enumerate(zip(_widths, _widths[1:])):
        STATE_SHAPES[f"{_name}.{_i}.weight"] = (_right, _left)
        if (_name, _i) != ("readout", 2):
            STATE_SHAPES[f"{_name}.{_i}.bias"] = (_right,)


def validate_state(state):
    if set(state) != set(STATE_SHAPES):
        raise ValueError("B08 state keys differ")
    for key, shape in STATE_SHAPES.items():
        value = state[key]
        if (not isinstance(value, torch.Tensor) or value.dtype != torch.float32
                or value.device.type != "cpu" or tuple(value.shape) != shape
                or not value.is_contiguous() or not torch.isfinite(value).all()):
            raise ValueError(f"invalid CPU FP32 state tensor: {key}")


def validate_inputs(x):
    if set(x) != {*SHAPES, "valid"}:
        raise ValueError("B08 feature keys differ")
    batch = x["U"].shape[0]
    if batch not in (1, 16):
        raise ValueError("fixed B=1 inference or B=16 training required")
    for key, shape in SHAPES.items():
        value = x[key]
        if (value.dtype != torch.float32 or value.device.type != "cpu"
                or tuple(value.shape) != (batch, *shape) or not value.is_contiguous()
                or not torch.isfinite(value).all()):
            raise ValueError(f"invalid CPU FP32 feature: {key}")
    valid = x["valid"]
    if (valid.dtype != torch.bool or valid.device.type != "cpu" or valid.shape != (batch, 8)
            or not valid.is_contiguous() or not valid[:, 0].all()
            or (valid[:, 1:] & ~valid[:, :-1]).any()):
        raise ValueError("valid candidates must form a nonempty prefix")
    return batch


class Scorer(nn.Module):
    def __init__(self):
        super().__init__()
        for name, widths in WIDTHS.items():
            setattr(self, name, nn.ModuleList([
                nn.Linear(left, right, bias=(name, i) != ("readout", 2),
                          device="cpu", dtype=torch.float32)
                for i, (left, right) in enumerate(zip(widths, widths[1:]))]))

    def _encode(self, x, name):
        shape = x.shape[:-1]
        x = x.reshape(-1, x.shape[-1])
        layers = getattr(self, name)
        for i, layer in enumerate(layers):
            x = F.linear(x, layer.weight, layer.bias)
            if (name, i) != ("readout", 2):
                x = F.relu(x)
        return x.reshape(*shape, x.shape[-1])

    def forward(self, x):
        validate_inputs(x)
        u, y = self._encode(x["U"], "u"), self._encode(x["Y"], "y")
        uy = self._encode(x["E_UY"], "uy").mean(dim=3)
        uu = self._encode(x["E_UU"], "uu").mean(dim=3)
        updated = F.relu(u + self._encode(torch.cat((u, uy, uu), dim=-1), "update"))
        selected = (updated * x["U"][..., 19:20]).sum(dim=2)
        readout = torch.cat((updated.mean(dim=2), selected, y.mean(dim=2), x["S"]), dim=-1)
        return self._encode(readout, "readout").squeeze(-1)


def build(seed):
    """Default Linear resets in declared layer order; restore caller CPU RNG."""
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(int(seed))
        result = Scorer()
    assert sum(p.numel() for p in result.parameters()) == 10272
    return result


def clone_state(module):
    return {key: value.detach().clone().contiguous() for key, value in module.state_dict().items()}


def state_digest(state):
    validate_state(state)
    digest = hashlib.sha256()
    for key in STATE_SHAPES:
        digest.update(key.encode("ascii") + b"\0")
        digest.update(state[key].detach().numpy().astype("<f4", copy=False).tobytes())
    return digest.hexdigest()


def parameter_movement(initial, final):
    validate_state(initial); validate_state(final)
    delta = torch.cat([(final[k].double() - initial[k].double()).flatten() for k in STATE_SHAPES])
    return {"l2": float(torch.linalg.vector_norm(delta)), "max_abs": float(delta.abs().max()),
            "changed_parameters": int(torch.count_nonzero(delta)),
            "initial_digest": state_digest(initial), "final_digest": state_digest(final)}
