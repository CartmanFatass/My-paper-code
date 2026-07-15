"""R30 fixed-clock all-agent autoregressive edit controller primitives."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch.distributions import Categorical


KEEP_TOKEN = 0
SET_TOKEN = 1
INVALID_SKILL = -1
HIGH_BUFFER_VERSION = 1


@dataclass(frozen=True)
class EditSequenceSample:
    token_kind: torch.Tensor
    set_skill: torch.Tensor
    token_logp: torch.Tensor
    token_valid: torch.Tensor
    skill_entropy: torch.Tensor
    final_skills: torch.Tensor
    final_ages: torch.Tensor
    final_active: torch.Tensor


class FixedClockAREditPolicy(nn.Module):
    """Canonical-order skill editor with one combined log-prob per token."""

    def __init__(
        self,
        obs_dim: int,
        n_agents: int,
        n_skills: int,
        hidden_dim: int,
        compact_dim: int,
        team_code_dim: int,
        omega_dim: int = 0,
        agent_relevance_dim: int = 0,
        keep_init: float = 0.6,
        age_reference_steps: int = 500,
        force_refresh_every_check: bool = False,
        native_categorical_edit: bool = False,
    ) -> None:
        super().__init__()
        self.obs_dim = int(obs_dim)
        self.n_agents = int(n_agents)
        self.n_skills = int(n_skills)
        self.omega_dim = int(max(omega_dim, 0))
        self.agent_relevance_dim = int(max(agent_relevance_dim, 0))
        self.force_refresh_every_check = bool(force_refresh_every_check)
        self.native_categorical_edit = bool(native_categorical_edit)
        self.ar_prefix_dim = self.n_skills * (1 + 2 * self.n_agents)
        self.age_reference_steps = int(max(age_reference_steps, 1))
        input_dim = (
            self.obs_dim
            + self.n_skills
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
        self.skill_head = nn.Linear(hidden_dim, self.n_skills)
        self.keep_head: nn.Linear | None = None
        if not self.native_categorical_edit:
            self.keep_head = nn.Linear(hidden_dim, 1)
            keep_init = float(np.clip(keep_init, 1e-6, 1.0 - 1e-6))
            nn.init.zeros_(self.keep_head.weight)
            nn.init.constant_(
                self.keep_head.bias, math.log(keep_init / (1.0 - keep_init))
            )

    def encode_working_roster(
        self,
        skills: torch.Tensor,
        ages: torch.Tensor,
        active: torch.Tensor,
        focal_agent: int,
    ) -> torch.Tensor:
        """Encode integer working state; this output is never stored as replay truth."""

        skills = skills.long().reshape(-1)
        ages = ages.float().reshape(-1)
        active = active.bool().reshape(-1)
        out = torch.zeros(self.ar_prefix_dim, dtype=torch.float32, device=skills.device)
        count_scale = 1.0 / float(max(self.n_agents, 1))
        identity_offset = self.n_skills
        age_offset = identity_offset + self.n_agents * self.n_skills
        age_denom = math.log1p(float(self.age_reference_steps))
        for agent_id in range(self.n_agents):
            if agent_id == int(focal_agent) or not bool(active[agent_id].item()):
                continue
            skill = int(skills[agent_id].item())
            if not 0 <= skill < self.n_skills:
                continue
            out[skill] += count_scale
            out[identity_offset + agent_id * self.n_skills + skill] = count_scale
            age_value = math.log1p(max(float(ages[agent_id].item()), 0.0)) / age_denom
            out[age_offset + agent_id * self.n_skills + skill] = count_scale * age_value
        return out.unsqueeze(0)

    def _hidden(
        self,
        obs: torch.Tensor,
        current_skill: torch.Tensor,
        current_age: torch.Tensor,
        current_active: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        roster: torch.Tensor,
        omega: torch.Tensor | None,
        agent_relevance: torch.Tensor | None,
    ) -> torch.Tensor:
        current_skill = current_skill.long().reshape(-1)
        current_active = current_active.bool().reshape(-1)
        safe_skill = current_skill.clamp(0, self.n_skills - 1)
        skill_onehot = F.one_hot(safe_skill, num_classes=self.n_skills).float()
        skill_onehot = skill_onehot * current_active.float().unsqueeze(-1)
        age_feature = torch.log1p(current_age.float().clamp_min(0.0)).reshape(-1, 1) / 10.0
        age_feature = age_feature * current_active.float().unsqueeze(-1)
        pieces = [obs.float(), skill_onehot, age_feature, compact.float(), team_vector.float()]
        if self.omega_dim > 0:
            if omega is None:
                omega = torch.zeros(obs.shape[0], self.omega_dim, device=obs.device)
            pieces.append(omega.float())
        if self.agent_relevance_dim > 0:
            if agent_relevance is None:
                agent_relevance = torch.zeros(
                    obs.shape[0], self.agent_relevance_dim, device=obs.device
                )
            pieces.append(agent_relevance.float())
        pieces.append(roster.float())
        return self.input(torch.cat(pieces, dim=-1))

    def _masked_skill_logits(
        self,
        hidden: torch.Tensor,
        current_skill: int,
        current_active: bool,
        *,
        detached_hidden: bool = False,
    ) -> torch.Tensor:
        logits = self.skill_head(hidden.detach() if detached_hidden else hidden)
        if (
            current_active
            and not self.force_refresh_every_check
            and not self.native_categorical_edit
        ):
            logits = logits.clone()
            logits[:, int(current_skill)] = torch.finfo(logits.dtype).min
        return logits

    def _token_context(
        self,
        joint_obs: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        working_skills: torch.Tensor,
        working_ages: torch.Tensor,
        working_active: torch.Tensor,
        agent_id: int,
        omega: torch.Tensor | None,
        agent_relevance: torch.Tensor | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        roster = self.encode_working_roster(
            working_skills, working_ages, working_active, agent_id
        )
        rel = None
        if agent_relevance is not None:
            rel = agent_relevance[:, int(agent_id), :]
        hidden = self._hidden(
            joint_obs[int(agent_id) : int(agent_id) + 1],
            working_skills[int(agent_id) : int(agent_id) + 1],
            working_ages[int(agent_id) : int(agent_id) + 1],
            working_active[int(agent_id) : int(agent_id) + 1],
            compact,
            team_vector,
            roster,
            omega,
            rel,
        )
        current_active = bool(working_active[int(agent_id)].item())
        current_skill = int(working_skills[int(agent_id)].item())
        keep_logit = (
            self.keep_head(hidden).squeeze(-1)
            if self.keep_head is not None
            else torch.zeros(hidden.shape[0], device=hidden.device, dtype=hidden.dtype)
        )
        skill_logits = self._masked_skill_logits(
            hidden, current_skill, current_active
        )
        entropy_logits = self._masked_skill_logits(
            hidden, current_skill, current_active, detached_hidden=True
        )
        return hidden, keep_logit, skill_logits, entropy_logits

    def act_sequence(
        self,
        joint_obs: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        prev_skills: torch.Tensor,
        prev_ages: torch.Tensor,
        prev_active: torch.Tensor,
        agent_order: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> EditSequenceSample:
        working_skills = prev_skills.long().clone().reshape(-1)
        working_ages = prev_ages.long().clone().reshape(-1)
        working_active = prev_active.bool().clone().reshape(-1)
        kinds: list[torch.Tensor] = []
        set_skills: list[torch.Tensor] = []
        logps: list[torch.Tensor] = []
        entropies: list[torch.Tensor] = []
        for raw_agent_id in agent_order.long().reshape(-1):
            agent_id = int(raw_agent_id.item())
            _hidden, keep_logit, skill_logits, entropy_logits = self._token_context(
                joint_obs,
                compact,
                team_vector,
                working_skills,
                working_ages,
                working_active,
                agent_id,
                omega,
                agent_relevance,
            )
            active = bool(working_active[agent_id].item())
            skill_dist = Categorical(logits=skill_logits)
            if self.native_categorical_edit:
                skill = (
                    torch.argmax(skill_logits, dim=-1)
                    if deterministic
                    else skill_dist.sample()
                )
                choose_keep = (
                    active
                    and not self.force_refresh_every_check
                    and int(skill.item()) == int(working_skills[agent_id].item())
                )
                kind = torch.full_like(
                    skill, KEEP_TOKEN if choose_keep else SET_TOKEN
                )
                logp = skill_dist.log_prob(skill)
                entropy_weight = torch.ones_like(logp)
            elif not active:
                skill = torch.argmax(skill_logits, dim=-1) if deterministic else skill_dist.sample()
                kind = torch.ones_like(skill, dtype=torch.long) * SET_TOKEN
                logp = skill_dist.log_prob(skill)
                entropy_weight = torch.ones_like(logp)
            elif self.force_refresh_every_check:
                skill = (
                    torch.argmax(skill_logits, dim=-1)
                    if deterministic
                    else skill_dist.sample()
                )
                kind = torch.ones_like(skill, dtype=torch.long) * SET_TOKEN
                logp = skill_dist.log_prob(skill)
                entropy_weight = torch.ones_like(logp)
            else:
                skill_log_probs = F.log_softmax(skill_logits, dim=-1)
                log_keep = F.logsigmoid(keep_logit)
                log_switch = F.logsigmoid(-keep_logit)
                if deterministic:
                    best_skill = torch.argmax(skill_log_probs, dim=-1)
                    best_set_logp = log_switch + skill_log_probs.gather(
                        -1, best_skill.unsqueeze(-1)
                    ).squeeze(-1)
                    choose_keep = log_keep >= best_set_logp
                else:
                    choose_keep = torch.rand_like(keep_logit) < torch.sigmoid(keep_logit)
                    best_skill = skill_dist.sample()
                skill = best_skill
                kind = torch.where(
                    choose_keep,
                    torch.full_like(skill, KEEP_TOKEN),
                    torch.full_like(skill, SET_TOKEN),
                )
                set_logp = log_switch + skill_dist.log_prob(skill)
                logp = torch.where(choose_keep, log_keep, set_logp)
                entropy_weight = (1.0 - torch.sigmoid(keep_logit)).detach()
            entropy = Categorical(logits=entropy_logits).entropy() * entropy_weight
            if int(kind.item()) == SET_TOKEN:
                working_skills[agent_id] = int(skill.item())
                working_ages[agent_id] = 0
                working_active[agent_id] = True
                set_value = skill
            else:
                set_value = torch.full_like(skill, INVALID_SKILL)
            kinds.append(kind.squeeze(0))
            set_skills.append(set_value.squeeze(0))
            logps.append(logp.squeeze(0))
            entropies.append(entropy.squeeze(0))
        token_kind = torch.stack(kinds)
        set_skill = torch.stack(set_skills)
        token_logp = torch.stack(logps)
        skill_entropy = torch.stack(entropies)
        return EditSequenceSample(
            token_kind=token_kind,
            set_skill=set_skill,
            token_logp=token_logp,
            token_valid=torch.ones_like(token_kind, dtype=torch.bool),
            skill_entropy=skill_entropy,
            final_skills=working_skills,
            final_ages=working_ages,
            final_active=working_active,
        )

    def evaluate_sequence(
        self,
        joint_obs: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        prev_skills: torch.Tensor,
        prev_ages: torch.Tensor,
        prev_active: torch.Tensor,
        agent_order: torch.Tensor,
        token_kind: torch.Tensor,
        set_skill: torch.Tensor,
        omega: torch.Tensor | None = None,
        agent_relevance: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        working_skills = prev_skills.long().clone().reshape(-1)
        working_ages = prev_ages.long().clone().reshape(-1)
        working_active = prev_active.bool().clone().reshape(-1)
        logps: list[torch.Tensor] = []
        entropies: list[torch.Tensor] = []
        for position, raw_agent_id in enumerate(agent_order.long().reshape(-1)):
            agent_id = int(raw_agent_id.item())
            _hidden, keep_logit, skill_logits, entropy_logits = self._token_context(
                joint_obs,
                compact,
                team_vector,
                working_skills,
                working_ages,
                working_active,
                agent_id,
                omega,
                agent_relevance,
            )
            active = bool(working_active[agent_id].item())
            kind = int(token_kind[position].item())
            if not active and kind != SET_TOKEN:
                raise ValueError("initial R30 token must be SET")
            skill_dist = Categorical(logits=skill_logits)
            if self.native_categorical_edit:
                if kind == KEEP_TOKEN:
                    if self.force_refresh_every_check or not active:
                        raise ValueError(
                            "native categorical KEEP requires an active incumbent"
                        )
                    skill = working_skills[agent_id].long().reshape(1)
                elif kind == SET_TOKEN:
                    skill = set_skill[position].long().reshape(1)
                    if (
                        active
                        and not self.force_refresh_every_check
                        and int(skill.item()) == int(working_skills[agent_id].item())
                    ):
                        raise ValueError(
                            "native categorical incumbent action must replay as KEEP"
                        )
                    working_skills[agent_id] = int(skill.item())
                    working_ages[agent_id] = 0
                    working_active[agent_id] = True
                else:
                    raise ValueError(f"invalid R30 token kind {kind}")
                logp = skill_dist.log_prob(skill)
                weight = torch.ones_like(logp)
            elif kind == KEEP_TOKEN:
                if self.force_refresh_every_check:
                    raise ValueError("shared fixed-k control cannot replay KEEP")
                logp = F.logsigmoid(keep_logit)
                weight = (1.0 - torch.sigmoid(keep_logit)).detach()
            elif kind == SET_TOKEN:
                skill = set_skill[position].long().reshape(1)
                skill_logp = skill_dist.log_prob(skill)
                logp = (
                    skill_logp
                    if not active or self.force_refresh_every_check
                    else F.logsigmoid(-keep_logit) + skill_logp
                )
                working_skills[agent_id] = int(skill.item())
                working_ages[agent_id] = 0
                working_active[agent_id] = True
                weight = (
                    torch.ones_like(logp)
                    if not active or self.force_refresh_every_check
                    else (1.0 - torch.sigmoid(keep_logit)).detach()
                )
            else:
                raise ValueError(f"invalid R30 token kind {kind}")
            entropy = Categorical(logits=entropy_logits).entropy() * weight
            logps.append(logp.squeeze(0))
            entropies.append(entropy.squeeze(0))
        return torch.stack(logps), torch.stack(entropies)


class HighCheckValue(nn.Module):
    """One prefix-independent centralized value for a high-check row."""

    def __init__(
        self,
        state_dim: int,
        obs_dim: int,
        n_agents: int,
        n_skills: int,
        compact_dim: int,
        team_code_dim: int,
        hidden_dim: int,
        age_reference_steps: int = 500,
        k0: int = 10,
    ) -> None:
        super().__init__()
        self.n_agents = int(n_agents)
        self.n_skills = int(n_skills)
        self.age_reference_steps = int(max(age_reference_steps, 1))
        self.k0 = int(max(k0, 1))
        roster_dim = self.n_agents * self.n_skills + 2 * self.n_agents
        input_dim = (
            int(state_dim)
            + self.n_agents * int(obs_dim)
            + int(compact_dim)
            + int(team_code_dim)
            + roster_dim
            + 1
        )
        self.net = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(
        self,
        state: torch.Tensor,
        joint_obs: torch.Tensor,
        prev_skills: torch.Tensor,
        prev_active: torch.Tensor,
        prev_ages: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        steps_to_check: torch.Tensor,
    ) -> torch.Tensor:
        batch = state.shape[0]
        skills = prev_skills.long().reshape(batch, self.n_agents)
        active = prev_active.bool().reshape(batch, self.n_agents)
        safe = skills.clamp(0, self.n_skills - 1)
        skill_onehot = F.one_hot(safe, self.n_skills).float()
        skill_onehot = skill_onehot * active.float().unsqueeze(-1)
        age_denom = math.log1p(float(self.age_reference_steps))
        age = torch.log1p(prev_ages.float().clamp_min(0.0)) / age_denom
        age = age * active.float()
        clock = steps_to_check.float().reshape(batch, 1) / float(self.k0)
        features = torch.cat(
            [
                state.float().reshape(batch, -1),
                joint_obs.float().reshape(batch, -1),
                compact.float().reshape(batch, -1),
                team_vector.float().reshape(batch, -1),
                skill_onehot.reshape(batch, -1),
                active.float(),
                age,
                clock,
            ],
            dim=-1,
        )
        return self.net(features).squeeze(-1)


@dataclass
class HighCheckRow:
    env_id: int
    episode_id: int
    sequence_index: int
    state: np.ndarray
    joint_obs: np.ndarray
    prev_skills: np.ndarray
    prev_active: np.ndarray
    prev_ages: np.ndarray
    steps_to_check: int
    decision_mask: bool
    agent_order: np.ndarray
    token_kind: np.ndarray
    set_skill: np.ndarray
    token_valid: np.ndarray
    old_token_logp: np.ndarray
    old_value: float
    old_next_value: float = 0.0
    block_reward: float = 0.0
    block_len: int = 0
    terminal: bool = False
    policy_truncated: bool = False


class HighCheckBuffer:
    """Per-environment pending fixed-clock rows and completed PPO rows."""

    version = HIGH_BUFFER_VERSION

    def __init__(self, num_envs: int, n_agents: int, gamma: float) -> None:
        self.num_envs = int(num_envs)
        self.n_agents = int(n_agents)
        self.gamma = float(gamma)
        self.pending: list[HighCheckRow | None] = [None for _ in range(self.num_envs)]
        self.rows: list[HighCheckRow] = []
        self.sequence_indices = np.zeros(self.num_envs, dtype=np.int64)

    def _new_row(
        self,
        *,
        env_id: int,
        episode_id: int,
        state,
        joint_obs,
        prev_skills,
        prev_active,
        prev_ages,
        steps_to_check: int,
        decision_mask: bool,
        old_value: float,
        agent_order=None,
        token_kind=None,
        set_skill=None,
        token_valid=None,
        old_token_logp=None,
    ) -> HighCheckRow:
        env_id = int(env_id)
        if self.pending[env_id] is not None:
            raise RuntimeError(f"R30 env {env_id} already has a pending high row")
        zeros_i = np.zeros(self.n_agents, dtype=np.int64)
        row = HighCheckRow(
            env_id=env_id,
            episode_id=int(episode_id),
            sequence_index=int(self.sequence_indices[env_id]),
            state=np.asarray(state, dtype=np.float32).copy(),
            joint_obs=np.asarray(joint_obs, dtype=np.float32).copy(),
            prev_skills=np.asarray(prev_skills, dtype=np.int64).copy(),
            prev_active=np.asarray(prev_active, dtype=np.bool_).copy(),
            prev_ages=np.asarray(prev_ages, dtype=np.int64).copy(),
            steps_to_check=int(steps_to_check),
            decision_mask=bool(decision_mask),
            agent_order=(
                zeros_i.copy()
                if agent_order is None
                else np.asarray(agent_order, dtype=np.int64).copy()
            ),
            token_kind=(
                zeros_i.copy()
                if token_kind is None
                else np.asarray(token_kind, dtype=np.int64).copy()
            ),
            set_skill=(
                np.full(self.n_agents, INVALID_SKILL, dtype=np.int64)
                if set_skill is None
                else np.asarray(set_skill, dtype=np.int64).copy()
            ),
            token_valid=(
                np.zeros(self.n_agents, dtype=np.bool_)
                if token_valid is None
                else np.asarray(token_valid, dtype=np.bool_).copy()
            ),
            old_token_logp=(
                np.zeros(self.n_agents, dtype=np.float32)
                if old_token_logp is None
                else np.asarray(old_token_logp, dtype=np.float32).copy()
            ),
            old_value=float(old_value),
        )
        self.sequence_indices[env_id] += 1
        self.pending[env_id] = row
        return row

    def start_decision(self, **kwargs) -> HighCheckRow:
        kwargs["decision_mask"] = True
        return self._new_row(**kwargs)

    def start_continuation(self, **kwargs) -> HighCheckRow:
        kwargs["decision_mask"] = False
        return self._new_row(**kwargs)

    def accumulate(self, env_id: int, reward: float) -> None:
        row = self.pending[int(env_id)]
        if row is None:
            raise RuntimeError(f"R30 env {env_id} has no pending high row")
        row.block_reward += (self.gamma ** int(row.block_len)) * float(reward)
        row.block_len += 1

    def close(
        self,
        env_id: int,
        *,
        old_next_value: float,
        terminal: bool,
        policy_truncated: bool,
    ) -> HighCheckRow:
        env_id = int(env_id)
        row = self.pending[env_id]
        if row is None:
            raise RuntimeError(f"R30 env {env_id} has no pending row to close")
        row.old_next_value = float(old_next_value)
        row.terminal = bool(terminal)
        row.policy_truncated = bool(policy_truncated)
        self.rows.append(row)
        self.pending[env_id] = None
        return row

    def clear_env(self, env_id: int) -> None:
        self.pending[int(env_id)] = None

    def pop_completed(self) -> list[HighCheckRow]:
        rows = self.rows
        self.rows = []
        return rows
