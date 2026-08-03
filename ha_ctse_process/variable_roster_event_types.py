"""Immutable and mutable transport types for the variable-roster event runtime."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np
import torch


MEMBERSHIP_KINDS = ("JOIN", "TEMPORARY_LEAVE", "TERMINAL_LEAVE", "REJOIN")


def _float_array(value: Any, *, size: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32).reshape(-1)
    if tuple(array.shape) != (int(size),):
        raise ValueError(f"{name} must have shape [{size}]")
    if not bool(np.all(np.isfinite(array))):
        raise ValueError(f"{name} contains a non-finite value")
    return array.copy()


@dataclass(frozen=True)
class BoundaryMember:
    """One physical member row carried by a typed boundary transaction.

    ``lifecycle_key`` and ``membership_epoch`` are routing-only.  The model
    receives only the observation and critic feature arrays.
    """

    lifecycle_key: str
    membership_epoch: int
    observation: np.ndarray
    critic_member_features: np.ndarray

    @classmethod
    def make(
        cls,
        lifecycle_key: str,
        membership_epoch: int,
        observation: Any,
        critic_member_features: Any,
        *,
        obs_dim: int,
        critic_member_dim: int,
    ) -> "BoundaryMember":
        key = str(lifecycle_key)
        if not key:
            raise ValueError("lifecycle_key must be non-empty")
        return cls(
            lifecycle_key=key,
            membership_epoch=int(membership_epoch),
            observation=_float_array(observation, size=obs_dim, name="observation"),
            critic_member_features=_float_array(
                critic_member_features,
                size=critic_member_dim,
                name="critic_member_features",
            ),
        )


@dataclass(frozen=True)
class BoundarySnapshot:
    physical_time: int
    members: tuple[BoundaryMember, ...]
    critic_global_features: np.ndarray
    frontier: tuple[str, ...] = ()

    @classmethod
    def make(
        cls,
        physical_time: int,
        members: Sequence[BoundaryMember],
        critic_global_features: Any,
        *,
        critic_global_dim: int,
        frontier: Sequence[str] = (),
    ) -> "BoundarySnapshot":
        rows = tuple(members)
        keys = tuple(row.lifecycle_key for row in rows)
        if len(keys) != len(set(keys)):
            raise ValueError("boundary snapshot contains duplicate lifecycle keys")
        frontier_keys = tuple(str(key) for key in frontier)
        if len(frontier_keys) != len(set(frontier_keys)):
            raise ValueError("boundary frontier contains duplicate lifecycle keys")
        if not set(frontier_keys).issubset(set(keys)):
            raise ValueError("boundary frontier contains an inactive lifecycle")
        return cls(
            physical_time=int(physical_time),
            members=rows,
            critic_global_features=_float_array(
                critic_global_features,
                size=critic_global_dim,
                name="critic_global_features",
            ),
            frontier=frontier_keys,
        )

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(member.lifecycle_key for member in self.members)


@dataclass(frozen=True)
class MembershipDelta:
    kind: str
    lifecycle_key: str
    expected_membership_epoch: int

    def __post_init__(self) -> None:
        if str(self.kind) not in MEMBERSHIP_KINDS:
            raise ValueError(f"unsupported membership delta kind {self.kind!r}")
        if not str(self.lifecycle_key):
            raise ValueError("membership delta lifecycle key must be non-empty")


@dataclass(frozen=True)
class MembershipTransaction:
    pre_membership_boundary_snapshot: BoundarySnapshot
    atomic_membership_delta: tuple[MembershipDelta, ...]
    post_membership_pre_policy_snapshot: BoundarySnapshot

    def __post_init__(self) -> None:
        deltas = tuple(self.atomic_membership_delta)
        keys = tuple(delta.lifecycle_key for delta in deltas)
        if len(keys) != len(set(keys)):
            raise ValueError("one transaction cannot mutate a lifecycle twice")
        if (
            int(self.pre_membership_boundary_snapshot.physical_time)
            != int(self.post_membership_pre_policy_snapshot.physical_time)
        ):
            raise ValueError("transaction snapshots must share physical time")


@dataclass
class OpenEventTrace:
    start_time: int
    policy_version: int
    actor_valid: bool
    old_value: float
    old_log_probability: float | None
    token_ledger_index: int | None
    discounted_reward: float = 0.0
    elapsed_physical_time: int = 0

    def accumulate(self, reward: float, gamma: float) -> None:
        self.discounted_reward += (float(gamma) ** self.elapsed_physical_time) * float(
            reward
        )
        self.elapsed_physical_time += 1


@dataclass
class LifecycleRecord:
    lifecycle_key: str
    status: str
    membership_epoch: int
    low_actor_hidden: np.ndarray
    low_critic_hidden: np.ndarray
    high_hidden: np.ndarray
    active_skill: int | None
    skill_active_age: int
    active_gap_remaining: int | None
    last_policy_event_time: int | None
    open_event_trace: OpenEventTrace | None
    policy_version: int
    is_genuine_join: bool = False
    is_rejoin: bool = False

    def clone(self) -> "LifecycleRecord":
        return deepcopy(self)


@dataclass(frozen=True)
class ClosedEventRow:
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    actor_valid: bool
    start_time: int
    end_time: int
    elapsed_physical_time: int
    discounted_reward: float
    old_value: float
    bootstrap_value: float
    bootstrap_discount: float
    return_target: float
    old_log_probability: float | None
    token_ledger_index: int | None
    boundary_kind: str


@dataclass(frozen=True)
class EventTokenRow:
    environment_index: int
    policy_version: int
    physical_event_time: int
    owner_lifecycle_key: str
    membership_epoch: int
    frontier: tuple[str, ...]
    sampled_order: tuple[str, ...]
    order_log_probability: float
    token_position: int
    sampled_replacement_gap: int
    active_lifecycle_keys: tuple[str, ...]
    active_membership_epochs: tuple[int, ...]
    active_observations: np.ndarray
    active_critic_member_features: np.ndarray
    critic_global_features: np.ndarray
    event_flags: np.ndarray
    initial_skills: np.ndarray
    initial_ages: np.ndarray
    pre_token_working_skills: np.ndarray
    pre_token_working_ages: np.ndarray
    post_token_working_skills: np.ndarray
    post_token_working_ages: np.ndarray
    active_high_hidden: np.ndarray
    pre_token_high_hidden: np.ndarray
    exact_legal_mask: np.ndarray
    policy_action_uniform: float | None
    combined_action: int
    old_token_log_probability: float
    old_owner_value: float
    action_kind: str


@dataclass
class LowTransitionRow:
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    physical_time: int
    observation: np.ndarray
    skill: int
    action: np.ndarray
    old_log_probability: float
    old_value: float
    actor_hidden_before: np.ndarray
    critic_hidden_before: np.ndarray
    critic_member_features: np.ndarray
    active_critic_member_features: np.ndarray
    active_skills: np.ndarray
    critic_global_features: np.ndarray
    focal_active_index: int
    critic_source_summary: np.ndarray
    policy_action_uniform: float | None = None
    reward: float | None = None
    terminal_or_truncation_kind: str | None = None
    environment_step_pointer: int = 0
    lifecycle_chunk_pointer: int = 0
    bootstrap_source: str | None = None
    bootstrap_value: float | None = None


@dataclass(frozen=True)
class PackedActiveBatch:
    """Model-facing active-only tensors.  Routing metadata is excluded."""

    env_ptr: torch.Tensor
    member_obs: torch.Tensor
    critic_member_features: torch.Tensor
    critic_global_features: torch.Tensor
    skills: torch.Tensor
    active_ages: torch.Tensor
    event_flags: torch.Tensor
    low_actor_hidden: torch.Tensor
    low_critic_hidden: torch.Tensor
    high_hidden: torch.Tensor


@dataclass(frozen=True)
class ActiveRoutingView:
    lifecycle_keys: tuple[str, ...]
    membership_epochs: tuple[int, ...]


@dataclass(frozen=True)
class EventTransactionResult:
    sampled_order: tuple[str, ...]
    order_log_probability: float
    token_rows: tuple[EventTokenRow, ...]
    final_skills: dict[str, int]


@dataclass(frozen=True)
class EventActionHook:
    """Stable read-only semantic hook for one executed KEEP/SET token."""

    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    physical_time: int
    action_kind: str
    previous_skill: int | None
    next_skill: int


@dataclass(frozen=True)
class LifecycleBoundaryHook:
    lifecycle_key: str
    expected_membership_epoch: int
    boundary_kind: str
    physical_time: int


@dataclass(frozen=True)
class LowRowIndexHook:
    low_row_index: int
    lifecycle_key: str
    membership_epoch: int
    policy_version: int
    physical_time: int
    skill: int


def event_action_hooks(result: EventTransactionResult) -> tuple[EventActionHook, ...]:
    hooks: list[EventActionHook] = []
    for row in result.token_rows:
        owner_index = row.active_lifecycle_keys.index(row.owner_lifecycle_key)
        previous = int(row.pre_token_working_skills[owner_index])
        hooks.append(
            EventActionHook(
                lifecycle_key=row.owner_lifecycle_key,
                membership_epoch=int(row.membership_epoch),
                policy_version=int(row.policy_version),
                physical_time=int(row.physical_event_time),
                action_kind=str(row.action_kind),
                previous_skill=None if previous < 0 else previous,
                next_skill=int(row.combined_action),
            )
        )
    return tuple(hooks)


def lifecycle_boundary_hooks(
    transaction: MembershipTransaction,
) -> tuple[LifecycleBoundaryHook, ...]:
    physical_time = int(transaction.post_membership_pre_policy_snapshot.physical_time)
    return tuple(
        LifecycleBoundaryHook(
            lifecycle_key=delta.lifecycle_key,
            expected_membership_epoch=int(delta.expected_membership_epoch),
            boundary_kind=str(delta.kind),
            physical_time=physical_time,
        )
        for delta in transaction.atomic_membership_delta
    )


def low_row_index_hooks(
    core: "VariableRosterEventCore", start_index: int
) -> tuple[LowRowIndexHook, ...]:
    start = int(start_index)
    if not 0 <= start <= len(core.low_ledger):
        raise ValueError("low-row hook start index is outside the ledger")
    return tuple(
        LowRowIndexHook(
            low_row_index=index,
            lifecycle_key=row.lifecycle_key,
            membership_epoch=int(row.membership_epoch),
            policy_version=int(row.policy_version),
            physical_time=int(row.physical_time),
            skill=int(row.skill),
        )
        for index, row in enumerate(core.low_ledger[start:], start=start)
    )


@dataclass(frozen=True)
class EventPPOLosses:
    high_loss: torch.Tensor
    low_loss: torch.Tensor
    high_policy_loss: torch.Tensor
    high_value_loss: torch.Tensor
    low_policy_loss: torch.Tensor
    low_value_loss: torch.Tensor
    high_entropy: torch.Tensor
    low_entropy: torch.Tensor
    high_rows: int
    low_rows: int
    high_logp_max_error: float
    high_value_max_error: float
    low_logp_max_error: float
    low_value_max_error: float


@dataclass(frozen=True)
class EventHighPPOLosses:
    """The high half of :class:`EventPPOLosses`, with no low-policy surface."""

    high_loss: torch.Tensor
    high_policy_loss: torch.Tensor
    high_value_loss: torch.Tensor
    high_entropy: torch.Tensor
    high_rows: int
    high_logp_max_error: float
    high_value_max_error: float


@dataclass(frozen=True)
class BatchedLowStepResult:
    """Cross-environment low-policy outputs plus already-routed CPU actions."""

    per_core: tuple[tuple[torch.Tensor, torch.Tensor, torch.Tensor], ...]
    routed_actions: tuple[dict[str, int], ...]


@dataclass(frozen=True)
class PackedEventHighReplay:
    core: "VariableRosterEventCore"
    observations: torch.Tensor
    flags: torch.Tensor
    initial_skills: torch.Tensor
    initial_ages: torch.Tensor
    working_skills: torch.Tensor
    working_ages: torch.Tensor
    pre_hidden: torch.Tensor
    legal_mask: torch.Tensor
    active_high_hidden: torch.Tensor
    critic_member_features: torch.Tensor
    critic_global_features: torch.Tensor
    owner_index: int
    action: int
    old_logp: torch.Tensor
    old_value: torch.Tensor
    target: torch.Tensor
    advantage: torch.Tensor


@dataclass(frozen=True)
class PackedEventLowReplay:
    core: "VariableRosterEventCore"
    observations: torch.Tensor
    skills: torch.Tensor
    actions: torch.Tensor
    actor_initial_hidden: torch.Tensor
    valid_masks: torch.Tensor
    reset_masks: torch.Tensor
    active_member_features: torch.Tensor
    active_skills: torch.Tensor
    active_masks: torch.Tensor
    focal_indices: torch.Tensor
    global_features: torch.Tensor
    critic_initial_hidden: torch.Tensor
    old_logp: torch.Tensor
    old_value: torch.Tensor
    advantages: torch.Tensor
    targets: torch.Tensor
    row_count: int


@dataclass(frozen=True)
class PackedEventPPOData:
    """Immutable rollout tensors reused by every PPO pass."""

    cores: tuple["VariableRosterEventCore", ...]
    high: tuple[PackedEventHighReplay, ...]
    low: PackedEventLowReplay


@dataclass(frozen=True)
class PackedEventHighPPOData:
    """Immutable owner-GAE replay reused by every high-only PPO pass."""

    cores: tuple["VariableRosterEventCore", ...]
    high: tuple[PackedEventHighReplay, ...]
