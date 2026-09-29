"""Hash-bound frozen endpoint loading and residual-free constant deployment."""

import hashlib
import io
import time

import numpy as np
import torch
from torch import nn

from experiments.candidates.uav_message_content.b05 import model as retained


def tensor_hash(value):
    return hashlib.sha256(value.detach().cpu().numpy().tobytes()).hexdigest()


def state_hashes(actor):
    return {key: tensor_hash(value) for key, value in actor.state_dict().items()}


def group_hash(state, prefix):
    values = [value.flatten() for key, value in state.items() if key.startswith(prefix)]
    if not values:
        raise ValueError(f"missing tensor group {prefix}")
    return tensor_hash(torch.cat(values))


class ConstantActor(nn.Module):
    """The original base on actual history; no residual layers exist here."""
    def __init__(self, base, constant):
        super().__init__()
        self.base = base
        self.register_buffer("constant", torch.from_numpy(constant.copy()))
        self.duration = self.send = None
        self.requires_grad_(False).eval()

    @property
    def log_std(self):
        return self.base.log_std

    def components(self, observations, hidden):
        if observations.shape[-1] != 186:
            raise ValueError("fixed actor input size")
        base_mean, recurrent, next_hidden = self.base(observations[..., :171], hidden)
        correction = self.constant.expand_as(base_mean)
        return base_mean + correction, recurrent, next_hidden, base_mean, correction

    def forward(self, observations, hidden):
        return self.components(observations, hidden)[:3]


def bound_constant(asset):
    rounded = np.asarray(asset["constant_float64"], dtype=np.float64).astype(np.float32)
    specified = np.asarray(asset["constant_float32"], dtype=np.float64)
    if (rounded.shape != (3,) or not np.isfinite(rounded).all()
            or np.any(np.abs(rounded) > retained.CORRECTION_BOUND)
            or not np.array_equal(rounded.astype(np.float64), specified)):
        raise ValueError("constant rounding/bound mismatch")
    return rounded


def validate_endpoint(content, asset, parent):
    if hashlib.sha256(content).hexdigest() != asset["checkpoint"]["sha256"]:
        raise ValueError("endpoint checkpoint digest mismatch")
    state = torch.load(io.BytesIO(content), map_location="cpu", weights_only=True)
    fields = dict(arm="D", master=asset["master"], input_size=186, critic_size=526,
                  inherited_sha256=retained.SOURCE_SHA256, correction_bound=.10,
                  source_sha=asset["source_sha"])
    if not isinstance(state, dict) or any(state.get(k) != v for k, v in fields.items()):
        raise ValueError("endpoint checkpoint metadata mismatch")
    base_state = parent.state_dict()
    expected_actor = {f"base.{k}": tuple(v.shape) for k, v in base_state.items()}
    expected_actor.update({"residual_hidden.weight": (64, 250), "residual_hidden.bias": (64,),
                           "residual_output.weight": (3, 64), "residual_output.bias": (3,)})
    expected_critic = {"network.0.weight": (128, 451), "network.0.bias": (128,),
                       "network.2.weight": (128, 128), "network.2.bias": (128,),
                       "network.4.weight": (1, 128), "network.4.bias": (1,),
                       "forecast_projection.weight": (128, 75)}
    for name, expected in (("actor", expected_actor), ("critic", expected_critic)):
        values = state.get(name)
        if not isinstance(values, dict) or set(values) != set(expected):
            raise ValueError(f"endpoint {name} keys mismatch")
        for key, shape in expected.items():
            value = values[key]
            if (not isinstance(value, torch.Tensor) or tuple(value.shape) != shape
                    or value.dtype != torch.float32 or not torch.isfinite(value).all()):
                raise ValueError(f"endpoint tensor contract mismatch: {key}")
    for key, value in base_state.items():
        if not torch.equal(state["actor"][f"base.{key}"], value):
            raise ValueError(f"endpoint frozen base differs from parent: {key}")
    hashes = {"base_actor": group_hash(state["actor"], "base."),
              "residual_hidden": group_hash(state["actor"], "residual_hidden."),
              "residual_output": group_hash(state["actor"], "residual_output."),
              "critic_old": group_hash(state["critic"], "network."),
              "critic_forecast": group_hash(state["critic"], "forecast_projection.")}
    if hashes != asset["final_tensor_sha256"]:
        raise ValueError("endpoint tensor group hashes mismatch")
    return state


def load_programs(parent_content, inputs, endpoint_contents):
    """Construct precisely seven deployment actors; C never constructs a D actor."""
    with torch.random.fork_rng(devices=[]):
        parent, _ = retained.load_base(parent_content, inputs["parent"]["sha256"])
        if any(v.dtype != torch.float32 or not torch.isfinite(v).all()
               for v in parent.state_dict().values()):
            raise ValueError("parent tensor contract mismatch")
        programs = {}
        for asset in inputs["assets"]:
            state = validate_endpoint(endpoint_contents[asset["endpoint"]], asset, parent)
            endpoint = retained.Actor()
            endpoint.load_state_dict(state["actor"], strict=True)
            endpoint.requires_grad_(False).eval()
            base = retained.BaseActor()
            base.load_state_dict(parent.state_dict(), strict=True)
            programs[asset["endpoint"]] = endpoint
            programs[asset["constant"]] = ConstantActor(base, bound_constant(asset))
        programs["B40"] = parent.requires_grad_(False).eval()
    return programs


class TimedActor(nn.Module):
    """Meter exactly the collector's full behavioral actor calls."""
    def __init__(self, actor):
        super().__init__()
        self.actor = actor
        self.duration = self.send = None
        self.timing = dict(calls=0, wall_ns=0, process_cpu_ns=0)

    @property
    def log_std(self):
        return self.actor.log_std

    def _call(self, method, *args):
        wall, cpu = time.perf_counter_ns(), time.process_time_ns()
        try:
            return method(*args)
        finally:
            self.timing["calls"] += 1
            self.timing["wall_ns"] += time.perf_counter_ns() - wall
            self.timing["process_cpu_ns"] += time.process_time_ns() - cpu

    def forward(self, *args):
        return self._call(self.actor, *args)

    def components(self, *args):
        return self._call(self.actor.components, *args)
