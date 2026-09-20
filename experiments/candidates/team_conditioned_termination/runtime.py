"""Frozen-foundation wiring for future team termination experiments.

This module is exercised by correctness tests. It is not a result-launch entry and
does not accept B08 checkpoints or assert their scientific acceptance. The eventual
runner must bind those identities and perform admission before using this machinery.
"""
from dataclasses import dataclass

import numpy as np
import torch

from .policy import RolloutBatch, compute_gae


@dataclass(frozen=True)
class Scenario1Features:
    """Fixed scaling of legal current inputs, identical for both mask policies.

    Scenario1's state is UAV xyz, user xy, normalized time. Every coordinate is
    divided by area_size, matching the observation's position convention. This
    includes no serving assignment, next state, reward, or foundation hidden state.
    """

    n_agents: int
    n_users: int
    obs_dim: int
    area_size: float = 1000.0
    n_team_labels: int = 6
    n_agent_labels: int = 6
    local_cap: int = 10
    team_cap: int = 10

    def __post_init__(self):
        if min(self.n_agents, self.n_users, self.obs_dim, self.n_team_labels,
               self.n_agent_labels, self.local_cap, self.team_cap) <= 0:
            raise ValueError('feature dimensions and caps must be positive')
        if not np.isfinite(self.area_size) or self.area_size <= 0:
            raise ValueError('area_size must be finite and positive')

    @property
    def state_dim(self):
        return 3 * self.n_agents + 2 * self.n_users + 1

    @property
    def context_dim(self):
        return (self.state_dim + self.n_agents * self.obs_dim + self.n_team_labels
                + self.n_agents * self.n_agent_labels + 3 * self.n_agents + 3)

    def encode(self, snapshot):
        states = np.array(snapshot['states'], dtype=np.float32, copy=True)
        obs = np.asarray(snapshot['observations'], dtype=np.float32)
        batch = states.shape[0]
        if states.shape != (batch, self.state_dim):
            raise ValueError('unexpected Scenario1 state layout')
        if obs.shape != (batch, self.n_agents, self.obs_dim):
            raise ValueError('unexpected Scenario1 observation layout')
        states[:, :-1] /= self.area_size
        reset = np.asarray(snapshot['reset'], dtype=bool)

        def one_hot(labels, size):
            labels = np.array(labels, dtype=np.int64, copy=True)
            live = np.broadcast_to(~reset.reshape((-1,) + (1,) * (labels.ndim - 1)), labels.shape)
            if np.any(live & ((labels < 0) | (labels >= size))):
                raise ValueError('invalid held label outside a reset')
            labels[~live] = 0
            return np.eye(size, dtype=np.float32)[labels] * live[..., None]

        team = one_hot(snapshot['held_team'], self.n_team_labels)
        agents = one_hot(snapshot['held_agents'], self.n_agent_labels)
        ages = np.array(snapshot['agent_ages'], dtype=np.float32, copy=True)
        team_ages = np.array(snapshot['team_ages'], dtype=np.float32, copy=True)
        ages[reset] = 0
        team_ages[reset] = 0
        features = np.concatenate([
            states, obs.reshape(batch, -1), team, agents.reshape(batch, -1),
            ages / self.local_cap, team_ages[:, None] / self.team_cap,
            np.asarray(snapshot['forced_end'], dtype=np.float32),
            np.asarray(snapshot['eligible'], dtype=np.float32),
            reset[:, None].astype(np.float32),
            np.asarray(snapshot['team_forced'], dtype=np.float32)[:, None],
        ], axis=1)
        if features.shape != (batch, self.context_dim) or not np.isfinite(features).all():
            raise ValueError('nonfinite or malformed termination context')
        return torch.from_numpy(features)


def foundation_modules(agent):
    """Parameter owners on the accepted D_K10 construction."""
    names = ('skill_coordinator', 'skill_discoverer', 'team_discriminator',
             'individual_discriminator')
    return {name: getattr(agent, name) for name in names if getattr(agent, name, None) is not None}


def freeze_foundation(agent):
    """Freeze weights/statistics, while step() still advances ordinary GRU state."""
    config = agent.config
    if (not agent.d2_enabled or agent.use_ha_ctse
            or not np.isposinf(agent.d2_cost_c) or not np.isposinf(agent.d2_cost_c_Z)
            or (config.k, agent.d2_k_max, agent.d2_k_Z) != (10, 10, 10)
            or (config.n_Z, config.n_z) != (6, 6)
            or agent.d2_age_feature != 'off'):
        raise ValueError('frozen termination adapter requires the D_K10 construction')
    if config.use_obsnorm or config.use_statenorm or getattr(config, 'coordinator_dropout', 0.0):
        raise ValueError('this adapter requires B08 normalization/dropout settings')
    if agent.device.type != 'cpu':
        raise ValueError('this implementation has been checked only on the CPU foundation')
    agent.train(False)
    for module in foundation_modules(agent).values():
        module.eval()
        for parameter in module.parameters():
            parameter.requires_grad_(False)


