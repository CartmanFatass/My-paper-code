"""Direction-owned content head on the unchanged CADC motion actor."""

import math

import torch
from torch import nn

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import build_arm as build_cadc_arm
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob


def build_arm(master, arm):
    if arm not in ("C", "H", "L"):
        raise ValueError(arm)
    actor, critic = build_cadc_arm(master, "RR")
    if arm == "L":
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(100000 * master + 12)
            actor.content = nn.Linear(64, 7)
            nn.init.zeros_(actor.content.weight)
            nn.init.zeros_(actor.content.bias)
        actor.content_log_std = nn.Parameter(torch.zeros(7))
    return actor, critic


def sample_content(actor, recurrent, sender, rng):
    if not hasattr(actor, "content"):
        raise ValueError("only L samples content")
    mean = actor.content(recurrent[sender])
    pre_tanh = mean + actor.content_log_std.clamp(-5, 2).exp() * torch.randn(7, generator=rng)
    return pre_tanh, pre_tanh.tanh()


def action_terms(actor, mean, recurrent, motion, content_u, content_mask):
    logp = tanh_log_prob(motion, mean, actor.log_std)
    motion_entropy = (actor.log_std.clamp(-5, 2) + .5 * math.log(2 * math.pi * math.e)).sum()
    entropy = torch.ones_like(logp).sum(-1) * motion_entropy
    if hasattr(actor, "content"):
        content_mean = actor.content(recurrent)
        content_lp = tanh_log_prob(content_u, content_mean, actor.content_log_std)
        logp = logp + torch.where(content_mask, content_lp, 0)
        content_entropy = (actor.content_log_std.clamp(-5, 2)
                           + .5 * math.log(2 * math.pi * math.e)).sum()
        entropy = entropy + content_mask.sum(-1) * content_entropy
    return logp, entropy


def parameter_groups(actor, critic):
    common = [p for name, p in actor.named_parameters()
              if not name.startswith("content.") and name != "content_log_std"]
    groups = {"motion_receiver": common, "critic": list(critic.parameters())}
    if hasattr(actor, "content"):
        groups["content_head"] = list(actor.content.parameters()) + [actor.content_log_std]
    return groups


def snapshot(actor, critic):
    return {name: torch.cat([p.detach().flatten() for p in params]).clone()
            for name, params in parameter_groups(actor, critic).items()}


def exposure(initial, actor, critic):
    final = snapshot(actor, critic)
    return {name: dict(parameters=start.numel(), initial_norm=float(start.norm()),
                       final_norm=float(final[name].norm()),
                       displacement=float((final[name] - start).norm()),
                       relative_displacement=(float((final[name] - start).norm() / start.norm())
                                              if float(start.norm()) else None))
            for name, start in initial.items()}
