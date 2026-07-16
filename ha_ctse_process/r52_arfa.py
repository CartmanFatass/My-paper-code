"""R52 Anonymous Reliability--Fulfillment Allocation and pointer policy.

The module is deliberately isolated from HA-CTSE/HMASD training code.  It
contains one terminal graded-utility assignment environment and one anonymous,
N-independent recurrent pointer actor-critic.  No skill, role, member identity,
KEEP/SET, shaping, or intrinsic-reward input exists in this implementation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


TEAM_SIZES = (2, 3, 4, 5, 6)
HORIZON = 32
WAVE_STARTS = (4, 12, 20)
JOB_DEADLINE = 6
STATION_HEALTH_MAX = 4
SELF_FEATURE_DIM = 6
ENTITY_FEATURE_DIM = 8
CRITIC_FIELD_DIM = 4
HIDDEN_DIM = 32


@dataclass(frozen=True)
class EpisodeLedger:
    """All exogenous randomness shared by the two experimental arms."""

    active_n: int
    initial_locations: np.ndarray
    member_keys: np.ndarray
    entity_keys: np.ndarray
    agent_orders: np.ndarray
    entity_orders: np.ndarray
    sampling_uniforms: np.ndarray

    @property
    def batch_size(self) -> int:
        return int(self.initial_locations.shape[0])

    @property
    def entity_count(self) -> int:
        return int(self.entity_keys.shape[2])

    def validate(self) -> None:
        n = int(self.active_n)
        batch = self.batch_size
        entities = n + 1
        expected = {
            "initial_locations": (batch, n),
            "member_keys": (batch, n),
            "entity_keys": (HORIZON, batch, entities),
            "agent_orders": (HORIZON, batch, n),
            "entity_orders": (HORIZON, batch, entities),
            "sampling_uniforms": (HORIZON, batch, n),
        }
        for name, shape in expected.items():
            if tuple(getattr(self, name).shape) != shape:
                raise ValueError(f"ledger {name} has shape {getattr(self, name).shape}, expected {shape}")
        agent_reference = np.arange(n, dtype=np.int64)
        entity_reference = np.arange(entities, dtype=np.int64)
        if not all(
            np.array_equal(np.sort(row), agent_reference)
            for row in self.agent_orders.reshape(-1, n)
        ):
            raise ValueError("ledger agent order is not a permutation")
        if not all(
            np.array_equal(np.sort(row), entity_reference)
            for row in self.entity_orders.reshape(-1, entities)
        ):
            raise ValueError("ledger entity order is not a permutation")
        if np.any(self.sampling_uniforms < 0.0) or np.any(
            self.sampling_uniforms >= 1.0
        ):
            raise ValueError("ledger categorical uniforms must be in [0, 1)")


def make_episode_ledger(
    *,
    active_n: int,
    batch_size: int,
    reset_rng: np.random.Generator,
    control_rng: np.random.Generator,
) -> EpisodeLedger:
    """Generate one paired batch without exposing keys to the policy."""

    if active_n not in TEAM_SIZES:
        raise ValueError(f"unsupported team size: {active_n}")
    n = int(active_n)
    batch = int(batch_size)
    persistent = n // 2
    entities = n + 1
    initial_locations = np.zeros((batch, n), dtype=np.int64)
    member_keys = np.empty((batch, n), dtype=np.int64)
    entity_keys = np.empty((HORIZON, batch, entities), dtype=np.int64)
    base_entity_orders = np.empty((batch, entities), dtype=np.int64)
    for episode in range(batch):
        agent_permutation = reset_rng.permutation(n)
        station_permutation = reset_rng.permutation(persistent)
        initial_locations[
            episode, agent_permutation[:persistent]
        ] = 1 + station_permutation
        member_keys[episode] = 10_000 + reset_rng.permutation(n)
        persistent_keys = 20_000 + reset_rng.permutation(1 + persistent)
        phase_ranges = ((0, 4), (4, 12), (12, 20), (20, HORIZON))
        for phase, (start, stop) in enumerate(phase_ranges):
            entity_keys[start:stop, episode, : 1 + persistent] = persistent_keys
            entity_keys[start:stop, episode, 1 + persistent :] = (
                30_000
                + phase * 100
                + reset_rng.permutation(n - persistent)
            )
        base_entity_orders[episode] = reset_rng.permutation(entities)

    agent_orders = np.argsort(
        control_rng.random((HORIZON, batch, n)), axis=-1
    ).astype(np.int64)
    entity_orders = np.broadcast_to(
        base_entity_orders[None, :, :], (HORIZON, batch, entities)
    ).copy()
    sampling_uniforms = control_rng.random(
        (HORIZON, batch, n), dtype=np.float32
    )
    ledger = EpisodeLedger(
        active_n=n,
        initial_locations=initial_locations,
        member_keys=member_keys,
        entity_keys=entity_keys,
        agent_orders=agent_orders,
        entity_orders=entity_orders,
        sampling_uniforms=sampling_uniforms,
    )
    ledger.validate()
    return ledger


class AnonymousReliabilityFulfillmentBatch:
    """Vectorized fixed-horizon ARFA transition kernel on NumPy arrays."""

    def __init__(self, ledger: EpisodeLedger):
        ledger.validate()
        self.ledger = ledger
        self.n = int(ledger.active_n)
        self.batch_size = int(ledger.batch_size)
        self.persistent = self.n // 2
        self.dispatch = self.n - self.persistent
        self.entities = self.n + 1
        self.station_slice = slice(1, 1 + self.persistent)
        self.job_slice = slice(1 + self.persistent, self.entities)
        self.locations = ledger.initial_locations.copy()
        self.station_health = np.full(
            (self.batch_size, self.persistent),
            STATION_HEALTH_MAX,
            dtype=np.int64,
        )
        self.station_health_integral = np.zeros(
            (self.batch_size, self.persistent), dtype=np.float64
        )
        self.job_work = np.zeros(
            (self.batch_size, self.dispatch), dtype=np.int64
        )
        self.job_deadline = np.zeros_like(self.job_work)
        self.job_expired = np.zeros_like(self.job_work, dtype=np.bool_)
        self.jobs_active = False
        self.wave_index = 0
        self.station_zero_visits = np.zeros(self.batch_size, dtype=np.int64)
        self.completed_jobs = np.zeros(self.batch_size, dtype=np.int64)
        self.deadline_misses = np.zeros(self.batch_size, dtype=np.int64)
        self.served_previous = np.zeros(
            (self.batch_size, self.n), dtype=np.bool_
        )
        self.served_previous_entity = np.full(
            (self.batch_size, self.n), -1, dtype=np.int64
        )
        self.time = 0
        self.nonterminal_reward_nonzero = 0
        self.final_reward_predicate_mismatch = 0
        self.expired_completion_violation = 0
        self.expired_completion_attempts = 0
        self.invalid_action_count = 0
        self.duplicate_excess_sum = np.zeros(self.batch_size, dtype=np.float64)
        self.assignment_decisions = np.zeros(self.batch_size, dtype=np.int64)
        self.current_dwell = np.zeros(
            (self.batch_size, self.n), dtype=np.int64
        )
        self.station_dwell_lengths: list[int] = []
        self.job_dwell_lengths: list[int] = []

    def _entity_kind(self, entity: int) -> str:
        if entity == 0:
            return "depot"
        if entity <= self.persistent:
            return "station"
        return "job"

    def _close_dwell(self, episode: int, agent: int, entity: int) -> None:
        kind = self._entity_kind(int(entity))
        length = int(self.current_dwell[episode, agent])
        if length <= 0:
            return
        if kind == "station":
            self.station_dwell_lengths.append(length)
        elif kind == "job":
            self.job_dwell_lengths.append(length)

    def prepare_step(self, step: int) -> None:
        if int(step) != self.time:
            raise ValueError(f"ARFA clock mismatch: expected {self.time}, got {step}")
        if step not in WAVE_STARTS:
            return
        if self.jobs_active:
            first_job = 1 + self.persistent
            at_old_job = self.locations >= first_job
            for episode, agent in np.argwhere(at_old_job):
                self._close_dwell(
                    int(episode), int(agent), int(self.locations[episode, agent])
                )
            self.locations[at_old_job] = 0
            self.current_dwell[at_old_job] = 0
            self.served_previous[at_old_job] = False
            self.served_previous_entity[at_old_job] = -1
        self.jobs_active = True
        self.wave_index += 1
        self.job_work.fill(1)
        self.job_deadline.fill(JOB_DEADLINE)
        self.job_expired.fill(False)

    def _active_entity_mask(self) -> np.ndarray:
        mask = np.ones((self.batch_size, self.entities), dtype=np.bool_)
        if not self.jobs_active:
            mask[:, self.job_slice] = False
        return mask

    def observations(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return canonical self/entity views, mask, and critic-only fields."""

        active = self._active_entity_mask()
        assigned_counts = np.zeros(
            (self.batch_size, self.entities), dtype=np.float32
        )
        ready_counts = np.zeros_like(assigned_counts)
        for episode in range(self.batch_size):
            assigned_counts[episode] = np.bincount(
                self.locations[episode], minlength=self.entities
            ).astype(np.float32)
            ready_entities = self.served_previous_entity[episode]
            valid_ready = ready_entities >= 0
            if np.any(valid_ready):
                ready_counts[episode] = np.bincount(
                    ready_entities[valid_ready], minlength=self.entities
                ).astype(np.float32)

        entities = np.zeros(
            (self.batch_size, self.entities, ENTITY_FEATURE_DIM),
            dtype=np.float32,
        )
        entities[:, 0, 0] = 1.0
        entities[:, :, 1] = active.astype(np.float32)
        entities[:, self.station_slice, 2] = (
            self.station_health.astype(np.float32) / STATION_HEALTH_MAX
        )
        entities[:, self.station_slice, 3] = (
            self.station_health_integral.astype(np.float32) / HORIZON
        )
        if self.jobs_active:
            entities[:, self.job_slice, 4] = self.job_work.astype(np.float32)
            entities[:, self.job_slice, 5] = (
                self.job_deadline.astype(np.float32) / JOB_DEADLINE
            )
        entities[:, :, 6] = ready_counts / float(self.n)
        entities[:, :, 7] = assigned_counts / float(self.n)

        self_view = np.zeros(
            (self.batch_size, self.n, SELF_FEATURE_DIM), dtype=np.float32
        )
        self_view[:, :, 0] = (self.locations == 0).astype(np.float32)
        for episode in range(self.batch_size):
            for agent in range(self.n):
                location = int(self.locations[episode, agent])
                if 1 <= location <= self.persistent:
                    health = self.station_health[episode, location - 1]
                    self_view[episode, agent, 1] = 1.0
                    self_view[episode, agent, 3] = (
                        float(health) / STATION_HEALTH_MAX
                    )
                elif location > self.persistent and self.jobs_active:
                    job = location - 1 - self.persistent
                    work = self.job_work[episode, job]
                    self_view[episode, agent, 2] = float(work > 0)
                    self_view[episode, agent, 4] = (
                        float(self.job_deadline[episode, job]) / JOB_DEADLINE
                    )
        self_view[:, :, 5] = self.served_previous.astype(np.float32)
        critic_fields = np.stack(
            (
                np.full(self.batch_size, self.time / HORIZON, dtype=np.float32),
                np.full(
                    self.batch_size, self.wave_index / len(WAVE_STARTS), dtype=np.float32
                ),
                self.completed_jobs.astype(np.float32)
                / float(3 * self.dispatch),
                np.min(self.station_health_integral, axis=1).astype(np.float32)
                / HORIZON,
            ),
            axis=1,
        )
        return self_view, entities, active, critic_fields

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        if tuple(actions.shape) != (self.batch_size, self.n):
            raise ValueError("ARFA action shape mismatch")
        active = self._active_entity_mask()
        if np.any(actions < 0) or np.any(actions >= self.entities):
            self.invalid_action_count += int(
                np.count_nonzero((actions < 0) | (actions >= self.entities))
            )
            raise ValueError("ARFA action outside entity range")
        valid = np.take_along_axis(active, actions, axis=1)
        if not np.all(valid):
            self.invalid_action_count += int(np.count_nonzero(~valid))
            raise ValueError("ARFA action selected an inactive entity")

        previous_locations = self.locations.copy()
        staying = actions == previous_locations
        service = staying & (actions != 0)
        station_served = np.zeros(
            (self.batch_size, self.persistent), dtype=np.bool_
        )
        job_served = np.zeros(
            (self.batch_size, self.dispatch), dtype=np.bool_
        )
        for episode in range(self.batch_size):
            service_entities = actions[episode, service[episode]]
            for entity in service_entities:
                entity = int(entity)
                if entity <= self.persistent:
                    station_served[episode, entity - 1] = True
                elif self.jobs_active:
                    job_served[episode, entity - 1 - self.persistent] = True

            counts = np.bincount(actions[episode], minlength=self.entities)
            self.duplicate_excess_sum[episode] += float(
                np.maximum(counts[1:] - 1, 0).sum()
            )
            self.assignment_decisions[episode] += self.n

        self.station_health = np.where(
            station_served,
            STATION_HEALTH_MAX,
            np.maximum(self.station_health - 1, 0),
        )
        station_zero_now = np.any(self.station_health == 0, axis=1)
        self.station_zero_visits += station_zero_now.astype(np.int64)
        self.station_health_integral += (
            self.station_health.astype(np.float64) / STATION_HEALTH_MAX
        )

        completed_now = np.zeros_like(self.job_work, dtype=np.bool_)
        missed_now = np.zeros_like(self.job_work, dtype=np.bool_)
        if self.jobs_active:
            completed_before = self.completed_jobs.copy()
            incomplete = (self.job_work > 0) & (~self.job_expired)
            self.expired_completion_attempts += int(
                np.count_nonzero((self.job_work > 0) & self.job_expired & job_served)
            )
            completed_now = incomplete & job_served
            self.job_work[completed_now] = 0
            self.completed_jobs += completed_now.sum(axis=1)
            if np.any(
                self.completed_jobs
                != completed_before + completed_now.sum(axis=1)
            ):
                self.expired_completion_violation += 1
            still_incomplete = (self.job_work > 0) & (~self.job_expired)
            previous_deadline = self.job_deadline.copy()
            self.job_deadline[still_incomplete] = np.maximum(
                self.job_deadline[still_incomplete] - 1, 0
            )
            missed_now = (
                still_incomplete
                & (previous_deadline > 0)
                & (self.job_deadline == 0)
            )
            self.deadline_misses += missed_now.sum(axis=1)
            self.job_expired[missed_now] = True

        changed = actions != previous_locations
        for episode, agent in np.argwhere(changed):
            self._close_dwell(
                int(episode), int(agent), int(previous_locations[episode, agent])
            )
        self.current_dwell[~changed] += 1
        self.current_dwell[changed] = 0
        self.locations = actions.astype(np.int64, copy=True)
        self.served_previous = service
        self.served_previous_entity = np.where(service, actions, -1)

        final_step = self.time == HORIZON - 1
        reliability = np.min(self.station_health_integral, axis=1) / HORIZON
        fulfillment = self.completed_jobs.astype(np.float64) / float(
            3 * self.dispatch
        )
        utility = np.minimum(reliability, fulfillment).astype(np.float32)
        reward = utility if final_step else np.zeros(self.batch_size, dtype=np.float32)
        if not final_step:
            self.nonterminal_reward_nonzero += int(np.count_nonzero(reward))
        else:
            self.final_reward_predicate_mismatch += int(
                np.count_nonzero(
                    np.abs(reward - np.minimum(reliability, fulfillment)) > 1.0e-7
                )
            )
            for episode in range(self.batch_size):
                for agent in range(self.n):
                    self._close_dwell(
                        episode, agent, int(self.locations[episode, agent])
                    )
        self.time += 1
        info = {
            "utility": utility.copy(),
            "reliability": reliability.astype(np.float32),
            "fulfillment": fulfillment.astype(np.float32),
            "station_zero_now": station_zero_now,
            "completed_now": completed_now.sum(axis=1),
            "missed_now": missed_now.sum(axis=1),
        }
        return reward, info

    def diagnostics(self) -> dict[str, Any]:
        station_dwell = np.asarray(self.station_dwell_lengths, dtype=np.float64)
        job_dwell = np.asarray(self.job_dwell_lengths, dtype=np.float64)
        return {
            "utility": np.minimum(
                np.min(self.station_health_integral, axis=1) / HORIZON,
                self.completed_jobs.astype(np.float64) / float(3 * self.dispatch),
            ).astype(np.float32),
            "reliability": (
                np.min(self.station_health_integral, axis=1) / HORIZON
            ).astype(np.float32),
            "fulfillment": (
                self.completed_jobs.astype(np.float64) / float(3 * self.dispatch)
            ).astype(np.float32),
            "station_zero_visit_fraction": self.station_zero_visits.astype(np.float32)
            / HORIZON,
            "completed_job_fraction": self.completed_jobs.astype(np.float32)
            / float(3 * self.dispatch),
            "deadline_miss_fraction": self.deadline_misses.astype(np.float32)
            / float(3 * self.dispatch),
            "duplicate_assignment_fraction": self.duplicate_excess_sum
            / np.maximum(self.assignment_decisions, 1),
            "station_dwell_mean": float(station_dwell.mean()) if station_dwell.size else 0.0,
            "job_dwell_mean": float(job_dwell.mean()) if job_dwell.size else 0.0,
            "nonterminal_reward_nonzero": int(self.nonterminal_reward_nonzero),
            "final_reward_predicate_mismatch": int(self.final_reward_predicate_mismatch),
            "expired_completion_violation": int(self.expired_completion_violation),
            "expired_completion_attempts": int(self.expired_completion_attempts),
            "invalid_action_count": int(self.invalid_action_count),
        }


