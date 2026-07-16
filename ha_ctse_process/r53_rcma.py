"""R53 residual-capacity masked variable-N queue allocation.

The module is isolated from HA-CTSE/HMASD training code.  Productive queues
have unit per-step capacity while one anonymous idle entity has capacity N.
The actor sees only generic member/entity state, residual capacity, and the
focal agent's previous action.  No skill, identity, role, shaping, intrinsic
reward, or environment-specific priority enters the policy.
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
HORIZON = 16
PERSISTENT_ARRIVAL_STEPS = tuple(range(0, HORIZON, 2))
BURST_WAVE_STEPS = (3, 9)
BURST_DEADLINE = 3
SELF_FEATURE_DIM = 2
ENTITY_FEATURE_DIM = 7
CRITIC_FIELD_DIM = 4
HIDDEN_DIM = 32


@dataclass(frozen=True)
class EpisodeLedger:
    """All exogenous randomness shared by the two experimental arms."""

    active_n: int
    member_keys: np.ndarray
    entity_keys: np.ndarray
    agent_orders: np.ndarray
    entity_orders: np.ndarray
    sampling_uniforms: np.ndarray

    @property
    def batch_size(self) -> int:
        return int(self.member_keys.shape[0])

    @property
    def entity_count(self) -> int:
        return int(self.entity_keys.shape[2])

    def validate(self) -> None:
        n = int(self.active_n)
        batch = self.batch_size
        entities = n + 2
        expected = {
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
    entities = n + 2
    member_keys = np.empty((batch, n), dtype=np.int64)
    entity_keys = np.empty((HORIZON, batch, entities), dtype=np.int64)
    base_entity_orders = np.empty((batch, entities), dtype=np.int64)
    for episode in range(batch):
        member_keys[episode] = 10_000 + reset_rng.permutation(n)
        canonical_keys = 20_000 + reset_rng.permutation(entities)
        entity_keys[:, episode, :] = canonical_keys
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
        member_keys=member_keys,
        entity_keys=entity_keys,
        agent_orders=agent_orders,
        entity_orders=entity_orders,
        sampling_uniforms=sampling_uniforms,
    )
    ledger.validate()
    return ledger


class AnonymousMultiRateQueueBatch:
    """Vectorized fixed-horizon AMQA transition kernel."""

    def __init__(self, ledger: EpisodeLedger):
        ledger.validate()
        self.ledger = ledger
        self.n = int(ledger.active_n)
        self.batch_size = int(ledger.batch_size)
        self.persistent = self.n // 2
        self.burst = self.n + 1 - self.persistent
        self.productive = self.persistent + self.burst
        self.entities = self.productive + 1
        self.idle_action = self.productive
        self.persistent_slice = slice(0, self.persistent)
        self.burst_slice = slice(self.persistent, self.productive)

        self.persistent_backlog = np.zeros(
            (self.batch_size, self.persistent), dtype=np.int64
        )
        self.persistent_arrived = np.zeros_like(self.persistent_backlog)
        self.persistent_served = np.zeros_like(self.persistent_backlog)
        self.burst_work = np.zeros(
            (self.batch_size, self.burst), dtype=np.int64
        )
        self.burst_deadline = np.zeros_like(self.burst_work)
        self.burst_arrived = np.zeros_like(self.burst_work)
        self.burst_served = np.zeros_like(self.burst_work)
        self.burst_expired = np.zeros_like(self.burst_work)
        self.persistent_new_arrival = np.zeros_like(
            self.persistent_backlog, dtype=np.bool_
        )
        self.burst_new_arrival = np.zeros_like(
            self.burst_work, dtype=np.bool_
        )
        self.previous_actions = np.full(
            (self.batch_size, self.n), -1, dtype=np.int64
        )
        self.served_previous = np.zeros(
            (self.batch_size, self.n), dtype=np.bool_
        )
        self.selected_previous_counts = np.zeros(
            (self.batch_size, self.entities), dtype=np.int64
        )
        self.time = 0
        self.nonterminal_reward_nonzero = 0
        self.final_reward_predicate_mismatch = 0
        self.invalid_action_count = 0
        self.capacity_violation_count = 0
        self.idle_selections = np.zeros(self.batch_size, dtype=np.int64)
        self.total_selections = np.zeros(self.batch_size, dtype=np.int64)

    def prepare_step(self, step: int) -> None:
        if int(step) != self.time:
            raise ValueError(
                f"RCMA clock mismatch: expected {self.time}, got {step}"
            )
        self.persistent_new_arrival.fill(False)
        self.burst_new_arrival.fill(False)
        if step in PERSISTENT_ARRIVAL_STEPS:
            self.persistent_backlog += 1
            self.persistent_arrived += 1
            self.persistent_new_arrival.fill(True)
        if step in BURST_WAVE_STEPS:
            if np.any(self.burst_work != 0):
                raise RuntimeError("RCMA burst waves overlap unexpectedly")
            self.burst_work.fill(1)
            self.burst_deadline.fill(BURST_DEADLINE)
            self.burst_arrived += 1
            self.burst_new_arrival.fill(True)

    def observations(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return member/entity views, static mask, and critic-only fields."""

        self_view = np.zeros(
            (self.batch_size, self.n, SELF_FEATURE_DIM), dtype=np.float32
        )
        self_view[:, :, 0] = (self.previous_actions >= 0).astype(np.float32)
        self_view[:, :, 1] = self.served_previous.astype(np.float32)

        entities = np.zeros(
            (self.batch_size, self.entities, ENTITY_FEATURE_DIM),
            dtype=np.float32,
        )
        entities[:, : self.productive, 0] = 1.0
        entities[:, self.persistent_slice, 1] = (
            self.persistent_backlog.astype(np.float32) / 8.0
        )
        entities[:, self.burst_slice, 1] = (
            self.burst_work.astype(np.float32) / 8.0
        )
        entities[:, self.persistent_slice, 2] = (
            self.persistent_new_arrival.astype(np.float32)
        )
        entities[:, self.burst_slice, 2] = (
            self.burst_new_arrival.astype(np.float32)
        )
        entities[:, self.burst_slice, 3] = (
            self.burst_deadline.astype(np.float32) / BURST_DEADLINE
        )
        persistent_denominator = np.maximum(self.persistent_arrived, 1)
        burst_denominator = np.maximum(self.burst_arrived, 1)
        entities[:, self.persistent_slice, 4] = np.where(
            self.persistent_arrived > 0,
            self.persistent_served / persistent_denominator,
            0.0,
        ).astype(np.float32)
        entities[:, self.burst_slice, 4] = np.where(
            self.burst_arrived > 0,
            self.burst_served / burst_denominator,
            0.0,
        ).astype(np.float32)
        entities[:, self.burst_slice, 5] = np.where(
            self.burst_arrived > 0,
            self.burst_expired / burst_denominator,
            0.0,
        ).astype(np.float32)
        entities[:, :, 6] = (
            self.selected_previous_counts.astype(np.float32) / float(self.n)
        )
        static_mask = np.ones(
            (self.batch_size, self.entities), dtype=np.bool_
        )
        critic_fields = np.stack(
            (
                np.full(
                    self.batch_size, self.time / HORIZON, dtype=np.float32
                ),
                self.persistent_backlog.sum(axis=1).astype(np.float32)
                / float(8 * self.persistent),
                self.persistent_served.sum(axis=1).astype(np.float32)
                / float(8 * self.persistent),
                self.burst_served.sum(axis=1).astype(np.float32)
                / float(2 * self.burst),
            ),
            axis=1,
        )
        return self_view, entities, static_mask, critic_fields

    def _terminal_metrics(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        persistent_fraction = 1.0 - (
            self.persistent_backlog.sum(axis=1).astype(np.float64)
            / float(8 * self.persistent)
        )
        burst_fraction = (
            self.burst_served.sum(axis=1).astype(np.float64)
            / float(2 * self.burst)
        )
        utility = np.sqrt(
            np.clip(persistent_fraction, 0.0, 1.0)
            * np.clip(burst_fraction, 0.0, 1.0)
        )
        return (
            persistent_fraction.astype(np.float32),
            burst_fraction.astype(np.float32),
            utility.astype(np.float32),
        )

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        if tuple(actions.shape) != (self.batch_size, self.n):
            raise ValueError("RCMA action shape mismatch")
        if np.any(actions < 0) or np.any(actions >= self.entities):
            self.invalid_action_count += int(
                np.count_nonzero((actions < 0) | (actions >= self.entities))
            )
            raise ValueError("RCMA action outside entity range")

        served_by_agent = np.zeros(
            (self.batch_size, self.n), dtype=np.bool_
        )
        selected_counts = np.zeros(
            (self.batch_size, self.entities), dtype=np.int64
        )
        for episode in range(self.batch_size):
            counts = np.bincount(
                actions[episode], minlength=self.entities
            ).astype(np.int64)
            selected_counts[episode] = counts
            productive_violation = np.maximum(
                counts[: self.productive] - 1, 0
            ).sum()
            idle_violation = max(int(counts[self.idle_action]) - self.n, 0)
            if productive_violation or idle_violation:
                self.capacity_violation_count += int(
                    productive_violation + idle_violation
                )
                raise ValueError("RCMA heterogeneous capacity violated")
            for agent, action in enumerate(actions[episode]):
                entity = int(action)
                if entity < self.persistent:
                    if self.persistent_backlog[episode, entity] > 0:
                        self.persistent_backlog[episode, entity] -= 1
                        self.persistent_served[episode, entity] += 1
                        served_by_agent[episode, agent] = True
                elif entity < self.productive:
                    burst_index = entity - self.persistent
                    if self.burst_work[episode, burst_index] > 0:
                        self.burst_work[episode, burst_index] = 0
                        self.burst_served[episode, burst_index] += 1
                        served_by_agent[episode, agent] = True
            self.idle_selections[episode] += counts[self.idle_action]
            self.total_selections[episode] += self.n

        still_live = self.burst_work > 0
        previous_deadline = self.burst_deadline.copy()
        self.burst_deadline[still_live] = np.maximum(
            self.burst_deadline[still_live] - 1, 0
        )
        expired_now = (
            still_live
            & (previous_deadline > 0)
            & (self.burst_deadline == 0)
        )
        self.burst_expired[expired_now] += 1
        self.burst_work[expired_now] = 0

        self.previous_actions = actions.astype(np.int64, copy=True)
        self.served_previous = served_by_agent
        self.selected_previous_counts = selected_counts

        persistent_fraction, burst_fraction, utility = self._terminal_metrics()
        final_step = self.time == HORIZON - 1
        reward = (
            utility.copy()
            if final_step
            else np.zeros(self.batch_size, dtype=np.float32)
        )
        if not final_step:
            self.nonterminal_reward_nonzero += int(np.count_nonzero(reward))
        else:
            self.final_reward_predicate_mismatch += int(
                np.count_nonzero(np.abs(reward - utility) > 1.0e-7)
            )
        self.time += 1
        return reward, {
            "utility": utility.copy(),
            "persistent_fraction": persistent_fraction.copy(),
            "burst_fraction": burst_fraction.copy(),
            "served_now": served_by_agent.sum(axis=1),
            "expired_now": expired_now.sum(axis=1),
        }

    def diagnostics(self) -> dict[str, Any]:
        persistent_fraction, burst_fraction, utility = self._terminal_metrics()
        return {
            "utility": utility,
            "persistent_fraction": persistent_fraction,
            "burst_fraction": burst_fraction,
            "final_persistent_backlog": self.persistent_backlog.sum(
                axis=1
            ).astype(np.int64),
            "timely_burst_completions": self.burst_served.sum(
                axis=1
            ).astype(np.int64),
            "expired_burst_jobs": self.burst_expired.sum(axis=1).astype(
                np.int64
            ),
            "idle_selection_fraction": self.idle_selections.astype(np.float32)
            / np.maximum(self.total_selections, 1),
            "nonterminal_reward_nonzero": int(self.nonterminal_reward_nonzero),
            "final_reward_predicate_mismatch": int(
                self.final_reward_predicate_mismatch
            ),
            "invalid_action_count": int(self.invalid_action_count),
            "capacity_violation_count": int(self.capacity_violation_count),
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
    residual_capacities: torch.Tensor
    dynamic_masks: torch.Tensor
    masked_probability_mass: torch.Tensor
    focal_relation_counts: torch.Tensor


class RCMASetPointerPolicy(nn.Module):
    """Anonymous recurrent pointer actor-critic with heterogeneous capacity."""

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
        focal_previous_actions: torch.Tensor,
        sampling_uniforms: torch.Tensor | None = None,
        teacher_pointers: torch.Tensor | None = None,
        deterministic: bool = False,
    ) -> PointerStepOutput:
        batch, active_n, feature_dim = self_features.shape
        entities = int(entity_features.shape[1])
        if feature_dim != SELF_FEATURE_DIM:
            raise ValueError("RCMA self feature dimension mismatch")
        if tuple(entity_features.shape) != (batch, entities, ENTITY_FEATURE_DIM):
            raise ValueError("RCMA entity feature dimension mismatch")
        if entities != active_n + 2:
            raise ValueError("RCMA action entity count must equal N+2")
        if tuple(entity_mask.shape) != (batch, entities):
            raise ValueError("RCMA entity mask shape mismatch")
        if tuple(agent_order.shape) != (batch, active_n):
            raise ValueError("RCMA agent order shape mismatch")
        if tuple(entity_order.shape) != (batch, entities):
            raise ValueError("RCMA entity order shape mismatch")
        if tuple(hidden.shape) != (batch, active_n, HIDDEN_DIM):
            raise ValueError("RCMA recurrent hidden shape mismatch")
        if tuple(hidden_reset_mask.shape) != (batch, active_n):
            raise ValueError("RCMA hidden reset mask shape mismatch")
        if tuple(critic_fields.shape) != (batch, CRITIC_FIELD_DIM):
            raise ValueError("RCMA critic field shape mismatch")
        if tuple(focal_previous_actions.shape) != (batch, active_n):
            raise ValueError("RCMA previous-action shape mismatch")
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
        canonical_capacity = torch.ones(
            (batch, entities), dtype=self_features.dtype, device=device
        )
        canonical_capacity[:, -1] = float(active_n)
        presented_initial_capacity = torch.gather(
            canonical_capacity, 1, entity_order
        )
        pointers: list[torch.Tensor] = []
        actions_by_agent = torch.empty(
            (batch, active_n), dtype=torch.long, device=device
        )
        log_probs: list[torch.Tensor] = []
        entropies: list[torch.Tensor] = []
        prefixes: list[torch.Tensor] = []
        residuals: list[torch.Tensor] = []
        dynamic_masks: list[torch.Tensor] = []
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
            residual_capacity = presented_initial_capacity - planned_counts
            normalized_residual = residual_capacity / presented_initial_capacity
            dynamic_mask = presented_mask & residual_capacity.gt(0.0)
            focal_previous_action = focal_previous_actions[
                batch_indices, agent_indices
            ]
            focal_relation = entity_order.eq(
                focal_previous_action.unsqueeze(-1)
            ).to(
                entity_embeddings.dtype
            )
            keys = self.entity_key(
                torch.cat(
                    (
                        entity_embeddings,
                        normalized_residual.unsqueeze(-1),
                        focal_relation.unsqueeze(-1),
                    ),
                    dim=-1,
                )
            )
            logits = torch.einsum("bd,bed->be", query, keys) / math.sqrt(
                HIDDEN_DIM
            )
            logits = logits.masked_fill(~dynamic_mask, -torch.inf)
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
                torch.gather(dynamic_mask, 1, selected.unsqueeze(-1)).all()
            ):
                raise RuntimeError("RCMA pointer selected an exhausted entity")
            prefixes.append(planned_counts.clone())
            residuals.append(residual_capacity.clone())
            dynamic_masks.append(dynamic_mask.clone())
            selected_log_probability = torch.gather(
                log_probability, 1, selected.unsqueeze(-1)
            ).squeeze(-1)
            safe_log_probability = torch.where(
                dynamic_mask,
                log_probability,
                torch.zeros_like(log_probability),
            )
            entropy = -torch.sum(
                probability * safe_log_probability, dim=-1
            )
            masked_mass = torch.sum(
                torch.where(~dynamic_mask, probability, 0.0), dim=-1
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
            residual_capacities=torch.stack(residuals, dim=1),
            dynamic_masks=torch.stack(dynamic_masks, dim=1),
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
