"""Actual-command collection and gate-only primitive-time PPO."""
import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import actor_features, critic_features, team_reward
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import returns_to_go, clipped_policy_loss, optimizer_for
from .binding import Binding
from .model import action_generators, proposal_sample, gate_sample, gate_terms


@torch.no_grad()
def collect(env, base, gate, critic, seed, arm, phase, episode, horizon, check, counts, emit):
    check()
    reset_seed = seed * 100000 + (1000 if phase == "train" else 2000) + episode
    obs, info = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    state = info["state"]
    last = np.zeros((5, 3), dtype=np.float32)
    remaining = np.zeros(5, dtype=np.int64)
    base_hidden = torch.zeros(1, 5, 64)
    hidden = gate.initial_state() if gate is not None else None
    binding = Binding() if arm != "C" else None
    proposal_rng, gate_rng = action_generators(seed, arm, phase, episode)
    storage = {k: [] for k in ("x", "hidden", "z", "b", "u", "choice", "mask", "logp", "value", "critic", "reward")}
    decisions = {"opportunities": 0, "retrace": 0, "apply": 0, "distinguishable": 0}
    rewards = []
    for t in range(horizon):
        check()
        x = torch.from_numpy(actor_features(obs, last, remaining))
        mean, _, base_hidden = base(x[None], base_hidden)
        u, b = proposal_sample(base, mean[0], proposal_rng)
        if binding is None:
            z, mask, c = np.zeros((5, 13), np.float32), np.zeros(5, bool), np.zeros((5, 3), np.float32)
        else:
            z, mask, c = binding.observe(obs, b.numpy())
        z, mask = torch.from_numpy(z), torch.from_numpy(mask)
        choices = mask.float() if arm == "F" else torch.zeros(5)
        logp, value = torch.zeros(5), torch.tensor(0.)
        if gate is not None:
            h0 = hidden.clone()
            logits, hidden = gate(x[None], b[None], z[None], hidden)
            choices = gate_sample(logits[0], mask, gate_rng)
            logp, _ = gate_terms(logits[0], choices, mask)
        sent = np.where((choices.numpy() == 1)[:, None], c, b.numpy()).astype(np.float32)
        cx = torch.from_numpy(critic_features(state, last, remaining)) if critic is not None else None
        if critic is not None:
            value = critic(cx)
        n = int(mask.sum())
        nr = int(choices.sum())
        decisions["opportunities"] += n
        decisions["retrace"] += nr
        decisions["apply"] += n - nr
        decisions["distinguishable"] += int((mask.numpy() & np.any(c != b.numpy(), axis=1)).sum())
        counts["base_agent_forwards"] += 5
        counts["learned_gate_agent_forwards"] += 5 if gate is not None else 0
        counts["step_calls"] += 1
        obs, _, terminated, truncated, info = env.step(sent)
        counts["team_steps"] += 1
        reward = team_reward(info)
        rewards.append(reward)
        if phase == "train":
            values = (x, h0, z, b, u, choices, mask, logp, value, cx, torch.tensor(reward, dtype=torch.float32))
            for key, value in zip(storage, values):
                storage[key].append(value.detach().clone())
        last = sent.copy()
        state = info["next_state"]
        if (terminated or truncated) and t + 1 != horizon:
            raise RuntimeError(f"early episode termination at {t + 1}")
    row = dict(arm=arm, phase=phase, episode=episode, reset_seed=reset_seed,
               steps=horizon, S=sum(rewards), J=sum(rewards) / horizon, **decisions)
    emit(row)
    counts[phase + "_episodes"] += 1
    check()
    return {k: torch.stack(v) for k, v in storage.items()} if phase == "train" else None


def recurrent_logits(gate, rollout, chunk=32):
    episodes, horizon, agents, _ = rollout["x"].shape
    nchunks = episodes * (horizon // chunk)
    def sequence(key):
        value = rollout[key]
        width = value.shape[-1]
        return value.reshape(nchunks, chunk, agents, width).permute(1, 0, 2, 3).reshape(chunk, nchunks * agents, width)
    # Stored shape E,H,path,agent,hidden. Each chunk owns its detached start.
    h0 = rollout["hidden"][:, ::chunk].reshape(nchunks, -1, agents, 32)
    h0 = h0.permute(1, 0, 2, 3).reshape(-1, nchunks * agents, 32).detach()
    logits, _ = gate(sequence("x"), sequence("b"), sequence("z"), h0)
    return logits.reshape(chunk, nchunks, agents).permute(1, 0, 2).reshape(episodes, horizon, agents)


def update(gate, critic, optimizer, episodes, check, counts):
    rollout = {k: torch.stack([e[k] for e in episodes]) for k in episodes[0]}
    targets = returns_to_go(rollout["reward"])
    raw = targets - rollout["value"]
    advantage = ((raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)).detach()
    records = []
    parameters = list(gate.parameters()) + list(critic.parameters())
    for epoch in range(4):
        check()
        logits = recurrent_logits(gate, rollout)
        logp, entropy = gate_terms(logits, rollout["choice"], rollout["mask"])
        policy_loss = clipped_policy_loss(logp, rollout["logp"], advantage, velocity_mask=rollout["mask"])
        value_loss = (critic(rollout["critic"]) - targets).square().mean()
        loss = policy_loss + .5 * value_loss - .01 * entropy.mean()
        optimizer.zero_grad()
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(parameters, .5)
        optimizer.step()
        counts["optimizer_steps"] += 1
        records.append(dict(epoch=epoch, loss=float(loss.detach()), policy_loss=float(policy_loss.detach()),
                            value_loss=float(value_loss.detach()), entropy=float(entropy.mean().detach()),
                            grad_norm=float(grad_norm), opportunities=int(rollout["mask"].sum())))
        check()
    return records
