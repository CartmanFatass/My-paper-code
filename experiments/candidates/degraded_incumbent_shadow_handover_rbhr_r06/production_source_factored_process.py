"""Source-specific masked observation normalization for DISH PSF R01.

This module is additive.  In particular, it deliberately does not import the
legacy scalar-count Welford implementation: actor, accepted snapshots, and
critic observations have independent per-coordinate state here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .production_source_factored_backend import (
    LaneCausalFacts,
    test_only_two_owner_batch,
)


ACTOR_WIDTH = 54
SNAPSHOT_WIDTH = 18
CRITIC_WIDTH = 58
NORMALIZATION_EPSILON = 1e-8
NORMALIZATION_CLIP = (-10.0, 10.0)
ACTOR_UPDATE_ORDER = ("lane", "tick", "physical_uav", "copy_I_then_S")

# The scientific freeze specifies one-based coordinates.  The process seam
# exposes zero-based tuples because they index the NumPy observation tensors.
ACTOR_CONTINUOUS_ZERO_BASED = (
    *range(4, 11),
    12,
    13,
    *range(15, 25),
    26,
    *range(28, 36),
    41,
    42,
    48,
    50,
    52,
)
CRITIC_CONTINUOUS_ZERO_BASED = (
    *range(0, 11),
    12,
    13,
    *range(15, 18),
    19,
    20,
    *range(22, 29),
    30,
    31,
    *range(33, 36),
    37,
    38,
    *range(41, 45),
    47,
    48,
    53,
    54,
)

_ACTOR_PRESENCE_GATES = {
    12: 11,
    13: 11,
    26: 25,
    **{coordinate: 27 for coordinate in range(28, 36)},
    50: 49,
    52: 51,
}
_CRITIC_PRESENCE_GATES = {
    12: 11,
    13: 11,
    19: 18,
    20: 18,
    30: 29,
    31: 29,
    37: 36,
    38: 36,
    **{coordinate: 40 for coordinate in range(41, 45)},
}


def _continuous_mask(width: int, coordinates: tuple[int, ...]) -> np.ndarray:
    mask = np.zeros(width, dtype=np.bool_)
    mask[list(coordinates)] = True
    return mask


_ACTOR_CONTINUOUS_MASK = _continuous_mask(ACTOR_WIDTH, ACTOR_CONTINUOUS_ZERO_BASED)
_CRITIC_CONTINUOUS_MASK = _continuous_mask(CRITIC_WIDTH, CRITIC_CONTINUOUS_ZERO_BASED)


@dataclass
class _PerDimensionWelford:
    count: np.ndarray
    mean: np.ndarray
    m2: np.ndarray

    @classmethod
    def empty(cls, width: int) -> "_PerDimensionWelford":
        return cls(
            count=np.zeros(width, dtype=np.int64),
            mean=np.zeros(width, dtype=np.float64),
            m2=np.zeros(width, dtype=np.float64),
        )

    @property
    def variance(self) -> np.ndarray:
        result = np.ones(self.mean.shape, dtype=np.float64)
        established = self.count >= 2
        result[established] = self.m2[established] / (self.count[established] - 1)
        return result

    def normalize(self, rows: np.ndarray, present: np.ndarray) -> np.ndarray:
        result = np.zeros(rows.shape, dtype=np.float64)
        if np.any(present):
            inverse_scale = np.reciprocal(np.sqrt(self.variance + NORMALIZATION_EPSILON))
            normalized = (rows - self.mean) * inverse_scale
            np.clip(normalized, *NORMALIZATION_CLIP, out=normalized)
            result[present] = normalized[present]
        return result

    def update(self, rows: np.ndarray, present: np.ndarray) -> None:
        if rows.shape != present.shape or rows.ndim != 2:
            raise ValueError("Welford rows/presence shape differs")
        if np.any(~np.isfinite(rows[present])):
            raise ValueError("present Welford value must be finite")
        batch_counts = present.sum(axis=0, dtype=np.int64)
        if np.any(self.count > np.iinfo(np.int64).max - batch_counts):
            raise OverflowError("Welford count would overflow int64")
        # The flattening caller fixes lane -> tick -> physical UAV -> I/S.
        # Advance one collection row at a time: a batch mean/dot merge is
        # mathematically equivalent in exact arithmetic but not bit-equivalent
        # to the registered float64 Welford recurrence.
        for row, row_present in zip(rows, present):
            coordinates = np.flatnonzero(row_present)
            if coordinates.size == 0:
                continue
            next_count = self.count[coordinates] + np.int64(1)
            delta = row[coordinates] - self.mean[coordinates]
            next_mean = self.mean[coordinates] + delta / next_count
            self.m2[coordinates] += delta * (row[coordinates] - next_mean)
            self.mean[coordinates] = next_mean
            self.count[coordinates] = next_count

    def state_dict(self) -> dict[str, np.ndarray]:
        return {
            "count": self.count.copy(),
            "mean": self.mean.copy(),
            "m2": self.m2.copy(),
        }

    @classmethod
    def from_state_dict(
        cls,
        state: object,
        *,
        width: int,
        name: str,
        permitted: np.ndarray,
    ) -> "_PerDimensionWelford":
        if not isinstance(state, Mapping) or set(state) != {"count", "mean", "m2"}:
            raise ValueError(f"{name} Welford state schema differs")
        count = state["count"]
        mean = state["mean"]
        m2 = state["m2"]
        if not isinstance(count, np.ndarray) or count.dtype != np.dtype(np.int64):
            raise ValueError(f"{name} Welford count must be an int64 array")
        if not isinstance(mean, np.ndarray) or mean.dtype != np.dtype(np.float64):
            raise ValueError(f"{name} Welford mean must be a float64 array")
        if not isinstance(m2, np.ndarray) or m2.dtype != np.dtype(np.float64):
            raise ValueError(f"{name} Welford m2 must be a float64 array")
        expected_shape = (width,)
        if count.shape != expected_shape or mean.shape != expected_shape or m2.shape != expected_shape:
            raise ValueError(f"{name} Welford state shape differs")
        if np.any(count < 0):
            raise ValueError(f"{name} Welford count must be nonnegative")
        if np.any(~np.isfinite(mean)) or np.any(~np.isfinite(m2)):
            raise ValueError(f"{name} Welford state must be finite")
        if np.any(m2 < 0.0):
            raise ValueError(f"{name} Welford m2 must be nonnegative")
        if np.any((count < 2) & (m2 != 0.0)):
            raise ValueError(f"{name} Welford m2 differs below count two")
        if np.any((count == 0) & (mean != 0.0)):
            raise ValueError(f"{name} Welford mean differs at count zero")
        if np.any(~permitted & ((count != 0) | (mean != 0.0) | (m2 != 0.0))):
            raise ValueError(f"{name} passthrough coordinate has Welford state")
        return cls(count=count.copy(), mean=mean.copy(), m2=m2.copy())


def _as_observations(
    value: object,
    *,
    ndim: int,
    shape_tail: tuple[int, ...],
    name: str,
) -> np.ndarray:
    try:
        rows = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} observations must be numeric") from error
    if rows.ndim != ndim or rows.shape[-len(shape_tail):] != shape_tail:
        raise ValueError(f"{name} observation shape differs")
    return rows


def _field_presence(
    rows: np.ndarray,
    continuous: tuple[int, ...],
    gates: Mapping[int, int],
) -> np.ndarray:
    gate_coordinates = tuple(sorted(set(gates.values())))
    gate_values = rows[..., gate_coordinates]
    if np.any(~np.isfinite(gate_values)) or np.any((gate_values != 0.0) & (gate_values != 1.0)):
        raise ValueError("presence gate must be exactly numeric {0,1}")
    present = np.zeros(rows.shape, dtype=np.bool_)
    present[..., list(continuous)] = True
    for coordinate, gate in gates.items():
        present[..., coordinate] = rows[..., gate] != 0.0
    return present


def _validate_observed_values(rows: np.ndarray, present: np.ndarray, continuous_mask: np.ndarray, name: str) -> None:
    passthrough = np.broadcast_to(~continuous_mask, rows.shape)
    observed = present | passthrough
    if np.any(~np.isfinite(rows[observed])):
        raise ValueError(f"{name} observed value must be finite")


class SourceSpecificMaskedWelford:
    """Independent actor/snapshot/critic per-dimension Welford state."""

    def __init__(
        self,
        actor: _PerDimensionWelford,
        snapshot: _PerDimensionWelford,
        critic: _PerDimensionWelford,
    ) -> None:
        self.actor = actor
        self.snapshot = snapshot
        self.critic = critic

    @classmethod
    def empty(cls) -> "SourceSpecificMaskedWelford":
        return cls(
            actor=_PerDimensionWelford.empty(ACTOR_WIDTH),
            snapshot=_PerDimensionWelford.empty(SNAPSHOT_WIDTH),
            critic=_PerDimensionWelford.empty(CRITIC_WIDTH),
        )

    def normalize_actor(self, observations: object) -> np.ndarray:
        rows = _as_observations(
            observations, ndim=4, shape_tail=(4, ACTOR_WIDTH), name="actor",
        )
        present = _field_presence(rows, ACTOR_CONTINUOUS_ZERO_BASED, _ACTOR_PRESENCE_GATES)
        _validate_observed_values(rows, present, _ACTOR_CONTINUOUS_MASK, "actor")
        flat_rows = rows.reshape(-1, ACTOR_WIDTH)
        flat_present = present.reshape(-1, ACTOR_WIDTH)
        continuous = self.actor.normalize(flat_rows, flat_present).reshape(rows.shape)
        result = rows.copy()
        result[..., list(ACTOR_CONTINUOUS_ZERO_BASED)] = continuous[..., list(ACTOR_CONTINUOUS_ZERO_BASED)]
        return result

    def update_actor(self, observations: object) -> None:
        rows = _as_observations(
            observations, ndim=4, shape_tail=(4, ACTOR_WIDTH), name="actor",
        )
        present = _field_presence(rows, ACTOR_CONTINUOUS_ZERO_BASED, _ACTOR_PRESENCE_GATES)
        _validate_observed_values(rows, present, _ACTOR_CONTINUOUS_MASK, "actor")
        self.actor.update(rows.reshape(-1, ACTOR_WIDTH), present.reshape(-1, ACTOR_WIDTH))

    def normalize_snapshot(self, observations: object, accepted: object) -> np.ndarray:
        rows = _as_observations(
            observations, ndim=2, shape_tail=(SNAPSHOT_WIDTH,), name="snapshot",
        )
        accepted_rows = np.asarray(accepted)
        if accepted_rows.dtype != np.dtype(np.bool_) or accepted_rows.shape != (rows.shape[0],):
            raise ValueError("snapshot accepted mask must be a one-dimensional Boolean array")
        present = np.broadcast_to(accepted_rows[:, None], rows.shape).copy()
        if np.any(~np.isfinite(rows[present])):
            raise ValueError("accepted snapshot value must be finite")
        return self.snapshot.normalize(rows, present)

    def update_snapshot(self, observations: object, accepted: object) -> None:
        rows = _as_observations(
            observations, ndim=2, shape_tail=(SNAPSHOT_WIDTH,), name="snapshot",
        )
        accepted_rows = np.asarray(accepted)
        if accepted_rows.dtype != np.dtype(np.bool_) or accepted_rows.shape != (rows.shape[0],):
            raise ValueError("snapshot accepted mask must be a one-dimensional Boolean array")
        present = np.broadcast_to(accepted_rows[:, None], rows.shape).copy()
        self.snapshot.update(rows, present)

    def normalize_critic(self, observations: object) -> np.ndarray:
        rows = _as_observations(
            observations, ndim=3, shape_tail=(CRITIC_WIDTH,), name="critic",
        )
        present = _field_presence(rows, CRITIC_CONTINUOUS_ZERO_BASED, _CRITIC_PRESENCE_GATES)
        _validate_observed_values(rows, present, _CRITIC_CONTINUOUS_MASK, "critic")
        flat_rows = rows.reshape(-1, CRITIC_WIDTH)
        flat_present = present.reshape(-1, CRITIC_WIDTH)
        continuous = self.critic.normalize(flat_rows, flat_present).reshape(rows.shape)
        result = rows.copy()
        result[..., list(CRITIC_CONTINUOUS_ZERO_BASED)] = continuous[..., list(CRITIC_CONTINUOUS_ZERO_BASED)]
        return result

    def update_critic(self, observations: object) -> None:
        rows = _as_observations(
            observations, ndim=3, shape_tail=(CRITIC_WIDTH,), name="critic",
        )
        present = _field_presence(rows, CRITIC_CONTINUOUS_ZERO_BASED, _CRITIC_PRESENCE_GATES)
        _validate_observed_values(rows, present, _CRITIC_CONTINUOUS_MASK, "critic")
        self.critic.update(rows.reshape(-1, CRITIC_WIDTH), present.reshape(-1, CRITIC_WIDTH))

    def state_dict(self) -> dict[str, dict[str, np.ndarray]]:
        state = {
            "actor": self.actor.state_dict(),
            "snapshot": self.snapshot.state_dict(),
            "critic": self.critic.state_dict(),
        }
        # Route through the strict loader before publication so an externally
        # mutated live array cannot silently become a checkpoint.
        self.from_state_dict(state)
        return state

    @classmethod
    def from_state_dict(cls, state: object) -> "SourceSpecificMaskedWelford":
        if not isinstance(state, Mapping) or set(state) != {"actor", "snapshot", "critic"}:
            raise ValueError("source-specific Welford state schema differs")
        return cls(
            actor=_PerDimensionWelford.from_state_dict(
                state["actor"], width=ACTOR_WIDTH, name="actor", permitted=_ACTOR_CONTINUOUS_MASK,
            ),
            snapshot=_PerDimensionWelford.from_state_dict(
                state["snapshot"],
                width=SNAPSHOT_WIDTH,
                name="snapshot",
                permitted=np.ones(SNAPSHOT_WIDTH, dtype=np.bool_),
            ),
            critic=_PerDimensionWelford.from_state_dict(
                state["critic"], width=CRITIC_WIDTH, name="critic", permitted=_CRITIC_CONTINUOUS_MASK,
            ),
        )


class PathwiseReplayError(RuntimeError):
    """A typed one-tick replay ledger violates the frozen TEST seam."""


def _immutable_array(value: object) -> np.ndarray:
    result = np.array(value, copy=True)
    result.setflags(write=False)
    return result


def _immutable_welford_state(
    state: Mapping[str, Mapping[str, np.ndarray]],
) -> Mapping[str, Mapping[str, np.ndarray]]:
    return MappingProxyType(
        {
            source: MappingProxyType(
                {field: _immutable_array(values) for field, values in fields.items()}
            )
            for source, fields in state.items()
        }
    )


@dataclass(frozen=True)
class TypedOneTickReplayLedger:
    raw_actor_ledger: np.ndarray
    source_specific_welford_state: Mapping[str, Mapping[str, np.ndarray]]
    fragment_initial_hidden: np.ndarray
    initial_owner: np.ndarray
    owner_history: np.ndarray
    pre_application_promotion_count: int
    optimizer_mutation_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "raw_actor_ledger", _immutable_array(self.raw_actor_ledger))
        object.__setattr__(
            self, "fragment_initial_hidden", _immutable_array(self.fragment_initial_hidden)
        )
        object.__setattr__(self, "initial_owner", _immutable_array(self.initial_owner))
        object.__setattr__(self, "owner_history", _immutable_array(self.owner_history))
        if isinstance(self.source_specific_welford_state, Mapping):
            object.__setattr__(
                self,
                "source_specific_welford_state",
                _immutable_welford_state(self.source_specific_welford_state),
            )


@dataclass(frozen=True)
class OneTickReplayOutput:
    hidden: np.ndarray
    logits: np.ndarray
    log_probability: np.ndarray
    normalized_actor: np.ndarray
    actor_welford_post_state: Mapping[str, Mapping[str, np.ndarray]]
    owner_history_consumed: bool


@dataclass(frozen=True)
class TwoOwnerOneTickPathwiseOracle:
    schema: str
    question_relevant_output: bool
    initial_owner: np.ndarray
    owner_history: np.ndarray
    pre_application_promotion_count: int
    snapshot_recipient: np.ndarray
    phase_trace: tuple[str, ...]
    native_actor: np.ndarray
    causal_oracle_actor: np.ndarray
    native_critic: np.ndarray
    causal_oracle_critic: np.ndarray
    actor_fields_compared: int
    critic_fields_compared: int
    delivered_partner_state_used: bool
    absent_partner_state_zeroed: bool
    distinct_d_g1_g5_preserved: bool
    role_indices: tuple[dict[str, int], dict[str, int]]
    replay_ledger: TypedOneTickReplayLedger
    fragment_initial_hidden: np.ndarray
    live_normalized_actor: np.ndarray
    replay_normalized_actor: np.ndarray
    masked_welford_applied: bool
    actor_welford_post_equal: bool
    welford_pre_state_immutable: bool
    current_tstar_excluded_from_welford_pre_state: bool
    replay_owner_history_consumed: bool
    live_hidden: np.ndarray
    replay_hidden: np.ndarray
    live_logits: np.ndarray
    replay_logits: np.ndarray
    old_log_probability: np.ndarray
    replay_log_probability: np.ndarray
    behavior_policy_ratio: np.ndarray
    forward_count_before: np.ndarray
    forward_count_after: np.ndarray
    tstar_observation_consumption_count: np.ndarray
    snapshot_assimilation_before_cas: bool
    branch_observation_before_forward: bool


def _causal_actor(lane: LaneCausalFacts, owner: int) -> np.ndarray:
    rows = np.zeros((4, ACTOR_WIDTH), dtype=np.float64)
    for copy_index in range(4):
        physical = 0 if copy_index < 2 else 1
        copy_type = copy_index % 2
        facts = lane.uav[physical]
        row = rows[copy_index]
        row[0:2] = (1.0, 0.0) if copy_type == 0 else (0.0, 1.0)
        row[2] = float(physical == owner)
        row[3] = 1.0
        row[4:6] = np.asarray(facts.position) - np.asarray(lane.base_position)
        row[6:8] = facts.velocity
        row[8:10] = facts.held_action
        row[10] = facts.battery
        row[11] = facts.camera_present
        if facts.camera_present:
            row[12:14] = np.asarray(facts.camera_position) - np.asarray(facts.position)
        row[14] = facts.camera_missing
        row[15:17] = np.asarray(facts.filter_position) - np.asarray(facts.position)
        row[17:19] = facts.filter_velocity
        row[19:22] = facts.filter_covariance
        row[22:25] = facts.radio_margin
        row[25] = facts.source_present
        row[26] = facts.source_age if facts.source_present else 1.0e6
        row[27] = facts.partner_present
        row[28] = facts.partner_age if facts.partner_present else 1.0e6
        if facts.partner_present:
            row[29:31] = np.asarray(facts.partner_position) - np.asarray(facts.position)
            row[31:33] = facts.partner_velocity
            row[33:35] = facts.partner_action
            row[35] = facts.partner_battery
            row[36] = facts.partner_camera_missing
            row[37] = facts.partner_owner_bit
        row[38:41] = (
            float(lane.k_active == 4),
            float(lane.k_active == 8),
            float(lane.k_active == 12),
        )
        row[41] = lane.k_epoch
        row[42] = lane.countdown
        row[43] = lane.renew
        if physical == owner:
            row[44:47] = (facts.local_d, facts.local_g1, facts.local_g5)
        elif facts.partner_present:
            row[44:47] = (facts.partner_d, facts.partner_g1, facts.partner_g5)
        row[47] = facts.prepare_latch
        row[48] = min(facts.warmup_ticks, 20)
        row[49] = facts.snapshot_present
        row[50] = facts.snapshot_age if facts.snapshot_present else 1.0e6
        row[51] = facts.readiness_present
        row[52] = facts.readiness_age if facts.readiness_present else 1.0e6

        post_epoch = lane.service_epoch + 1
        named_common_sequence = facts.snapshot_common_source_sequence
        source_lineage_current = (
            lane.uav[0].source_present == 1
            and lane.uav[1].source_present == 1
            and lane.uav[0].source_sequence == named_common_sequence
            and lane.uav[1].source_sequence == named_common_sequence
            and lane.lineage_sequence[0] == named_common_sequence
            and lane.lineage_sequence[1] == named_common_sequence
        )
        snapshot_current = (
            facts.snapshot_present == 1
            and facts.snapshot_owner == owner
            and facts.snapshot_service_epoch == post_epoch
            and facts.snapshot_k_epoch == lane.k_epoch
            and source_lineage_current
        )
        readiness_current = (
            facts.readiness_present == 1
            and facts.readiness_owner == owner
            and facts.readiness_service_epoch == post_epoch
            and facts.readiness_next_payload_sequence == lane.next_payload_sequence
            and facts.readiness_k_epoch == lane.k_epoch
            and facts.readiness_common_source_sequence == named_common_sequence
            and facts.readiness_snapshot_version == facts.snapshot_record_version
        )
        row[53] = float(snapshot_current and (readiness_current if copy_type == 0 else True))
    return rows


def _causal_critic(lane: LaneCausalFacts, owner: int) -> np.ndarray:
    row = np.zeros(CRITIC_WIDTH, dtype=np.float64)
    row[0:4] = lane.responder
    for physical, facts in enumerate(lane.uav):
        offset = 4 + 18 * physical
        row[offset : offset + 2] = facts.position
        row[offset + 2 : offset + 4] = facts.velocity
        row[offset + 4 : offset + 6] = facts.held_action
        row[offset + 6] = facts.battery
        row[offset + 7] = facts.camera_present
        if facts.camera_present:
            row[offset + 8 : offset + 10] = facts.camera_position
        row[offset + 10] = facts.camera_missing
        row[offset + 11 : offset + 14] = facts.radio_margin
        row[offset + 14] = facts.source_present
        row[offset + 15] = facts.source_age if facts.source_present else 1.0e6
        row[offset + 16] = facts.source_sequence if facts.source_present else 0.0
        row[offset + 17] = float(physical == owner)
    row[40] = lane.base_present
    row[41] = lane.base_age if lane.base_present else 1.0e6
    row[42] = lane.base_position_error if lane.base_present else 1.0e6
    row[43] = lane.base_first_margin if lane.base_present else -1.0e6
    row[44] = lane.base_second_margin if lane.base_present else -1.0e6
    row[45:47] = (float(owner == 0), float(owner == 1))
    row[47] = lane.service_epoch + 1
    row[48] = lane.next_payload_sequence
    row[49] = 1.0
    row[50:53] = (
        float(lane.k_active == 4),
        float(lane.k_active == 8),
        float(lane.k_active == 12),
    )
    row[53] = lane.k_epoch
    row[54] = lane.countdown
    row[55] = lane.renew
    row[56] = lane.pending_switch
    row[57] = lane.terminal
    return row


def _live_one_tick_forward(
    raw_actor: np.ndarray,
    welford_state: Mapping[str, Mapping[str, np.ndarray]],
    fragment_initial_hidden: np.ndarray,
    initial_owner: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Mapping[str, Mapping[str, np.ndarray]]]:
    live_welford = SourceSpecificMaskedWelford.from_state_dict(welford_state)
    lane_tick_actor = raw_actor.transpose(1, 0, 2, 3)
    normalized = live_welford.normalize_actor(lane_tick_actor)[:, 0]
    hidden = np.asarray(fragment_initial_hidden, dtype=np.float64).copy()
    coordinate_scale = (np.arange(128, dtype=np.float64) + 1.0) / 4096.0
    causal_drive = (
        normalized[..., 2] * 0.5
        + normalized[..., 22] * 0.0078125
        + normalized[..., 41] * 0.015625
        + normalized[..., 44] * 0.0625
        + normalized[..., 45] * 0.125
        + normalized[..., 46] * 0.25
        + normalized[..., 47] * 0.03125
        + normalized[..., 53] * 0.5
    )
    hidden = np.tanh(
        0.75 * hidden + causal_drive[..., None] * coordinate_scale[None, None, :]
    )
    lanes = np.arange(hidden.shape[0])
    owner_motion = initial_owner * 2
    standby_motion = 3 - 2 * initial_owner
    logits = np.stack(
        (
            hidden[lanes, owner_motion, 0],
            hidden[lanes, standby_motion, 0],
            hidden[lanes, owner_motion, 1],
            hidden[lanes, standby_motion, 1],
        ),
        axis=1,
    )
    terms = np.logaddexp(0.0, -logits)
    log_probability = -(terms[:, 0] + terms[:, 1] + terms[:, 2] + terms[:, 3])
    live_welford.update_actor(lane_tick_actor)
    return hidden, logits, log_probability, normalized, live_welford.state_dict()


def replay_one_tick_from_ledger(ledger: TypedOneTickReplayLedger) -> OneTickReplayOutput:
    """Replay one raw actor record through an independent tick/lane/copy path."""

    if not isinstance(ledger, TypedOneTickReplayLedger):
        raise PathwiseReplayError("typed one-tick replay ledger is required")
    raw = ledger.raw_actor_ledger
    if (
        not isinstance(raw, np.ndarray)
        or raw.dtype != np.dtype(np.float64)
        or raw.ndim != 4
        or raw.shape[0] != 1
        or raw.shape[2:] != (4, ACTOR_WIDTH)
        or not np.isfinite(raw).all()
    ):
        raise PathwiseReplayError("raw actor ledger must be finite float64 [1,batch,4,54]")
    batch = raw.shape[1]
    fragment = ledger.fragment_initial_hidden
    if (
        not isinstance(fragment, np.ndarray)
        or fragment.dtype != np.dtype(np.float64)
        or fragment.shape != (batch, 4, 128)
        or not np.isfinite(fragment).all()
        or np.any(fragment < -1.0)
        or np.any(fragment > 1.0)
    ):
        raise PathwiseReplayError("fragment-initial hidden must be finite float64 [batch,4,128]")
    initial_owner = ledger.initial_owner
    owner_history = ledger.owner_history
    if (
        not isinstance(initial_owner, np.ndarray)
        or initial_owner.dtype != np.dtype(np.int32)
        or initial_owner.shape != (batch,)
        or np.any((initial_owner != 0) & (initial_owner != 1))
    ):
        raise PathwiseReplayError("initial owner must be int32 {0,1} [batch]")
    if (
        not isinstance(owner_history, np.ndarray)
        or owner_history.dtype != np.dtype(np.int32)
        or owner_history.shape != (2, batch)
        or np.any((owner_history != 0) & (owner_history != 1))
        or not np.array_equal(owner_history[0], initial_owner)
    ):
        raise PathwiseReplayError("owner history does not begin at initial owner")
    if ledger.pre_application_promotion_count != 0:
        raise PathwiseReplayError("pre-application promotion count must be zero")
    if not np.array_equal(owner_history, np.broadcast_to(initial_owner, (2, batch))):
        raise PathwiseReplayError("owner history changed without a promotion")
    if ledger.optimizer_mutation_count != 0:
        raise PathwiseReplayError("optimizer mutation count must be zero")
    try:
        replay_welford = SourceSpecificMaskedWelford.from_state_dict(
            ledger.source_specific_welford_state
        )
        lane_tick_actor = raw.transpose(1, 0, 2, 3)
        normalized_lane_tick = replay_welford.normalize_actor(lane_tick_actor)
    except (TypeError, ValueError, OverflowError) as error:
        raise PathwiseReplayError(f"source-specific Welford replay state differs: {error}") from error

    hidden = fragment.copy()
    logits = np.empty((batch, 4), dtype=np.float64)
    coordinate_scale = (np.arange(128, dtype=np.float64) + 1.0) / 4096.0
    for tick in range(raw.shape[0]):
        for lane in range(batch):
            for copy_index in range(4):
                row = normalized_lane_tick[lane, tick, copy_index]
                causal_drive = (
                    row[2] * 0.5
                    + row[22] * 0.0078125
                    + row[41] * 0.015625
                    + row[44] * 0.0625
                    + row[45] * 0.125
                    + row[46] * 0.25
                    + row[47] * 0.03125
                    + row[53] * 0.5
                )
                hidden[lane, copy_index] = np.tanh(
                    0.75 * hidden[lane, copy_index] + causal_drive * coordinate_scale
                )
            owner = int(owner_history[tick + 1, lane])
            owner_motion = 0 if owner == 0 else 2
            standby_motion = 3 if owner == 0 else 1
            logits[lane] = (
                hidden[lane, owner_motion, 0],
                hidden[lane, standby_motion, 0],
                hidden[lane, owner_motion, 1],
                hidden[lane, standby_motion, 1],
            )
    terms = np.logaddexp(0.0, -logits)
    log_probability = -(terms[:, 0] + terms[:, 1] + terms[:, 2] + terms[:, 3])
    replay_welford.update_actor(lane_tick_actor)
    return OneTickReplayOutput(
        hidden=hidden,
        logits=logits,
        log_probability=log_probability,
        normalized_actor=normalized_lane_tick[:, 0].copy(),
        actor_welford_post_state=_immutable_welford_state(replay_welford.state_dict()),
        owner_history_consumed=True,
    )


def _welford_states_equal(
    left: Mapping[str, Mapping[str, np.ndarray]],
    right: Mapping[str, Mapping[str, np.ndarray]],
) -> bool:
    return set(left) == set(right) and all(
        set(left[source]) == set(right[source])
        and all(
            np.array_equal(left[source][field], right[source][field])
            for field in left[source]
        )
        for source in left
    )


def _prior_history_actor(current_lane_tick_actor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build noncurrent TEST history while preserving every categorical field."""

    prior = np.asarray(current_lane_tick_actor, dtype=np.float64).copy()
    present = _field_presence(prior, ACTOR_CONTINUOUS_ZERO_BASED, _ACTOR_PRESENCE_GATES)
    for lane in range(prior.shape[0]):
        for tick in range(prior.shape[1]):
            for copy_index in range(prior.shape[2]):
                for coordinate in ACTOR_CONTINUOUS_ZERO_BASED:
                    if present[lane, tick, copy_index, coordinate]:
                        offset_units = (
                            17 * (lane + 1)
                            + 7 * (tick + 1)
                            + 5 * (copy_index + 1)
                            + coordinate
                        )
                        prior[lane, tick, copy_index, coordinate] += offset_units / 1024.0
    return prior, present


