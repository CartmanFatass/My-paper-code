"""Two bounded corrections around the same frozen B19451 motion policy."""

import torch
from torch import nn

from experiments.candidates.uav_message_content.b05 import model as b05

SOURCE_SHA256 = b05.SOURCE_SHA256
SOURCE_COMMIT = b05.SOURCE_COMMIT
SOURCE_MASTER = b05.SOURCE_MASTER
SOURCE_INHERITED_SHA256 = b05.SOURCE_INHERITED_SHA256
ACTOR_SIZE = b05.ACTOR_SIZE
CRITIC_SIZE = b05.CRITIC_SIZE
CORRECTION_BOUND = b05.CORRECTION_BOUND

ResidualActor = b05.Actor
Critic = b05.Critic
load_warm_start = b05.load_warm_start
load_base = b05.load_base
motion_terms = b05.motion_terms


class CalibrationActor(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = b05.BaseActor()
        self.base.requires_grad_(False)
        self.b = nn.Parameter(torch.zeros(3))
        self.duration = None
        self.send = None

    @property
    def log_std(self):
        return self.base.log_std

    def components(self, observations, hidden):
        if observations.shape[-1] != ACTOR_SIZE:
            raise ValueError("B06 actor input size")
        with torch.no_grad():
            base_mean, recurrent, next_hidden = self.base(observations[..., :171], hidden)
        correction = (CORRECTION_BOUND * torch.tanh(self.b)).expand_as(base_mean)
        return base_mean + correction, recurrent, next_hidden, base_mean, correction

    def forward(self, observations, hidden):
        mean, recurrent, next_hidden, _, _ = self.components(observations, hidden)
        return mean, recurrent, next_hidden


def build_arm(master, arm):
    if master not in (19701, 19702, 19703) or arm not in ("K", "D"):
        raise ValueError("fixed B06 learner cell")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * master + 11)
        # Critic construction precedes the arm-specific actor so its fresh
        # forecast projection and inherited network match across K and D.
        critic = Critic()
        actor = CalibrationActor() if arm == "K" else ResidualActor()
    return actor, critic


def parameter_snapshot(actor, critic):
    groups = {"base_actor": actor.base.parameters(),
              "critic_old": critic.network.parameters(),
              "critic_forecast": critic.forecast_projection.parameters()}
    if isinstance(actor, CalibrationActor):
        groups["calibration"] = (actor.b,)
    elif isinstance(actor, ResidualActor):
        groups["residual_hidden"] = actor.residual_hidden.parameters()
        groups["residual_output"] = actor.residual_output.parameters()
    else:
        raise TypeError("B06 actor must be K or D")
    return {name: torch.cat([parameter.detach().flatten() for parameter in parameters]).clone()
            for name, parameters in groups.items()}


def exposure(initial, actor, critic):
    current = parameter_snapshot(actor, critic)
    if initial.keys() != current.keys():
        raise ValueError("B06 exposure groups changed")
    result = {}
    for name, before in initial.items():
        after = current[name]
        displacement = float((after - before).norm())
        initial_norm = float(before.norm())
        result[name] = dict(parameters=before.numel(), initial_norm=initial_norm,
                            final_norm=float(after.norm()), displacement=displacement,
                            relative_displacement=displacement / initial_norm if initial_norm else None)
    return result
