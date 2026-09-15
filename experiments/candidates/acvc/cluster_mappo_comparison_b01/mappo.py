"""Pinned MAPPO with the selected raw-tanh density and native private-state adapter.

Upstream (read-only dependency): marlbenchmark/on-policy at de66d7a4b23fac2513f56f96f73b3f5cb96695ac.
R_MAPPO retains its own GAE, ValueNorm, clipped Huber loss, recurrent generator and optimizers.
"""
import math

import numpy as np
import torch
from gymnasium.spaces import Box
from torch import nn

from onpolicy.config import get_config
from onpolicy.algorithms.r_mappo.algorithm.rMAPPOPolicy import R_MAPPOPolicy
from onpolicy.algorithms.r_mappo.r_mappo import R_MAPPO
from onpolicy.utils.shared_buffer import SharedReplayBuffer

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import actor_features, critic_features, team_reward
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, tanh_log_prob
from .protocol import MASTER, EVALUATION_NAMESPACE, HORIZON, EVAL_EPISODES


def configuration():
    args = get_config().parse_args([])
    settings = dict(algorithm_name="rmappo", seed=MASTER, hidden_size=64, recurrent_N=1,
                    layer_N=1, use_ReLU=True, use_feature_normalization=True,
                    use_orthogonal=True, gain=.01, use_recurrent_policy=True,
                    use_naive_recurrent_policy=False, episode_length=HORIZON,
                    n_rollout_threads=2, ppo_epoch=4, num_mini_batch=1, data_chunk_length=32,
                    gamma=.99, gae_lambda=.95, use_gae=True, use_proper_time_limits=False,
                    clip_param=.2, entropy_coef=.01, value_loss_coef=1.,
                    use_max_grad_norm=True, max_grad_norm=.5, lr=3e-4, critic_lr=3e-4,
                    opti_eps=1e-5, weight_decay=0., use_linear_lr_decay=False,
                    use_valuenorm=True, use_popart=False, use_clipped_value_loss=True,
                    use_huber_loss=True, huber_delta=10.,
                    use_value_active_masks=True, use_policy_active_masks=True)
    for key, value in settings.items():
        setattr(args, key, value)
    return args, settings


class MotionHead(nn.Module):
    """Return raw u to replay, execute tanh(u) only at the native environment boundary."""
    def __init__(self, seed):
        super().__init__()
        self.mean = nn.Linear(64, 3)
        nn.init.orthogonal_(self.mean.weight, gain=.01)
        nn.init.zeros_(self.mean.bias)
        self.log_std = nn.Parameter(torch.zeros(3))
        self.generator = generator(seed)

    def forward(self, x, available_actions=None, deterministic=False):
        mean = self.mean(x)
        raw = mean if deterministic else mean + self.log_std.clamp(-5, 2).exp() * torch.randn(
            mean.shape, generator=self.generator, dtype=mean.dtype, device=mean.device)
        return raw, tanh_log_prob(raw, mean, self.log_std).unsqueeze(-1)

    def evaluate_actions(self, x, action, available_actions=None, active_masks=None):
        logp = tanh_log_prob(action, self.mean(x), self.log_std).unsqueeze(-1)
        entropy = (self.log_std.clamp(-5, 2) + .5 * math.log(2 * math.pi * math.e)).sum()
        return logp, entropy


def make_policy(args):
    spaces = (Box(-np.inf, np.inf, (108,), dtype=np.float32),
              Box(-np.inf, np.inf, (136,), dtype=np.float32),
              Box(-1., 1., (3,), dtype=np.float32))
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(100000 * MASTER + 131)
        policy = R_MAPPOPolicy(args, *spaces, device=torch.device("cpu"))
        policy.actor.act = MotionHead(100000 * MASTER + 121)
        # The old optimizer refers to the upstream unsquashed head; no update has run.
        policy.actor_optimizer = torch.optim.Adam(policy.actor.parameters(), lr=args.lr,
                                                  eps=args.opti_eps, weight_decay=args.weight_decay)
    return policy, spaces


def make_buffer(args, spaces):
    buffer = SharedReplayBuffer(args, 5, *spaces)
    # One joint three-coordinate likelihood, not three broadcast copies of its sum.
    buffer.action_log_probs = np.zeros_like(buffer.rewards)
    return buffer


def count_steps(optimizer, counts, key):
    original = optimizer.step
    counts[key] = 0

    def counted(*args, **kwargs):
        result = original(*args, **kwargs)
        counts[key] += 1
        counts["optimizer_steps"] += 1
        return result
    optimizer.step = counted


def parameter_snapshot(policy):
    return {name: torch.cat([p.detach().flatten() for p in module.parameters()]).clone()
            for name, module in (("actor", policy.actor), ("critic", policy.critic),
                                 ("action_head", policy.actor.act))}


def parameter_exposure(initial, policy):
    final = parameter_snapshot(policy)
    return {name: dict(parameters=a.numel(), initial_norm=float(a.norm()), final_norm=float(final[name].norm()),
                       displacement=float((final[name] - a).norm()),
                       finite=bool(torch.isfinite(final[name]).all())) for name, a in initial.items()}