class FrozenGateController:
    """Own a private mask sampler and retain exactly the predecision training row."""

    def __init__(self, agent, policy, critic, features, *, seed):
        if (policy.context_dim != features.context_dim or policy.n_agents != features.n_agents
                or features.n_agents != agent.config.n_agents
                or features.obs_dim != agent.config.obs_dim
                or features.state_dim != agent.config.state_dim
                or (features.local_cap, features.team_cap) != (10, 10)
                or (features.n_team_labels, features.n_agent_labels) != (6, 6)):
            raise ValueError('policy, features and foundation disagree')
        if next(policy.parameters()).device.type != 'cpu' or next(critic.parameters()).device.type != 'cpu':
            raise ValueError('gate and critic must be on CPU')
        freeze_foundation(agent)
        self.agent, self.policy, self.critic, self.features = agent, policy, critic, features
        self.generator = torch.Generator(device='cpu').manual_seed(int(seed))
        self.last = None
        agent.set_optional_end_hook(self)

    @torch.no_grad()
    def __call__(self, snapshot, *, deterministic):
        context = self.features.encode(snapshot)
        eligible = torch.from_numpy(snapshot['eligible'].copy())
        forced_end = torch.from_numpy(snapshot['forced_end'].copy())
        decision = self.policy.sample(context, eligible, forced_end,
                                      generator=self.generator, deterministic=deterministic)
        self.last = {
            'context': context, 'eligible': eligible, 'forced_end': forced_end,
            'actions': decision.actions.clone(), 'old_log_prob': decision.log_prob.clone(),
            'values': self.critic(context).clone(),
        }
        return (decision.actions & eligible).cpu().numpy()

    def detach(self):
        if getattr(self.agent, '_optional_end_hook', None) is self:
            self.agent.set_optional_end_hook(None)


def collect_episode(envs, agent, controller, *, horizon, gamma=0.99,
                    gae_lambda=0.95, deterministic=False):
    """One complete finite Scenario1 episode per lane, without foundation updates.

    Kept deliberately narrow: no partial episodes, automatic reset within a batch,
    reward transformation, hidden bootstrap action, or evaluation-on-training lanes.
    The time limit ends the native finite objective, so its final value is zero.
    Call with a separate agent/environment/controller when evaluating a live learner.
    """
    if controller.agent is not agent or getattr(agent, '_optional_end_hook', None) is not controller:
        raise ValueError('collector requires its installed controller')
    if agent.training:
        raise ValueError('foundation must remain in evaluation mode during gate learning')
    if len(envs) != agent.config.num_envs or horizon <= 0:
        raise ValueError('collector lane count/horizon mismatch')
    for env in envs:
        raw = env.env
        if (raw.max_steps != horizon or raw.n_uavs != controller.features.n_agents
                or raw.n_users != controller.features.n_users
                or raw.area_size != controller.features.area_size):
            raise ValueError('collector environment differs from the feature/episode contract')

    states, observations = [], []
    for lane, env in enumerate(envs):
        obs, info = env.reset()
        agent.reset_env_state(lane)
        observations.append(np.asarray(obs, dtype=np.float32))
        states.append(np.asarray(info['state'], dtype=np.float64))
    states, observations = np.stack(states), np.stack(observations)
    lanes = len(envs)
    steps, dones = np.zeros(lanes, dtype=np.int64), np.zeros(lanes, dtype=bool)
    records, reward_rows, terminal_rows = [], [], []
    optional_ends = 0
    for tick in range(horizon):
        action, _, _ = agent.step(states, observations, steps, dones,
                                  deterministic=deterministic, return_step_data=True, build_infos=False)
        if not np.isfinite(action).all():
            raise ValueError('nonfinite foundation action')
        records.append(controller.last)
        optional_ends += int((controller.last['actions'] & controller.last['eligible']).sum())
        next_states, next_obs, rewards, terminal = [], [], [], []
        for lane, env in enumerate(envs):
            obs, reward, term, trunc, info = env.step(action[lane])
            next_states.append(np.asarray(info['next_state'], dtype=np.float64))
            next_obs.append(np.asarray(obs, dtype=np.float32))
            rewards.append(float(reward))
            terminal.append(bool(term or trunc))
        dones = np.asarray(terminal, dtype=bool)
        if (tick < horizon - 1 and dones.any()) or (tick == horizon - 1 and not dones.all()):
            raise ValueError('episode ended outside the declared finite horizon')
        reward_rows.append(torch.tensor(rewards, dtype=torch.float32))
        terminal_rows.append(torch.from_numpy(dones.copy()))
        states, observations = np.stack(next_states), np.stack(next_obs)
        if not np.isfinite(states).all() or not np.isfinite(observations).all():
            raise ValueError('nonfinite native successor')
        steps += 1

    stacked = {name: torch.stack([row[name] for row in records]) for name in records[0]}
    rewards, terminal = torch.stack(reward_rows), torch.stack(terminal_rows)
    if not torch.isfinite(rewards).all():
        raise ValueError('nonfinite native reward')
    values = stacked.pop('values')
    next_values = torch.cat((values[1:], torch.zeros_like(values[:1])), dim=0)
    advantages, returns = compute_gae(rewards, values, next_values, terminal,
                                     torch.zeros_like(terminal), gamma, gae_lambda)
    flat = {name: value.flatten(0, 1) for name, value in stacked.items()}
    batch = RolloutBatch(**flat, advantages=advantages.flatten(), returns=returns.flatten())
    counts = {
        'native_team_steps': lanes * horizon, 'episodes': lanes,
        'foundation_optimizer_steps': 0, 'foundation_buffer_writes': 0,
        'optional_decision_rows': int(stacked['eligible'].any(-1).sum()),
        'optional_end_bits': optional_ends,
        'finite_episode_returns': rewards.sum(0).tolist(),
        'deterministic': bool(deterministic),
    }
    return batch, counts
