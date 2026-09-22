"""Direction-local joint duration learner.

The adapter keeps HMASD's primitive actor, critic, discriminator and recurrent
replay unchanged.  It replaces only the D2 high-level clock and coordinator
update with a common event return shared by the sampled team, skill and
duration factors.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from torch.optim import Adam

from hmasd.agent import HMASDAgent


DURATION_CAP = 10
DURATION_MODES = ("fixed", "factored", "ar")
GROUPED_REPLAY_ABS_TOLERANCE = 2e-5
MERGED_REPLAY_RELATIVE_TOLERANCE = 0.001


class ReplayAuditError(RuntimeError):
    """Replay identity or merged numerical-drift audit failure."""

    def __init__(self, message: str, *, reason: str | None = None, facts: dict | None = None):
        super().__init__(message)
        self.reason = reason
        self.facts = facts


def mask_duration_logits(logits: torch.Tensor, remaining: torch.Tensor | int) -> torch.Tensor:
    """Mask a ten-way duration distribution to ``1..remaining`` before sampling."""
    if logits.shape[-1] != DURATION_CAP:
        raise ValueError(f"duration logits must have {DURATION_CAP} classes")
    remaining_t = torch.as_tensor(remaining, device=logits.device, dtype=torch.long)
    remaining_t = torch.broadcast_to(remaining_t, logits.shape[:-1])
    if torch.any((remaining_t < 1) | (remaining_t > DURATION_CAP)):
        raise ValueError("remaining duration support must be in 1..10")
    duration = torch.arange(1, DURATION_CAP + 1, device=logits.device)
    return logits.masked_fill(duration > remaining_t.unsqueeze(-1), -torch.inf)


def compute_event_gae(
    rewards: Sequence[float],
    values: Sequence[float],
    elapsed: Sequence[int],
    terminals: Sequence[bool],
    *,
    gamma: float,
    lambda_10: float = 0.95,
    env_ids: Sequence[int] | None = None,
    bootstrap_values: Mapping[int, float] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute real-scale common event GAE in collection order.

    ``values`` are the frozen, denormalized values collected at event starts.
    A nonterminal final row may use an explicit continuation value for unit
    checks, while the first native runner accepts terminal-aligned batches only.
    """
    rewards_a = np.asarray(rewards, dtype=np.float64)
    values_a = np.asarray(values, dtype=np.float64)
    elapsed_a = np.asarray(elapsed, dtype=np.int64)
    terminals_a = np.asarray(terminals, dtype=np.bool_)
    if not (rewards_a.ndim == values_a.ndim == elapsed_a.ndim == terminals_a.ndim == 1):
        raise ValueError("event GAE inputs must be one-dimensional")
    if not (len(rewards_a) == len(values_a) == len(elapsed_a) == len(terminals_a)):
        raise ValueError("event GAE inputs must have equal lengths")
    if np.any(elapsed_a < 1):
        raise ValueError("every event must execute at least one primitive transition")
    if not np.isfinite(rewards_a).all() or not np.isfinite(values_a).all():
        raise ValueError("event GAE rewards and values must be finite")
    env_a = (
        np.zeros(len(rewards_a), dtype=np.int64)
        if env_ids is None
        else np.asarray(env_ids, dtype=np.int64)
    )
    if env_a.shape != rewards_a.shape:
        raise ValueError("env_ids must match the event arrays")
    boot = {} if bootstrap_values is None else {int(k): float(v) for k, v in bootstrap_values.items()}
    advantages = np.zeros_like(rewards_a)

    for env_id in np.unique(env_a):
        indices = np.flatnonzero(env_a == env_id)
        next_value = float(boot.get(int(env_id), 0.0))
        next_advantage = 0.0
        for idx in indices[::-1]:
            dt = int(elapsed_a[idx])
            continuation = 0.0 if terminals_a[idx] else 1.0
            discount = float(gamma) ** dt
            trace = float(lambda_10) ** (dt / 10.0)
            delta = rewards_a[idx] + continuation * discount * next_value - values_a[idx]
            advantage = delta + continuation * discount * trace * next_advantage
            advantages[idx] = advantage
            next_value = values_a[idx]
            next_advantage = advantage
    return advantages.astype(np.float32), (advantages + values_a).astype(np.float32)


class DurationPolicyHead(nn.Module):
    """One identically shaped head for factored and autoregressive durations."""

    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, DURATION_CAP),
        )
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=1.0)
                nn.init.zeros_(module.bias)
        nn.init.orthogonal_(self.net[-1].weight, gain=0.01)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


@dataclass
class EventRecord:
    env_id: int
    start_step: int
    state: np.ndarray
    observations: np.ndarray
    context: np.ndarray
    team_skill: int
    agent_skills: np.ndarray
    order: np.ndarray
    sampled_mask: np.ndarray
    sample_Z: bool
    duration_tokens: np.ndarray
    duration_support: np.ndarray
    old_team_log_prob: float
    old_agent_log_probs: np.ndarray
    old_duration_log_probs: np.ndarray
    old_value: float
    reward: float = 0.0
    elapsed: int = 0
    terminal: bool = False


