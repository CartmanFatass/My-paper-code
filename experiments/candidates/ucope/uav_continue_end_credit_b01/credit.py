"""Separately clipped suffix credit; no change to the fixed-short F learner."""
import torch
from torch import nn

from ..uav_motion_prefix_b01.learner import recurrent_outputs, returns_to_go
from ..uav_motion_prefix_b01.policy import separate_terms, snapshot


def residual_baseline(seed):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        model = nn.Sequential(nn.Linear(67, 32), nn.Tanh(), nn.Linear(32, 1))
    nn.init.zeros_(model[-1].weight)
    nn.init.zeros_(model[-1].bias)
    return model


def optimizer_for(actor, critic, residual):
    parameters = list(actor.parameters()) + list(critic.parameters()) + list(residual.parameters())
    return torch.optim.Adam(parameters, lr=3e-4, betas=(.9, .999), eps=1e-8,
                            weight_decay=0, amsgrad=False, foreach=False, fused=False)


def fixed_targets(rollout):
    returns = returns_to_go(rollout["reward"])
    raw = returns - rollout["value"]
    sigma = raw.std(unbiased=False) + 1e-8
    velocity = ((raw - raw.mean()) / sigma).detach()
    suffix_target = (returns - rollout["reward"] - rollout["value"])[..., None].detach()
    duration = ((suffix_target - rollout["residual_old"]) / sigma).detach()
    return returns.detach(), velocity, duration, suffix_target


def masked_surrogate(new, old, advantage, mask):
    ratio = (new - old).exp()
    score = torch.minimum(ratio * advantage, ratio.clamp(.8, 1.2) * advantage)
    # Sum actual agent decisions, average over ALL E*H primitive rows.
    return -torch.where(mask, score, 0).sum(-1).mean()


def update(actor, critic, residual, optimizer, episodes, chunk, check, counts):
    rollout = {key: torch.stack([episode[key] for episode in episodes]) for key in episodes[0]}
    returns, velocity_advantage, duration_advantage, residual_target = fixed_targets(rollout)
    mask = rollout["credit_mask"]
    features = rollout["baseline_input"][mask].detach()
    target = residual_target.expand_as(mask)[mask]
    parameters = list(actor.parameters()) + list(critic.parameters()) + list(residual.parameters())
    records = []
    for epoch in range(4):
        check()
        mean, recurrent = recurrent_outputs(actor, rollout, chunk)
        velocity_lp, duration_lp = separate_terms(actor, mean, recurrent, rollout["u"],
            rollout["durations"], rollout["velocity_mask"], mask)
        velocity_loss = masked_surrogate(velocity_lp, rollout["velocity_logp"],
                                        velocity_advantage[..., None], rollout["velocity_mask"])
        duration_loss = masked_surrogate(duration_lp, rollout["duration_logp"],
                                        duration_advantage, mask)
        value_loss = (critic(rollout["critic"]) - returns).square().mean()
        residual_loss = (residual(features).squeeze(-1) - target).square().mean()
        loss = velocity_loss + duration_loss + .5 * value_loss + .5 * residual_loss
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite separate-credit PPO loss")
        optimizer.zero_grad()
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError("nonfinite separate-credit PPO gradient")
        check()
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite parameters after separate-credit Adam")
        records.append(dict(epoch=epoch, loss=float(loss.detach()),
            velocity_loss=float(velocity_loss.detach()), duration_loss=float(duration_loss.detach()),
            value_loss=float(value_loss.detach()), residual_loss=float(residual_loss.detach()),
            grad_norm=float(grad_norm)))
        check()
    return records


def model_snapshot(actor, critic, residual=None):
    values = snapshot(actor, critic)
    if residual is not None:
        values["residual"] = torch.cat([p.detach().flatten() for p in residual.parameters()]).clone()
        values["total"] = torch.cat((values["total"], values["residual"]))
    return values


def movement(initial, actor, critic, residual=None):
    final = model_snapshot(actor, critic, residual)
    result = {}
    for name, before in initial.items():
        after = final[name]
        norm, displacement = float(before.norm()), float((after-before).norm())
        result[name] = dict(parameters=before.numel(), initial_norm=norm,
            final_norm=float(after.norm()), displacement=displacement,
            relative_displacement=displacement/norm if norm else None)
    return result
