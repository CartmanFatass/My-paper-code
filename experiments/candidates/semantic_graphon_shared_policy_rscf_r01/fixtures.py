"""Deterministic synthetic TEST-only inputs for RSCF Gate-B conformance.

The formulas below are literals indexed by engineering case labels and lane
numbers.  They are not random generators and create no scientific seed,
coordinate, initialization, model, checkpoint, episode, rollout, or endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np

from .contracts import (
    ACTION_COUNT,
    FIFO_CAPACITY,
    FIXTURE_SCHEMA,
    HIDDEN_DIM,
    HORIZON,
    MAX_AGENTS,
    MESSAGE_DIM,
    OBSERVATION_DIM,
    ROLE_COUNT,
    SUPPORTED_ROSTERS,
    ContractError,
    FrozenRecord,
    TestIdentity,
    canonical_digest,
    legal_actions,
    require_test_identity,
    validate_roster_size,
)
from .snapshot import (
    FutureTapeCursor,
    PretransitionSnapshot,
    SnapshotBatch,
    create_snapshot_batch,
    create_test_snapshot,
)


ROLE_SUMMARY_DIM: Final = 33
TAPE_MODULUS: Final = 1_000_003


def make_test_identity(case_label: str = "CASE_ALPHA") -> TestIdentity:
    return TestIdentity(case_label)


def _case_code(identity: TestIdentity) -> int:
    require_test_identity(identity)
    value = 17
    for char in identity.label.encode("ascii"):
        value = (value * 257 + char + 29) & 0xFFFFFFFF
    return value


def _word(case_code: int, *parts: int) -> int:
    value = (case_code ^ 0xA5A55A5A) & 0xFFFFFFFF
    for part in parts:
        value = (value * 65_537 + int(part) * 257 + 97) & 0xFFFFFFFF
    return value


def _literal_array(case_code: int, shape: tuple[int, ...], salt: int, *, dtype: np.dtype) -> np.ndarray:
    values = np.empty(shape, dtype=dtype)
    for flat_index in range(values.size):
        word = _word(case_code, salt, flat_index)
        if np.issubdtype(dtype, np.floating):
            values.flat[flat_index] = ((word % 257) - 128) / 128.0
        else:
            values.flat[flat_index] = word % TAPE_MODULUS
    return values


@dataclass(frozen=True)
class FixtureParameterBundle:
    """Synthetic parameter-shaped tensors, explicitly outside model identity."""

    test_identity: TestIdentity
    actor_carriage: FrozenRecord
    critic_carriage: FrozenRecord
    residual_coefficients: FrozenRecord
    digest: str

    def __post_init__(self) -> None:
        require_test_identity(self.test_identity)
        if canonical_digest(self.canonical_payload()) != self.digest:
            raise ContractError("fixture parameter-bundle digest mismatch")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": FIXTURE_SCHEMA + "_PARAMETER_BUNDLE",
            "test_namespace": self.test_identity.namespace,
            "actor_carriage": self.actor_carriage.canonical_payload(),
            "critic_carriage": self.critic_carriage.canonical_payload(),
            "residual_coefficients": self.residual_coefficients.canonical_payload(),
        }


def make_test_parameter_bundle(identity: TestIdentity) -> FixtureParameterBundle:
    """Create immutable tensor shapes for TEST graph/conformance consumers."""
    identity = require_test_identity(identity)
    code = _case_code(identity)
    actor = FrozenRecord.freeze(
        {
            "message_encoder_weight": _literal_array(code, (OBSERVATION_DIM, MESSAGE_DIM), 101, dtype=np.dtype(np.float32)),
            "message_encoder_bias": _literal_array(code, (MESSAGE_DIM,), 102, dtype=np.dtype(np.float32)),
            "gru_input_weight": _literal_array(code, (3 * HIDDEN_DIM, OBSERVATION_DIM + ROLE_SUMMARY_DIM), 103, dtype=np.dtype(np.float32)),
            "gru_hidden_weight": _literal_array(code, (3 * HIDDEN_DIM, HIDDEN_DIM), 104, dtype=np.dtype(np.float32)),
            "action_head_weight": _literal_array(code, (HIDDEN_DIM, ACTION_COUNT), 105, dtype=np.dtype(np.float32)),
            "action_head_bias": _literal_array(code, (ACTION_COUNT,), 106, dtype=np.dtype(np.float32)),
        },
        path="fixture_actor_carriage",
    )
    critic = FrozenRecord.freeze(
        {
            "global_value_weight": _literal_array(code, (HIDDEN_DIM,), 201, dtype=np.dtype(np.float32)),
            "global_value_bias": float((code % 31) - 15) / 32.0,
        },
        path="fixture_critic_carriage",
    )
    residual = FrozenRecord.freeze(
        {
            "shared_eighteen_coefficients": _literal_array(code, (18,), 301, dtype=np.dtype(np.float32)) / 16.0,
            "phy_projection": [-0.15, 0.15],
            "edge_projection": [-1.50, 1.50],
        },
        path="fixture_residual_carriage",
    )
    provisional = FixtureParameterBundle.__new__(FixtureParameterBundle)
    object.__setattr__(provisional, "test_identity", identity)
    object.__setattr__(provisional, "actor_carriage", actor)
    object.__setattr__(provisional, "critic_carriage", critic)
    object.__setattr__(provisional, "residual_coefficients", residual)
    object.__setattr__(provisional, "digest", "0" * 64)
    object.__setattr__(provisional, "digest", canonical_digest(provisional.canonical_payload()))
    FixtureParameterBundle.__post_init__(provisional)
    return provisional


def make_test_pretransition_snapshot(
    identity: TestIdentity,
    *,
    roster_size: int,
    fixture_lane_index: int = 0,
) -> PretransitionSnapshot:
    """Construct one complete deterministic TEST carriage for any frozen roster."""
    identity = require_test_identity(identity)
    n = validate_roster_size(roster_size)
    if type(fixture_lane_index) is not int or fixture_lane_index < 0:
        raise ContractError("fixture_lane_index must be a nonnegative int")
    code = (_case_code(identity) + fixture_lane_index * 7_919) & 0xFFFFFFFF
    multiplicity = n // ROLE_COUNT
    slot = _word(code, 1) % HORIZON

    active = np.arange(MAX_AGENTS) < n
    roles = np.full(MAX_AGENTS, -1, dtype=np.int8)
    roles[:n] = np.repeat(np.arange(ROLE_COUNT, dtype=np.int8), multiplicity)
    local = np.full(MAX_AGENTS, -1, dtype=np.int16)
    local[:n] = np.tile(np.arange(multiplicity, dtype=np.int16), ROLE_COUNT)

    observations = np.zeros((MAX_AGENTS, OBSERVATION_DIM), dtype=np.float32)
    messages = np.zeros((MAX_AGENTS, MESSAGE_DIM), dtype=np.float32)
    summaries = np.zeros((MAX_AGENTS, ROLE_SUMMARY_DIM), dtype=np.float32)
    hidden = np.zeros((MAX_AGENTS, HIDDEN_DIM), dtype=np.float32)
    observations[:n] = _literal_array(code, (n, OBSERVATION_DIM), 11, dtype=np.dtype(np.float32))
    messages[:n] = _literal_array(code, (n, MESSAGE_DIM), 12, dtype=np.dtype(np.float32))
    summaries[:n] = _literal_array(code, (n, ROLE_SUMMARY_DIM), 13, dtype=np.dtype(np.float32))
    hidden[:n] = _literal_array(code, (n, HIDDEN_DIM), 14, dtype=np.dtype(np.float32))

    distribution = np.zeros((MAX_AGENTS, ACTION_COUNT), dtype=np.float32)
    actions = np.full(MAX_AGENTS, -1, dtype=np.int8)
    for agent in range(n):
        legal = legal_actions(int(roles[agent]))
        raw = np.asarray([1 + _word(code, 15, agent, action) % 97 for action in legal], dtype=np.float32)
        row = 0.96 * raw / raw.sum() + 0.04 / len(legal)
        distribution[agent, list(legal)] = row
        needle = _word(code, 16, agent) % 10_000
        cumulative = 0.0
        selected = legal[-1]
        for action in legal:
            cumulative += distribution[agent, action]
            if needle < int(round(cumulative * 10_000)):
                selected = action
                break
        actions[agent] = selected

    agent_basin = np.full(MAX_AGENTS, -1, dtype=np.int8)
    agent_basin[:n] = np.asarray([_word(code, 21, agent) % 2 for agent in range(n)], dtype=np.int8)
    previous_action = np.full(MAX_AGENTS, -1, dtype=np.int8)
    previous_success = np.zeros(MAX_AGENTS, dtype=np.bool_)
    for agent in range(n):
        previous_action[agent] = actions[agent] if (agent + slot) % 4 else -1
        previous_success[agent] = bool(_word(code, 22, agent) & 1)
    event_times = np.asarray([[0, 3, 7], [1, 4, 6]], dtype=np.int16)
    event_seen = np.zeros((2, 3), dtype=np.bool_)
    event_seen[:] = event_times <= slot
    world = {
        "static": {
            "horizon": HORIZON,
            "public_roles": list(("WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY")),
            "roster_size": n,
        },
        "agent_state": {
            "basin": agent_basin,
            "previous_action": previous_action,
            "previous_success": previous_success,
            "active_mask": active,
        },
        "event_state": {"event_times": event_times, "event_seen": event_seen},
        "slot_state": {"pretransition_slot": slot, "transition_applied": False},
    }

    fifo_basin = np.full((MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int8)
    fifo_event = np.full((MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int16)
    fifo_slot = np.full((MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int16)
    fifo_lengths = np.zeros(MAX_AGENTS, dtype=np.int8)
    for agent in range(n):
        capacity = 2 if int(roles[agent]) in (0, 1) else FIFO_CAPACITY
        length = _word(code, 31, agent) % (capacity + 1)
        fifo_lengths[agent] = length
        for position in range(length):
            fifo_basin[agent, position] = _word(code, 32, agent, position) % 2
            fifo_event[agent, position] = _word(code, 33, agent, position) % 3
            fifo_slot[agent, position] = _word(code, 34, agent, position) % (slot + 1)
    fifo_state = {
        "basin": fifo_basin,
        "event_index": fifo_event,
        "produced_slot": fifo_slot,
        "lengths": fifo_lengths,
    }

    scheduled_state = {
        "uplink": {
            "active": np.zeros((MAX_AGENTS, FIFO_CAPACITY), dtype=np.bool_),
            "arrival_slot": np.full((MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int16),
            "receiver_mask": np.zeros((MAX_AGENTS, FIFO_CAPACITY, MAX_AGENTS), dtype=np.bool_),
        },
        "base_delivery": {
            "active": np.zeros((MAX_AGENTS, FIFO_CAPACITY), dtype=np.bool_),
            "arrival_slot": np.full((MAX_AGENTS, FIFO_CAPACITY), -1, dtype=np.int16),
        },
    }
    delivered_mask = np.zeros((2, 3), dtype=np.bool_)
    if slot >= 5:
        delivered_mask[0, 0] = True
    delivered_state = {
        "event_mask": delivered_mask,
        "counts_by_basin": delivered_mask.sum(axis=1, dtype=np.int64),
    }
    metrics_state = {
        "radio_uses": int(_word(code, 41) % 8),
        "waste": int(_word(code, 42) % 4),
        "deliveries": int(delivered_mask.sum()),
        "scans": int(_word(code, 43) % 9),
        "reward_accumulator": float(int(_word(code, 44) % 33) - 16) / 16.0,
    }
    future_tape = {
        "action_uniforms": _literal_array(code, (HORIZON, MAX_AGENTS), 51, dtype=np.dtype(np.uint32)),
        "environment_events": _literal_array(code, (HORIZON, 2, 3), 52, dtype=np.dtype(np.uint32)),
        "detection": _literal_array(code, (HORIZON, 2, 7), 53, dtype=np.dtype(np.uint32)),
        "radio": _literal_array(code, (HORIZON, MAX_AGENTS), 54, dtype=np.dtype(np.uint32)),
        "packet": _literal_array(code, (HORIZON, MAX_AGENTS), 55, dtype=np.dtype(np.uint32)),
    }
    return create_test_snapshot(
        identity,
        roster_size=n,
        slot=slot,
        active_mask=active,
        roles=roles,
        role_local_indices=local,
        world=world,
        observations=observations,
        messages=messages,
        role_summaries=summaries,
        post_gru_hidden=hidden,
        legal_distribution=distribution,
        factual_joint_action=actions,
        future_tape_cursor=FutureTapeCursor(slot=slot),
        future_tape=future_tape,
        fifo_state=fifo_state,
        scheduled_state=scheduled_state,
        delivered_state=delivered_state,
        metrics_state=metrics_state,
    )


def make_test_snapshot_batch(
    identity: TestIdentity,
    *,
    width: int,
    active_lanes: int,
) -> SnapshotBatch:
    """Create packed active lanes and a canonical inactive tail for native batching."""
    identity = require_test_identity(identity)
    if type(active_lanes) is not int or not 0 <= active_lanes <= width:
        raise ContractError("active_lanes must be an integer in [0, width]")
    snapshots = tuple(
        make_test_pretransition_snapshot(
            identity,
            roster_size=SUPPORTED_ROSTERS[lane % len(SUPPORTED_ROSTERS)],
            fixture_lane_index=lane,
        )
        for lane in range(active_lanes)
    )
    return create_snapshot_batch(width, snapshots)
