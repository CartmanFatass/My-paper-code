"""Complete primitive episodes and four full-rollout recurrent PPO epochs."""
import math

import numpy as np
import torch

from .environment import (AGENTS, HoldState, actor_features, critic_features,
                          local_indices, own_positions, team_reward)
from .policy import joint_terms, sample


def returns_to_go(rewards):
    """Last axis is one complete episode, with no terminal bootstrap."""
    return rewards.flip(-1).cumsum(-1).flip(-1)


def clipped_policy_loss(new_logp, old_logp, advantage, velocity_mask=None):
    if velocity_mask is not None:
        advantage = advantage[..., None]
    ratio = (new_logp - old_logp).exp()
    surrogate = torch.minimum(ratio * advantage, ratio.clamp(.8, 1.2) * advantage)
    if velocity_mask is not None:
        # Keep every primitive row, including all-held rows, in the denominator.
        surrogate = torch.where(velocity_mask, surrogate, 0).sum(-1)
    return -surrogate.mean()


@torch.no_grad()
def collect_episode(env, actor, critic, horizon, reset_seed, velocity_rng, duration_rng,
                    metadata, check, counts, emit_episode, emit_diagnostic, limits,
                    real=False, diagnostics=False, ratio_grouping="joint", value_moments=None, renewal=False,
                    duration_support=(1, 4), velocity_mode="sampled"):
    """Counts survive an exception; only a complete episode emits a scored row."""
    check()
    obs, info = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    check()
    state = info["state"]
    hold = HoldState(renewal=renewal)
    hidden = torch.zeros(1, 5, 64)
    storage = {key: [] for key in ("obs", "hidden", "critic", "u", "durations",
                                   "velocity_mask", "duration_mask", "logp", "value", "reward")}
    rewards, commands, services = [], [], []
    first_position = own_positions(obs)
    prefix_position = first_position.copy()
    prefix_path = np.zeros(5, dtype=np.float64)
    decisions = {"velocity_decisions": 0, "duration_decisions": 0, "d4": 0}
    short = duration_support == (1, 2)
    if short:
        decisions["d2"] = 0
    if renewal:
        decisions.update(horizon_censored_holds=0, suppressed_decisions=0)
    for t in range(horizon):
        check()
        x = actor_features(obs, hold.last, hold.remaining)
        cx = critic_features(state, hold.last, hold.remaining)
        remaining_before = hold.remaining.copy()
        active = hold.remaining == 0
        duration_mask = np.full(5, actor is not None and actor.duration is not None and t == 0)
        if renewal:
            duration_mask = active & (actor is not None and actor.duration is not None)
        h0 = hidden[0].clone()
        selected_steps = np.ones(5, dtype=np.int64)
        if actor is None:
            sent = np.zeros((5, 3), dtype=np.float32)
            u, duration = torch.zeros(5, 3), torch.zeros(5, dtype=torch.long)
            logp, value = torch.tensor(0.), torch.tensor(0.)
            if ratio_grouping == "agent_compound":
                logp = torch.zeros(5)
            active = np.zeros(5, dtype=bool)
        else:
            mean, recurrent, hidden = actor(torch.from_numpy(x)[None], hidden)
            mean, recurrent = mean[0], recurrent[0]
            value = critic(torch.from_numpy(cx))
            if value_moments is not None:
                value = value_moments.decode(value)
            if not torch.isfinite(mean).all() or not torch.isfinite(value):
                raise FloatingPointError("nonfinite learner during collection")
            sample_options = {"duration_mask": duration_mask} if renewal else {}
            if velocity_mode == "mean":
                sample_options["velocity_mode"] = velocity_mode
            u, duration = sample(actor, mean, recurrent, active, t == 0,
                                 velocity_rng, duration_rng, **sample_options)
            selected_steps = np.where(duration.numpy() == 1, duration_support[1], duration_support[0])
            sent, active = hold.decide(t, u.tanh().numpy(), selected_steps)
            logp, _ = joint_terms(actor, mean, recurrent, u, duration,
                                  torch.from_numpy(active), torch.from_numpy(duration_mask),
                                  ratio_grouping)
            if not torch.isfinite(logp).all():
                raise FloatingPointError("nonfinite sampled density")
        frames = []
        if diagnostics and t <= 4:
            for i in range(5):
                frame = dict(metadata, reset_seed=reset_seed, time=t, agent=AGENTS[i],
                             actor_input=x[i].copy().tolist(), remaining_hold=int(remaining_before[i]),
                             actual_decision=bool(active[i]), sent_velocity=sent[i].copy().tolist(),
                             chosen_duration=(int(selected_steps[i]) if duration_mask[i] else None))
                try:
                    frame.update(local_indices(env, i))
                except Exception as error:
                    message = f"source diagnostics: {type(error).__name__}: {error}"
                    if message not in limits:
                        limits.append(message)
                    frame["diagnostic_error"] = message
                frames.append(frame)
        # These are actual sampling/observation events even if the next call fails.
        events = (("velocity_decisions", int(active.sum())),
                  ("duration_decisions", int(duration_mask.sum())),
                  ("d4", int(((selected_steps == 4) & duration_mask).sum())))
        if short:
            events += (("d2", int(((selected_steps == 2) & duration_mask).sum())),)
        for key, number in events:
            decisions[key] += number
            counts[key] += number
            if renewal:
                counts[f"{metadata['phase']}_{key}"] += number
        if actor is not None:
            counts["recurrent_observations"] += 5
        check()
        before = own_positions(obs)
        counts["step_calls"] += 1
        if real:
            counts["scientific_uav_calls"] += 1
        next_obs, _scalar, terminated, truncated, info = env.step(sent)
        counts["team_steps"] += 1
        counts[f"{metadata['phase']}_team_steps"] += 1
        if renewal:
            # Only executed held steps suppress decisions. A remaining timer >1
            # on the final executed step identifies an actually censored label.
            for key, number in (("suppressed_decisions", int((remaining_before > 0).sum())),
                                ("horizon_censored_holds", int((hold.remaining > 1).sum())
                                 if t + 1 == horizon else 0)):
                decisions[key] += number
                counts[key] += number
                counts[f"{metadata['phase']}_{key}"] += number
        reward = team_reward(info)
        if not math.isfinite(reward):
            raise FloatingPointError("nonfinite native team reward")
        rewards.append(reward)
        commands.append(float(np.linalg.norm(sent, axis=1).mean()))
        try:
            services.append(float(info["infos_dict"][AGENTS[0]]["global"]["served_users"]))
        except (KeyError, TypeError, ValueError) as error:
            message = f"service diagnostic: {type(error).__name__}: {error}"
            if message not in limits:
                limits.append(message)
        if t < 4:
            prefix_position = own_positions(next_obs)
            prefix_path += np.linalg.norm(prefix_position - before, axis=1)
        for frame in frames:
            frame["team_reward"] = reward
            try:
                emit_diagnostic(frame)
                counts["diagnostic_frames"] += 1
            except Exception as error:
                message = f"diagnostic publication: {type(error).__name__}: {error}"
                if message not in limits:
                    limits.append(message)
        values = (torch.from_numpy(x), h0, torch.from_numpy(cx), u, duration,
                  torch.from_numpy(active), torch.from_numpy(duration_mask), logp,
                  value, torch.tensor(reward, dtype=torch.float32))
        for key, item in zip(storage, values):
            storage[key].append(item.detach().clone())
        hold.advance(sent)
        obs, state = next_obs, info["next_state"]
        if (terminated or truncated) and t + 1 < horizon:
            raise RuntimeError(f"incomplete episode: boundary at {t + 1}/{horizon}")
        # Preserve an episode completed by an indivisible call before detecting its overrun.
        if t + 1 < horizon:
            check()
    total = sum(rewards)
    row = dict(metadata, reset_seed=reset_seed, steps=horizon, reward_sum=total,
               J=total / horizon, prefix_reward_sum=sum(rewards[:4]),
               suffix_reward_sum=sum(rewards[4:]), mean_commanded_velocity_norm=float(np.mean(commands)),
               prefix_displacement=np.linalg.norm(prefix_position - first_position, axis=1).tolist(),
               prefix_path_length=prefix_path.tolist(),
               mean_served_connections=(sum(services) / horizon if len(services) == horizon else None),
               **decisions)
    emit_episode(row)
    counts[f"{metadata['phase']}_episodes"] += 1
    counts["completed_episode_steps"] += horizon
    check()
    return {key: torch.stack(items) for key, items in storage.items()}