class DurationAgent(HMASDAgent):
    """HMASD adapter with fixed, factored, or ordered-AR commitment durations."""

    def __init__(self, config, log_dir="logs", device=None):
        self._validate_duration_config(config)
        super().__init__(config, log_dir=log_dir, device=device)
        self.duration_mode = str(config.duration_mode)
        self.duration_cap = DURATION_CAP
        self.lambda_10 = float(config.duration_lambda_10)
        self._install_duration_modules()
        self._rebuild_coordinator_optimizer()

        self._duration_events: list[EventRecord] = []
        self._duration_open_events: dict[int, EventRecord] = {}
        self._duration_team_deadline: dict[int, int] = {}
        self._duration_agent_deadlines: dict[int, np.ndarray] = {}
        self._duration_agent_commit_start: dict[int, np.ndarray] = {}
        self._duration_episode_position: dict[int, int] = {}
        self._duration_last_step = None
        self._duration_metrics = self._new_duration_metrics()
        self._replay_failure_snapshot = None
        self._duration_theta0 = [p.detach().clone() for p in self.skill_coordinator.parameters()]
        self._duration_theta0_norm = float(torch.sqrt(sum(
            (p.double() ** 2).sum() for p in self._duration_theta0
        )).item())
        self._prime_invalid_lanes()

    @staticmethod
    def _validate_duration_config(config) -> None:
        mode = str(getattr(config, "duration_mode", ""))
        if mode not in DURATION_MODES:
            raise ValueError(f"duration_mode must be one of {DURATION_MODES}, got {mode!r}")
        checks = (
            (not bool(getattr(config, "use_horizon_window", False)), "HA-CTSE must be disabled"),
            (str(getattr(config, "policy_interruption_mode", "")) == "d2", "D2 metadata mode is required"),
            (int(getattr(config, "k", 0)) == 10, "primitive recurrent chunk k must remain 10"),
            (int(getattr(config, "skill_cap_k_max", 0)) == 10, "member cap must be 10"),
            (int(getattr(config, "team_cap_k_Z", 0)) == 10, "team cap must be 10"),
            (not np.isfinite(float(getattr(config, "interruption_cost_c", 0.0))), "member gap cost must be infinite"),
            (not np.isfinite(float(getattr(config, "interruption_cost_c_Z", 0.0))), "team gap cost must be infinite"),
            (not bool(getattr(config, "use_obsnorm", False)), "observation normalization must be disabled"),
            (not bool(getattr(config, "use_statenorm", True)), "state normalization must be disabled"),
            (bool(getattr(config, "use_valuenorm", False)), "value normalization must be enabled"),
            (float(getattr(config, "coordinator_dropout", 0.0)) == 0.0, "coordinator dropout must be zero"),
            (int(getattr(config, "ppo_epochs", 0)) > 0, "coordinator PPO epochs must be positive"),
            (int(getattr(config, "coordinator_batch_size", 0)) > 0, "coordinator batch size must be positive"),
            (float(getattr(config, "duration_lambda_10", -1.0)) == 0.95, "duration lambda_10 must be .95"),
        )
        failures = [message for ok, message in checks if not ok]
        if failures:
            raise ValueError("invalid duration learning configuration: " + "; ".join(failures))

    @property
    def _context_dim(self) -> int:
        n = int(self.config.n_agents)
        return (int(self.config.n_Z) + 1) + n * (int(self.config.n_z) + 1) + 3 * n + 4

    def _install_duration_modules(self) -> None:
        coordinator = self.skill_coordinator
        hidden = int(self.config.embedding_dim)
        coordinator.duration_context_projection = nn.Linear(self._context_dim, hidden).to(self.device)
        coordinator.event_value_head = nn.Linear(hidden, 1).to(self.device)
        duration_input = (
            2 * hidden
            + int(self.config.n_Z)
            + int(self.config.n_agents) * int(self.config.n_z)
            + 2 * int(self.config.n_agents)
        )
        coordinator.duration_head = DurationPolicyHead(duration_input, hidden).to(self.device)
        nn.init.orthogonal_(coordinator.duration_context_projection.weight, gain=1.0)
        nn.init.zeros_(coordinator.duration_context_projection.bias)
        nn.init.orthogonal_(coordinator.event_value_head.weight, gain=0.01)
        nn.init.zeros_(coordinator.event_value_head.bias)

    def _rebuild_coordinator_optimizer(self) -> None:
        # The inherited optimizer is still empty at construction time.  Rebuilding it
        # here registers the newly attached coordinator modules in one coherent group.
        self.coordinator_optimizer = Adam(
            self.skill_coordinator.parameters(),
            lr=self.config.lr_coordinator,
            weight_decay=self.config.weight_decay,
        )
        if getattr(self.config, "use_lr_decay", False):
            schedule = str(self.config.lr_decay_schedule)
            if schedule == "linear":
                self.coordinator_scheduler = torch.optim.lr_scheduler.LinearLR(
                    self.coordinator_optimizer,
                    start_factor=1.0,
                    end_factor=self.config.coordinator_lr_decay_factor,
                    total_iters=self.config.lr_decay_steps,
                )
            elif schedule == "cosine":
                self.coordinator_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                    self.coordinator_optimizer, T_max=self.config.lr_decay_steps
                )
            else:
                raise ValueError(f"unsupported coordinator lr schedule {schedule!r}")

    def _prime_invalid_lanes(self) -> None:
        invalid = np.full(int(self.config.n_agents), -1, dtype=np.int64)
        for env_id in range(int(getattr(self.config, "num_envs", 1))):
            self.env_timers[env_id] = 0
            self.env_team_skills[env_id] = -1
            self.env_agent_skills[env_id] = invalid.copy()
            self.env_log_probs[env_id] = {}

    @staticmethod
    def _new_duration_metrics() -> dict:
        return {
            "events": 0,
            "stored_events": 0,
            "primitive_steps": 0,
            "eligible_factors": 0,
            "joint_nondegenerate_events": 0,
            "same_label_renewals": 0,
            "cap_boundaries": 0,
            "terminal_boundaries": 0,
            "optimizer_steps": 0,
            "declared_durations": [],
            "executed_durations": [],
            "team_skill_occupancy": {},
            "agent_skill_occupancy": {},
            "replay_pre_max_abs_error": 0.0,
            "replay_grouped_threshold": GROUPED_REPLAY_ABS_TOLERANCE,
            "replay_merged_max_abs_error": 0.0,
            "replay_merged_max_relative_probability_drift": 0.0,
            "replay_merged_relative_probability_threshold": MERGED_REPLAY_RELATIVE_TOLERANCE,
            "replay_post_mean_abs_change": 0.0,
            "approx_kl": 0.0,
            "clip_fraction": 0.0,
            "duration_entropy": 0.0,
            "event_elapsed_total": 0,
            "last_update": {},
            "last_replay_audit": {},
        }

    def _pre_event_context(
        self,
        held_team: np.ndarray,
        held_agents: np.ndarray,
        agent_ages: np.ndarray,
        remaining: np.ndarray,
        eligible: np.ndarray,
        team_ages: np.ndarray,
        team_remaining: np.ndarray,
        team_refresh: np.ndarray,
        env_steps: np.ndarray,
    ) -> np.ndarray:
        batch = held_team.shape[0]
        n = int(self.config.n_agents)
        team_onehot = np.zeros((batch, int(self.config.n_Z) + 1), dtype=np.float32)
        team_index = np.where(held_team >= 0, held_team, int(self.config.n_Z))
        team_onehot[np.arange(batch), team_index] = 1.0
        agent_onehot = np.zeros((batch, n, int(self.config.n_z) + 1), dtype=np.float32)
        agent_index = np.where(held_agents >= 0, held_agents, int(self.config.n_z))
        rows = np.arange(batch)[:, None]
        agents = np.arange(n)[None, :]
        agent_onehot[rows, agents, agent_index] = 1.0
        episode_length = float(max(1, int(getattr(self.config, "episode_length", self.config.rollout_length))))
        return np.concatenate(
            [
                team_onehot,
                agent_onehot.reshape(batch, -1),
                np.clip(agent_ages.astype(np.float32) / DURATION_CAP, 0.0, 1.0),
                np.clip(remaining.astype(np.float32) / DURATION_CAP, 0.0, 1.0),
                eligible.astype(np.float32),
                np.clip(team_ages[:, None].astype(np.float32) / DURATION_CAP, 0.0, 1.0),
                np.clip(team_remaining[:, None].astype(np.float32) / DURATION_CAP, 0.0, 1.0),
                team_refresh[:, None].astype(np.float32),
                np.clip(env_steps[:, None].astype(np.float32) / episode_length, 0.0, 1.0),
            ],
            axis=1,
        ).astype(np.float32, copy=False)

    def _encode_event(
        self, states: torch.Tensor, observations: torch.Tensor, context: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        coordinator = self.skill_coordinator
        entities = coordinator._build_entity_sequence(states.float(), observations.float())
        entities = entities.clone()
        entities[:, 0, :] = entities[:, 0, :] + torch.tanh(
            coordinator.duration_context_projection(context.float())
        )
        processed = coordinator.encoder(entities)
        return processed[:, 0:1, :], processed[:, 1:, :]

    def _assign_skills(
        self,
        states: torch.Tensor,
        observations: torch.Tensor,
        context: torch.Tensor,
        held_team: torch.Tensor,
        held_agents: torch.Tensor,
        sample_Z: torch.Tensor,
        sampled_mask: torch.Tensor,
        deterministic: bool,
    ) -> dict[str, torch.Tensor]:
        coordinator = self.skill_coordinator
        batch, n = held_agents.shape
        device = states.device
        encoded_state, encoded_obs = self._encode_event(states, observations, context)
        agent_range = torch.arange(n, device=device).unsqueeze(0).expand(batch, -1)
        order = torch.argsort(agent_range + n * sampled_mask.long(), dim=1)
        z_logits = coordinator.skill_decoder(encoded_state, encoded_obs)
        z_dist = Categorical(logits=torch.clamp(torch.nan_to_num(z_logits), -50.0, 50.0))
        sampled_team = z_logits.argmax(dim=-1) if deterministic else z_dist.sample()
        team = torch.where(sample_Z, sampled_team, held_team)
        team_log_prob = torch.where(sample_Z, z_dist.log_prob(team), torch.zeros(batch, device=device))

        batch_idx = torch.arange(batch, device=device)
        decoded = torch.zeros(batch, n, dtype=torch.long, device=device)
        agent_log_probs = torch.zeros(batch, n, device=device)
        for position in range(n):
            agent_at = order[:, position]
            query = encoded_obs[batch_idx, agent_at].unsqueeze(1)
            logits = coordinator.skill_decoder(
                encoded_state,
                encoded_obs,
                team,
                decoded[:, :position] if position else None,
                step=position + 1,
                agent_specific_query=query,
            )
            logits = torch.clamp(torch.nan_to_num(logits), -50.0, 50.0)
            dist = Categorical(logits=logits)
            sampled = logits.argmax(dim=-1) if deterministic else dist.sample()
            forced = ~sampled_mask[batch_idx, agent_at]
            token = torch.where(forced, held_agents[batch_idx, agent_at], sampled)
            decoded[:, position] = token
            agent_log_probs[batch_idx, agent_at] = torch.where(
                forced, torch.zeros(batch, device=device), dist.log_prob(token)
            )
        agents = torch.zeros(batch, n, dtype=torch.long, device=device)
        agents[batch_idx.unsqueeze(1), order] = decoded
        value = coordinator.event_value_head(encoded_state.squeeze(1)).squeeze(-1)
        return {
            "team_skills": team,
            "agent_skills": agents,
            "team_log_probs": team_log_prob,
            "agent_log_probs": agent_log_probs,
            "order": order,
            "value": value,
            "encoded_state": encoded_state,
            "encoded_observations": encoded_obs,
        }

    def _duration_features(
        self,
        encoded_state: torch.Tensor,
        encoded_observations: torch.Tensor,
        team_skills: torch.Tensor,
        agent_skills: torch.Tensor,
        agent_idx: int,
        prefix: torch.Tensor,
    ) -> torch.Tensor:
        batch = team_skills.shape[0]
        team_tokens = F.one_hot(team_skills.long(), num_classes=int(self.config.n_Z)).float()
        joint_tokens = F.one_hot(agent_skills.long(), num_classes=int(self.config.n_z)).float().reshape(batch, -1)
        identity = F.one_hot(
            torch.full((batch,), int(agent_idx), device=team_skills.device),
            num_classes=int(self.config.n_agents),
        ).float()
        return torch.cat(
            [
                encoded_state.squeeze(1),
                encoded_observations[:, agent_idx, :],
                team_tokens,
                joint_tokens,
                identity,
                prefix,
            ],
            dim=-1,
        )

    def _sample_durations(
        self,
        assignment: dict[str, torch.Tensor],
        sampled_mask: torch.Tensor,
        support: torch.Tensor,
        deterministic: bool,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        batch, n = sampled_mask.shape
        device = sampled_mask.device
        tokens = torch.zeros(batch, n, dtype=torch.long, device=device)
        log_probs = torch.zeros(batch, n, device=device)
        entropies = torch.zeros(batch, n, device=device)
        prefix = torch.zeros(batch, n, device=device)
        if self.duration_mode == "fixed":
            tokens = torch.where(sampled_mask, support, tokens)
            return tokens, log_probs, entropies

        for agent_idx in range(n):
            active = sampled_mask[:, agent_idx]
            if not torch.any(active):
                continue
            features = self._duration_features(
                assignment["encoded_state"], assignment["encoded_observations"],
                assignment["team_skills"], assignment["agent_skills"], agent_idx, prefix,
            )
            logits = mask_duration_logits(
                self.skill_coordinator.duration_head(features), support[:, agent_idx].clamp(min=1)
            )
            dist = Categorical(logits=logits)
            chosen = logits.argmax(dim=-1) + 1 if deterministic else dist.sample() + 1
            forced = support[:, agent_idx] == 1
            chosen = torch.where(forced, torch.ones_like(chosen), chosen)
            tokens[:, agent_idx] = torch.where(active, chosen, torch.zeros_like(chosen))
            log_probs[:, agent_idx] = torch.where(
                active & ~forced, dist.log_prob(chosen - 1), torch.zeros(batch, device=device)
            )
            entropies[:, agent_idx] = torch.where(
                active & ~forced, dist.entropy(), torch.zeros(batch, device=device)
            )
            if self.duration_mode == "ar":
                prefix[:, agent_idx] = torch.where(active, chosen.float() / DURATION_CAP, prefix[:, agent_idx])
        return tokens, log_probs, entropies

    def _batched_assign_skills_d2(
        self, states_batch, observations_batch, env_steps_batch, dones_batch, deterministic=False
    ):
        states_np = np.asarray(states_batch)
        observations_np = np.asarray(observations_batch)
        env_steps = np.asarray(env_steps_batch, dtype=np.int64).reshape(-1)
        dones = np.asarray(dones_batch, dtype=np.bool_).reshape(-1)
        batch = len(env_steps)
        n = int(self.config.n_agents)

        held_team = np.asarray([self.env_team_skills.get(i, -1) for i in range(batch)], dtype=np.int64)
        held_agents = np.asarray([
            self.env_agent_skills.get(i, np.full(n, -1, dtype=np.int64)) for i in range(batch)
        ], dtype=np.int64)
        reset = (env_steps == 0) | dones | (held_team < 0) | np.any(held_agents < 0, axis=1)
        team_deadline = np.asarray([
            self._duration_team_deadline.get(i, int(env_steps[i])) for i in range(batch)
        ], dtype=np.int64)
        agent_deadlines = np.asarray([
            self._duration_agent_deadlines.get(i, np.full(n, int(env_steps[i]), dtype=np.int64))
            for i in range(batch)
        ], dtype=np.int64)
        commit_start = np.asarray([
            self._duration_agent_commit_start.get(i, np.full(n, int(env_steps[i]), dtype=np.int64))
            for i in range(batch)
        ], dtype=np.int64)
        team_refresh = reset | (env_steps >= team_deadline)
        refreshed_deadline = np.where(team_refresh, env_steps + DURATION_CAP, team_deadline)
        sampled_mask = team_refresh[:, None] | (env_steps[:, None] >= agent_deadlines)
        sample_Z = team_refresh.copy()
        decision = sampled_mask.any(axis=1)
        remaining_cap = refreshed_deadline - env_steps
        support = np.where(sampled_mask, remaining_cap[:, None], 0).astype(np.int64)
        if np.any((support[sampled_mask] < 1) | (support[sampled_mask] > DURATION_CAP)):
            raise RuntimeError("duration support escaped the active team window")

        held_team_context = held_team.copy()
        held_agents_context = held_agents.copy()
        held_team_context[reset] = -1
        held_agents_context[reset] = -1
        agent_ages = np.maximum(env_steps[:, None] - commit_start, 0)
        remaining = np.maximum(agent_deadlines - env_steps[:, None], 0)
        team_ages = np.where(reset, 0, np.maximum(DURATION_CAP - (team_deadline - env_steps), 0))
        context = self._pre_event_context(
            held_team_context, held_agents_context, agent_ages, remaining, sampled_mask,
            team_ages, remaining_cap, team_refresh, env_steps,
        )

        out_team = held_team.copy()
        out_agents = held_agents.copy()
        log_probs = [self.env_log_probs.get(i, {}) for i in range(batch)]
        order = np.tile(np.arange(n, dtype=np.int64), (batch, 1))
        duration_tokens = np.zeros((batch, n), dtype=np.int64)
        duration_log_probs = np.zeros((batch, n), dtype=np.float32)
        duration_entropies = np.zeros((batch, n), dtype=np.float32)
        common_values = np.zeros(batch, dtype=np.float32)

        indices = np.flatnonzero(decision)
        if indices.size:
            states_t = torch.as_tensor(states_np[indices], dtype=torch.float32, device=self.device)
            obs_t = torch.as_tensor(observations_np[indices], dtype=torch.float32, device=self.device)
            context_t = torch.as_tensor(context[indices], dtype=torch.float32, device=self.device)
            with torch.no_grad():
                assignment = self._assign_skills(
                    states_t, obs_t, context_t,
                    torch.as_tensor(held_team[indices], dtype=torch.long, device=self.device),
                    torch.as_tensor(held_agents[indices], dtype=torch.long, device=self.device),
                    torch.as_tensor(sample_Z[indices], dtype=torch.bool, device=self.device),
                    torch.as_tensor(sampled_mask[indices], dtype=torch.bool, device=self.device),
                    deterministic,
                )
                durations_t, duration_lp_t, duration_entropy_t = self._sample_durations(
                    assignment,
                    torch.as_tensor(sampled_mask[indices], dtype=torch.bool, device=self.device),
                    torch.as_tensor(support[indices], dtype=torch.long, device=self.device),
                    deterministic,
                )
                raw_value = assignment["value"]
                if self.value_norm_coordinator is not None:
                    raw_value = self._denormalize_values(raw_value, self.value_norm_coordinator)

            assigned_team = assignment["team_skills"].cpu().numpy()
            assigned_agents = assignment["agent_skills"].cpu().numpy()
            team_lp = assignment["team_log_probs"].cpu().numpy()
            agent_lp = assignment["agent_log_probs"].cpu().numpy()
            order_i = assignment["order"].cpu().numpy()
            durations_i = durations_t.cpu().numpy()
            duration_lp_i = duration_lp_t.cpu().numpy()
            duration_entropy_i = duration_entropy_t.cpu().numpy()
            raw_value_i = raw_value.cpu().numpy()

            for local, env_id in enumerate(indices.tolist()):
                old_agents = held_agents[env_id].copy()
                out_team[env_id] = int(assigned_team[local])
                out_agents[env_id] = assigned_agents[local]
                order[env_id] = order_i[local]
                duration_tokens[env_id] = durations_i[local]
                duration_log_probs[env_id] = duration_lp_i[local]
                duration_entropies[env_id] = duration_entropy_i[local]
                common_values[env_id] = float(raw_value_i[local])
                log_probs[env_id] = {
                    "team_log_prob": float(team_lp[local]),
                    "agent_log_probs": agent_lp[local].astype(np.float32).tolist(),
                    "state_value": float(raw_value_i[local]),
                    "agent_values": [float(raw_value_i[local])] * n,
                    "duration_log_probs": duration_lp_i[local].astype(np.float32).tolist(),
                    "duration_tokens": durations_i[local].astype(np.int64).tolist(),
                    "duration_support": support[env_id].astype(np.int64).tolist(),
                    "duration_entropy": duration_entropy_i[local].astype(np.float32).tolist(),
                    "duration_context": context[env_id].copy(),
                    "duration_state": np.asarray(states_np[env_id], dtype=np.float32).copy(),
                    "duration_observations": np.asarray(observations_np[env_id], dtype=np.float32).copy(),
                    "duration_order": order_i[local].copy(),
                    "duration_sampled_mask": sampled_mask[env_id].copy(),
                    "duration_sample_Z": bool(sample_Z[env_id]),
                }
                renewed = sampled_mask[env_id] & (old_agents >= 0) & (assigned_agents[local] == old_agents)
                self._duration_metrics["same_label_renewals"] += int(renewed.sum())
                self._duration_metrics["declared_durations"].extend(
                    durations_i[local][sampled_mask[env_id]].astype(int).tolist()
                )
                if self.duration_mode != "fixed" and np.sum(
                    sampled_mask[env_id] & (support[env_id] > 1)
                ) >= 2:
                    self._duration_metrics["joint_nondegenerate_events"] += 1
                self._duration_metrics["eligible_factors"] += int(sampled_mask[env_id].sum())
                self._duration_metrics["events"] += 1
                if team_refresh[env_id] and not reset[env_id]:
                    self._duration_metrics["cap_boundaries"] += 1

        exec_ages = np.where(sampled_mask, 0, agent_ages).astype(np.int64)
        exec_team_ages = np.where(sample_Z, 0, team_ages).astype(np.int64)
        agent_cause = np.where(sampled_mask, self.D2_CAUSE_CAP, self.D2_CAUSE_NONE).astype(np.int64)
        team_cause = np.where(sample_Z, self.D2_CAUSE_TEAM_CAP, self.D2_CAUSE_NONE).astype(np.int64)
        agent_cause[reset] = self.D2_CAUSE_RESET
        team_cause[reset] = self.D2_CAUSE_RESET

        for env_id in range(batch):
            if decision[env_id]:
                for agent_idx in np.flatnonzero(sampled_mask[env_id]):
                    if held_agents[env_id, agent_idx] >= 0:
                        self._duration_metrics["executed_durations"].append(
                            int(env_steps[env_id] - commit_start[env_id, agent_idx])
                        )
                    commit_start[env_id, agent_idx] = env_steps[env_id]
                    agent_deadlines[env_id, agent_idx] = (
                        env_steps[env_id] + int(duration_tokens[env_id, agent_idx])
                    )
                self.env_timers[env_id] = 0
            else:
                self.env_timers[env_id] = self.env_timers.get(env_id, 0) + 1
            self._duration_team_deadline[env_id] = int(refreshed_deadline[env_id])
            self._duration_agent_deadlines[env_id] = agent_deadlines[env_id].copy()
            self._duration_agent_commit_start[env_id] = commit_start[env_id].copy()
            self._duration_episode_position[env_id] = int(env_steps[env_id])
            self.env_team_skills[env_id] = int(out_team[env_id])
            self.env_agent_skills[env_id] = out_agents[env_id].copy()
            self.env_log_probs[env_id] = log_probs[env_id]
            self.env_skill_ages[env_id] = exec_ages[env_id] + 1
            self.env_team_ages[env_id] = int(exec_team_ages[env_id]) + 1
            self._duration_metrics["primitive_steps"] += 1
            team_key = str(int(out_team[env_id]))
            self._duration_metrics["team_skill_occupancy"][team_key] = (
                self._duration_metrics["team_skill_occupancy"].get(team_key, 0) + 1
            )
            for skill in np.asarray(out_agents[env_id], dtype=np.int64):
                skill_key = str(int(skill))
                self._duration_metrics["agent_skill_occupancy"][skill_key] = (
                    self._duration_metrics["agent_skill_occupancy"].get(skill_key, 0) + 1
                )

        self._d2_last_step = {
            "decision": decision.copy(),
            "team_decision": team_refresh.copy(),
            "sampled_mask": sampled_mask.copy(),
            "sample_Z": sample_Z.copy(),
            "order": order.copy(),
            "agent_ages": exec_ages.copy(),
            "team_ages": exec_team_ages.copy(),
            "agent_cause": agent_cause.copy(),
            "team_cause": team_cause.copy(),
        }
        for env_id in range(batch):
            self.env_d2_last_decision[env_id] = {
                "decision": bool(decision[env_id]),
                "team_decision": bool(team_refresh[env_id]),
                "sampled_mask": sampled_mask[env_id].copy(),
                "sample_Z": bool(sample_Z[env_id]),
                "order": order[env_id].copy(),
                "agent_ages": exec_ages[env_id].copy(),
                "team_age": int(exec_team_ages[env_id]),
                "agent_cause": agent_cause[env_id].copy(),
                "team_cause": int(team_cause[env_id]),
            }
        return out_team, out_agents, log_probs

    def _new_event_record(self, env_id: int, step: int, d2_step: dict) -> EventRecord:
        log = self.env_log_probs[env_id]
        required = (
            "duration_context", "duration_state", "duration_observations", "duration_tokens",
            "duration_support", "duration_log_probs", "duration_order", "duration_sampled_mask",
        )
        missing = [key for key in required if key not in log]
        if missing:
            raise RuntimeError(f"duration event metadata missing {missing}")
        return EventRecord(
            env_id=int(env_id), start_step=int(step),
            state=np.asarray(log["duration_state"], dtype=np.float32).copy(),
            observations=np.asarray(log["duration_observations"], dtype=np.float32).copy(),
            context=np.asarray(log["duration_context"], dtype=np.float32).copy(),
            team_skill=int(self.env_team_skills[env_id]),
            agent_skills=np.asarray(self.env_agent_skills[env_id], dtype=np.int64).copy(),
            order=np.asarray(log["duration_order"], dtype=np.int64).copy(),
            sampled_mask=np.asarray(log["duration_sampled_mask"], dtype=np.bool_).copy(),
            sample_Z=bool(d2_step["sample_Z"]),
            duration_tokens=np.asarray(log["duration_tokens"], dtype=np.int64).copy(),
            duration_support=np.asarray(log["duration_support"], dtype=np.int64).copy(),
            old_team_log_prob=float(log["team_log_prob"]),
            old_agent_log_probs=np.asarray(log["agent_log_probs"], dtype=np.float32).copy(),
            old_duration_log_probs=np.asarray(log["duration_log_probs"], dtype=np.float32).copy(),
            old_value=float(log["state_value"]),
        )

    def _close_event(self, env_id: int, terminal: bool) -> None:
        event = self._duration_open_events.pop(env_id, None)
        if event is None:
            return
        if event.elapsed < 1:
            raise RuntimeError("a duration event closed without a primitive transition")
        event.terminal = bool(terminal)
        self._duration_events.append(event)
        self._duration_metrics["stored_events"] += 1
        self._duration_metrics["event_elapsed_total"] += int(event.elapsed)

    def _d2_store_transition(self, env_id, rollout_step_idx, reward, done, d2_step):
        if rollout_step_idx is None:
            raise ValueError("duration event storage requires rollout_step_idx")
        step = int(rollout_step_idx)
        if bool(d2_step["decision"]):
            self._close_event(int(env_id), terminal=False)
            self._duration_open_events[int(env_id)] = self._new_event_record(int(env_id), step, d2_step)

        log = self.env_log_probs.get(int(env_id), {})
        self.rollout_buffer.add_d2_step(
            env_idx=int(env_id), time_step=step,
            agent_age=d2_step["agent_ages"], team_age=d2_step["team_age"],
            decision=bool(d2_step["decision"]),
            team_skill=int(self.env_team_skills.get(int(env_id), -1)),
            agent_skills=np.asarray(self.env_agent_skills.get(int(env_id)), dtype=np.int64),
            sampled_mask=d2_step["sampled_mask"], sample_Z=bool(d2_step["sample_Z"]),
            order=d2_step["order"], team_log_prob=float(log.get("team_log_prob", 0.0)),
            agent_log_probs=np.asarray(log.get("agent_log_probs", [0.0] * self.config.n_agents)),
            team_value=float(log.get("state_value", 0.0)),
            agent_values=np.full(self.config.n_agents, float(log.get("state_value", 0.0))),
            agent_cause=d2_step["agent_cause"], team_cause=d2_step["team_cause"],
        )

        event = self._duration_open_events.get(int(env_id))
        if event is None:
            raise RuntimeError(f"lane {env_id} executed without an open duration event")
        event.reward += (float(self.config.gamma) ** event.elapsed) * float(reward)
        event.elapsed += 1

        terminal = bool(np.any(done)) if hasattr(done, "__iter__") else bool(done)
        if terminal:
            self._close_event(int(env_id), terminal=True)
            self._duration_metrics["terminal_boundaries"] += 1
            starts = self._duration_agent_commit_start.get(int(env_id))
            if starts is not None:
                final_time = int(self._duration_episode_position.get(int(env_id), step)) + 1
                self._duration_metrics["executed_durations"].extend(
                    (final_time - np.asarray(starts, dtype=np.int64)).astype(int).tolist()
                )
        return True

    def _evaluate_events(self, events: Sequence[EventRecord]) -> dict[str, torch.Tensor]:
        device = self.device
        states = torch.as_tensor(np.stack([e.state for e in events]), dtype=torch.float32, device=device)
        observations = torch.as_tensor(
            np.stack([e.observations for e in events]), dtype=torch.float32, device=device
        )
        contexts = torch.as_tensor(np.stack([e.context for e in events]), dtype=torch.float32, device=device)
        team = torch.as_tensor([e.team_skill for e in events], dtype=torch.long, device=device)
        agents = torch.as_tensor(np.stack([e.agent_skills for e in events]), dtype=torch.long, device=device)
        order = torch.as_tensor(np.stack([e.order for e in events]), dtype=torch.long, device=device)
        sampled_mask = torch.as_tensor(
            np.stack([e.sampled_mask for e in events]), dtype=torch.bool, device=device
        )
        sample_Z = torch.as_tensor([e.sample_Z for e in events], dtype=torch.bool, device=device)
        duration_tokens = torch.as_tensor(
            np.stack([e.duration_tokens for e in events]), dtype=torch.long, device=device
        )
        support = torch.as_tensor(
            np.stack([e.duration_support for e in events]), dtype=torch.long, device=device
        )
        encoded_state, encoded_obs = self._encode_event(states, observations, contexts)
        coordinator = self.skill_coordinator
        batch, n = agents.shape
        batch_idx = torch.arange(batch, device=device)

        team_dist = Categorical(logits=torch.clamp(torch.nan_to_num(
            coordinator.skill_decoder(encoded_state, encoded_obs)), -50.0, 50.0
        ))
        team_log_probs = torch.where(sample_Z, team_dist.log_prob(team), torch.zeros(batch, device=device))
        team_entropy = torch.where(sample_Z, team_dist.entropy(), torch.zeros(batch, device=device))
        ordered_skills = torch.gather(agents, 1, order)
        agent_log_probs = torch.zeros(batch, n, device=device)
        agent_entropies = torch.zeros(batch, n, device=device)
        for position in range(n):
            agent_at = order[:, position]
            logits = coordinator.skill_decoder(
                encoded_state, encoded_obs, team,
                ordered_skills[:, :position] if position else None,
                step=position + 1,
                agent_specific_query=encoded_obs[batch_idx, agent_at].unsqueeze(1),
            )
            dist = Categorical(logits=torch.clamp(torch.nan_to_num(logits), -50.0, 50.0))
            token = ordered_skills[:, position]
            active = sampled_mask[batch_idx, agent_at]
            agent_log_probs[batch_idx, agent_at] = torch.where(
                active, dist.log_prob(token), torch.zeros(batch, device=device)
            )
            agent_entropies[batch_idx, agent_at] = torch.where(
                active, dist.entropy(), torch.zeros(batch, device=device)
            )

        duration_log_probs = torch.zeros(batch, n, device=device)
        duration_entropies = torch.zeros(batch, n, device=device)
        prefix = torch.zeros(batch, n, device=device)
        if self.duration_mode != "fixed":
            for agent_idx in range(n):
                active = sampled_mask[:, agent_idx]
                if not torch.any(active):
                    continue
                logits = mask_duration_logits(
                    coordinator.duration_head(self._duration_features(
                        encoded_state, encoded_obs, team, agents, agent_idx, prefix
                    )),
                    support[:, agent_idx].clamp(min=1),
                )
                dist = Categorical(logits=logits)
                token = duration_tokens[:, agent_idx]
                forced = support[:, agent_idx] == 1
                duration_log_probs[:, agent_idx] = torch.where(
                    active & ~forced, dist.log_prob((token - 1).clamp(min=0)),
                    torch.zeros(batch, device=device),
                )
                duration_entropies[:, agent_idx] = torch.where(
                    active & ~forced, dist.entropy(), torch.zeros(batch, device=device)
                )
                if self.duration_mode == "ar":
                    prefix[:, agent_idx] = torch.where(
                        active, token.float() / DURATION_CAP, prefix[:, agent_idx]
                    )
        return {
            "team_log_probs": team_log_probs,
            "agent_log_probs": agent_log_probs,
            "duration_log_probs": duration_log_probs,
            "team_entropy": team_entropy,
            "agent_entropies": agent_entropies,
            "duration_entropies": duration_entropies,
            "values": coordinator.event_value_head(encoded_state.squeeze(1)).squeeze(-1),
        }

    def _factor_tensors(self, events: Sequence[EventRecord], device) -> tuple[torch.Tensor, torch.Tensor]:
        old = []
        masks = []
        for event in events:
            old.append(np.concatenate([
                np.asarray([event.old_team_log_prob], dtype=np.float32),
                event.old_agent_log_probs.astype(np.float32),
                event.old_duration_log_probs.astype(np.float32),
            ]))
            duration_active = (
                event.sampled_mask
                & (event.duration_support > 1)
                & (event.duration_tokens > 0)
                & (self.duration_mode != "fixed")
            )
            masks.append(np.concatenate([
                np.asarray([event.sample_Z], dtype=np.bool_),
                event.sampled_mask.astype(np.bool_),
                duration_active.astype(np.bool_),
            ]))
        return (
            torch.as_tensor(np.stack(old), dtype=torch.float32, device=device),
            torch.as_tensor(np.stack(masks), dtype=torch.bool, device=device),
        )

    @staticmethod
    def _flatten_new_factors(evaluation: dict[str, torch.Tensor]) -> torch.Tensor:
        return torch.cat([
            evaluation["team_log_probs"].unsqueeze(1),
            evaluation["agent_log_probs"],
            evaluation["duration_log_probs"],
        ], dim=1)

    @staticmethod
    def _flatten_entropies(evaluation: dict[str, torch.Tensor]) -> torch.Tensor:
        return torch.cat([
            evaluation["team_entropy"].unsqueeze(1),
            evaluation["agent_entropies"],
            evaluation["duration_entropies"],
        ], dim=1)

    def _replay_backend_facts(self) -> dict:
        parameter = next(self.skill_coordinator.parameters())
        facts = {
            "torch_version": torch.__version__,
            "device": str(self.device),
            "coordinator_dtype": str(parameter.dtype),
            "coordinator_training": bool(self.skill_coordinator.training),
            "grad_enabled_at_capture": bool(torch.is_grad_enabled()),
            "float32_matmul_precision": torch.get_float32_matmul_precision(),
        }
        if torch.device(self.device).type == "cuda":
            facts.update({
                "cuda_version": torch.version.cuda,
                "cuda_device_name": torch.cuda.get_device_name(self.device),
                "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
                "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
                "flash_sdp_enabled": bool(torch.backends.cuda.flash_sdp_enabled()),
                "mem_efficient_sdp_enabled": bool(torch.backends.cuda.mem_efficient_sdp_enabled()),
                "math_sdp_enabled": bool(torch.backends.cuda.math_sdp_enabled()),
            })
        return facts

    def _freeze_config(self) -> dict:
        values = {}
        for name in dir(self.config):
            if name.startswith("_"):
                continue
            try:
                value = getattr(self.config, name)
            except Exception:
                continue
            if callable(value):
                continue
            try:
                values[name] = deepcopy(value)
            except Exception:
                values[name] = repr(value)
        return {
            "class_module": self.config.__class__.__module__,
            "class_name": self.config.__class__.__qualname__,
            "values": values,
        }

    @staticmethod
    def _audit_offending_indices(condition: torch.Tensor, limit: int = 64) -> list[list[int]]:
        indices = torch.nonzero(condition, as_tuple=False).detach().cpu().tolist()
        return [[int(value) for value in row] for row in indices[:limit]]

    def _record_replay_audit(self, facts: dict) -> None:
        grouped = float(facts.get("grouped_max_abs_logprob_error", 0.0))
        merged_abs = float(facts.get("merged_max_abs_logprob_error", 0.0))
        merged_relative = float(facts.get("merged_max_relative_probability_drift", 0.0))
        self._duration_metrics["replay_pre_max_abs_error"] = max(
            float(self._duration_metrics["replay_pre_max_abs_error"]), grouped
        )
        self._duration_metrics["replay_merged_max_abs_error"] = max(
            float(self._duration_metrics["replay_merged_max_abs_error"]), merged_abs
        )
        self._duration_metrics["replay_merged_max_relative_probability_drift"] = max(
            float(self._duration_metrics["replay_merged_max_relative_probability_drift"]),
            merged_relative,
        )
        self._duration_metrics["last_replay_audit"] = deepcopy(facts)

    def _raise_replay_audit(
        self,
        message: str,
        reason: str,
        facts: dict,
        events: Sequence[EventRecord],
        old_factors: torch.Tensor,
        factor_mask: torch.Tensor,
        group_ids: Sequence[int],
        offending_indices: Sequence[Sequence[int]],
        cause: BaseException | None = None,
    ) -> None:
        failure_facts = deepcopy(facts)
        failure_facts.update({
            "status": "failed",
            "reason": reason,
            "message": message,
            "offending_indices": [list(map(int, row)) for row in offending_indices],
        })
        self._record_replay_audit(failure_facts)
        try:
            self._replay_failure_snapshot = {
                "schema": "joint_duration_replay_failure_v1",
                "failure": deepcopy(failure_facts),
                "backend": self._replay_backend_facts(),
                "duration_mode": self.duration_mode,
                "config": self._freeze_config(),
                "coordinator_state_dict": {
                    name: tensor.detach().cpu().clone()
                    for name, tensor in self.skill_coordinator.state_dict().items()
                },
                "event_records": [asdict(event) for event in events],
                "factor_old_log_probabilities": old_factors.detach().cpu().clone(),
                "factor_masks": factor_mask.detach().cpu().clone(),
                "collection_group_start_steps": torch.as_tensor(
                    list(group_ids), dtype=torch.int64
                ),
                "collection_group_env_ids": torch.as_tensor(
                    [int(event.env_id) for event in events], dtype=torch.int64
                ),
                "collection_group_identities": torch.as_tensor(
                    [(int(event.start_step), int(event.env_id)) for event in events],
                    dtype=torch.int64,
                ),
                "collection_replay_record_indices": torch.as_tensor(
                    sorted(
                        range(len(events)),
                        key=lambda index: (
                            int(events[index].start_step), int(events[index].env_id)
                        ),
                    ),
                    dtype=torch.int64,
                ),
            }
        except Exception as capture_error:
            # Diagnostic persistence must never replace the primary audit failure.
            self._replay_failure_snapshot = {
                "schema": "joint_duration_replay_failure_v1",
                "failure": deepcopy(failure_facts),
                "duration_mode": self.duration_mode,
                "snapshot_capture_error": repr(capture_error),
            }
        error = ReplayAuditError(message, reason=reason, facts=failure_facts)
        if cause is not None:
            raise error from cause
        raise error

    def replay_failure_payload(self):
        """Return the frozen diagnostic snapshot only after a replay audit failure."""
        return self._replay_failure_snapshot

    def audit_event_replay(self, events: Sequence[EventRecord] | None = None) -> dict:
        """Audit collection-group identity and merged-batch probability drift.

        Collection groups are reconstructed by ``start_step`` and evaluated in
        ascending environment order, then scattered back to the original
        closure-time record order.  The merged diagnostic retains the actual
        coordinator batch size but does not sample, permute, or change model
        mode, precision, parameters, optimizer state, or RNG state.
        """
        records = list(self._duration_events if events is None else events)
        if not records:
            facts = {
                "status": "passed",
                "event_count": 0,
                "factor_count": 0,
                "collection_group_count": 0,
                "merged_batch_size": int(self.config.coordinator_batch_size),
                "grouped_max_abs_logprob_error": 0.0,
                "grouped_abs_logprob_threshold": GROUPED_REPLAY_ABS_TOLERANCE,
                "merged_max_abs_logprob_error": 0.0,
                "merged_max_relative_probability_drift": 0.0,
                "merged_relative_probability_threshold": MERGED_REPLAY_RELATIVE_TOLERANCE,
            }
            self._record_replay_audit(facts)
            return facts

        old_factors, factor_mask = self._factor_tensors(records, self.device)
        group_ids = [int(event.start_step) for event in records]
        base_facts = {
            "event_count": len(records),
            "factor_count": int(factor_mask.sum().item()),
            "merged_batch_size": int(self.config.coordinator_batch_size),
            "grouped_abs_logprob_threshold": GROUPED_REPLAY_ABS_TOLERANCE,
            "merged_relative_probability_threshold": MERGED_REPLAY_RELATIVE_TOLERANCE,
            "grouped_max_abs_logprob_error": 0.0,
            "merged_max_abs_logprob_error": 0.0,
            "merged_max_relative_probability_drift": 0.0,
        }

        groups: dict[int, list[tuple[int, EventRecord]]] = {}
        seen = set()
        for original_index, event in enumerate(records):
            identity = (int(event.start_step), int(event.env_id))
            if identity in seen:
                self._raise_replay_audit(
                    f"duplicate replay collection identity start_step={identity[0]} env_id={identity[1]}",
                    "duplicate_collection_identity", base_facts, records, old_factors,
                    factor_mask, group_ids, [[original_index]],
                )
            seen.add(identity)
            groups.setdefault(identity[0], []).append((original_index, event))
        base_facts["collection_group_count"] = len(groups)

        grouped_new = torch.empty_like(old_factors)
        with torch.no_grad():
            for start_step in sorted(groups):
                group = sorted(groups[start_step], key=lambda row: row[1].env_id)
                group_events = [event for _index, event in group]
                try:
                    evaluated = self._flatten_new_factors(self._evaluate_events(group_events))
                except Exception as scoring_error:
                    scoring_facts = deepcopy(base_facts)
                    scoring_facts.update({
                        "scoring_phase": "collection_group",
                        "scoring_group_start_step": int(start_step),
                        "scoring_exception_type": type(scoring_error).__name__,
                        "scoring_exception_message": str(scoring_error),
                    })
                    self._raise_replay_audit(
                        "collection-group replay scoring failed: "
                        f"{type(scoring_error).__name__}: {scoring_error}",
                        "grouped_scoring_exception", scoring_facts, records, old_factors,
                        factor_mask, group_ids,
                        [[original_index, -1] for original_index, _event in group],
                        cause=scoring_error,
                    )
                for row, (original_index, _event) in enumerate(group):
                    grouped_new[original_index] = evaluated[row]

        active_old = old_factors[factor_mask]
        active_grouped = grouped_new[factor_mask]
        finite_old = torch.isfinite(active_old)
        finite_grouped = torch.isfinite(active_grouped)
        if not bool(finite_old.all()) or not bool(finite_grouped.all()):
            bad_full = (~torch.isfinite(old_factors) | ~torch.isfinite(grouped_new)) & factor_mask
            self._raise_replay_audit(
                "nonfinite active factor score in collection-group replay",
                "nonfinite_grouped_factor", base_facts, records, old_factors, factor_mask,
                group_ids, self._audit_offending_indices(bad_full),
            )
        grouped_error = torch.abs(active_grouped - active_old)
        grouped_max = float(grouped_error.max().item()) if grouped_error.numel() else 0.0
        base_facts["grouped_max_abs_logprob_error"] = grouped_max
        if grouped_max > GROUPED_REPLAY_ABS_TOLERANCE:
            full_error = torch.zeros_like(old_factors)
            full_error[factor_mask] = torch.abs(grouped_new[factor_mask] - old_factors[factor_mask])
            self._raise_replay_audit(
                f"collection-group replay mismatch {grouped_max:.9g} > "
                f"{GROUPED_REPLAY_ABS_TOLERANCE:.9g}",
                "grouped_identity_mismatch", base_facts, records, old_factors, factor_mask,
                group_ids,
                self._audit_offending_indices(
                    (full_error > GROUPED_REPLAY_ABS_TOLERANCE) & factor_mask
                ),
            )

        merged_abs_max = 0.0
        merged_relative_max = 0.0
        audit_batch = int(self.config.coordinator_batch_size)
        with torch.no_grad():
            for start in range(0, len(records), audit_batch):
                stop = min(len(records), start + audit_batch)
                try:
                    merged_new = self._flatten_new_factors(
                        self._evaluate_events(records[start:stop])
                    )
                except Exception as scoring_error:
                    scoring_facts = deepcopy(base_facts)
                    scoring_facts.update({
                        "scoring_phase": "merged_batch",
                        "scoring_batch_start": int(start),
                        "scoring_batch_stop": int(stop),
                        "scoring_exception_type": type(scoring_error).__name__,
                        "scoring_exception_message": str(scoring_error),
                    })
                    self._raise_replay_audit(
                        "merged replay scoring failed: "
                        f"{type(scoring_error).__name__}: {scoring_error}",
                        "merged_scoring_exception", scoring_facts, records, old_factors,
                        factor_mask, group_ids,
                        [[record_index, -1] for record_index in range(start, stop)],
                        cause=scoring_error,
                    )
                merged_old = old_factors[start:stop]
                merged_mask = factor_mask[start:stop]
                active_merged_old = merged_old[merged_mask]
                active_merged_new = merged_new[merged_mask]
                if not bool(torch.isfinite(active_merged_old).all()) or not bool(
                    torch.isfinite(active_merged_new).all()
                ):
                    bad_local = (
                        ~torch.isfinite(merged_old) | ~torch.isfinite(merged_new)
                    ) & merged_mask
                    bad = self._audit_offending_indices(bad_local)
                    shifted = [[row + start, factor] for row, factor in bad]
                    self._raise_replay_audit(
                        "nonfinite active factor score in merged replay",
                        "nonfinite_merged_factor", base_facts, records, old_factors,
                        factor_mask, group_ids, shifted,
                    )
                difference = active_merged_new - active_merged_old
                relative = torch.abs(torch.expm1(difference))
                if not bool(torch.isfinite(relative).all()):
                    self._raise_replay_audit(
                        "nonfinite relative factor probability drift in merged replay",
                        "nonfinite_merged_probability_drift", base_facts, records,
                        old_factors, factor_mask, group_ids, [[start]],
                    )
                if difference.numel():
                    merged_abs_max = max(merged_abs_max, float(torch.abs(difference).max().item()))
                    merged_relative_max = max(merged_relative_max, float(relative.max().item()))
                if bool((relative > MERGED_REPLAY_RELATIVE_TOLERANCE).any()):
                    full_relative = torch.zeros_like(merged_old)
                    full_relative[merged_mask] = relative
                    bad = self._audit_offending_indices(
                        (full_relative > MERGED_REPLAY_RELATIVE_TOLERANCE) & merged_mask
                    )
                    shifted = [[row + start, factor] for row, factor in bad]
                    base_facts["merged_max_abs_logprob_error"] = merged_abs_max
                    base_facts["merged_max_relative_probability_drift"] = merged_relative_max
                    self._raise_replay_audit(
                        f"merged replay relative probability drift {merged_relative_max:.9g} > "
                        f"{MERGED_REPLAY_RELATIVE_TOLERANCE:.9g}",
                        "merged_probability_drift", base_facts, records, old_factors,
                        factor_mask, group_ids, shifted,
                    )

        base_facts.update({
            "status": "passed",
            "merged_max_abs_logprob_error": merged_abs_max,
            "merged_max_relative_probability_drift": merged_relative_max,
        })
        self._record_replay_audit(base_facts)
        return deepcopy(base_facts)

    def update_coordinator(self, num_steps, bootstrap_values=None):
        if bootstrap_values is not None:
            raise ValueError("terminal-aligned duration updates do not accept high-level bootstrap values")
        if self._duration_open_events:
            raise ValueError("duration update refuses a nonterminal rollout cutoff")
        events = list(self._duration_events)
        if not events:
            return (0.0,) * 9
        last_by_env: dict[int, EventRecord] = {}
        for event in events:
            last_by_env[event.env_id] = event
        if not all(event.terminal for event in last_by_env.values()):
            raise ValueError("every lane must end at a native terminal boundary")

        # This audit must precede ValueNorm mutation and every optimizer step.
        audit_facts = self.audit_event_replay(events)

        advantages_np, returns_np = compute_event_gae(
            [e.reward for e in events], [e.old_value for e in events], [e.elapsed for e in events],
            [e.terminal for e in events], gamma=float(self.config.gamma), lambda_10=self.lambda_10,
            env_ids=[e.env_id for e in events],
        )
        advantages = torch.as_tensor(advantages_np, dtype=torch.float32, device=self.device)
        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)
        returns = torch.as_tensor(returns_np, dtype=torch.float32, device=self.device)
        if self.value_norm_coordinator is not None:
            self.value_norm_coordinator.update(returns_np)
        value_norm = self._value_norm_tensors(self.value_norm_coordinator)
        old_factors, factor_mask = self._factor_tensors(events, self.device)

        event_count = len(events)
        audit_batch = int(self.config.coordinator_batch_size)
        replay_max = float(audit_facts["grouped_max_abs_logprob_error"])

        primitive_count = int(num_steps) * int(self.config.num_envs)
        if sum(e.elapsed for e in events) != primitive_count:
            raise ValueError(
                f"event chains cover {sum(e.elapsed for e in events)} primitive transitions, "
                f"expected {primitive_count}"
            )
        batch_size = int(self.config.coordinator_batch_size)
        epochs = int(self.config.ppo_epochs)
        totals = {key: 0.0 for key in ("loss", "policy", "value", "team_entropy", "agent_entropy")}
        kl_sum = clip_sum = factor_total = duration_entropy_sum = duration_factor_total = 0.0
        updates = 0

        for _ in range(epochs):
            permutation = torch.randperm(event_count, device=self.device)
            for start in range(0, event_count, batch_size):
                selection = permutation[start:start + batch_size]
                batch_events = [events[int(i)] for i in selection.cpu().tolist()]
                scale = float(event_count) / float(len(batch_events) * primitive_count)
                evaluation = self._evaluate_events(batch_events)
                new_log_probs = self._flatten_new_factors(evaluation)
                entropy = self._flatten_entropies(evaluation)
                old_batch = old_factors[selection]
                mask_batch = factor_mask[selection]
                adv_batch = advantages[selection].unsqueeze(1)
                log_ratio = new_log_probs - old_batch.detach()
                ratio = torch.exp(log_ratio)
                clipped = torch.clamp(
                    ratio, 1.0 - float(self.config.clip_epsilon), 1.0 + float(self.config.clip_epsilon)
                )
                surrogate = torch.minimum(ratio * adv_batch, clipped * adv_batch)
                policy_loss = -(surrogate * mask_batch).sum() * scale
                entropy_total = (entropy * mask_batch).sum() * scale

                targets = returns[selection]
                if value_norm is not None:
                    mean, _var, std = value_norm
                    targets = (targets - mean) / std
                    targets = torch.clamp(targets, -self.config.value_clip, self.config.value_clip)
                value_loss = ((evaluation["values"] - targets.detach()) ** 2).sum() * scale
                loss = (
                    policy_loss
                    + float(self.config.value_loss_coef) * value_loss
                    - float(self.config.lambda_h) * entropy_total
                )
                if not torch.isfinite(loss):
                    raise RuntimeError("duration coordinator loss is not finite")
                self.coordinator_optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.skill_coordinator.parameters(), float(self.config.max_grad_norm)
                )
                self.coordinator_optimizer.step()

                active_log_ratio = log_ratio[mask_batch].detach()
                active_ratio = ratio[mask_batch].detach()
                active_count = float(active_log_ratio.numel())
                kl_sum += float(((active_ratio - 1.0) - active_log_ratio).sum().item())
                clip_sum += float((torch.abs(active_ratio - 1.0) > self.config.clip_epsilon).sum().item())
                factor_total += active_count
                duration_mask = mask_batch[:, 1 + self.config.n_agents:]
                duration_entropy_sum += float(
                    (evaluation["duration_entropies"] * duration_mask).sum().detach().item()
                )
                duration_factor_total += float(duration_mask.sum().item())
                totals["loss"] += float(loss.detach().item())
                totals["policy"] += float(policy_loss.detach().item())
                totals["value"] += float(value_loss.detach().item())
                totals["team_entropy"] += float(evaluation["team_entropy"].mean().detach().item())
                totals["agent_entropy"] += float(evaluation["agent_entropies"].mean().detach().item())
                updates += 1

        post_change_sum = 0.0
        post_change_count = 0
        with torch.no_grad():
            for start in range(0, event_count, audit_batch):
                stop = min(event_count, start + audit_batch)
                post_eval = self._evaluate_events(events[start:stop])
                post_new = self._flatten_new_factors(post_eval)
                post_change = torch.abs(post_new - old_factors[start:stop])[factor_mask[start:stop]]
                post_change_sum += float(post_change.sum().item())
                post_change_count += int(post_change.numel())
        post_mean = post_change_sum / max(1, post_change_count)
        approx_kl = kl_sum / max(1.0, factor_total)
        clip_fraction = clip_sum / max(1.0, factor_total)
        duration_entropy_mean = duration_entropy_sum / max(1.0, duration_factor_total)
        self._duration_metrics["optimizer_steps"] += updates
        self.native_toy_optimizer_updates["high"] += updates
        self._duration_metrics["replay_post_mean_abs_change"] = post_mean
        self._duration_metrics["approx_kl"] = approx_kl
        self._duration_metrics["clip_fraction"] = clip_fraction
        self._duration_metrics["duration_entropy"] = duration_entropy_mean
        self._duration_metrics["last_update"] = {
            "events": event_count,
            "primitive_transitions": primitive_count,
            "optimizer_steps": updates,
            "replay_pre_max_abs_error": replay_max,
            "replay_grouped_abs_logprob_threshold": GROUPED_REPLAY_ABS_TOLERANCE,
            "replay_merged_max_abs_logprob_error": float(
                audit_facts["merged_max_abs_logprob_error"]
            ),
            "replay_merged_max_relative_probability_drift": float(
                audit_facts["merged_max_relative_probability_drift"]
            ),
            "replay_merged_relative_probability_threshold": MERGED_REPLAY_RELATIVE_TOLERANCE,
            "replay_post_mean_abs_change": post_mean,
            "approx_kl": approx_kl,
            "clip_fraction": clip_fraction,
            "duration_entropy": duration_entropy_mean,
        }
        denominator = max(1, updates)
        mean_reward = float(np.mean([e.reward for e in events]))
        mean_value = float(np.mean([e.old_value for e in events]))
        return (
            totals["loss"] / denominator,
            totals["policy"] / denominator,
            totals["value"] / denominator,
            totals["team_entropy"] / denominator,
            totals["agent_entropy"] / denominator,
            mean_value,
            mean_value,
            mean_reward,
            0.0,
        )

    def update(self, last_values, dones, steps_in_buffer, last_state=None, last_observations=None):
        if last_state is not None or last_observations is not None:
            raise ValueError("duration updates must omit the inherited raw-state high bootstrap")
        if not np.asarray(dones, dtype=np.bool_).all():
            raise ValueError("duration updates require terminal-aligned complete episodes")
        if self._duration_open_events:
            raise ValueError("duration updates refuse unclosed training events")
        return super().update(
            last_values, dones, steps_in_buffer, last_state=None, last_observations=None
        )

    def clear_buffers(self):
        if self._duration_open_events:
            raise ValueError("clear_buffers refuses to discard unclosed duration events")
        super().clear_buffers()
        self._duration_events.clear()
        self._duration_team_deadline.clear()
        self._duration_agent_deadlines.clear()
        self._duration_agent_commit_start.clear()
        self._duration_episode_position.clear()
        self._prime_invalid_lanes()

    def reset_env_state(self, env_id):
        if int(env_id) in self._duration_open_events:
            raise ValueError("reset_env_state refuses to discard an unclosed duration event")
        super().reset_env_state(env_id)
        self._duration_team_deadline.pop(int(env_id), None)
        self._duration_agent_deadlines.pop(int(env_id), None)
        self._duration_agent_commit_start.pop(int(env_id), None)
        self._duration_episode_position.pop(int(env_id), None)

    def finish_evaluation_episode(self, dones) -> None:
        """Finalize duration-only evaluator telemetry without creating training events."""
        done_array = np.asarray(dones, dtype=np.bool_).reshape(-1)
        if not done_array.all():
            raise ValueError("evaluation duration finalization requires terminal lanes")
        if self._duration_open_events or self._duration_events:
            raise ValueError("evaluation finalization cannot be mixed with stored training events")
        for env_id in range(len(done_array)):
            starts = self._duration_agent_commit_start.get(env_id)
            if starts is None:
                continue
            final_time = int(self._duration_episode_position.get(env_id, -1)) + 1
            self._duration_metrics["executed_durations"].extend(
                (final_time - np.asarray(starts, dtype=np.int64)).astype(int).tolist()
            )
            self._duration_metrics["terminal_boundaries"] += 1

    @staticmethod
    def _summary(values: Iterable[int | float]) -> dict:
        array = np.asarray(list(values), dtype=np.float64)
        if array.size == 0:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "histogram": {}}
        unique, counts = np.unique(array.astype(np.int64), return_counts=True)
        return {
            "count": int(array.size),
            "mean": float(array.mean()),
            "min": float(array.min()),
            "max": float(array.max()),
            "histogram": {str(int(k)): int(v) for k, v in zip(unique, counts)},
        }

    def get_duration_metrics(self) -> dict:
        """Return cumulative scheduler/occupancy facts plus the latest update facts."""
        metrics = self._duration_metrics
        with torch.no_grad():
            displacement = torch.sqrt(sum(
                ((p.detach() - p0).double() ** 2).sum()
                for p, p0 in zip(self.skill_coordinator.parameters(), self._duration_theta0)
            )).item()
        parameter_counts = {
            "coordinator_total": int(sum(p.numel() for p in self.skill_coordinator.parameters())),
            "duration_head": int(sum(p.numel() for p in self.skill_coordinator.duration_head.parameters())),
            "event_context_and_value": int(sum(
                p.numel() for module in (
                    self.skill_coordinator.duration_context_projection,
                    self.skill_coordinator.event_value_head,
                ) for p in module.parameters()
            )),
        }
        return {
            "duration_mode": self.duration_mode,
            "events": int(metrics["events"]),
            "stored_events": int(metrics["stored_events"]),
            "primitive_steps": int(metrics["primitive_steps"]),
            "eligible_factors": int(metrics["eligible_factors"]),
            "joint_nondegenerate_events": int(metrics["joint_nondegenerate_events"]),
            "same_label_renewals": int(metrics["same_label_renewals"]),
            "cap_boundaries": int(metrics["cap_boundaries"]),
            "terminal_boundaries": int(metrics["terminal_boundaries"]),
            "stored_event_elapsed_total": int(metrics["event_elapsed_total"]),
            "declared_duration": self._summary(metrics["declared_durations"]),
            "executed_duration": self._summary(metrics["executed_durations"]),
            "team_skill_occupancy": dict(metrics["team_skill_occupancy"]),
            "agent_skill_occupancy": dict(metrics["agent_skill_occupancy"]),
            "replay_pre_max_abs_error": float(metrics["replay_pre_max_abs_error"]),
            "replay_grouped_abs_logprob_threshold": float(metrics["replay_grouped_threshold"]),
            "replay_merged_max_abs_logprob_error": float(
                metrics["replay_merged_max_abs_error"]
            ),
            "replay_merged_max_relative_probability_drift": float(
                metrics["replay_merged_max_relative_probability_drift"]
            ),
            "replay_merged_relative_probability_threshold": float(
                metrics["replay_merged_relative_probability_threshold"]
            ),
            "replay_post_mean_abs_change": float(metrics["replay_post_mean_abs_change"]),
            "approx_kl": float(metrics["approx_kl"]),
            "clip_fraction": float(metrics["clip_fraction"]),
            "duration_entropy": float(metrics["duration_entropy"]),
            "optimizer_steps": int(metrics["optimizer_steps"]),
            "parameter_counts": parameter_counts,
            "coordinator_relative_initialization_displacement": (
                float(displacement) / self._duration_theta0_norm
                if self._duration_theta0_norm > 0.0 else 0.0
            ),
            "last_update": dict(metrics["last_update"]),
            "last_replay_audit": dict(metrics["last_replay_audit"]),
        }
