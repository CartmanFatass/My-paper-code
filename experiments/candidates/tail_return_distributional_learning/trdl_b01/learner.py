"""TRDL B01: factual episode targets and a frozen lower-tail PPO score.

Scientific laws: TRDL_B01_SCIENCE_CARD_20260914.md, supported by A01 E0's
Tamar Proposition1 / Dabney Eq8 reading. This is the finite carded package,
not a CVaR-gradient theorem or the source learner's return-to-go update.
"""
import math
import time

import numpy as np
import torch
from torch import nn

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    DENSE, NativeGeometryActor)
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import (
    actor_features, critic_features, team_reward)
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    clipped_policy_loss, optimizer_for, recurrent_outputs)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    Actor, generator, sample, tanh_log_prob)

ARMS = ("SCALAR", "Q32")
HORIZON, BATCH, TRAIN_EPISODES, EVAL_EPISODES = 256, 16, 512, 256
ALPHA, QUANTILES, EPOCHS, CHUNK = .25, 32, 4, 32


class TailCritic(nn.Module):
    def __init__(self, arm, base):
        super().__init__()
        if arm not in ARMS:
            raise ValueError(arm)
        self.arm = arm
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(base + 13)
            self.trunk = nn.Sequential(nn.Linear(137, 128), nn.Tanh(),
                                       nn.Linear(128, 128), nn.Tanh())
            torch.manual_seed(base + (14 if arm == "SCALAR" else 15))
            self.head = nn.Linear(128, 1 if arm == "SCALAR" else QUANTILES)

    def forward(self, context):
        output = self.head(self.trunk(context))
        return output.squeeze(-1) if self.arm == "SCALAR" else output


def models(master, arm):
    base = 100000 * master
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(base + 11)
        common = Actor()
    return NativeGeometryActor(common, DENSE, base + 12), TailCritic(arm, base)


def critic_context(state, last, past_reward_sum, horizon=HORIZON):
    """Only rewards strictly before this action enter the context."""
    common = critic_features(state, last, np.zeros(5, dtype=np.int64))
    return np.concatenate((common, [past_reward_sum / horizon])).astype(np.float32)


def tail_score(values, eta):
    return torch.where(values <= eta, (values - eta) / ALPHA, 0)


def pinball(predictions, targets):
    levels = (torch.arange(QUANTILES, device=predictions.device,
                           dtype=predictions.dtype) + .5) / QUANTILES
    error = targets[..., None] - predictions
    return ((levels - (error < 0).to(error.dtype)) * error).mean()


@torch.no_grad()
def frozen_batch(critic, episodes):
    """One empirical threshold and pre-update baseline for all four epochs."""
    batch = {key: torch.stack([episode[key] for episode in episodes]).detach()
             for key in episodes[0]}
    returns = batch["G"]  # FP32 conversion already made after native accumulation.
    eta = returns.sort().values[math.ceil(ALPHA * len(episodes)) - 1]
    scores = tail_score(returns, eta)
    predictions = critic(batch["critic"])
    baseline = (predictions if critic.arm == "SCALAR"
                else tail_score(predictions, eta).mean(-1))
    batch.update(eta=eta, scores=scores, baseline=baseline,
                 advantages=scores[:, None] - baseline)
    return batch


def update(actor, critic, optimizer, batch, check, counts, emit_update,
           chunk=CHUNK):
    parameters = list(actor.parameters()) + list(critic.parameters())
    mask = torch.ones_like(batch["logp"], dtype=torch.bool)
    factual = batch["G"][:, None].expand(batch["critic"].shape[:2])
    scalar_target = batch["scores"][:, None].expand_as(factual)
    for epoch in range(EPOCHS):
        check()
        started = time.monotonic()
        mean, _ = recurrent_outputs(actor, batch, chunk)
        logp = tanh_log_prob(batch["u"], mean, actor.log_std)
        actor_loss = clipped_policy_loss(logp, batch["logp"], batch["advantages"], mask)
        prediction = critic(batch["critic"])
        critic_loss = ((prediction - scalar_target).square().mean()
                       if critic.arm == "SCALAR" else pinball(prediction, factual))
        loss = actor_loss + .5 * critic_loss
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite TRDL loss")
        optimizer.zero_grad()
        loss.backward()
        actor_grad = torch.stack([p.grad.norm() for p in actor.parameters()
                                  if p.grad is not None]).norm()
        critic_grad = torch.stack([p.grad.norm() for p in critic.parameters()
                                   if p.grad is not None]).norm()
        norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(norm):
            raise FloatingPointError("nonfinite TRDL gradient")
        check()
        counts["optimizer_attempts"] += 1
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite TRDL parameter after Adam")
        emit_update(dict(epoch=epoch, actor_loss=float(actor_loss.detach()),
                         critic_loss=float(critic_loss.detach()), loss=float(loss.detach()),
                         grad_norm=float(norm), actor_grad_norm=float(actor_grad),
                         critic_grad_norm=float(critic_grad), eta=float(batch["eta"]),
                         strictly_negative_scores=int((batch["scores"] < 0).sum()),
                         optimizer_step=counts["optimizer_steps"],
                         wall_seconds=time.monotonic() - started))


