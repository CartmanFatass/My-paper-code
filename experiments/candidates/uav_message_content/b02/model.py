"""One scalar head on the unchanged CADC motion actor."""

import math
import hashlib
import io

import torch
from torch import nn

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import build_arm as build_cadc_arm
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob

SOURCE_MASTER = 19431
SOURCE_SHA256 = "456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad"
SCALAR_ACTOR_COLUMNS = tuple(126 + 10 * sender for sender in range(5))
SCALAR_CRITIC_COLUMNS = tuple(154 + 63 * receiver + 10 * sender
                              for receiver in range(5) for sender in range(5))


def build_arm(master, arm):
    if arm not in ("B", "O", "L"):
        raise ValueError(arm)
    actor, critic = build_cadc_arm(SOURCE_MASTER, "RR")
    if arm == "L":
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(100000 * master + 12)
            actor.content = nn.Linear(64, 1)
            nn.init.zeros_(actor.content.weight)
            nn.init.zeros_(actor.content.bias)
        actor.content_log_std = nn.Parameter(torch.zeros(1))
    return actor, critic


def load_warm_start(actor, critic, checkpoint_bytes, expected_sha256):
    if hashlib.sha256(checkpoint_bytes).hexdigest() != expected_sha256:
        raise ValueError("C checkpoint digest mismatch")
    state = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or any(state.get(key) != value for key, value in (
            ("arm", "C"), ("master", SOURCE_MASTER), ("input_size", 171),
            ("critic_size", 451))):
        raise ValueError("C checkpoint metadata mismatch")
    source_actor = state.get("actor")
    source_critic = state.get("critic")
    if not isinstance(source_actor, dict) or not isinstance(source_critic, dict):
        raise ValueError("C checkpoint lacks actor/critic state")
    expected_actor = {key for key in actor.state_dict() if not key.startswith("content")}
    if set(source_actor) != expected_actor or set(source_critic) != set(critic.state_dict()):
        raise ValueError("C checkpoint state keys mismatch")
    actor.load_state_dict(source_actor, strict=not hasattr(actor, "content"))
    critic.load_state_dict(source_critic, strict=True)
    with torch.no_grad():
        actor.encoder.raw.weight[:, SCALAR_ACTOR_COLUMNS] = 0
        actor.encoder.hidden.weight[:, SCALAR_ACTOR_COLUMNS] = 0
        critic.network[0].weight[:, SCALAR_CRITIC_COLUMNS] = 0


def sample_content(actor, recurrent, sender, rng):
    if not hasattr(actor, "content"):
        raise ValueError("only L samples content")
    mean = actor.content(recurrent[sender])
    pre_tanh = mean + actor.content_log_std.clamp(-5, 2).exp() * torch.randn(1, generator=rng)
    return pre_tanh, (1 + pre_tanh.tanh()) / 2


def action_terms(actor, mean, recurrent, motion, content_u, content_mask):
    logp = tanh_log_prob(motion, mean, actor.log_std)
    motion_entropy = (actor.log_std.clamp(-5, 2) + .5 * math.log(2 * math.pi * math.e)).sum()
    entropy = torch.ones_like(logp).sum(-1) * motion_entropy
    if hasattr(actor, "content"):
        content_mean = actor.content(recurrent)
        content_lp = tanh_log_prob(content_u, content_mean, actor.content_log_std) + math.log(2)
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
