"""Pure neural-network and policy definitions for the standalone process core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

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
        self.register_buffer("prototype_bank_ema", self.prototypes.detach().clone())
        self.output = nn.Sequential(
            nn.LayerNorm(compact_dim * 2),
            nn.Linear(compact_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, compact_dim),
        )

    @torch.no_grad()
    def update_prototype_bank_ema(self, tau: float = 0.005) -> None:
        tau = float(min(max(tau, 0.0), 1.0))
        self.prototype_bank_ema.mul_(1.0 - tau).add_(self.prototypes.detach(), alpha=tau)

    @torch.no_grad()
    def prototype_bank_drift_cos(self) -> torch.Tensor:
        current = F.normalize(self.prototypes.detach(), dim=-1)
        ema = F.normalize(self.prototype_bank_ema.detach(), dim=-1)
        return (current * ema).sum(dim=-1).mean()

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
        agent_logits = self.prototype_logits(obs_tokens.reshape(-1, self.compact_dim)).reshape(
            batch_size,
            n_agents,
            self.num_prototypes,
        )
        agent_relevance = (
            sparsemax(agent_logits, dim=-1)
            if self.use_sparsemax
            else F.softmax(agent_logits, dim=-1)
        )
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
        return compact, cd_loss, cmi_loss, weights, aggregation_entropy, agent_relevance


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

    def expected_context(self, compact: torch.Tensor):
        """R30 deterministic bridge context; never a sampled policy action."""

        batch_size = compact.shape[0]
        device = compact.device
        if self.bridge_type == "none":
            logits = torch.zeros(batch_size, self.num_team_codes, device=device)
            probs = torch.full_like(logits, 1.0 / float(self.num_team_codes))
            vector = torch.zeros(batch_size, self.team_code_dim, device=device)
            code = torch.zeros(batch_size, dtype=torch.long, device=device)
            return code, vector, probs, logits
        base_vector = self.vector_bridge(compact)
        logits = torch.clamp(self.code_head(base_vector), -50.0, 50.0)
        probs = F.softmax(logits, dim=-1)
        vector = probs @ self.code_embedding.weight
        code = torch.argmax(probs, dim=-1)
        return code, vector, probs, logits

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
        if self.bridge_type == "deterministic_expected":
            probs = F.softmax(logits, dim=-1)
            team_vector = probs @ self.code_embedding.weight
            team_code = torch.argmax(probs, dim=-1)
            zeros = torch.zeros(batch_size, device=device)
            return team_code, team_vector, zeros, zeros, logits
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


class FixedSkillPrimitivePolicy(nn.Module):
    """Zero-parameter four-skill action carrier for the R39 toy positive control."""

    def __init__(self, n_skills: int, action_dim: int, action_space_type: str):
        super().__init__()
        if int(n_skills) != 4 or int(action_dim) != 2 or action_space_type != "continuous":
            raise ValueError("R39 fixed primitives require four skills and 2D continuous actions")
        self.n_skills = 4
        self.action_dim = 2
        self.action_space_type = "continuous"
        self.register_buffer(
            "action_table",
            torch.tensor(
                [[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]],
                dtype=torch.float32,
            ),
        )

    def act(self, obs: torch.Tensor, skills: torch.Tensor, deterministic: bool = False):
        del obs, deterministic
        actions = self.action_table[skills.long().clamp(0, self.n_skills - 1)]
        zeros = torch.zeros(skills.shape, dtype=torch.float32, device=skills.device)
        return actions, zeros, zeros, zeros


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
            self.action_epsilon = 1e-6

    def _features(self, obs: torch.Tensor, skills: torch.Tensor) -> torch.Tensor:
        skill_onehot = F.one_hot(skills.long(), num_classes=self.n_skills).float()
        return torch.cat([obs.float(), skill_onehot], dim=-1)

    def actor_update_parameters(self):
        params = list(self.actor.parameters())
        if self.action_space_type == "continuous":
            params.append(self.log_std)
        return params

    def critic_update_parameters(self):
        return list(self.critic.parameters())

    def _continuous_distribution(self, actor_out: torch.Tensor):
        std = torch.exp(self.log_std).expand_as(actor_out)
        return torch.distributions.Normal(actor_out, std)

    def _action_scale_bias(self) -> tuple[torch.Tensor, torch.Tensor]:
        scale = ((self.action_high - self.action_low) * 0.5).clamp_min(self.action_epsilon)
        bias = (self.action_high + self.action_low) * 0.5
        return scale, bias

    def _squashed_log_prob(
        self,
        dist: torch.distributions.Normal,
        raw_action: torch.Tensor,
        unit_action: torch.Tensor,
    ) -> torch.Tensor:
        scale, _bias = self._action_scale_bias()
        log_jacobian = torch.log(scale) + torch.log(
            1.0 - unit_action.square() + self.action_epsilon
        )
        return (dist.log_prob(raw_action) - log_jacobian).sum(dim=-1)

    def _sample_continuous(self, actor_out: torch.Tensor, deterministic: bool):
        dist = self._continuous_distribution(actor_out)
        raw_action = actor_out if deterministic else dist.rsample()
        unit_action = torch.tanh(raw_action)
        scale, bias = self._action_scale_bias()
        action = bias + scale * unit_action
        # Record the likelihood of the float32 action that is actually handed
        # to the environment.  Reconstructing it here uses the same numerical
        # path as PPO replay, including near-boundary clamping.
        replay_unit_action = ((action - bias) / scale).clamp(
            -1.0 + self.action_epsilon,
            1.0 - self.action_epsilon,
        )
        replay_raw_action = torch.atanh(replay_unit_action)
        log_prob = self._squashed_log_prob(
            dist, replay_raw_action, replay_unit_action
        )
        return action, log_prob, -log_prob

    def _evaluate_continuous(self, actor_out: torch.Tensor, actions: torch.Tensor):
        dist = self._continuous_distribution(actor_out)
        scale, bias = self._action_scale_bias()
        unit_action = ((actions.float() - bias) / scale).clamp(
            -1.0 + self.action_epsilon,
            1.0 - self.action_epsilon,
        )
        raw_action = torch.atanh(unit_action)
        log_prob = self._squashed_log_prob(dist, raw_action, unit_action)
        entropy_raw = dist.rsample()
        entropy_unit = torch.tanh(entropy_raw)
        entropy = -self._squashed_log_prob(dist, entropy_raw, entropy_unit)
        return log_prob, entropy

    def act(self, obs: torch.Tensor, skills: torch.Tensor, deterministic: bool = False):
        features = self._features(obs, skills)
        actor_out = self.actor(features)
        if self.action_space_type == "continuous":
            actions, log_prob, entropy = self._sample_continuous(actor_out, deterministic)
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
            log_prob, entropy = self._evaluate_continuous(actor_out, actions)
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

    def film_update_parameters(self):
        """Return the only low-actor parameters admitted by R32-IFEPG."""

        return list(self.actor_film.parameters())

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

    def evaluate_focal_sequence_log_probs(
        self,
        obs_seq: torch.Tensor,
        skills_seq: torch.Tensor,
        actions_seq: torch.Tensor,
        initial_actor_hxs: torch.Tensor,
        team_codes_seq: torch.Tensor | None = None,
        masks_seq: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Replay one focal trajectory through the current low actor.

        R32 uses this actor-only path to compare stored behavior likelihoods
        with likelihoods under the current skill FiLM.  It intentionally does
        not evaluate the critic or sample an entropy estimate.
        """

        if self.action_space_type != "continuous":
            raise TypeError("R32 focal replay requires a continuous low actor")
        action_out = self.actor_act.action_out
        if type(action_out).__name__ != "TanhDiagGaussian":
            raise TypeError("R32 focal replay requires the tanh-Gaussian action head")

        obs = check(obs_seq).to(dtype=torch.float32, device=self.device)
        skills = check(skills_seq).to(dtype=torch.long, device=self.device).reshape(-1)
        actions = check(actions_seq).to(dtype=torch.float32, device=self.device)
        if obs.ndim != 2 or obs.shape[1] != self.obs_dim:
            raise ValueError("R32 focal observations must have shape [T, obs_dim]")
        time_steps = int(obs.shape[0])
        if skills.shape != (time_steps,):
            raise ValueError("R32 focal skills must have shape [T]")
        if actions.shape != (time_steps, self.action_dim):
            raise ValueError("R32 focal actions must have shape [T, action_dim]")

        actor_hxs = check(initial_actor_hxs).to(
            dtype=torch.float32,
            device=self.device,
        )
        if actor_hxs.ndim == 1:
            actor_hxs = actor_hxs.unsqueeze(0)
        if actor_hxs.shape != (1, self.hidden_dim):
            raise ValueError("R32 focal initial hidden state must have shape [hidden_dim]")

        if team_codes_seq is None:
            team_codes = torch.zeros(time_steps, dtype=torch.long, device=self.device)
        else:
            team_codes = check(team_codes_seq).to(
                dtype=torch.long,
                device=self.device,
            ).reshape(-1)
            if team_codes.shape != (time_steps,):
                raise ValueError("R32 focal team codes must have shape [T]")

        if masks_seq is None:
            masks = torch.ones(time_steps, 1, 1, dtype=torch.float32, device=self.device)
        else:
            masks = check(masks_seq).to(dtype=torch.float32, device=self.device)
            if masks.numel() != time_steps:
                raise ValueError("R32 focal masks must contain one value per step")
            masks = masks.reshape(time_steps, 1, 1)

        bounded_actions = torch.clamp(
            actions,
            -1.0 + action_out.epsilon,
            1.0 - action_out.epsilon,
        )
        log_probabilities: list[torch.Tensor] = []
        recurrent_state = actor_hxs
        for step in range(time_steps):
            actor_features = self._actor_features(
                obs[step : step + 1],
                skills[step : step + 1],
                team_codes[step : step + 1],
            )
            actor_features, recurrent_state = self.actor_rnn(
                actor_features,
                recurrent_state,
                masks[step].reshape(1, 1),
            )
            distribution = action_out._distribution(actor_features)
            bounded_action = bounded_actions[step : step + 1]
            raw_action = torch.atanh(bounded_action)
            log_probabilities.append(
                self._squeeze_log_probs(
                    action_out._squashed_log_probs(
                        distribution,
                        raw_action,
                        bounded_action,
                    )
                )[0]
            )
        return torch.stack(log_probabilities)

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
        return_deterministic_action: bool = False,
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
        result = (
            actions,
            self._squeeze_log_probs(log_probs),
            torch.zeros_like(values),
            values,
            new_actor_hxs,
            new_critic_hxs,
        )
        if not return_deterministic_action:
            return result
        action_out = self.actor_act.action_out
        if type(action_out).__name__ != "TanhDiagGaussian":
            raise TypeError("R28-G1 requires the registered tanh-Gaussian action head")
        distribution = action_out._distribution(actor_features)
        deterministic_action = torch.tanh(distribution.mean)
        return (*result, deterministic_action)

    def r27_g2_audit_step(
        self,
        obs: torch.Tensor,
        skills: torch.Tensor,
        actor_hxs: torch.Tensor,
        states: torch.Tensor,
        team_codes: torch.Tensor,
        critic_hxs: torch.Tensor,
        *,
        focal_agent: int,
        focal_inactive_film: bool = False,
    ) -> dict[str, torch.Tensor]:
        """Run one strict, RNG-free R27-G2 low-level transition.

        This audit-only path mirrors the registered strict MAPPO actor and
        critic while exposing the pre-tanh Gaussian parameters.  It never
        mutates the supplied roster or hidden tensors.  A focal inactive-FiLM
        branch replaces only that row's skill FiLM with the identity transform.
        """

        if self.action_space_type != "continuous":
            raise TypeError("R27-G2 requires the registered continuous low actor")
        if self.actor_condition_on_team_code or self.actor_team_film is not None:
            raise TypeError("R27-G2 rejects actor team-code conditioning")
        action_out = self.actor_act.action_out
        if type(action_out).__name__ != "TanhDiagGaussian":
            raise TypeError("R27-G2 requires the registered tanh-Gaussian action head")
        if obs.ndim != 2 or obs.shape != (skills.shape[0], self.obs_dim):
            raise ValueError("R27-G2 observation shape does not match the source actor")
        batch = int(obs.shape[0])
        if batch <= 0 or not 0 <= int(focal_agent) < batch:
            raise ValueError("R27-G2 focal_agent is outside the actor batch")
        expected_hidden = (batch, self.hidden_dim)
        if tuple(actor_hxs.shape) != expected_hidden or tuple(critic_hxs.shape) != expected_hidden:
            raise ValueError("R27-G2 recurrent hidden shape does not match the source actor")
        if tuple(states.shape) != (batch, self.state_dim):
            raise ValueError("R27-G2 state shape does not match the source critic")
        if tuple(skills.shape) != (batch,) or tuple(team_codes.shape) != (batch,):
            raise ValueError("R27-G2 roster/team-code shape mismatch")
        if bool(torch.any(skills < 0)) or bool(torch.any(skills >= self.n_skills)):
            raise ValueError("R27-G2 actor-visible skill is outside the source codebook")

        actor_features = self.actor_base(
            check(obs).to(dtype=torch.float32, device=self.device)
        )
        skill_onehot = F.one_hot(skills.long(), num_classes=self.n_skills).float()
        film = self.actor_film(skill_onehot)
        gamma, beta = torch.chunk(film, 2, dim=-1)
        if focal_inactive_film:
            gamma = gamma.clone()
            beta = beta.clone()
            gamma[int(focal_agent)] = 1.0
            beta[int(focal_agent)] = 0.0
        actor_features = gamma * actor_features + beta
        masks = torch.ones(batch, 1, dtype=torch.float32, device=self.device)
        actor_features, new_actor_hxs = self.actor_rnn(
            actor_features, actor_hxs.float(), masks
        )

        distribution = action_out._distribution(actor_features)
        pre_tanh_mean = distribution.mean
        log_standard_deviation = torch.log(distribution.stddev)
        deterministic_action = torch.tanh(pre_tanh_mean)
        log_probability = action_out._squashed_log_probs(
            distribution, pre_tanh_mean, deterministic_action
        )

        critic_features = self._critic_features(states, team_codes)
        critic_features, new_critic_hxs = self.critic_rnn(
            critic_features, critic_hxs.float(), masks
        )
        values = self.value_head(critic_features).squeeze(-1)
        return {
            "pre_tanh_mean": pre_tanh_mean,
            "log_standard_deviation": log_standard_deviation,
            "deterministic_action": deterministic_action,
            "log_probability": self._squeeze_log_probs(log_probability),
            "value": values,
            "new_actor_hxs": new_actor_hxs,
            "new_critic_hxs": new_critic_hxs,
        }

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


