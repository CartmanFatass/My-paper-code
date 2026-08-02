"""Direct semantic owners for event-held commitment types and arm model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import torch
from torch import nn

from ha_ctse_process.dynamic_roster_direct import DirectPrimitiveARPolicy
from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, OBSERVATION_DIM
from ha_ctse_process.noncalendar_commitment_testbed import (
    NoncalendarLedger,
    NoncalendarTrackingEnv,
    TrackingOutcome,
)

ArmName = Literal["OR", "DUM", "EHC"]
EVENT_INPUT_DIM = OBSERVATION_DIM + 32 + 32 + 8
MARK_DIM = 8


@dataclass
class SegmentRecord:
    episode_id: int
    key: int
    membership_epoch: int
    segment_id: int
    start_active_step: int
    end_active_step: int
    censored: bool
    close_reason: str
    opportunity_count: int

    @property
    def active_lifetime(self) -> int:
        return self.end_active_step - self.start_active_step


@dataclass
class LifecycleState:
    membership_epoch: int
    z: torch.Tensor
    q: int
    segment_id: int
    segment_start_active_step: int
    active_steps: int = 0
    non_create_opportunities: int = 0
    spell_opportunity_count: int = 0
    """Running `K` (KEEP/RENEW opportunities so far) for the currently open
    spell only; reset to 0 only when a RENEW closes that spell and opens the
    next one. At CREATE (`LifecycleState` construction) it is
    zero-initialized, not reset -- there is no prior spell to reset from.
    Distinct from `non_create_opportunities`, which accumulates across all
    spells of this lifecycle and is never reset."""


@dataclass
class CollectionCursor:
    episode_ids: tuple[int, ...]
    ledgers: tuple[NoncalendarLedger, ...]
    environments: list[NoncalendarTrackingEnv]
    hidden: torch.Tensor
    lifecycles: list[dict[int, LifecycleState]]
    segments: list[list[SegmentRecord]]


@dataclass
class EventTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    orders: torch.Tensor
    actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    terminal: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    primitive_z: torch.Tensor
    event_kind: torch.Tensor
    event_inputs: torch.Tensor
    event_categorical_actions: torch.Tensor
    event_u: torch.Tensor
    event_z_pre: torch.Tensor
    event_new_z: torch.Tensor
    candidate_u: torch.Tensor
    candidate_z: torch.Tensor
    event_cat_mask: torch.Tensor
    event_mark_mask: torch.Tensor
    event_old_cat_logp: torch.Tensor
    event_old_mark_component_logp: torch.Tensor
    event_old_joint_logp: torch.Tensor
    membership_epoch: torch.Tensor
    segment_id: torch.Tensor
    q_before: torch.Tensor
    raw_event_trace: tuple[dict[str, Any], ...]
    outcomes: tuple[TrackingOutcome, ...]
    segments: tuple[tuple[SegmentRecord, ...], ...]
    ledger_ids: tuple[int, ...]
    cutoff: bool
    bootstrap_values: torch.Tensor
    rng_audit: dict[str, Any]
    cursor: CollectionCursor | None

    @property
    def time_steps(self) -> int:
        return int(self.rewards.shape[0])


class CommitmentArm(nn.Module):
    """Ordinary source base plus the exact DUM/EHC additions."""

    def __init__(self, arm: ArmName) -> None:
        super().__init__()
        if arm not in ("OR", "DUM", "EHC"):
            raise ValueError("invalid commitment arm")
        self.arm: ArmName = arm
        self.base = DirectPrimitiveARPolicy()
        if arm != "OR":
            self.W_z = nn.Linear(MARK_DIM, ACTION_COUNT, bias=False)
            self.event_head = nn.Linear(EVENT_INPUT_DIM, 2)
            self.mark_head = nn.Linear(EVENT_INPUT_DIM, 2 * MARK_DIM)
        else:
            self.W_z = None
            self.event_head = None
            self.mark_head = None

    @property
    def treatment(self) -> int:
        return int(self.arm == "EHC")

    @property
    def base_parameter_count(self) -> int:
        return sum(p.numel() for p in self.base.parameters())

    @property
    def added_parameter_count(self) -> int:
        return sum(
            p.numel()
            for name, p in self.named_parameters()
            if not name.startswith("base.")
        )

    def primitive_bias(self, z: torch.Tensor) -> torch.Tensor | None:
        if self.W_z is None:
            return None
        return self.W_z(float(self.treatment) * z.detach())

    def event_parameters(self) -> list[nn.Parameter]:
        if self.arm == "OR":
            return []
        assert self.event_head is not None and self.mark_head is not None
        return [*self.event_head.parameters(), *self.mark_head.parameters()]

    def base_optimizer_parameters(self) -> list[nn.Parameter]:
        values = list(self.base.parameters())
        if self.W_z is not None:
            values.extend(self.W_z.parameters())
        return values


@dataclass
class TrainingState:
    arm: ArmName
    replicate: int
    profile: Literal["train", "iid", "held_out"] = "train"
    seed_map: dict[str, int] = field(default_factory=dict)
    completed_update: int = 0
    next_episode_id: int = 0
    base_optimizer_steps: int = 0
    event_optimizer_steps: int = 0
    pending_cursor: CollectionCursor | None = None
    rngs: dict[str, np.random.Generator] = field(default_factory=dict)
