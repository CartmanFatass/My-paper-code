"""Construction-only schemas for the future atomic empirical lifecycle.

No checkpoint, coordinate, evaluation row, or result is created here.  The
module only validates the frozen slot declarations and the barrier that a
future runner must satisfy before evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


REPLICATES = tuple(range(18))
LEARNED_ARMS = ("TREAT", "FREE", "SET")
EVALUATION_CONTROLLERS = ("TREAT", "FREE", "REVERSED", "SET")
EVALUATION_REGIMES = ("fixed-4", "fixed-10", "fixed-6", "fixed-14", "6-to-14", "14-to-6")
EPISODES_PER_CELL = 120
REQUIRED_CHECKPOINT_SLOTS = frozenset(
    (replicate, arm) for replicate in REPLICATES for arm in LEARNED_ARMS
)


class LifecycleBarrierError(RuntimeError):
    pass


@dataclass(frozen=True)
class CheckpointBarrierReceipt:
    accepted_slots: int
    required_slots: int
    all_before_evaluation: bool
    evaluation_values_observed: bool


def require_all_checkpoints_before_evaluation(
    technically_accepted_slots: Iterable[tuple[int, str]],
    *,
    evaluation_values_observed: bool = False,
) -> CheckpointBarrierReceipt:
    slots = tuple(technically_accepted_slots)
    if len(slots) != len(set(slots)):
        raise LifecycleBarrierError("checkpoint acceptance slots contain duplicates")
    accepted = frozenset(slots)
    if accepted != REQUIRED_CHECKPOINT_SLOTS:
        missing = len(REQUIRED_CHECKPOINT_SLOTS - accepted)
        extra = len(accepted - REQUIRED_CHECKPOINT_SLOTS)
        raise LifecycleBarrierError(
            f"evaluation remains closed until all 54 learned slots are accepted "
            f"(missing={missing}, extra={extra})"
        )
    if evaluation_values_observed:
        raise LifecycleBarrierError(
            "checkpoint barrier admission must precede every evaluation observation"
        )
    return CheckpointBarrierReceipt(
        accepted_slots=len(accepted),
        required_slots=54,
        all_before_evaluation=True,
        evaluation_values_observed=False,
    )


def atomic_panel_shape() -> dict[str, object]:
    return {
        "replicates": 18,
        "learned_arms": LEARNED_ARMS,
        "controllers": EVALUATION_CONTROLLERS,
        "regimes": EVALUATION_REGIMES,
        "episodes_per_cell": EPISODES_PER_CELL,
        "episode_count": 18 * 4 * 6 * 120,
        "learned_checkpoint_count": 18 * 3,
        "checkpoint_barrier": "all_54_technically_accepted_before_any_evaluation",
        "fixed_regime_balance": {
            "event_orders": ("RG", "GR"),
            "episodes_per_order": 60,
        },
        "switch_regime_balance": {
            "event_orders": ("RG", "GR"),
            "switch_ticks": (168, 252),
            "episodes_per_order_time_cell": 30,
        },
        "support_panel": {
            "replicates": 18,
            "fixed_k": (6, 14),
            "public_states_per_k": 72,
            "histories": ("RG", "GR"),
            "actions": 27,
            "action_intervals": 139_968,
            "maximum_primitive_ticks": 1_399_680,
            "shared_disturbance_tape_within_state_k": True,
        },
        "claim_endpoint_families": ("P", "W", "T", "E", "O", "G", "F"),
        "simultaneous_families": {
            "competence_one_sided_bounds": 15,
            "support_action_one_sided_bounds": 3,
            "direct_two_sided_intervals": 17,
        },
        "registered_workload": {
            "training_episodes": 93_312,
            "training_allocated_slots": 39_191_040,
            "maximum_training_policy_decisions": 6_858_432,
            "adamw_steps": 124_416,
            "maximum_minibatch_record_traversals": 27_433_728,
            "evaluation_episodes": 51_840,
            "evaluation_allocated_slots": 21_772_800,
            "maximum_evaluation_policy_decisions": 2_998_080,
            "support_action_intervals": 139_968,
            "maximum_support_primitive_ticks": 1_399_680,
            "full_primitive_slot_upper_bound": 62_363_520,
        },
        "atomic": True,
        "partial_inspection_permitted": False,
    }


def require_complete_atomic_panel_declaration(declaration: Mapping[str, object]) -> None:
    if dict(declaration) != atomic_panel_shape():
        raise LifecycleBarrierError("future panel declaration is partial or differs from the frozen shape")