def recurrent_outputs(actor, rollout, chunk):
    # E,H,agent -> chunk,within-chunk,agent. Batch fixed independent sequences.
    observations = rollout["obs"]
    episodes, horizon, agents, features = observations.shape
    nchunks = episodes * (horizon // chunk)
    x = observations.reshape(nchunks, chunk, agents, features)
    x = x.permute(1, 0, 2, 3).reshape(chunk, nchunks * agents, features)
    h0 = rollout["hidden"][:, ::chunk].reshape(1, nchunks * agents, 64).detach()
    mean, recurrent, _ = actor(x, h0)
    def restore(value):
        return value.reshape(chunk, nchunks, agents, -1).permute(1, 0, 2, 3).reshape(
            episodes, horizon, agents, -1)
    return restore(mean), restore(recurrent)


def optimizer_for(actor, critic):
    return torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4,
                            betas=(.9, .999), eps=1e-8, weight_decay=0, amsgrad=False,
                            foreach=False, fused=False)


def update(actor, critic, optimizer, episodes, chunk, check, counts, ratio_grouping="joint",
           entropy_coef=0.01, value_moments=None):
    rollout = {key: torch.stack([ep[key] for ep in episodes]) for key in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw = targets - rollout["value"]
    advantages = ((raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)).detach()
    if value_moments is not None:
        value_moments.update(targets)
        targets = value_moments.normalize(targets)
    parameters = list(actor.parameters()) + list(critic.parameters())
    records = []
    for epoch in range(4):
        check()
        mean, recurrent = recurrent_outputs(actor, rollout, chunk)
        logp, entropy = joint_terms(actor, mean, recurrent, rollout["u"], rollout["durations"],
                                    rollout["velocity_mask"], rollout["duration_mask"], ratio_grouping)
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantages,
                                          rollout["velocity_mask"] if ratio_grouping == "agent_compound" else None)
        value_loss = (critic(rollout["critic"]) - targets).square().mean()
        loss = policy_loss + .5 * value_loss - entropy_coef * entropy.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite PPO loss")
        optimizer.zero_grad()
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError("nonfinite PPO gradient")
        check()
        optimizer.step()
        counts["optimizer_steps"] += 1
        if not all(torch.isfinite(p).all() for p in parameters):
            raise FloatingPointError("nonfinite parameters after Adam")
        records.append({"epoch": epoch, "loss": float(loss.detach()),
                        "policy_loss": float(policy_loss.detach()),
                        "value_loss": float(value_loss.detach()),
                        "entropy": float(entropy.mean().detach()), "grad_norm": float(grad_norm)})
        if value_moments is not None:
            records[-1]["value_loss_units"] = "normalized_squared"
        check()
    return records