@dataclass(frozen=True)
class HighActionSample:
    skills: torch.Tensor
    durations: torch.Tensor
    logp: torch.Tensor
    entropy: torch.Tensor
    value: torch.Tensor
    skill_logp: torch.Tensor
    duration_logp: torch.Tensor
    skill_entropy: torch.Tensor
    duration_entropy: torch.Tensor
    skill_logits: torch.Tensor
    duration_logits: torch.Tensor


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
        omega_dim: int = 0,
        agent_relevance_dim: int = 0,
        ar_prefix_dim: int = 0,
        z_action_gain: float = 0.0,
    ):
        super().__init__()
        self.n_skills = int(n_skills)
        self.omega_dim = int(max(omega_dim, 0))
        self.agent_relevance_dim = int(max(agent_relevance_dim, 0))
        self.ar_prefix_dim = int(max(ar_prefix_dim, 0))
        self.team_code_dim = int(team_code_dim)
        # R23 architecture correction: a direct, controllable residual path from the
        # team-intent vector into the assignment logits, bypassing the LayerNorm'd
        # trunk (whose effective Z gain was ~noise, per R21 autopsy). Default-off
        # (gain 0.0 -> modules absent -> S-base architecture is bit-identical).
        self.z_action_gain = float(z_action_gain)
        if self.z_action_gain > 0.0:
            self.z_skill_residual = nn.Linear(self.team_code_dim, int(n_skills))
            self.z_duration_residual = nn.Linear(self.team_code_dim, int(n_durations))
        else:
            self.z_skill_residual = None
            self.z_duration_residual = None
        input_dim = (
            int(obs_dim)
            + int(n_skills)
            + 1
            + int(compact_dim)
            + int(team_code_dim)
            + self.omega_dim
            + self.agent_relevance_dim
            + self.ar_prefix_dim
        )
        self.input = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden_dim),
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
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        ar_prefix: torch.Tensor | None = None,
    ) -> torch.Tensor:
        prev_onehot = F.one_hot(prev_skills.long().clamp(0, self.n_skills - 1), num_classes=self.n_skills).float()
        age_feature = torch.log1p(ages.float()).unsqueeze(-1) / 10.0
        pieces = [obs.float(), prev_onehot, age_feature, compact.float(), team_vector.float()]
        if self.omega_dim > 0:
            if omega is None:
                omega = torch.zeros(obs.shape[0], self.omega_dim, dtype=obs.dtype, device=obs.device)
            pieces.append(omega.float())
        if self.agent_relevance_dim > 0:
            if agent_relevance is None:
                agent_relevance = torch.zeros(
                    obs.shape[0],
                    self.agent_relevance_dim,
                    dtype=obs.dtype,
                    device=obs.device,
                )
            pieces.append(agent_relevance.float())
        if self.ar_prefix_dim > 0:
            if ar_prefix is None:
                ar_prefix = torch.zeros(obs.shape[0], self.ar_prefix_dim, dtype=obs.dtype, device=obs.device)
            pieces.append(ar_prefix.float())
        return self.input(torch.cat(pieces, dim=-1))

    def logits(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        ar_prefix: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = self._features(
            obs,
            prev_skills,
            ages,
            compact,
            team_vector,
            omega,
            agent_relevance,
            ar_prefix,
        )
        skill_logits = self.skill_head(hidden)
        duration_logits = self.duration_head(hidden)
        if self.z_action_gain > 0.0 and self.z_skill_residual is not None:
            skill_logits = skill_logits + self.z_action_gain * self.z_skill_residual(team_vector.float())
            duration_logits = duration_logits + self.z_action_gain * self.z_duration_residual(team_vector.float())
        return skill_logits, duration_logits, self.value_head(hidden).squeeze(-1)

    def act_with_parts(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        ar_prefix: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> HighActionSample:
        skill_logits, duration_logits, value = self.logits(
            obs,
            prev_skills,
            ages,
            compact,
            team_vector,
            omega=omega,
            agent_relevance=agent_relevance,
            ar_prefix=ar_prefix,
        )
        skill_dist = Categorical(logits=skill_logits)
        duration_dist = Categorical(logits=duration_logits)
        if deterministic:
            skills = torch.argmax(skill_logits, dim=-1)
            durations = torch.argmax(duration_logits, dim=-1)
        else:
            skills = skill_dist.sample()
            durations = duration_dist.sample()
        skill_logp = skill_dist.log_prob(skills)
        duration_logp = duration_dist.log_prob(durations)
        skill_entropy = skill_dist.entropy()
        duration_entropy = duration_dist.entropy()
        return HighActionSample(
            skills=skills,
            durations=durations,
            logp=skill_logp + duration_logp,
            entropy=skill_entropy + duration_entropy,
            value=value,
            skill_logp=skill_logp,
            duration_logp=duration_logp,
            skill_entropy=skill_entropy,
            duration_entropy=duration_entropy,
            skill_logits=skill_logits,
            duration_logits=duration_logits,
        )

    def act(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        ar_prefix: torch.Tensor | None = None,
        deterministic: bool = False,
    ):
        sample = self.act_with_parts(
            obs,
            prev_skills,
            ages,
            compact,
            team_vector,
            omega=omega,
            agent_relevance=agent_relevance,
            ar_prefix=ar_prefix,
            deterministic=deterministic,
        )
        return sample.skills, sample.durations, sample.logp, sample.entropy, sample.value

    def evaluate(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        skills: torch.Tensor,
        durations: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        ar_prefix: torch.Tensor | None = None,
    ):
        skill_logits, duration_logits, value = self.logits(
            obs,
            prev_skills,
            ages,
            compact,
            team_vector,
            omega=omega,
            agent_relevance=agent_relevance,
            ar_prefix=ar_prefix,
        )
        skill_dist = Categorical(logits=skill_logits)
        duration_dist = Categorical(logits=duration_logits)
        logp = skill_dist.log_prob(skills.long()) + duration_dist.log_prob(durations.long())
        entropy = skill_dist.entropy() + duration_dist.entropy()
        return logp, entropy, value

    def entropy_components(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        ar_prefix: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        skill_logits, duration_logits, _value = self.logits(
            obs,
            prev_skills,
            ages,
            compact,
            team_vector,
            omega=omega,
            agent_relevance=agent_relevance,
            ar_prefix=ar_prefix,
        )
        return Categorical(logits=skill_logits).entropy(), Categorical(logits=duration_logits).entropy()


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