@torch.no_grad()
def collect_episode(env, actor, reset_seed, velocity_rng, phase, episode,
                    check, counts, emit_episode, horizon=HORIZON):
    """Fixed primitive motion; native scalar average is deliberately ignored."""
    check()
    started = time.monotonic()
    counts["reset_calls"] += 1
    obs, info = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    reset_wall = time.monotonic() - started
    state, past_reward = info["state"], 0.0
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    hidden = torch.zeros(1, 5, 64)
    training = phase == "train"
    storage = {key: [] for key in ("obs", "hidden", "critic", "u", "logp")}
    active = np.ones(5, dtype=bool)
    for tick in range(horizon):
        check()
        x = actor_features(obs, last, remaining)
        context = critic_context(state, last, past_reward, horizon) if training else None
        h0 = hidden[0]
        mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
        mean, recurrent = mean[0], recurrent[0]
        if not torch.isfinite(mean).all():
            raise FloatingPointError("nonfinite actor mean")
        u, _ = sample(actor, mean, recurrent, active, False, velocity_rng, None)
        logp = tanh_log_prob(u, mean, actor.log_std)
        if not torch.isfinite(logp).all():
            raise FloatingPointError("nonfinite behavior density")
        sent = u.tanh().numpy()
        counts["velocity_decisions"] += 5
        counts["recurrent_observations"] += 5
        counts["step_calls"] += 1
        next_obs, _averaged_scalar, terminated, truncated, info = env.step(sent)
        counts["team_steps"] += 1
        counts[f"{phase}_team_steps"] += 1
        reward = team_reward(info)
        if not math.isfinite(reward):
            raise FloatingPointError("nonfinite native team reward")
        if training:
            for key, value in (("obs", torch.from_numpy(x)), ("hidden", h0),
                               ("critic", torch.from_numpy(context)), ("u", u),
                               ("logp", logp)):
                storage[key].append(value.detach().clone())
        past_reward += reward  # Python double, in native temporal order.
        last, obs, state = sent.copy(), next_obs, info["next_state"]
        if (terminated or truncated) and tick + 1 < horizon:
            raise RuntimeError(f"incomplete {phase} episode: {tick + 1}/{horizon}")
    row = dict(phase=phase, episode=episode, reset_seed=reset_seed, steps=horizon,
               reward_sum=past_reward, J=past_reward / horizon,
               reset_wall_seconds=reset_wall, wall_seconds=time.monotonic() - started)
    emit_episode(row)
    counts[f"{phase}_episodes"] += 1
    counts["completed_episode_steps"] += horizon
    if not training:
        return None, row
    rollout = {key: torch.stack(values) for key, values in storage.items()}
    rollout["G"] = torch.tensor(row["J"], dtype=torch.float32)
    return rollout, row


def action_generator(master, arm, evaluation_episode=None):
    base = 100000 * master
    if evaluation_episode is None:
        offset = 21 if arm == "SCALAR" else 22
    else:
        offset = (3000 if arm == "SCALAR" else 6000) + evaluation_episode
    return generator(base + offset)


def endpoint(returns):
    """One arm's own empirical lower quarter, reduced in double precision."""
    values = np.asarray(returns, dtype=np.float64)
    if values.shape != (EVAL_EPISODES,) or not np.isfinite(values).all():
        raise ValueError("requires 256 finite final returns from this arm")
    ordered = np.sort(values)
    return dict(mean=float(values.mean()), lower_tail=float(ordered[:64].mean()),
                tail_threshold=float(ordered[63]), returns=values.tolist())


def contrast(scalar_returns, quantile_returns):
    scalar, quantile = endpoint(scalar_returns), endpoint(quantile_returns)
    delta = quantile["lower_tail"] - scalar["lower_tail"]
    branch = ("Q32_ABOVE_MEI" if delta > .01 else
              "SCALAR_ABOVE_MEI" if delta < -.01 else "INSIDE_MEI")
    return dict(SCALAR=scalar, Q32=quantile, delta_tail=delta,
                delta_mean=quantile["mean"] - scalar["mean"], branch=branch,
                independent_training_instances_per_arm=1,
                uncertainty="conditional order-statistic tails; no training-population interval")
