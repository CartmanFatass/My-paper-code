"""Channel-aware collection and the source recurrent PPO loss, with actual sends."""

import math
import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import actor_features, critic_features, team_reward
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    returns_to_go, recurrent_outputs, clipped_policy_loss, optimizer_for,
)
from .channel import Channel
from .model import action_terms, sample_actions


@torch.no_grad()
def collect_episode(env, actor, critic, horizon, reset_seed, channel_seed, motion_rng,
                    send_rng, metadata, counts, emit, check):
    check()
    raw, info = env.reset(seed=reset_seed)
    state = info["state"]
    counts["explicit_resets"] += 1
    channel = Channel(channel_seed)
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    hidden = torch.zeros(1, 5, 64)
    storage = {k: [] for k in ("obs", "hidden", "critic", "u", "sends", "eligible", "logp", "value", "reward")}
    physical, charges = [], []
    for t in range(horizon):
        check()
        channel.begin_tick()
        extras = channel.features()
        x = torch.from_numpy(np.concatenate((actor_features(raw, last, remaining), extras), axis=1))
        cx = torch.from_numpy(np.concatenate((critic_features(state, last, remaining), extras.ravel())))
        h0 = hidden[0].clone()
        mean, recurrent, hidden = actor(x[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        value = critic(cx)
        eligible = torch.from_numpy(~channel.pending.copy())
        u, sends = sample_actions(actor, mean, recurrent, eligible, t, motion_rng, send_rng)
        logp, _ = action_terms(actor, mean, recurrent, u, sends, eligible)
        if not torch.isfinite(logp).all() or not torch.isfinite(value):
            raise FloatingPointError("nonfinite sampled density or critic")
        command = u.tanh().numpy()
        charge = channel.resolve(sends.numpy(), raw)
        counts["motion_decisions"] += 5
        counts["send_decisions"] += int(eligible.sum()) if actor.send is not None else 0
        counts["attempts"] += int(sends.sum())
        raw_next, _, terminated, truncated, info = env.step(command)
        counts["team_steps"] += 1
        counts[f"{metadata['phase']}_team_steps"] += 1
        reward_physical = team_reward(info)
        reward_net = reward_physical - charge
        if not math.isfinite(reward_net):
            raise FloatingPointError("nonfinite net native reward")
        physical.append(reward_physical)
        charges.append(charge)
        values = (x, h0, cx, u, sends, eligible, logp, value, torch.tensor(reward_net))
        for key, value in zip(storage, values):
            storage[key].append(value.detach().clone())
        last[:] = command
        raw, state = raw_next, info["next_state"]
        channel.advance()
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete native episode {t+1}/{horizon}")
    row = dict(metadata, reset_seed=reset_seed, channel_seed=channel_seed, steps=horizon,
               reward_sum=sum(physical)-sum(charges), physical_reward_sum=sum(physical),
               communication_charge=sum(charges), J_net=(sum(physical)-sum(charges))/horizon,
               J_physical=sum(physical)/horizon, charge_per_tick=sum(charges)/horizon,
               **channel.facts())
    emit(row)
    counts[f"{metadata['phase']}_episodes"] += 1
    check()
    return {k: torch.stack(v) for k, v in storage.items()}


def update(actor, critic, optimizer, episodes, counts, check, chunk=32):
    rollout = {k: torch.stack([ep[k] for ep in episodes]) for k in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw = targets - rollout["value"]
    advantages = ((raw-raw.mean()) / (raw.std(unbiased=False)+1e-8)).detach()
    parameters = list(actor.parameters()) + list(critic.parameters())
    records = []
    for epoch in range(4):
        check()
        mean, recurrent = recurrent_outputs(actor, rollout, chunk)
        logp, entropy = action_terms(actor, mean, recurrent, rollout["u"], rollout["sends"], rollout["eligible"])
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantages,
                                          torch.ones_like(logp, dtype=torch.bool))
        value_loss = (critic(rollout["critic"])-targets).square().mean()
        loss = policy_loss + .5*value_loss - .01*entropy.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite PPO loss")
        optimizer.zero_grad()
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(norm):
            raise FloatingPointError("nonfinite PPO gradient")
        check()
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite Adam parameters")
        records.append(dict(epoch=epoch, loss=float(loss.detach()), policy_loss=float(policy_loss.detach()),
                            value_loss=float(value_loss.detach()), entropy=float(entropy.mean().detach()), grad_norm=float(norm)))
    return records
