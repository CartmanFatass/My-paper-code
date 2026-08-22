"""Immutable complete pre-transition carriage for the RSCF Gate-B runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .contracts import (
    ACTION_COUNT,
    FIFO_CAPACITY,
    HORIZON,
    HIDDEN_DIM,
    MAX_AGENTS,
    OBSERVATION_DIM,
    MESSAGE_DIM,
    PUBLIC_ROLES,
    ROLE_COUNT,
    SNAPSHOT_SCHEMA,
    SUPPORTED_WIDTHS,
    ContractError,
    FrozenArray,
    FrozenRecord,
    TestIdentity,
    canonical_digest,
    legal_actions,
    require_test_identity,
    validate_roster_size,
)


@dataclass(frozen=True)
class FutureTapeCursor:
    slot: int
    event_offset: int = 0
    detection_offset: int = 0
    radio_offset: int = 0
    packet_offset: int = 0
    action_offset: int = 0

    def __post_init__(self) -> None:
        if type(self.slot) is not int or not 0 <= self.slot < 12:
            raise ContractError("future-tape cursor slot outside [0, 11]")
        for name in ("event_offset", "detection_offset", "radio_offset", "packet_offset", "action_offset"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ContractError(f"future-tape cursor {name} must be a nonnegative int")

    def canonical_payload(self) -> dict[str, int]:
        return {
            "slot": self.slot,
            "event_offset": self.event_offset,
            "detection_offset": self.detection_offset,
            "radio_offset": self.radio_offset,
            "packet_offset": self.packet_offset,
            "action_offset": self.action_offset,
        }


@dataclass(frozen=True)
class PretransitionSnapshot:
    """Frozen branch origin after policy sampling and before world mutation."""

    test_identity: TestIdentity
    roster_size: int
    slot: int
    active_mask: FrozenArray
    roles: FrozenArray
    role_local_indices: FrozenArray
    world: FrozenRecord
    observations: FrozenArray
    messages: FrozenArray
    role_summaries: FrozenArray
    post_gru_hidden: FrozenArray
    legal_distribution: FrozenArray
    factual_joint_action: FrozenArray
    future_tape_cursor: FutureTapeCursor
    future_tape: FrozenRecord
    fifo_state: FrozenRecord
    scheduled_state: FrozenRecord
    delivered_state: FrozenRecord
    metrics_state: FrozenRecord
    digest: str

    def __post_init__(self) -> None:
        _validate_snapshot(self, verify_digest=True)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "test_namespace": self.test_identity.namespace,
            "roster_size": self.roster_size,
            "slot": self.slot,
            "active_mask": self.active_mask.canonical_payload(),
            "roles": self.roles.canonical_payload(),
            "role_local_indices": self.role_local_indices.canonical_payload(),
            "world": self.world.canonical_payload(),
            "observations": self.observations.canonical_payload(),
            "messages": self.messages.canonical_payload(),
            "role_summaries": self.role_summaries.canonical_payload(),
            "post_gru_hidden": self.post_gru_hidden.canonical_payload(),
            "legal_distribution": self.legal_distribution.canonical_payload(),
            "factual_joint_action": self.factual_joint_action.canonical_payload(),
            "future_tape_cursor": self.future_tape_cursor.canonical_payload(),
            "future_tape": self.future_tape.canonical_payload(),
            "fifo_state": self.fifo_state.canonical_payload(),
            "scheduled_state": self.scheduled_state.canonical_payload(),
            "delivered_state": self.delivered_state.canonical_payload(),
            "metrics_state": self.metrics_state.canonical_payload(),
        }

    def mutable_native_payload(self) -> dict[str, object]:
        """Return a fresh, complete mutable carriage for one branch restore."""
        return {
            "schema": SNAPSHOT_SCHEMA,
            "test_namespace": self.test_identity.namespace,
            "roster_size": self.roster_size,
            "slot": self.slot,
            "active_mask": self.active_mask.array(copy=True),
            "roles": self.roles.array(copy=True),
            "role_local_indices": self.role_local_indices.array(copy=True),
            "world": self.world.thaw(),
            "observations": self.observations.array(copy=True),
            "messages": self.messages.array(copy=True),
            "role_summaries": self.role_summaries.array(copy=True),
            "post_gru_hidden": self.post_gru_hidden.array(copy=True),
            "legal_distribution": self.legal_distribution.array(copy=True),
            "factual_joint_action": self.factual_joint_action.array(copy=True),
            "future_tape_cursor": dict(self.future_tape_cursor.canonical_payload()),
            "future_tape": self.future_tape.thaw(),
            "fifo_state": self.fifo_state.thaw(),
            "scheduled_state": self.scheduled_state.thaw(),
            "delivered_state": self.delivered_state.thaw(),
            "metrics_state": self.metrics_state.thaw(),
            "snapshot_digest": self.digest,
        }


def _require_array(
    frozen: FrozenArray,
    *,
    name: str,
    dtype: np.dtype,
    shape: tuple[int, ...] | None = None,
) -> np.ndarray:
    if not isinstance(frozen, FrozenArray):
        raise ContractError(f"snapshot {name} is not a FrozenArray")
    value = frozen.array()
    if value.dtype != dtype:
        raise ContractError(f"snapshot {name} has dtype {value.dtype}, expected {dtype}")
    if shape is not None and value.shape != shape:
        raise ContractError(f"snapshot {name} has shape {value.shape}, expected {shape}")
    if value.flags.writeable:
        raise ContractError(f"snapshot {name} storage must be immutable")
    return value


def _validate_snapshot(snapshot: PretransitionSnapshot, *, verify_digest: bool) -> None:
    require_test_identity(snapshot.test_identity)
    n = validate_roster_size(snapshot.roster_size)
    if type(snapshot.slot) is not int or not 0 <= snapshot.slot < 12:
        raise ContractError("snapshot slot outside [0, 11]")
    if snapshot.future_tape_cursor.slot != snapshot.slot:
        raise ContractError("future-tape cursor does not point at the pre-transition slot")

    active = _require_array(snapshot.active_mask, name="active_mask", dtype=np.dtype(np.bool_), shape=(MAX_AGENTS,))
    roles = _require_array(snapshot.roles, name="roles", dtype=np.dtype(np.int8), shape=(MAX_AGENTS,))
    local = _require_array(
        snapshot.role_local_indices,
        name="role_local_indices",
        dtype=np.dtype(np.int16),
        shape=(MAX_AGENTS,),
    )
    expected_active = np.arange(MAX_AGENTS) < n
    if not np.array_equal(active, expected_active):
        raise ContractError("active lanes must be a packed prefix with an inactive tail")
    multiplicity = n // ROLE_COUNT
    expected_roles = np.full(MAX_AGENTS, -1, dtype=np.int8)
    expected_roles[:n] = np.repeat(np.arange(ROLE_COUNT, dtype=np.int8), multiplicity)
    if not np.array_equal(roles, expected_roles):
        raise ContractError("roles must be balanced, public, contiguous, and tail-sentinel filled")
    expected_local = np.full(MAX_AGENTS, -1, dtype=np.int16)
    expected_local[:n] = np.tile(np.arange(multiplicity, dtype=np.int16), ROLE_COUNT)
    if not np.array_equal(local, expected_local):
        raise ContractError("role-local indices or inactive-tail sentinels are invalid")

    observations = _require_array(
        snapshot.observations,
        name="observations",
        dtype=np.dtype(np.float64),
        shape=(MAX_AGENTS, OBSERVATION_DIM),
    )
    messages = _require_array(
        snapshot.messages,
        name="messages",
        dtype=np.dtype(np.float64),
        shape=(MAX_AGENTS, MESSAGE_DIM),
    )
    summaries = _require_array(snapshot.role_summaries, name="role_summaries", dtype=np.dtype(np.float64))
    if summaries.ndim != 2 or summaries.shape[0] != MAX_AGENTS or summaries.shape[1] <= 0:
        raise ContractError("role summaries must be [MAX_AGENTS, positive_width]")
    hidden = _require_array(
        snapshot.post_gru_hidden,
        name="post_gru_hidden",
        dtype=np.dtype(np.float64),
        shape=(MAX_AGENTS, HIDDEN_DIM),
    )
    distribution = _require_array(
        snapshot.legal_distribution,
        name="legal_distribution",
        dtype=np.dtype(np.float64),
        shape=(MAX_AGENTS, ACTION_COUNT),
    )
    actions = _require_array(
        snapshot.factual_joint_action,
        name="factual_joint_action",
        dtype=np.dtype(np.int8),
        shape=(MAX_AGENTS,),
    )
    for name, value in (("observations", observations), ("messages", messages), ("role_summaries", summaries), ("post_gru_hidden", hidden)):
        if not bool(np.isfinite(value).all()):
            raise ContractError(f"snapshot {name} contains non-finite values")
        if not bool(np.all(value[n:] == 0.0)):
            raise ContractError(f"snapshot {name} inactive tail must be zero")
    if not bool(np.isfinite(distribution).all()) or bool(np.any(distribution < 0.0)):
        raise ContractError("legal distributions must be finite and nonnegative")
    for agent in range(n):
        role = int(roles[agent])
        legal = legal_actions(role)
        illegal = tuple(action for action in range(ACTION_COUNT) if action not in legal)
        if illegal and not bool(np.all(distribution[agent, list(illegal)] == 0.0)):
            raise ContractError("legal distribution gives probability to a masked action")
        if not np.isclose(float(distribution[agent, list(legal)].sum()), 1.0, atol=1e-12, rtol=0.0):
            raise ContractError("legal distribution row does not sum to one")
        floor = 0.04 / len(legal)
        if bool(np.any(distribution[agent, list(legal)] < floor - 1e-12)):
            raise ContractError("legal distribution violates the 0.04 legal-uniform floor")
        if int(actions[agent]) not in legal:
            raise ContractError("factual joint action violates its public-role mask")
    if not bool(np.all(distribution[n:] == 0.0)) or not bool(np.all(actions[n:] == -1)):
        raise ContractError("distribution/action inactive tails are not canonical")

    snapshot.world.require_keys(("static", "agent_state", "event_state", "slot_state"), name="world")
    snapshot.future_tape.require_keys(
        ("action_uniforms", "environment_events", "detection", "radio", "packet"),
        name="future_tape",
    )
    snapshot.fifo_state.require_keys(("basin", "event_index", "produced_slot", "lengths"), name="fifo_state")
    snapshot.scheduled_state.require_keys(("uplink", "base_delivery"), name="scheduled_state")
    snapshot.delivered_state.require_keys(("event_mask", "counts_by_basin"), name="delivered_state")
    snapshot.metrics_state.require_keys(
        ("radio_uses", "waste", "deliveries", "scans", "reward_accumulator"),
        name="metrics_state",
    )
    _validate_complete_records(snapshot, n=n, active=active, roles=roles)
    if verify_digest:
        if not isinstance(snapshot.digest, str) or len(snapshot.digest) != 64:
            raise ContractError("snapshot digest is not a SHA-256 hex digest")
        if canonical_digest(snapshot.canonical_payload()) != snapshot.digest:
            raise ContractError("snapshot canonical digest mismatch")


def _as_mapping(value: object, *, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ContractError(f"snapshot {name} must be a mapping")
    return value


def _as_array(value: object, *, name: str, shape: tuple[int, ...], kind: str | None = None) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.shape != shape or value.dtype.hasobject:
        raise ContractError(f"snapshot {name} must be an ndarray with shape {shape}")
    if kind is not None and value.dtype.kind not in kind:
        raise ContractError(f"snapshot {name} has incompatible dtype {value.dtype}")
    if np.issubdtype(value.dtype, np.floating) and not bool(np.isfinite(value).all()):
        raise ContractError(f"snapshot {name} contains non-finite values")
    return value


def _validate_complete_records(
    snapshot: PretransitionSnapshot,
    *,
    n: int,
    active: np.ndarray,
    roles: np.ndarray,
) -> None:
    """Validate complete mutable carriage fields and their inactive tails."""
    world = snapshot.world.thaw()
    static = _as_mapping(world["static"], name="world.static")
    if static.get("horizon") != 12 or static.get("roster_size") != n:
        raise ContractError("world static horizon/roster does not match snapshot")
    if tuple(static.get("public_roles", ())) != PUBLIC_ROLES:
        raise ContractError("world static public roles differ from the frozen roles")
    agent_state = _as_mapping(world["agent_state"], name="world.agent_state")
    world_active = _as_array(agent_state.get("active_mask"), name="world.agent_state.active_mask", shape=(MAX_AGENTS,), kind="b")
    basin = _as_array(agent_state.get("basin"), name="world.agent_state.basin", shape=(MAX_AGENTS,), kind="iu")
    previous_action = _as_array(
        agent_state.get("previous_action"), name="world.agent_state.previous_action", shape=(MAX_AGENTS,), kind="iu"
    )
    previous_success = _as_array(
        agent_state.get("previous_success"), name="world.agent_state.previous_success", shape=(MAX_AGENTS,), kind="b"
    )
    if not np.array_equal(world_active, active):
        raise ContractError("world active mask differs from snapshot active mask")
    if not bool(np.all(basin[n:] == -1)) or not bool(np.all(previous_action[n:] == -1)) or bool(np.any(previous_success[n:])):
        raise ContractError("world agent-state inactive tail is not canonical")
    if bool(np.any((basin[:n] < 0) | (basin[:n] > 1))):
        raise ContractError("active agent basin is outside the two-basin support")
    event_state = _as_mapping(world["event_state"], name="world.event_state")
    _as_array(event_state.get("event_times"), name="world.event_state.event_times", shape=(2, 3), kind="iu")
    _as_array(event_state.get("event_seen"), name="world.event_state.event_seen", shape=(2, 3), kind="b")
    slot_state = _as_mapping(world["slot_state"], name="world.slot_state")
    if slot_state.get("pretransition_slot") != snapshot.slot or slot_state.get("transition_applied") is not False:
        raise ContractError("world slot state is not the required pre-transition boundary")

    fifo = snapshot.fifo_state.thaw()
    fifo_basin = _as_array(fifo["basin"], name="fifo_state.basin", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="iu")
    fifo_event = _as_array(fifo["event_index"], name="fifo_state.event_index", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="iu")
    fifo_slot = _as_array(fifo["produced_slot"], name="fifo_state.produced_slot", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="iu")
    fifo_lengths = _as_array(fifo["lengths"], name="fifo_state.lengths", shape=(MAX_AGENTS,), kind="iu")
    for agent in range(MAX_AGENTS):
        length = int(fifo_lengths[agent])
        capacity = 2 if agent < n and int(roles[agent]) in (0, 1) else FIFO_CAPACITY
        if agent >= n:
            capacity = 0
        if not 0 <= length <= capacity:
            raise ContractError("FIFO length exceeds the role or inactive-tail capacity")
        if not (
            bool(np.all(fifo_basin[agent, length:] == -1))
            and bool(np.all(fifo_event[agent, length:] == -1))
            and bool(np.all(fifo_slot[agent, length:] == -1))
        ):
            raise ContractError("FIFO inactive positions must use -1 sentinels")
        if length and (
            bool(np.any((fifo_basin[agent, :length] < 0) | (fifo_basin[agent, :length] > 1)))
            or bool(np.any((fifo_event[agent, :length] < 0) | (fifo_event[agent, :length] >= 3)))
            or bool(np.any((fifo_slot[agent, :length] < 0) | (fifo_slot[agent, :length] > snapshot.slot)))
        ):
            raise ContractError("FIFO active payload is outside its finite support")

    scheduled = snapshot.scheduled_state.thaw()
    uplink = _as_mapping(scheduled["uplink"], name="scheduled_state.uplink")
    uplink_active = _as_array(uplink.get("active"), name="scheduled_state.uplink.active", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="b")
    uplink_arrival = _as_array(
        uplink.get("arrival_slot"), name="scheduled_state.uplink.arrival_slot", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="iu"
    )
    receiver_mask = _as_array(
        uplink.get("receiver_mask"),
        name="scheduled_state.uplink.receiver_mask",
        shape=(MAX_AGENTS, FIFO_CAPACITY, MAX_AGENTS),
        kind="b",
    )
    base = _as_mapping(scheduled["base_delivery"], name="scheduled_state.base_delivery")
    base_active = _as_array(base.get("active"), name="scheduled_state.base_delivery.active", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="b")
    base_arrival = _as_array(
        base.get("arrival_slot"), name="scheduled_state.base_delivery.arrival_slot", shape=(MAX_AGENTS, FIFO_CAPACITY), kind="iu"
    )
    for active_entries, arrivals, name in (
        (uplink_active, uplink_arrival, "uplink"),
        (base_active, base_arrival, "base_delivery"),
    ):
        if bool(np.any(active_entries[n:])) or not bool(np.all(arrivals[n:] == -1)):
            raise ContractError(f"scheduled {name} inactive-agent tail is not canonical")
        if not bool(np.all(arrivals[~active_entries] == -1)):
            raise ContractError(f"scheduled {name} inactive entries must use -1 arrival")
        if bool(np.any(arrivals[active_entries] <= snapshot.slot)) or bool(np.any(arrivals[active_entries] >= HORIZON)):
            raise ContractError(f"scheduled {name} active arrival is not in the remaining horizon")
    if bool(np.any(receiver_mask[n:])) or bool(np.any(receiver_mask[:, :, n:])):
        raise ContractError("scheduled receiver-mask inactive tails must be false")

    delivered = snapshot.delivered_state.thaw()
    event_mask = _as_array(delivered["event_mask"], name="delivered_state.event_mask", shape=(2, 3), kind="b")
    counts = _as_array(delivered["counts_by_basin"], name="delivered_state.counts_by_basin", shape=(2,), kind="iu")
    if not np.array_equal(counts.astype(np.int64), event_mask.sum(axis=1, dtype=np.int64)):
        raise ContractError("delivered counts do not match delivered-event mask")

    metrics = snapshot.metrics_state.thaw()
    for name in ("radio_uses", "waste", "deliveries", "scans"):
        value = metrics[name]
        if type(value) is not int or value < 0:
            raise ContractError(f"metrics_state.{name} must be a nonnegative int")
    reward = metrics["reward_accumulator"]
    if not isinstance(reward, (int, float)) or not np.isfinite(float(reward)):
        raise ContractError("metrics_state.reward_accumulator must be finite")

    tape = snapshot.future_tape.thaw()
    _as_array(tape["action_uniforms"], name="future_tape.action_uniforms", shape=(HORIZON, MAX_AGENTS), kind="iu")
    _as_array(tape["environment_events"], name="future_tape.environment_events", shape=(HORIZON, 2, 3), kind="iu")
    detection = tape["detection"]
    if not isinstance(detection, np.ndarray) or detection.ndim != 3 or detection.shape[:2] != (HORIZON, 2):
        raise ContractError("future_tape.detection must be [HORIZON, 2, support]")
    _as_array(tape["radio"], name="future_tape.radio", shape=(HORIZON, MAX_AGENTS), kind="iu")
    _as_array(tape["packet"], name="future_tape.packet", shape=(HORIZON, MAX_AGENTS), kind="iu")


def create_test_snapshot(
    identity: TestIdentity,
    *,
    roster_size: int,
    slot: int,
    active_mask: np.ndarray,
    roles: np.ndarray,
    role_local_indices: np.ndarray,
    world: Mapping[str, object],
    observations: np.ndarray,
    messages: np.ndarray,
    role_summaries: np.ndarray,
    post_gru_hidden: np.ndarray,
    legal_distribution: np.ndarray,
    factual_joint_action: np.ndarray,
    future_tape_cursor: FutureTapeCursor,
    future_tape: Mapping[str, object],
    fifo_state: Mapping[str, object],
    scheduled_state: Mapping[str, object],
    delivered_state: Mapping[str, object],
    metrics_state: Mapping[str, object],
) -> PretransitionSnapshot:
    """Deep-freeze one TEST carriage and seal it with a canonical digest."""
    require_test_identity(identity)
    frozen = PretransitionSnapshot.__new__(PretransitionSnapshot)
    object.__setattr__(frozen, "test_identity", identity)
    object.__setattr__(frozen, "roster_size", roster_size)
    object.__setattr__(frozen, "slot", slot)
    object.__setattr__(frozen, "active_mask", FrozenArray.freeze(active_mask, name="active_mask"))
    object.__setattr__(frozen, "roles", FrozenArray.freeze(roles, name="roles"))
    object.__setattr__(frozen, "role_local_indices", FrozenArray.freeze(role_local_indices, name="role_local_indices"))
    object.__setattr__(frozen, "world", FrozenRecord.freeze(world, path="world"))
    object.__setattr__(frozen, "observations", FrozenArray.freeze(observations, name="observations"))
    object.__setattr__(frozen, "messages", FrozenArray.freeze(messages, name="messages"))
    object.__setattr__(frozen, "role_summaries", FrozenArray.freeze(role_summaries, name="role_summaries"))
    object.__setattr__(frozen, "post_gru_hidden", FrozenArray.freeze(post_gru_hidden, name="post_gru_hidden"))
    object.__setattr__(frozen, "legal_distribution", FrozenArray.freeze(legal_distribution, name="legal_distribution"))
    object.__setattr__(frozen, "factual_joint_action", FrozenArray.freeze(factual_joint_action, name="factual_joint_action"))
    object.__setattr__(frozen, "future_tape_cursor", future_tape_cursor)
    object.__setattr__(frozen, "future_tape", FrozenRecord.freeze(future_tape, path="future_tape"))
    object.__setattr__(frozen, "fifo_state", FrozenRecord.freeze(fifo_state, path="fifo_state"))
    object.__setattr__(frozen, "scheduled_state", FrozenRecord.freeze(scheduled_state, path="scheduled_state"))
    object.__setattr__(frozen, "delivered_state", FrozenRecord.freeze(delivered_state, path="delivered_state"))
    object.__setattr__(frozen, "metrics_state", FrozenRecord.freeze(metrics_state, path="metrics_state"))
    object.__setattr__(frozen, "digest", "0" * 64)
    _validate_snapshot(frozen, verify_digest=False)
    object.__setattr__(frozen, "digest", canonical_digest(frozen.canonical_payload()))
    _validate_snapshot(frozen, verify_digest=True)
    return frozen


def restore_snapshot(snapshot: PretransitionSnapshot) -> dict[str, object]:
    """Produce an isolated mutable restore; the sealed origin is unchanged."""
    _validate_snapshot(snapshot, verify_digest=True)
    return snapshot.mutable_native_payload()


def copy_snapshot(snapshot: PretransitionSnapshot) -> PretransitionSnapshot:
    """Deep-copy every carrier while preserving the canonical snapshot digest."""
    _validate_snapshot(snapshot, verify_digest=True)
    payload = snapshot.mutable_native_payload()
    copied = create_test_snapshot(
        snapshot.test_identity,
        roster_size=snapshot.roster_size,
        slot=snapshot.slot,
        active_mask=payload["active_mask"],  # type: ignore[arg-type]
        roles=payload["roles"],  # type: ignore[arg-type]
        role_local_indices=payload["role_local_indices"],  # type: ignore[arg-type]
        world=payload["world"],  # type: ignore[arg-type]
        observations=payload["observations"],  # type: ignore[arg-type]
        messages=payload["messages"],  # type: ignore[arg-type]
        role_summaries=payload["role_summaries"],  # type: ignore[arg-type]
        post_gru_hidden=payload["post_gru_hidden"],  # type: ignore[arg-type]
        legal_distribution=payload["legal_distribution"],  # type: ignore[arg-type]
        factual_joint_action=payload["factual_joint_action"],  # type: ignore[arg-type]
        future_tape_cursor=snapshot.future_tape_cursor,
        future_tape=payload["future_tape"],  # type: ignore[arg-type]
        fifo_state=payload["fifo_state"],  # type: ignore[arg-type]
        scheduled_state=payload["scheduled_state"],  # type: ignore[arg-type]
        delivered_state=payload["delivered_state"],  # type: ignore[arg-type]
        metrics_state=payload["metrics_state"],  # type: ignore[arg-type]
    )
    if copied.digest != snapshot.digest:
        raise ContractError("copy changed the snapshot canonical digest")
    return copied


@dataclass(frozen=True)
class SnapshotBatch:
    width: int
    active_lanes: int
    lanes: tuple[PretransitionSnapshot | None, ...]
    digest: str

    def __post_init__(self) -> None:
        if self.width not in SUPPORTED_WIDTHS or len(self.lanes) != self.width:
            raise ContractError("snapshot batch width is unsupported or inconsistent")
        if type(self.active_lanes) is not int or not 0 <= self.active_lanes <= self.width:
            raise ContractError("invalid snapshot batch active-lane count")
        if any(lane is None for lane in self.lanes[: self.active_lanes]):
            raise ContractError("active snapshot lanes must be a packed prefix")
        if any(lane is not None for lane in self.lanes[self.active_lanes :]):
            raise ContractError("inactive snapshot tail must contain only None")
        for lane in self.lanes[: self.active_lanes]:
            assert lane is not None
            _validate_snapshot(lane, verify_digest=True)
        if canonical_digest(self.canonical_payload()) != self.digest:
            raise ContractError("snapshot batch digest mismatch")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": SNAPSHOT_SCHEMA + "_BATCH",
            "width": self.width,
            "active_lanes": self.active_lanes,
            "lane_digests": [lane.digest if lane is not None else None for lane in self.lanes],
        }


def create_snapshot_batch(width: int, snapshots: tuple[PretransitionSnapshot, ...]) -> SnapshotBatch:
    if width not in SUPPORTED_WIDTHS:
        raise ContractError(f"snapshot batch width must be one of {SUPPORTED_WIDTHS}")
    if not isinstance(snapshots, tuple) or len(snapshots) > width:
        raise ContractError("snapshots must be a tuple no longer than width")
    lanes: tuple[PretransitionSnapshot | None, ...] = snapshots + (None,) * (width - len(snapshots))
    provisional = SnapshotBatch.__new__(SnapshotBatch)
    object.__setattr__(provisional, "width", width)
    object.__setattr__(provisional, "active_lanes", len(snapshots))
    object.__setattr__(provisional, "lanes", lanes)
    object.__setattr__(provisional, "digest", "0" * 64)
    object.__setattr__(provisional, "digest", canonical_digest(provisional.canonical_payload()))
    SnapshotBatch.__post_init__(provisional)
    return provisional
