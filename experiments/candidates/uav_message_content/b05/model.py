"""Frozen B19451 motion policy with a bounded, trainable mean correction."""

import hashlib
import io
import math

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
CORRECTION_BOUND = .10


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = BaseActor()
        self.base.requires_grad_(False)
        self.residual_hidden = nn.Linear(ACTOR_SIZE + 64, 64)
        self.residual_output = nn.Linear(64, 3)
        nn.init.zeros_(self.residual_output.weight)
        nn.init.zeros_(self.residual_output.bias)
        self.duration = None
        self.send = None

    @property
    def log_std(self):
        return self.base.log_std

    def components(self, observations, hidden):
        if observations.shape[-1] != ACTOR_SIZE:
            raise ValueError("B05 actor input size")
        with torch.no_grad():
            base_mean, recurrent, next_hidden = self.base(observations[..., :171], hidden)
        residual_input = torch.cat((observations, recurrent), dim=-1)
        correction = CORRECTION_BOUND * torch.tanh(
            self.residual_output(torch.tanh(self.residual_hidden(residual_input))))
        return base_mean + correction, recurrent, next_hidden, base_mean, correction

    def forward(self, observations, hidden):
        mean, recurrent, next_hidden, _, _ = self.components(observations, hidden)
        return mean, recurrent, next_hidden


class Critic(BaseCritic):
    def __init__(self):
        super().__init__()
        self.forecast_projection = nn.Linear(75, 128, bias=False)
        nn.init.zeros_(self.forecast_projection.weight)

    def forward(self, x):
        if x.shape[-1] != CRITIC_SIZE:
            raise ValueError("B05 critic input size")
        value = self.network[0](x[..., :451]) + self.forecast_projection(x[..., 451:])
        for layer in self.network[1:]:
            value = layer(value)
        return value.squeeze(-1)


def build_arm(master, arm):
    if master not in (19601, 19602, 19603) or arm not in ("M_G", "M_O"):
        raise ValueError("fixed B05 learner cell")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 11)
        return Actor(), Critic()


def _source_state(checkpoint_bytes, expected_sha256):
    if expected_sha256 != SOURCE_SHA256 or hashlib.sha256(checkpoint_bytes).hexdigest() != expected_sha256:
        raise ValueError("B19451 checkpoint digest mismatch")
    state = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    fields = (("arm", "B"), ("master", SOURCE_MASTER), ("input_size", 171),
              ("critic_size", 451), ("inherited_sha256", SOURCE_INHERITED_SHA256))
    if not isinstance(state, dict) or any(state.get(key) != value for key, value in fields):
        raise ValueError("B19451 checkpoint metadata mismatch")
    base_actor, base_critic = BaseActor(), BaseCritic()
    if (not isinstance(state.get("actor"), dict) or not isinstance(state.get("critic"), dict)
            or set(state["actor"]) != set(base_actor.state_dict())
            or set(state["critic"]) != set(base_critic.state_dict())):
        raise ValueError("B19451 checkpoint parameter keys mismatch")
    base_actor.load_state_dict(state["actor"], strict=True)
    base_critic.load_state_dict(state["critic"], strict=True)
    return state


def load_warm_start(actor, critic, checkpoint_bytes, expected_sha256=SOURCE_SHA256):
    state = _source_state(checkpoint_bytes, expected_sha256)
    actor.base.load_state_dict(state["actor"], strict=True)
    actor.base.requires_grad_(False)
    critic.network.load_state_dict({key.removeprefix("network."): value
                                    for key, value in state["critic"].items()}, strict=True)
    return state


def load_base(checkpoint_bytes, expected_sha256=SOURCE_SHA256):
    state = _source_state(checkpoint_bytes, expected_sha256)
    actor, critic = BaseActor(), BaseCritic()
    actor.load_state_dict(state["actor"], strict=True)
    critic.load_state_dict(state["critic"], strict=True)
    actor.requires_grad_(False)
    critic.requires_grad_(False)
    return actor, critic


def motion_terms(actor, mean, u):
    logp = tanh_log_prob(u, mean, actor.log_std)
    gaussian_entropy = (actor.log_std.clamp(-5, 2) + .5 * math.log(2 * math.pi * math.e)).sum()
    return logp, torch.ones_like(logp).sum(-1) * gaussian_entropy


def parameter_snapshot(actor, critic):
    groups = {"base_actor": actor.base.parameters(),
              "residual_hidden": actor.residual_hidden.parameters(),
              "residual_output": actor.residual_output.parameters(),
              "critic_old": critic.network.parameters(),
              "critic_forecast": critic.forecast_projection.parameters()}
    return {name: torch.cat([parameter.detach().flatten() for parameter in parameters]).clone()
            for name, parameters in groups.items()}


def exposure(initial, actor, critic):
    current = parameter_snapshot(actor, critic)
    result = {}
    for name, before in initial.items():
        after = current[name]
        displacement = float((after - before).norm())
        initial_norm = float(before.norm())
        result[name] = dict(parameters=before.numel(), initial_norm=initial_norm,
                            final_norm=float(after.norm()), displacement=displacement,
                            relative_displacement=displacement / initial_norm if initial_norm else None)
    return result
