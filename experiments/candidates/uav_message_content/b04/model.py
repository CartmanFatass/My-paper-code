"""Exact old-path B warm start with separate forecast projections."""

import hashlib
import io
import math

import numpy as np
import torch
from torch import nn

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    Actor as BaseActor, Critic as BaseCritic,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob

SOURCE_SHA256 = "34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2"
SOURCE_COMMIT = "02ede8a4a75cc83e6e18d8b6619f1cfa84bc8d92"
SOURCE_MASTER = 19451
SOURCE_INHERITED_SHA256 = "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad"
ACTOR_SIZE, CRITIC_SIZE = 186, 526
D = np.array((.03, .03, .30), dtype=np.float32)


class Actor(BaseActor):
    def __init__(self):
        super().__init__()
        self.forecast_projection = nn.Linear(15, 64, bias=False)
        nn.init.zeros_(self.forecast_projection.weight)

    def forward(self, observations, hidden):
        if observations.shape[-1] != ACTOR_SIZE:
            raise ValueError("B04 actor input size")
        base = self.encoder(observations[..., :171])
        encoded = base + self.forecast_projection(observations[..., 171:])
        recurrent, hidden = self.gru(torch.tanh(encoded), hidden)
        return self.mean(recurrent), recurrent, hidden


class Critic(BaseCritic):
    def __init__(self):
        super().__init__()
        self.forecast_projection = nn.Linear(75, 128, bias=False)
        nn.init.zeros_(self.forecast_projection.weight)

    def forward(self, x):
        if x.shape[-1] != CRITIC_SIZE:
            raise ValueError("B04 critic input size")
        first = self.network[0](x[..., :451]) + self.forecast_projection(x[..., 451:])
        for layer in self.network[1:]:
            first = layer(first)
        return first.squeeze(-1)


class Predictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden = nn.Linear(74, 64)
        self.output = nn.Linear(64, 3)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def forward(self, x):
        return self.output(torch.tanh(self.hidden(x)))


def build_arm(master, arm):
    if master not in (19501, 19502, 19503) or arm not in ("G", "O", "F"):
        raise ValueError("fixed B04 cell")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 11)
        actor, critic = Actor(), Critic()
        predictor = None
        if arm == "F":
            torch.manual_seed(100000 * master + 12)
            predictor = Predictor()
    return actor, critic, predictor


def _source_state(checkpoint_bytes, expected_sha256=SOURCE_SHA256):
    if hashlib.sha256(checkpoint_bytes).hexdigest() != expected_sha256 or expected_sha256 != SOURCE_SHA256:
        raise ValueError("B19451 checkpoint digest mismatch")
    state = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    fields = (("arm", "B"), ("master", SOURCE_MASTER), ("input_size", 171),
              ("critic_size", 451), ("inherited_sha256", SOURCE_INHERITED_SHA256))
    if not isinstance(state, dict) or any(state.get(k) != v for k, v in fields):
        raise ValueError("B19451 checkpoint metadata mismatch")
    base_actor, base_critic = BaseActor(), BaseCritic()
    if set(state.get("actor", {})) != set(base_actor.state_dict()) or set(state.get("critic", {})) != set(base_critic.state_dict()):
        raise ValueError("B19451 checkpoint parameter keys mismatch")
    base_actor.load_state_dict(state["actor"], strict=True)
    base_critic.load_state_dict(state["critic"], strict=True)
    return state


def load_warm_start(actor, critic, checkpoint_bytes, expected_sha256=SOURCE_SHA256):
    state = _source_state(checkpoint_bytes, expected_sha256)
    actor.load_state_dict(state["actor"], strict=False)
    critic.load_state_dict(state["critic"], strict=False)
    return state


def load_base(checkpoint_bytes, expected_sha256=SOURCE_SHA256):
    state = _source_state(checkpoint_bytes, expected_sha256)
    actor, critic = BaseActor(), BaseCritic()
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    return actor, critic


def motion_terms(actor, mean, motion):
    logp = tanh_log_prob(motion, mean, actor.log_std)
    entropy = (actor.log_std.clamp(-5, 2) + .5 * math.log(2 * math.pi * math.e)).sum()
    return logp, torch.ones_like(logp).sum(-1) * entropy


def forecast_context(recurrent, position, sampled, central, horizon):
    return torch.cat((recurrent.detach(), torch.as_tensor(position, dtype=torch.float32),
                      sampled.detach(), central.detach(),
                      torch.tensor([horizon / 10], dtype=torch.float32)), -1).detach()


def endpoints(position, sampled, central, horizon, residual=None):
    if not 1 <= horizon <= 10:
        raise ValueError("forecast horizon")
    p = torch.as_tensor(position, dtype=torch.float32)
    step = torch.as_tensor(D)
    first = torch.clamp(p + step * sampled, 0, 1)
    ordinary = torch.clamp(first + (horizon - 1) * step * central, 0, 1)
    cv = torch.clamp(first + (horizon - 1) * step * sampled, 0, 1)
    if residual is None:
        return first, ordinary, cv, ordinary
    lower = torch.clamp(first - (horizon - 1) * step, min=0)
    upper = torch.clamp(first + (horizon - 1) * step, max=1)
    predicted = torch.maximum(lower, torch.minimum(upper,
        ordinary + 2 * (horizon - 1) * step * torch.tanh(residual)))
    return first, ordinary, cv, predicted


def parameter_snapshot(actor, critic, predictor=None):
    groups = {"actor_old": [p for n, p in actor.named_parameters() if n != "forecast_projection.weight"],
              "actor_forecast": list(actor.forecast_projection.parameters()),
              "critic_old": [p for n, p in critic.named_parameters() if n != "forecast_projection.weight"],
              "critic_forecast": list(critic.forecast_projection.parameters())}
    if predictor is not None:
        groups["predictor"] = list(predictor.parameters())
    return {name: torch.cat([p.detach().flatten() for p in params]).clone()
            for name, params in groups.items()}


def exposure(initial, actor, critic, predictor=None):
    final = parameter_snapshot(actor, critic, predictor)
    result = {}
    for name, before in initial.items():
        delta = float((final[name] - before).norm())
        norm = float(before.norm())
        result[name] = dict(parameters=before.numel(), initial_norm=norm,
                            final_norm=float(final[name].norm()), displacement=delta,
                            relative_displacement=delta / norm if norm else None)
    return result