@dataclass
class PointerStepOutput:
    pointers_by_position: torch.Tensor
    actions_by_agent: torch.Tensor
    token_log_probs: torch.Tensor
    token_entropies: torch.Tensor
    value: torch.Tensor
    next_hidden: torch.Tensor
    prefix_counts: torch.Tensor
    masked_probability_mass: torch.Tensor
    focal_relation_counts: torch.Tensor


class ARFASetPointerPolicy(nn.Module):
    """Small anonymous recurrent actor-critic with an entity pointer head."""

    def __init__(self) -> None:
        super().__init__()
        self.member_encoder = nn.Sequential(
            nn.Linear(SELF_FEATURE_DIM, HIDDEN_DIM),
            nn.GELU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.GELU(),
        )
        self.entity_encoder = nn.Sequential(
            nn.Linear(ENTITY_FEATURE_DIM, HIDDEN_DIM),
            nn.GELU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.GELU(),
        )
        self.temporal_core = nn.GRUCell(HIDDEN_DIM, HIDDEN_DIM)
        self.query_mlp = nn.Sequential(
            nn.Linear(4 * HIDDEN_DIM, 64),
            nn.GELU(),
            nn.Linear(64, HIDDEN_DIM),
        )
        self.entity_key = nn.Linear(HIDDEN_DIM + 2, HIDDEN_DIM)
        self.critic_hidden = nn.Sequential(
            nn.Linear(2 * HIDDEN_DIM + CRITIC_FIELD_DIM, 64), nn.GELU()
        )
        self.critic_value = nn.Linear(64, 1)

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def forward_step(
        self,
        *,
        self_features: torch.Tensor,
        entity_features: torch.Tensor,
        entity_mask: torch.Tensor,
        agent_order: torch.Tensor,
        entity_order: torch.Tensor,
        hidden: torch.Tensor,
        hidden_reset_mask: torch.Tensor,
        critic_fields: torch.Tensor,
        focal_locations: torch.Tensor,
        sampling_uniforms: torch.Tensor | None = None,
        teacher_pointers: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> PointerStepOutput:
        batch, active_n, feature_dim = self_features.shape
        entities = int(entity_features.shape[1])
        if feature_dim != SELF_FEATURE_DIM:
            raise ValueError("ARFA self feature dimension mismatch")
        if tuple(entity_features.shape) != (batch, entities, ENTITY_FEATURE_DIM):
            raise ValueError("ARFA entity feature dimension mismatch")
        if entities != active_n + 1:
            raise ValueError("ARFA entity count must equal N+1")
        if tuple(entity_mask.shape) != (batch, entities):
            raise ValueError("ARFA entity mask shape mismatch")
        if tuple(agent_order.shape) != (batch, active_n):
            raise ValueError("ARFA agent order shape mismatch")
        if tuple(entity_order.shape) != (batch, entities):
            raise ValueError("ARFA entity order shape mismatch")
        if tuple(hidden.shape) != (batch, active_n, HIDDEN_DIM):
            raise ValueError("ARFA recurrent hidden shape mismatch")
        if tuple(hidden_reset_mask.shape) != (batch, active_n):
            raise ValueError("ARFA hidden reset mask shape mismatch")
        if tuple(critic_fields.shape) != (batch, CRITIC_FIELD_DIM):
            raise ValueError("ARFA critic field shape mismatch")
        if tuple(focal_locations.shape) != (batch, active_n):
            raise ValueError("ARFA focal location shape mismatch")
        modes = sum(
            value is not None
            for value in (sampling_uniforms, teacher_pointers)
        ) + int(bool(deterministic))
        if modes != 1:
            raise ValueError("choose exactly one sampling, replay, or deterministic mode")

        device = self_features.device
        batch_indices = torch.arange(batch, device=device)
        hidden = hidden * hidden_reset_mask.unsqueeze(-1)
        member_embeddings = self.member_encoder(self_features)
        next_hidden = self.temporal_core(
            member_embeddings.reshape(batch * active_n, HIDDEN_DIM),
            hidden.reshape(batch * active_n, HIDDEN_DIM),
        ).reshape(batch, active_n, HIDDEN_DIM)

        entity_gather = entity_order.unsqueeze(-1).expand(
            batch, entities, ENTITY_FEATURE_DIM
        )
        presented_features = torch.gather(entity_features, 1, entity_gather)
        presented_mask = torch.gather(entity_mask, 1, entity_order)
        entity_embeddings = self.entity_encoder(presented_features)
        float_mask = presented_mask.to(entity_embeddings.dtype).unsqueeze(-1)
        entity_pool = (entity_embeddings * float_mask).sum(dim=1) / float_mask.sum(
            dim=1
        ).clamp_min(1.0)
        member_pool = member_embeddings.mean(dim=1)
        # The contract permits generic set cardinalities through the pooled
        # representation.  Inject them without a learned size/slot embedding.
        member_pool = member_pool.clone()
        entity_pool = entity_pool.clone()
        member_pool[:, 0] = member_pool[:, 0] + math.log1p(float(active_n))
        entity_pool[:, 0] = entity_pool[:, 0] + math.log1p(float(entities))
        value_input = torch.cat((member_pool, entity_pool, critic_fields), dim=-1)
        value = self.critic_value(self.critic_hidden(value_input)).squeeze(-1)

        planned_counts = torch.zeros(
            (batch, entities), dtype=self_features.dtype, device=device
        )
        pointers: list[torch.Tensor] = []
        actions_by_agent = torch.empty(
            (batch, active_n), dtype=torch.long, device=device
        )
        log_probs: list[torch.Tensor] = []
        entropies: list[torch.Tensor] = []
        prefixes: list[torch.Tensor] = []
        masked_masses: list[torch.Tensor] = []
        relation_counts: list[torch.Tensor] = []
        for position in range(active_n):
            agent_indices = agent_order[:, position]
            focal_member = member_embeddings[batch_indices, agent_indices]
            focal_hidden = next_hidden[batch_indices, agent_indices]
            query = self.query_mlp(
                torch.cat(
                    (focal_member, member_pool, entity_pool, focal_hidden), dim=-1
                )
            )
            normalized_prefix = planned_counts / float(active_n)
            focal_location = focal_locations[batch_indices, agent_indices]
            focal_relation = entity_order.eq(focal_location.unsqueeze(-1)).to(
                entity_embeddings.dtype
            )
            keys = self.entity_key(
                torch.cat(
                    (
                        entity_embeddings,
                        normalized_prefix.unsqueeze(-1),
                        focal_relation.unsqueeze(-1),
                    ),
                    dim=-1,
                )
            )
            logits = torch.einsum("bd,bed->be", query, keys) / math.sqrt(
                HIDDEN_DIM
            )
            logits = logits.masked_fill(~presented_mask, -torch.inf)
            log_probability = F.log_softmax(logits, dim=-1)
            probability = torch.exp(log_probability)
            if teacher_pointers is not None:
                selected = teacher_pointers[:, position]
            elif deterministic:
                selected = torch.argmax(logits, dim=-1)
            else:
                if sampling_uniforms is None:
                    raise AssertionError("sampling uniforms unexpectedly absent")
                cumulative = torch.cumsum(probability, dim=-1)
                selected = torch.sum(
                    sampling_uniforms[:, position].unsqueeze(-1) > cumulative,
                    dim=-1,
                ).clamp(max=entities - 1)
            if not bool(
                torch.gather(presented_mask, 1, selected.unsqueeze(-1)).all()
            ):
                raise RuntimeError("pointer selected a masked entity")
            prefixes.append(planned_counts.clone())
            selected_log_probability = torch.gather(
                log_probability, 1, selected.unsqueeze(-1)
            ).squeeze(-1)
            safe_log_probability = torch.where(
                presented_mask,
                log_probability,
                torch.zeros_like(log_probability),
            )
            entropy = -torch.sum(
                probability * safe_log_probability, dim=-1
            )
            masked_mass = torch.sum(
                torch.where(~presented_mask, probability, 0.0), dim=-1
            )
            canonical_action = torch.gather(
                entity_order, 1, selected.unsqueeze(-1)
            ).squeeze(-1)
            actions_by_agent[batch_indices, agent_indices] = canonical_action
            planned_counts.scatter_add_(
                1,
                selected.unsqueeze(-1),
                torch.ones((batch, 1), dtype=planned_counts.dtype, device=device),
            )
            pointers.append(selected)
            log_probs.append(selected_log_probability)
            entropies.append(entropy)
            masked_masses.append(masked_mass)
            relation_counts.append(focal_relation.sum(dim=-1))

        return PointerStepOutput(
            pointers_by_position=torch.stack(pointers, dim=1),
            actions_by_agent=actions_by_agent,
            token_log_probs=torch.stack(log_probs, dim=1),
            token_entropies=torch.stack(entropies, dim=1),
            value=value,
            next_hidden=next_hidden,
            prefix_counts=torch.stack(prefixes, dim=1),
            masked_probability_mass=torch.stack(masked_masses, dim=1),
            focal_relation_counts=torch.stack(relation_counts, dim=1),
        )


def model_state_copy(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: tensor.detach().cpu().clone()
        for name, tensor in model.state_dict().items()
    }


def maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return float("inf")
    return max(
        float(torch.max(torch.abs(left[name] - right[name]))) for name in left
    )


def state_dict_finite(state: dict[str, torch.Tensor]) -> bool:
    return all(bool(torch.isfinite(tensor).all()) for tensor in state.values())


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return json_ready(value.detach().cpu().numpy())
    return value
