"""Categorical collection and prefit-frozen, per-agent recurrent PPO."""
import math

import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    actor_features, critic_features, team_reward,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    recurrent_outputs, returns_to_go,
)
from .policy import (COMMANDS, action_terms, counterfactual_baseline, factual_inputs,
                     movement, sample_actions, snapshot)


def new_counts():
    return dict(constructors=0, constructor_resets=0, explicit_resets=0,
                step_calls=0, native_transitions=0, train_steps=0, eval_steps=0,
                train_episodes=0, eval_episodes=0, action_draws=0,
                rollouts=0, optimizer_steps=0, q_baseline_rows=0,
                v_baseline_rows=0, critic_fit_rows=0)


@torch.no_grad()
def collect_episode(env, actor, horizon, reset_seed, action_seed, metadata, counts,
                    emit, *, native=True):
    training = metadata["phase"] == "train"
    obs, info = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    state = info["state"]
    hidden = torch.zeros(1, 5, 64)
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    rng = torch.Generator().manual_seed(action_seed)
    storage = {k: [] for k in ("obs", "hidden", "critic", "actions", "probs", "logp", "reward")}
    rewards = []
    for tick in range(horizon):
        features = torch.from_numpy(actor_features(obs, last, remaining))
        old_hidden = hidden[0].clone()
        logits, _, hidden = actor(features[None], hidden)
        if not torch.isfinite(logits).all():
            raise FloatingPointError("nonfinite categorical logits")
        actions, probs, logp = sample_actions(logits[0], rng)
        sent = COMMANDS[actions].numpy().copy()
        counts["action_draws"] += 5
        context = torch.from_numpy(critic_features(state, last, remaining)) if training else None
        counts["step_calls"] += 1
        next_obs, _, terminated, truncated, info = env.step(sent)
        counts["native_transitions"] += int(native)
        counts[f"{metadata['phase']}_steps"] += 1
        reward = team_reward(info)
        if not math.isfinite(reward):
            raise FloatingPointError("nonfinite native team reward")
        rewards.append(reward)
        if training:
            values = (features, old_hidden, context, actions, probs, logp,
                      torch.tensor(reward, dtype=torch.float32))
            for key, value in zip(storage, values):
                storage[key].append(value.detach().clone())
        last = sent
        obs, state = next_obs, info["next_state"]
        if (terminated or truncated) and tick + 1 < horizon:
            raise RuntimeError(f"incomplete native episode at {tick + 1}/{horizon}")
    counts[f"{metadata['phase']}_episodes"] += 1
    row = dict(metadata, reset_seed=reset_seed, action_seed=action_seed, steps=horizon,
               reward_sum=sum(rewards), J=sum(rewards) / horizon)
    emit(row)
    return {key: torch.stack(value) for key, value in storage.items()} if training else row


@torch.no_grad()
def prepare_rollout(critic, episodes, arm, counts):
    rollout = {key: torch.stack([ep[key] for ep in episodes]) for key in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    rows = targets.numel()
    if arm == "Q":
        baseline, factual = counterfactual_baseline(
            critic, rollout["critic"], rollout["actions"], rollout["probs"])
        counts["q_baseline_rows"] += rows * 35
    else:
        factual = critic(rollout["critic"])
        baseline = factual[..., None].expand(*targets.shape, 5)
        counts["v_baseline_rows"] += rows
    raw = targets[..., None] - baseline
    advantage = (raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)
    rollout.update(targets=targets.detach().clone(), baseline=baseline.detach().clone(),
                   advantage=advantage.detach().clone())
    residual = targets - factual
    stats = {"prefit_residual_mean": float(residual.mean()),
             "prefit_residual_mse": float(residual.square().mean()),
             "raw_advantage_mean": float(raw.mean()),
             "raw_advantage_std": float(raw.std(unbiased=False))}
    return rollout, stats


def policy_loss(new_logp, old_logp, advantage):
    ratio = (new_logp - old_logp).exp()
    return -torch.minimum(ratio * advantage, ratio.clamp(.8, 1.2) * advantage).mean()


def optimizer_for(actor, critic):
    return torch.optim.Adam([{"params": list(actor.parameters())},
                             {"params": list(critic.parameters())}], lr=3e-4,
                            betas=(.9, .999), eps=1e-8, weight_decay=0,
                            foreach=False, fused=False)


def update(actor, critic, optimizer, episodes, arm, counts, chunk=32):
    # No optimizer step has yet consumed either episode's targets.
    rollout, record = prepare_rollout(critic, episodes, arm, counts)
    initial = snapshot(actor, critic)
    critic_inputs = (factual_inputs(rollout["critic"], rollout["actions"])
                     if arm == "Q" else rollout["critic"])
    epochs = []
    for epoch in range(4):
        logits, _ = recurrent_outputs(actor, rollout, chunk)
        logp, entropy = action_terms(logits, rollout["actions"])
        actor_loss = policy_loss(logp, rollout["logp"], rollout["advantage"]) - .01 * entropy.mean()
        value_loss = (critic(critic_inputs) - rollout["targets"]).square().mean()
        counts["critic_fit_rows"] += rollout["targets"].numel()
        loss = actor_loss + .5 * value_loss
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite PPO loss")
        optimizer.zero_grad()
        loss.backward()
        actor_norm = torch.nn.utils.clip_grad_norm_(actor.parameters(), .5)
        critic_norm = torch.nn.utils.clip_grad_norm_(critic.parameters(), .5)
        if not torch.isfinite(actor_norm) or not torch.isfinite(critic_norm):
            raise FloatingPointError("nonfinite PPO gradient")
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for group in optimizer.param_groups for p in group["params"]):
            raise FloatingPointError("nonfinite parameter after Adam")
        epochs.append(dict(epoch=epoch, actor_loss=float(actor_loss.detach()),
                           value_loss=float(value_loss.detach()), entropy=float(entropy.mean().detach()),
                           actor_preclip_norm=float(actor_norm), critic_preclip_norm=float(critic_norm)))
    counts["rollouts"] += 1
    record.update(epochs=epochs, movement=movement(initial, actor, critic),
                  optimizer_steps=4, team_training_rows=rollout["targets"].numel())
    return record
