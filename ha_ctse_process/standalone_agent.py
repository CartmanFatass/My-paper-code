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

from ha_ctse_process.process_outcomes import ProcessOutcomeExtractor
from ha_ctse_process.process_posterior import SegmentSkillPosterior


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

    def act(
        self,
        obs: torch.Tensor,
        prev_skills: torch.Tensor,
        ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        deterministic: bool = False,
    ):
        hidden = self._features(obs, prev_skills, ages, compact, team_vector)
        skill_dist = Categorical(logits=self.skill_head(hidden))
        duration_dist = Categorical(logits=self.duration_head(hidden))
        if deterministic:
            skills = torch.argmax(self.skill_head(hidden), dim=-1)
            durations = torch.argmax(self.duration_head(hidden), dim=-1)
        else:
            skills = skill_dist.sample()
            durations = duration_dist.sample()
        logp = skill_dist.log_prob(skills) + duration_dist.log_prob(durations)
        entropy = skill_dist.entropy() + duration_dist.entropy()
        value = self.value_head(hidden).squeeze(-1)
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
        hidden = self._features(obs, prev_skills, ages, compact, team_vector)
        skill_dist = Categorical(logits=self.skill_head(hidden))
        duration_dist = Categorical(logits=self.duration_head(hidden))
        logp = skill_dist.log_prob(skills.long()) + duration_dist.log_prob(durations.long())
        entropy = skill_dist.entropy() + duration_dist.entropy()
        value = self.value_head(hidden).squeeze(-1)
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
    end_obs: np.ndarray | None = None

    def append(self, obs, action, reward, next_obs, rollout_idx: int, reward_info=None):
        self.obs.append(np.asarray(obs, dtype=np.float32))
        action_arr = np.asarray(action, dtype=np.float32)
        self.actions.append(action_arr.reshape(-1))
        self.rewards.append(float(reward))
        self.rollout_indices.append(int(rollout_idx))
        self.reward_info_seq.append(dict(reward_info or {}))
        self.end_obs = np.asarray(next_obs, dtype=np.float32)

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

    def append(self, env_id: int, obs, actions, rewards, next_obs, rollout_idx: int, reward_info=None):
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
    obs: list[np.ndarray] = field(default_factory=list)
    skills: list[np.ndarray] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)
    logp: list[np.ndarray] = field(default_factory=list)
    values: list[np.ndarray] = field(default_factory=list)
    rewards: list[np.ndarray] = field(default_factory=list)
    dones: list[bool] = field(default_factory=list)


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
        self.duration_candidates = tuple(getattr(config, "skill_lifetime_candidates", (1, 2, 3, 5)))
        if not self.duration_candidates:
            self.duration_candidates = (1,)
        hidden = int(getattr(config, "hidden_size", 128))
        self.gamma = float(getattr(config, "gamma", 0.99))
        self.clip = float(getattr(config, "clip_epsilon", 0.2))
        self.process_reward_coef = float(getattr(config, "process_reward_coef", 0.05))
        self.process_reward_clip = float(getattr(config, "process_reward_clip", 2.0))
        self.process_contrast_coef = float(getattr(config, "process_contrast_coef", 1.0))
        self.process_outcome_coef = float(getattr(config, "process_outcome_coef", 0.25))
        self.process_reward_contrast_coef = float(getattr(config, "process_reward_contrast_coef", 1.0))
        self.process_reward_outcome_coef = float(getattr(config, "process_reward_outcome_coef", 0.25))
        self.use_process_reward = bool(getattr(config, "use_process_reward_for_discoverer", True))
        self.use_process_posterior_mi = bool(getattr(config, "use_process_posterior_mi", True))
        self.process_prior_coef = float(getattr(config, "process_prior_coef", 0.25))
        self.process_posterior_condition_on_team = bool(
            getattr(config, "process_posterior_condition_on_team", True)
        )
        self.high_entropy_coef = float(getattr(config, "high_entropy_coef", 0.01))
        self.low_entropy_coef = float(getattr(config, "low_entropy_coef", 0.01))
        self.edit_penalty_alpha = float(getattr(config, "edit_penalty_alpha", 0.0))
        self.switch_penalty_beta = float(getattr(config, "switch_penalty_beta", 0.0))
        self.opt_cd_coef = float(getattr(config, "opt_cd_coef", 0.0))
        self.opt_cmi_coef = float(getattr(config, "opt_cmi_coef", 0.0))
        self.outcome_extractor = ProcessOutcomeExtractor(
            normalize=bool(getattr(config, "normalize_process_outcomes", True))
        )

        self.action_space_type = str(action_space_type)
        self.action_dim = int(action_dim)
        compact_dim = int(getattr(config, "opt_compact_dim", getattr(config, "embedding_dim", 64) or 64))
        team_code_dim = int(getattr(config, "team_code_dim", compact_dim))
        num_team_codes = int(getattr(config, "num_team_codes", getattr(config, "n_Z", 1) or 1))
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
        self.process_posterior = SegmentSkillPosterior(
            process_embedding_dim,
            self.n_skills,
            num_team_codes,
            hidden,
            team_embed_dim=int(getattr(config, "process_posterior_team_embed_dim", 0) or min(hidden, max(8, num_team_codes * 4))),
            condition_on_team=self.process_posterior_condition_on_team,
        ).to(self.device)

        lr = float(getattr(config, "lr_discoverer_actor", 3e-4))
        high_lr = float(getattr(config, "lr_coordinator", lr))
        process_lr = float(getattr(config, "lr_process_encoder", 1e-4))
        self.low_opt = torch.optim.Adam(self.low.parameters(), lr=lr)
        self.high_opt = torch.optim.Adam(
            list(self.compact.parameters()) + list(self.bridge.parameters()) + list(self.high.parameters()),
            lr=high_lr,
        )
        self.process_opt = torch.optim.Adam(
            list(self.process.parameters()) + list(self.process_posterior.parameters()),
            lr=process_lr,
        )

        self.active_skills = np.zeros((self.num_envs, self.n_agents), dtype=np.int64)
        self.duration_remaining = np.zeros((self.num_envs, self.n_agents), dtype=np.int64)
        self.skill_age = np.zeros((self.num_envs, self.n_agents), dtype=np.int64)
        self.has_active_skill = np.zeros((self.num_envs, self.n_agents), dtype=np.bool_)
        self.segments = SegmentManager(self.num_envs, self.n_agents)

    def _fit_vector(self, value, dim: int) -> np.ndarray:
        arr = np.asarray(value, dtype=np.float32).reshape(-1)
        if arr.size == dim:
            return arr
        fitted = np.zeros(dim, dtype=np.float32)
        n = min(dim, arr.size)
        if n > 0:
            fitted[:n] = arr[:n]
        return fitted

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

    def reset_all_policy_state(self):
        self.duration_remaining[:, :] = 0
        self.active_skills[:, :] = 0
        self.skill_age[:, :] = 0
        self.has_active_skill[:, :] = False
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
            chosen_skills = skills.cpu().numpy()
            chosen_duration_idx = duration_idx.cpu().numpy()
            chosen_durations = np.asarray(self.duration_candidates, dtype=np.int64)[chosen_duration_idx]
            team_code_value = int(team_code.detach().cpu().numpy()[0])
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

    def act_low(self, obs: np.ndarray, env_id: int = 0, deterministic: bool = False):
        env_id = int(env_id)
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=self.device)
        skills_t = torch.as_tensor(self.active_skills[env_id], dtype=torch.long, device=self.device)
        with torch.no_grad():
            actions, logp, _, values = self.low.act(
                obs_t,
                skills_t,
                deterministic=deterministic,
            )
        return (
            actions.cpu().numpy().astype(np.int64 if self.action_space_type == "discrete" else np.float32),
            logp.cpu().numpy().astype(np.float32),
            values.cpu().numpy().astype(np.float32),
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

    def process_update(self, rollout: Rollout) -> dict[str, float]:
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
                "process_log_q_mean": 0.0,
                "process_log_p_mean": 0.0,
                "process_reward_mean": 0.0,
                "outcome_available_mean": 0.0,
                "outcome_abs_mean": 0.0,
                "duration_only_accuracy": 0.0,
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
                "high_loss": 0.0,
                "high_policy_loss": 0.0,
                "high_value_loss": 0.0,
                "high_entropy_loss": 0.0,
                "high_aux_loss": 0.0,
                "high_entropy": 0.0,
                "high_return_mean": 0.0,
            }

        max_len = max(s.length for s in valid)
        obs = np.zeros((len(valid), max_len, valid[0].obs[0].shape[0]), dtype=np.float32)
        action_dim = valid[0].actions[0].size
        actions = np.zeros((len(valid), max_len, action_dim), dtype=np.float32)
        rewards = np.zeros((len(valid), max_len), dtype=np.float32)
        masks = np.zeros((len(valid), max_len), dtype=np.float32)
        labels = np.zeros(len(valid), dtype=np.int64)
        durations_np = np.zeros(len(valid), dtype=np.int64)
        team_codes_np = np.zeros(len(valid), dtype=np.int64)
        outcomes = np.zeros((len(valid), self.outcome_extractor.num_outcomes), dtype=np.float32)
        outcome_masks = np.zeros_like(outcomes, dtype=np.float32)
        raw_outcomes = np.zeros_like(outcomes, dtype=np.float32)
        for idx, segment in enumerate(valid):
            length = segment.length
            obs[idx, :length] = np.asarray(segment.obs, dtype=np.float32)
            actions[idx, :length] = np.asarray(segment.actions, dtype=np.float32)
            rewards[idx, :length] = np.asarray(segment.rewards, dtype=np.float32)
            masks[idx, :length] = 1.0
            labels[idx] = int(segment.skill)
            durations_np[idx] = int(segment.duration_idx)
            team_codes_np[idx] = int(segment.team_code)
            raw, outcome_mask, normalized = self.outcome_extractor.transform(segment, update=True)
            raw_outcomes[idx] = raw
            outcomes[idx] = normalized
            outcome_masks[idx] = outcome_mask.astype(np.float32)

        obs_t = torch.as_tensor(obs, device=self.device)
        actions_t = torch.as_tensor(actions, device=self.device)
        rewards_t = torch.as_tensor(rewards, device=self.device)
        masks_t = torch.as_tensor(masks, device=self.device)
        labels_t = torch.as_tensor(labels, device=self.device)
        team_codes_t = torch.as_tensor(team_codes_np, dtype=torch.long, device=self.device)
        outcomes_t = torch.as_tensor(outcomes, device=self.device)
        outcome_masks_t = torch.as_tensor(outcome_masks, device=self.device)

        emb, pred_outcome, legacy_logits = self.process(obs_t, actions_t, rewards_t, masks_t)
        outcome_sq_error = torch.square(pred_outcome - outcomes_t) * outcome_masks_t
        outcome_loss = outcome_sq_error.sum() / outcome_masks_t.sum().clamp_min(1.0)
        if self.use_process_posterior_mi:
            posterior_logits, prior_logits = self.process_posterior(emb, team_codes_t)
            posterior_terms = self.process_posterior.losses(posterior_logits, prior_logits, labels_t)
            contrastive_loss = posterior_terms["posterior_loss"]
            prior_loss = posterior_terms["prior_loss"]
            posterior_acc = posterior_terms["posterior_acc"]
            posterior_logits_for_reward = posterior_logits
            prior_logits_for_reward = prior_logits
        else:
            contrastive_loss = F.cross_entropy(legacy_logits, labels_t)
            prior_loss = torch.zeros((), device=self.device)
            posterior_acc = (legacy_logits.argmax(dim=-1) == labels_t).float().mean()
            posterior_logits_for_reward = legacy_logits
            prior_logits_for_reward = None
        loss = (
            self.process_outcome_coef * outcome_loss
            + self.process_contrast_coef * contrastive_loss
            + (self.process_prior_coef * prior_loss if self.use_process_posterior_mi else 0.0)
        )
        self.process_opt.zero_grad()
        loss.backward()
        self.process_opt.step()

        with torch.no_grad():
            log_q = F.log_softmax(posterior_logits_for_reward, dim=-1)[
                torch.arange(len(valid), device=self.device),
                labels_t,
            ]
            if self.use_process_posterior_mi and prior_logits_for_reward is not None:
                log_p = F.log_softmax(prior_logits_for_reward, dim=-1)[
                    torch.arange(len(valid), device=self.device),
                    labels_t,
                ]
                mi_estimate = log_q - log_p
            else:
                log_p = torch.full_like(log_q, -float(np.log(self.n_skills)))
                mi_estimate = log_q + float(np.log(self.n_skills))
            outcome_error = outcome_sq_error.sum(dim=-1) / outcome_masks_t.sum(dim=-1).clamp_min(1.0)
            process_reward = self.process_reward_coef * (
                self.process_reward_contrast_coef * mi_estimate
                - self.process_reward_outcome_coef * outcome_error
            )
            if not self.use_process_reward:
                process_reward = torch.zeros_like(process_reward)
            if self.process_reward_clip > 0:
                process_reward = torch.clamp(process_reward, -self.process_reward_clip, self.process_reward_clip)
            process_reward_np = process_reward.detach().cpu().numpy()

        for segment, reward_value in zip(valid, process_reward_np):
            if segment.length <= 0:
                continue
            per_step = float(reward_value) / float(segment.length)
            for rollout_idx in segment.rollout_indices:
                if 0 <= rollout_idx < len(rollout.rewards):
                    rollout.rewards[rollout_idx][segment.agent_id] += per_step

        high_metrics = self.update_high_from_segments(valid, process_reward_np)

        lengths = np.asarray([s.length for s in valid], dtype=np.float32)
        skill_entropy, skill_max_frac = self._usage_stats(labels, self.n_skills)
        duration_entropy, duration_max_frac = self._usage_stats(durations_np, len(self.duration_candidates))
        team_code_entropy, team_code_max_frac = self._usage_stats(team_codes_np, self.bridge.num_team_codes)
        return {
            "process_segments": float(len(valid)),
            "process_loss": float(loss.detach().cpu().item()),
            "process_outcome_loss": float(outcome_loss.detach().cpu().item()),
            "process_contrastive_loss": float(contrastive_loss.detach().cpu().item()),
            "process_prior_loss": float(prior_loss.detach().cpu().item()),
            "process_posterior_acc": float(posterior_acc.detach().cpu().item()),
            "process_mi_estimate_mean": float(mi_estimate.detach().mean().cpu().item()),
            "process_log_q_mean": float(log_q.detach().mean().cpu().item()),
            "process_log_p_mean": float(log_p.detach().mean().cpu().item()),
            "process_reward_mean": float(np.mean(process_reward_np)),
            "outcome_available_mean": float(np.mean(outcome_masks)),
            "outcome_abs_mean": float(np.mean(np.abs(raw_outcomes[outcome_masks > 0.0]))) if np.any(outcome_masks > 0.0) else 0.0,
            "duration_only_accuracy": self.duration_only_accuracy(labels, durations_np),
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
            "team_code_skill_mi": self._joint_mi_norm(team_codes_np, labels, self.bridge.num_team_codes, self.n_skills),
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

    def update_high_from_segments(self, segments: list[Segment], process_rewards: np.ndarray) -> dict[str, float]:
        if not segments:
            return {
                "high_loss": 0.0,
                "high_policy_loss": 0.0,
                "high_value_loss": 0.0,
                "high_entropy_loss": 0.0,
                "high_aux_loss": 0.0,
                "high_entropy": 0.0,
                "high_return_mean": 0.0,
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

        returns_np = np.asarray(
            [
                float(np.sum(s.rewards)) + float(process_rewards[idx]) - float(s.renewal_penalty)
                for idx, s in enumerate(segments)
            ],
            dtype=np.float32,
        )
        returns = torch.as_tensor(returns_np, dtype=torch.float32, device=self.device)
        advantages = returns - old_value
        if advantages.numel() > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)

        ratio = torch.exp(logp - old_logp)
        policy_loss = -torch.min(
            ratio * advantages,
            torch.clamp(ratio, 1.0 - self.clip, 1.0 + self.clip) * advantages,
        ).mean()
        value_loss = F.mse_loss(values, returns)
        entropy_loss = -self.high_entropy_coef * entropy.mean()
        aux_loss = self.opt_cd_coef * cd_loss + self.opt_cmi_coef * cmi_loss
        loss = (
            policy_loss
            + 0.5 * value_loss
            + entropy_loss
            + aux_loss
        )

        self.high_opt.zero_grad()
        loss.backward()
        self.high_opt.step()
        return {
            "high_loss": float(loss.detach().cpu().item()),
            "high_policy_loss": float(policy_loss.detach().cpu().item()),
            "high_value_loss": float(value_loss.detach().cpu().item()),
            "high_entropy_loss": float(entropy_loss.detach().cpu().item()),
            "high_aux_loss": float(aux_loss.detach().cpu().item()),
            "high_entropy": float(entropy.detach().mean().cpu().item()),
            "high_return_mean": float(np.mean(returns_np)),
            "team_code_entropy": float(team_entropy.detach().mean().cpu().item()),
            "compact_norm_mean": float(compact.detach().norm(dim=-1).mean().cpu().item()),
            "opt_cd_loss": float(cd_loss.detach().cpu().item()),
            "opt_cmi_loss": float(cmi_loss.detach().cpu().item()),
            "opt_aggregation_entropy": float(aggregation_entropy.detach().mean().cpu().item()),
        }

    def update_low(self, rollout: Rollout) -> dict[str, float]:
        if not rollout.rewards:
            return {
                "low_loss": 0.0,
                "low_policy_loss": 0.0,
                "low_value_loss": 0.0,
                "low_entropy_loss": 0.0,
                "low_entropy": 0.0,
                "return_mean": 0.0,
            }
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
        policy_loss = -torch.min(ratio * adv_t, torch.clamp(ratio, 1.0 - self.clip, 1.0 + self.clip) * adv_t).mean()
        value_loss = F.mse_loss(new_values, returns_t)
        entropy_loss = -self.low_entropy_coef * entropy.mean()
        loss = policy_loss + 0.5 * value_loss + entropy_loss

        self.low_opt.zero_grad()
        loss.backward()
        self.low_opt.step()
        return {
            "low_loss": float(loss.detach().cpu().item()),
            "low_policy_loss": float(policy_loss.detach().cpu().item()),
            "low_value_loss": float(value_loss.detach().cpu().item()),
            "low_entropy_loss": float(entropy_loss.detach().cpu().item()),
            "low_entropy": float(entropy.detach().mean().cpu().item()),
            "return_mean": float(returns.mean()),
        }