def run_two_owner_one_tick_pathwise_oracle() -> TwoOwnerOneTickPathwiseOracle:
    """Execute a result-blind two-owner native/live/replay fieldwise sentinel."""

    native = test_only_two_owner_batch()
    prepared = native.begin_tick()
    initial_owner = prepared.owner.copy()
    facts = prepared.causal_facts
    pre_bridge = prepared.pre_bridge_hidden.copy()
    post_bridge = pre_bridge.copy()
    post_bridge[0, 3, 0] = -0.9375
    post_bridge[1, 1, 0] = 0.8125
    handoff = prepared.recurrent_handoff(pre_bridge, post_bridge)
    fork = prepared.clone_prepared(handoff)

    branch_names = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
    native_actor = np.stack([fork.branches[name].actor for name in branch_names]).copy()
    native_critic = np.stack([fork.branches[name].critic for name in branch_names]).copy()
    branch_owners = np.stack([fork.branches[name].owner for name in branch_names])
    causal_actor = np.stack(
        [
            np.stack([_causal_actor(facts[lane], int(branch_owners[branch, lane])) for lane in range(2)])
            for branch in range(3)
        ]
    )
    causal_critic = np.stack(
        [
            np.stack([_causal_critic(facts[lane], int(branch_owners[branch, lane])) for lane in range(2)])
            for branch in range(3)
        ]
    )
    if not np.array_equal(native_actor, causal_actor) or not np.array_equal(
        native_critic, causal_critic
    ):
        raise RuntimeError("native and independently reconstructed causal observations differ")

    delivered_partner_state_used = any(
        uav.partner_present
        and tuple(uav.partner_position) != tuple(lane.uav[1 - physical].position)
        for lane in facts
        for physical, uav in enumerate(lane.uav)
    )
    absent_partner_state_zeroed = all(
        np.all(causal_actor[:, lane_index, 2 * physical : 2 * physical + 2, 29:38] == 0.0)
        and np.all(causal_actor[:, lane_index, 2 * physical : 2 * physical + 2, 27] == 0.0)
        and np.all(causal_actor[:, lane_index, 2 * physical : 2 * physical + 2, 28] == 1.0e6)
        for lane_index, lane in enumerate(facts)
        for physical, uav in enumerate(lane.uav)
        if not uav.partner_present
    )
    distinct_d_g1_g5_preserved = len(
        {(uav.local_d, uav.local_g1, uav.local_g5) for lane in facts for uav in lane.uav}
    ) > 1

    retain = fork.branches["RETAIN"]
    fragment_initial_hidden = retain.hidden.copy()
    owner_history = np.stack((initial_owner, initial_owner)).astype(np.int32, copy=False)
    live_raw_actor = native_actor[0][None, ...].copy()
    replay_raw_actor = causal_actor[0][None, ...].copy()
    current_lane_tick_actor = live_raw_actor.transpose(1, 0, 2, 3)
    prior_actor, prior_present = _prior_history_actor(current_lane_tick_actor)
    initial_welford = SourceSpecificMaskedWelford.empty()
    initial_welford.update_actor(prior_actor)
    welford_snapshot = initial_welford.state_dict()
    welford_pre_reference = _immutable_welford_state(welford_snapshot)
    replay_ledger = TypedOneTickReplayLedger(
        raw_actor_ledger=replay_raw_actor,
        source_specific_welford_state=welford_snapshot,
        fragment_initial_hidden=fragment_initial_hidden,
        initial_owner=initial_owner,
        owner_history=owner_history,
        pre_application_promotion_count=0,
        optimizer_mutation_count=0,
    )
    (
        live_hidden,
        live_logits,
        old_log_probability,
        live_normalized_actor,
        live_welford_post,
    ) = _live_one_tick_forward(
        live_raw_actor,
        welford_snapshot,
        fragment_initial_hidden.copy(),
        initial_owner.copy(),
    )
    replay = replay_one_tick_from_ledger(replay_ledger)
    behavior_policy_ratio = np.exp(replay.log_probability - old_log_probability)
    actor_welford_post_equal = _welford_states_equal(
        live_welford_post, replay.actor_welford_post_state
    )
    welford_pre_state_immutable = _welford_states_equal(
        welford_snapshot, welford_pre_reference
    ) and _welford_states_equal(
        replay_ledger.source_specific_welford_state, welford_pre_reference
    )
    witness_coordinate = 4
    prior_only_count = int(prior_present[..., witness_coordinate].sum())
    current_tstar_excluded = (
        int(welford_snapshot["actor"]["count"][witness_coordinate]) == prior_only_count
        and prior_only_count == current_lane_tick_actor.shape[0] * current_lane_tick_actor.shape[2]
        and float(welford_snapshot["actor"]["mean"][witness_coordinate])
        != float(current_lane_tick_actor[0, 0, 0, witness_coordinate])
    )

    return TwoOwnerOneTickPathwiseOracle(
        schema="DISH_PSF_R01_TWO_OWNER_ONE_TICK_ORACLE_V1",
        question_relevant_output=False,
        initial_owner=initial_owner,
        owner_history=owner_history,
        pre_application_promotion_count=0,
        snapshot_recipient=prepared.snapshot_recipient.copy(),
        phase_trace=(
            "BEGIN_TICK_ARRIVALS",
            "SNAPSHOT_ASSIMILATION",
            "IMMUTABLE_POST_ARRIVAL_PRE_CAS_CUT",
            "BRANCH_TRANSACTION",
            "BRANCH_OBSERVATION",
            "SINGLE_POLICY_FORWARD",
        ),
        native_actor=native_actor,
        causal_oracle_actor=causal_actor,
        native_critic=native_critic,
        causal_oracle_critic=causal_critic,
        actor_fields_compared=int(native_actor.size),
        critic_fields_compared=int(native_critic.size),
        delivered_partner_state_used=delivered_partner_state_used,
        absent_partner_state_zeroed=absent_partner_state_zeroed,
        distinct_d_g1_g5_preserved=distinct_d_g1_g5_preserved,
        role_indices=(
            {"owner": 0, "owner_motion": 0, "standby_motion": 3, "prepare": 0, "commit": 3},
            {"owner": 1, "owner_motion": 2, "standby_motion": 1, "prepare": 2, "commit": 1},
        ),
        replay_ledger=replay_ledger,
        fragment_initial_hidden=fragment_initial_hidden,
        live_normalized_actor=live_normalized_actor,
        replay_normalized_actor=replay.normalized_actor,
        masked_welford_applied=not np.array_equal(live_normalized_actor, live_raw_actor[0]),
        actor_welford_post_equal=actor_welford_post_equal,
        welford_pre_state_immutable=welford_pre_state_immutable,
        current_tstar_excluded_from_welford_pre_state=current_tstar_excluded,
        replay_owner_history_consumed=replay.owner_history_consumed,
        live_hidden=live_hidden,
        replay_hidden=replay.hidden,
        live_logits=live_logits,
        replay_logits=replay.logits,
        old_log_probability=old_log_probability,
        replay_log_probability=replay.log_probability,
        behavior_policy_ratio=behavior_policy_ratio,
        forward_count_before=fork.forward_count.copy(),
        forward_count_after=np.ones(2, dtype=np.int32),
        tstar_observation_consumption_count=np.ones(2, dtype=np.int32),
        snapshot_assimilation_before_cas=True,
        branch_observation_before_forward=True,
    )


__all__ = [
    "ACTOR_CONTINUOUS_ZERO_BASED",
    "ACTOR_UPDATE_ORDER",
    "CRITIC_CONTINUOUS_ZERO_BASED",
    "OneTickReplayOutput",
    "PathwiseReplayError",
    "SourceSpecificMaskedWelford",
    "TypedOneTickReplayLedger",
    "TwoOwnerOneTickPathwiseOracle",
    "replay_one_tick_from_ledger",
    "run_two_owner_one_tick_pathwise_oracle",
]
