from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as functional

from .authorization import ProductionPermit, require_active_permit
from .config import ARMS, REGISTERED
from .rng import generator


class Actor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        # Explicit zeros keep construction/certificate imports preactivity;
        # the only prospective randomized initializer is initialized_actor.
        self.first_weight = nn.Parameter(torch.zeros((32, 11), dtype=torch.float64))
        self.first_bias = nn.Parameter(torch.zeros(32, dtype=torch.float64))
        self.second_weight = nn.Parameter(torch.zeros((32, 32), dtype=torch.float64))
        self.second_bias = nn.Parameter(torch.zeros(32, dtype=torch.float64))
        self.head_weight = nn.Parameter(torch.zeros((2, 32), dtype=torch.float64))
        self.head_bias = nn.Parameter(torch.zeros(2, dtype=torch.float64))

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        hidden = torch.tanh(functional.linear(observations, self.first_weight, self.first_bias))
        hidden = torch.tanh(functional.linear(hidden, self.second_weight, self.second_bias))
        return functional.linear(hidden, self.head_weight, self.head_bias)


class Posterior(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.logits = nn.Parameter(torch.zeros((4, 4), dtype=torch.float64))

    def log_probabilities(self) -> torch.Tensor:
        return torch.log_softmax(self.logits, dim=1)


def _xavier_fill(permit: ProductionPermit, seed: int, name: str, tensor: torch.Tensor) -> None:
    require_active_permit(permit)
    fan_out, fan_in = int(tensor.shape[0]), int(tensor.shape[1])
    bound = (5.0 / 3.0) * math.sqrt(6.0 / float(fan_in + fan_out))
    values = generator(permit, seed, "initialization", name).uniform(
        -bound, bound, size=tuple(tensor.shape),
    )
    tensor.copy_(torch.from_numpy(values).to(dtype=torch.float64))


def initialized_actor(permit: ProductionPermit, seed: int) -> Actor:
    actor = Actor()
    with torch.no_grad():
        _xavier_fill(permit, seed, "first.weight", actor.first_weight)
        _xavier_fill(permit, seed, "second.weight", actor.second_weight)
        _xavier_fill(permit, seed, "head.weight", actor.head_weight)
        actor.first_bias.zero_()
        actor.second_bias.zero_()
        actor.head_bias.zero_()
    if sum(parameter.numel() for parameter in actor.parameters()) != REGISTERED.actor_parameters:
        raise RuntimeError("actor parameter count mismatch")
    return actor


def paired_models(permit: ProductionPermit, seed: int) -> tuple[dict[str, Actor], dict[str, Posterior]]:
    actors = {arm: initialized_actor(permit, seed) for arm in ARMS}
    posteriors = {arm: Posterior() for arm in ARMS}
    reference = list(actors[ARMS[0]].state_dict().values())
    for arm in ARMS[1:]:
        if not all(
            torch.equal(left, right)
            for left, right in zip(reference, actors[arm].state_dict().values(), strict=True)
        ):
            raise RuntimeError("paired actor initialization mismatch")
    return actors, posteriors


def actor_inputs(
    x: np.ndarray,
    mu: float,
    latent: np.ndarray | int,
    phase: int,
    previous_action: np.ndarray | None = None,
) -> torch.Tensor:
    values = np.asarray(x, dtype=np.float64)
    n = len(values)
    latent_values = np.full(n, int(latent), dtype=np.int64) if np.isscalar(latent) else np.asarray(latent, dtype=np.int64)
    if latent_values.shape != (n,) or np.any((latent_values < 0) | (latent_values > 3)):
        raise ValueError("latent must have one value in 0..3 per agent")
    one_hot = np.eye(4, dtype=np.float64)[latent_values]
    if phase == 1:
        phase_fields = np.tile(np.asarray((1.0, 0.0, 0.0, 0.0)), (n, 1))
    elif phase == 2 and previous_action is not None:
        previous = np.asarray(previous_action, dtype=np.int64)
        if previous.shape != (n,) or np.any((previous < 0) | (previous > 1)):
            raise ValueError("phase-two previous actions must be binary")
        signed = 2.0 * previous.astype(np.float64) - 1.0
        phase_fields = np.stack((np.zeros(n), np.ones(n), np.ones(n), signed), axis=1)
    else:
        raise ValueError("phase must be 1 or phase 2 must include previous actions")
    base = np.stack((values, np.full(n, mu), values - mu), axis=1)
    return torch.from_numpy(np.concatenate((base, phase_fields, one_hot), axis=1))


def sample_binary(logits: torch.Tensor, uniforms: np.ndarray) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    probabilities = torch.softmax(logits, dim=-1)
    u = torch.from_numpy(np.asarray(uniforms, dtype=np.float64)).to(logits.device)
    actions = (u >= probabilities[..., 0]).to(torch.int64)
    selected = torch.log(probabilities.gather(-1, actions[..., None]).squeeze(-1))
    return actions, selected, probabilities
