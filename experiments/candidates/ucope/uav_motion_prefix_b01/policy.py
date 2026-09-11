"""CPU FP32 recurrent actor and independent centralized critic."""
import copy
import math

import torch
from torch import nn
from torch.nn import functional as F


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Linear(108, 64)
        self.gru = nn.GRU(64, 64)
        self.mean = nn.Linear(64, 3)
        self.log_std = nn.Parameter(torch.zeros(3))
        self.duration = None
        self.duration_conditioned = False

    def forward(self, observations, hidden):
        output, hidden = self.gru(torch.tanh(self.encoder(observations)), hidden)
        return self.mean(output), output, hidden


class Critic(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(136, 128), nn.Tanh(),
                                     nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 1))

    def forward(self, x):
        return self.network(x).squeeze(-1)


def templates(seed):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * seed + 11)
        actor = Actor()
        critic = Critic()
    return actor, critic


def arm_copy(common, treatment, duration_head_seed=None, freeze_duration=False):
    actor, critic = copy.deepcopy(common)
    if treatment:
        actor.duration_conditioned = duration_head_seed is not None
        with torch.random.fork_rng(devices=[]):
            if actor.duration_conditioned:
                torch.random.default_generator.manual_seed(duration_head_seed)
                actor.duration = nn.Sequential(nn.Linear(67, 32), nn.Tanh(), nn.Linear(32, 2))
            else:
                actor.duration = nn.Linear(64, 2)
        final = actor.duration[-1] if actor.duration_conditioned else actor.duration
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)
        if freeze_duration:
            actor.duration.requires_grad_(False)
    return actor, critic


def generator(seed):
    return torch.Generator(device="cpu").manual_seed(seed)


def tanh_log_prob(u, mean, log_std):
    log_std = log_std.clamp(-5, 2)
    normal = -.5 * ((u - mean) / log_std.exp()).square() - log_std
    normal = normal - .5 * math.log(2 * math.pi)
    jacobian = 2 * (math.log(2) - u - F.softplus(-2 * u))
    return (normal - jacobian).sum(-1)


def joint_terms(actor, mean, recurrent, u, durations, velocity_mask, duration_mask,
                ratio_grouping="joint"):
    velocity_lp = tanh_log_prob(u, mean, actor.log_std)
    logp = torch.where(velocity_mask, velocity_lp, 0)
    if ratio_grouping == "joint":
        logp = logp.sum(-1)
    normal_entropy = (actor.log_std.clamp(-5, 2)
                      + .5 * math.log(2 * math.pi * math.e)).sum()
    entropy = velocity_mask.sum(-1) * normal_entropy
    if actor.duration is not None:
        if actor.duration_conditioned:
            if not duration_mask.any():
                return logp, entropy
            inputs = torch.cat((recurrent[duration_mask], u[duration_mask].detach().tanh()), -1)
            logits = actor.duration(inputs)
            selected = durations[duration_mask]
        else:
            logits = actor.duration(recurrent)
            selected = durations
        log_probs = logits.log_softmax(-1)
        chosen = log_probs.gather(-1, selected[..., None]).squeeze(-1)
        cat_entropy = -(log_probs.exp() * log_probs).sum(-1)
        if actor.duration_conditioned:
            duration_lp = torch.zeros_like(velocity_lp).masked_scatter(duration_mask, chosen)
            duration_entropy = torch.zeros_like(velocity_lp).masked_scatter(duration_mask, cat_entropy)
        else:
            duration_lp = torch.where(duration_mask, chosen, 0)
            duration_entropy = torch.where(duration_mask, cat_entropy, 0)
        logp = logp + (duration_lp.sum(-1) if ratio_grouping == "joint" else duration_lp)
        entropy = entropy + duration_entropy.sum(-1)
    return logp, entropy


def separate_terms(actor, mean, recurrent, u, durations, velocity_mask, duration_mask):
    """Conditional velocity and duration densities for the opt-in credit package."""
    velocity = torch.where(velocity_mask, tanh_log_prob(u, mean, actor.log_std), 0)
    inputs = torch.cat((recurrent[duration_mask], u[duration_mask].detach().tanh()), -1)
    log_probs = actor.duration(inputs).log_softmax(-1)
    chosen = log_probs.gather(-1, durations[duration_mask][..., None]).squeeze(-1)
    duration = torch.zeros_like(velocity).masked_scatter(duration_mask, chosen)
    return velocity, duration


def sample(actor, mean, recurrent, active, opening, velocity_rng, duration_rng,
           duration_mask=None, velocity_mode="sampled"):
    u = torch.zeros_like(mean)
    durations = torch.zeros(5, dtype=torch.long)
    for i in range(5):
        if active[i]:
            if velocity_mode == "mean":
                u[i] = mean[i]
            else:
                u[i] = mean[i] + actor.log_std.clamp(-5, 2).exp() * torch.randn(
                    3, generator=velocity_rng)
        eligible = opening if duration_mask is None else duration_mask[i]
        if eligible and actor.duration is not None:
            inputs = (torch.cat((recurrent[i], u[i].detach().tanh()), -1)
                      if actor.duration_conditioned else recurrent[i])
            probabilities = actor.duration(inputs).softmax(-1)
            durations[i] = torch.multinomial(probabilities, 1, generator=duration_rng)[0]
    return u, durations


def parameter_groups(actor, critic):
    common = [p for name, p in actor.named_parameters() if not name.startswith("duration.")]
    groups = {"common_actor": common, "critic": list(critic.parameters())}
    if actor.duration is not None:
        groups["duration"] = list(actor.duration.parameters())
        if actor.duration_conditioned:
            groups["duration_hidden"] = list(actor.duration[0].parameters())
            groups["duration_final"] = list(actor.duration[2].parameters())
    groups["total"] = list(actor.parameters()) + list(critic.parameters())
    return groups


def snapshot(actor, critic):
    return {name: torch.cat([p.detach().flatten() for p in group]).clone()
            for name, group in parameter_groups(actor, critic).items()}


def exposure(initial, actor, critic):
    final = snapshot(actor, critic)
    result = {}
    for name, start in initial.items():
        end = final[name]
        initial_norm = float(start.norm())
        displacement = float((end - start).norm())
        result[name] = {"parameters": start.numel(), "initial_norm": initial_norm,
                        "final_norm": float(end.norm()), "displacement": displacement,
                        "relative_displacement": (None if actor.duration_conditioned and initial_norm == 0
                                                  else displacement / (initial_norm + 1e-12))}
    return result
