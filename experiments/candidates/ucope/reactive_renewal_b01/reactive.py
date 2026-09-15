"""Recorded branch likelihoods and primitive-return PPO for reactive persistence."""
import math

import numpy as np
import torch

from ..uav_motion_prefix_b01.environment import actor_features, critic_features, team_reward
from ..uav_motion_prefix_b01.learner import (
    clipped_policy_loss, recurrent_outputs, returns_to_go,
)
from ..uav_motion_prefix_b01.policy import tanh_log_prob

KEEP, END = 0, 1


def row_log_probs(actor, mean, recurrent, previous, eligible, branches, u, fresh):
    """Score the recorded branch and its conditional draw, without resampling."""
    logp = torch.where(fresh, tanh_log_prob(u, mean, actor.log_std), 0)
    if eligible.any():
        inputs = torch.cat((recurrent[eligible], previous[eligible].detach()), -1)
        gate = actor.duration(inputs).log_softmax(-1)
        chosen = gate.gather(-1, branches[eligible][..., None]).squeeze(-1)
        logp = logp + torch.zeros_like(logp).masked_scatter(eligible, chosen)
    return logp


@torch.no_grad()
def draw_commands(actor, mean, recurrent, previous, eligible, velocity_rng, gate_rng):
    previous = torch.as_tensor(previous, dtype=torch.float32)
    eligible = torch.as_tensor(eligible, dtype=torch.bool)
    branches = torch.zeros(5, dtype=torch.long)
    gate_lp = torch.zeros(5)
    gate_rows = torch.nonzero(eligible).flatten().tolist()
    gate_logs = actor.duration(torch.cat((recurrent[eligible], previous[eligible]), -1)) \
        .log_softmax(-1) if gate_rows else None
    u = torch.zeros_like(mean)
    fresh = ~eligible.clone()
    row_index = 0
    for i in range(5):
        if eligible[i]:
            branches[i] = torch.multinomial(gate_logs[row_index].exp(), 1,
                                             generator=gate_rng)[0]
            gate_lp[i] = gate_logs[row_index, branches[i]]
            fresh[i] = branches[i] == END
            row_index += 1
        if fresh[i]:
            u[i] = mean[i] + actor.log_std.clamp(-5, 2).exp() * torch.randn(
                3, generator=velocity_rng)
    sent = previous.clone()
    sent[fresh] = u[fresh].tanh()
    logp = gate_lp + torch.where(fresh, tanh_log_prob(u, mean, actor.log_std), 0)
    # Every new command gets a first tick; only an actual KEEP forces the next renewal.
    next_eligible = fresh.clone()
    return sent.numpy(), u, branches, fresh, logp, next_eligible.numpy()


def add_event(counts, phase, name, amount):
    counts[name] = counts.get(name, 0) + amount
    counts[f"{phase}_{name}"] = counts.get(f"{phase}_{name}", 0) + amount


@torch.no_grad()
def collect_episode(env, actor, critic, horizon, reset_seed, velocity_rng, gate_rng,
                    metadata, check, counts, emit_episode, real=False):
    check()
    obs, info = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    state = info["state"]
    last = np.zeros((5, 3), dtype=np.float32)
    eligible = np.zeros(5, dtype=bool)
    hidden = torch.zeros(1, 5, 64)
    keys = ("obs", "hidden", "critic", "previous", "eligible", "branches", "u",
            "fresh", "logp", "value", "reward")
    storage = {key: [] for key in keys}
    rewards = []
    decisions = dict(gate_decisions=0, keep_decisions=0, end_decisions=0,
                     velocity_decisions=0, final_gate_credit_decisions=0)
    phase = metadata["phase"]
    for t in range(horizon):
        check()
        x = actor_features(obs, last, eligible.astype(np.int64))
        cx = critic_features(state, last, eligible.astype(np.int64))
        h0 = hidden[0].clone()
        mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        value = critic(torch.from_numpy(cx))
        if not torch.isfinite(mean).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite reactive learner during collection")
        sent, u, branches, fresh, logp, next_eligible = draw_commands(
            actor, mean, recurrent, last, eligible, velocity_rng, gate_rng)
        gate_mask = torch.from_numpy(eligible)
        keep = gate_mask & (branches == KEEP)
        events = dict(gate_decisions=int(gate_mask.sum()), keep_decisions=int(keep.sum()),
                      end_decisions=int((gate_mask & (branches == END)).sum()),
                      velocity_decisions=int(fresh.sum()),
                      final_gate_credit_decisions=int(gate_mask.sum()) if t + 1 == horizon else 0)
        for name, amount in events.items():
            decisions[name] += amount
            add_event(counts, phase, name, amount)
        counts["recurrent_observations"] += 5
        counts["step_calls"] += 1
        if real:
            counts["scientific_uav_calls"] += 1
        next_obs, _scalar, terminated, truncated, info = env.step(sent)
        counts["team_steps"] += 1
        counts[f"{phase}_team_steps"] += 1
        reward = team_reward(info)
        if not math.isfinite(reward):
            raise FloatingPointError("nonfinite native reactive reward")
        rewards.append(reward)
        values = (torch.from_numpy(x), h0, torch.from_numpy(cx), torch.from_numpy(last),
                  gate_mask, branches, u, fresh, logp, value,
                  torch.tensor(reward, dtype=torch.float32))
        for key, value_item in zip(keys, values):
            storage[key].append(value_item.detach().clone())
        last = sent.copy()
        eligible = next_eligible.copy()
        obs, state = next_obs, info["next_state"]
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete reactive episode: {t + 1}/{horizon}")
    total = sum(rewards)
    emit_episode(dict(metadata, reset_seed=reset_seed, steps=horizon,
                      reward_sum=total, J=total / horizon, **decisions))
    counts[f"{phase}_episodes"] += 1
    counts["completed_episode_steps"] += horizon
    check()
    return {key: torch.stack(values) for key, values in storage.items()}


def update(actor, critic, optimizer, episodes, chunk, check, counts):
    rollout = {key: torch.stack([ep[key] for ep in episodes]) for key in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw = targets - rollout["value"]
    advantage = ((raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)).detach()
    policy_mask = rollout["fresh"] | rollout["eligible"]
    parameters = list(actor.parameters()) + list(critic.parameters())
    records = []
    for epoch in range(4):
        check()
        mean, recurrent = recurrent_outputs(actor, rollout, chunk)
        logp = row_log_probs(actor, mean, recurrent, rollout["previous"],
                            rollout["eligible"], rollout["branches"], rollout["u"],
                            rollout["fresh"])
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantage, policy_mask)
        value_loss = (critic(rollout["critic"]) - targets).square().mean()
        loss = policy_loss + .5 * value_loss
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite reactive PPO loss")
        optimizer.zero_grad()
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError("nonfinite reactive gradient")
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite reactive parameter after Adam")
        records.append(dict(epoch=epoch, loss=float(loss.detach()),
                            policy_loss=float(policy_loss.detach()),
                            value_loss=float(value_loss.detach()), grad_norm=float(grad_norm)))
        check()
    return records
