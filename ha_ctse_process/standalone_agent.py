"""Standalone process-core trainer components.

This module is intentionally independent from ``hmasd``.  It implements the
new HA-CTSE/process-core path: compact interaction context, compact-conditioned
team code, skill-duration high-level decisions, segment process reward, and
PPO-style high/low updates without legacy discriminator objectives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

from ha_ctse_process.cooperation_credit import (
    aggregate_cooperation_credit,
    empty_cooperation_credit_metrics,
)
from ha_ctse_process.intrinsic_rewards import IntrinsicRewardComposer
from ha_ctse_process.outcome_residual import (
    FUTURE_COOPERATION_OUTCOME_FIELDS,
    FutureCooperationOutcomeExtractor,
    OutcomeResidualProbe,
)
from ha_ctse_process.process_outcomes import ProcessOutcomeExtractor
from ha_ctse_process.process_posterior import SegmentSkillPosterior, TransitionSkillDiscriminator
from ha_ctse_process.topology_role import (
    TOPOLOGY_ROLE_FIELDS,
    TOPOLOGY_ROLE_NAMES,
    TopologyRoleDiscriminator,
    TopologyRoleExtractor,
    empty_topology_role_metrics,
)
from ha_ctse_process.topology_potential import (
    TopologyPotentialShaper,
    empty_topology_potential_metrics,
)
from ha_ctse_process.recovery_potential import (
    RecoveryPotentialComputer,
    RecoveryPotentialConfig,
    aggregate_p2_metrics,
    compute_segment_shaping,
    empty_p2_metrics,
)
from ha_ctse_process.skill_effect_discovery import (
    SkillEffectDiscoveryModule,
    empty_skill_effect_metrics,
)
from ha_ctse_process.g_info_objective import (
    GInfoObjective,
    empty_g_info_metrics,
)
from hmasd.r_mappo_utils import ACTLayer, MLPBase, RNNLayer, check


def mlp(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.Tanh(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.Tanh(),
        nn.Linear(hidden_dim, output_dim),
    )


def sparsemax(logits: torch.Tensor, dim: int = -1) -> torch.Tensor:
    """Sparsemax projection for prototype aggregation."""

    shifted = logits - logits.max(dim=dim, keepdim=True).values
    zs = torch.sort(shifted, dim=dim, descending=True).values
    cssv = torch.cumsum(zs, dim=dim)
    rhos = torch.arange(1, shifted.shape[dim] + 1, device=logits.device, dtype=logits.dtype)
    view = [1] * shifted.dim()
    view[dim] = -1
    rhos = rhos.view(view)
    support = 1 + rhos * zs > cssv
    support_size = support.sum(dim=dim, keepdim=True).clamp_min(1)
    tau = (cssv.gather(dim, support_size.long() - 1) - 1) / support_size.to(logits.dtype)
    return torch.clamp(shifted - tau, min=0.0)


class InteractionCompactEncoder(nn.Module):
    """OPT-style compact interaction context c_tau for the standalone core."""

    def __init__(
        self,
        state_dim: int,
        obs_dim: int,
        n_agents: int,
        hidden_dim: int,
        compact_dim: int,
        num_prototypes: int,
        use_sparsemax: bool = True,
    ):
        super().__init__()
        self.state_dim = int(state_dim)
        self.obs_dim = int(obs_dim)
        self.n_agents = int(n_agents)
        self.compact_dim = int(compact_dim)
        self.num_prototypes = int(max(num_prototypes, 1))
        self.use_sparsemax = bool(use_sparsemax)

        self.state_proj = nn.Sequential(
            nn.LayerNorm(self.state_dim),
            nn.Linear(self.state_dim, compact_dim),
            nn.GELU(),
        )
        self.obs_proj = nn.Sequential(
            nn.LayerNorm(self.obs_dim),
            nn.Linear(self.obs_dim, compact_dim),
            nn.GELU(),
        )
        self.prototype_logits = nn.Linear(compact_dim, self.num_prototypes)
        self.prototypes = nn.Parameter(torch.randn(self.num_prototypes, compact_dim) * 0.02)
        self.output = nn.Sequential(
            nn.LayerNorm(compact_dim * 2),
            nn.Linear(compact_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, compact_dim),
        )

    def forward(self, state: torch.Tensor, joint_obs: torch.Tensor):
        batch_size, n_agents, obs_dim = joint_obs.shape
        state_token = self.state_proj(state.float()).unsqueeze(1)
        obs_tokens = self.obs_proj(joint_obs.float().reshape(-1, obs_dim)).reshape(
            batch_size,
            n_agents,
            self.compact_dim,
        )
        pooled = torch.cat([state_token, obs_tokens], dim=1).mean(dim=1)
        logits = self.prototype_logits(pooled)
        weights = sparsemax(logits, dim=-1) if self.use_sparsemax else F.softmax(logits, dim=-1)
        proto_mix = weights @ self.prototypes
        compact = self.output(torch.cat([pooled, proto_mix], dim=-1))

        normalized_proto = F.normalize(self.prototypes, dim=-1)
        similarity = normalized_proto @ normalized_proto.t()
        off_diag = similarity - torch.eye(self.num_prototypes, device=similarity.device)
        cd_loss = torch.square(off_diag).sum() / max(self.num_prototypes * (self.num_prototypes - 1), 1)
        avg_weights = weights.mean(dim=0).clamp_min(1e-8)
        uniform = torch.full_like(avg_weights, 1.0 / self.num_prototypes)
        cmi_loss = F.kl_div(avg_weights.log(), uniform, reduction="sum")
        aggregation_entropy = -(weights * weights.clamp_min(1e-8).log()).sum(dim=-1)
        return compact, cd_loss, cmi_loss, weights, aggregation_entropy


class CompactTeamBridge(nn.Module):
    """Maps compact interaction context to a controllable team code g_tau."""

    def __init__(self, compact_dim: int, team_code_dim: int, num_team_codes: int, bridge_type: str):
        super().__init__()
        self.compact_dim = int(compact_dim)
        self.team_code_dim = int(team_code_dim)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.bridge_type = str(bridge_type or "stochastic").lower()
        self.vector_bridge = nn.Sequential(
            nn.LayerNorm(self.compact_dim),
            nn.Linear(self.compact_dim, self.team_code_dim),
            nn.GELU(),
        )
        self.code_head = nn.Linear(self.team_code_dim, self.num_team_codes)
        self.code_embedding = nn.Embedding(self.num_team_codes, self.team_code_dim)

    def forward(
        self,
        compact: torch.Tensor,
        deterministic: bool = False,
        forced_team_code: torch.Tensor | None = None,
    ):
        batch_size = compact.shape[0]
        device = compact.device
        if self.bridge_type == "none":
            team_code = torch.zeros(batch_size, dtype=torch.long, device=device)
            team_vector = torch.zeros(batch_size, self.team_code_dim, device=device)
            zeros = torch.zeros(batch_size, device=device)
            logits = torch.zeros(batch_size, self.num_team_codes, device=device)
            return team_code, team_vector, zeros, zeros, logits

        base_vector = self.vector_bridge(compact)
        logits = torch.clamp(self.code_head(base_vector), -50.0, 50.0)
        if self.bridge_type == "stochastic":
            dist = Categorical(logits=logits)
            if forced_team_code is not None:
                team_code = forced_team_code.long().clamp(0, self.num_team_codes - 1)
            elif deterministic:
                team_code = torch.argmax(logits, dim=-1)
            else:
                team_code = dist.sample()
            return (
                team_code,
                self.code_embedding(team_code),
                dist.log_prob(team_code),
                dist.entropy(),
                logits,
            )

        team_code = torch.argmax(logits, dim=-1) if forced_team_code is None else forced_team_code.long()
        zeros = torch.zeros(batch_size, device=device)
        return team_code.clamp(0, self.num_team_codes - 1), base_vector, zeros, zeros, logits


class LowLevelPolicy(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        n_skills: int,
        action_dim: int,
        hidden_dim: int,
        action_space_type: str = "discrete",
        action_low=None,
        action_high=None,
    ):
        super().__init__()
        self.n_skills = int(n_skills)
        self.action_dim = int(action_dim)
        self.action_space_type = str(action_space_type)
        input_dim = int(obs_dim) + int(n_skills)
        self.actor = mlp(input_dim, hidden_dim, action_dim)
        self.critic = mlp(input_dim, hidden_dim, 1)
        if self.action_space_type == "continuous":
            self.log_std = nn.Parameter(torch.zeros(action_dim))
            low = torch.as_tensor(action_low if action_low is not None else -1.0, dtype=torch.float32)
            high = torch.as_tensor(action_high if action_high is not None else 1.0, dtype=torch.float32)
            self.register_buffer("action_low", low.reshape(1, -1))
            self.register_buffer("action_high", high.reshape(1, -1))

    def _features(self, obs: torch.Tensor, skills: torch.Tensor) -> torch.Tensor:
        skill_onehot = F.one_hot(skills.long(), num_classes=self.n_skills).float()
        return torch.cat([obs.float(), skill_onehot], dim=-1)

    def act(self, obs: torch.Tensor, skills: torch.Tensor, deterministic: bool = False):
        features = self._features(obs, skills)
        actor_out = self.actor(features)
        if self.action_space_type == "continuous":
            std = torch.exp(self.log_std).expand_as(actor_out)
            dist = torch.distributions.Normal(actor_out, std)
            raw_actions = actor_out if deterministic else dist.sample()
            actions = torch.max(torch.min(raw_actions, self.action_high), self.action_low)
            log_prob = dist.log_prob(actions).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1)
        else:
            dist = Categorical(logits=actor_out)
            actions = torch.argmax(actor_out, dim=-1) if deterministic else dist.sample()
            log_prob = dist.log_prob(actions)
            entropy = dist.entropy()
        return actions, log_prob, entropy, self.critic(features).squeeze(-1)

    def evaluate(self, obs: torch.Tensor, skills: torch.Tensor, actions: torch.Tensor):
        features = self._features(obs, skills)
        actor_out = self.actor(features)
        if self.action_space_type == "continuous":
            std = torch.exp(self.log_std).expand_as(actor_out)
            dist = torch.distributions.Normal(actor_out, std)
            log_prob = dist.log_prob(actions.float()).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1)
        else:
            dist = Categorical(logits=actor_out)
            log_prob = dist.log_prob(actions.long())
            entropy = dist.entropy()
        return log_prob, entropy, self.critic(features).squeeze(-1)


class ScalarRunningMeanStd:
    def __init__(self, eps: float = 1e-4):
        self.mean = 0.0
        self.var = 1.0
        self.count = float(eps)

    def update(self, values) -> None:
        arr = np.asarray(values, dtype=np.float64).reshape(-1)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return
        batch_mean = float(np.mean(arr))
        batch_var = float(np.var(arr))
        batch_count = float(arr.size)
        delta = batch_mean - self.mean
        total_count = self.count + batch_count
        new_mean = self.mean + delta * batch_count / total_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m_2 = m_a + m_b + delta * delta * self.count * batch_count / total_count
        self.mean = float(new_mean)
        self.var = float(max(m_2 / total_count, 1e-8))
        self.count = float(total_count)

    def normalize_np(self, values):
        return (np.asarray(values, dtype=np.float32) - float(self.mean)) / float(np.sqrt(self.var) + 1e-8)

    def denormalize_np(self, values):
        return np.asarray(values, dtype=np.float32) * float(np.sqrt(self.var) + 1e-8) + float(self.mean)

    def normalize_tensor(self, values: torch.Tensor) -> torch.Tensor:
        return (values - float(self.mean)) / float(np.sqrt(self.var) + 1e-8)

    def denormalize_tensor(self, values: torch.Tensor) -> torch.Tensor:
        return values * float(np.sqrt(self.var) + 1e-8) + float(self.mean)

    def state_dict(self) -> dict[str, float]:
        return {"mean": float(self.mean), "var": float(self.var), "count": float(self.count)}

    def load_state_dict(self, state: dict[str, float]) -> None:
        self.mean = float(state.get("mean", 0.0))
        self.var = float(max(state.get("var", 1.0), 1e-8))
        self.count = float(max(state.get("count", 1e-4), 1e-8))


class RecurrentLowLevelPolicy(nn.Module):
    """HMASD-style recurrent skill executor with centralized critic."""

    def __init__(
        self,
        obs_dim: int,
        state_dim: int,
        n_agents: int,
        n_skills: int,
        num_team_codes: int,
        action_dim: int,
        hidden_dim: int,
        action_space_type: str = "discrete",
        action_low=None,
        action_high=None,
    ):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.state_dim = int(state_dim)
        self.n_agents = int(n_agents)
        self.n_skills = int(n_skills)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.action_space_type = str(action_space_type)

        actor_input_dim = self.obs_dim + self.n_skills
        critic_input_dim = self.state_dim + self.n_skills + self.n_agents + self.num_team_codes
        self.actor_input = nn.Sequential(
            nn.LayerNorm(actor_input_dim),
            nn.Linear(actor_input_dim, hidden_dim),
            nn.GELU(),
        )
        self.actor_rnn = nn.GRUCell(hidden_dim, hidden_dim)
        self.actor_head = nn.Linear(hidden_dim, self.action_dim)

        self.critic_input = nn.Sequential(
            nn.LayerNorm(critic_input_dim),
            nn.Linear(critic_input_dim, hidden_dim),
            nn.GELU(),
        )
        self.critic_rnn = nn.GRUCell(hidden_dim, hidden_dim)
        self.value_head = nn.Linear(hidden_dim, 1)

        if self.action_space_type == "continuous":
            self.log_std = nn.Parameter(torch.zeros(action_dim))
            low = torch.as_tensor(action_low if action_low is not None else -1.0, dtype=torch.float32)
            high = torch.as_tensor(action_high if action_high is not None else 1.0, dtype=torch.float32)
            self.register_buffer("action_low", low.reshape(1, -1))
            self.register_buffer("action_high", high.reshape(1, -1))

    def actor_update_parameters(self):
        params = list(self.actor_input.parameters()) + list(self.actor_rnn.parameters()) + list(self.actor_head.parameters())
        if self.action_space_type == "continuous":
            params.append(self.log_std)
        return params

    def critic_update_parameters(self):
        return list(self.critic_input.parameters()) + list(self.critic_rnn.parameters()) + list(self.value_head.parameters())

    def _actor_features(self, obs: torch.Tensor, skills: torch.Tensor) -> torch.Tensor:
        skill_onehot = F.one_hot(skills.long(), num_classes=self.n_skills).float()
        return self.actor_input(torch.cat([obs.float(), skill_onehot], dim=-1))

    def _critic_features(
        self,
        states: torch.Tensor,
        skills: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
    ) -> torch.Tensor:
        skill_onehot = F.one_hot(skills.long(), num_classes=self.n_skills).float()
        team_onehot = F.one_hot(team_codes.long().clamp(0, self.num_team_codes - 1), num_classes=self.num_team_codes).float()
        agent_onehot = F.one_hot(agent_ids.long().clamp(0, self.n_agents - 1), num_classes=self.n_agents).float()
        return self.critic_input(torch.cat([states.float(), skill_onehot, team_onehot, agent_onehot], dim=-1))

    def _dist(self, actor_h: torch.Tensor):
        actor_out = self.actor_head(actor_h)
        if self.action_space_type == "continuous":
            std = torch.exp(self.log_std).expand_as(actor_out)
            return torch.distributions.Normal(actor_out, std), actor_out
        return Categorical(logits=actor_out), actor_out

    def act(
        self,
        obs: torch.Tensor,
        skills: torch.Tensor,
        actor_hxs: torch.Tensor,
        states: torch.Tensor,
        team_codes: torch.Tensor,
        critic_hxs: torch.Tensor,
        agent_ids: torch.Tensor,
        deterministic: bool = False,
    ):
        actor_input = self._actor_features(obs, skills)
        new_actor_hxs = self.actor_rnn(actor_input, actor_hxs.float())
        dist, actor_out = self._dist(new_actor_hxs)
        if self.action_space_type == "continuous":
            raw_actions = actor_out if deterministic else dist.sample()
            actions = torch.max(torch.min(raw_actions, self.action_high), self.action_low)
            log_prob = dist.log_prob(actions).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1)
        else:
            actions = torch.argmax(actor_out, dim=-1) if deterministic else dist.sample()
            log_prob = dist.log_prob(actions)
            entropy = dist.entropy()

        critic_input = self._critic_features(states, skills, team_codes, agent_ids)
        new_critic_hxs = self.critic_rnn(critic_input, critic_hxs.float())
        values = self.value_head(new_critic_hxs).squeeze(-1)
        return actions, log_prob, entropy, values, new_actor_hxs, new_critic_hxs

    def value(
        self,
        states: torch.Tensor,
        skills: torch.Tensor,
        team_codes: torch.Tensor,
        critic_hxs: torch.Tensor,
        agent_ids: torch.Tensor,
    ):
        masks = torch.ones(states.shape[0], 1, dtype=torch.float32, device=states.device)
        critic_input = self._critic_features(states, skills, team_codes, agent_ids)
        new_critic_hxs = self.critic_rnn(critic_input, critic_hxs.float()) * masks
        return self.value_head(new_critic_hxs).squeeze(-1)

    def evaluate_sequence(
        self,
        obs_seq: torch.Tensor,
        skills_seq: torch.Tensor,
        actions_seq: torch.Tensor,
        states_seq: torch.Tensor,
        team_codes_seq: torch.Tensor,
        agent_ids_seq: torch.Tensor,
        initial_actor_hxs: torch.Tensor,
        initial_critic_hxs: torch.Tensor,
        masks_seq: torch.Tensor,
        reset_masks_seq: torch.Tensor,
    ):
        time_steps, batch_size, n_agents = skills_seq.shape
        actor_h = initial_actor_hxs.reshape(batch_size * n_agents, self.hidden_dim).float()
        critic_h = initial_critic_hxs.reshape(batch_size * n_agents, self.hidden_dim).float()
        log_probs = []
        entropies = []
        values = []
        for t in range(time_steps):
            valid_mask = masks_seq[t].reshape(-1, 1).float()
            obs_t = obs_seq[t].reshape(batch_size * n_agents, self.obs_dim)
            skills_t = skills_seq[t].reshape(-1)
            actor_input = self._actor_features(obs_t, skills_t)
            actor_h = self.actor_rnn(actor_input, actor_h) * valid_mask
            dist, actor_out = self._dist(actor_h)
            if self.action_space_type == "continuous":
                actions_t = actions_seq[t].reshape(batch_size * n_agents, self.action_dim).float()
                log_prob = dist.log_prob(actions_t).sum(dim=-1)
                entropy = dist.entropy().sum(dim=-1)
            else:
                actions_t = actions_seq[t].reshape(-1).long()
                log_prob = dist.log_prob(actions_t)
                entropy = dist.entropy()

            states_t = states_seq[t].unsqueeze(1).expand(batch_size, n_agents, self.state_dim).reshape(
                batch_size * n_agents,
                self.state_dim,
            )
            team_codes_t = team_codes_seq[t].unsqueeze(1).expand(batch_size, n_agents).reshape(-1)
            agent_ids_t = agent_ids_seq[t].reshape(-1)
            critic_input = self._critic_features(states_t, skills_t, team_codes_t, agent_ids_t)
            critic_h = self.critic_rnn(critic_input, critic_h) * valid_mask
            value = self.value_head(critic_h).squeeze(-1)

            log_probs.append(log_prob.reshape(batch_size, n_agents))
            entropies.append(entropy.reshape(batch_size, n_agents))
            values.append(value.reshape(batch_size, n_agents))

            reset_mask = reset_masks_seq[t].reshape(-1, 1).float()
            actor_h = actor_h * reset_mask
            critic_h = critic_h * reset_mask

        return torch.stack(log_probs), torch.stack(entropies), torch.stack(values)


class Box:
    def __init__(self, shape):
        self.shape = tuple(shape)


class Discrete:
    def __init__(self, n: int):
        self.n = int(n)


class StrictHMASDMAPPOLowLevelPolicy(nn.Module):
    """Standalone replica of HMASD's MAPPO-style SkillDiscoverer.

    Actor: MLPBase(obs) -> skill FiLM -> RNNLayer -> ACTLayer.
    Critic: MLPBase(global state) -> team-code FiLM -> RNNLayer -> value head.
    """

    def __init__(
        self,
        obs_dim: int,
        state_dim: int,
        n_skills: int,
        num_team_codes: int,
        action_dim: int,
        hidden_dim: int,
        action_space_type: str = "discrete",
        continuous_action_distribution: str = "tanh_gaussian",
        continuous_logstd_init: float = -1.0,
        continuous_logstd_min: float = -5.0,
        continuous_logstd_max: float = 0.0,
        actor_condition_on_team_code: bool = False,
        device: torch.device | str = "cpu",
    ):
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.state_dim = int(state_dim)
        self.n_skills = int(n_skills)
        self.num_team_codes = int(max(num_team_codes, 1))
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.action_space_type = str(action_space_type)
        self.actor_condition_on_team_code = bool(actor_condition_on_team_code)
        self.device = torch.device(device)

        class Args:
            pass

        args = Args()
        args.hidden_size = self.hidden_dim
        args.gain = 0.01
        args.use_orthogonal = True
        args.use_policy_active_masks = True
        args.use_naive_recurrent_policy = False
        args.use_recurrent_policy = True
        args.recurrent_N = 1
        args.use_feature_normalization = False
        args.use_popart = False
        args.continuous_action_distribution = continuous_action_distribution
        args.continuous_logstd_init = continuous_logstd_init
        args.continuous_logstd_min = continuous_logstd_min
        args.continuous_logstd_max = continuous_logstd_max
        self.args = args

        obs_space = Box((self.obs_dim,))
        action_space = Discrete(self.action_dim) if self.action_space_type == "discrete" else Box((self.action_dim,))
        self.actor_base = MLPBase(args, obs_space.shape)
        self.actor_film = nn.Linear(self.n_skills, 2 * self.hidden_dim)
        self.actor_team_film = (
            nn.Linear(self.num_team_codes, 2 * self.hidden_dim)
            if self.actor_condition_on_team_code
            else None
        )
        self.actor_rnn = RNNLayer(self.hidden_dim, self.hidden_dim, args.recurrent_N, args.use_orthogonal)
        self.actor_act = ACTLayer(action_space, self.hidden_dim, args.use_orthogonal, args.gain, args)

        self.critic_base = MLPBase(args, (self.state_dim,))
        self.critic_film = nn.Linear(self.num_team_codes, 2 * self.hidden_dim)
        self.critic_rnn = RNNLayer(self.hidden_dim, self.hidden_dim, args.recurrent_N, args.use_orthogonal)
        init_method = nn.init.orthogonal_

        def init_value(module):
            nn.init.orthogonal_(module.weight.data, gain=1.0)
            nn.init.constant_(module.bias.data, 0.0)
            return module

        self.value_head = init_value(nn.Linear(self.hidden_dim, 1))
        self.to(self.device)

    def actor_update_parameters(self):
        params = (
            list(self.actor_base.parameters())
            + list(self.actor_film.parameters())
            + list(self.actor_rnn.parameters())
            + list(self.actor_act.parameters())
        )
        if self.actor_team_film is not None:
            params += list(self.actor_team_film.parameters())
        return params

    def critic_update_parameters(self):
        return (
            list(self.critic_base.parameters())
            + list(self.critic_film.parameters())
            + list(self.critic_rnn.parameters())
            + list(self.value_head.parameters())
        )

    def _actor_features(
        self,
        obs: torch.Tensor,
        skills: torch.Tensor,
        team_codes: torch.Tensor | None = None,
    ) -> torch.Tensor:
        features = self.actor_base(check(obs).to(dtype=torch.float32, device=self.device))
        skill_onehot = F.one_hot(skills.long(), num_classes=self.n_skills).float()
        film = self.actor_film(skill_onehot)
        gamma, beta = torch.chunk(film, 2, dim=-1)
        features = gamma * features + beta
        if self.actor_team_film is not None:
            if team_codes is None:
                team_codes = torch.zeros(features.shape[0], dtype=torch.long, device=self.device)
            team_onehot = F.one_hot(
                team_codes.long().clamp(0, self.num_team_codes - 1),
                num_classes=self.num_team_codes,
            ).float()
            team_film = self.actor_team_film(team_onehot)
            team_gamma, team_beta = torch.chunk(team_film, 2, dim=-1)
            features = team_gamma * features + team_beta
        return features

    def _critic_features(self, states: torch.Tensor, team_codes: torch.Tensor) -> torch.Tensor:
        features = self.critic_base(check(states).to(dtype=torch.float32, device=self.device))
        team_onehot = F.one_hot(
            team_codes.long().clamp(0, self.num_team_codes - 1),
            num_classes=self.num_team_codes,
        ).float()
        film = self.critic_film(team_onehot)
        gamma, beta = torch.chunk(film, 2, dim=-1)
        return gamma * features + beta

    @staticmethod
    def _squeeze_log_probs(log_probs: torch.Tensor) -> torch.Tensor:
        return log_probs.squeeze(-1) if log_probs.dim() > 1 and log_probs.shape[-1] == 1 else log_probs

    def act(
        self,
        obs: torch.Tensor,
        skills: torch.Tensor,
        actor_hxs: torch.Tensor,
        states: torch.Tensor,
        team_codes: torch.Tensor,
        critic_hxs: torch.Tensor,
        agent_ids: torch.Tensor | None = None,
        deterministic: bool = False,
    ):
        masks = torch.ones(obs.shape[0], 1, dtype=torch.float32, device=self.device)
        actor_features = self._actor_features(obs, skills, team_codes)
        actor_features, new_actor_hxs = self.actor_rnn(actor_features, actor_hxs.float(), masks)
        actions, log_probs = self.actor_act(actor_features, deterministic=deterministic)

        critic_features = self._critic_features(states, team_codes)
        critic_features, new_critic_hxs = self.critic_rnn(critic_features, critic_hxs.float(), masks)
        values = self.value_head(critic_features).squeeze(-1)

        if self.action_space_type == "discrete":
            actions = actions.squeeze(-1)
        return (
            actions,
            self._squeeze_log_probs(log_probs),
            torch.zeros_like(values),
            values,
            new_actor_hxs,
            new_critic_hxs,
        )

    def value(
        self,
        states: torch.Tensor,
        skills: torch.Tensor | None,
        team_codes: torch.Tensor,
        critic_hxs: torch.Tensor,
        agent_ids: torch.Tensor | None = None,
    ):
        masks = torch.ones(states.shape[0], 1, dtype=torch.float32, device=self.device)
        critic_features = self._critic_features(states, team_codes)
        critic_features, _ = self.critic_rnn(critic_features, critic_hxs.float(), masks)
        return self.value_head(critic_features).squeeze(-1)

    def evaluate_sequence(
        self,
        obs_seq: torch.Tensor,
        skills_seq: torch.Tensor,
        actions_seq: torch.Tensor,
        states_seq: torch.Tensor,
        team_codes_seq: torch.Tensor,
        agent_ids_seq: torch.Tensor,
        initial_actor_hxs: torch.Tensor,
        initial_critic_hxs: torch.Tensor,
        masks_seq: torch.Tensor,
        reset_masks_seq: torch.Tensor,
    ):
        time_steps, batch_size, n_agents = skills_seq.shape
        flat_batch = batch_size * n_agents
        obs_flat = obs_seq.reshape(time_steps, flat_batch, self.obs_dim)
        skills_flat = skills_seq.reshape(time_steps, flat_batch)
        if self.action_space_type == "continuous":
            actions_flat = actions_seq.reshape(time_steps, flat_batch, self.action_dim)
        else:
            actions_flat = actions_seq.reshape(time_steps, flat_batch, 1)
        states_flat = states_seq.unsqueeze(2).expand(time_steps, batch_size, n_agents, self.state_dim)
        states_flat = states_flat.reshape(time_steps, flat_batch, self.state_dim)
        team_flat = team_codes_seq.unsqueeze(-1).expand(time_steps, batch_size, n_agents).reshape(time_steps, flat_batch)
        valid_masks = masks_seq.reshape(time_steps, flat_batch, 1)
        rnn_masks = torch.ones_like(valid_masks)
        if time_steps > 1:
            rnn_masks[1:] = reset_masks_seq[:-1].reshape(time_steps - 1, flat_batch, 1)

        actor_features = self._actor_features(obs_flat, skills_flat, team_flat)
        actor_hxs = initial_actor_hxs.reshape(flat_batch, self.hidden_dim)
        actor_features, _ = self.actor_rnn(actor_features, actor_hxs, rnn_masks)
        log_probs, entropy = self.actor_act.evaluate_actions(
            actor_features.reshape(time_steps * flat_batch, self.hidden_dim),
            actions_flat.reshape(time_steps * flat_batch, -1),
            active_masks=valid_masks.reshape(time_steps * flat_batch, 1),
        )
        log_probs = self._squeeze_log_probs(log_probs).reshape(time_steps, batch_size, n_agents)
        entropy_matrix = torch.ones_like(log_probs) * entropy

        critic_features = self._critic_features(states_flat, team_flat)
        critic_hxs = initial_critic_hxs.reshape(flat_batch, self.hidden_dim)
        critic_features, _ = self.critic_rnn(critic_features, critic_hxs, rnn_masks)
        values = self.value_head(critic_features).squeeze(-1).reshape(time_steps, batch_size, n_agents)
        return log_probs, entropy_matrix, values


class SkillDurationPolicy(nn.Module):
    """High-level skill-duration policy conditioned on c_tau and g_tau."""

    def __init__(
        self,
        obs_dim: int,
        n_skills: int,
        n_durations: int,
        hidden_dim: int,
        compact_dim: int,
        team_code_dim: int,
    ):
        super().__init__()
        self.n_skills = int(n_skills)
        self.input = nn.Sequential(
            nn.LayerNorm(obs_dim + n_skills + 1 + compact_dim + team_code_dim),
            nn.Linear(obs_dim + n_skills + 1 + compact_dim + team_code_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
        )
        self.skill_head = nn.Linear(hidden_dim, n_skills)
        self.duration_head = nn.Linear(hidden_dim, n_durations)
        self.value_head = nn.Linear(hidden_dim, 1)

    def _features(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
    ) -> torch.Tensor:
        prev_onehot = F.one_hot(prev_skills.long().clamp(0, self.n_skills - 1), num_classes=self.n_skills).float()
        age_feature = torch.log1p(ages.float()).unsqueeze(-1) / 10.0
        return self.input(torch.cat([obs.float(), prev_onehot, age_feature, compact.float(), team_vector.float()], dim=-1))

    def logits(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = self._features(obs, prev_skills, ages, compact, team_vector)
        return self.skill_head(hidden), self.duration_head(hidden), self.value_head(hidden).squeeze(-1)

    def act(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        deterministic: bool = False,
    ):
        skill_logits, duration_logits, value = self.logits(obs, prev_skills, ages, compact, team_vector)
        skill_dist = Categorical(logits=skill_logits)
        duration_dist = Categorical(logits=duration_logits)
        if deterministic:
            skills = torch.argmax(skill_logits, dim=-1)
            durations = torch.argmax(duration_logits, dim=-1)
        else:
            skills = skill_dist.sample()
            durations = duration_dist.sample()
        logp = skill_dist.log_prob(skills) + duration_dist.log_prob(durations)
        entropy = skill_dist.entropy() + duration_dist.entropy()
        return skills, durations, logp, entropy, value

    def evaluate(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        skills: torch.Tensor,
        durations: torch.Tensor,
    ):
        skill_logits, duration_logits, value = self.logits(obs, prev_skills, ages, compact, team_vector)
        skill_dist = Categorical(logits=skill_logits)
        duration_dist = Categorical(logits=duration_logits)
        logp = skill_dist.log_prob(skills.long()) + duration_dist.log_prob(durations.long())
        entropy = skill_dist.entropy() + duration_dist.entropy()
        return logp, entropy, value


class ProcessEncoder(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        hidden_dim: int,
        embedding_dim: int,
        n_skills: int,
        outcome_dim: int,
    ):
        super().__init__()
        self.step_encoder = mlp(obs_dim + action_dim + 1, hidden_dim, embedding_dim)
        self.outcome_head = mlp(embedding_dim, hidden_dim, outcome_dim)
        self.skill_head = nn.Linear(embedding_dim, n_skills)

    def forward(self, obs_seq, action_seq, reward_seq, mask):
        action_feat = action_seq.float()
        if action_feat.dim() == 2:
            action_feat = action_feat.unsqueeze(-1)
        reward_feat = reward_seq.float().unsqueeze(-1)
        step_input = torch.cat([obs_seq.float(), action_feat, reward_feat], dim=-1)
        encoded = self.step_encoder(step_input)
        masked = encoded * mask.unsqueeze(-1).float()
        denom = mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        pooled = masked.sum(dim=1) / denom
        return pooled, self.outcome_head(pooled), self.skill_head(pooled)


@dataclass
class Segment:
    env_id: int
    agent_id: int
    skill: int
    duration_idx: int
    start_step: int
    high_obs: np.ndarray
    high_logp: float
    high_value: float
    high_entropy: float
    high_state: np.ndarray | None = None
    high_joint_obs: np.ndarray | None = None
    prev_skill: int = 0
    skill_age_prev: int = 0
    team_code: int = 0
    team_logp_weight: float = 1.0
    initial_assignment: bool = False
    switched: bool = False
    duration_target: int = 1
    renewal_penalty: float = 0.0
    obs: list[np.ndarray] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)
    rewards: list[float] = field(default_factory=list)
    rollout_indices: list[int] = field(default_factory=list)
    reward_info_seq: list[dict] = field(default_factory=list)
    state_info_seq: list[dict[str, Any]] = field(default_factory=list)
    # True segment-start state (BEFORE the first action), captured separately from
    # state_info_seq (which only holds post-step states).  Used by P2 recovery
    # shaping so s0 is the real window start, not the post-first-step state.
    start_state_info: dict[str, Any] | None = None
    start_reward_info: dict[str, Any] | None = None
    end_obs: np.ndarray | None = None
    end_joint_obs: np.ndarray | None = None
    end_state: np.ndarray | None = None
    terminal: bool = False

    def append(
        self,
        obs,
        action,
        reward,
        next_obs,
        rollout_idx: int,
        reward_info=None,
        state_info=None,
        next_joint_obs=None,
        next_state=None,
        done: bool = False,
        pre_state_info=None,
        pre_reward_info=None,
    ):
        # On the segment's first step, record the pre-step (segment-start) state so
        # P2 shaping telescopes over the true window, not the post-first-step state.
        if not self.state_info_seq and self.start_state_info is None and pre_state_info:
            self.start_state_info = dict(pre_state_info)
            self.start_reward_info = dict(pre_reward_info or {})
        self.obs.append(np.asarray(obs, dtype=np.float32))
        action_arr = np.asarray(action, dtype=np.float32)
        self.actions.append(action_arr.reshape(-1))
        self.rewards.append(float(reward))
        self.rollout_indices.append(int(rollout_idx))
        self.reward_info_seq.append(dict(reward_info or {}))
        self.state_info_seq.append(dict(state_info or {}))
        self.end_obs = np.asarray(next_obs, dtype=np.float32)
        self.end_joint_obs = None if next_joint_obs is None else np.asarray(next_joint_obs, dtype=np.float32)
        self.end_state = None if next_state is None else np.asarray(next_state, dtype=np.float32)
        self.terminal = bool(done)

    @property
    def length(self) -> int:
        return len(self.rewards)


class SegmentManager:
    def __init__(self, n_envs: int, n_agents: int):
        self.n_envs = int(n_envs)
        self.n_agents = int(n_agents)
        self.active: list[list[Segment | None]] = [
            [None for _ in range(n_agents)]
            for _ in range(n_envs)
        ]
        self.completed: list[Segment] = []

    def renew(
        self,
        env_id: int,
        agent_id: int,
        skill: int,
        duration_idx: int,
        step: int,
        high_obs,
        high_logp: float,
        high_value: float,
        high_entropy: float,
        high_state=None,
        high_joint_obs=None,
        prev_skill: int = 0,
        skill_age_prev: int = 0,
        team_code: int = 0,
        team_logp_weight: float = 1.0,
        initial_assignment: bool = False,
        switched: bool = False,
        duration_target: int = 1,
        renewal_penalty: float = 0.0,
    ):
        old = self.active[env_id][agent_id]
        if old is not None and old.length > 0:
            self.completed.append(old)
        self.active[env_id][agent_id] = Segment(
            env_id=int(env_id),
            agent_id=int(agent_id),
            skill=int(skill),
            duration_idx=int(duration_idx),
            start_step=int(step),
            high_obs=np.asarray(high_obs, dtype=np.float32),
            high_logp=float(high_logp),
            high_value=float(high_value),
            high_entropy=float(high_entropy),
            high_state=None if high_state is None else np.asarray(high_state, dtype=np.float32),
            high_joint_obs=None if high_joint_obs is None else np.asarray(high_joint_obs, dtype=np.float32),
            prev_skill=int(prev_skill),
            skill_age_prev=int(skill_age_prev),
            team_code=int(team_code),
            team_logp_weight=float(team_logp_weight),
            initial_assignment=bool(initial_assignment),
            switched=bool(switched),
            duration_target=int(duration_target),
            renewal_penalty=float(renewal_penalty),
        )

    def append(
        self,
        env_id: int,
        obs,
        actions,
        rewards,
        next_obs,
        rollout_idx: int,
        reward_info=None,
        state_info=None,
        next_state=None,
        done: bool = False,
        pre_state_info=None,
        pre_reward_info=None,
    ):
        for agent_id, segment in enumerate(self.active[env_id]):
            if segment is None:
                continue
            segment.append(
                obs[agent_id],
                actions[agent_id],
                rewards[agent_id],
                next_obs[agent_id],
                rollout_idx,
                reward_info=reward_info,
                state_info=state_info,
                next_joint_obs=next_obs,
                next_state=next_state,
                done=done,
                pre_state_info=pre_state_info,
                pre_reward_info=pre_reward_info,
            )

    def flush(self, env_id: int | None = None):
        env_ids = range(self.n_envs) if env_id is None else [int(env_id)]
        for current_env in env_ids:
            for agent_id, segment in enumerate(self.active[current_env]):
                if segment is not None and segment.length > 0:
                    self.completed.append(segment)
                self.active[current_env][agent_id] = None

    def pop_completed(self) -> list[Segment]:
        segments = self.completed
        self.completed = []
        return segments


@dataclass
class Rollout:
    env_ids: list[int] = field(default_factory=list)
    obs: list[np.ndarray] = field(default_factory=list)
    states: list[np.ndarray] = field(default_factory=list)
    skills: list[np.ndarray] = field(default_factory=list)
    team_codes: list[int] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)
    logp: list[np.ndarray] = field(default_factory=list)
    values: list[np.ndarray] = field(default_factory=list)
    low_actor_hxs: list[np.ndarray] = field(default_factory=list)
    low_critic_hxs: list[np.ndarray] = field(default_factory=list)
    rewards: list[np.ndarray] = field(default_factory=list)
    dones: list[bool] = field(default_factory=list)
    bootstrap_values: dict[int, np.ndarray] = field(default_factory=dict)


class StandaloneProcessAgent:
    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        n_agents: int,
        config: Any,
        device: str = "cpu",
        action_space_type: str = "discrete",
        action_low=None,
        action_high=None,
        num_envs: int = 1,
        state_dim: int | None = None,
    ):
        self.device = torch.device(device)
        self.num_envs = int(num_envs)
        self.n_agents = int(n_agents)
        self.obs_dim = int(obs_dim)
        self.state_dim = int(state_dim or getattr(config, "state_dim", 0) or (self.obs_dim * self.n_agents))
        self.n_skills = int(getattr(config, "n_z", 3))
        self.duration_candidates = tuple(getattr(config, "skill_lifetime_candidates", (3, 7, 13, 24)))
        if not self.duration_candidates:
            self.duration_candidates = (1,)
        hidden = int(getattr(config, "hidden_size", 128))
        self.gamma = float(getattr(config, "gamma", 0.99))
        self.high_clip = float(getattr(config, "clip_epsilon", 0.2))
        self.low_clip = float(getattr(config, "low_clip_epsilon", self.high_clip))
        self.process_reward_coef = float(getattr(config, "process_reward_coef", 0.05))
        self.process_reward_clip = float(getattr(config, "process_reward_clip", 2.0))
        self.process_contrast_coef = float(getattr(config, "process_contrast_coef", 1.0))
        self.process_outcome_coef = float(getattr(config, "process_outcome_coef", 0.25))
        self.process_reward_mode = str(getattr(config, "process_reward_mode", "mi_outcome")).lower()
        valid_reward_modes = {
            "mi_outcome",
            "mi_only",
            "positive_mi",
            "centered_mi",
            "residual_mi",
            "positive_residual_mi",
            "centered_residual_mi",
            "residual_mi_outcome",
            "none",
        }
        if self.process_reward_mode not in valid_reward_modes:
            raise ValueError(
                f"Unsupported process_reward_mode={self.process_reward_mode!r}; "
                f"expected one of {sorted(valid_reward_modes)}"
            )
        self.process_reward_injection = str(getattr(config, "process_reward_injection", "none")).lower()
        valid_injection_modes = {"high_only", "high_and_low", "low_only", "none"}
        if self.process_reward_injection not in valid_injection_modes:
            raise ValueError(
                f"Unsupported process_reward_injection={self.process_reward_injection!r}; "
                f"expected one of {sorted(valid_injection_modes)}"
            )
        self.process_reward_contrast_coef = float(getattr(config, "process_reward_contrast_coef", 1.0))
        self.process_reward_outcome_coef = float(getattr(config, "process_reward_outcome_coef", 0.25))
        self.use_process_reward = bool(getattr(config, "use_process_reward_for_discoverer", True))
        self.use_process_posterior_mi = bool(getattr(config, "use_process_posterior_mi", True))
        self.use_residual_process_posterior = bool(getattr(config, "use_residual_process_posterior", True))
        self.process_shortcut_coef = float(getattr(config, "process_shortcut_coef", 0.5))
        self.use_context_skill_shortcut = bool(getattr(config, "use_context_skill_shortcut", True))
        self.context_shortcut_coef = float(getattr(config, "context_shortcut_coef", 0.5))
        self.transition_context_shortcut_coef = float(getattr(config, "transition_context_shortcut_coef", 0.25))
        self.intrinsic_phase_bins = int(max(getattr(config, "intrinsic_phase_bins", 8), 1))
        self.intrinsic_phase_reference_steps = int(
            max(
                getattr(config, "episode_length", getattr(config, "max_steps", 500)),
                1,
            )
        )
        self.process_shortcut_margin = float(getattr(config, "process_shortcut_margin", 0.0))
        self.process_shortcut_margin_coef = float(getattr(config, "process_shortcut_margin_coef", 0.0))
        self.process_reward_warmup_steps = int(getattr(config, "process_reward_warmup_steps", 0))
        self.semantic_shortcut_hard_stop_enabled = bool(
            getattr(config, "semantic_shortcut_hard_stop_enabled", True)
        )
        self.semantic_shortcut_hard_stop_margin = float(
            getattr(config, "semantic_shortcut_hard_stop_margin", 0.0)
        )
        self.semantic_shortcut_hard_stop_min_segments = int(
            max(getattr(config, "semantic_shortcut_hard_stop_min_segments", 64), 1)
        )
        self.semantic_shortcut_hard_stop_raise = bool(
            getattr(config, "semantic_shortcut_hard_stop_raise", False)
        )
        self.use_g_intervention_kl_diagnostic = bool(
            getattr(config, "use_g_intervention_kl_diagnostic", True)
        )
        self.g_intervention_kl_max_segments = int(
            max(getattr(config, "g_intervention_kl_max_segments", 256), 1)
        )
        self.use_g_info_diagnostic = bool(getattr(config, "use_g_info_diagnostic", True))
        self.enable_g_info_objective = bool(getattr(config, "enable_g_info_objective", False))
        self.use_transition_skill_discriminator = bool(
            getattr(config, "use_transition_skill_discriminator", True)
        )
        self.transition_skill_condition_on_team = bool(
            getattr(config, "transition_skill_condition_on_team", True)
        )
        self.transition_skill_coef = float(getattr(config, "transition_skill_coef", 0.5))
        self.transition_skill_prior_coef = float(getattr(config, "transition_skill_prior_coef", 0.25))
        self.transition_skill_reward_coef = float(getattr(config, "transition_skill_reward_coef", 0.02))
        self.transition_skill_reward_warmup_steps = int(
            getattr(config, "transition_skill_reward_warmup_steps", 0)
        )
        self.transition_skill_reward_clip = float(getattr(config, "transition_skill_reward_clip", 0.05))
        self.transition_skill_max_samples = int(max(getattr(config, "transition_skill_max_samples", 8192), 1))
        self.process_prior_coef = float(getattr(config, "process_prior_coef", 0.25))
        self.process_posterior_condition_on_team = bool(
            getattr(config, "process_posterior_condition_on_team", True)
        )
        self.high_entropy_coef = float(getattr(config, "high_entropy_coef", 0.01))
        self.low_entropy_coef = float(getattr(config, "low_entropy_coef", 0.01))
        self.use_smdp_discounted_high_return = bool(getattr(config, "use_smdp_discounted_high_return", True))
        self.use_smdp_bootstrap = bool(getattr(config, "use_smdp_bootstrap", True))
        self.smdp_bootstrap_coef = float(getattr(config, "smdp_bootstrap_coef", 1.0))
        self.use_high_value_norm = bool(getattr(config, "use_high_value_norm", True))
        self.high_max_grad_norm = float(getattr(config, "high_max_grad_norm", 0.0))
        self.low_level_architecture = str(getattr(config, "low_level_architecture", "strict_hmasd_mappo")).lower()
        requested_recurrent_low = bool(getattr(config, "use_recurrent_low_level", True))
        if self.low_level_architecture == "feedforward" or not requested_recurrent_low:
            self.use_recurrent_low_level = False
            self.low_level_architecture = "feedforward"
        elif self.low_level_architecture in {"strict_hmasd_mappo", "gru_ctde"}:
            self.use_recurrent_low_level = True
        else:
            raise ValueError(
                f"Unsupported low_level_architecture={self.low_level_architecture!r}; "
                "expected strict_hmasd_mappo, gru_ctde, or feedforward"
            )
        self.low_rnn_hidden_size = int(getattr(config, "low_rnn_hidden_size", hidden))
        self.low_sequence_length = int(max(getattr(config, "low_sequence_length", 16), 1))
        self.low_sequence_batch_size = int(max(getattr(config, "low_sequence_batch_size", 16), 1))
        self.low_ppo_epochs = int(max(getattr(config, "low_ppo_epochs", getattr(config, "ppo_epochs", 4)), 1))
        self.low_actor_condition_on_team_code = bool(getattr(config, "low_actor_condition_on_team_code", False))
        self.use_low_value_norm = bool(getattr(config, "use_low_value_norm", True))
        self.low_gae_lambda = float(getattr(config, "low_gae_lambda", getattr(config, "gae_lambda", 0.95)))
        self.low_value_loss_coef = float(getattr(config, "low_value_loss_coef", getattr(config, "value_loss_coef", 1.0)))
        self.low_value_clip = float(getattr(config, "low_value_clip", getattr(config, "value_clip", 0.0)))
        self.low_max_grad_norm = float(getattr(config, "low_max_grad_norm", getattr(config, "max_grad_norm", 0.5)))
        self.edit_penalty_alpha = float(getattr(config, "edit_penalty_alpha", 0.0))
        self.switch_penalty_beta = float(getattr(config, "switch_penalty_beta", 0.0))
        self.opt_cd_coef = float(getattr(config, "opt_cd_coef", 0.0))
        self.opt_cmi_coef = float(getattr(config, "opt_cmi_coef", 0.0))
        self.outcome_extractor = ProcessOutcomeExtractor(
            normalize=bool(getattr(config, "normalize_process_outcomes", True))
        )
        self.use_outcome_residual_probe = bool(getattr(config, "use_outcome_residual_probe", True))
        self.outcome_residual_coef = float(getattr(config, "outcome_residual_coef", 1.0))
        self.outcome_residual_reward_coef = float(getattr(config, "outcome_residual_reward_coef", 0.0))
        self.outcome_residual_reward_clip = float(getattr(config, "outcome_residual_reward_clip", 0.05))
        self.outcome_residual_injection = str(getattr(config, "outcome_residual_injection", "none")).lower()
        if self.outcome_residual_injection not in valid_injection_modes:
            raise ValueError(
                f"Unsupported outcome_residual_injection={self.outcome_residual_injection!r}; "
                f"expected one of {sorted(valid_injection_modes)}"
            )
        self.outcome_residual_extractor = (
            FutureCooperationOutcomeExtractor(
                horizon_steps=int(getattr(config, "outcome_residual_horizon", 50)),
                normalize=bool(getattr(config, "normalize_outcome_residual_targets", True)),
            )
            if self.use_outcome_residual_probe
            else None
        )
        self.use_topology_role_probe = bool(getattr(config, "use_topology_role_probe", True))
        self.topology_role_coef = float(getattr(config, "topology_role_coef", 1.0))
        self.topology_role_reward_coef = float(getattr(config, "topology_role_reward_coef", 0.0))
        self.topology_role_reward_clip = float(getattr(config, "topology_role_reward_clip", 0.05))
        self.topology_role_injection = str(getattr(config, "topology_role_injection", "none")).lower()
        if self.topology_role_injection not in valid_injection_modes:
            raise ValueError(
                f"Unsupported topology_role_injection={self.topology_role_injection!r}; "
                f"expected one of {sorted(valid_injection_modes)}"
            )
        self.topology_role_extractor = (
            TopologyRoleExtractor(
                self.n_agents,
                min_score=float(getattr(config, "topology_role_min_score", 1e-6)),
            )
            if self.use_topology_role_probe
            else None
        )
        self.topology_potential_injection = str(
            getattr(config, "topology_potential_injection", "none")
        ).lower()
        if self.topology_potential_injection not in valid_injection_modes:
            raise ValueError(
                f"Unsupported topology_potential_injection={self.topology_potential_injection!r}; "
                f"expected one of {sorted(valid_injection_modes)}"
            )
        self.topology_potential_shaper = TopologyPotentialShaper(
            config,
            n_agents=self.n_agents,
            gamma=self.gamma,
        )
        self.intrinsic_rewards = IntrinsicRewardComposer(config)

        # P2-lite recovery-window contribution credit (default OFF).
        self.p2_compute_on = bool(getattr(config, "p2_recovery_credit_compute_on", False))
        self.p2_reward_on = bool(getattr(config, "p2_recovery_credit_reward_on", False))
        self.p2_reward_level = str(getattr(config, "p2_recovery_reward_level", "high_team"))
        self.p2_reward_coef = float(getattr(config, "p2_recovery_reward_coef", 0.05))
        self.p2_reward_clip = float(getattr(config, "p2_recovery_reward_clip", 0.5))
        self.p2_low_positive_only = bool(getattr(config, "p2_low_positive_only", True))
        self.p2_near_disconnect_bh_frac = float(getattr(config, "p2_near_disconnect_bh_frac", 0.4))
        self.p2_cfg = RecoveryPotentialConfig.from_config(config)
        self.p2_computer = RecoveryPotentialComputer(self.n_agents, self.p2_cfg)

        self.action_space_type = str(action_space_type)
        self.action_dim = int(action_dim)
        compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 64) or 64))
        team_code_dim = int(getattr(config, "team_code_dim", compact_dim))
        num_team_codes = int(getattr(config, "num_team_codes", getattr(config, "n_Z", 1) or 1))
        self.num_team_codes = int(max(num_team_codes, 1))
        bridge_type = str(getattr(config, "team_bridge_type", "stochastic"))
        process_embedding_dim = int(getattr(config, "process_encoder_embedding_dim", 64))

        self.compact = InteractionCompactEncoder(
            self.state_dim,
            self.obs_dim,
            self.n_agents,
            hidden,
            compact_dim,
            int(getattr(config, "opt_num_prototypes", 4)),
            use_sparsemax=bool(getattr(config, "opt_use_sparsemax", True)),
        ).to(self.device)
        self.bridge = CompactTeamBridge(compact_dim, team_code_dim, num_team_codes, bridge_type).to(self.device)
        self.high = SkillDurationPolicy(
            self.obs_dim,
            self.n_skills,
            len(self.duration_candidates),
            hidden,
            compact_dim,
            team_code_dim,
        ).to(self.device)
        if self.use_recurrent_low_level and self.low_level_architecture == "strict_hmasd_mappo":
            self.low = StrictHMASDMAPPOLowLevelPolicy(
                self.obs_dim,
                self.state_dim,
                self.n_skills,
                num_team_codes,
                action_dim,
                self.low_rnn_hidden_size,
                action_space_type=self.action_space_type,
                continuous_action_distribution=str(getattr(config, "continuous_action_distribution", "tanh_gaussian")),
                continuous_logstd_init=float(getattr(config, "continuous_logstd_init", -1.0)),
                continuous_logstd_min=float(getattr(config, "continuous_logstd_min", -5.0)),
                continuous_logstd_max=float(getattr(config, "continuous_logstd_max", 0.0)),
                actor_condition_on_team_code=self.low_actor_condition_on_team_code,
                device=self.device,
            ).to(self.device)
        elif self.use_recurrent_low_level:
            self.low = RecurrentLowLevelPolicy(
                self.obs_dim,
                self.state_dim,
                self.n_agents,
                self.n_skills,
                num_team_codes,
                action_dim,
                self.low_rnn_hidden_size,
                action_space_type=self.action_space_type,
                action_low=action_low,
                action_high=action_high,
            ).to(self.device)
        else:
            self.low = LowLevelPolicy(
                self.obs_dim,
                self.n_skills,
                action_dim,
                hidden,
                action_space_type=self.action_space_type,
                action_low=action_low,
                action_high=action_high,
            ).to(self.device)
        self.process = ProcessEncoder(
            self.obs_dim,
            1 if self.action_space_type == "discrete" else self.action_dim,
            hidden,
            process_embedding_dim,
            self.n_skills,
            self.outcome_extractor.num_outcomes,
        ).to(self.device)
        outcome_residual_hidden = int(getattr(config, "outcome_residual_hidden_dim", 0) or hidden)
        self.outcome_residual_probe = (
            OutcomeResidualProbe(
                process_embedding_dim,
                self.obs_dim,
                self.n_skills,
                num_team_codes,
                self.n_agents,
                self.intrinsic_phase_bins,
                len(self.duration_candidates),
                self.outcome_residual_extractor.num_outcomes,
                outcome_residual_hidden,
            ).to(self.device)
            if self.outcome_residual_extractor is not None
            else None
        )
        topology_role_hidden = int(getattr(config, "topology_role_hidden_dim", 0) or hidden)
        self.topology_role_probe = (
            TopologyRoleDiscriminator(
                self.topology_role_extractor.num_features,
                process_embedding_dim,
                compact_dim,
                self.obs_dim,
                self.n_skills,
                num_team_codes,
                self.n_agents,
                self.intrinsic_phase_bins,
                len(self.duration_candidates),
                topology_role_hidden,
                num_roles=self.topology_role_extractor.num_roles,
            ).to(self.device)
            if self.topology_role_extractor is not None
            else None
        )
        self.process_posterior = SegmentSkillPosterior(
            process_embedding_dim,
            self.n_skills,
            num_team_codes,
            hidden,
            team_embed_dim=int(getattr(config, "process_posterior_team_embed_dim", 0) or min(hidden, max(8, num_team_codes * 4))),
            condition_on_team=self.process_posterior_condition_on_team,
            num_duration_bins=len(self.duration_candidates),
            obs_dim=self.obs_dim,
            num_agents=self.n_agents,
            num_phase_bins=self.intrinsic_phase_bins,
            use_context_shortcut=self.use_context_skill_shortcut,
        ).to(self.device)
        transition_action_dim = 1 if self.action_space_type == "discrete" else self.action_dim
        self.transition_discriminator = (
            TransitionSkillDiscriminator(
                self.obs_dim,
                transition_action_dim,
                self.n_skills,
                num_team_codes,
                hidden,
                team_embed_dim=int(
                    getattr(config, "process_posterior_team_embed_dim", 0)
                    or min(hidden, max(8, num_team_codes * 4))
                ),
                condition_on_team=self.transition_skill_condition_on_team,
                num_agents=self.n_agents,
                num_phase_bins=self.intrinsic_phase_bins,
                use_context_shortcut=self.use_context_skill_shortcut,
            ).to(self.device)
            if self.use_transition_skill_discriminator
            else None
        )
        self.g_info_objective = (
            GInfoObjective(config)
            if (self.use_g_info_diagnostic or self.enable_g_info_objective)
            else None
        )
        self.skill_effect_discovery = (
            SkillEffectDiscoveryModule(
                config=config,
                obs_dim=self.obs_dim,
                n_skills=self.n_skills,
                n_agents=self.n_agents,
                num_team_codes=num_team_codes,
                num_duration_bins=len(self.duration_candidates),
                device=self.device,
                action_feature_dim=1 if self.action_space_type == "discrete" else self.action_dim,
            )
            if (
                bool(getattr(config, "skill_effect_discovery_on", False))
                or bool(getattr(config, "skill_effect_reward_on", False))
                or bool(getattr(config, "skill_force_probe_on", False))
                or bool(getattr(config, "enable_skill_forcing_probe", False))
                or bool(getattr(config, "enable_skill_forcing_reward", False))
                or bool(getattr(config, "skill_forcing_reward_on", False))
            )
            else None
        )

        lr = float(getattr(config, "lr_discoverer_actor", 3e-4))
        high_lr = float(getattr(config, "lr_coordinator", lr))
        process_lr = float(getattr(config, "lr_process_encoder", 1e-4))
        low_critic_lr = float(getattr(config, "lr_discoverer_critic", lr))
        if self.use_recurrent_low_level:
            self.low_opt = None
            self.low_actor_opt = torch.optim.Adam(self.low.actor_update_parameters(), lr=lr)
            self.low_critic_opt = torch.optim.Adam(self.low.critic_update_parameters(), lr=low_critic_lr)
            self.low_value_norm = ScalarRunningMeanStd() if self.use_low_value_norm else None
        else:
            self.low_opt = torch.optim.Adam(self.low.parameters(), lr=lr)
            self.low_actor_opt = None
            self.low_critic_opt = None
            self.low_value_norm = None
        self.high_value_norm = ScalarRunningMeanStd() if self.use_high_value_norm else None
        self.high_opt = torch.optim.Adam(
            list(self.compact.parameters()) + list(self.bridge.parameters()) + list(self.high.parameters()),
            lr=high_lr,
        )
        self.process_opt = torch.optim.Adam(
            list(self.process.parameters())
            + list(self.process_posterior.parameters())
            + (list(self.outcome_residual_probe.parameters()) if self.outcome_residual_probe is not None else [])
            + (list(self.topology_role_probe.parameters()) if self.topology_role_probe is not None else [])
            + (list(self.transition_discriminator.parameters()) if self.transition_discriminator is not None else []),
            lr=process_lr,
        )

        self.active_skills = np.zeros((self.num_envs, self.n_agents), dtype=np.int64)
        self.duration_remaining = np.zeros((self.num_envs, self.n_agents), dtype=np.int64)
        self.skill_age = np.zeros((self.num_envs, self.n_agents), dtype=np.int64)
        self.has_active_skill = np.zeros((self.num_envs, self.n_agents), dtype=np.bool_)
        self.active_team_codes = np.zeros(self.num_envs, dtype=np.int64)
        self.low_actor_hxs = np.zeros(
            (self.num_envs, self.n_agents, self.low_rnn_hidden_size),
            dtype=np.float32,
        )
        self.low_critic_hxs = np.zeros_like(self.low_actor_hxs, dtype=np.float32)
        self._last_low_context: list[dict[str, np.ndarray | int] | None] = [None for _ in range(self.num_envs)]
        self.segments = SegmentManager(self.num_envs, self.n_agents)

    @staticmethod
    def _count_parameters(module: nn.Module | None) -> int:
        if module is None:
            return 0
        return int(sum(param.numel() for param in module.parameters()))

    def parameter_counts(self) -> dict[str, int]:
        counts = {
            "compact": self._count_parameters(self.compact),
            "bridge": self._count_parameters(self.bridge),
            "high": self._count_parameters(self.high),
            "low": self._count_parameters(self.low),
            "process": self._count_parameters(self.process),
            "process_posterior": self._count_parameters(self.process_posterior),
            "outcome_residual_probe": self._count_parameters(self.outcome_residual_probe),
            "topology_role_probe": self._count_parameters(self.topology_role_probe),
            "transition_discriminator": self._count_parameters(self.transition_discriminator),
            "skill_effect_discovery": self._count_parameters(self.skill_effect_discovery),
        }
        if self.use_recurrent_low_level and hasattr(self.low, "actor_update_parameters"):
            counts["low_actor"] = int(sum(param.numel() for param in self.low.actor_update_parameters()))
            counts["low_critic"] = int(sum(param.numel() for param in self.low.critic_update_parameters()))
        else:
            counts["low_actor"] = counts["low"]
            counts["low_critic"] = 0
        counts["high_stack"] = counts["compact"] + counts["bridge"] + counts["high"]
        counts["process_stack"] = (
            counts["process"]
            + counts["process_posterior"]
            + counts["outcome_residual_probe"]
            + counts["topology_role_probe"]
            + counts["transition_discriminator"]
            + counts["skill_effect_discovery"]
        )
        counts["total_trainable"] = int(
            sum(
                counts[name]
                for name in (
                    "compact",
                    "bridge",
                    "high",
                    "low",
                    "process",
                    "process_posterior",
                    "outcome_residual_probe",
                    "topology_role_probe",
                    "transition_discriminator",
                    "skill_effect_discovery",
                )
            )
        )
        return counts

    def low_bootstrap_values(self, observations, states) -> dict[int, np.ndarray]:
        bootstrap: dict[int, np.ndarray] = {}
        if not self.use_recurrent_low_level:
            for env_id in range(self.num_envs):
                obs = np.asarray(observations[env_id], dtype=np.float32)
                obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device)
                skills_t = torch.as_tensor(self.active_skills[env_id], dtype=torch.long, device=self.device)
                with torch.no_grad():
                    _actions, _logp, _entropy, values = self.low.act(obs_t, skills_t, deterministic=True)
                bootstrap[env_id] = values.detach().cpu().numpy().astype(np.float32)
            return bootstrap

        for env_id in range(self.num_envs):
            joint_obs = self._joint_obs_array(observations[env_id])
            state_arr = self._state_array(states[env_id], joint_obs)
            state_t = torch.as_tensor(state_arr, dtype=torch.float32, device=self.device).reshape(1, -1).expand(
                self.n_agents,
                -1,
            )
            skills_t = torch.as_tensor(self.active_skills[env_id], dtype=torch.long, device=self.device)
            team_code_t = torch.full(
                (self.n_agents,),
                int(self.active_team_codes[env_id]),
                dtype=torch.long,
                device=self.device,
            )
            critic_hxs_t = torch.as_tensor(self.low_critic_hxs[env_id], dtype=torch.float32, device=self.device)
            agent_ids_t = torch.arange(self.n_agents, dtype=torch.long, device=self.device)
            with torch.no_grad():
                values = self.low.value(state_t, skills_t, team_code_t, critic_hxs_t, agent_ids_t)
                if self.low_value_norm is not None:
                    values = self.low_value_norm.denormalize_tensor(values)
            bootstrap[env_id] = values.detach().cpu().numpy().astype(np.float32)
        return bootstrap

    def _fit_vector(self, value, dim: int) -> np.ndarray:
        arr = np.asarray(value, dtype=np.float32).reshape(-1)
        if arr.size == dim:
            return arr
        fitted = np.zeros(dim, dtype=np.float32)
        n = min(dim, arr.size)
        if n > 0:
            fitted[:n] = arr[:n]
        return fitted

    def _phase_bin(self, rollout_step: int) -> int:
        env_local_step = int(max(rollout_step, 0)) // max(self.num_envs, 1)
        reference = max(int(self.intrinsic_phase_reference_steps), 1)
        phase = float(env_local_step % reference) / float(reference)
        return int(min(self.intrinsic_phase_bins - 1, max(0, np.floor(phase * self.intrinsic_phase_bins))))

    def _state_array(self, state, obs: np.ndarray) -> np.ndarray:
        if state is None:
            state = np.asarray(obs, dtype=np.float32).reshape(-1)
        return self._fit_vector(state, self.state_dim)

    def _joint_obs_array(self, obs: np.ndarray) -> np.ndarray:
        arr = np.asarray(obs, dtype=np.float32)
        if arr.shape == (self.n_agents, self.obs_dim):
            return arr
        fitted = np.zeros((self.n_agents, self.obs_dim), dtype=np.float32)
        flat = arr.reshape(-1)
        n = min(flat.size, fitted.size)
        fitted.reshape(-1)[:n] = flat[:n]
        return fitted

    def _context_tensors(
        self,
        state: np.ndarray,
        joint_obs: np.ndarray,
        deterministic: bool = False,
        forced_team_code: torch.Tensor | None = None,
    ):
        state_t = torch.as_tensor(state, dtype=torch.float32, device=self.device).reshape(1, -1)
        joint_t = torch.as_tensor(joint_obs, dtype=torch.float32, device=self.device).reshape(
            1,
            self.n_agents,
            self.obs_dim,
        )
        compact, cd_loss, cmi_loss, weights, aggregation_entropy = self.compact(state_t, joint_t)
        team_code, team_vector, team_logp, team_entropy, team_logits = self.bridge(
            compact,
            deterministic=deterministic,
            forced_team_code=forced_team_code,
        )
        return compact, team_code, team_vector, team_logp, team_entropy, cd_loss, cmi_loss, aggregation_entropy

    def reset_env_state(self, env_id: int):
        env_id = int(env_id)
        self.duration_remaining[env_id, :] = 0
        self.active_skills[env_id, :] = 0
        self.skill_age[env_id, :] = 0
        self.has_active_skill[env_id, :] = False
        self.active_team_codes[env_id] = 0
        self.low_actor_hxs[env_id, :, :] = 0.0
        self.low_critic_hxs[env_id, :, :] = 0.0
        self._last_low_context[env_id] = None

    def reset_all_policy_state(self):
        self.duration_remaining[:, :] = 0
        self.active_skills[:, :] = 0
        self.skill_age[:, :] = 0
        self.has_active_skill[:, :] = False
        self.active_team_codes[:] = 0
        self.low_actor_hxs[:, :, :] = 0.0
        self.low_critic_hxs[:, :, :] = 0.0
        self._last_low_context = [None for _ in range(self.num_envs)]
        self.segments = SegmentManager(self.num_envs, self.n_agents)

    def maybe_assign_skills(
        self,
        obs: np.ndarray,
        state=None,
        step: int = 0,
        k: int = 1,
        env_id: int = 0,
        deterministic: bool = False,
    ):
        env_id = int(env_id)
        joint_obs = self._joint_obs_array(obs)
        state_arr = self._state_array(state, joint_obs)
        expired = (~self.has_active_skill[env_id]) | (self.duration_remaining[env_id] <= 0)
        if np.any(expired):
            compact, team_code, team_vector, team_logp, team_entropy, *_ = self._context_tensors(
                state_arr,
                joint_obs,
                deterministic=deterministic,
            )
            expired_ids = np.flatnonzero(expired)
            obs_t = torch.as_tensor(joint_obs[expired_ids], dtype=torch.float32, device=self.device)
            prev_np = self.active_skills[env_id, expired_ids].copy()
            age_np = self.skill_age[env_id, expired_ids].copy()
            prev_t = torch.as_tensor(prev_np, dtype=torch.long, device=self.device)
            age_t = torch.as_tensor(age_np, dtype=torch.float32, device=self.device)
            compact_t = compact.expand(len(expired_ids), -1)
            team_vector_t = team_vector.expand(len(expired_ids), -1)
            with torch.no_grad():
                skills, duration_idx, logp, entropy, value = self.high.act(
                    obs_t,
                    prev_t,
                    age_t,
                    compact_t,
                    team_vector_t,
                    deterministic=deterministic,
                )
                if self.high_value_norm is not None:
                    value = self.high_value_norm.denormalize_tensor(value)
            chosen_skills = skills.cpu().numpy()
            chosen_duration_idx = duration_idx.cpu().numpy()
            chosen_durations = np.asarray(self.duration_candidates, dtype=np.int64)[chosen_duration_idx]
            team_code_value = int(team_code.detach().cpu().numpy()[0])
            self.active_team_codes[env_id] = team_code_value
            team_logp_weight = 1.0 / max(len(expired_ids), 1)
            team_logp_share = team_logp.detach().cpu().numpy()[0] * team_logp_weight
            team_entropy_share = team_entropy.detach().cpu().numpy()[0] * team_logp_weight
            old_logp = logp.cpu().numpy() + float(team_logp_share)
            old_entropy = entropy.cpu().numpy() + float(team_entropy_share)
            old_value = value.cpu().numpy()
            for local_idx, agent_id in enumerate(expired_ids):
                prev_skill = int(prev_np[local_idx])
                initial = not bool(self.has_active_skill[env_id, agent_id])
                switched = (not initial) and int(chosen_skills[local_idx]) != prev_skill
                penalty = 0.0
                if not initial:
                    penalty += self.edit_penalty_alpha
                if switched:
                    penalty += self.switch_penalty_beta

                self.active_skills[env_id, agent_id] = int(chosen_skills[local_idx])
                self.duration_remaining[env_id, agent_id] = int(chosen_durations[local_idx]) * int(k)
                self.skill_age[env_id, agent_id] = 0
                self.has_active_skill[env_id, agent_id] = True
                self.segments.renew(
                    env_id=env_id,
                    agent_id=int(agent_id),
                    skill=self.active_skills[env_id, agent_id],
                    duration_idx=int(chosen_duration_idx[local_idx]),
                    step=step,
                    high_obs=joint_obs[agent_id],
                    high_logp=float(old_logp[local_idx]),
                    high_value=float(old_value[local_idx]),
                    high_entropy=float(old_entropy[local_idx]),
                    high_state=state_arr,
                    high_joint_obs=joint_obs,
                    prev_skill=prev_skill,
                    skill_age_prev=int(age_np[local_idx]),
                    team_code=team_code_value,
                    team_logp_weight=team_logp_weight,
                    initial_assignment=initial,
                    switched=switched,
                    duration_target=int(chosen_durations[local_idx]),
                    renewal_penalty=penalty,
                )

        active = self.has_active_skill[env_id]
        self.duration_remaining[env_id, active] -= 1
        self.skill_age[env_id, active] += 1

    def act_low(
        self,
        obs: np.ndarray,
        env_id: int = 0,
        deterministic: bool = False,
        state=None,
        return_context: bool = False,
    ):
        env_id = int(env_id)
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device)
        skills_t = torch.as_tensor(self.active_skills[env_id], dtype=torch.long, device=self.device)
        state_arr = self._state_array(state, self._joint_obs_array(obs))
        context = {
            "state": state_arr.copy(),
            "team_code": int(self.active_team_codes[env_id]),
            "actor_hxs": self.low_actor_hxs[env_id].copy(),
            "critic_hxs": self.low_critic_hxs[env_id].copy(),
        }
        with torch.no_grad():
            if self.use_recurrent_low_level:
                state_t = torch.as_tensor(state_arr, dtype=torch.float32, device=self.device).reshape(1, -1).expand(
                    self.n_agents,
                    -1,
                )
                team_code_t = torch.full(
                    (self.n_agents,),
                    int(self.active_team_codes[env_id]),
                    dtype=torch.long,
                    device=self.device,
                )
                agent_ids_t = torch.arange(self.n_agents, dtype=torch.long, device=self.device)
                actor_hxs_t = torch.as_tensor(
                    self.low_actor_hxs[env_id],
                    dtype=torch.float32,
                    device=self.device,
                )
                critic_hxs_t = torch.as_tensor(
                    self.low_critic_hxs[env_id],
                    dtype=torch.float32,
                    device=self.device,
                )
                actions, logp, _, values, new_actor_hxs, new_critic_hxs = self.low.act(
                    obs_t,
                    skills_t,
                    actor_hxs_t,
                    state_t,
                    team_code_t,
                    critic_hxs_t,
                    agent_ids_t,
                    deterministic=deterministic,
                )
                self.low_actor_hxs[env_id] = new_actor_hxs.detach().cpu().numpy().astype(np.float32)
                self.low_critic_hxs[env_id] = new_critic_hxs.detach().cpu().numpy().astype(np.float32)
                if self.low_value_norm is not None:
                    values = self.low_value_norm.denormalize_tensor(values)
            else:
                actions, logp, _, values = self.low.act(
                    obs_t,
                    skills_t,
                    deterministic=deterministic,
                )
        self._last_low_context[env_id] = context
        result = (
            actions.cpu().numpy().astype(np.int64 if self.action_space_type == "discrete" else np.float32),
            logp.cpu().numpy().astype(np.float32),
            values.cpu().numpy().astype(np.float32),
        )
        if return_context:
            return (*result, context)
        return (
            *result,
        )

    def _low_actor_forced_skill_outputs(
        self,
        obs_np: np.ndarray,
        skills_np: np.ndarray,
        team_codes_np: np.ndarray,
        agent_ids_np: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return low-actor action-distribution features under forced skills.

        This is a diagnostic-only path for P3-2c.  It does not sample from or
        mutate the rollout hidden state; recurrent actors use zero hidden state
        so the same observation can be compared across all forced skill labels.
        """
        obs_t = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device)
        skills_t = torch.as_tensor(skills_np, dtype=torch.long, device=self.device)
        team_t = torch.as_tensor(team_codes_np, dtype=torch.long, device=self.device)
        count = int(obs_t.shape[0])

        def _continuous_from_action_out(action_out, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            if hasattr(action_out, "_distribution"):
                dist = action_out._distribution(features)
                mean = torch.tanh(dist.mean) if action_out.__class__.__name__ == "TanhDiagGaussian" else dist.mean
                entropy = dist.entropy()
                if entropy.dim() > 1:
                    entropy = entropy.sum(dim=-1)
                return mean, entropy
            if hasattr(action_out, "fc_mean"):
                mean = action_out.fc_mean(features)
                return mean, torch.zeros(mean.shape[0], dtype=torch.float32, device=features.device)
            action, _logp = action_out(features, deterministic=True)
            if action.dim() == 1:
                action = action.unsqueeze(-1)
            return action.float(), torch.zeros(action.shape[0], dtype=torch.float32, device=features.device)

        with torch.no_grad():
            if isinstance(self.low, StrictHMASDMAPPOLowLevelPolicy):
                actor_hxs = torch.zeros(count, self.low.hidden_dim, dtype=torch.float32, device=self.device)
                masks = torch.ones(count, 1, dtype=torch.float32, device=self.device)
                actor_features = self.low._actor_features(obs_t, skills_t, team_t)
                actor_features, _new_hxs = self.low.actor_rnn(actor_features, actor_hxs, masks)
                if self.action_space_type == "discrete":
                    dist = self.low.actor_act.action_out(actor_features)
                    action_features = dist.probs.float()
                    entropy = dist.entropy().float()
                else:
                    action_features, entropy = _continuous_from_action_out(self.low.actor_act.action_out, actor_features)
            elif isinstance(self.low, RecurrentLowLevelPolicy):
                actor_hxs = torch.zeros(count, self.low.hidden_dim, dtype=torch.float32, device=self.device)
                actor_input = self.low._actor_features(obs_t, skills_t)
                actor_h = self.low.actor_rnn(actor_input, actor_hxs)
                dist, actor_out = self.low._dist(actor_h)
                if self.action_space_type == "discrete":
                    action_features = dist.probs.float()
                    entropy = dist.entropy().float()
                else:
                    action_features = actor_out.float()
                    entropy = dist.entropy()
                    if entropy.dim() > 1:
                        entropy = entropy.sum(dim=-1)
            else:
                features = self.low._features(obs_t, skills_t)
                actor_out = self.low.actor(features)
                if self.action_space_type == "discrete":
                    dist = torch.distributions.Categorical(logits=actor_out)
                    action_features = dist.probs.float()
                    entropy = dist.entropy().float()
                else:
                    action_features = actor_out.float()
                    std = torch.exp(self.low.log_std).expand_as(actor_out)
                    entropy = torch.distributions.Normal(actor_out, std).entropy().sum(dim=-1)

        return (
            action_features.detach().cpu().numpy().astype(np.float32),
            entropy.detach().cpu().numpy().astype(np.float32),
        )

    def duration_only_accuracy(self, labels: np.ndarray, durations: np.ndarray) -> float:
        if labels.size == 0:
            return 0.0
        correct = 0
        for duration in np.unique(durations):
            mask = durations == duration
            if not np.any(mask):
                continue
            counts = np.bincount(labels[mask], minlength=self.n_skills)
            correct += int(np.max(counts))
        return float(correct) / float(labels.size)

    def binned_scalar_accuracy(self, labels: np.ndarray, values: np.ndarray, num_bins: int = 5) -> float:
        labels = np.asarray(labels, dtype=np.int64).reshape(-1)
        values = np.asarray(values, dtype=np.float64).reshape(-1)
        if labels.size == 0 or labels.size != values.size:
            return 0.0
        finite = np.isfinite(values)
        if not np.any(finite):
            return 0.0
        labels = labels[finite]
        values = values[finite]
        if values.size == 0:
            return 0.0
        if np.unique(values).size <= 1:
            bins = np.zeros(values.shape[0], dtype=np.int64)
        else:
            quantiles = np.linspace(0.0, 1.0, int(max(num_bins, 2)) + 1)[1:-1]
            edges = np.unique(np.quantile(values, quantiles))
            bins = np.digitize(values, edges, right=False)
        return self.duration_only_accuracy(labels, bins)

    def _g_intervention_kl_metrics(
        self,
        segments: list[Segment],
        segment_states: torch.Tensor,
        segment_joint_obs: torch.Tensor,
        start_obs: torch.Tensor,
    ) -> dict[str, float]:
        metrics = {
            "g_intervention_kl_active": 0.0,
            "g_intervention_kl_samples": 0.0,
            "g_intervention_kl_mean": 0.0,
            "g_intervention_kl_max": 0.0,
            "g_intervention_tv_mean": 0.0,
        }
        if (
            not self.use_g_intervention_kl_diagnostic
            or not segments
            or self.num_team_codes <= 1
            or getattr(self.bridge, "bridge_type", "none") != "stochastic"
        ):
            return metrics

        sample_count = min(len(segments), int(self.g_intervention_kl_max_segments))
        if sample_count <= 0:
            return metrics
        if sample_count < len(segments):
            sample_idx = torch.linspace(
                0,
                len(segments) - 1,
                steps=sample_count,
                device=self.device,
            ).long()
        else:
            sample_idx = torch.arange(len(segments), device=self.device)

        sampled_segments = [segments[int(idx.detach().cpu().item())] for idx in sample_idx]
        states = segment_states.index_select(0, sample_idx)
        joint_obs = segment_joint_obs.index_select(0, sample_idx)
        high_obs = start_obs.index_select(0, sample_idx)
        prev_skills = torch.as_tensor(
            [segment.prev_skill for segment in sampled_segments],
            dtype=torch.long,
            device=self.device,
        )
        ages = torch.as_tensor(
            [segment.skill_age_prev for segment in sampled_segments],
            dtype=torch.float32,
            device=self.device,
        )

        with torch.no_grad():
            compact, _cd, _cmi, _weights, _entropy = self.compact(states, joint_obs)
            codes = torch.arange(self.num_team_codes, dtype=torch.long, device=self.device)
            team_vectors = self.bridge.code_embedding(codes)
            batch_size = high_obs.shape[0]
            num_codes = int(self.num_team_codes)
            skill_logits, _duration_logits, _values = self.high.logits(
                high_obs.unsqueeze(1).expand(batch_size, num_codes, self.obs_dim).reshape(batch_size * num_codes, -1),
                prev_skills.unsqueeze(1).expand(batch_size, num_codes).reshape(-1),
                ages.unsqueeze(1).expand(batch_size, num_codes).reshape(-1),
                compact.unsqueeze(1).expand(batch_size, num_codes, compact.shape[-1]).reshape(batch_size * num_codes, -1),
                team_vectors.unsqueeze(0).expand(batch_size, num_codes, team_vectors.shape[-1]).reshape(batch_size * num_codes, -1),
            )
            probs = F.softmax(skill_logits, dim=-1).reshape(batch_size, num_codes, self.n_skills)
            log_probs = F.log_softmax(skill_logits, dim=-1).reshape(batch_size, num_codes, self.n_skills)
            kl = torch.sum(
                probs.unsqueeze(2) * (log_probs.unsqueeze(2) - log_probs.unsqueeze(1)),
                dim=-1,
            )
            tv = 0.5 * torch.sum(torch.abs(probs.unsqueeze(2) - probs.unsqueeze(1)), dim=-1)
            mask = ~torch.eye(num_codes, dtype=torch.bool, device=self.device).unsqueeze(0)
            kl_values = kl[mask.expand_as(kl)]
            tv_values = tv[mask.expand_as(tv)]
            if kl_values.numel() == 0:
                return metrics
            metrics.update(
                {
                    "g_intervention_kl_active": 1.0,
                    "g_intervention_kl_samples": float(sample_count),
                    "g_intervention_kl_mean": float(kl_values.mean().detach().cpu().item()),
                    "g_intervention_kl_max": float(kl_values.max().detach().cpu().item()),
                    "g_intervention_tv_mean": float(tv_values.mean().detach().cpu().item()),
                }
            )
        return metrics

    @staticmethod
    def _usage_stats(values: np.ndarray, cardinality: int) -> tuple[float, float]:
        values = np.asarray(values, dtype=np.int64).reshape(-1)
        cardinality = int(max(cardinality, 1))
        if values.size == 0:
            return 0.0, 0.0
        counts = np.bincount(np.clip(values, 0, cardinality - 1), minlength=cardinality).astype(np.float64)
        probs = counts / max(float(counts.sum()), 1.0)
        nonzero = probs[probs > 0.0]
        entropy = -float(np.sum(nonzero * np.log(nonzero))) if nonzero.size else 0.0
        norm_entropy = entropy / float(np.log(cardinality)) if cardinality > 1 else 0.0
        return norm_entropy, float(np.max(probs))

    @staticmethod
    def _joint_mi_norm(x: np.ndarray, y: np.ndarray, x_cardinality: int, y_cardinality: int) -> float:
        x = np.asarray(x, dtype=np.int64).reshape(-1)
        y = np.asarray(y, dtype=np.int64).reshape(-1)
        if x.size == 0 or y.size == 0 or x.size != y.size:
            return 0.0
        x_cardinality = int(max(x_cardinality, 1))
        y_cardinality = int(max(y_cardinality, 1))
        x = np.clip(x, 0, x_cardinality - 1)
        y = np.clip(y, 0, y_cardinality - 1)
        joint = np.zeros((x_cardinality, y_cardinality), dtype=np.float64)
        for x_value, y_value in zip(x, y):
            joint[int(x_value), int(y_value)] += 1.0
        joint /= max(float(joint.sum()), 1.0)
        px = joint.sum(axis=1, keepdims=True)
        py = joint.sum(axis=0, keepdims=True)
        expected = px @ py
        mask = joint > 0.0
        mi = float(np.sum(joint[mask] * (np.log(joint[mask]) - np.log(expected[mask]))))
        norm = float(min(np.log(x_cardinality), np.log(y_cardinality))) if min(x_cardinality, y_cardinality) > 1 else 0.0
        return mi / norm if norm > 0.0 else 0.0

    def _transition_discriminator_batch(self, valid: list[Segment]) -> dict[str, np.ndarray] | None:
        if self.transition_discriminator is None:
            return None
        action_dim = 1 if self.action_space_type == "discrete" else self.action_dim
        obs_rows: list[np.ndarray] = []
        action_rows: list[np.ndarray] = []
        delta_rows: list[np.ndarray] = []
        reward_rows: list[float] = []
        label_rows: list[int] = []
        team_rows: list[int] = []
        rollout_rows: list[int] = []
        agent_rows: list[int] = []
        start_obs_rows: list[np.ndarray] = []
        phase_rows: list[int] = []

        for segment in valid:
            length = int(segment.length)
            if length <= 0:
                continue
            segment_start_obs = self._fit_vector(segment.high_obs, self.obs_dim)
            segment_phase_bin = self._phase_bin(segment.start_step)
            for step_idx in range(length):
                current_obs = self._fit_vector(segment.obs[step_idx], self.obs_dim)
                if step_idx + 1 < length:
                    next_obs = self._fit_vector(segment.obs[step_idx + 1], self.obs_dim)
                elif segment.end_obs is not None:
                    next_obs = self._fit_vector(segment.end_obs, self.obs_dim)
                else:
                    next_obs = current_obs
                obs_rows.append(current_obs)
                action_rows.append(self._fit_vector(segment.actions[step_idx], action_dim))
                delta_rows.append((next_obs - current_obs).astype(np.float32, copy=False))
                reward_rows.append(float(segment.rewards[step_idx]))
                label_rows.append(int(segment.skill))
                team_rows.append(int(segment.team_code))
                rollout_rows.append(int(segment.rollout_indices[step_idx]))
                agent_rows.append(int(segment.agent_id))
                start_obs_rows.append(segment_start_obs)
                phase_rows.append(segment_phase_bin)

        if not obs_rows:
            return None

        sample_count = len(obs_rows)
        max_samples = int(self.transition_skill_max_samples)
        if sample_count > max_samples:
            chosen = np.random.choice(sample_count, size=max_samples, replace=False)
        else:
            chosen = np.arange(sample_count)

        return {
            "obs": np.asarray(obs_rows, dtype=np.float32)[chosen],
            "actions": np.asarray(action_rows, dtype=np.float32)[chosen],
            "delta_obs": np.asarray(delta_rows, dtype=np.float32)[chosen],
            "rewards": np.asarray(reward_rows, dtype=np.float32)[chosen],
            "labels": np.asarray(label_rows, dtype=np.int64)[chosen],
            "team_codes": np.asarray(team_rows, dtype=np.int64)[chosen],
            "rollout_indices": np.asarray(rollout_rows, dtype=np.int64)[chosen],
            "agent_ids": np.asarray(agent_rows, dtype=np.int64)[chosen],
            "start_obs": np.asarray(start_obs_rows, dtype=np.float32)[chosen],
            "phase_bins": np.asarray(phase_rows, dtype=np.int64)[chosen],
            "sample_count": np.asarray([len(chosen)], dtype=np.int64),
            "available_count": np.asarray([sample_count], dtype=np.int64),
        }

    def process_update(self, rollout: Rollout, total_steps: int = 0) -> dict[str, float]:
        segments = self.segments.pop_completed()
        valid = [s for s in segments if s.length > 0]
        if not valid:
            return {
                "process_segments": 0.0,
                "process_loss": 0.0,
                "process_outcome_loss": 0.0,
                "process_contrastive_loss": 0.0,
                "process_prior_loss": 0.0,
                "process_posterior_acc": 0.0,
                "process_mi_estimate_mean": 0.0,
                "process_residual_mi_mean": 0.0,
                "process_residual_mi_positive_frac": 0.0,
                "process_residual_log_shortcut_mean": 0.0,
                "process_residual_log_context_mean": 0.0,
                "process_log_q_mean": 0.0,
                "process_log_p_mean": 0.0,
                "process_shortcut_loss": 0.0,
                "process_shortcut_margin_loss": 0.0,
                "process_reward_warmup_active": 0.0,
                "transition_skill_samples": 0.0,
                "transition_skill_available_samples": 0.0,
                "transition_skill_loss": 0.0,
                "transition_skill_prior_loss": 0.0,
                "transition_skill_acc": 0.0,
                "transition_skill_mi_mean": 0.0,
                "transition_skill_mi_positive_frac": 0.0,
                "transition_skill_residual_mi_mean": 0.0,
                "transition_skill_residual_mi_positive_frac": 0.0,
                "transition_skill_context_loss": 0.0,
                "transition_skill_context_acc": 0.0,
                "transition_skill_log_context_mean": 0.0,
                "transition_skill_reward_mean": 0.0,
                "transition_skill_reward_active": 0.0,
                "transition_skill_log_q_mean": 0.0,
                "transition_skill_log_p_mean": 0.0,
                "transition_skill_reward_unclipped_mean": 0.0,
                "transition_skill_reward_warmup_active": 0.0,
                "intrinsic_segment_high_gate_active": 0.0,
                "intrinsic_segment_high_gate_score": 0.0,
                "intrinsic_segment_high_gate_posterior_minus_shortcut": 0.0,
                "intrinsic_segment_high_gate_residual_mi": 0.0,
                "intrinsic_segment_high_gate_segment_count": 0.0,
                "intrinsic_segment_high_gate_reason_code": 0.0,
                "process_shortcut_duration_acc": 0.0,
                "process_shortcut_length_acc": 0.0,
                "process_shortcut_reward_sum_acc": 0.0,
                "process_shortcut_context_acc": 0.0,
                "process_shortcut_context_loss": 0.0,
                "process_shortcut_max_acc": 0.0,
                "posterior_acc_minus_shortcut_max": 0.0,
                "posterior_acc_minus_context_shortcut": 0.0,
                "process_reward_mi_component_mean": 0.0,
                "process_reward_outcome_penalty_mean": 0.0,
                "process_reward_unclipped_mean": 0.0,
                "process_mi_positive_frac": 0.0,
                "process_reward_mean": 0.0,
                "process_reward_high_mean": 0.0,
                "process_reward_low_mean": 0.0,
                "semantic_shortcut_hard_stop_triggered": 0.0,
                "semantic_shortcut_hard_stop_applied": 0.0,
                "semantic_shortcut_hard_stop_score": 0.0,
                "semantic_shortcut_hard_stop_reason_code": 0.0,
                "outcome_available_mean": 0.0,
                "outcome_abs_mean": 0.0,
                "outcome_residual_full_loss": 0.0,
                "outcome_residual_base_loss": 0.0,
                "outcome_residual_total_loss": 0.0,
                "outcome_residual_gain_mean": 0.0,
                "outcome_residual_gain_positive_frac": 0.0,
                "outcome_residual_available_mean": 0.0,
                "outcome_residual_target_abs_mean": 0.0,
                "outcome_residual_reward_mean": 0.0,
                "outcome_residual_reward_active": 0.0,
                "outcome_residual_reward_unclipped_mean": 0.0,
                "outcome_residual_skill_gain_std": 0.0,
                "outcome_residual_team_gain_std": 0.0,
                "outcome_residual_duration_gain_std": 0.0,
                "outcome_residual_gain_coverage_delta_h": 0.0,
                "outcome_residual_gain_qos_delta_h": 0.0,
                "outcome_residual_gain_full_disconnect_improvement_h": 0.0,
                "outcome_residual_gain_relay_margin_delta_h": 0.0,
                "outcome_residual_gain_connected_components_improvement_h": 0.0,
                "outcome_residual_gain_teammate_service_gain_h": 0.0,
                "outcome_residual_gain_bottleneck_link_gain_h": 0.0,
                "duration_only_accuracy": 0.0,
                "length_only_accuracy": 0.0,
                "reward_sum_only_accuracy": 0.0,
                "posterior_acc_minus_duration_only": 0.0,
                "posterior_acc_minus_length_only": 0.0,
                "posterior_acc_minus_reward_sum_only": 0.0,
                "segment_length_mean": 0.0,
                "segment_length_max": 0.0,
                "duration_target_mean": 0.0,
                "skill_switch_rate": 0.0,
                "initial_assignment_rate": 0.0,
                "skill_usage_entropy": 0.0,
                "skill_usage_max_frac": 0.0,
                "duration_usage_entropy": 0.0,
                "duration_usage_max_frac": 0.0,
                "skill_duration_mi": 0.0,
                "team_code_usage_entropy": 0.0,
                "team_code_usage_max_frac": 0.0,
                "team_code_skill_mi": 0.0,
                "g_intervention_kl_active": 0.0,
                "g_intervention_kl_samples": 0.0,
                "g_intervention_kl_mean": 0.0,
                "g_intervention_kl_max": 0.0,
                "g_intervention_tv_mean": 0.0,
                "g_usage_entropy": 0.0,
                "g_usage_max_frac": 0.0,
                "team_code_duration_mi": 0.0,
                "team_code_edit_mi": 0.0,
                "high_loss": 0.0,
                "high_policy_loss": 0.0,
                "high_value_loss": 0.0,
                "high_entropy_loss": 0.0,
                "high_aux_loss": 0.0,
                "high_entropy": 0.0,
                "high_return_mean": 0.0,
                "high_env_return_mean": 0.0,
                "high_bootstrap_value_mean": 0.0,
                "high_bootstrap_contribution_mean": 0.0,
                "high_smdp_discount_mean": 0.0,
                "high_value_norm_mean": float(self.high_value_norm.mean) if self.high_value_norm is not None else 0.0,
                "high_value_norm_std": float(np.sqrt(self.high_value_norm.var)) if self.high_value_norm is not None else 0.0,
                "high_grad_norm": 0.0,
                **empty_cooperation_credit_metrics(),
                **empty_topology_role_metrics(),
                **empty_topology_potential_metrics(),
                **empty_p2_metrics(),
                **empty_g_info_metrics(),
                **empty_skill_effect_metrics(),
            }

        effect_metrics, effect_micro_rewards = (
            self.skill_effect_discovery.update(valid, total_steps=total_steps)
            if self.skill_effect_discovery is not None
            else (empty_skill_effect_metrics(), {})
        )
        if self.skill_effect_discovery is not None:
            effect_metrics.update(
                self.skill_effect_discovery.intervention_audit(
                    valid,
                    action_probe_fn=self._low_actor_forced_skill_outputs,
                )
            )

        max_len = max(s.length for s in valid)
        obs = np.zeros((len(valid), max_len, valid[0].obs[0].shape[0]), dtype=np.float32)
        action_dim = valid[0].actions[0].size
        actions = np.zeros((len(valid), max_len, action_dim), dtype=np.float32)
        rewards = np.zeros((len(valid), max_len), dtype=np.float32)
        masks = np.zeros((len(valid), max_len), dtype=np.float32)
        labels = np.zeros(len(valid), dtype=np.int64)
        durations_np = np.zeros(len(valid), dtype=np.int64)
        team_codes_np = np.zeros(len(valid), dtype=np.int64)
        start_obs_np = np.zeros((len(valid), self.obs_dim), dtype=np.float32)
        agent_ids_np = np.zeros(len(valid), dtype=np.int64)
        phase_bins_np = np.zeros(len(valid), dtype=np.int64)
        outcomes = np.zeros((len(valid), self.outcome_extractor.num_outcomes), dtype=np.float32)
        outcome_masks = np.zeros_like(outcomes, dtype=np.float32)
        raw_outcomes = np.zeros_like(outcomes, dtype=np.float32)
        future_outcome_dim = (
            self.outcome_residual_extractor.num_outcomes
            if self.outcome_residual_extractor is not None
            else len(FUTURE_COOPERATION_OUTCOME_FIELDS)
        )
        future_outcomes = np.zeros((len(valid), future_outcome_dim), dtype=np.float32)
        future_outcome_masks = np.zeros_like(future_outcomes, dtype=np.float32)
        raw_future_outcomes = np.zeros_like(future_outcomes, dtype=np.float32)
        topology_feature_dim = len(TOPOLOGY_ROLE_FIELDS)
        topology_features = np.zeros((len(valid), topology_feature_dim), dtype=np.float32)
        topology_role_labels = np.zeros(len(valid), dtype=np.int64)
        topology_role_masks = np.zeros(len(valid), dtype=np.float32)
        topology_role_scores = np.zeros((len(valid), len(TOPOLOGY_ROLE_NAMES)), dtype=np.float32)
        segment_states_np = np.zeros((len(valid), self.state_dim), dtype=np.float32)
        segment_joint_obs_np = np.zeros((len(valid), self.n_agents, self.obs_dim), dtype=np.float32)
        for idx, segment in enumerate(valid):
            length = segment.length
            obs[idx, :length] = np.asarray(segment.obs, dtype=np.float32)
            actions[idx, :length] = np.asarray(segment.actions, dtype=np.float32)
            rewards[idx, :length] = np.asarray(segment.rewards, dtype=np.float32)
            masks[idx, :length] = 1.0
            labels[idx] = int(segment.skill)
            durations_np[idx] = int(segment.duration_idx)
            team_codes_np[idx] = int(segment.team_code)
            start_obs_np[idx] = self._fit_vector(segment.high_obs, self.obs_dim)
            agent_ids_np[idx] = int(segment.agent_id)
            phase_bins_np[idx] = self._phase_bin(segment.start_step)
            raw, outcome_mask, normalized = self.outcome_extractor.transform(segment, update=True)
            raw_outcomes[idx] = raw
            outcomes[idx] = normalized
            outcome_masks[idx] = outcome_mask.astype(np.float32)
            if self.outcome_residual_extractor is not None:
                raw_future, future_mask, normalized_future = self.outcome_residual_extractor.transform(
                    segment,
                    update=True,
                )
                raw_future_outcomes[idx] = raw_future
                future_outcomes[idx] = normalized_future
                future_outcome_masks[idx] = future_mask.astype(np.float32)
            if self.topology_role_extractor is not None:
                role_sample = self.topology_role_extractor.extract(segment)
                topology_features[idx] = role_sample.features
                topology_role_labels[idx] = int(role_sample.label)
                topology_role_masks[idx] = float(role_sample.available)
                topology_role_scores[idx] = role_sample.role_scores
            segment_states_np[idx] = self._segment_state(segment)
            segment_joint_obs_np[idx] = self._segment_joint_obs(segment)

        lengths = np.asarray([s.length for s in valid], dtype=np.float32)
        reward_sums = np.asarray([np.sum(s.rewards) for s in valid], dtype=np.float32)
        obs_t = torch.as_tensor(obs, device=self.device)
        actions_t = torch.as_tensor(actions, device=self.device)
        rewards_t = torch.as_tensor(rewards, device=self.device)
        masks_t = torch.as_tensor(masks, device=self.device)
        labels_t = torch.as_tensor(labels, device=self.device)
        durations_t = torch.as_tensor(durations_np, dtype=torch.long, device=self.device)
        lengths_t = torch.as_tensor(lengths, dtype=torch.float32, device=self.device)
        reward_sums_t = torch.as_tensor(reward_sums, dtype=torch.float32, device=self.device)
        team_codes_t = torch.as_tensor(team_codes_np, dtype=torch.long, device=self.device)
        start_obs_t = torch.as_tensor(start_obs_np, dtype=torch.float32, device=self.device)
        agent_ids_t = torch.as_tensor(agent_ids_np, dtype=torch.long, device=self.device)
        phase_bins_t = torch.as_tensor(phase_bins_np, dtype=torch.long, device=self.device)
        outcomes_t = torch.as_tensor(outcomes, device=self.device)
        outcome_masks_t = torch.as_tensor(outcome_masks, device=self.device)
        future_outcomes_t = torch.as_tensor(future_outcomes, dtype=torch.float32, device=self.device)
        future_outcome_masks_t = torch.as_tensor(future_outcome_masks, dtype=torch.float32, device=self.device)
        topology_features_t = torch.as_tensor(topology_features, dtype=torch.float32, device=self.device)
        topology_role_labels_t = torch.as_tensor(topology_role_labels, dtype=torch.long, device=self.device)
        topology_role_masks_t = torch.as_tensor(topology_role_masks, dtype=torch.float32, device=self.device)
        segment_states_t = torch.as_tensor(segment_states_np, dtype=torch.float32, device=self.device)
        segment_joint_obs_t = torch.as_tensor(segment_joint_obs_np, dtype=torch.float32, device=self.device)
        if self.topology_role_probe is not None:
            with torch.no_grad():
                opt_context_t, _cd, _cmi, _weights, _entropy = self.compact(segment_states_t, segment_joint_obs_t)
        else:
            opt_context_t = torch.zeros(
                (len(valid), int(getattr(self.compact, "compact_dim", 1))),
                dtype=torch.float32,
                device=self.device,
            )
        g_intervention_metrics = self._g_intervention_kl_metrics(
            valid,
            segment_states_t,
            segment_joint_obs_t,
            start_obs_t,
        )

        transition_batch = self._transition_discriminator_batch(valid)
        transition_labels_t = None
        transition_rollout_indices = np.zeros(0, dtype=np.int64)
        transition_agent_ids = np.zeros(0, dtype=np.int64)
        transition_loss = torch.zeros((), device=self.device)
        transition_prior_loss = torch.zeros((), device=self.device)
        transition_context_loss = torch.zeros((), device=self.device)
        transition_acc = torch.zeros((), device=self.device)
        transition_context_acc = torch.zeros((), device=self.device)
        transition_logits_for_reward = None
        transition_prior_logits_for_reward = None
        transition_context_logits_for_reward = None
        transition_sample_count = 0
        transition_available_count = 0
        if transition_batch is not None and self.transition_discriminator is not None:
            transition_obs_t = torch.as_tensor(transition_batch["obs"], device=self.device)
            transition_actions_t = torch.as_tensor(transition_batch["actions"], device=self.device)
            transition_delta_t = torch.as_tensor(transition_batch["delta_obs"], device=self.device)
            transition_rewards_t = torch.as_tensor(transition_batch["rewards"], device=self.device)
            transition_labels_t = torch.as_tensor(transition_batch["labels"], dtype=torch.long, device=self.device)
            transition_team_t = torch.as_tensor(transition_batch["team_codes"], dtype=torch.long, device=self.device)
            transition_start_obs_t = torch.as_tensor(transition_batch["start_obs"], dtype=torch.float32, device=self.device)
            transition_agent_ids_t = torch.as_tensor(
                transition_batch["agent_ids"],
                dtype=torch.long,
                device=self.device,
            )
            transition_phase_bins_t = torch.as_tensor(
                transition_batch["phase_bins"],
                dtype=torch.long,
                device=self.device,
            )
            transition_rollout_indices = np.asarray(transition_batch["rollout_indices"], dtype=np.int64)
            transition_agent_ids = np.asarray(transition_batch["agent_ids"], dtype=np.int64)
            transition_sample_count = int(transition_batch["sample_count"][0])
            transition_available_count = int(transition_batch["available_count"][0])
            transition_logits, transition_prior_logits = self.transition_discriminator(
                transition_obs_t,
                transition_actions_t,
                transition_delta_t,
                transition_rewards_t,
                transition_team_t,
            )
            transition_terms = self.transition_discriminator.losses(
                transition_logits,
                transition_prior_logits,
                transition_labels_t,
            )
            transition_loss = transition_terms["posterior_loss"]
            transition_prior_loss = transition_terms["prior_loss"]
            transition_acc = transition_terms["posterior_acc"]
            transition_logits_for_reward = transition_logits.detach()
            transition_prior_logits_for_reward = transition_prior_logits.detach()
            if self.use_context_skill_shortcut and self.transition_discriminator.use_context_shortcut:
                transition_context_logits = self.transition_discriminator.context_shortcut_logits(
                    transition_start_obs_t,
                    transition_team_t,
                    transition_agent_ids_t,
                    transition_phase_bins_t,
                )
                transition_context_loss = F.cross_entropy(transition_context_logits, transition_labels_t)
                transition_context_acc = (
                    transition_context_logits.argmax(dim=-1) == transition_labels_t
                ).float().mean()
                transition_context_logits_for_reward = transition_context_logits.detach()

        emb, pred_outcome, legacy_logits = self.process(obs_t, actions_t, rewards_t, masks_t)
        outcome_sq_error = torch.square(pred_outcome - outcomes_t) * outcome_masks_t
        outcome_loss = outcome_sq_error.sum() / outcome_masks_t.sum().clamp_min(1.0)
        outcome_residual_loss = torch.zeros((), device=self.device)
        outcome_residual_terms: dict[str, torch.Tensor] | None = None
        if self.outcome_residual_probe is not None:
            outcome_full_pred, outcome_base_pred = self.outcome_residual_probe(
                emb,
                labels_t,
                start_obs_t,
                team_codes_t,
                agent_ids_t,
                phase_bins_t,
                durations_t,
                lengths_t,
                reward_sums_t,
            )
            outcome_residual_terms = self.outcome_residual_probe.losses(
                outcome_full_pred,
                outcome_base_pred,
                future_outcomes_t,
                future_outcome_masks_t,
            )
            outcome_residual_loss = (
                outcome_residual_terms["full_loss"] + outcome_residual_terms["baseline_loss"]
            )
        shortcut_loss = torch.zeros((), device=self.device)
        context_shortcut_loss = torch.zeros((), device=self.device)
        shortcut_margin_loss = torch.zeros((), device=self.device)
        shortcut_terms = None
        if self.use_process_posterior_mi:
            posterior_logits, prior_logits = self.process_posterior(emb, team_codes_t)
            posterior_terms = self.process_posterior.losses(posterior_logits, prior_logits, labels_t)
            contrastive_loss = posterior_terms["posterior_loss"]
            prior_loss = posterior_terms["prior_loss"]
            posterior_acc = posterior_terms["posterior_acc"]
            posterior_logits_for_reward = posterior_logits
            prior_logits_for_reward = prior_logits
            if self.use_residual_process_posterior:
                shortcut_terms = self.process_posterior.shortcut_losses(
                    labels_t,
                    durations_t,
                    lengths_t,
                    reward_sums_t,
                    start_obs=start_obs_t,
                    team_codes=team_codes_t,
                    agent_ids=agent_ids_t,
                    phase_bins=phase_bins_t,
                )
                shortcut_loss = shortcut_terms["shortcut_loss"]
                context_shortcut_loss = shortcut_terms["context_loss"]
                if self.process_shortcut_margin > 0.0:
                    train_log_q = F.log_softmax(posterior_logits, dim=-1)[
                        torch.arange(len(valid), device=self.device),
                        labels_t,
                    ]
                    train_log_p = F.log_softmax(prior_logits, dim=-1)[
                        torch.arange(len(valid), device=self.device),
                        labels_t,
                    ].detach()
                    shortcut_baseline = torch.maximum(
                        train_log_p,
                        shortcut_terms["max_log_q"].to(device=self.device, dtype=train_log_q.dtype).detach(),
                    )
                    shortcut_margin_loss = torch.relu(
                        float(self.process_shortcut_margin) - (train_log_q - shortcut_baseline)
                    ).mean()
        else:
            contrastive_loss = F.cross_entropy(legacy_logits, labels_t)
            prior_loss = torch.zeros((), device=self.device)
            posterior_acc = (legacy_logits.argmax(dim=-1) == labels_t).float().mean()
            posterior_logits_for_reward = legacy_logits
            prior_logits_for_reward = None
        topology_role_loss = torch.zeros((), device=self.device)
        topology_role_terms: dict[str, torch.Tensor] | None = None
        if self.topology_role_probe is not None:
            topology_full_logits, topology_shortcut_logits = self.topology_role_probe(
                topology_features_t,
                emb,
                labels_t,
                start_obs_t,
                opt_context_t,
                team_codes_t,
                agent_ids_t,
                phase_bins_t,
                durations_t,
                lengths_t,
                reward_sums_t,
            )
            topology_role_terms = self.topology_role_probe.losses(
                topology_full_logits,
                topology_shortcut_logits,
                topology_role_labels_t,
                topology_role_masks_t,
            )
            topology_role_loss = topology_role_terms["total_loss"]
        loss = (
            self.process_outcome_coef * outcome_loss
            + self.outcome_residual_coef * outcome_residual_loss
            + self.topology_role_coef * topology_role_loss
            + self.process_contrast_coef * contrastive_loss
            + (self.process_prior_coef * prior_loss if self.use_process_posterior_mi else 0.0)
            + (
                self.process_shortcut_coef * shortcut_loss
                if self.use_process_posterior_mi and self.use_residual_process_posterior
                else 0.0
            )
            + (
                self.context_shortcut_coef * context_shortcut_loss
                if self.use_process_posterior_mi and self.use_residual_process_posterior
                else 0.0
            )
            + (
                self.process_shortcut_margin_coef * shortcut_margin_loss
                if self.use_process_posterior_mi and self.use_residual_process_posterior
                else 0.0
            )
            + (
                self.transition_skill_coef * transition_loss
                + self.transition_skill_prior_coef * transition_prior_loss
                + self.transition_context_shortcut_coef * transition_context_loss
                if self.transition_discriminator is not None
                else 0.0
            )
        )
        # Reward uses the pre-update posterior for this rollout. The posterior is
        # trained below, after these logits and outcome errors are detached.
        reward_logits = posterior_logits_for_reward.detach()
        reward_prior_logits = None if prior_logits_for_reward is None else prior_logits_for_reward.detach()
        reward_outcome_sq_error = outcome_sq_error.detach()
        reward_outcome_masks = outcome_masks_t.detach()
        self.process_opt.zero_grad()
        loss.backward()
        self.process_opt.step()

        with torch.no_grad():
            log_q = F.log_softmax(reward_logits, dim=-1)[
                torch.arange(len(valid), device=self.device),
                labels_t,
            ]
            if self.use_process_posterior_mi and reward_prior_logits is not None:
                log_p = F.log_softmax(reward_prior_logits, dim=-1)[
                    torch.arange(len(valid), device=self.device),
                    labels_t,
                ]
                mi_estimate = log_q - log_p
            else:
                log_p = torch.full_like(log_q, -float(np.log(self.n_skills)))
                mi_estimate = log_q + float(np.log(self.n_skills))
            if shortcut_terms is not None:
                shortcut_log_q = shortcut_terms["max_log_q"].to(device=self.device, dtype=log_q.dtype)
                if self.process_posterior.use_context_shortcut:
                    context_log_q = shortcut_terms["log_q_context"].to(device=self.device, dtype=log_q.dtype)
                else:
                    context_log_q = log_p
            else:
                shortcut_log_q = log_p
                context_log_q = log_p
            residual_log_baseline = torch.maximum(log_p, shortcut_log_q)
            residual_mi_estimate = log_q - residual_log_baseline
            outcome_error = reward_outcome_sq_error.sum(dim=-1) / reward_outcome_masks.sum(dim=-1).clamp_min(1.0)
            if self.process_reward_mode in {
                "residual_mi",
                "positive_residual_mi",
                "centered_residual_mi",
                "residual_mi_outcome",
            }:
                semantic_estimate = residual_mi_estimate
            else:
                semantic_estimate = mi_estimate
            mi_component = self.process_reward_contrast_coef * semantic_estimate
            outcome_penalty = self.process_reward_outcome_coef * outcome_error
            if self.process_reward_mode == "mi_outcome":
                raw_reward = mi_component - outcome_penalty
            elif self.process_reward_mode == "mi_only":
                raw_reward = mi_component
            elif self.process_reward_mode == "positive_mi":
                raw_reward = torch.relu(mi_component)
            elif self.process_reward_mode == "centered_mi":
                raw_reward = mi_component - mi_component.mean()
            elif self.process_reward_mode == "residual_mi":
                raw_reward = mi_component
            elif self.process_reward_mode == "positive_residual_mi":
                raw_reward = torch.relu(mi_component)
            elif self.process_reward_mode == "centered_residual_mi":
                raw_reward = mi_component - mi_component.mean()
            elif self.process_reward_mode == "residual_mi_outcome":
                raw_reward = mi_component - outcome_penalty
            else:
                raw_reward = torch.zeros_like(mi_component)
            process_reward_unclipped = self.process_reward_coef * raw_reward
            warmup_active = int(total_steps) < int(self.process_reward_warmup_steps)
            if (not self.use_process_reward) or warmup_active:
                process_reward = torch.zeros_like(process_reward_unclipped)
            else:
                process_reward = process_reward_unclipped
            if self.process_reward_clip > 0:
                process_reward = torch.clamp(process_reward, -self.process_reward_clip, self.process_reward_clip)
            process_reward_np = process_reward.detach().cpu().numpy()
            process_reward_mi_component_mean = float(
                (self.process_reward_coef * mi_component).detach().mean().cpu().item()
            )
            process_reward_outcome_penalty_mean = float(
                (self.process_reward_coef * outcome_penalty).detach().mean().cpu().item()
            )
            process_reward_unclipped_mean = float(process_reward_unclipped.detach().mean().cpu().item())
            process_mi_positive_frac = float((mi_estimate > 0.0).float().mean().detach().cpu().item())
            process_residual_mi_positive_frac = float(
                (residual_mi_estimate > 0.0).float().mean().detach().cpu().item()
            )
            outcome_residual_reward_np = np.zeros(len(valid), dtype=np.float32)
            outcome_residual_reward_active = 0.0
            outcome_residual_reward_unclipped_mean = 0.0
            if outcome_residual_terms is not None:
                outcome_gain_for_reward = outcome_residual_terms["gain"].detach()
                outcome_residual_reward_unclipped = self.outcome_residual_reward_coef * outcome_gain_for_reward
                if (
                    self.outcome_residual_injection != "none"
                    and self.outcome_residual_reward_coef != 0.0
                    and self.use_process_reward
                ):
                    outcome_residual_reward = outcome_residual_reward_unclipped
                    outcome_residual_reward_active = 1.0
                else:
                    outcome_residual_reward = torch.zeros_like(outcome_residual_reward_unclipped)
                if self.outcome_residual_reward_clip > 0:
                    outcome_residual_reward = torch.clamp(
                        outcome_residual_reward,
                        -self.outcome_residual_reward_clip,
                        self.outcome_residual_reward_clip,
                    )
                outcome_residual_reward_np = outcome_residual_reward.detach().cpu().numpy().astype(np.float32)
                outcome_residual_reward_unclipped_mean = float(
                    outcome_residual_reward_unclipped.detach().mean().cpu().item()
                )
            topology_role_reward_np = np.zeros(len(valid), dtype=np.float32)
            topology_role_reward_active = 0.0
            topology_role_reward_unclipped_mean = 0.0
            if topology_role_terms is not None:
                topology_gain_for_reward = torch.relu(topology_role_terms["residual_gain"].detach())
                topology_role_reward_unclipped = self.topology_role_reward_coef * topology_gain_for_reward
                if (
                    self.topology_role_injection != "none"
                    and self.topology_role_reward_coef != 0.0
                    and self.use_process_reward
                ):
                    topology_role_reward = topology_role_reward_unclipped
                    topology_role_reward_active = 1.0
                else:
                    topology_role_reward = torch.zeros_like(topology_role_reward_unclipped)
                if self.topology_role_reward_clip > 0:
                    topology_role_reward = torch.clamp(
                        topology_role_reward,
                        0.0,
                        self.topology_role_reward_clip,
                    )
                topology_role_reward_np = topology_role_reward.detach().cpu().numpy().astype(np.float32)
                topology_role_reward_unclipped_mean = float(
                    topology_role_reward_unclipped.detach().mean().cpu().item()
                )
            topology_potential_reward_np, topology_potential_metrics = self.topology_potential_shaper.rewards(
                valid,
                total_steps=total_steps,
            )
            transition_log_q_mean = 0.0
            transition_log_p_mean = 0.0
            transition_log_context_mean = 0.0
            transition_mi_mean = 0.0
            transition_mi_positive_frac = 0.0
            transition_residual_mi_mean = 0.0
            transition_residual_mi_positive_frac = 0.0
            transition_reward_active = 0.0
            transition_reward_unclipped_mean = 0.0
            transition_reward_warmup_active = 0.0
            transition_reward_np = np.zeros(0, dtype=np.float32)
            if (
                transition_logits_for_reward is not None
                and transition_prior_logits_for_reward is not None
                and transition_labels_t is not None
            ):
                transition_log_q = F.log_softmax(transition_logits_for_reward, dim=-1)[
                    torch.arange(transition_labels_t.shape[0], device=self.device),
                    transition_labels_t,
                ]
                transition_log_p = F.log_softmax(transition_prior_logits_for_reward, dim=-1)[
                    torch.arange(transition_labels_t.shape[0], device=self.device),
                    transition_labels_t,
                ]
                transition_mi = transition_log_q - transition_log_p
                if transition_context_logits_for_reward is not None:
                    transition_log_context = F.log_softmax(transition_context_logits_for_reward, dim=-1)[
                        torch.arange(transition_labels_t.shape[0], device=self.device),
                        transition_labels_t,
                    ]
                else:
                    transition_log_context = transition_log_p
                transition_residual_baseline = torch.maximum(transition_log_p, transition_log_context)
                transition_residual_mi = transition_log_q - transition_residual_baseline
                transition_warmup_active = int(total_steps) < int(self.transition_skill_reward_warmup_steps)
                transition_reward, transition_reward_metrics = self.intrinsic_rewards.transition_rewards(
                    transition_residual_mi,
                    coef=self.transition_skill_reward_coef,
                    clip=self.transition_skill_reward_clip,
                    warmup_active=transition_warmup_active,
                    enabled=self.use_process_reward,
                )
                transition_reward_np = transition_reward.detach().cpu().numpy().astype(np.float32)
                transition_log_q_mean = float(transition_log_q.detach().mean().cpu().item())
                transition_log_p_mean = float(transition_log_p.detach().mean().cpu().item())
                transition_log_context_mean = float(transition_log_context.detach().mean().cpu().item())
                transition_mi_mean = float(transition_mi.detach().mean().cpu().item())
                transition_mi_positive_frac = float((transition_mi > 0.0).float().mean().detach().cpu().item())
                transition_residual_mi_mean = float(transition_residual_mi.detach().mean().cpu().item())
                transition_residual_mi_positive_frac = float(
                    (transition_residual_mi > 0.0).float().mean().detach().cpu().item()
                )
                transition_reward_active = float(transition_reward_metrics["active"])
                transition_reward_unclipped_mean = float(transition_reward_metrics["unclipped_mean"])
                transition_reward_warmup_active = float(transition_reward_metrics["warmup_active"])

        posterior_acc_for_gate = float(posterior_acc.detach().cpu().item())
        duration_only_acc_for_gate = self.duration_only_accuracy(labels, durations_np)
        shortcut_acc_for_gate = 0.0
        if shortcut_terms is not None:
            shortcut_acc_for_gate = float(shortcut_terms["max_shortcut_acc"].detach().cpu().item())
        semantic_shortcut_hard_stop_triggered = 0.0
        semantic_shortcut_hard_stop_applied = 0.0
        semantic_shortcut_hard_stop_reason_code = 0.0
        semantic_shortcut_hard_stop_score = posterior_acc_for_gate - duration_only_acc_for_gate
        if not self.semantic_shortcut_hard_stop_enabled:
            semantic_shortcut_hard_stop_reason_code = 1.0
        elif len(valid) < self.semantic_shortcut_hard_stop_min_segments:
            semantic_shortcut_hard_stop_reason_code = 2.0
        elif semantic_shortcut_hard_stop_score <= self.semantic_shortcut_hard_stop_margin:
            semantic_shortcut_hard_stop_triggered = 1.0
            semantic_shortcut_hard_stop_reason_code = 3.0
            if self.process_reward_injection != "none" and process_reward_np.size:
                process_reward_np = np.zeros_like(process_reward_np)
                semantic_shortcut_hard_stop_applied = 1.0
                if self.semantic_shortcut_hard_stop_raise:
                    raise RuntimeError(
                        "Semantic shortcut hard-stop: duration-only baseline is not worse than "
                        f"segment posterior (posterior_acc={posterior_acc_for_gate:.4f}, "
                        f"duration_only_acc={duration_only_acc_for_gate:.4f})."
                    )
        segment_high_gate = self.intrinsic_rewards.segment_quality_gate(
            enabled=self.use_process_reward and self.process_reward_injection in {"high_only", "high_and_low"},
            warmup_active=int(total_steps) < int(self.process_reward_warmup_steps),
            segment_count=len(valid),
            posterior_acc=posterior_acc_for_gate,
            shortcut_acc=shortcut_acc_for_gate,
            residual_mi_mean=float(residual_mi_estimate.detach().mean().cpu().item()),
        )
        high_process_rewards, low_process_rewards = self.intrinsic_rewards.split_segment_rewards(
            process_reward_np,
            injection=self.process_reward_injection,
            high_gate=segment_high_gate,
            low_gate_active=self.use_process_reward,
        )
        high_outcome_residual_rewards, low_outcome_residual_rewards = self.intrinsic_rewards.split_segment_rewards(
            outcome_residual_reward_np,
            injection=self.outcome_residual_injection,
            high_gate=None,
            low_gate_active=self.use_process_reward,
        )
        high_topology_role_rewards, low_topology_role_rewards = self.intrinsic_rewards.split_segment_rewards(
            topology_role_reward_np,
            injection=self.topology_role_injection,
            high_gate=None,
            low_gate_active=self.use_process_reward,
        )
        high_topology_potential_rewards, low_topology_potential_rewards = self.intrinsic_rewards.split_segment_rewards(
            topology_potential_reward_np,
            injection=self.topology_potential_injection,
            high_gate=None,
            low_gate_active=bool(topology_potential_metrics.get("topology_potential_active", 0.0) > 0.0),
        )
        topology_potential_metrics["topology_potential_high_mean"] = (
            float(np.mean(high_topology_potential_rewards))
            if high_topology_potential_rewards.size
            else 0.0
        )
        topology_potential_metrics["topology_potential_low_mean"] = (
            float(np.mean(low_topology_potential_rewards))
            if low_topology_potential_rewards.size
            else 0.0
        )
        # P2-lite recovery-window contribution credit (compute-on / reward-off by
        # default).  Signed potential shaping; per-agent attribution via phi_i.
        high_p2_rewards = np.zeros(len(valid), dtype=np.float32)
        low_p2_rewards = np.zeros(len(valid), dtype=np.float32)
        p2_metrics = empty_p2_metrics()
        if self.p2_compute_on:
            p2_shapings = [
                compute_segment_shaping(
                    seg,
                    self.p2_computer,
                    self.p2_cfg,
                    near_disconnect_bh_frac=self.p2_near_disconnect_bh_frac,
                )
                for seg in valid
            ]
            # owner_credit / recovery_flags are aligned to the AVAILABLE shapings so
            # their length matches aggregate_p2_metrics' internal `valid` filter;
            # otherwise the length checks there silently drop both arrays.
            owner_credit = []
            recovery_flags = []
            bh_threshold = float(self.p2_cfg.bh_threshold)
            for seg, sh in zip(valid, p2_shapings):
                if not sh.available:
                    continue
                aid = int(getattr(seg, "agent_id", 0))
                owner_credit.append(float(sh.f_i[aid]) if sh.f_i.size > aid else 0.0)
                # Recovery event: backhaul started broken (near/full disconnect) and
                # ended reconnected.  Drives p2_corr_phi_recovery_event (Pre-check 2).
                started_broken = float(sh.phi_start.bh_frac) < float(self.p2_near_disconnect_bh_frac)
                ended_connected = float(sh.phi_end.bh_frac) >= bh_threshold
                recovery_flags.append(1.0 if (started_broken and ended_connected) else 0.0)
            p2_metrics = aggregate_p2_metrics(
                p2_shapings,
                owner_credit=owner_credit,
                recovery_flags=recovery_flags,
            )
            if self.p2_reward_on:
                clip = self.p2_reward_clip
                for idx, (seg, sh) in enumerate(zip(valid, p2_shapings)):
                    if not sh.available:
                        continue
                    aid = int(getattr(seg, "agent_id", 0))
                    if self.p2_reward_level == "high_per_agent":
                        val = float(sh.f_i[aid]) if sh.f_i.size > aid else 0.0
                    else:
                        val = float(sh.f_team)
                    val = self.p2_reward_coef * val
                    if clip > 0.0:
                        val = float(np.clip(val, -clip, clip))
                    if self.p2_reward_level == "low_only":
                        low_v = float(sh.f_i[aid]) if sh.f_i.size > aid else 0.0
                        low_v = self.p2_reward_coef * low_v
                        if self.p2_low_positive_only:
                            low_v = max(low_v, 0.0)
                        if clip > 0.0:
                            low_v = float(np.clip(low_v, -clip, clip))
                        low_p2_rewards[idx] = low_v
                    else:
                        high_p2_rewards[idx] = val

        combined_high_rewards = (
            high_process_rewards
            + high_outcome_residual_rewards
            + high_topology_role_rewards
            + high_topology_potential_rewards
            + high_p2_rewards
        )
        combined_low_rewards = (
            low_process_rewards
            + low_outcome_residual_rewards
            + low_topology_role_rewards
            + low_topology_potential_rewards
            + low_p2_rewards
        )

        for rollout_idx, agent_id, reward_value in zip(
            transition_rollout_indices,
            transition_agent_ids,
            transition_reward_np,
        ):
            if 0 <= int(rollout_idx) < len(rollout.rewards) and 0 <= int(agent_id) < self.n_agents:
                rollout.rewards[int(rollout_idx)][int(agent_id)] += float(reward_value)

        if isinstance(effect_micro_rewards, dict):
            micro_indices = effect_micro_rewards.get("rollout_indices", [])
            micro_agents = np.asarray(effect_micro_rewards.get("agent_ids", []), dtype=np.int64).reshape(-1)
            micro_rewards = np.asarray(effect_micro_rewards.get("rewards", []), dtype=np.float32).reshape(-1)
            for indices, agent_id, reward_value in zip(micro_indices, micro_agents, micro_rewards):
                step_indices = np.asarray(indices, dtype=np.int64).reshape(-1)
                if step_indices.size <= 0 or not np.isfinite(float(reward_value)):
                    continue
                if not (0 <= int(agent_id) < self.n_agents):
                    continue
                per_step = float(reward_value) / float(step_indices.size)
                for rollout_idx in step_indices:
                    if 0 <= int(rollout_idx) < len(rollout.rewards):
                        rollout.rewards[int(rollout_idx)][int(agent_id)] += per_step

        for segment, reward_value in zip(valid, combined_low_rewards):
            if segment.length <= 0:
                continue
            per_step = float(reward_value) / float(segment.length)
            for rollout_idx in segment.rollout_indices:
                if 0 <= rollout_idx < len(rollout.rewards):
                    rollout.rewards[rollout_idx][segment.agent_id] += per_step

        high_metrics = self.update_high_from_segments(
            valid,
            combined_high_rewards,
            total_steps=total_steps,
        )

        lengths = np.asarray([s.length for s in valid], dtype=np.float32)
        reward_sums = np.asarray([np.sum(s.rewards) for s in valid], dtype=np.float32)
        skill_entropy, skill_max_frac = self._usage_stats(labels, self.n_skills)
        duration_entropy, duration_max_frac = self._usage_stats(durations_np, len(self.duration_candidates))
        team_code_entropy, team_code_max_frac = self._usage_stats(team_codes_np, self.bridge.num_team_codes)
        posterior_acc_value = float(posterior_acc.detach().cpu().item())
        duration_only_acc = duration_only_acc_for_gate
        length_only_acc = self.binned_scalar_accuracy(labels, lengths)
        reward_sum_only_acc = self.binned_scalar_accuracy(labels, reward_sums)
        if shortcut_terms is not None:
            process_shortcut_loss_value = float(shortcut_loss.detach().cpu().item())
            process_shortcut_context_loss_value = float(context_shortcut_loss.detach().cpu().item())
            process_shortcut_margin_loss_value = float(shortcut_margin_loss.detach().cpu().item())
            process_shortcut_duration_acc = float(shortcut_terms["duration_acc"].detach().cpu().item())
            process_shortcut_length_acc = float(shortcut_terms["length_acc"].detach().cpu().item())
            process_shortcut_reward_sum_acc = float(shortcut_terms["reward_sum_acc"].detach().cpu().item())
            process_shortcut_context_acc = float(shortcut_terms["context_acc"].detach().cpu().item())
            process_shortcut_max_acc = float(shortcut_terms["max_shortcut_acc"].detach().cpu().item())
            process_residual_log_shortcut_mean = float(shortcut_log_q.detach().mean().cpu().item())
            process_residual_log_context_mean = float(context_log_q.detach().mean().cpu().item())
        else:
            process_shortcut_loss_value = 0.0
            process_shortcut_context_loss_value = 0.0
            process_shortcut_margin_loss_value = 0.0
            process_shortcut_duration_acc = 0.0
            process_shortcut_length_acc = 0.0
            process_shortcut_reward_sum_acc = 0.0
            process_shortcut_context_acc = 0.0
            process_shortcut_max_acc = 0.0
            process_residual_log_shortcut_mean = float(log_p.detach().mean().cpu().item())
            process_residual_log_context_mean = float(log_p.detach().mean().cpu().item())
        cooperation_credit_metrics = aggregate_cooperation_credit(valid)
        lifetime_metrics = self._lifetime_diagnostics(valid, durations_np, reward_sums)
        outcome_residual_metrics = {
            "outcome_residual_full_loss": 0.0,
            "outcome_residual_base_loss": 0.0,
            "outcome_residual_total_loss": float(outcome_residual_loss.detach().cpu().item()),
            "outcome_residual_gain_mean": 0.0,
            "outcome_residual_gain_positive_frac": 0.0,
            "outcome_residual_available_mean": float(np.mean(future_outcome_masks > 0.0))
            if future_outcome_masks.size
            else 0.0,
            "outcome_residual_target_abs_mean": float(
                np.mean(np.abs(raw_future_outcomes[future_outcome_masks > 0.0]))
            )
            if np.any(future_outcome_masks > 0.0)
            else 0.0,
            "outcome_residual_reward_mean": float(np.mean(outcome_residual_reward_np))
            if outcome_residual_reward_np.size
            else 0.0,
            "outcome_residual_reward_active": float(outcome_residual_reward_active),
            "outcome_residual_reward_unclipped_mean": float(outcome_residual_reward_unclipped_mean),
            "outcome_residual_skill_gain_std": 0.0,
            "outcome_residual_team_gain_std": 0.0,
            "outcome_residual_duration_gain_std": 0.0,
        }
        for field_name in FUTURE_COOPERATION_OUTCOME_FIELDS:
            outcome_residual_metrics[f"outcome_residual_gain_{field_name}"] = 0.0
        if outcome_residual_terms is not None:
            gain_np = outcome_residual_terms["gain"].detach().cpu().numpy().astype(np.float64)
            finite_gain = gain_np[np.isfinite(gain_np)]
            field_gain_np = outcome_residual_terms["field_gain"].detach().cpu().numpy().astype(np.float64)
            if finite_gain.size:
                skill_gain = self._group_mean_summary(labels, gain_np, self.n_skills)
                team_gain = self._group_mean_summary(team_codes_np, gain_np, self.bridge.num_team_codes)
                duration_gain = self._group_mean_summary(durations_np, gain_np, len(self.duration_candidates))
                outcome_residual_metrics.update(
                    {
                        "outcome_residual_full_loss": float(
                            outcome_residual_terms["full_loss"].detach().cpu().item()
                        ),
                        "outcome_residual_base_loss": float(
                            outcome_residual_terms["baseline_loss"].detach().cpu().item()
                        ),
                        "outcome_residual_gain_mean": float(np.mean(finite_gain)),
                        "outcome_residual_gain_positive_frac": float(np.mean(finite_gain > 0.0)),
                        "outcome_residual_skill_gain_std": float(skill_gain["std"]),
                        "outcome_residual_team_gain_std": float(team_gain["std"]),
                        "outcome_residual_duration_gain_std": float(duration_gain["std"]),
                    }
                )
            for field_idx, field_name in enumerate(FUTURE_COOPERATION_OUTCOME_FIELDS):
                if field_idx < field_gain_np.size and np.isfinite(field_gain_np[field_idx]):
                    outcome_residual_metrics[f"outcome_residual_gain_{field_name}"] = float(field_gain_np[field_idx])
        topology_role_metrics = empty_topology_role_metrics()
        topology_role_metrics.update(
            {
                "topology_role_samples": float(len(valid)),
                "topology_role_available_frac": float(np.mean(topology_role_masks > 0.0))
                if topology_role_masks.size
                else 0.0,
                "topology_role_loss": float(topology_role_loss.detach().cpu().item()),
                "topology_role_reward_mean": float(np.mean(topology_role_reward_np))
                if topology_role_reward_np.size
                else 0.0,
                "topology_role_reward_active": float(topology_role_reward_active),
                "topology_role_reward_unclipped_mean": float(topology_role_reward_unclipped_mean),
            }
        )
        available_role = topology_role_masks > 0.0
        if np.any(available_role):
            available_labels = topology_role_labels[available_role]
            for role_idx, role_name in enumerate(TOPOLOGY_ROLE_NAMES):
                topology_role_metrics[f"topology_role_frac_{role_name}"] = float(
                    np.mean(available_labels == role_idx)
                )
            feature_means = np.mean(topology_features[available_role], axis=0)
            for field_idx, field_name in enumerate(TOPOLOGY_ROLE_FIELDS):
                if field_idx < feature_means.shape[0] and np.isfinite(feature_means[field_idx]):
                    topology_role_metrics[f"topology_{field_name}_mean"] = float(feature_means[field_idx])
            topology_role_metrics["topology_role_z_mi"] = self._joint_mi_norm(
                labels[available_role],
                topology_role_labels[available_role],
                self.n_skills,
                len(TOPOLOGY_ROLE_NAMES),
            )
            topology_role_metrics["topology_role_g_mi"] = self._joint_mi_norm(
                team_codes_np[available_role],
                topology_role_labels[available_role],
                self.bridge.num_team_codes,
                len(TOPOLOGY_ROLE_NAMES),
            )
        if topology_role_terms is not None:
            topology_gain_np = topology_role_terms["residual_gain"].detach().cpu().numpy().astype(np.float64)
            topology_gain_np = topology_gain_np[available_role & np.isfinite(topology_gain_np)]
            topology_role_metrics.update(
                {
                    "topology_role_full_loss": float(
                        topology_role_terms["full_loss"].detach().cpu().item()
                    ),
                    "topology_role_shortcut_loss": float(
                        topology_role_terms["shortcut_loss"].detach().cpu().item()
                    ),
                    "topology_role_acc": float(topology_role_terms["full_acc"].detach().cpu().item()),
                    "topology_role_shortcut_acc": float(
                        topology_role_terms["shortcut_acc"].detach().cpu().item()
                    ),
                    "topology_role_resid_gain_mean": float(np.mean(topology_gain_np))
                    if topology_gain_np.size
                    else 0.0,
                    "topology_role_resid_gain_positive_frac": float(
                        topology_role_terms["residual_gain_positive_frac"].detach().cpu().item()
                    ),
                }
            )
        return {
            "process_segments": float(len(valid)),
            "process_loss": float(loss.detach().cpu().item()),
            "process_outcome_loss": float(outcome_loss.detach().cpu().item()),
            "process_contrastive_loss": float(contrastive_loss.detach().cpu().item()),
            "process_prior_loss": float(prior_loss.detach().cpu().item()),
            "process_posterior_acc": posterior_acc_value,
            "process_mi_estimate_mean": float(mi_estimate.detach().mean().cpu().item()),
            "process_residual_mi_mean": float(residual_mi_estimate.detach().mean().cpu().item()),
            "process_residual_mi_positive_frac": process_residual_mi_positive_frac,
            "process_residual_log_shortcut_mean": process_residual_log_shortcut_mean,
            "process_residual_log_context_mean": process_residual_log_context_mean,
            "process_log_q_mean": float(log_q.detach().mean().cpu().item()),
            "process_log_p_mean": float(log_p.detach().mean().cpu().item()),
            "process_shortcut_loss": process_shortcut_loss_value,
            "process_shortcut_context_loss": process_shortcut_context_loss_value,
            "process_shortcut_margin_loss": process_shortcut_margin_loss_value,
            "process_reward_warmup_active": float(int(total_steps) < int(self.process_reward_warmup_steps)),
            "transition_skill_samples": float(transition_sample_count),
            "transition_skill_available_samples": float(transition_available_count),
            "transition_skill_loss": float(transition_loss.detach().cpu().item()),
            "transition_skill_prior_loss": float(transition_prior_loss.detach().cpu().item()),
            "transition_skill_context_loss": float(transition_context_loss.detach().cpu().item()),
            "transition_skill_acc": float(transition_acc.detach().cpu().item()),
            "transition_skill_context_acc": float(transition_context_acc.detach().cpu().item()),
            "transition_skill_mi_mean": transition_mi_mean,
            "transition_skill_mi_positive_frac": transition_mi_positive_frac,
            "transition_skill_residual_mi_mean": transition_residual_mi_mean,
            "transition_skill_residual_mi_positive_frac": transition_residual_mi_positive_frac,
            "transition_skill_reward_mean": float(np.mean(transition_reward_np)) if transition_reward_np.size else 0.0,
            "transition_skill_reward_active": float(transition_reward_active),
            "transition_skill_log_q_mean": transition_log_q_mean,
            "transition_skill_log_p_mean": transition_log_p_mean,
            "transition_skill_log_context_mean": transition_log_context_mean,
            "transition_skill_reward_unclipped_mean": transition_reward_unclipped_mean,
            "transition_skill_reward_warmup_active": transition_reward_warmup_active,
            **segment_high_gate.metrics("intrinsic_segment_high_gate"),
            "process_shortcut_duration_acc": process_shortcut_duration_acc,
            "process_shortcut_length_acc": process_shortcut_length_acc,
            "process_shortcut_reward_sum_acc": process_shortcut_reward_sum_acc,
            "process_shortcut_context_acc": process_shortcut_context_acc,
            "process_shortcut_max_acc": process_shortcut_max_acc,
            "posterior_acc_minus_shortcut_max": posterior_acc_value - process_shortcut_max_acc,
            "posterior_acc_minus_context_shortcut": posterior_acc_value - process_shortcut_context_acc,
            "process_reward_mi_component_mean": process_reward_mi_component_mean,
            "process_reward_outcome_penalty_mean": process_reward_outcome_penalty_mean,
            "process_reward_unclipped_mean": process_reward_unclipped_mean,
            "process_mi_positive_frac": process_mi_positive_frac,
            "process_reward_mean": float(np.mean(process_reward_np)),
            "process_reward_high_mean": float(np.mean(high_process_rewards)),
            "process_reward_low_mean": float(np.mean(low_process_rewards)),
            "semantic_shortcut_hard_stop_triggered": semantic_shortcut_hard_stop_triggered,
            "semantic_shortcut_hard_stop_applied": semantic_shortcut_hard_stop_applied,
            "semantic_shortcut_hard_stop_score": semantic_shortcut_hard_stop_score,
            "semantic_shortcut_hard_stop_reason_code": semantic_shortcut_hard_stop_reason_code,
            "outcome_available_mean": float(np.mean(outcome_masks)),
            "outcome_abs_mean": float(np.mean(np.abs(raw_outcomes[outcome_masks > 0.0]))) if np.any(outcome_masks > 0.0) else 0.0,
            **outcome_residual_metrics,
            **topology_role_metrics,
            **topology_potential_metrics,
            **p2_metrics,
            **effect_metrics,
            "duration_only_accuracy": duration_only_acc,
            "length_only_accuracy": length_only_acc,
            "reward_sum_only_accuracy": reward_sum_only_acc,
            "posterior_acc_minus_duration_only": posterior_acc_value - duration_only_acc,
            "posterior_acc_minus_length_only": posterior_acc_value - length_only_acc,
            "posterior_acc_minus_reward_sum_only": posterior_acc_value - reward_sum_only_acc,
            "segment_length_mean": float(np.mean(lengths)),
            "segment_length_max": float(np.max(lengths)),
            "duration_target_mean": float(np.mean([s.duration_target for s in valid])),
            "skill_switch_rate": float(np.mean([float(s.switched) for s in valid])),
            "initial_assignment_rate": float(np.mean([float(s.initial_assignment) for s in valid])),
            "skill_usage_entropy": skill_entropy,
            "skill_usage_max_frac": skill_max_frac,
            "duration_usage_entropy": duration_entropy,
            "duration_usage_max_frac": duration_max_frac,
            "skill_duration_mi": self._joint_mi_norm(labels, durations_np, self.n_skills, len(self.duration_candidates)),
            "team_code_usage_entropy": team_code_entropy,
            "team_code_usage_max_frac": team_code_max_frac,
            "g_usage_entropy": team_code_entropy,
            "g_usage_max_frac": team_code_max_frac,
            "team_code_skill_mi": self._joint_mi_norm(team_codes_np, labels, self.bridge.num_team_codes, self.n_skills),
            "team_code_duration_mi": self._joint_mi_norm(
                team_codes_np,
                durations_np,
                self.bridge.num_team_codes,
                len(self.duration_candidates),
            ),
            "team_code_edit_mi": self._joint_mi_norm(
                team_codes_np,
                np.asarray([int(s.switched) for s in valid], dtype=np.int64),
                self.bridge.num_team_codes,
                2,
            ),
            **lifetime_metrics,
            **g_intervention_metrics,
            **cooperation_credit_metrics,
            **high_metrics,
        }

    def _segment_state(self, segment: Segment) -> np.ndarray:
        if segment.high_state is not None:
            return self._fit_vector(segment.high_state, self.state_dim)
        joint = self._segment_joint_obs(segment)
        return self._state_array(None, joint)

    def _segment_joint_obs(self, segment: Segment) -> np.ndarray:
        if segment.high_joint_obs is not None:
            return self._joint_obs_array(segment.high_joint_obs)
        joint = np.zeros((self.n_agents, self.obs_dim), dtype=np.float32)
        joint[segment.agent_id] = self._fit_vector(segment.high_obs, self.obs_dim)
        return joint

    def _segment_end_joint_obs(self, segment: Segment) -> np.ndarray:
        if segment.end_joint_obs is not None:
            return self._joint_obs_array(segment.end_joint_obs)
        joint = self._segment_joint_obs(segment)
        if segment.end_obs is not None:
            joint[segment.agent_id] = self._fit_vector(segment.end_obs, self.obs_dim)
        return joint

    def _discounted_segment_return(self, segment: Segment) -> float:
        rewards = np.asarray(segment.rewards, dtype=np.float32)
        if rewards.size == 0:
            return 0.0
        if not self.use_smdp_discounted_high_return:
            return float(np.sum(rewards))
        discounts = np.power(float(self.gamma), np.arange(rewards.size, dtype=np.float32))
        return float(np.sum(discounts * rewards))

    def _segment_discount_factor(self, segment: Segment) -> float:
        if not self.use_smdp_discounted_high_return:
            return 1.0
        return float(float(self.gamma) ** max(int(segment.length), 0))

    def _bootstrap_high_values(self, segments: list[Segment]) -> np.ndarray:
        values = np.zeros(len(segments), dtype=np.float32)
        if not self.use_smdp_bootstrap or not segments:
            return values

        bootstrap_indices = [
            idx
            for idx, segment in enumerate(segments)
            if not segment.terminal and segment.end_obs is not None and segment.length > 0
        ]
        if not bootstrap_indices:
            return values

        states = torch.as_tensor(
            np.asarray(
                [
                    self._state_array(segments[idx].end_state, self._segment_end_joint_obs(segments[idx]))
                    for idx in bootstrap_indices
                ],
                dtype=np.float32,
            ),
            device=self.device,
        )
        joint_obs = torch.as_tensor(
            np.asarray(
                [self._segment_end_joint_obs(segments[idx]) for idx in bootstrap_indices],
                dtype=np.float32,
            ),
            device=self.device,
        )
        high_obs = torch.as_tensor(
            np.asarray(
                [self._fit_vector(segments[idx].end_obs, self.obs_dim) for idx in bootstrap_indices],
                dtype=np.float32,
            ),
            device=self.device,
        )
        prev_skills = torch.as_tensor(
            [segments[idx].skill for idx in bootstrap_indices],
            dtype=torch.long,
            device=self.device,
        )
        ages = torch.as_tensor(
            [segments[idx].skill_age_prev + segments[idx].length for idx in bootstrap_indices],
            dtype=torch.float32,
            device=self.device,
        )
        team_codes = torch.as_tensor(
            [segments[idx].team_code for idx in bootstrap_indices],
            dtype=torch.long,
            device=self.device,
        )
        skills = torch.as_tensor(
            [segments[idx].skill for idx in bootstrap_indices],
            dtype=torch.long,
            device=self.device,
        )
        durations = torch.as_tensor(
            [segments[idx].duration_idx for idx in bootstrap_indices],
            dtype=torch.long,
            device=self.device,
        )
        with torch.no_grad():
            compact, _cd_loss, _cmi_loss, _weights, _aggregation_entropy = self.compact(states, joint_obs)
            _team_code, team_vector, _team_logp, _team_entropy, _team_logits = self.bridge(
                compact,
                forced_team_code=team_codes,
            )
            _logp, _entropy, bootstrap_values = self.high.evaluate(
                high_obs,
                prev_skills,
                ages,
                compact,
                team_vector,
                skills,
                durations,
            )
            if self.high_value_norm is not None:
                bootstrap_values = self.high_value_norm.denormalize_tensor(bootstrap_values)
        values[np.asarray(bootstrap_indices, dtype=np.int64)] = bootstrap_values.detach().cpu().numpy()
        return values

    def update_high_from_segments(
        self,
        segments: list[Segment],
        process_rewards: np.ndarray,
        total_steps: int = 0,
    ) -> dict[str, float]:
        if not segments:
            return {
                "high_loss": 0.0,
                "high_policy_loss": 0.0,
                "high_value_loss": 0.0,
                "high_entropy_loss": 0.0,
                "high_aux_loss": 0.0,
                "high_entropy": 0.0,
                "high_return_mean": 0.0,
                "high_env_return_mean": 0.0,
                "high_bootstrap_value_mean": 0.0,
                "high_bootstrap_contribution_mean": 0.0,
                "high_smdp_discount_mean": 0.0,
                "high_value_norm_mean": float(self.high_value_norm.mean) if self.high_value_norm is not None else 0.0,
                "high_value_norm_std": float(np.sqrt(self.high_value_norm.var)) if self.high_value_norm is not None else 0.0,
                "high_grad_norm": 0.0,
                **empty_g_info_metrics(),
            }

        states = torch.as_tensor(
            np.asarray([self._segment_state(s) for s in segments], dtype=np.float32),
            device=self.device,
        )
        joint_obs = torch.as_tensor(
            np.asarray([self._segment_joint_obs(s) for s in segments], dtype=np.float32),
            device=self.device,
        )
        high_obs = torch.as_tensor(
            np.asarray([s.high_obs for s in segments], dtype=np.float32),
            device=self.device,
        )
        prev_skills = torch.as_tensor([s.prev_skill for s in segments], dtype=torch.long, device=self.device)
        ages = torch.as_tensor([s.skill_age_prev for s in segments], dtype=torch.float32, device=self.device)
        team_codes = torch.as_tensor([s.team_code for s in segments], dtype=torch.long, device=self.device)
        skills = torch.as_tensor([s.skill for s in segments], dtype=torch.long, device=self.device)
        durations = torch.as_tensor([s.duration_idx for s in segments], dtype=torch.long, device=self.device)
        old_logp = torch.as_tensor([s.high_logp for s in segments], dtype=torch.float32, device=self.device)
        old_value = torch.as_tensor([s.high_value for s in segments], dtype=torch.float32, device=self.device)

        compact, cd_loss, cmi_loss, _weights, aggregation_entropy = self.compact(states, joint_obs)
        _team_code, team_vector, team_logp, team_entropy, _team_logits = self.bridge(
            compact,
            forced_team_code=team_codes,
        )
        logp_high, entropy_high, values = self.high.evaluate(
            high_obs,
            prev_skills,
            ages,
            compact,
            team_vector,
            skills,
            durations,
        )
        team_weights = torch.as_tensor(
            [s.team_logp_weight for s in segments],
            dtype=torch.float32,
            device=self.device,
        )
        logp = logp_high + team_logp * team_weights
        entropy = entropy_high + team_entropy * team_weights

        env_returns_np = np.asarray([self._discounted_segment_return(s) for s in segments], dtype=np.float32)
        bootstrap_values_np = self._bootstrap_high_values(segments)
        smdp_discounts_np = np.asarray([self._segment_discount_factor(s) for s in segments], dtype=np.float32)
        renewal_penalties_np = np.asarray([s.renewal_penalty for s in segments], dtype=np.float32)
        returns_np = (
            env_returns_np
            + np.asarray(process_rewards, dtype=np.float32)
            - renewal_penalties_np
            + self.smdp_bootstrap_coef * smdp_discounts_np * bootstrap_values_np
        ).astype(np.float32)
        bootstrap_contrib_np = (
            self.smdp_bootstrap_coef * smdp_discounts_np * bootstrap_values_np
        ).astype(np.float32)
        returns = torch.as_tensor(returns_np, dtype=torch.float32, device=self.device)
        advantages = returns - old_value
        if advantages.numel() > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
        value_targets = returns
        if self.high_value_norm is not None:
            self.high_value_norm.update(returns_np)
            value_targets = self.high_value_norm.normalize_tensor(returns)

        ratio = torch.exp(logp - old_logp)
        policy_loss = -torch.min(
            ratio * advantages,
            torch.clamp(ratio, 1.0 - self.high_clip, 1.0 + self.high_clip) * advantages,
        ).mean()
        value_loss = F.mse_loss(values, value_targets)
        entropy_loss = -self.high_entropy_coef * entropy.mean()
        aux_loss = self.opt_cd_coef * cd_loss + self.opt_cmi_coef * cmi_loss
        if self.g_info_objective is not None:
            g_info_loss, g_info_metrics = self.g_info_objective(
                high_policy=self.high,
                bridge=self.bridge,
                high_obs=high_obs,
                prev_skills=prev_skills,
                ages=ages,
                compact=compact,
                total_steps=total_steps,
            )
        else:
            g_info_loss = torch.zeros((), device=self.device)
            g_info_metrics = empty_g_info_metrics()
        loss = (
            policy_loss
            + 0.5 * value_loss
            + entropy_loss
            + aux_loss
            + g_info_loss
        )

        self.high_opt.zero_grad()
        loss.backward()
        high_grad_norm = torch.zeros((), device=self.device)
        if self.high_max_grad_norm > 0.0:
            high_params = [
                param
                for group in self.high_opt.param_groups
                for param in group["params"]
                if param.grad is not None
            ]
            if high_params:
                high_grad_norm = torch.nn.utils.clip_grad_norm_(high_params, self.high_max_grad_norm)
        self.high_opt.step()
        return {
            "high_loss": float(loss.detach().cpu().item()),
            "high_policy_loss": float(policy_loss.detach().cpu().item()),
            "high_value_loss": float(value_loss.detach().cpu().item()),
            "high_entropy_loss": float(entropy_loss.detach().cpu().item()),
            "high_aux_loss": float(aux_loss.detach().cpu().item()),
            "high_entropy": float(entropy.detach().mean().cpu().item()),
            "high_return_mean": float(np.mean(returns_np)),
            "high_env_return_mean": float(np.mean(env_returns_np)),
            "high_bootstrap_value_mean": float(np.mean(bootstrap_values_np)),
            "high_bootstrap_contribution_mean": float(np.mean(bootstrap_contrib_np)),
            "high_smdp_discount_mean": float(np.mean(smdp_discounts_np)),
            "high_value_norm_mean": float(self.high_value_norm.mean) if self.high_value_norm is not None else 0.0,
            "high_value_norm_std": float(np.sqrt(self.high_value_norm.var)) if self.high_value_norm is not None else 0.0,
            "high_grad_norm": float(high_grad_norm.detach().cpu().item()),
            "team_code_entropy": float(team_entropy.detach().mean().cpu().item()),
            "compact_norm_mean": float(compact.detach().norm(dim=-1).mean().cpu().item()),
            "opt_cd_loss": float(cd_loss.detach().cpu().item()),
            "opt_cmi_loss": float(cmi_loss.detach().cpu().item()),
            "opt_aggregation_entropy": float(aggregation_entropy.detach().mean().cpu().item()),
            **g_info_metrics,
        }

    def _empty_low_metrics(self) -> dict[str, float]:
        return {
            "low_loss": 0.0,
            "low_policy_loss": 0.0,
            "low_value_loss": 0.0,
            "low_entropy_loss": 0.0,
            "low_actor_loss": 0.0,
            "low_critic_loss": 0.0,
            "low_entropy": 0.0,
            "low_sequence_chunks": 0.0,
            "low_value_norm_mean": float(self.low_value_norm.mean) if self.low_value_norm is not None else 0.0,
            "low_value_norm_std": float(np.sqrt(self.low_value_norm.var)) if self.low_value_norm is not None else 0.0,
            "low_value_error_abs_mean": 0.0,
            "low_value_error_rmse": 0.0,
            "low_advantage_std": 0.0,
            "low_ratio_mean": 0.0,
            "low_clip_frac": 0.0,
            "low_approx_kl": 0.0,
            "low_actor_grad_norm": 0.0,
            "low_critic_grad_norm": 0.0,
            "low_actor_h_norm_mean": 0.0,
            "low_critic_h_norm_mean": 0.0,
            "low_skill_usage_entropy": 0.0,
            "low_skill_return_std": 0.0,
            "low_skill_return_range": 0.0,
            "low_skill_value_error_abs_std": 0.0,
            "low_skill_entropy_std": 0.0,
            "low_team_usage_entropy": 0.0,
            "low_team_return_std": 0.0,
            "low_team_return_range": 0.0,
            "low_team_value_error_abs_std": 0.0,
            "return_mean": 0.0,
        }

    @staticmethod
    def _label_entropy_np(labels: np.ndarray, num_classes: int) -> float:
        labels = np.asarray(labels, dtype=np.int64).reshape(-1)
        if labels.size == 0 or num_classes <= 1:
            return 0.0
        labels = labels[(labels >= 0) & (labels < int(num_classes))]
        if labels.size == 0:
            return 0.0
        counts = np.bincount(labels, minlength=int(num_classes)).astype(np.float64)
        probs = counts[counts > 0.0] / max(float(counts.sum()), 1.0)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))
        return entropy / float(np.log(max(int(num_classes), 2)))

    @staticmethod
    def _group_mean_summary(labels: np.ndarray, values: np.ndarray, num_classes: int) -> dict[str, float]:
        labels = np.asarray(labels, dtype=np.int64).reshape(-1)
        values = np.asarray(values, dtype=np.float64).reshape(-1)
        if labels.size == 0 or values.size == 0:
            return {"std": 0.0, "range": 0.0, "active_frac": 0.0}
        n = min(labels.size, values.size)
        labels = labels[:n]
        values = values[:n]
        means = []
        active = 0
        for label in range(int(max(num_classes, 1))):
            mask = labels == label
            if np.any(mask):
                active += 1
                group_values = values[mask]
                finite = group_values[np.isfinite(group_values)]
                if finite.size:
                    means.append(float(np.mean(finite)))
        if not means:
            return {"std": 0.0, "range": 0.0, "active_frac": 0.0}
        means_arr = np.asarray(means, dtype=np.float64)
        return {
            "std": float(np.std(means_arr)),
            "range": float(np.max(means_arr) - np.min(means_arr)),
            "active_frac": float(active) / float(max(int(num_classes), 1)),
        }

    @staticmethod
    def _info_scalar(value) -> float | None:
        if value is None:
            return None
        try:
            arr = np.asarray(value, dtype=np.float64)
        except (TypeError, ValueError):
            return None
        if arr.size == 0:
            return None
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            return None
        return float(np.mean(finite))

    @classmethod
    def _segment_info_series(cls, segment: Segment, aliases: tuple[str, ...]) -> list[float]:
        values: list[float] = []
        for info in getattr(segment, "reward_info_seq", []):
            if not isinstance(info, dict):
                continue
            for key in aliases:
                if key in info:
                    scalar = cls._info_scalar(info.get(key))
                    if scalar is not None:
                        values.append(scalar)
                    break
        return values

    @classmethod
    def _segment_full_disconnect_mean(cls, segment: Segment) -> float:
        values = cls._segment_info_series(
            segment,
            (
                "full_network_disconnect",
                "full_disconnect",
                "network_disconnected",
            ),
        )
        return float(np.mean(values)) if values else float("nan")

    @classmethod
    def _segment_recovery_flag(cls, segment: Segment) -> float:
        values = cls._segment_info_series(
            segment,
            (
                "full_network_disconnect",
                "full_disconnect",
                "network_disconnected",
            ),
        )
        if len(values) < 2:
            return float("nan")
        return float(values[0] >= 0.5 and values[-1] < 0.5)

    @classmethod
    def _segment_backhaul_up_frac(cls, segment: Segment) -> float:
        flags: list[float] = []
        for info in getattr(segment, "reward_info_seq", []):
            if not isinstance(info, dict):
                continue
            served = cls._info_scalar(
                next(
                    (
                        info.get(key)
                        for key in (
                            "current_backhaul_served_users",
                            "backhaul_served_users",
                            "effective_connected_users",
                            "served_users",
                        )
                        if key in info
                    ),
                    None,
                )
            )
            disconnect = cls._info_scalar(
                next(
                    (
                        info.get(key)
                        for key in (
                            "full_network_disconnect",
                            "full_disconnect",
                            "network_disconnected",
                        )
                        if key in info
                    ),
                    None,
                )
            )
            outage = cls._info_scalar(
                next(
                    (
                        info.get(key)
                        for key in (
                            "backhaul_outage_ratio",
                            "service_drop_ratio",
                        )
                        if key in info
                    ),
                    None,
                )
            )
            backhaul_up = (
                served is not None
                and float(served) > 0.0
                and (disconnect is None or float(disconnect) < 0.5)
                and (outage is None or float(outage) < 0.999)
            )
            flags.append(1.0 if backhaul_up else 0.0)
        return float(np.mean(flags)) if flags else float("nan")

    def _lifetime_diagnostics(
        self,
        segments: list[Segment],
        duration_indices: np.ndarray,
        reward_sums: np.ndarray,
    ) -> dict[str, float]:
        metrics = {
            "lifetime_heterogeneity": 0.0,
            "duration_target_std": 0.0,
            "duration_target_cv": 0.0,
            "duration_agent_mi": 0.0,
            "duration_return_std": 0.0,
            "duration_return_range": 0.0,
            "duration_return_active_frac": 0.0,
            "duration_full_disconnect_std": 0.0,
            "duration_full_disconnect_range": 0.0,
            "duration_recovery_std": 0.0,
            "duration_recovery_range": 0.0,
            "duration_bh_frac_std": 0.0,
            "duration_bh_frac_range": 0.0,
            "renewal_agents_mean": 0.0,
            "renewal_agents_std": 0.0,
            "renewal_full_sync_rate": 0.0,
            "renewal_pairwise_corr_mean": 0.0,
        }
        if not segments:
            return metrics

        n_durations = int(max(len(self.duration_candidates), 1))
        duration_indices = np.asarray(duration_indices, dtype=np.int64).reshape(-1)
        duration_indices = np.clip(duration_indices[: len(segments)], 0, n_durations - 1)
        reward_sums = np.asarray(reward_sums, dtype=np.float64).reshape(-1)[: len(segments)]
        duration_targets = np.asarray([s.duration_target for s in segments], dtype=np.float64)
        agent_ids = np.asarray([s.agent_id for s in segments], dtype=np.int64)

        if duration_targets.size:
            metrics["duration_target_std"] = float(np.std(duration_targets))
            target_mean = float(np.mean(np.abs(duration_targets)))
            metrics["duration_target_cv"] = float(metrics["duration_target_std"] / max(target_mean, 1e-6))
            if len(self.duration_candidates) > 1:
                duration_range = float(max(self.duration_candidates) - min(self.duration_candidates))
                metrics["lifetime_heterogeneity"] = float(
                    metrics["duration_target_std"] / max(duration_range, 1e-6)
                )

        metrics["duration_agent_mi"] = self._joint_mi_norm(
            agent_ids,
            duration_indices,
            self.n_agents,
            n_durations,
        )

        for prefix, values in (
            ("duration_return", reward_sums),
            (
                "duration_full_disconnect",
                np.asarray([self._segment_full_disconnect_mean(s) for s in segments], dtype=np.float64),
            ),
            (
                "duration_recovery",
                np.asarray([self._segment_recovery_flag(s) for s in segments], dtype=np.float64),
            ),
            (
                "duration_bh_frac",
                np.asarray([self._segment_backhaul_up_frac(s) for s in segments], dtype=np.float64),
            ),
        ):
            summary = self._group_mean_summary(duration_indices, values, n_durations)
            metrics[f"{prefix}_std"] = float(summary["std"])
            metrics[f"{prefix}_range"] = float(summary["range"])
            if prefix == "duration_return":
                metrics["duration_return_active_frac"] = float(summary["active_frac"])

        starts_by_env_step: dict[tuple[int, int], set[int]] = {}
        for segment in segments:
            if segment.initial_assignment:
                continue
            key = (int(segment.env_id), int(segment.start_step))
            starts_by_env_step.setdefault(key, set()).add(int(segment.agent_id))
        if starts_by_env_step:
            counts = np.asarray([len(v) for v in starts_by_env_step.values()], dtype=np.float64)
            metrics["renewal_agents_mean"] = float(np.mean(counts))
            metrics["renewal_agents_std"] = float(np.std(counts))
            metrics["renewal_full_sync_rate"] = float(np.mean(counts >= float(self.n_agents)))

            corrs: list[float] = []
            env_ids = sorted({key[0] for key in starts_by_env_step})
            for env_id in env_ids:
                env_keys = sorted(key for key in starts_by_env_step if key[0] == env_id)
                if len(env_keys) < 2:
                    continue
                matrix = np.zeros((len(env_keys), self.n_agents), dtype=np.float64)
                for row_idx, key in enumerate(env_keys):
                    for agent_id in starts_by_env_step[key]:
                        if 0 <= agent_id < self.n_agents:
                            matrix[row_idx, agent_id] = 1.0
                for i in range(self.n_agents):
                    xi = matrix[:, i]
                    if float(np.std(xi)) <= 1e-8:
                        continue
                    for j in range(i + 1, self.n_agents):
                        xj = matrix[:, j]
                        if float(np.std(xj)) <= 1e-8:
                            continue
                        corrs.append(float(np.corrcoef(xi, xj)[0, 1]))
            if corrs:
                metrics["renewal_pairwise_corr_mean"] = float(np.mean(corrs))
        return metrics

    @staticmethod
    def _grad_norm(parameters) -> float:
        total = 0.0
        for param in parameters:
            if param.grad is None:
                continue
            grad = param.grad.detach()
            total += float(torch.sum(grad * grad).cpu().item())
        return float(np.sqrt(max(total, 0.0)))

    def _low_rollout_diagnostics(
        self,
        rollout: Rollout,
        returns: np.ndarray,
        advantages: np.ndarray,
        values: np.ndarray,
    ) -> dict[str, float]:
        skills = np.asarray(rollout.skills, dtype=np.int64).reshape(-1)
        team_codes = np.asarray(rollout.team_codes, dtype=np.int64).reshape(-1)
        if team_codes.size:
            team_codes = np.repeat(team_codes, self.n_agents)
        returns_flat = np.asarray(returns, dtype=np.float32).reshape(-1)
        advantages_flat = np.asarray(advantages, dtype=np.float32).reshape(-1)
        values_flat = np.asarray(values, dtype=np.float32).reshape(-1)
        value_error = returns_flat - values_flat
        value_error_abs = np.abs(value_error)
        actor_hxs = np.asarray(rollout.low_actor_hxs, dtype=np.float32)
        critic_hxs = np.asarray(rollout.low_critic_hxs, dtype=np.float32)
        actor_h_norm = (
            np.linalg.norm(actor_hxs, axis=-1).reshape(-1)
            if actor_hxs.size
            else np.asarray([], dtype=np.float32)
        )
        critic_h_norm = (
            np.linalg.norm(critic_hxs, axis=-1).reshape(-1)
            if critic_hxs.size
            else np.asarray([], dtype=np.float32)
        )
        skill_return = self._group_mean_summary(skills, returns_flat, self.n_skills)
        skill_value_error = self._group_mean_summary(skills, value_error_abs, self.n_skills)
        team_return = self._group_mean_summary(team_codes, returns_flat, self.num_team_codes)
        team_value_error = self._group_mean_summary(team_codes, value_error_abs, self.num_team_codes)
        return {
            "low_value_error_abs_mean": float(np.mean(value_error_abs)) if value_error_abs.size else 0.0,
            "low_value_error_rmse": float(np.sqrt(np.mean(value_error * value_error))) if value_error.size else 0.0,
            "low_advantage_std": float(np.std(advantages_flat)) if advantages_flat.size else 0.0,
            "low_actor_h_norm_mean": float(np.mean(actor_h_norm)) if actor_h_norm.size else 0.0,
            "low_critic_h_norm_mean": float(np.mean(critic_h_norm)) if critic_h_norm.size else 0.0,
            "low_skill_usage_entropy": self._label_entropy_np(skills, self.n_skills),
            "low_skill_return_std": skill_return["std"],
            "low_skill_return_range": skill_return["range"],
            "low_skill_value_error_abs_std": skill_value_error["std"],
            "low_team_usage_entropy": self._label_entropy_np(team_codes, self.num_team_codes),
            "low_team_return_std": team_return["std"],
            "low_team_return_range": team_return["range"],
            "low_team_value_error_abs_std": team_value_error["std"],
        }

    def _low_returns(self, rollout: Rollout) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        rewards = np.asarray(rollout.rewards, dtype=np.float32)
        values = np.asarray(rollout.values, dtype=np.float32)
        dones = np.asarray(rollout.dones, dtype=np.bool_)
        env_ids = np.asarray(
            rollout.env_ids if rollout.env_ids else [0 for _ in range(len(rewards))],
            dtype=np.int64,
        )
        bootstrap_values = getattr(rollout, "bootstrap_values", {}) or {}
        returns = np.zeros_like(rewards, dtype=np.float32)
        advantages = np.zeros_like(rewards, dtype=np.float32)
        for env_id in np.unique(env_ids):
            indices = np.flatnonzero(env_ids == int(env_id))
            last_gae = np.zeros(self.n_agents, dtype=np.float32)
            default_bootstrap = np.zeros(self.n_agents, dtype=np.float32)
            final_bootstrap = np.asarray(
                bootstrap_values.get(int(env_id), default_bootstrap),
                dtype=np.float32,
            ).reshape(-1)
            if final_bootstrap.size != self.n_agents:
                fitted = np.zeros(self.n_agents, dtype=np.float32)
                n = min(fitted.size, final_bootstrap.size)
                if n > 0:
                    fitted[:n] = final_bootstrap[:n]
                final_bootstrap = fitted
            for pos in range(indices.size - 1, -1, -1):
                idx = int(indices[pos])
                if bool(dones[idx]):
                    next_value = default_bootstrap
                    next_nonterminal = 0.0
                elif pos + 1 < indices.size:
                    next_value = values[int(indices[pos + 1])]
                    next_nonterminal = 1.0
                else:
                    next_value = final_bootstrap
                    next_nonterminal = 1.0
                delta = rewards[idx] + self.gamma * next_value * next_nonterminal - values[idx]
                last_gae = delta + self.gamma * self.low_gae_lambda * next_nonterminal * last_gae
                advantages[idx] = last_gae
                returns[idx] = advantages[idx] + values[idx]
        finite = np.isfinite(advantages)
        if np.any(finite):
            mean = float(np.mean(advantages[finite]))
            std = float(np.std(advantages[finite]))
            advantages = (advantages - mean) / (std + 1e-8)
        return returns, advantages.astype(np.float32), values, env_ids

    def _low_sequence_chunks(self, rollout: Rollout, returns: np.ndarray, advantages: np.ndarray, env_ids: np.ndarray):
        obs_arr = np.asarray(rollout.obs, dtype=np.float32)
        states_arr = np.asarray(rollout.states, dtype=np.float32)
        skills_arr = np.asarray(rollout.skills, dtype=np.int64)
        team_codes_arr = np.asarray(rollout.team_codes, dtype=np.int64)
        actions_arr = np.asarray(rollout.actions)
        old_logp_arr = np.asarray(rollout.logp, dtype=np.float32)
        dones_arr = np.asarray(rollout.dones, dtype=np.bool_)
        actor_hxs_arr = np.asarray(rollout.low_actor_hxs, dtype=np.float32)
        critic_hxs_arr = np.asarray(rollout.low_critic_hxs, dtype=np.float32)
        values_arr = np.asarray(rollout.values, dtype=np.float32)
        chunks = []
        seq_len = int(max(self.low_sequence_length, 1))
        for env_id in np.unique(env_ids):
            indices = np.flatnonzero(env_ids == int(env_id))
            for start in range(0, len(indices), seq_len):
                chunk_indices = indices[start:start + seq_len]
                if chunk_indices.size == 0:
                    continue
                first = int(chunk_indices[0])
                chunks.append(
                    {
                        "indices": chunk_indices.astype(np.int64),
                        "initial_actor_hxs": actor_hxs_arr[first],
                        "initial_critic_hxs": critic_hxs_arr[first],
                    }
                )
        return {
            "obs": obs_arr,
            "states": states_arr,
            "skills": skills_arr,
            "team_codes": team_codes_arr,
            "actions": actions_arr,
            "old_logp": old_logp_arr,
            "old_values": values_arr,
            "returns": returns,
            "advantages": advantages,
            "dones": dones_arr,
            "chunks": chunks,
        }

    def _low_batch_from_chunks(self, data: dict[str, Any], chunk_batch: list[dict[str, Any]]):
        batch_size = len(chunk_batch)
        time_steps = max(int(chunk["indices"].size) for chunk in chunk_batch)
        obs = np.zeros((time_steps, batch_size, self.n_agents, self.obs_dim), dtype=np.float32)
        states = np.zeros((time_steps, batch_size, self.state_dim), dtype=np.float32)
        skills = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.int64)
        team_codes = np.zeros((time_steps, batch_size), dtype=np.int64)
        old_logp = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.float32)
        old_values = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.float32)
        returns = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.float32)
        advantages = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.float32)
        masks = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.float32)
        reset_masks = np.ones((time_steps, batch_size, self.n_agents), dtype=np.float32)
        if self.action_space_type == "continuous":
            actions = np.zeros((time_steps, batch_size, self.n_agents, self.action_dim), dtype=np.float32)
        else:
            actions = np.zeros((time_steps, batch_size, self.n_agents), dtype=np.int64)
        initial_actor_hxs = np.zeros((batch_size, self.n_agents, self.low_rnn_hidden_size), dtype=np.float32)
        initial_critic_hxs = np.zeros_like(initial_actor_hxs, dtype=np.float32)

        for batch_idx, chunk in enumerate(chunk_batch):
            chunk_indices = chunk["indices"]
            initial_actor_hxs[batch_idx] = chunk["initial_actor_hxs"]
            initial_critic_hxs[batch_idx] = chunk["initial_critic_hxs"]
            for t, idx in enumerate(chunk_indices):
                obs[t, batch_idx] = data["obs"][idx]
                states[t, batch_idx] = data["states"][idx]
                skills[t, batch_idx] = data["skills"][idx]
                team_codes[t, batch_idx] = data["team_codes"][idx]
                actions[t, batch_idx] = data["actions"][idx]
                old_logp[t, batch_idx] = data["old_logp"][idx]
                old_values[t, batch_idx] = data["old_values"][idx]
                returns[t, batch_idx] = data["returns"][idx]
                advantages[t, batch_idx] = data["advantages"][idx]
                masks[t, batch_idx, :] = 1.0
                if bool(data["dones"][idx]):
                    reset_masks[t, batch_idx, :] = 0.0

        agent_ids = np.broadcast_to(
            np.arange(self.n_agents, dtype=np.int64).reshape(1, 1, self.n_agents),
            (time_steps, batch_size, self.n_agents),
        )
        return {
            "obs": torch.as_tensor(obs, dtype=torch.float32, device=self.device),
            "states": torch.as_tensor(states, dtype=torch.float32, device=self.device),
            "skills": torch.as_tensor(skills, dtype=torch.long, device=self.device),
            "team_codes": torch.as_tensor(team_codes, dtype=torch.long, device=self.device),
            "actions": torch.as_tensor(
                actions,
                dtype=torch.float32 if self.action_space_type == "continuous" else torch.long,
                device=self.device,
            ),
            "old_logp": torch.as_tensor(old_logp, dtype=torch.float32, device=self.device),
            "old_values": torch.as_tensor(old_values, dtype=torch.float32, device=self.device),
            "returns": torch.as_tensor(returns, dtype=torch.float32, device=self.device),
            "advantages": torch.as_tensor(advantages, dtype=torch.float32, device=self.device),
            "masks": torch.as_tensor(masks, dtype=torch.float32, device=self.device),
            "reset_masks": torch.as_tensor(reset_masks, dtype=torch.float32, device=self.device),
            "agent_ids": torch.as_tensor(agent_ids.copy(), dtype=torch.long, device=self.device),
            "initial_actor_hxs": torch.as_tensor(initial_actor_hxs, dtype=torch.float32, device=self.device),
            "initial_critic_hxs": torch.as_tensor(initial_critic_hxs, dtype=torch.float32, device=self.device),
        }

    def _update_low_recurrent(self, rollout: Rollout) -> dict[str, float]:
        returns, advantages, old_values_np, env_ids = self._low_returns(rollout)
        rollout_diagnostics = self._low_rollout_diagnostics(rollout, returns, advantages, old_values_np)
        if self.low_value_norm is not None:
            self.low_value_norm.update(returns.reshape(-1))
        data = self._low_sequence_chunks(rollout, returns, advantages, env_ids)
        chunks = data["chunks"]
        if not chunks:
            return self._empty_low_metrics()

        total_loss = 0.0
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        total_entropy = 0.0
        total_ratio_mean = 0.0
        total_clip_frac = 0.0
        total_approx_kl = 0.0
        total_actor_grad_norm = 0.0
        total_critic_grad_norm = 0.0
        skill_entropy_sums = np.zeros(self.n_skills, dtype=np.float64)
        skill_entropy_counts = np.zeros(self.n_skills, dtype=np.float64)
        update_count = 0
        rng = np.random.default_rng()
        for _epoch in range(self.low_ppo_epochs):
            order = rng.permutation(len(chunks))
            for start in range(0, len(order), self.low_sequence_batch_size):
                batch_chunks = [chunks[int(i)] for i in order[start:start + self.low_sequence_batch_size]]
                if not batch_chunks:
                    continue
                batch = self._low_batch_from_chunks(data, batch_chunks)
                logp, entropy, values = self.low.evaluate_sequence(
                    batch["obs"],
                    batch["skills"],
                    batch["actions"],
                    batch["states"],
                    batch["team_codes"],
                    batch["agent_ids"],
                    batch["initial_actor_hxs"],
                    batch["initial_critic_hxs"],
                    batch["masks"],
                    batch["reset_masks"],
                )
                valid = batch["masks"] > 0.0
                if not torch.any(valid):
                    continue
                ratio = torch.exp(logp[valid] - batch["old_logp"][valid].detach())
                adv = batch["advantages"][valid]
                old_logp_valid = batch["old_logp"][valid].detach()
                policy_loss = -torch.min(
                    ratio * adv,
                    torch.clamp(ratio, 1.0 - self.low_clip, 1.0 + self.low_clip) * adv,
                ).mean()
                target_returns = batch["returns"]
                old_values = batch["old_values"]
                if self.low_value_norm is not None:
                    target_returns = self.low_value_norm.normalize_tensor(target_returns)
                    old_values = self.low_value_norm.normalize_tensor(old_values)
                    if self.low_value_clip > 0.0:
                        target_returns = target_returns.clamp(-self.low_value_clip, self.low_value_clip)
                target_returns = target_returns.detach()
                old_values = old_values.detach()
                if self.low_value_clip > 0.0:
                    clipped_values = old_values + (values - old_values).clamp(
                        -self.low_value_clip,
                        self.low_value_clip,
                    )
                    value_loss_unclipped = (values - target_returns).pow(2)
                    value_loss_clipped = (clipped_values - target_returns).pow(2)
                    value_loss = 0.5 * torch.max(
                        value_loss_unclipped[valid],
                        value_loss_clipped[valid],
                    ).mean()
                else:
                    value_loss = 0.5 * F.mse_loss(values[valid], target_returns[valid])
                entropy_mean = entropy[valid].mean()
                entropy_loss = -self.low_entropy_coef * entropy_mean
                actor_loss = policy_loss + entropy_loss
                critic_loss = self.low_value_loss_coef * value_loss
                loss = actor_loss + critic_loss

                self.low_actor_opt.zero_grad()
                self.low_critic_opt.zero_grad()
                loss.backward()
                actor_params = list(self.low.actor_update_parameters())
                critic_params = list(self.low.critic_update_parameters())
                if self.low_max_grad_norm > 0.0:
                    actor_grad_norm = float(
                        torch.nn.utils.clip_grad_norm_(actor_params, self.low_max_grad_norm).detach().cpu().item()
                    )
                    critic_grad_norm = float(
                        torch.nn.utils.clip_grad_norm_(critic_params, self.low_max_grad_norm).detach().cpu().item()
                    )
                else:
                    actor_grad_norm = self._grad_norm(actor_params)
                    critic_grad_norm = self._grad_norm(critic_params)
                self.low_actor_opt.step()
                self.low_critic_opt.step()

                total_loss += float(loss.detach().cpu().item())
                total_policy_loss += float(policy_loss.detach().cpu().item())
                total_value_loss += float(value_loss.detach().cpu().item())
                total_entropy_loss += float(entropy_loss.detach().cpu().item())
                total_entropy += float(entropy_mean.detach().cpu().item())
                total_ratio_mean += float(ratio.detach().mean().cpu().item())
                total_clip_frac += float((torch.abs(ratio.detach() - 1.0) > self.low_clip).float().mean().cpu().item())
                total_approx_kl += float((old_logp_valid - logp[valid].detach()).mean().cpu().item())
                total_actor_grad_norm += actor_grad_norm
                total_critic_grad_norm += critic_grad_norm
                skills_np = batch["skills"][valid].detach().cpu().numpy().astype(np.int64)
                entropy_np = entropy[valid].detach().cpu().numpy().astype(np.float64)
                for skill_id in range(self.n_skills):
                    mask = skills_np == skill_id
                    if np.any(mask):
                        skill_entropy_sums[skill_id] += float(np.sum(entropy_np[mask]))
                        skill_entropy_counts[skill_id] += float(np.sum(mask))
                update_count += 1

        denom = max(update_count, 1)
        active_skill_entropy = skill_entropy_counts > 0.0
        if np.any(active_skill_entropy):
            skill_entropy_means = skill_entropy_sums[active_skill_entropy] / skill_entropy_counts[active_skill_entropy]
            low_skill_entropy_std = float(np.std(skill_entropy_means))
        else:
            low_skill_entropy_std = 0.0
        return {
            "low_loss": total_loss / denom,
            "low_policy_loss": total_policy_loss / denom,
            "low_value_loss": total_value_loss / denom,
            "low_entropy_loss": total_entropy_loss / denom,
            "low_actor_loss": (total_policy_loss + total_entropy_loss) / denom,
            "low_critic_loss": self.low_value_loss_coef * total_value_loss / denom,
            "low_entropy": total_entropy / denom,
            "low_sequence_chunks": float(len(chunks)),
            "low_value_norm_mean": float(self.low_value_norm.mean) if self.low_value_norm is not None else 0.0,
            "low_value_norm_std": float(np.sqrt(self.low_value_norm.var)) if self.low_value_norm is not None else 0.0,
            "low_ratio_mean": total_ratio_mean / denom,
            "low_clip_frac": total_clip_frac / denom,
            "low_approx_kl": total_approx_kl / denom,
            "low_actor_grad_norm": total_actor_grad_norm / denom,
            "low_critic_grad_norm": total_critic_grad_norm / denom,
            "low_skill_entropy_std": low_skill_entropy_std,
            "return_mean": float(np.mean(returns)),
            **rollout_diagnostics,
        }

    def update_low(self, rollout: Rollout) -> dict[str, float]:
        if not rollout.rewards:
            return self._empty_low_metrics()
        if self.use_recurrent_low_level:
            return self._update_low_recurrent(rollout)
        rewards = np.asarray(rollout.rewards, dtype=np.float32)
        values = np.asarray(rollout.values, dtype=np.float32)
        returns = np.zeros_like(rewards)
        running = np.zeros(self.n_agents, dtype=np.float32)
        for t in reversed(range(len(rewards))):
            running = rewards[t] + self.gamma * running * (1.0 - float(rollout.dones[t]))
            returns[t] = running
        advantages = returns - values
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        obs_t = torch.as_tensor(np.asarray(rollout.obs), dtype=torch.float32, device=self.device).reshape(-1, rollout.obs[0].shape[-1])
        skills_t = torch.as_tensor(np.asarray(rollout.skills), dtype=torch.long, device=self.device).reshape(-1)
        if self.action_space_type == "continuous":
            actions_t = torch.as_tensor(
                np.asarray(rollout.actions),
                dtype=torch.float32,
                device=self.device,
            ).reshape(-1, self.action_dim)
        else:
            actions_t = torch.as_tensor(
                np.asarray(rollout.actions),
                dtype=torch.long,
                device=self.device,
            ).reshape(-1)
        old_logp_t = torch.as_tensor(np.asarray(rollout.logp), dtype=torch.float32, device=self.device).reshape(-1)
        returns_t = torch.as_tensor(returns, dtype=torch.float32, device=self.device).reshape(-1)
        adv_t = torch.as_tensor(advantages, dtype=torch.float32, device=self.device).reshape(-1)

        logp, entropy, new_values = self.low.evaluate(obs_t, skills_t, actions_t)
        ratio = torch.exp(logp - old_logp_t)
        policy_loss = -torch.min(
            ratio * adv_t,
            torch.clamp(ratio, 1.0 - self.low_clip, 1.0 + self.low_clip) * adv_t,
        ).mean()
        value_loss = F.mse_loss(new_values, returns_t)
        entropy_loss = -self.low_entropy_coef * entropy.mean()
        critic_loss = self.low_value_loss_coef * value_loss
        loss = policy_loss + critic_loss + entropy_loss

        self.low_opt.zero_grad()
        loss.backward()
        self.low_opt.step()
        return {
            **self._empty_low_metrics(),
            "low_loss": float(loss.detach().cpu().item()),
            "low_policy_loss": float(policy_loss.detach().cpu().item()),
            "low_value_loss": float(value_loss.detach().cpu().item()),
            "low_entropy_loss": float(entropy_loss.detach().cpu().item()),
            "low_actor_loss": float((policy_loss + entropy_loss).detach().cpu().item()),
            "low_critic_loss": float(critic_loss.detach().cpu().item()),
            "low_entropy": float(entropy.detach().mean().cpu().item()),
            "low_sequence_chunks": 0.0,
            "low_value_norm_mean": 0.0,
            "low_value_norm_std": 0.0,
            "return_mean": float(returns.mean()),
        }