def features(obs, state, last):
    own = actor_features(obs, last, np.zeros(5, dtype=np.int64))
    central = critic_features(state, last, np.zeros(5, dtype=np.int64))
    return own, np.repeat(central[None], 5, axis=0)


@torch.no_grad()
def fill_rollout(policy, buffer, envs, episodes, counts, emit):
    """Two isolated complete episodes; state[t] is before observation[t]."""
    policy.actor.eval()
    policy.critic.eval()
    horizon, lanes = buffer.episode_length, len(envs)
    last = np.zeros((lanes, 5, 3), dtype=np.float32)
    rewards_by_lane = [[] for _ in envs]
    buffer.rnn_states[0].fill(0)
    buffer.rnn_states_critic[0].fill(0)
    buffer.masks[0].fill(0)
    for lane, (env, episode) in enumerate(zip(envs, episodes)):
        obs, info = env.reset(seed=100000 * MASTER + 1000 + episode)
        counts["explicit_resets"] += 1
        buffer.obs[0, lane], buffer.share_obs[0, lane] = features(obs, info["state"], last[lane])
    for step in range(horizon):
        values, raw, logp, actor_state, critic_state = policy.get_actions(
            np.concatenate(buffer.share_obs[step]), np.concatenate(buffer.obs[step]),
            np.concatenate(buffer.rnn_states[step]), np.concatenate(buffer.rnn_states_critic[step]),
            np.concatenate(buffer.masks[step]))
        sent = raw.tanh().cpu().numpy().reshape(lanes, 5, 3)
        astate = actor_state.cpu().numpy().reshape(lanes, 5, 1, 64)
        cstate = critic_state.cpu().numpy().reshape(lanes, 5, 1, 64)
        next_obs, next_central = np.empty_like(buffer.obs[0]), np.empty_like(buffer.share_obs[0])
        rewards, masks = np.zeros_like(buffer.rewards[0]), np.ones_like(buffer.masks[0])
        counts["train_actor_agent_forwards"] += lanes * 5
        counts["critic_forwards"] += lanes * 5
        for lane, env in enumerate(envs):
            counts["step_calls"] += 1
            counts["scientific_uav_calls"] += 1
            obs, _, terminated, truncated, info = env.step(sent[lane])
            counts["team_steps"] += 1
            counts["train_team_steps"] += 1
            value = team_reward(info)
            rewards_by_lane[lane].append(value)
            rewards[lane, :, 0] = value
            if truncated or bool(terminated) != (step + 1 == horizon):
                raise RuntimeError(f"unexpected native boundary at {step + 1}/{horizon}: {terminated=}, {truncated=}")
            last[lane] = sent[lane]
            next_obs[lane], next_central[lane] = features(obs, info["next_state"], last[lane])
            if terminated:
                masks[lane].fill(0)
                astate[lane].fill(0)
                cstate[lane].fill(0)
        buffer.insert(next_central, next_obs, astate, cstate,
                      raw.cpu().numpy().reshape(lanes, 5, 3), logp.cpu().numpy().reshape(lanes, 5, 1),
                      values.cpu().numpy().reshape(lanes, 5, 1), rewards, masks)
    for lane, episode in enumerate(episodes):
        total = sum(rewards_by_lane[lane])
        emit(dict(phase="train", arm="M", episode=episode, steps=horizon,
                  reset_seed=100000 * MASTER + 1000 + episode, S=total, J=total / horizon,
                  terminated=True, truncated=False))
        counts["train_episodes"] += 1
        counts["completed_episode_steps"] += horizon


@torch.no_grad()
def evaluate(policy, env, episode, counts, emit, horizon=HORIZON):
    """Actor-only final evaluation; no critic/global input or ValueNorm update."""
    policy.actor.eval()
    policy.actor.act.generator = generator(100000 * EVALUATION_NAMESPACE + 5000 + episode)
    reset_seed = 100000 * EVALUATION_NAMESPACE + 2000 + episode
    obs, _ = env.reset(seed=reset_seed)
    counts["explicit_resets"] += 1
    last = np.zeros((5, 3), dtype=np.float32)
    hidden, masks = np.zeros((5, 1, 64), dtype=np.float32), np.zeros((5, 1), dtype=np.float32)
    rewards = []
    for step in range(horizon):
        own = actor_features(obs, last, np.zeros(5, dtype=np.int64))
        raw, hidden_tensor = policy.act(own, hidden, masks)
        sent = raw.tanh().cpu().numpy()
        hidden = hidden_tensor.cpu().numpy()
        masks.fill(1)
        counts["eval_actor_agent_forwards"] += 5
        counts["step_calls"] += 1
        counts["scientific_uav_calls"] += 1
        obs, _, terminated, truncated, info = env.step(sent)
        counts["team_steps"] += 1
        counts["eval_team_steps"] += 1
        rewards.append(team_reward(info))
        last = sent.copy()
        if truncated or bool(terminated) != (step + 1 == horizon):
            raise RuntimeError(f"unexpected final native boundary at {step + 1}/{horizon}")
    total = sum(rewards)
    emit(dict(phase="eval", arm="M", episode=episode, reset_seed=reset_seed, steps=horizon,
              S=total, J=total / horizon, terminated=True, truncated=False))
    counts["eval_episodes"] += 1
    counts["completed_episode_steps"] += horizon
