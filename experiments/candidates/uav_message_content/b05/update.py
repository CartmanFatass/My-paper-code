"""Full-rollout recurrent PPO with independent residual actor and critic steps."""

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss, recurrent_outputs, returns_to_go,
)
from .model import motion_terms


def optimizers_for(actor, critic):
    options = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False)
    actor_parameters = [parameter for parameter in actor.parameters() if parameter.requires_grad]
    return torch.optim.Adam(actor_parameters, **options), torch.optim.Adam(critic.parameters(), **options)


def _count(counts, key, rows=1):
    counts[key] = counts.get(key, 0) + rows


def update_motion(actor, critic, actor_opt, critic_opt, episodes, counts, check, emit_update=None):
    if len(episodes) != 2:
        raise ValueError("B05 PPO requires two complete episodes")
    rollout = {key: torch.stack([episode[key] for episode in episodes]) for key in episodes[0]}
    episode_count, horizon, agents, _ = rollout["obs"].shape
    if horizon % 32 or agents != 5:
        raise ValueError("B05 PPO requires five agents and chunk32 replay")
    targets = returns_to_go(rollout["reward"])
    raw_advantage = targets - rollout["value"]
    advantage = ((raw_advantage - raw_advantage.mean()) /
                 (raw_advantage.std(unbiased=False) + 1e-8)).detach()
    actor_parameters = [parameter for parameter in actor.parameters() if parameter.requires_grad]
    critic_parameters = list(critic.parameters())
    for epoch in range(4):
        check()
        mean, _ = recurrent_outputs(actor, rollout, 32)
        _count(counts, "ppo_actor_forward_calls")
        _count(counts, "ppo_actor_forward_rows", episode_count * horizon * agents)
        logp, entropy = motion_terms(actor, mean, rollout["u"])
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantage,
                                          torch.ones_like(logp, dtype=torch.bool))
        actor_loss = policy_loss - .01 * entropy.mean()
        if not torch.isfinite(actor_loss):
            raise FloatingPointError("nonfinite PPO actor loss")
        actor_opt.zero_grad()
        actor_loss.backward()
        actor_norm = torch.nn.utils.clip_grad_norm_(actor_parameters, .5)
        if not torch.isfinite(actor_norm):
            raise FloatingPointError("nonfinite PPO actor gradient")
        check()
        actor_opt.step()
        _count(counts, "actor_optimizer_steps")

        value_loss = (critic(rollout["critic"]) - targets).square().mean()
        critic_loss = .5 * value_loss
        _count(counts, "ppo_critic_forward_calls")
        _count(counts, "ppo_critic_forward_rows", episode_count * horizon)
        if not torch.isfinite(critic_loss):
            raise FloatingPointError("nonfinite PPO critic loss")
        critic_opt.zero_grad()
        critic_loss.backward()
        critic_norm = torch.nn.utils.clip_grad_norm_(critic_parameters, .5)
        if not torch.isfinite(critic_norm):
            raise FloatingPointError("nonfinite PPO critic gradient")
        check()
        critic_opt.step()
        _count(counts, "critic_optimizer_steps")
        _count(counts, "optimizer_steps")
        _count(counts, "replayed_actor_rows", episode_count * horizon * agents)
        if not all(torch.isfinite(parameter).all() for parameter in actor_parameters + critic_parameters):
            raise FloatingPointError("nonfinite Adam parameters")
        if emit_update is not None:
            emit_update(dict(kind="ppo", epoch=epoch,
                             loss=float((actor_loss + critic_loss).detach()),
                             policy_loss=float(policy_loss.detach()),
                             value_loss=float(value_loss.detach()),
                             gaussian_entropy=float(entropy.mean().detach()),
                             actor_grad_norm=float(actor_norm), critic_grad_norm=float(critic_norm)))
